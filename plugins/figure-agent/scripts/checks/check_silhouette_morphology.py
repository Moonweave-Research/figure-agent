#!/usr/bin/env python3
"""Opt-in rendered-vector checks for finite-width member silhouettes."""

from __future__ import annotations

import argparse
import hashlib
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    for segment in segments:
        if not isinstance(segment, CubicBezier):
            continue
        pieces = [
            segment.cropped(index / 24.0, (index + 1) / 24.0)
            for index in range(24)
        ]
        for left_index, left_piece in enumerate(pieces):
            for right_piece in pieces[left_index + 2 :]:
                for left_t, _right_t in left_piece.intersect(right_piece):
                    point = left_piece.point(left_t)
                    intersections[(round(point.real, 4), round(point.imag, 4))] = point
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


def analyze_stroked_centerline(
    curve: dict[str, Any],
    *,
    max_width_to_length_ratio: float,
) -> dict[str, Any]:
    segments = parse_segments(curve["path"])
    centerline_length = sum(segment.length() for segment in segments)
    stroke_width = float(curve.get("linewidth") or 0.0)
    start = segments[0].start
    end = segments[-1].end
    intersections = _self_intersections(segments)
    metrics = {
        "self_intersection_count": len(intersections),
        "centerline_length_pt": centerline_length,
        "stroke_width_pt": stroke_width,
        "width_to_length_ratio": stroke_width / max(centerline_length, 1e-9),
        "tip_displacement_x_pt": end.real - start.real,
        "tip_displacement_y_pt": end.imag - start.imag,
    }
    violations: list[str] = []
    if intersections:
        violations.append("self_intersection")
    if metrics["width_to_length_ratio"] > max_width_to_length_ratio:
        violations.append("width_to_length_ratio")
    return {"metrics": metrics, "violations": violations}


def _ratio(values: list[float]) -> float:
    return max(values) / max(min(values), 1e-9)


