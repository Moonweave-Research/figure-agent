from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import yaml

RUN_SCHEMA = "figure-agent.failure-ablation-run.v1"
REPORT_SCHEMA = "figure-agent.failure-ablation-report.v1"
VARIANTS = {"raw", "verified", "repaired"}
SCIENTIFIC_CLASSES = {"semantic", "relation"}


class FailureAblationError(ValueError):
    pass


def _load_run(path: Path, *, expected_variant: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise FailureAblationError("run_path_invalid")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != RUN_SCHEMA:
        raise FailureAblationError("run_schema_invalid")
    if payload.get("variant") != expected_variant:
        raise FailureAblationError("run_variant_invalid")
    findings = payload.get("findings")
    if not isinstance(findings, list) or any(
        not isinstance(item, dict) for item in findings
    ):
        raise FailureAblationError("run_findings_invalid")
    return payload


def _summarize_run(run: dict[str, Any]) -> dict[str, Any]:
    confirmed = [
        item
        for item in run["findings"]
        if item.get("review_outcome") == "confirmed_defect"
    ]
    class_counts = Counter(str(item.get("failure_class")) for item in confirmed)
    scientific_failed = any(
        item.get("failure_class") in SCIENTIFIC_CLASSES for item in confirmed
    )
    verdict = run.get("human_verdict")
    verdict_state = (
        "recorded"
        if (
            isinstance(verdict, dict)
            and verdict.get("state") == "recorded"
            and isinstance(verdict.get("reviewer"), str)
            and bool(verdict["reviewer"].strip())
        )
        else "pending"
    )
    return {
        "confirmed_defect_count": len(confirmed),
        "confirmed_defect_counts": dict(sorted(class_counts.items())),
        "scientific_gate": "failed" if scientific_failed else "passed",
        "human_correction_minutes": run.get("human_correction_minutes"),
        "intervention_count": run.get("intervention_count"),
        "clean_reproduction": run.get("clean_reproduction") is True,
        "human_verdict_state": verdict_state,
    }


def _delta(current: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in (
        "confirmed_defect_count",
        "human_correction_minutes",
        "intervention_count",
    ):
        current_value = current.get(key)
        baseline_value = baseline.get(key)
        if (
            isinstance(current_value, int | float)
            and not isinstance(current_value, bool)
            and isinstance(baseline_value, int | float)
            and not isinstance(baseline_value, bool)
        ):
            result[key] = current_value - baseline_value
        else:
            result[key] = None
    return result


def evaluate_ablation(run_paths: dict[str, Path]) -> dict[str, Any]:
    if set(run_paths) != VARIANTS:
        raise FailureAblationError("variant_set_invalid")
    runs = {
        name: _load_run(path, expected_variant=name)
        for name, path in run_paths.items()
    }
    keys = (
        "model_contract_hash",
        "input_packet_hash",
        "budget_contract_hash",
        "figure_family",
    )
    if any(
        any(not runs[name].get(key) for name in VARIANTS)
        or len({runs[name][key] for name in VARIANTS}) != 1
        for key in keys
    ):
        raise FailureAblationError("comparison_contract_mismatch")

    variants = {name: _summarize_run(runs[name]) for name in sorted(VARIANTS)}
    raw = variants["raw"]
    verified = variants["verified"]
    repaired = variants["repaired"]
    scientific_pass = all(
        item["scientific_gate"] == "passed" for item in variants.values()
    )
    human_complete = all(
        item["human_verdict_state"] == "recorded" for item in variants.values()
    )
    return {
        "schema": REPORT_SCHEMA,
        "variants": variants,
        "deltas": {
            "verified_vs_raw": _delta(verified, raw),
            "repaired_vs_raw": _delta(repaired, raw),
        },
        "product_claim": (
            "review_eligible" if scientific_pass and human_complete else "not_authorized"
        ),
        "publication_acceptance": "not_claimed",
    }
