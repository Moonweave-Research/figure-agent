#!/usr/bin/env python3
"""Place fixture source geometry in the compiled PDF's coordinate space.

A declared path is authored in PDF cm while the element it guards lives in the
.tex in source cm, and nothing bridged the two: a declaration kept measuring
after the element it names had moved.  The bridge is recovered from the fixture
itself -- the source segments the render actually draws -- and is
then verified against the render before any distance is reported, so a fixture
whose source the parser cannot cover fails loudly instead of being measured
against a guessed placement.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pdfplumber
import vector_clearance
from check_undeclared_geometry import (
    _iter_tikz_operations,
    _parse_tikz_geometry,
    _scope_shift_cm,
)

CM_TO_PT = 72.0 / 2.54
PT_TO_CM = 2.54 / 72.0
# A projected source segment counts as found when both endpoints sit this close
# to rendered ink; 0.02 cm is below the thinnest stroke the fixtures draw.
INK_MATCH_TOLERANCE_CM = 0.02
MIN_SEGMENT_LENGTH_CM = 0.05
# Two segments are the same line when their unit directions are parallel to
# within this dot product; anything looser matches unrelated near-parallel ink.
DIRECTION_TOLERANCE = 0.9999
SCALE_LOG_BUCKET = 0.002
OFFSET_BUCKET_CM = 0.01
BEZIER_FLATTEN_STEPS = 16
MIN_VERIFIED_SEGMENTS = 8
MIN_VERIFIED_RATIO = 0.5
# A path marker comment sits on the element's own line or the line above it.
SELECTOR_LINE_SPAN = 1
PATH_SAMPLE_STEP_CM = 0.02


@dataclass(frozen=True)
class Placement:
    """Verified source-cm to PDF-cm mapping for one fixture."""

    scale: float
    offset_x_cm: float
    offset_y_cm: float
    verified_segments: int
    source_segments: int

    def project(self, x_cm: float, y_cm: float) -> tuple[float, float]:
        return (self.scale * x_cm + self.offset_x_cm, self.offset_y_cm - self.scale * y_cm)

    @property
    def verified_ratio(self) -> float:
        return self.verified_segments / self.source_segments


def _segment_from_line(line: dict[str, Any]) -> tuple[float, float, float, float]:
    if line["kind"] == "horizontal_line":
        return (
            line["x_range"][0] * PT_TO_CM,
            line["y"] * PT_TO_CM,
            line["x_range"][1] * PT_TO_CM,
            line["y"] * PT_TO_CM,
        )
    return (
        line["x"] * PT_TO_CM,
        line["y_range"][0] * PT_TO_CM,
        line["x"] * PT_TO_CM,
        line["y_range"][1] * PT_TO_CM,
    )


def _flatten_cubic(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Sample a cubic Bezier so distance is measured to the curve, not its chords."""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = points
    sampled = []
    for step in range(BEZIER_FLATTEN_STEPS + 1):
        t = step / BEZIER_FLATTEN_STEPS
        u = 1.0 - t
        sampled.append(
            (
                u * u * u * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t * t * t * x3,
                u * u * u * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t * t * t * y3,
            )
        )
    return sampled


def source_shapes(
    geometry: dict[str, Any],
    *,
    flatten_curves: bool = False,
) -> list[tuple[str, tuple[float, ...]]]:
    """Return one parsed source operation as area or segment shapes, in source cm.

    Curves keep their control hull for placement voting, because that is the
    shape the PDF stores; a declared path is measured against the flattened
    curve instead, so a chord of the hull is not mistaken for drift.
    """
    kind = geometry["kind"]
    if kind == "rect":
        x0, y0, x1, y1 = (value * PT_TO_CM for value in geometry["bbox_pt"])
        return [("area", (x0, y0, x1, y1))]
    if kind == "circle":
        cx, cy = (value * PT_TO_CM for value in geometry["center_pt"])
        radius = geometry["radius_pt"] * PT_TO_CM
        return [("disc", (cx, cy, radius))]
    if kind in {"horizontal_line", "vertical_line"}:
        return [("segment", _segment_from_line(geometry["line_pt"]))]
    if kind == "line_segment":
        start = geometry["start_pt"]
        end = geometry["end_pt"]
        return [
            (
                "segment",
                (
                    start[0] * PT_TO_CM,
                    start[1] * PT_TO_CM,
                    end[0] * PT_TO_CM,
                    end[1] * PT_TO_CM,
                ),
            )
        ]
    if kind == "curve":
        points = [(x * PT_TO_CM, y * PT_TO_CM) for x, y in geometry.get("control_hull_pt", [])]
        if flatten_curves and len(points) == 4:
            points = _flatten_cubic(points)
        return [
            ("segment", (a[0], a[1], b[0], b[1])) for a, b in zip(points, points[1:], strict=False)
        ]
    return []