def analyze_groups(
    results: list[dict[str, Any]], groups: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_id = {str(result["id"]): result for result in results}
    compared: list[dict[str, Any]] = []
    for group in groups:
        group_id = str(group.get("id", "unnamed"))
        member_ids = group.get("member_ids")
        if (
            not isinstance(member_ids, list)
            or len(member_ids) < 2
            or not all(isinstance(member_id, str) for member_id in member_ids)
        ):
            raise SilhouetteMorphologyError("group_member_ids_invalid")
        if any(member_id not in by_id for member_id in member_ids):
            raise SilhouetteMorphologyError("group_member_missing")
        metrics_by_id = {
            member_id: by_id[member_id]["metrics"] for member_id in member_ids
        }
        lengths = [
            float(metrics_by_id[member_id]["centerline_length_pt"])
            for member_id in member_ids
        ]
        widths = [
            float(metrics_by_id[member_id]["stroke_width_pt"])
            for member_id in member_ids
        ]
        group_metrics: dict[str, Any] = {
            "centerline_length_ratio": _ratio(lengths),
            "stroke_width_ratio": _ratio(widths),
            "absolute_tip_displacement_pt": {
                member_id: abs(
                    float(metrics_by_id[member_id]["tip_displacement_x_pt"])
                )
                for member_id in member_ids
            },
        }
        violations: list[str] = []
        if group_metrics["centerline_length_ratio"] > float(
            group.get("max_centerline_length_ratio", math.inf)
        ):
            violations.append("centerline_length_ratio")
        if group_metrics["stroke_width_ratio"] > float(
            group.get("max_stroke_width_ratio", math.inf)
        ):
            violations.append("stroke_width_ratio")
        bend_order = group.get("absolute_bend_order")
        if bend_order is not None:
            if (
                not isinstance(bend_order, list)
                or set(bend_order) != set(member_ids)
                or len(bend_order) != len(member_ids)
            ):
                raise SilhouetteMorphologyError("absolute_bend_order_invalid")
            minimum_step = float(group.get("minimum_bend_step_pt", 0.0))
            displacements = group_metrics["absolute_tip_displacement_pt"]
            if any(
                displacements[right] - displacements[left] < minimum_step
                for left, right in zip(bend_order, bend_order[1:])
            ):
                violations.append("absolute_bend_order")
        directions = group.get("tip_directions") or {}
        if not isinstance(directions, dict):
            raise SilhouetteMorphologyError("tip_directions_invalid")
        minimum_direction_displacement = float(
            group.get("minimum_direction_displacement_pt", 0.0)
        )
        wrong_directions: list[str] = []
        for member_id, direction in directions.items():
            if member_id not in metrics_by_id or direction not in {"positive", "negative"}:
                raise SilhouetteMorphologyError("tip_direction_declaration_invalid")
            displacement = float(metrics_by_id[member_id]["tip_displacement_x_pt"])
            if (
                abs(displacement) < minimum_direction_displacement
                or direction == "positive"
                and displacement <= 0
                or direction == "negative"
                and displacement >= 0
            ):
                wrong_directions.append(member_id)
        group_metrics["wrong_tip_directions"] = wrong_directions
        if wrong_directions:
            violations.append("tip_direction")
        compared.append(
            {
                "id": group_id,
                "member_ids": member_ids,
                "metrics": group_metrics,
                "violations": violations,
            }
        )
    return compared


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
    fill_required: bool = True,
    linewidth_range_pt: list[float] | None = None,
) -> dict[str, Any]:
    left, top, right, bottom = bbox_pt
    candidates = []
    for curve in curves:
        center_x = (float(curve["x0"]) + float(curve["x1"])) / 2.0
        center_y = (float(curve["top"]) + float(curve["bottom"])) / 2.0
        if not (left <= center_x <= right and top <= center_y <= bottom):
            continue
        if curve.get("fill") is not fill_required:
            continue
        if _color_distance(curve.get("stroking_color"), stroke_rgb) > color_tolerance:
            continue
        if linewidth_range_pt is not None:
            linewidth = float(curve.get("linewidth") or 0.0)
            if not linewidth_range_pt[0] <= linewidth <= linewidth_range_pt[1]:
                continue
        candidates.append(curve)
    if not candidates:
        raise SilhouetteMorphologyError("target_curve_missing")
    if len(candidates) != 1:
        raise SilhouetteMorphologyError("target_curve_ambiguous")
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
            representation = str(check.get("representation", "filled_boundary"))
            if representation not in {"filled_boundary", "stroked_centerline"}:
                raise SilhouetteMorphologyError("representation_invalid")
            linewidth_range = check.get("linewidth_range_pt")
            if linewidth_range is not None and (
                not isinstance(linewidth_range, list)
                or len(linewidth_range) != 2
                or not all(isinstance(value, (int, float)) for value in linewidth_range)
            ):
                raise SilhouetteMorphologyError("linewidth_range_pt_invalid")
            curve = select_curve(
                curves,
                bbox_pt=[float(value) * CM_TO_PT for value in bbox_cm],
                stroke_rgb=[float(value) for value in stroke_rgb],
                color_tolerance=float(check.get("color_tolerance", 0.03)),
                fill_required=representation == "filled_boundary",
                linewidth_range_pt=(
                    [float(value) for value in linewidth_range]
                    if linewidth_range is not None
                    else None
                ),
            )
            if representation == "filled_boundary":
                analysis = analyze_curve(
                    curve,
                    max_width_to_length_ratio=float(
                        check.get("max_width_to_length_ratio", 0.20)
                    ),
                    max_width_variation_ratio=float(
                        check.get("max_width_variation_ratio", 3.0)
                    ),
                )
            else:
                analysis = analyze_stroked_centerline(
                    curve,
                    max_width_to_length_ratio=float(
                        check.get("max_width_to_length_ratio", 0.20)
                    ),
                )
            results.append(
                {
                    "id": str(check.get("id", "unnamed")),
                    "representation": representation,
                    **analysis,
                }
            )
    raw_groups = spec.get("silhouette_morphology_groups") or []
    if not isinstance(raw_groups, list):
        raise SilhouetteMorphologyError("silhouette_groups_must_be_list")
    groups = analyze_groups(results, raw_groups)
    violation_count = sum(len(result["violations"]) for result in results) + sum(
        len(group["violations"]) for group in groups
    )
    return {
        "schema": SCHEMA,
        "render_pdf": pdf_path.as_posix(),
        "render_pdf_sha256": _sha256(pdf_path),
        "spec_sha256": _sha256(spec_path),
        "source": "spec.yaml:silhouette_morphology_checks",
        "checked": len(results),
        "group_checked": len(groups),
        "violation_count": violation_count,
        "results": results,
        "groups": groups,
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
        for group in payload["groups"]:
            for violation in group["violations"]:
                print(f"WARN silhouette_morphology_group: {group['id']} {violation}")
    else:
        print(
            "OK: "
            f"{payload['checked']} silhouette morphology check(s) and "
            f"{payload['group_checked']} comparison group(s) passed"
        )
    return 1 if args.strict and payload["violation_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
