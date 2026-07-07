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

import pdfplumber
import yaml

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
for script_dir in reversed(
    (
        SCRIPTS_DIR,
        SCRIPTS_DIR / "checks",
        SCRIPTS_DIR / "candidates",
        SCRIPTS_DIR / "quality",
        SCRIPTS_DIR / "loop",
        SCRIPTS_DIR / "driver",
    )
):
    sys.path.insert(0, str(script_dir))

from check_visual_clash import extract_pdf_words_and_page  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402

SCHEMA = "figure-agent.undeclared-geometry.v1"
CM_TO_PT = 72.0 / 2.54
DEFAULT_NEAR_MISS_PT = 4.0
_POINT_RE = r"\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)"
_RECT_RE = re.compile(rf"{_POINT_RE}\s*rectangle\s*{_POINT_RE}")
_SEGMENT_RE = re.compile(rf"{_POINT_RE}\s*--\s*{_POINT_RE}")
_CIRCLE_RE = re.compile(rf"{_POINT_RE}\s*circle\s*\(\s*(-?\d+(?:\.\d+)?)(cm|mm|pt)?\s*\)")
_BEZIER_RE = re.compile(
    rf"{_POINT_RE}\s*\.\.\s*controls\s*{_POINT_RE}\s*and\s*{_POINT_RE}\s*\.\.\s*{_POINT_RE}",
    re.DOTALL,
)
_OPERATION_RE = re.compile(
    r"\\(?P<command>draw|fill|shade)(?:\[(?P<options>[^\]]*)\])?(?P<body>.*?);",
    re.DOTALL,
)
_LINE_WIDTH_RE = re.compile(r"line width\s*=\s*([0-9.]+)\s*pt")
_CGRAY_TONE_RE = re.compile(r"cGray!(\d+(?:\.\d+)?)")
FRAME_TONE_MAX = 35.0
FRAME_LINE_WIDTH_MAX_PT = 0.35
FRAME_LINE_MIN_LENGTH_PT = 2.0 * CM_TO_PT
FRAME_RECT_MIN_WIDTH_PT = 4.0 * CM_TO_PT
FRAME_RECT_MIN_HEIGHT_PT = 3.0 * CM_TO_PT
RENDERED_FRAME_LINE_WIDTH_MAX_PT = 0.75
RENDERED_FRAME_LINE_MIN_LENGTH_PT = 2.0 * CM_TO_PT
RENDERED_FRAME_RECT_MIN_WIDTH_PT = 4.0 * CM_TO_PT
RENDERED_FRAME_RECT_MIN_HEIGHT_PT = 3.0 * CM_TO_PT
RENDERED_FRAME_GRAY_MIN = 0.55
RENDERED_FRAME_NEUTRAL_DELTA_MAX = 0.04

# Conceptual-geometry kinds a pure schematic declares on purpose: axes, dividers,
# region rectangles, and plot frames are intentional, not layout regions to police.
# Under the schematic profile these are reported as INFO rather than actionable WARN.
# Label/frame crossings (label_crosses_*) are real defects and stay WARN.
_SCHEMATIC_PROFILE_DOWNRANK_KINDS = frozenset(
    {
        "undeclared_column_rule",
        "undeclared_horizontal_rule",
        "undeclared_rect_boundary",
        "label_endpoint_near_miss",
    }
)


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


def _point_cm_to_pt(x: float, y: float) -> list[float]:
    return [_cm_to_pt(x), _cm_to_pt(y)]


def _bbox_from_points_pt(points: list[list[float]]) -> list[float]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def _radius_to_pt(value: float, unit: str | None) -> float:
    if unit == "pt":
        return round(value, 6)
    if unit == "mm":
        return _cm_to_pt(value / 10.0)
    return _cm_to_pt(value)


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


def _iter_tikz_operations(tex_text: str) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for match in _OPERATION_RE.finditer(tex_text):
        prefix = tex_text[: match.start()]
        start_line = prefix.count("\n") + 1
        line_start = prefix.rfind("\n") + 1
        if tex_text[line_start : match.start()].lstrip().startswith("%"):
            continue
        operations.append(
            {
                "text": match.group(0),
                "source_line": start_line,
                "command": str(match.group("command") or ""),
                "options": str(match.group("options") or ""),
            }
        )
    return operations