def resolved_source(tex_text: str) -> str:
    """Substitute `\\coordinate` names with their literal points, scope for scope.

    The geometry parser reads literal points only, so a path the author wrote
    as `(name)--(other)` had no readable geometry and its declaration could not
    be measured. The resolver that vector_clearance already uses supplies the
    points; a name is substituted only where the reference sits under the same
    scope shift as its definition, because the same local token means a
    different place under a different shift. Substitution never adds or removes
    a newline, so source line numbers survive it.
    """
    coordinates = vector_clearance.collect_named_coordinates(tex_text)
    if not coordinates:
        return tex_text
    definition_shift: dict[str, tuple[float, float]] = {}
    declaration_spans: list[tuple[int, int]] = []
    for match in vector_clearance._COORDINATE_DEF_RE.finditer(tex_text):
        definition_shift[str(match.group("name"))] = _scope_shift_cm(tex_text, match.start())
        declaration_spans.append(match.span())

    def _replace(match: re.Match[str]) -> str:
        name = str(match.group("name"))
        if name not in coordinates:
            return match.group(0)
        if any(start <= match.start() < end for start, end in declaration_spans):
            return match.group(0)
        if _scope_shift_cm(tex_text, match.start()) != definition_shift.get(name):
            return match.group(0)
        return coordinates[name]

    return vector_clearance._COORDINATE_REF_RE.sub(_replace, tex_text)


_POINT_PATTERN = r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)"
_POINT_RE = re.compile(_POINT_PATTERN)
_CONTROLS_RE = re.compile(
    rf"\.\.\s*controls\s*{_POINT_PATTERN}\s*and\s*{_POINT_PATTERN}\s*\.\.\s*{_POINT_PATTERN}",
    re.DOTALL,
)
_LINK_RE = re.compile(rf"--\s*{_POINT_PATTERN}", re.DOTALL)
_CHAINED_KINDS = frozenset({"curve", "line_segment", "horizontal_line", "vertical_line"})


def _anchor_point(text: str, before: int) -> tuple[float, float] | None:
    """Return the last literal point written before this position in the path."""
    preceding = list(_POINT_RE.finditer(text, 0, before))
    if not preceding:
        return None
    last = preceding[-1]
    return (float(last.group(1)), float(last.group(2)))


def _operation_cubics(text: str) -> list[list[tuple[float, float]]]:
    """Return every cubic in a path, including the ones a chain scan drops.

    A `A .. controls .. B .. controls .. C` chain consumes its shared endpoint,
    so a non-overlapping scan for whole cubics sees only every other segment and
    the rest of the drawn curve is invisible to any check bound to it. Each
    `controls` clause is instead anchored to the last point written before it,
    which is that segment's start whether it opens the path or continues one.
    """
    cubics: list[list[tuple[float, float]]] = []
    for match in _CONTROLS_RE.finditer(text):
        start = _anchor_point(text, match.start())
        if start is None:
            continue
        values = [float(value) for value in match.groups()]
        cubics.append(
            [start, (values[0], values[1]), (values[2], values[3]), (values[4], values[5])]
        )
    return cubics


