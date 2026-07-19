#!/usr/bin/env python3
"""Check declared horizontal state fields for accidental density-envelope grammar.

The check is opt-in through ``state_field_geometry_assertions`` in a fixture
``spec.yaml``.  It does not prescribe an illustration: it only verifies the
minimum visible grammar a fixture already declares for a horizontal-state-mark
field.  In particular, a field whose marks systematically widen toward the
vertical midpoint is flagged because it reads as a symmetric fitted density
silhouette rather than a qualitative collection of state marks.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from statistics import pstdev
from typing import Any

import yaml

SCHEMA = "figure-agent.state-field-geometry.v1"
_OBJECT_BLOCK_RE = re.compile(
    r"fig-agent:start\s+object=(?P<object>[A-Za-z0-9_-]+).*?"
    r"fig-agent:end\s+object=(?P=object)",
    re.DOTALL,
)
_FOREACH_TRIPLES_RE = re.compile(
    r"\\foreach\s+\\[A-Za-z]+/\\[A-Za-z]+/\\[A-Za-z]+\s+in\s*\{(?P<values>.*?)\}",
    re.DOTALL,
)
_TRIPLE_RE = re.compile(
    r"(?P<y>-?\d+(?:\.\d+)?)/(?P<x>-?\d+(?:\.\d+)?)/(?P<length>\d+(?:\.\d+)?)"
)


class StateFieldGeometryError(ValueError):
    """Raised for malformed geometry assertions or unparseable state fields."""


def _pearson(values_a: list[float], values_b: list[float]) -> float:
    mean_a = sum(values_a) / len(values_a)
    mean_b = sum(values_b) / len(values_b)
    numerator = sum((a - mean_a) * (b - mean_b) for a, b in zip(values_a, values_b))
    denominator = math.sqrt(
        sum((a - mean_a) ** 2 for a in values_a) * sum((b - mean_b) ** 2 for b in values_b)
    )
    return 0.0 if denominator == 0.0 else numerator / denominator


def evaluate_state_field(
    marks: list[tuple[float, float, float]],
    *,
    min_marks: int,
    min_vertical_span_cm: float,
    min_center_std_cm: float,
    max_width_abs_midpoint_correlation: float,
) -> dict[str, Any]:
    """Evaluate a state-mark field without prescribing its composition or palette."""
    if min_marks < 2:
        raise StateFieldGeometryError("min_marks must be at least 2")
    if min_vertical_span_cm <= 0.0:
        raise StateFieldGeometryError("min_vertical_span_cm must be > 0")
    if min_center_std_cm < 0.0:
        raise StateFieldGeometryError("min_center_std_cm must be >= 0")
    if not -1.0 <= max_width_abs_midpoint_correlation <= 1.0:
        raise StateFieldGeometryError(
            "max_width_abs_midpoint_correlation must be between -1 and 1"
        )
    if not marks:
        return {
            "status": "violated",
            "metrics": {"mark_count": 0},
            "violations": ["state_field_marks_missing"],
        }

    ordered = sorted(marks)
    ys = [mark[0] for mark in ordered]
    centers = [mark[1] for mark in ordered]
    widths = [mark[2] for mark in ordered]
    vertical_span_cm = max(ys) - min(ys)
    midpoint = (max(ys) + min(ys)) / 2.0
    width_abs_midpoint_correlation = _pearson(widths, [abs(y - midpoint) for y in ys])
    center_std_cm = pstdev(centers) if len(centers) > 1 else 0.0
    violations: list[str] = []
    if len(marks) < min_marks:
        violations.append("insufficient_state_mark_density")
    if vertical_span_cm < min_vertical_span_cm:
        violations.append("insufficient_vertical_energy_support")
    if center_std_cm < min_center_std_cm:
        violations.append("insufficient_irregular_lateral_positions")
    if width_abs_midpoint_correlation < max_width_abs_midpoint_correlation:
        violations.append("symmetric_density_silhouette")
    return {
        "status": "passed" if not violations else "violated",
        "metrics": {
            "mark_count": len(marks),
            "vertical_span_cm": round(vertical_span_cm, 6),
            "center_std_cm": round(center_std_cm, 6),
            "width_abs_midpoint_correlation": round(width_abs_midpoint_correlation, 6),
        },
        "violations": violations,
    }


def _object_block(tex_source: str, object_name: str) -> str:
    for match in _OBJECT_BLOCK_RE.finditer(tex_source):
        if match.group("object") == object_name:
            return match.group(0)
    raise StateFieldGeometryError(f"missing fig-agent object block: {object_name}")


def _horizontal_marks(object_block: str) -> list[tuple[float, float, float]]:
    matches = list(_FOREACH_TRIPLES_RE.finditer(object_block))
    if len(matches) != 1:
        raise StateFieldGeometryError(
            "horizontal_state_field requires exactly one three-value \\foreach declaration"
        )
    return [
        (float(item.group("y")), float(item.group("x")), float(item.group("length")))
        for item in _TRIPLE_RE.finditer(matches[0].group("values"))
    ]


def _read_assertions(spec: dict[str, Any]) -> list[dict[str, Any]]:
    raw_assertions = spec.get("state_field_geometry_assertions", [])
    if raw_assertions is None:
        return []
    if not isinstance(raw_assertions, list):
        raise StateFieldGeometryError("state_field_geometry_assertions must be a list")
    assertions: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_assertions):
        if not isinstance(raw, dict):
            raise StateFieldGeometryError(
                f"state_field_geometry_assertions[{index}] must be a mapping"
            )
        assertion_id = raw.get("id")
        object_name = raw.get("source_object")
        if not isinstance(assertion_id, str) or not assertion_id.strip():
            raise StateFieldGeometryError(
                f"state_field_geometry_assertions[{index}].id is required"
            )
        if not isinstance(object_name, str) or not object_name.strip():
            raise StateFieldGeometryError(
                f"state_field_geometry_assertions[{index}].source_object is required"
            )
        if raw.get("kind") != "horizontal_state_field":
            raise StateFieldGeometryError(
                f"state_field_geometry_assertions[{index}].kind must be horizontal_state_field"
            )
        try:
            parsed = {
                "id": assertion_id.strip(),
                "source_object": object_name.strip(),
                "min_marks": int(raw["min_marks"]),
                "min_vertical_span_cm": float(raw["min_vertical_span_cm"]),
                "min_center_std_cm": float(raw["min_center_std_cm"]),
                "max_width_abs_midpoint_correlation": float(
                    raw["max_width_abs_midpoint_correlation"]
                ),
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise StateFieldGeometryError(
                f"state_field_geometry_assertions[{index}] has invalid thresholds"
            ) from exc
        thresholds = {
            key: parsed[key] for key in parsed if key not in {"id", "source_object"}
        }
        evaluate_state_field([], **thresholds)
        assertions.append(parsed)
    return assertions


def state_field_geometry_payload(tex_path: Path, spec_path: Path) -> dict[str, Any]:
    try:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise StateFieldGeometryError(f"unreadable spec: {spec_path}: {exc}") from exc
    if not isinstance(spec, dict):
        raise StateFieldGeometryError("spec.yaml must be a mapping")
    tex_source = tex_path.read_text(encoding="utf-8")
    results: list[dict[str, Any]] = []
    for assertion in _read_assertions(spec):
        marks = _horizontal_marks(_object_block(tex_source, assertion["source_object"]))
        result = evaluate_state_field(
            marks,
            min_marks=assertion["min_marks"],
            min_vertical_span_cm=assertion["min_vertical_span_cm"],
            min_center_std_cm=assertion["min_center_std_cm"],
            max_width_abs_midpoint_correlation=assertion[
                "max_width_abs_midpoint_correlation"
            ],
        )
        results.append(
            {"id": assertion["id"], "source_object": assertion["source_object"], **result}
        )
    return {
        "schema": SCHEMA,
        "source_tex": str(tex_path),
        "spec": str(spec_path),
        "checked": len(results),
        "issues": [result for result in results if result["status"] != "passed"],
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tex", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = state_field_geometry_payload(args.tex, args.spec)
    except StateFieldGeometryError as exc:
        print(f"ERROR: {exc}")
        return 2
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for issue in payload["issues"]:
        print(f"WARN state_field_geometry: {issue['id']}: {', '.join(issue['violations'])}")
    return 1 if args.strict and payload["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
