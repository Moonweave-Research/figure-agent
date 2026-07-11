"""Validate the TikZ-only versus hybrid comparison evidence contract."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml


class ComparisonReportError(ValueError):
    """Raised when comparison evidence could support a misleading claim."""


_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_ACCOUNTING_CATEGORIES = {
    "preparation",
    "failed_attempts",
    "detector_diagnosis",
    "rendering",
    "repair",
}
_MEASUREMENTS = {
    "visual_quality",
    "scientific_fidelity",
    "source_edit_size",
    "correction_minutes",
    "detector_findings",
    "actionable_attribution_rate",
    "artifact_reproducibility",
}


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ComparisonReportError(f"{field} must be a mapping")
    return value


def _missing_measurement_is_explicit(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    has_null = value.get("value", object()) is None or any(
        value.get(variant, object()) is None for variant in ("tikz_only", "hybrid")
    )
    return not has_null or bool(value.get("missing_reason"))


def aggregate_review_input_hash(
    inputs: list[dict[str, str]], toolchain: dict[str, str]
) -> str:
    normalized_inputs = sorted(inputs, key=lambda item: (item["role"], item["path"]))
    for item in normalized_inputs:
        if set(item) != {"role", "path", "sha256"}:
            raise ComparisonReportError("review input must contain role, path, and sha256")
        if not _SHA256.fullmatch(item["sha256"]):
            raise ComparisonReportError("review input sha256 is invalid")
    payload = json.dumps(
        {"inputs": normalized_inputs, "toolchain": toolchain},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def load_comparison_report(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ComparisonReportError("comparison report requires YAML frontmatter")
    frontmatter = text.split("\n---\n", 1)[0][4:]
    loaded = yaml.safe_load(frontmatter)
    return validate_comparison_report(_mapping(loaded, "report frontmatter"))


def validate_human_verdict_bindings(
    verdict_path: Path,
    fixture_root: Path,
    *,
    current_toolchain: dict[str, str] | None = None,
) -> dict[str, Any]:
    verdict = _mapping(yaml.safe_load(verdict_path.read_text(encoding="utf-8")), "verdict")
    inputs = verdict.get("bound_inputs")
    if not isinstance(inputs, list):
        raise ComparisonReportError("bound_inputs must be a list")
    declared_toolchain = _mapping(verdict.get("toolchain"), "toolchain")
    declared_hash = verdict.get("review_input_hash")
    if declared_hash != aggregate_review_input_hash(inputs, declared_toolchain):
        raise ComparisonReportError("stored review_input_hash does not match declared bindings")

    root = fixture_root.resolve()
    mismatches: list[str] = []
    for item in inputs:
        relative = Path(item["path"])
        candidate = (root / relative).resolve()
        if relative.is_absolute() or not candidate.is_relative_to(root):
            raise ComparisonReportError(f"unsafe bound input path: {relative}")
        if not candidate.is_file():
            mismatches.append(relative.as_posix())
            continue
        actual = "sha256:" + hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != item["sha256"]:
            mismatches.append(relative.as_posix())
    if current_toolchain is not None and current_toolchain != declared_toolchain:
        mismatches.append("toolchain")
    return {"stale": bool(mismatches), "mismatches": mismatches, "review_input_hash": declared_hash}


def validate_comparison_report(report: dict[str, Any]) -> dict[str, Any]:
    if report.get("schema") != "figure-agent.hybrid-comparison.v1":
        raise ComparisonReportError("unsupported comparison schema")

    protocol = _mapping(report.get("protocol"), "protocol")
    if protocol.get("predeclared") is not True:
        raise ComparisonReportError("protocol must be predeclared")
    if protocol.get("same_clean_environment") is not True:
        raise ComparisonReportError("variants must run in the same clean environment")
    categories = protocol.get("accounting_categories")
    if not isinstance(categories, list) or set(categories) != _ACCOUNTING_CATEGORIES:
        raise ComparisonReportError("accounting_categories must include the full cost boundary")

    variants = _mapping(report.get("variants"), "variants")
    if set(variants) != {"tikz_only", "hybrid"}:
        raise ComparisonReportError("exactly tikz_only and hybrid variants are required")
    for name, raw_variant in variants.items():
        variant = _mapping(raw_variant, f"variants.{name}")
        if not isinstance(variant.get("compile_exit"), int):
            raise ComparisonReportError(f"variants.{name}.compile_exit must be an integer")
        if not _SHA256.fullmatch(str(variant.get("output_sha256", ""))):
            raise ComparisonReportError(f"variants.{name}.output_sha256 must be sha256")

    measurements = _mapping(report.get("measurements"), "measurements")
    if set(measurements) != _MEASUREMENTS:
        raise ComparisonReportError("comparison measurements are incomplete")
    for name, measurement in measurements.items():
        if not _missing_measurement_is_explicit(measurement):
            raise ComparisonReportError(f"measurements.{name} hides a missing value")

    verdicts = _mapping(report.get("verdicts"), "verdicts")
    for kind in ("scaffold", "artifact"):
        if kind not in verdicts:
            raise ComparisonReportError(f"{kind} verdict is required")
        verdict = _mapping(verdicts[kind], f"verdicts.{kind}")
        if verdict.get("status") not in {"pending", "accepted", "rejected"}:
            raise ComparisonReportError(f"invalid {kind} verdict status")
        if not _SHA256.fullmatch(str(verdict.get("review_input_hash", ""))):
            raise ComparisonReportError(f"invalid {kind} review_input_hash")

    if report.get("publication_acceptance") != "not_claimed":
        raise ComparisonReportError("publication_acceptance must remain not_claimed")
    if report.get("review_state") not in {"machine-valid", "review-ready"}:
        raise ComparisonReportError("machine evidence may only reach review-ready")
    return report