def _operation_segments(text: str) -> list[tuple[float, float, float, float]]:
    """Return every `--` leg of a path, including the ones a chain scan drops.

    `A--B--C` consumes B as the first leg's endpoint, so a non-overlapping scan
    for whole legs never sees `B--C`: half of a rerouted wire was invisible to
    the check bound to it. Each `--` is anchored to the point written before it.
    """
    legs: list[tuple[float, float, float, float]] = []
    for match in _LINK_RE.finditer(text):
        start = _anchor_point(text, match.start())
        if start is None:
            continue
        legs.append((start[0], start[1], float(match.group(1)), float(match.group(2))))
    return legs


def source_geometry(tex_text: str) -> list[dict[str, Any]]:
    """Return the fixture's drawn operations with named points and chains resolved."""
    resolved = resolved_source(tex_text)
    geometry = [
        item for item in _parse_tikz_geometry(resolved) if item["kind"] not in _CHAINED_KINDS
    ]
    for operation in _iter_tikz_operations(resolved):
        shift_x, shift_y = operation.get("scope_shift_cm", (0.0, 0.0))
        source_line = int(operation["source_line"])
        text = str(operation["text"])
        for cubic in _operation_cubics(text):
            geometry.append(
                {
                    "kind": "curve",
                    "source_line": source_line,
                    "control_hull_pt": [
                        [(x + shift_x) * CM_TO_PT, (y + shift_y) * CM_TO_PT] for x, y in cubic
                    ],
                }
            )
        for ax, ay, bx, by in _operation_segments(text):
            geometry.append(
                {
                    "kind": "line_segment",
                    "source_line": source_line,
                    "start_pt": [(ax + shift_x) * CM_TO_PT, (ay + shift_y) * CM_TO_PT],
                    "end_pt": [(bx + shift_x) * CM_TO_PT, (by + shift_y) * CM_TO_PT],
                }
            )
    return geometry


def source_segments(tex_text: str) -> list[tuple[float, float, float, float]]:
    """Return every parsed source operation as straight segments, in source cm."""
    segments: list[tuple[float, float, float, float]] = []
    for geometry in source_geometry(tex_text):
        for shape, values in source_shapes(geometry):
            if shape == "segment":
                segments.append(values)  # type: ignore[arg-type]
            elif shape == "area":
                x0, y0, x1, y1 = values
                segments.extend(
                    [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]
                )
    return segments


def pdf_ink_segments(pdf_path: Path) -> list[tuple[float, float, float, float]]:
    """Return every stroked or filled PDF path as straight segments, in PDF cm."""
    segments: list[tuple[float, float, float, float]] = []
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        for line in page.lines:
            segments.append(
                (
                    line["x0"] / CM_TO_PT,
                    line["top"] / CM_TO_PT,
                    line["x1"] / CM_TO_PT,
                    line["bottom"] / CM_TO_PT,
                )
            )
        for rect in page.rects:
            x0 = rect["x0"] / CM_TO_PT
            y0 = rect["top"] / CM_TO_PT
            x1 = rect["x1"] / CM_TO_PT
            y1 = rect["bottom"] / CM_TO_PT
            segments.extend(
                [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]
            )
        for curve in page.curves:
            points = [(x / CM_TO_PT, y / CM_TO_PT) for x, y in curve.get("pts", [])]
            segments.extend(
                (a[0], a[1], b[0], b[1]) for a, b in zip(points, points[1:], strict=False)
            )
    return segments


def point_segment_distance(
    px: float,
    py: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
) -> float:
    abx = bx - ax
    aby = by - ay
    denom = abx * abx + aby * aby
    if denom == 0.0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / denom))
    return math.hypot(px - (ax + t * abx), py - (ay + t * aby))


def _nearest_ink(
    px: float,
    py: float,
    ink: list[tuple[float, float, float, float]],
    limit: float,
) -> float:
    best = math.inf
    for ax, ay, bx, by in ink:
        if px < min(ax, bx) - limit or px > max(ax, bx) + limit:
            continue
        if py < min(ay, by) - limit or py > max(ay, by) + limit:
            continue
        distance = point_segment_distance(px, py, ax, ay, bx, by)
        if distance < best:
            best = distance
        if best == 0.0:
            break
    return best