def _parse_operation_geometry(operation: dict[str, Any]) -> list[dict[str, Any]]:
    text = str(operation["text"])
    source_line = int(operation["source_line"])
    command = str(operation["command"])
    options = str(operation["options"])
    geometry: list[dict[str, Any]] = []
    for match in _RECT_RE.finditer(text):
        x0, y0, x1, y1 = (float(value) for value in match.groups())
        geometry.append(
            {
                "kind": "rect",
                "bbox_pt": _bbox_cm_to_pt([x0, y0, x1, y1]),
                "source_line": source_line,
                "command": command,
                "options": options,
            }
        )
    for match in _SEGMENT_RE.finditer(text):
        x0, y0, x1, y1 = (float(value) for value in match.groups())
        if abs(x0 - x1) < 0.03 and abs(y0 - y1) >= 0.25:
            geometry.append(
                {
                    "kind": "vertical_line",
                    "line_pt": _line_pt((x0, y0, x1, y1)),
                    "source_line": source_line,
                    "command": command,
                    "options": options,
                }
            )
        elif abs(y0 - y1) < 0.03 and abs(x0 - x1) >= 0.25:
            geometry.append(
                {
                    "kind": "horizontal_line",
                    "line_pt": _line_pt((x0, y0, x1, y1)),
                    "source_line": source_line,
                    "command": command,
                    "options": options,
                }
            )
    for match in _CIRCLE_RE.finditer(text):
        x, y, radius, unit = match.groups()
        center_pt = _point_cm_to_pt(float(x), float(y))
        radius_pt = _radius_to_pt(float(radius), unit)
        geometry.append(
            {
                "kind": "circle",
                "center_pt": center_pt,
                "radius_pt": radius_pt,
                "bbox_pt": [
                    round(center_pt[0] - radius_pt, 6),
                    round(center_pt[1] - radius_pt, 6),
                    round(center_pt[0] + radius_pt, 6),
                    round(center_pt[1] + radius_pt, 6),
                ],
                "source_line": source_line,
                "command": command,
                "options": options,
                "clearance_mode": "disc_envelope",
            }
        )
    for match in _BEZIER_RE.finditer(text):
        values = [float(value) for value in match.groups()]
        points = [
            _point_cm_to_pt(values[index], values[index + 1])
            for index in range(0, len(values), 2)
        ]
        geometry.append(
            {
                "kind": "curve",
                "control_hull_pt": points,
                "bbox_pt": _bbox_from_points_pt(points),
                "source_line": source_line,
                "command": command,
                "options": options,
                "clearance_mode": "conservative_hull",
            }
        )
    return geometry


def _parse_tikz_geometry(tex_text: str) -> list[dict[str, Any]]:
    geometry: list[dict[str, Any]] = []
    for operation in _iter_tikz_operations(tex_text):
        geometry.extend(_parse_operation_geometry(operation))
    return geometry


def _operation_unknown_reasons(
    operation: dict[str, Any],
    parsed: list[dict[str, Any]],
) -> list[str]:
    text = str(operation["text"])
    parsed_kind_counts: dict[str, int] = {}
    for item in parsed:
        kind = str(item["kind"])
        parsed_kind_counts[kind] = parsed_kind_counts.get(kind, 0) + 1
    reasons: list[str] = []
    circle_count = len(re.findall(r"\bcircle\s*\(", text))
    if circle_count > parsed_kind_counts.get("circle", 0):
        reasons.append("nonliteral_circle")
    controls_count = text.count("controls")
    if controls_count > parsed_kind_counts.get("curve", 0):
        reasons.append("unsupported_curve")
    if re.search(r"\bellipse\b", text):
        reasons.append("unsupported_ellipse")
    if re.search(r"\barc\b", text):
        reasons.append("unsupported_arc")
    if re.search(r"\bplot\b", text):
        reasons.append("unsupported_plot")
    if re.search(r"\bto\s*\[", text):
        reasons.append("unsupported_to_curve")
    if not reasons and re.search(r"\([^)]*(?:\\|\{)[^)]*\)", text):
        reasons.append("nonliteral_coordinate")
    if not parsed and not reasons:
        reasons.append("unsupported_geometry")
    return sorted(set(reasons))


