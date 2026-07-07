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
from pathlib import Path
from typing import Any

import yaml

CHECKS_DIR = Path(__file__).resolve().parent / "checks"
sys.path.insert(0, str(CHECKS_DIR))

from check_visual_clash import extract_pdf_words_and_page  # noqa: E402

SCHEMA = "figure-agent.semantic-assertions.v1"
RELATIONS = ("above", "below", "left_of", "right_of")
DEFAULT_TOLERANCE_PT = 2.0


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
                raise SemanticAssertionError(
                    f"semantic_assertions[{index}].tolerance_pt must be > 0"
                )
            parsed["tolerance_pt"] = float(tolerance)
        assertions.append(parsed)
    return assertions


def _center(word: dict[str, Any]) -> tuple[float, float]:
    return (word["xmin"] + word["xmax"]) / 2.0, (word["ymin"] + word["ymax"]) / 2.0


def _find(words: list[dict[str, Any]], token: str) -> dict[str, Any] | None:
    token_lower = token.lower()
    for word in words:
        if word["text"].lower() == token_lower:
            return word
    for word in words:
        if token_lower in word["text"].lower():
            return word
    return None


def _signed_margin(relation: str, sx: float, sy: float, rx: float, ry: float) -> float:
    """Signed margin along the relevant axis; positive when the relation holds."""
    if relation == "above":
        return ry - sy
    if relation == "below":
        return sy - ry
    if relation == "left_of":
        return rx - sx
    return sx - rx  # right_of


def check_semantic_assertions(
    words: list[dict[str, Any]], assertions: list[dict[str, Any]]
) -> list[dict[str, str]]:
    """Return one issue per assertion that is violated, indeterminate, or anchor-missing.

    The margin is signed along the relevant axis (positive when the relation holds).
    Within ``tolerance_pt`` of zero the relation is too close to call between
    local-native and Docker renders, so it is reported as ``indeterminate``
    (report-only, distinct from ``violated``).
    """
    issues: list[dict[str, str]] = []
    for assertion in assertions:
        subject = _find(words, assertion["subject"])
        reference = _find(words, assertion["reference"])
        if subject is None or reference is None:
            missing = assertion["subject"] if subject is None else assertion["reference"]
            issues.append(
                {
                    "id": assertion["id"],
                    "status": "anchor_missing",
                    "message": f"assertion {assertion['id']!r}: text anchor {missing!r} not found",
                }
            )
            continue
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


def semantic_assertions_payload(
    pdf_path: Path, issues: list[dict[str, str]], assertion_count: int
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "render_pdf": f"build/{pdf_path.name}",
        "checked": assertion_count,
        "issues": issues,
        "total": len(issues),
    }


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