def _directed(
    segments: list[tuple[float, float, float, float]],
    *,
    flip_y: bool,
) -> list[tuple[float, float, float, float, float, float, float]]:
    """Return (ax, ay, bx, by, ux, uy, length) with the unit direction in PDF sense."""
    directed = []
    for ax, ay, bx, by in segments:
        dx = bx - ax
        dy = -(by - ay) if flip_y else (by - ay)
        length = math.hypot(dx, dy)
        if length < MIN_SEGMENT_LENGTH_CM:
            continue
        directed.append((ax, ay, bx, by, dx / length, dy / length, length))
    return directed


def _peak(votes: dict[Any, list[float]]) -> list[float] | None:
    if not votes:
        return None
    return max(votes.values(), key=len)


def _vote_scale(source: list[tuple[Any, ...]], ink: list[tuple[Any, ...]]) -> float | None:
    """Return the length ratio the most source/ink segment pairs agree on."""
    buckets: dict[int, list[float]] = defaultdict(list)
    for _, _, _, _, sux, suy, slen in source:
        for _, _, _, _, iux, iuy, ilen in ink:
            if abs(sux * iux + suy * iuy) < DIRECTION_TOLERANCE:
                continue
            ratio = ilen / slen
            buckets[round(math.log(ratio) / SCALE_LOG_BUCKET)].append(ratio)
    winner = _peak(buckets)
    if winner is None or len(winner) < MIN_VERIFIED_SEGMENTS:
        return None
    return sum(winner) / len(winner)


def _vote_offset(
    source: list[tuple[Any, ...]],
    ink: list[tuple[Any, ...]],
    scale: float,
) -> tuple[float, float] | None:
    """Return the translation the most equal-length segment pairs agree on."""
    buckets: dict[tuple[int, int], list[tuple[float, float]]] = defaultdict(list)
    for sax, say, sbx, sby, sux, suy, slen in source:
        for iax, iay, ibx, iby, iux, iuy, ilen in ink:
            if abs(ilen - scale * slen) > INK_MATCH_TOLERANCE_CM:
                continue
            alignment = sux * iux + suy * iuy
            if abs(alignment) < DIRECTION_TOLERANCE:
                continue
            pairs = (
                ((sax, say, iax, iay), (sbx, sby, ibx, iby))
                if alignment > 0
                else ((sax, say, ibx, iby), (sbx, sby, iax, iay))
            )
            for sx, sy, px, py in pairs:
                offset = (px - scale * sx, py + scale * sy)
                bucket = (
                    round(offset[0] / OFFSET_BUCKET_CM),
                    round(offset[1] / OFFSET_BUCKET_CM),
                )
                buckets[bucket].append(offset)
    winner = _peak(buckets)
    if winner is None or len(winner) < MIN_VERIFIED_SEGMENTS:
        return None
    return (
        sum(offset[0] for offset in winner) / len(winner),
        sum(offset[1] for offset in winner) / len(winner),
    )


