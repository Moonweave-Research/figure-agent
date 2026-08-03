#!/usr/bin/env python3
"""Opt-in rendered-vector checks for finite-width member silhouettes."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pdfplumber
import yaml
from svgpathtools import CubicBezier, Line

SCHEMA = "figure-agent.silhouette-morphology.v1"
CM_TO_PT = 72.0 / 2.54


class SilhouetteMorphologyError(ValueError):
    """Raised when a declared rendered silhouette cannot be analyzed safely."""


def _point(raw: tuple[float, float]) -> complex:
    return complex(float(raw[0]), float(raw[1]))


def parse_segments(raw_path: list[tuple]) -> list[CubicBezier | Line]:
    segments: list[CubicBezier | Line] = []
    current: complex | None = None
    start: complex | None = None
    for command in raw_path:
        kind = command[0]
        if kind == "m":
            current = _point(command[1])
            start = current
        elif kind == "c" and current is not None:
            segment = CubicBezier(
                current,
                _point(command[1]),
                _point(command[2]),
                _point(command[3]),
            )
            segments.append(segment)
            current = segment.end
        elif kind == "l" and current is not None:
            segment = Line(current, _point(command[1]))
            segments.append(segment)
            current = segment.end
        elif kind == "h" and current is not None and start is not None:
            segments.append(Line(current, start))
            current = start
        else:
            raise SilhouetteMorphologyError(f"unsupported_path_command:{kind}")
    if not segments:
        raise SilhouetteMorphologyError("empty_curve_path")
    return segments


def _self_intersections(segments: list[CubicBezier | Line]) -> list[complex]:
    intersections: dict[tuple[float, float], complex] = {}
    final_index = len(segments) - 1
    for left_index, left in enumerate(segments):
        for right_index in range(left_index + 1, len(segments)):
            right = segments[right_index]
            for left_t, right_t in left.intersect(right):
                adjacent_join = (
                    right_index == left_index + 1
                    and math.isclose(float(left_t), 1.0, abs_tol=1e-7)
                    and math.isclose(float(right_t), 0.0, abs_tol=1e-7)
                )
                closure_join = (
                    left_index == 0
                    and right_index == final_index
                    and math.isclose(float(left_t), 0.0, abs_tol=1e-7)
                    and math.isclose(float(right_t), 1.0, abs_tol=1e-7)
                )
                if adjacent_join or closure_join:
                    continue
                point = left.point(left_t)
                intersections[(round(point.real, 4), round(point.imag, 4))] = point
    return list(intersections.values())


def _edge_metrics(segments: list[CubicBezier | Line]) -> dict[str, float]:
    cubic_segments = [segment for segment in segments if isinstance(segment, CubicBezier)]
    if len(cubic_segments) < 3:
        raise SilhouetteMorphologyError("three_cubic_segments_required")
    first, second = sorted(cubic_segments, key=lambda segment: segment.length(), reverse=True)[:2]
    same_orientation = abs(first.start - second.start) + abs(first.end - second.end)
    reverse_orientation = abs(first.start - second.end) + abs(first.end - second.start)
    reverse_second = reverse_orientation < same_orientation
    sample_positions = [index / 20.0 for index in range(2, 19)]
    widths = [
        abs(first.point(t) - second.point(1.0 - t if reverse_second else t))
        for t in sample_positions
    ]
    widths_sorted = sorted(widths)
    median_width = widths_sorted[len(widths_sorted) // 2]
    mean_edge_length = (first.length() + second.length()) / 2.0
    minimum_width = min(widths)
    maximum_width = max(widths)
    return {
        "median_width_pt": median_width,
        "minimum_width_pt": minimum_width,
        "maximum_width_pt": maximum_width,
        "mean_edge_length_pt": mean_edge_length,
        "width_to_length_ratio": median_width / mean_edge_length,
        "width_variation_ratio": maximum_width / max(minimum_width, 1e-9),
    }


def analyze_curve(
    curve: dict[str, Any],
    *,
    max_width_to_length_ratio: float,
    max_width_variation_ratio: float,
) -> dict[str, Any]:
    segments = parse_segments(curve["path"])
    intersections = _self_intersections(segments)
    metrics = {
        "self_intersection_count": len(intersections),
        **_edge_metrics(segments),
    }
    violations: list[str] = []
    if intersections:
        violations.append("self_intersection")
    if metrics["width_to_length_ratio"] > max_width_to_length_ratio:
        violations.append("width_to_length_ratio")
    if metrics["width_variation_ratio"] > max_width_variation_ratio:
        violations.append("width_variation_ratio")
    return {"metrics": metrics, "violations": violations}


def _color_distance(left: object, right: list[float]) -> float:
    if not isinstance(left, (list, tuple)) or len(left) != 3:
        return math.inf
    return math.sqrt(sum((float(left[index]) - right[index]) ** 2 for index in range(3)))


def select_curve(
    curves: list[dict[str, Any]],
    *,
    bbox_pt: list[float],
    stroke_rgb: list[float],
    color_tolerance: float,
) -> dict[str, Any]:
    left, top, right, bottom = bbox_pt
    candidates = []
    for curve in curves:
        center_x = (float(curve["x0"]) + float(curve["x1"])) / 2.0
        center_y = (float(curve["top"]) + float(curve["bottom"])) / 2.0
        if not (left <= center_x <= right and top <= center_y <= bottom):
            continue
        if curve.get("fill") is not True:
            continue
        if _color_distance(curve.get("stroking_color"), stroke_rgb) > color_tolerance:
            continue
        candidates.append(curve)
    if not candidates:
        raise SilhouetteMorphologyError("target_curve_missing")
    candidates.sort(
        key=lambda curve: (float(curve["x1"]) - float(curve["x0"]))
        * (float(curve["bottom"]) - float(curve["top"])),
        reverse=True,
    )
    return candidates[0]


def check_pdf(pdf_path: Path, spec_path: Path) -> dict[str, Any]:
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    checks = spec.get("silhouette_morphology_checks") or []
    if not isinstance(checks, list):
        raise SilhouetteMorphologyError("silhouette_checks_must_be_list")
    results: list[dict[str, Any]] = []
    with pdfplumber.open(pdf_path) as document:
        if len(document.pages) != 1:
            raise SilhouetteMorphologyError("single_page_pdf_required")
        curves = document.pages[0].curves
        for check in checks:
            if not isinstance(check, dict):
                raise SilhouetteMorphologyError("silhouette_check_must_be_mapping")
            bbox_cm = check.get("bbox_pdf_cm")
            stroke_rgb = check.get("stroke_rgb")
            if not isinstance(bbox_cm, list) or len(bbox_cm) != 4:
                raise SilhouetteMorphologyError("bbox_pdf_cm_invalid")
            if not isinstance(stroke_rgb, list) or len(stroke_rgb) != 3:
                raise SilhouetteMorphologyError("stroke_rgb_invalid")
            curve = select_curve(
                curves,
                bbox_pt=[float(value) * CM_TO_PT for value in bbox_cm],
                stroke_rgb=[float(value) for value in stroke_rgb],
                color_tolerance=float(check.get("color_tolerance", 0.03)),
            )
            analysis = analyze_curve(
                curve,
                max_width_to_length_ratio=float(
                    check.get("max_width_to_length_ratio", 0.20)
                ),
                max_width_variation_ratio=float(
                    check.get("max_width_variation_ratio", 3.0)
                ),
            )
            results.append({"id": str(check.get("id", "unnamed")), **analysis})
    violation_count = sum(len(result["violations"]) for result in results)
    return {
        "schema": SCHEMA,
        "render_pdf": pdf_path.as_posix(),
        "source": "spec.yaml:silhouette_morphology_checks",
        "checked": len(results),
        "violation_count": violation_count,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    payload = check_pdf(args.pdf, args.spec)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if payload["violation_count"]:
        for result in payload["results"]:
            for violation in result["violations"]:
                print(f"WARN silhouette_morphology: {result['id']} {violation}")
    else:
        print(f"OK: {payload['checked']} silhouette morphology check(s) passed")
    return 1 if args.strict and payload["violation_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
