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
from check_visual_clash import extract_pdf_words_and_page

SCHEMA = "figure-agent.undeclared-geometry.v1"
CM_TO_PT = 72.0 / 2.54
DEFAULT_NEAR_MISS_PT = 4.0
_POINT_RE = r"\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)"
_RECT_RE = re.compile(rf"{_POINT_RE}\s*rectangle\s*{_POINT_RE}")
_SEGMENT_RE = re.compile(rf"{_POINT_RE}\s*--\s*{_POINT_RE}")
_COMMAND_RE = re.compile(r"\\(?P<command>draw|fill|shade)(?:\[(?P<options>[^\]]*)\])?")
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
    current_command = ""
    current_options = ""
    for line_no, line in enumerate(tex_text.splitlines(), start=1):
        if line.lstrip().startswith("%"):
            continue
        command_match = _COMMAND_RE.search(line)
        if command_match is not None:
            current_command = str(command_match.group("command") or "")
            current_options = str(command_match.group("options") or "")
        for match in _RECT_RE.finditer(line):
            x0, y0, x1, y1 = (float(value) for value in match.groups())
            geometry.append(
                {
                    "kind": "rect",
                    "bbox_pt": _bbox_cm_to_pt([x0, y0, x1, y1]),
                    "source_line": line_no,
                    "command": current_command,
                    "options": current_options,
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
                        "command": current_command,
                        "options": current_options,
                    }
                )
            elif abs(y0 - y1) < 0.03 and abs(x0 - x1) >= 0.25:
                geometry.append(
                    {
                        "kind": "horizontal_line",
                        "line_pt": _line_pt((x0, y0, x1, y1)),
                        "source_line": line_no,
                        "command": current_command,
                        "options": current_options,
                    }
                )
        if ";" in line:
            current_command = ""
            current_options = ""
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
                        f"source line {geometry['source_line']} rectangle "
                        "lacks text_boundary_check"
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
            if (
                source_crossings
                and _is_frame_like_geometry(geometry)
                and _line_crosses_word(line, word)
            ):
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
        words, page_size = extract_pdf_words_and_page(pdf_path)
        candidates = detect_undeclared_geometry(
            tex_path.read_text(encoding="utf-8"),
            words,
            _load_spec(spec_path),
            page_size_pt=page_size,
            source_crossings=False,
        )
        candidates.extend(_rendered_boundary_crossings_from_pdf(pdf_path, words))
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