def recover_placement(
    tex_text: str,
    ink_segments: list[tuple[float, float, float, float]],
) -> Placement | None:
    """Return the fixture's verified source-cm to PDF-cm placement, or None.

    The placement is voted on by the source segments that the render draws at a
    consistent scale and offset, then verified by re-projecting every source
    segment onto the render.  None means the two cannot be reconciled, which the
    caller reports: nothing may be measured against an unverified placement.
    """
    source = _directed(source_segments(tex_text), flip_y=True)
    ink = _directed(ink_segments, flip_y=False)
    if len(source) < MIN_VERIFIED_SEGMENTS or not ink:
        return None
    scale = _vote_scale(source, ink)
    if scale is None or scale <= 0.0:
        return None
    offset = _vote_offset(source, ink, scale)
    if offset is None:
        return None
    placement = Placement(
        scale=scale,
        offset_x_cm=offset[0],
        offset_y_cm=offset[1],
        verified_segments=0,
        source_segments=len(source),
    )
    long_ink = [(iax, iay, ibx, iby) for iax, iay, ibx, iby, _, _, _ in ink]
    verified = 0
    for sax, say, sbx, sby, _, _, _ in source:
        start = placement.project(sax, say)
        end = placement.project(sbx, sby)
        if (
            _nearest_ink(*start, long_ink, INK_MATCH_TOLERANCE_CM) <= INK_MATCH_TOLERANCE_CM
            and _nearest_ink(*end, long_ink, INK_MATCH_TOLERANCE_CM) <= INK_MATCH_TOLERANCE_CM
        ):
            verified += 1
    if verified / len(source) < MIN_VERIFIED_RATIO:
        return None
    return Placement(
        scale=placement.scale,
        offset_x_cm=placement.offset_x_cm,
        offset_y_cm=placement.offset_y_cm,
        verified_segments=verified,
        source_segments=len(source),
    )


def selector_names_an_operation(tex_text: str, selector_line: int) -> bool:
    """Report whether any drawing operation starts in the selector's line span."""
    return any(
        selector_line <= int(operation["source_line"]) <= selector_line + SELECTOR_LINE_SPAN
        for operation in _iter_tikz_operations(tex_text)
    )


def bound_element_shapes(
    tex_text: str,
    selector_line: int,
    placement: Placement,
) -> list[tuple[str, tuple[float, ...]]]:
    """Return the shapes of the operation the selector names, in PDF cm.

    An empty list means the operation carries no geometry this parser can read,
    which the caller reports rather than silently skipping the measurement.
    """
    candidates = [
        geometry
        for geometry in source_geometry(tex_text)
        if selector_line <= geometry["source_line"] <= selector_line + SELECTOR_LINE_SPAN
    ]
    if not candidates:
        return []
    first_line = min(geometry["source_line"] for geometry in candidates)
    shapes: list[tuple[str, tuple[float, ...]]] = []
    for geometry in candidates:
        if geometry["source_line"] != first_line:
            continue
        for shape, values in source_shapes(geometry, flatten_curves=True):
            if shape == "area":
                x0, y0, x1, y1 = values
                a = placement.project(x0, y1)
                b = placement.project(x1, y0)
                shapes.append(("area", (a[0], a[1], b[0], b[1])))
            elif shape == "disc":
                cx, cy, radius = values
                px, py = placement.project(cx, cy)
                shapes.append(("disc", (px, py, radius * placement.scale)))
            else:
                ax, ay, bx, by = values
                start = placement.project(ax, ay)
                end = placement.project(bx, by)
                shapes.append(("segment", (start[0], start[1], end[0], end[1])))
    return shapes


def _shape_distance(px: float, py: float, shape: tuple[str, tuple[float, ...]]) -> float:
    name, values = shape
    if name == "area":
        x0, y0, x1, y1 = values
        return math.hypot(max(x0 - px, 0.0, px - x1), max(y0 - py, 0.0, py - y1))
    if name == "disc":
        cx, cy, radius = values
        return max(0.0, math.hypot(px - cx, py - cy) - radius)
    return point_segment_distance(px, py, *values)


def path_gap_cm(
    points_pdf_cm: list[tuple[float, float]],
    shapes: list[tuple[str, tuple[float, ...]]],
) -> tuple[float, tuple[float, float]]:
    """Return the declared path's worst distance from the bound element, and where."""
    worst = 0.0
    worst_at = points_pdf_cm[0]
    for (ax, ay), (bx, by) in zip(points_pdf_cm, points_pdf_cm[1:], strict=False):
        steps = max(1, int(math.hypot(bx - ax, by - ay) / PATH_SAMPLE_STEP_CM))
        for step in range(steps + 1):
            t = step / steps
            px = ax + t * (bx - ax)
            py = ay + t * (by - ay)
            distance = min(_shape_distance(px, py, shape) for shape in shapes)
            if distance > worst:
                worst = distance
                worst_at = (px, py)
    return worst, worst_at