def geometry_parse_coverage(tex_text: str) -> dict[str, Any]:
    operations = _iter_tikz_operations(tex_text)
    parsed_counts: dict[str, int] = {}
    unknown_reasons: dict[str, int] = {}
    unknown_samples: list[dict[str, Any]] = []
    parsed_operations = 0
    fully_parsed_operations = 0
    partial_unknown_operations = 0
    unknown_operations = 0
    for operation in operations:
        parsed = _parse_operation_geometry(operation)
        reasons = _operation_unknown_reasons(operation, parsed)
        if parsed:
            parsed_operations += 1
            for item in parsed:
                kind = str(item["kind"])
                parsed_counts[kind] = parsed_counts.get(kind, 0) + 1
            if reasons:
                partial_unknown_operations += 1
            else:
                fully_parsed_operations += 1
        else:
            unknown_operations += 1
        for reason in reasons:
            unknown_reasons[reason] = unknown_reasons.get(reason, 0) + 1
            if len(unknown_samples) < 10:
                unknown_samples.append(
                    {
                        "source_line": int(operation["source_line"]),
                        "reason": reason,
                        "command": str(operation["command"]),
                        "sample": str(operation["text"]).strip()[:160],
                    }
                )
    total = len(operations)
    return {
        "total_operations": total,
        "parsed_operations": parsed_operations,
        "fully_parsed_operations": fully_parsed_operations,
        "partial_unknown_operations": partial_unknown_operations,
        "unknown_operations": unknown_operations,
        "coverage_ratio": None if total == 0 else round(parsed_operations / total, 6),
        "parsed_geometry_counts": dict(sorted(parsed_counts.items())),
        "unknown_reasons": dict(sorted(unknown_reasons.items())),
        "unknown_samples": unknown_samples,
        "non_auto_promotable_geometry": [
            "circle_envelope",
            "curve_conservative_hull",
        ],
    }


