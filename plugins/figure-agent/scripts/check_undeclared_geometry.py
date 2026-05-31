#!/usr/bin/env python3
"""Detect TikZ geometry that is not covered by declared audit checks."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from check_visual_clash import extract_pdf_words_and_page

SCHEMA = "figure-agent.undeclared-geometry.v1"
CM_TO_PT = 72.0 / 2.54
DEFAULT_NEAR_MISS_PT = 4.0
_POINT_RE = r"\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)"
_RECT_RE = re.compile(rf"{_POINT_RE}\s*rectangle\s*{_POINT_RE}")
_SEGMENT_RE = re.compile(rf"{_POINT_RE}\s*--\s*{_POINT_RE}")


class UndeclaredGeometryError(ValueError):
    """Controlled error for malformed undeclared-geometry inputs."""


def _cm_to_pt(value: float | int) -> float:
    return round(float(value) * CM_TO_PT, 6)


def _bbox_cm_to_pt(values: list[float]) -> list[float]:
    x0, y0, x1, y1 = values
    return [
        min(_cm_to_pt(x0), _cm_to_pt(x1)),
        min(_cm_to_pt(y0), _cm_to_pt(y1)),
        max(_cm_to_pt(x0), _cm_to_pt(x1)),
        max(_cm_to_pt(y0), _cm_to_pt(y1)),
    ]


def _line_pt(values: tuple[float, float, float, float]) -> dict[str, Any]:
    x0, y0, x1, y1 = values
    if abs(x0 - x1) < 0.03:
        return {
            "kind": "vertical_line",
            "x": _cm_to_pt(x0),
            "y_range": sorted([_cm_to_pt(y0), _cm_to_pt(y1)]),
        }
    return {
        "kind": "horizontal_line",
        "y": _cm_to_pt(y0),
        "x_range": sorted([_cm_to_pt(x0), _cm_to_pt(x1)]),
    }


def _parse_tikz_geometry(tex_text: str) -> list[dict[str, Any]]:
    geometry: list[dict[str, Any]] = []
    for line_no, line in enumerate(tex_text.splitlines(), start=1):
        if line.lstrip().startswith("%"):
            continue
        for match in _RECT_RE.finditer(line):
            x0, y0, x1, y1 = (float(value) for value in match.groups())
            geometry.append(
                {
                    "kind": "rect",
                    "bbox_pt": _bbox_cm_to_pt([x0, y0, x1, y1]),
                    "source_line": line_no,
                }
            )
        for match in _SEGMENT_RE.finditer(line):
            x0, y0, x1, y1 = (float(value) for value in match.groups())
            if abs(x0 - x1) < 0.03 and abs(y0 - y1) >= 0.25:
                geometry.append(
                    {
                        "kind": "vertical_line",
                        "line_pt": _line_pt((x0, y0, x1, y1)),
                        "source_line": line_no,
                    }
                )
            elif abs(y0 - y1) < 0.03 and abs(x0 - x1) >= 0.25:
                geometry.append(
                    {
                        "kind": "horizontal_line",
                        "line_pt": _line_pt((x0, y0, x1, y1)),
                        "source_line": line_no,
                    }
                )
    return geometry


def _as_bbox_pt(values: object) -> list[float] | None:
    if (
        not isinstance(values, list)
        or len(values) != 4
        or not all(isinstance(item, int | float) for item in values)
    ):
        return None
    return _bbox_cm_to_pt([float(value) for value in values])


def _ranges_overlap(a: list[float], b: list[float], tolerance: float = 1.5) -> bool:
    return max(a[0], b[0]) <= min(a[1], b[1]) + tolerance


def _almost_equal(a: float, b: float, tolerance: float = 1.5) -> bool:
    return abs(a - b) <= tolerance


def _declared_boundaries(spec: dict[str, Any]) -> list[dict[str, Any]]:
    checks = spec.get("text_boundary_checks")
    if not isinstance(checks, list):
        return []
    declared: list[dict[str, Any]] = []
    for check in checks:
        if not isinstance(check, dict):
            continue
        kind = check.get("kind")
        if kind == "rect":
            bbox = _as_bbox_pt(check.get("bbox_pdf_cm"))
            if bbox is not None:
                declared.append({"kind": "rect", "bbox_pt": bbox})
        elif kind == "vertical_line" and isinstance(check.get("pdf_cm_x"), int | float):
            y_range = check.get("pdf_cm_y_range")
            if (
                isinstance(y_range, list)
                and len(y_range) == 2
                and all(isinstance(item, int | float) for item in y_range)
            ):
                declared.append(
                    {
                        "kind": "vertical_line",
                        "x": _cm_to_pt(check["pdf_cm_x"]),
                        "y_range": sorted([_cm_to_pt(y_range[0]), _cm_to_pt(y_range[1])]),
                    }
                )
        elif kind == "horizontal_line" and isinstance(check.get("pdf_cm_y"), int | float):
            x_range = check.get("pdf_cm_x_range")
            if (
                isinstance(x_range, list)
                and len(x_range) == 2
                and all(isinstance(item, int | float) for item in x_range)
            ):
                declared.append(
                    {
                        "kind": "horizontal_line",
                        "y": _cm_to_pt(check["pdf_cm_y"]),
                        "x_range": sorted([_cm_to_pt(x_range[0]), _cm_to_pt(x_range[1])]),
                    }
                )
    return declared


def _is_declared(geometry: dict[str, Any], declared: list[dict[str, Any]]) -> bool:
    for item in declared:
        if geometry["kind"] != item["kind"]:
            continue
        if geometry["kind"] == "rect":
            if all(
                _almost_equal(a, b)
                for a, b in zip(geometry["bbox_pt"], item["bbox_pt"], strict=True)
            ):
                return True
        elif geometry["kind"] == "vertical_line":
            line = geometry["line_pt"]
            if _almost_equal(line["x"], item["x"]) and _ranges_overlap(
                line["y_range"],
                item["y_range"],
            ):
                return True
        elif geometry["kind"] == "horizontal_line":
            line = geometry["line_pt"]
            if _almost_equal(line["y"], item["y"]) and _ranges_overlap(
                line["x_range"],
                item["x_range"],
            ):
                return True
    return False


def _word_bbox(word: dict[str, Any]) -> tuple[float, float, float, float]:
    return (
        float(word["xmin"]),
        float(word["ymin"]),
        float(word["xmax"]),
        float(word["ymax"]),
    )


def _point_rect_distance(
    x: float,
    y: float,
    rect: tuple[float, float, float, float],
) -> float:
    x0, y0, x1, y1 = rect
    dx = max(x0 - x, 0.0, x - x1)
    dy = max(y0 - y, 0.0, y - y1)
    return math.hypot(dx, dy)


def _segment_rect_distance(line: dict[str, Any], word: dict[str, Any]) -> float:
    x0, y0, x1, y1 = _word_bbox(word)
    if line["kind"] == "vertical_line":
        x = float(line["x"])
        y_start, y_end = line["y_range"]
        y = min(max((y0 + y1) / 2.0, y_start), y_end)
        return _point_rect_distance(x, y, (x0, y0, x1, y1))
    y = float(line["y"])
    x_start, x_end = line["x_range"]
    x = min(max((x0 + x1) / 2.0, x_start), x_end)
    return _point_rect_distance(x, y, (x0, y0, x1, y1))


def _base_candidate(
    *,
    kind: str,
    evidence: str,
    bbox_pt: list[float],
    source_line: int,
    nearest_text: str = "",
    distance_pt: float | None = None,
    recommended_action: str = "add_spec_check",
) -> dict[str, Any]:
    return {
        "kind": kind,
        "evidence": evidence,
        "bbox_pt": [round(value, 6) for value in bbox_pt],
        "source_line": source_line,
        "nearest_text": nearest_text,
        "distance_pt": None if distance_pt is None else round(distance_pt, 6),
        "recommended_action": recommended_action,
    }


def detect_undeclared_geometry(
    tex_text: str,
    words: list[dict[str, Any]],
    spec: dict[str, Any] | None,
    *,
    near_miss_pt: float = DEFAULT_NEAR_MISS_PT,
) -> list[dict[str, Any]]:
    """Return deterministic undeclared geometry and near-miss candidates."""
    spec = spec or {}
    declared = _declared_boundaries(spec)
    candidates: list[dict[str, Any]] = []
    for geometry in _parse_tikz_geometry(tex_text):
        if _is_declared(geometry, declared):
            continue
        if geometry["kind"] == "rect":
            candidates.append(
                _base_candidate(
                    kind="undeclared_rect_boundary",
                    evidence=(
                        f"source line {geometry['source_line']} rectangle "
                        "lacks text_boundary_check"
                    ),
                    bbox_pt=geometry["bbox_pt"],
                    source_line=geometry["source_line"],
                )
            )
            continue
        line = geometry["line_pt"]
        if geometry["kind"] == "vertical_line":
            bbox = [line["x"], line["y_range"][0], line["x"], line["y_range"][1]]
            kind = "undeclared_column_rule"
        else:
            bbox = [line["x_range"][0], line["y"], line["x_range"][1], line["y"]]
            kind = "undeclared_horizontal_rule"
        candidates.append(
            _base_candidate(
                kind=kind,
                evidence=f"source line {geometry['source_line']} line lacks text_boundary_check",
                bbox_pt=bbox,
                source_line=geometry["source_line"],
            )
        )
        for word in words:
            distance = _segment_rect_distance(line, word)
            if 0 < distance <= near_miss_pt:
                candidates.append(
                    _base_candidate(
                        kind="label_endpoint_near_miss",
                        evidence=(
                            f"source line {geometry['source_line']} is within "
                            f"{distance:.2f} pt of text {word.get('text', '')!r}"
                        ),
                        bbox_pt=bbox,
                        source_line=geometry["source_line"],
                        nearest_text=str(word.get("text", "")),
                        distance_pt=distance,
                        recommended_action="add_micro_defect",
                    )
                )
    kind_rank = {
        "undeclared_rect_boundary": 0,
        "undeclared_column_rule": 0,
        "undeclared_horizontal_rule": 0,
        "label_endpoint_near_miss": 1,
        "undeclared_path_near_label": 1,
        "low_clearance_inside_boundary": 1,
    }
    candidates.sort(
        key=lambda item: (
            item["source_line"],
            kind_rank.get(item["kind"], 99),
            item["kind"],
            item["nearest_text"],
        )
    )
    for index, candidate in enumerate(candidates, start=1):
        candidate["id"] = f"UG{index:03d}"
    return candidates


def undeclared_geometry_payload(pdf_path: Path, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    fixture_dir = pdf_path.parent.parent
    fixture_name = fixture_dir.name or Path.cwd().name
    return {
        "schema": SCHEMA,
        "fixture": fixture_name,
        "render_pdf": f"build/{pdf_path.name}",
        "source": "tikz-source:auto-discovery",
        "candidates": candidates,
        "total": len(candidates),
    }


def _load_spec(spec_path: Path) -> dict[str, Any]:
    if not spec_path.is_file():
        return {}
    try:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise UndeclaredGeometryError(f"malformed spec.yaml: {exc}") from exc
    if spec is None:
        return {}
    if not isinstance(spec, dict):
        raise UndeclaredGeometryError("spec.yaml must be a mapping")
    return spec


def _infer_tex_path(pdf_path: Path) -> Path:
    fixture_dir = pdf_path.parent.parent
    return fixture_dir / f"{fixture_dir.name}.tex"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="build/<name>.pdf")
    parser.add_argument("--tex", type=Path, default=None)
    parser.add_argument("--spec", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    try:
        pdf_path = args.pdf
        tex_path = args.tex or _infer_tex_path(pdf_path)
        spec_path = args.spec or pdf_path.parent.parent / "spec.yaml"
        if not tex_path.is_file():
            raise UndeclaredGeometryError(f"missing TeX source: {tex_path}")
        words, _page_size = extract_pdf_words_and_page(pdf_path)
        candidates = detect_undeclared_geometry(
            tex_path.read_text(encoding="utf-8"),
            words,
            _load_spec(spec_path),
        )
        payload = undeclared_geometry_payload(pdf_path, candidates)
        output = args.json_output or pdf_path.parent / "undeclared_geometry.json"
        _write_json(output, payload)
    except (UndeclaredGeometryError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for candidate in candidates:
        print(
            f"WARN {candidate['kind']}: {candidate['id']} "
            f"text={candidate['nearest_text']!r} distance={candidate['distance_pt']}",
            file=sys.stderr,
        )
    if candidates:
        print(f"{len(candidates)} undeclared geometry candidate(s)", file=sys.stderr)
    if args.strict and candidates:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
