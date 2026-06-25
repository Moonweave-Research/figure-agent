"""Bounded, value-preserving TikZ coordinate translation primitive."""

from __future__ import annotations

import re

MAX_TRANSLATE_CM = 0.10
_AXIS_ALIGN_TOL_PT = 0.5
_COORD_RE = re.compile(
    r"(?P<lead>(?:at\s*)?)"
    r"\(\s*(?P<x>-?\d+(?:\.\d+)?)\s*,\s*(?P<y>-?\d+(?:\.\d+)?)\s*\)"
)


def offset_first_coordinate(line: str, *, dx_cm: float = MAX_TRANSLATE_CM) -> str | None:
    if abs(dx_cm) > MAX_TRANSLATE_CM:
        return None
    match = _COORD_RE.search(line)
    if match is None:
        return None
    new_x = float(match.group("x")) + dx_cm
    replacement = f"{match.group('lead')}({new_x:.2f}, {match.group('y')})"
    return _COORD_RE.sub(replacement, line, count=1)


def offset_all_coordinates(line: str, *, axis: str, dx_cm: float) -> str | None:
    """Translate every (x,y) on a line by dx_cm on the given axis (whole-line move)."""
    if axis not in ("x", "y") or abs(dx_cm) > MAX_TRANSLATE_CM:
        return None
    if _COORD_RE.search(line) is None:
        return None

    def _shift(match: re.Match[str]) -> str:
        old_x = float(match.group("x"))
        old_y = float(match.group("y"))
        if axis == "x":
            return f"{match.group('lead')}({old_x + dx_cm:.2f}, {match.group('y')})"
        return f"{match.group('lead')}({match.group('x')}, {old_y + dx_cm:.2f})"

    return _COORD_RE.sub(_shift, line)


def offset_direction(
    line_bbox_pt: list[float],
    word_bbox_pt: list[float],
) -> tuple[str, float] | None:
    """Pick the tikz axis + signed offset that moves a near-miss line away from text.

    Inputs are PDF-point bboxes (pdfplumber: y grows downward). A horizontal line
    moves on tikz-y; a vertical line moves on tikz-x. Returns None for any line that
    is neither axis-aligned. The tikz sign accounts for the standard TikZ->PDF
    y-flip (pt-y grows opposite to tikz-y; pt-x shares tikz-x's direction).
    """
    x0, y0, x1, y1 = line_bbox_pt[0], line_bbox_pt[1], line_bbox_pt[2], line_bbox_pt[3]
    wx0, wy0, wx1, wy1 = word_bbox_pt[0], word_bbox_pt[1], word_bbox_pt[2], word_bbox_pt[3]
    horizontal = abs(y0 - y1) <= _AXIS_ALIGN_TOL_PT and abs(x0 - x1) > _AXIS_ALIGN_TOL_PT
    vertical = abs(x0 - x1) <= _AXIS_ALIGN_TOL_PT and abs(y0 - y1) > _AXIS_ALIGN_TOL_PT
    if horizontal == vertical:
        return None
    if horizontal:
        line_pt = (y0 + y1) / 2.0
        word_pt = (wy0 + wy1) / 2.0
        # Move the line in pt-y AWAY from the word, then flip pt-y -> tikz-y.
        away_pt = MAX_TRANSLATE_CM if line_pt >= word_pt else -MAX_TRANSLATE_CM
        return ("y", -away_pt)
    line_pt = (x0 + x1) / 2.0
    word_pt = (wx0 + wx1) / 2.0
    # x is not flipped between pt and tikz.
    away_pt = MAX_TRANSLATE_CM if line_pt >= word_pt else -MAX_TRANSLATE_CM
    return ("x", away_pt)