def rendered_curve_coverage(curves: list[dict[str, Any]]) -> dict[str, Any]:
    envelopes: list[dict[str, Any]] = []
    for raw_curve in curves:
        points = raw_curve.get("pts")
        if not isinstance(points, list) or not points:
            continue
        point_values: list[list[float]] = []
        for point in points:
            if (
                isinstance(point, tuple | list)
                and len(point) == 2
                and all(isinstance(value, int | float) for value in point)
            ):
                point_values.append([float(point[0]), float(point[1])])
        if not point_values:
            continue
        envelopes.append(
            {
                "bbox_pt": [round(value, 6) for value in _bbox_from_points_pt(point_values)],
                "clearance_mode": "rendered_curve_bbox",
                "linewidth_pt": round(float(raw_curve.get("linewidth") or 0.0), 6),
            }
        )
    return {
        "rendered_curve_count": len(envelopes),
        "rendered_curve_envelopes": envelopes[:25],
    }


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
        elif kind == "vertical_line" and isinstance(check.get("x_pdf_cm"), int | float):
            y_range = check.get("y_range_pdf_cm")
            if (
                isinstance(y_range, list)
                and len(y_range) == 2
                and all(isinstance(item, int | float) for item in y_range)
            ):
                declared.append(
                    {
                        "kind": "vertical_line",
                        "x": _cm_to_pt(check["x_pdf_cm"]),
                        "y_range": sorted([_cm_to_pt(y_range[0]), _cm_to_pt(y_range[1])]),
                    }
                )
        elif kind == "horizontal_line" and isinstance(check.get("y_pdf_cm"), int | float):
            x_range = check.get("x_range_pdf_cm")
            if (
                isinstance(x_range, list)
                and len(x_range) == 2
                and all(isinstance(item, int | float) for item in x_range)
            ):
                declared.append(
                    {
                        "kind": "horizontal_line",
                        "y": _cm_to_pt(check["y_pdf_cm"]),
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


def _line_crosses_word(line: dict[str, Any], word: dict[str, Any]) -> bool:
    x0, y0, x1, y1 = _word_bbox(word)
    if line["kind"] == "vertical_line":
        x = float(line["x"])
        y_start, y_end = line["y_range"]
        return x0 <= x <= x1 and _ranges_overlap([y0, y1], [y_start, y_end], 0.0)
    y = float(line["y"])
    x_start, x_end = line["x_range"]
    return y0 <= y <= y1 and _ranges_overlap([x0, x1], [x_start, x_end], 0.0)


def _rect_boundary_lines(bbox_pt: list[float]) -> list[dict[str, Any]]:
    x0, y0, x1, y1 = bbox_pt
    return [
        {"kind": "horizontal_line", "y": y0, "x_range": [x0, x1], "side": "bottom"},
        {"kind": "horizontal_line", "y": y1, "x_range": [x0, x1], "side": "top"},
        {"kind": "vertical_line", "x": x0, "y_range": [y0, y1], "side": "left"},
        {"kind": "vertical_line", "x": x1, "y_range": [y0, y1], "side": "right"},
    ]


def _line_bbox(line: dict[str, Any]) -> list[float]:
    if line["kind"] == "vertical_line":
        x = float(line["x"])
        y0, y1 = line["y_range"]
        return [x, float(y0), x, float(y1)]
    y = float(line["y"])
    x0, x1 = line["x_range"]
    return [float(x0), y, float(x1), y]


def _gray_tone(options: str) -> float | None:
    match = _CGRAY_TONE_RE.search(options)
    if match is not None:
        return float(match.group(1))
    return 50.0 if "cGray" in options else None


def _line_width_pt(options: str) -> float:
    match = _LINE_WIDTH_RE.search(options)
    return float(match.group(1)) if match is not None else 0.4


def _is_frame_like_geometry(geometry: dict[str, Any]) -> bool:
    if geometry.get("command") != "draw":
        return False
    options = str(geometry.get("options") or "")
    tone = _gray_tone(options)
    if tone is None or tone > FRAME_TONE_MAX:
        return False
    if _line_width_pt(options) > FRAME_LINE_WIDTH_MAX_PT:
        return False
    if geometry["kind"] == "rect":
        x0, y0, x1, y1 = geometry["bbox_pt"]
        width = abs(x1 - x0)
        height = abs(y1 - y0)
        return width >= FRAME_RECT_MIN_WIDTH_PT and height >= FRAME_RECT_MIN_HEIGHT_PT
    line = geometry["line_pt"]
    if line["kind"] == "vertical_line":
        y0, y1 = line["y_range"]
        return abs(float(y1) - float(y0)) >= FRAME_LINE_MIN_LENGTH_PT - 1e-3
    x0, x1 = line["x_range"]
    return abs(float(x1) - float(x0)) >= FRAME_LINE_MIN_LENGTH_PT - 1e-3


def _is_semantic_path_like_geometry(geometry: dict[str, Any]) -> bool:
    if geometry.get("command") != "draw" or geometry["kind"] not in {
        "vertical_line",
        "horizontal_line",
    }:
        return False
    options = str(geometry.get("options") or "")
    return "Stealth" in options or "->" in options or "<-" in options


def _semantic_path_label_candidate(word: dict[str, Any]) -> bool:
    return len(str(word.get("text", "")).strip()) > 1


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


def _is_light_neutral_stroke(color: object) -> bool:
    if isinstance(color, int | float):
        return float(color) >= RENDERED_FRAME_GRAY_MIN
    if not isinstance(color, tuple) or not color:
        return False
    channels = [float(value) for value in color if isinstance(value, int | float)]
    if not channels:
        return False
    return (
        max(channels) - min(channels) <= RENDERED_FRAME_NEUTRAL_DELTA_MAX
        and sum(channels) / len(channels) >= RENDERED_FRAME_GRAY_MIN
    )


def _rendered_line_from_pdf_line(raw_line: dict[str, Any]) -> dict[str, Any] | None:
    if float(raw_line.get("linewidth") or 0.0) > RENDERED_FRAME_LINE_WIDTH_MAX_PT:
        return None
    if not _is_light_neutral_stroke(raw_line.get("stroking_color")):
        return None
    x0 = float(raw_line["x0"])
    x1 = float(raw_line["x1"])
    top = float(raw_line["top"])
    bottom = float(raw_line["bottom"])
    if abs(x0 - x1) < 0.5 and abs(bottom - top) >= RENDERED_FRAME_LINE_MIN_LENGTH_PT:
        return {"kind": "vertical_line", "x": x0, "y_range": sorted([top, bottom])}
    if abs(top - bottom) < 0.5 and abs(x1 - x0) >= RENDERED_FRAME_LINE_MIN_LENGTH_PT:
        return {"kind": "horizontal_line", "y": top, "x_range": sorted([x0, x1])}
    return None


def _rendered_rect_boundary_lines(raw_rect: dict[str, Any]) -> list[dict[str, Any]]:
    if not raw_rect.get("stroke"):
        return []
    if raw_rect.get("fill"):
        return []
    if float(raw_rect.get("linewidth") or 0.0) > RENDERED_FRAME_LINE_WIDTH_MAX_PT:
        return []
    if not _is_light_neutral_stroke(raw_rect.get("stroking_color")):
        return []
    x0 = float(raw_rect["x0"])
    x1 = float(raw_rect["x1"])
    top = float(raw_rect["top"])
    bottom = float(raw_rect["bottom"])
    if abs(x1 - x0) < RENDERED_FRAME_RECT_MIN_WIDTH_PT:
        return []
    if abs(bottom - top) < RENDERED_FRAME_RECT_MIN_HEIGHT_PT:
        return []
    return [
        {"kind": "horizontal_line", "y": top, "x_range": sorted([x0, x1]), "side": "top"},
        {
            "kind": "horizontal_line",
            "y": bottom,
            "x_range": sorted([x0, x1]),
            "side": "bottom",
        },
        {"kind": "vertical_line", "x": x0, "y_range": sorted([top, bottom]), "side": "left"},
        {"kind": "vertical_line", "x": x1, "y_range": sorted([top, bottom]), "side": "right"},
    ]


def detect_rendered_boundary_crossings(
    words: list[dict[str, Any]],
    rendered_lines: list[dict[str, Any]],
    rendered_rects: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return label/frame crossing candidates from rendered PDF coordinates."""
    candidates: list[dict[str, Any]] = []
    for raw_line in rendered_lines:
        line = _rendered_line_from_pdf_line(raw_line)
        if line is None:
            continue
        crossing_kind = (
            "label_crosses_column_rule"
            if line["kind"] == "vertical_line"
            else "label_crosses_horizontal_rule"
        )
        for word in words:
            if not _line_crosses_word(line, word):
                continue
            candidates.append(
                _base_candidate(
                    kind=crossing_kind,
                    evidence=f"rendered frame/rule crosses text {word.get('text', '')!r}",
                    bbox_pt=_line_bbox(line),
                    source_line=0,
                    nearest_text=str(word.get("text", "")),
                    distance_pt=0.0,
                    recommended_action="add_micro_defect",
                )
            )
    for raw_rect in rendered_rects:
        for line in _rendered_rect_boundary_lines(raw_rect):
            for word in words:
                if not _line_crosses_word(line, word):
                    continue
                candidate = _base_candidate(
                    kind="label_crosses_rect_boundary",
                    evidence=(
                        f"rendered frame rectangle {line['side']} border crosses "
                        f"text {word.get('text', '')!r}"
                    ),
                    bbox_pt=_line_bbox(line),
                    source_line=0,
                    nearest_text=str(word.get("text", "")),
                    distance_pt=0.0,
                    recommended_action="add_micro_defect",
                )
                candidate["boundary_side"] = line["side"]
                candidates.append(candidate)
    return candidates


def _rendered_boundary_crossings_from_pdf(
    pdf_path: Path,
    words: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            return []
        page = pdf.pages[0]
        return detect_rendered_boundary_crossings(words, page.lines, page.rects)


def _rendered_curves_from_pdf(pdf_path: Path) -> list[dict[str, Any]]:
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            return []
        return list(pdf.pages[0].curves)


def detect_undeclared_geometry(
    tex_text: str,
    words: list[dict[str, Any]],
    spec: dict[str, Any] | None,
    *,
    near_miss_pt: float = DEFAULT_NEAR_MISS_PT,
    page_size_pt: tuple[float, float] | None = None,
    source_crossings: bool = True,
) -> list[dict[str, Any]]:
    """Return deterministic undeclared geometry and near-miss candidates."""
    _ = page_size_pt
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
                        f"source line {geometry['source_line']} rectangle lacks text_boundary_check"
                    ),
                    bbox_pt=geometry["bbox_pt"],
                    source_line=geometry["source_line"],
                )
            )
            if not source_crossings or not _is_frame_like_geometry(geometry):
                continue
            for line in _rect_boundary_lines(geometry["bbox_pt"]):
                for word in words:
                    if not _line_crosses_word(line, word):
                        continue
                    candidate = _base_candidate(
                        kind="label_crosses_rect_boundary",
                        evidence=(
                            f"source line {geometry['source_line']} rectangle "
                            f"{line['side']} border crosses text "
                            f"{word.get('text', '')!r}"
                        ),
                        bbox_pt=_line_bbox(line),
                        source_line=geometry["source_line"],
                        nearest_text=str(word.get("text", "")),
                        distance_pt=0.0,
                        recommended_action="add_micro_defect",
                    )
                    candidate["boundary_side"] = line["side"]
                    candidates.append(candidate)
            continue
        if geometry["kind"] not in {"vertical_line", "horizontal_line"}:
            continue
        line = geometry["line_pt"]
        if geometry["kind"] == "vertical_line":
            bbox = [line["x"], line["y_range"][0], line["x"], line["y_range"][1]]
            kind = "undeclared_column_rule"
            crossing_kind = "label_crosses_column_rule"
        else:
            bbox = [line["x_range"][0], line["y"], line["x_range"][1], line["y"]]
            kind = "undeclared_horizontal_rule"
            crossing_kind = "label_crosses_horizontal_rule"
        candidates.append(
            _base_candidate(
                kind=kind,
                evidence=f"source line {geometry['source_line']} line lacks text_boundary_check",
                bbox_pt=bbox,
                source_line=geometry["source_line"],
            )
        )
        for word in words:
            semantic_path_like = _is_semantic_path_like_geometry(geometry)
            line_crosses_word = (
                (source_crossings or semantic_path_like)
                and _line_crosses_word(line, word)
            )
            if line_crosses_word and _is_frame_like_geometry(geometry):
                candidates.append(
                    _base_candidate(
                        kind=crossing_kind,
                        evidence=(
                            f"source line {geometry['source_line']} line crosses "
                            f"text {word.get('text', '')!r}"
                        ),
                        bbox_pt=_line_bbox(line),
                        source_line=geometry["source_line"],
                        nearest_text=str(word.get("text", "")),
                        distance_pt=0.0,
                        recommended_action="add_micro_defect",
                    )
                )
                continue
            if line_crosses_word and semantic_path_like:
                if not _semantic_path_label_candidate(word):
                    continue
                candidates.append(
                    _base_candidate(
                        kind="label_crosses_semantic_path",
                        evidence=(
                            f"source line {geometry['source_line']} semantic path "
                            f"crosses text {word.get('text', '')!r}"
                        ),
                        bbox_pt=_line_bbox(line),
                        source_line=geometry["source_line"],
                        nearest_text=str(word.get("text", "")),
                        distance_pt=0.0,
                        recommended_action="add_micro_defect",
                    )
                )
                continue
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
        "label_crosses_rect_boundary": 1,
        "label_crosses_column_rule": 1,
        "label_crosses_horizontal_rule": 1,
        "label_crosses_semantic_path": 1,
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


def undeclared_geometry_payload(
    pdf_path: Path,
    candidates: list[dict[str, Any]],
    *,
    tex_path: Path | None = None,
    tex_text: str | None = None,
    rendered_curves: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    fixture_dir = pdf_path.parent.parent
    fixture_name = fixture_dir.name or Path.cwd().name
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "fixture": fixture_name,
        "render_pdf": f"build/{pdf_path.name}",
        "source": "tikz-source:auto-discovery",
        "candidates": candidates,
        "total": len(candidates),
    }
    if tex_path is not None:
        payload["source_hashes"] = {
            f"examples/{fixture_name}/{tex_path.name}": file_sha256(tex_path)
        }
    if tex_text is not None:
        coverage = geometry_parse_coverage(tex_text)
        if rendered_curves is not None:
            coverage["rendered_curves"] = rendered_curve_coverage(rendered_curves)
        payload["geometry_parse_coverage"] = coverage
    return payload


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


def _undeclared_geometry_profile(spec: dict[str, Any]) -> str | None:
    raw_profile = spec.get("undeclared_geometry_profile")
    if raw_profile is None:
        return None
    if raw_profile != "schematic":
        raise UndeclaredGeometryError("undeclared_geometry_profile must be 'schematic' or absent")
    return raw_profile


def partition_candidates_by_profile(
    candidates: list[dict[str, Any]],
    profile: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split candidates into (downranked, actionable) for the given profile.

    Under the schematic profile, intentional conceptual geometry is downranked to
    INFO; label/frame crossings stay actionable. Any other profile leaves every
    candidate actionable.
    """
    if profile != "schematic":
        return [], list(candidates)
    downranked = [c for c in candidates if c["kind"] in _SCHEMATIC_PROFILE_DOWNRANK_KINDS]
    actionable = [c for c in candidates if c["kind"] not in _SCHEMATIC_PROFILE_DOWNRANK_KINDS]
    return downranked, actionable


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
        tex_text = tex_path.read_text(encoding="utf-8")
        words, page_size = extract_pdf_words_and_page(pdf_path)
        spec = _load_spec(spec_path)
        profile = _undeclared_geometry_profile(spec)
        candidates = detect_undeclared_geometry(
            tex_text,
            words,
            spec,
            page_size_pt=page_size,
            source_crossings=False,
        )
        candidates.extend(_rendered_boundary_crossings_from_pdf(pdf_path, words))
        rendered_curves = _rendered_curves_from_pdf(pdf_path)
        candidates.sort(
            key=lambda item: (
                item["source_line"],
                item["kind"],
                item["nearest_text"],
                item["bbox_pt"],
            )
        )
        for index, candidate in enumerate(candidates, start=1):
            candidate["id"] = f"UG{index:03d}"
        downranked, actionable = partition_candidates_by_profile(candidates, profile)
        # Under the schematic profile the downranked conceptual geometry (axes,
        # dividers, region rects) is recorded under a separate key but kept OUT of
        # `candidates`, so the critique undeclared-geometry accounting gate does not
        # require it to be hand-accounted. Non-schematic fixtures are unchanged.
        accounted = actionable if profile == "schematic" else candidates
        payload = undeclared_geometry_payload(
            pdf_path,
            accounted,
            tex_path=tex_path,
            tex_text=tex_text,
            rendered_curves=rendered_curves,
        )
        if profile == "schematic":
            payload["profile"] = "schematic"
            payload["downranked"] = downranked
        output = args.json_output or pdf_path.parent / "undeclared_geometry.json"
        _write_json(output, payload)
    except (UndeclaredGeometryError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for candidate in downranked:
        print(
            f"INFO {candidate['kind']}: {candidate['id']} "
            f"text={candidate['nearest_text']!r} distance={candidate['distance_pt']}",
            file=sys.stderr,
        )
    for candidate in actionable:
        print(
            f"WARN {candidate['kind']}: {candidate['id']} "
            f"text={candidate['nearest_text']!r} distance={candidate['distance_pt']}",
            file=sys.stderr,
        )
    if actionable:
        print(f"{len(actionable)} undeclared geometry candidate(s)", file=sys.stderr)
    if args.strict and actionable:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
