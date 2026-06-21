"""Render-ship equivalence gate (spec §5 H3): does the shipped PDF render faithfully
show each truth-bearing path? Pure colour/coord/sampling logic here is render-free
and unit-testable; the render adapter (rsvg-convert + pdftoppm) is the only part that
needs system tools.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np

_NAMED_COLORS = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "none": None,
}


def _parse_color(value: str | None) -> tuple[int, int, int] | None:
    """Parse an SVG colour string to an RGB triple. Returns None for absent,
    `none`, or any form we do not parse (e.g. `url(#grad)`) — such paths are
    simply not colour-checked rather than crashing the gate."""
    if not value:
        return None
    token = value.strip().lower()
    if token in _NAMED_COLORS:
        return _NAMED_COLORS[token]
    match = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", token)
    if not match:
        return None
    digits = match.group(1)
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    return (int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16))


def _svg_to_pixel(
    point: complex,
    viewbox: tuple[float, float, float, float],
    *,
    raster_w: int,
    raster_h: int,
) -> tuple[int, int]:
    """Map an SVG user-space point to an (x, y) raster pixel, clamped in-bounds."""
    min_x, min_y, width, height = viewbox
    fx = (point.real - min_x) / width if width else 0.0
    fy = (point.imag - min_y) / height if height else 0.0
    px = min(max(int(round(fx * raster_w)), 0), raster_w - 1)
    py = min(max(int(round(fy * raster_h)), 0), raster_h - 1)
    return (px, py)


# per-channel L-infinity tolerance. 60 is intentionally tight: it passes pure
# rendered colours while rejecting semi-transparent variants (e.g. stroke-opacity=0.5
# red renders channel-127 over white). Task 3 adds _blend_to_white to match those.
COLOR_DELTA = 60


def _color_present_near(
    raster: np.ndarray,
    pixel: tuple[int, int],
    colors: set[tuple[int, int, int]],
    *,
    radius: int = 2,
    delta: int = COLOR_DELTA,
) -> bool:
    """True if any declared colour appears within a `radius`-pixel window of `pixel`.
    The window is ESSENTIAL (verified empirically, see "Review hardening"): a truth
    path's polyline traces the path *outline*, so for a FILLED region the on-line
    pixels straddle the antialiased fill/background edge (~50% background). A single
    centre sample false-BLOCKERs a faithfully-rendered filled region; the window
    catches the fill colour 1-2px inside the edge. It does NOT weaken occlusion
    detection — an opaque cover leaves no declared colour anywhere near the point."""
    px, py = pixel
    raster_h, raster_w = raster.shape[0], raster.shape[1]
    for yy in range(max(0, py - radius), min(raster_h, py + radius + 1)):
        for xx in range(max(0, px - radius), min(raster_w, px + radius + 1)):
            sample = raster[yy, xx]
            if any(
                all(abs(int(sample[i]) - color[i]) <= delta for i in range(3)) for color in colors
            ):
                return True
    return False


MIN_MATCH_FRACTION = 0.5  # at least this fraction of on-path samples must match


def detect_render_ship_divergence(
    raster: np.ndarray,
    truth_paths: list[dict[str, Any]],
    viewbox: tuple[float, float, float, float],
    *,
    min_match_fraction: float = MIN_MATCH_FRACTION,
) -> list[dict[str, str]]:
    """BLOCKER findings for truth paths whose rendered on-path colours diverge from
    every declared colour. `truth_paths` items: {id, polyline (list[complex]), colors
    (set of RGB triples — declared fill/stroke PLUS their opacity-blended variants,
    assembled in `_truth_samples`)}. Each polyline point is matched via a small window
    (`_color_present_near`) so a filled region's outline samples still match. Paths
    with an empty `colors` set are skipped (not checkable, not a crash)."""
    raster_h, raster_w = raster.shape[0], raster.shape[1]
    findings: list[dict[str, str]] = []
    for entry in sorted(truth_paths, key=lambda item: item["id"]):
        colors = entry["colors"]
        polyline = entry["polyline"]
        if not colors or not polyline:
            continue
        matched = 0
        for point in polyline:
            pixel = _svg_to_pixel(point, viewbox, raster_w=raster_w, raster_h=raster_h)
            if _color_present_near(raster, pixel, colors):
                matched += 1
        fraction = matched / len(polyline)
        if fraction < min_match_fraction:
            findings.append(
                {
                    "id": f"RS{len(findings) + 1:03d}",
                    "kind": "render_ship_divergence",
                    "severity": "BLOCKER",
                    "evidence": (
                        f"truth path #{entry['id']} renders unfaithfully: only "
                        f"{matched}/{len(polyline)} on-path samples match a declared "
                        "colour (covered, filtered, or renderer-shifted)"
                    ),
                    "recommended_route": "semantic_backport_required",
                }
            )
    return findings
