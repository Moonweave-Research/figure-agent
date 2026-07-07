#!/usr/bin/env python3
"""Deterministic figure-vs-claim spatial assertion check (report-only WARN).

The relational/directional facts a figure asserts — a shallow trap sits ABOVE a
deep trap, a +V cantilever deflects opposite a -V one, curve P stays above curve
Q — are invisible to geometric clash detectors yet are the highest-stakes silent
errors (a reversed relation is a wrong figure no detector catches). A fixture may
declare the deterministically-checkable ones in spec.yaml; this checker verifies
each against the rendered text geometry.

spec.yaml::

    semantic_assertions:
      - id: shallow-above-deep
        relation: above        # above | below | left_of | right_of
        subject: shallow       # a distinctive label token to locate
        reference: deep

Coordinates are pdftotext bbox points (origin top-left, y increases downward), so
"above" means the subject's centre sits at a smaller y than the reference's.
Report-only by default; --strict exits non-zero on any violation or missing anchor.
"""

from __future__ import annotations

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml

CHECKS_DIR = Path(__file__).resolve().parent / "checks"
sys.path.insert(0, str(CHECKS_DIR))

from check_visual_clash import extract_pdf_words_and_page  # noqa: E402

SCHEMA = "figure-agent.semantic-assertions.v1"
RELATIONS = ("above", "below", "left_of", "right_of")
ALIGNMENT_KINDS = (
    "baseline_aligned",
    "top_aligned",
    "left_aligned",
    "right_aligned",
    "center_aligned_x",
    "center_aligned_y",
)
DEFAULT_TOLERANCE_PT = 2.0
DEFAULT_ALIGNMENT_TOLERANCE_CM = 0.05
PT_PER_CM = 72.0 / 2.54


class SemanticAssertionError(ValueError):
    """Raised when declared semantic_assertions are malformed."""


def parse_assertions(spec: dict[str, Any]) -> list[dict[str, Any]]:
    raw = spec.get("semantic_assertions")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise SemanticAssertionError("semantic_assertions must be a list")
    assertions: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise SemanticAssertionError(f"semantic_assertions[{index}] must be a mapping")
        if "kind" in item:
            assertions.append(_parse_alignment_assertion(item, index))
            continue
        assertions.append(_parse_relation_assertion(item, index))
    return assertions


def _parse_relation_assertion(item: dict[str, Any], index: int) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for field in ("id", "relation", "subject", "reference"):
        value = item.get(field)
        if not isinstance(value, str) or not value.strip():
            raise SemanticAssertionError(f"semantic_assertions[{index}].{field} is required")
        parsed[field] = value.strip()
    if parsed["relation"] not in RELATIONS:
        raise SemanticAssertionError(
            f"semantic_assertions[{index}].relation must be one of {RELATIONS}"
        )
    if "tolerance_pt" in item:
        tolerance = item["tolerance_pt"]
        if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
            raise SemanticAssertionError(
                f"semantic_assertions[{index}].tolerance_pt must be a number"
            )
        if tolerance <= 0:
            raise SemanticAssertionError(f"semantic_assertions[{index}].tolerance_pt must be > 0")
        parsed["tolerance_pt"] = float(tolerance)
    return parsed


def _parse_alignment_assertion(item: dict[str, Any], index: int) -> dict[str, Any]:
    assertion_id = item.get("id")
    if not isinstance(assertion_id, str) or not assertion_id.strip():
        raise SemanticAssertionError(f"semantic_assertions[{index}].id is required")
    kind = item.get("kind")
    if not isinstance(kind, str) or not kind.strip():
        raise SemanticAssertionError(f"semantic_assertions[{index}].kind is required")
    kind = kind.strip()
    if kind not in ALIGNMENT_KINDS:
        raise SemanticAssertionError(
            f"semantic_assertions[{index}].kind must be one of {ALIGNMENT_KINDS}"
        )
    targets = item.get("targets")
    if (
        not isinstance(targets, list)
        or len(targets) < 2
        or any(not isinstance(target, str) or not target.strip() for target in targets)
    ):
        raise SemanticAssertionError(
            f"semantic_assertions[{index}].targets must be a list of 2+ strings"
        )
    tolerance_cm = item.get("tolerance_cm", DEFAULT_ALIGNMENT_TOLERANCE_CM)
    if isinstance(tolerance_cm, bool) or not isinstance(tolerance_cm, (int, float)):
        raise SemanticAssertionError(f"semantic_assertions[{index}].tolerance_cm must be a number")
    if tolerance_cm <= 0:
        raise SemanticAssertionError(f"semantic_assertions[{index}].tolerance_cm must be > 0")
    return {
        "id": assertion_id.strip(),
        "kind": kind,
        "targets": [target.strip() for target in targets],
        "tolerance_cm": float(tolerance_cm),
        **_optional_string_field(item, "target_panel"),
    }


