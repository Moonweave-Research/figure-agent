"""Rewrite a straight two-point draw into a detour chain that clears a neighbour.

Composition-level counterpart to the bounded coordinate nudge: instead of
translating a line, it reroutes it over or under the obstacle's bounding box
via two waypoints, preserving both endpoint literals (topology is untouched).
Everything it cannot prove safe it refuses: the line must contain exactly one
two-point ``--`` segment and no other geometry, both endpoints must sit clear
of the obstacle's x-range, and the detour must stay inside MAX_DETOUR_CM.

The construction is conservative against the clearance detector: the detour
keeps ``clearance + CLEARANCE_PAD_CM`` to the obstacle's bbox, and any element
inside a bbox is at least that far from the new chain.
"""

from __future__ import annotations

import re
from typing import Any

MAX_DETOUR_CM = 1.5
CLEARANCE_PAD_CM = 0.05

_POINT_RE = re.compile(r"\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)")
_SEGMENT_RE = re.compile(
    r"(?P<start>\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\))"
    r"\s*--\s*"
    r"(?P<end>\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\))"
)
_FORBIDDEN_TOKENS = ("circle", "rectangle", "..", "grid", "to[")


def _format_cm(value: float) -> str:
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text if text not in {"", "-"} else "0"


def parse_two_point_draw(line: str) -> dict[str, Any] | None:
    """Return the single straight segment of a draw line, or None to refuse."""
    if any(token in line for token in _FORBIDDEN_TOKENS):
        return None
    if len(_POINT_RE.findall(line)) != 2:
        return None
    matches = list(_SEGMENT_RE.finditer(line))
    if len(matches) != 1:
        return None
    match = matches[0]
    x0, y0 = float(match.group(2)), float(match.group(3))
    x1, y1 = float(match.group(5)), float(match.group(6))
    return {
        "start": (x0, y0),
        "end": (x1, y1),
        "start_text": match.group("start"),
        "end_text": match.group("end"),
        "span": (match.start(), match.end()),
    }


def reroute_detour(
    line: str,
    *,
    obstacle_bbox_cm: list[float],
    clearance_cm: float,
) -> dict[str, Any] | None:
    """Build the detour replacement for one line, or None to refuse."""
    segment = parse_two_point_draw(line)
    if segment is None:
        return None
    if clearance_cm <= 0 or len(obstacle_bbox_cm) != 4:
        return None
    x_min, y_min, x_max, y_max = (float(value) for value in obstacle_bbox_cm)
    (sx, sy), (ex, ey) = segment["start"], segment["end"]
    margin = clearance_cm + CLEARANCE_PAD_CM
    # The vertical connectors run at the endpoint x-positions; both must
    # already be clear of the obstacle band or the detour cannot help.
    for x in (sx, ex):
        if x_min - margin < x < x_max + margin:
            return None
    routes = (
        ("reroute_over_neighbor", y_max + margin),
        ("reroute_under_neighbor", y_min - margin),
    )
    best: tuple[str, float, float] | None = None
    for template_id, waypoint_y in routes:
        detour = max(abs(waypoint_y - sy), abs(waypoint_y - ey))
        if detour > MAX_DETOUR_CM:
            continue
        if best is None or detour < best[2]:
            best = (template_id, waypoint_y, detour)
    if best is None:
        return None
    template_id, waypoint_y, _detour = best
    waypoint_text = _format_cm(waypoint_y)
    chain = (
        f"{segment['start_text']} -- ({_format_cm(sx)},{waypoint_text}) -- "
        f"({_format_cm(ex)},{waypoint_text}) -- {segment['end_text']}"
    )
    span_start, span_end = segment["span"]
    return {
        "replacement": line[:span_start] + chain + line[span_end:],
        "template_id": template_id,
        "waypoint_y_cm": waypoint_y,
        "predicted_clearance_cm": round(margin, 6),
    }