def _optional_string_field(item: dict[str, Any], field: str) -> dict[str, str]:
    if field not in item:
        return {}
    value = item[field]
    if not isinstance(value, str) or not value.strip():
        raise SemanticAssertionError(f"semantic_assertions[].{field} must be a string")
    return {field: value.strip()}


def _center(word: dict[str, Any]) -> tuple[float, float]:
    return (word["xmin"] + word["xmax"]) / 2.0, (word["ymin"] + word["ymax"]) / 2.0


def _find_matches(words: list[dict[str, Any]], token: str) -> list[dict[str, Any]]:
    token_lower = token.lower()
    exact = [word for word in words if word["text"].lower() == token_lower]
    if exact:
        return exact
    return [word for word in words if token_lower in word["text"].lower()]


def _resolve_word(
    words: list[dict[str, Any]], assertion_id: str, anchor: str
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    matches = _find_matches(words, anchor)
    if not matches:
        return None, {
            "id": assertion_id,
            "status": "anchor_missing",
            "anchor": anchor,
            "message": f"assertion {assertion_id!r}: text anchor {anchor!r} not found",
        }
    if len(matches) > 1:
        return None, {
            "id": assertion_id,
            "status": "anchor_ambiguous",
            "anchor": anchor,
            "match_count": len(matches),
            "message": (
                f"assertion {assertion_id!r}: text anchor {anchor!r} matched "
                f"{len(matches)} words"
            ),
        }
    return matches[0], None


def _signed_margin(relation: str, sx: float, sy: float, rx: float, ry: float) -> float:
    """Signed margin along the relevant axis; positive when the relation holds."""
    if relation == "above":
        return ry - sy
    if relation == "below":
        return sy - ry
    if relation == "left_of":
        return rx - sx
    return sx - rx  # right_of


def _alignment_metric(kind: str, word: dict[str, Any]) -> float:
    if kind == "baseline_aligned":
        return float(word["ymax"])
    if kind == "top_aligned":
        return float(word["ymin"])
    if kind == "left_aligned":
        return float(word["xmin"])
    if kind == "right_aligned":
        return float(word["xmax"])
    if kind == "center_aligned_x":
        return _center(word)[0]
    if kind == "center_aligned_y":
        return _center(word)[1]
    raise SemanticAssertionError(f"unsupported alignment kind: {kind}")


def _unique_alignment_outlier(
    targets: list[str],
    values: list[float],
    tolerance_pt: float,
) -> str | None:
    candidates: list[str] = []
    for index, value in enumerate(values):
        others = values[:index] + values[index + 1 :]
        if max(others) - min(others) > tolerance_pt:
            continue
        consensus = sum(others) / len(others)
        if abs(value - consensus) > tolerance_pt:
            candidates.append(targets[index])
    return candidates[0] if len(candidates) == 1 else None


def check_semantic_assertions(
    words: list[dict[str, Any]], assertions: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return one issue per assertion that is violated, indeterminate, or anchor-missing.

    The margin is signed along the relevant axis (positive when the relation holds).
    Within ``tolerance_pt`` of zero the relation is too close to call between
    local-native and Docker renders, so it is reported as ``indeterminate``
    (report-only, distinct from ``violated``).
    """
    issues: list[dict[str, Any]] = []
    for assertion in assertions:
        if "kind" in assertion:
            issues.extend(_check_alignment_assertion(words, assertion))
            continue
        subject, subject_issue = _resolve_word(words, assertion["id"], assertion["subject"])
        if subject_issue is not None:
            issues.append(subject_issue)
            continue
        reference, reference_issue = _resolve_word(words, assertion["id"], assertion["reference"])
        if reference_issue is not None:
            issues.append(reference_issue)
            continue
        assert subject is not None and reference is not None
        sx, sy = _center(subject)
        rx, ry = _center(reference)
        relation = assertion["relation"]
        tolerance = assertion.get("tolerance_pt", DEFAULT_TOLERANCE_PT)
        margin = _signed_margin(relation, sx, sy, rx, ry)
        if abs(margin) < tolerance:
            issues.append(
                {
                    "id": assertion["id"],
                    "status": "indeterminate",
                    "message": (
                        f"assertion {assertion['id']!r} indeterminate: "
                        f"{assertion['subject']!r} vs {assertion['reference']!r} "
                        f"margin {margin:.2f}pt within tolerance {tolerance:.2f}pt for {relation}"
                    ),
                }
            )
        elif margin <= 0:
            issues.append(
                {
                    "id": assertion["id"],
                    "status": "violated",
                    "message": (
                        f"assertion {assertion['id']!r} violated: "
                        f"{assertion['subject']!r} is not {relation} {assertion['reference']!r}"
                    ),
                }
            )
    return issues


def _check_alignment_assertion(
    words: list[dict[str, Any]], assertion: dict[str, Any]
) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for target in assertion["targets"]:
        word, issue = _resolve_word(words, assertion["id"], target)
        if issue is not None:
            return [issue]
        assert word is not None
        resolved.append(word)
    kind = assertion["kind"]
    values = [_alignment_metric(kind, word) for word in resolved]
    measured_delta_pt = max(values) - min(values)
    tolerance_cm = float(assertion.get("tolerance_cm", DEFAULT_ALIGNMENT_TOLERANCE_CM))
    tolerance_pt = tolerance_cm * PT_PER_CM
    if measured_delta_pt <= tolerance_pt:
        return []
    measured_delta_cm = measured_delta_pt / PT_PER_CM
    issue: dict[str, Any] = {
        "id": assertion["id"],
        "status": "violated",
        "kind": kind,
        "targets": list(assertion["targets"]),
        "measured_delta_pt": measured_delta_pt,
        "measured_delta_cm": measured_delta_cm,
        "tolerance_pt": tolerance_pt,
        "tolerance_cm": tolerance_cm,
        "message": (
            f"assertion {assertion['id']!r} violated: {kind} delta "
            f"{measured_delta_pt:.2f}pt ({measured_delta_cm:.3f}cm) exceeds "
            f"tolerance {tolerance_pt:.2f}pt ({tolerance_cm:.3f}cm)"
        ),
    }
    edit_target = _unique_alignment_outlier(list(assertion["targets"]), values, tolerance_pt)
    if edit_target is not None:
        issue["edit_target"] = edit_target
    if "target_panel" in assertion:
        issue["target_panel"] = assertion["target_panel"]
    return [
        issue
    ]


def _hash_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _source_hashes_for_pdf(pdf_path: Path) -> dict[str, str]:
    name = pdf_path.stem
    source = pdf_path.parent.parent / f"{name}.tex"
    if not source.is_file():
        return {}
    return {f"examples/{name}/{name}.tex": _hash_file(source)}


def semantic_assertions_payload(
    pdf_path: Path,
    issues: list[dict[str, Any]],
    assertion_count: int,
    source_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema": SCHEMA,
        "render_pdf": f"build/{pdf_path.name}",
        "checked": assertion_count,
        "issues": issues,
        "total": len(issues),
    }
    hashes = source_hashes if source_hashes is not None else _source_hashes_for_pdf(pdf_path)
    if hashes:
        payload["source_hashes"] = hashes
    return payload


def _load_spec(spec_path: Path) -> dict[str, Any]:
    # A missing spec.yaml means no assertions were declared (e.g. an ad-hoc compile
    # with no fixture) -> nothing to check. But a spec that IS present yet cannot be
    # read as a mapping is corrupt evidence: fail closed instead of silently treating
    # it as an empty declaration.
    if not spec_path.is_file():
        return {}
    try:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise SemanticAssertionError(f"unreadable spec.yaml: {exc}") from exc
    if spec is None:
        return {}
    if not isinstance(spec, dict):
        raise SemanticAssertionError(f"spec.yaml is not a mapping: {spec_path}")
    return spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check declared spatial semantic assertions.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args(argv)

    pdf_path: Path = args.pdf
    if not pdf_path.is_file():
        print(f"ERROR: missing PDF: {pdf_path}", file=sys.stderr)
        return 2
    spec_path = pdf_path.parent.parent / "spec.yaml"
    try:
        assertions = parse_assertions(_load_spec(spec_path))
    except (SemanticAssertionError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if not assertions:
        return 0
    try:
        words, _ = extract_pdf_words_and_page(pdf_path)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    issues = check_semantic_assertions(words, assertions)
    output = args.json_output or pdf_path.parent / "semantic_assertions.json"
    output.write_text(
        json.dumps(
            semantic_assertions_payload(pdf_path, issues, len(assertions)),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    for issue in issues:
        if issue["status"] == "indeterminate":
            print(f"INFO semantic_assertion: {issue['message']}", file=sys.stderr)
        else:
            print(f"WARN semantic_assertion: {issue['message']}", file=sys.stderr)
    strict_issues = [issue for issue in issues if issue["status"] != "indeterminate"]
    if issues:
        print(f"{len(issues)} semantic assertion issue(s)", file=sys.stderr)
        if args.strict and strict_issues:
            return 1
    else:
        print(f"OK: {len(assertions)} semantic assertion(s) hold", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
