"""Geometry-derived label_refit proposal (Approach 2).

Derives the refit magnitudes the eye used to hand-supply (text-width + reposition)
from the figure itself: the crossed reference line's coordinate is read from the
figure's own TikZ `\\draw` (exact, no fragile pixel line-detection, no resizebox
scale recovery), and the wrap line-count is measured from the render. No eye
input. The derived proposal still rides the existing fail-loud verifier (4a/4b),
so a bad derivation is rejected and rolled back, never trusted blindly.
"""

from __future__ import annotations

import re
import statistics

# A reference line the label crosses is at most this far below the node anchor.
MAX_CROSS_DISTANCE_CM = 1.0
# Drop the repositioned node top this far below the crossed line. Dogfooded on
# fig2: 0.05cm sits in the detector's noise band at the line (still flagged), 0.20cm
# drifts toward the next element below (re-flags); 0.10-0.15cm clears robustly. A
# too-large drop that hits a lower element is caught by the new-crossing verifier.
CLEAR_MARGIN_CM = 0.12
# Headroom on the collapsed text-width: lines x current-width is ~the natural
# 1-line width, but AT the natural width the text wraps back to 2 lines on kerning
# rounding (dogfooded on fig2: 5.20cm still wrapped; 5.6cm cleared). 10% guarantees
# one line; a too-wide box is caught by the new-crossing verifier (4a) anyway.
WIDTH_MARGIN = 1.10

_COORD_RE = re.compile(r"at\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)")
_TEXT_WIDTH_RE = re.compile(r"text width\s*=\s*(-?\d+(?:\.\d+)?)\s*cm")
_DRAW_SEG_RE = re.compile(
    r"\\draw\b[^\n]*?\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)"
    r"\s*--\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)"
)


def parse_node(node_line: str) -> tuple[float, float, float] | None:
    """Return (x, y, text_width_cm) for a node line carrying both a coordinate and
    a text-width key, else None."""
    coord = _COORD_RE.search(node_line)
    width = _TEXT_WIDTH_RE.search(node_line)
    if coord is None or width is None:
        return None
    return (float(coord.group(1)), float(coord.group(2)), float(width.group(1)))


def nearest_crossed_hline(
    node_x: float,
    node_y: float,
    tex_lines: list[str],
    *,
    max_distance_cm: float = MAX_CROSS_DISTANCE_CM,
) -> float | None:
    """Y of the horizontal `\\draw` the node crosses: the closest one BELOW the node
    anchor (within max_distance_cm) whose x-span contains node_x. None if none."""
    best: float | None = None
    for line in tex_lines:
        match = _DRAW_SEG_RE.search(line)
        if match is None:
            continue
        x1, y1, x2, y2 = (float(match.group(i)) for i in range(1, 5))
        if abs(y1 - y2) > 1e-6:  # not horizontal
            continue
        if not min(x1, x2) <= node_x <= max(x1, x2):
            continue
        if not 0 < node_y - y1 <= max_distance_cm:
            continue
        if best is None or y1 > best:
            best = y1
    return best


def count_lines(word_boxes: list[tuple[int, int, int, int]]) -> int:
    """Number of wrapped lines a node renders to, from its words' px bboxes: total
    vertical extent / a single line's height (the median word-box height)."""
    if not word_boxes:
        return 1
    word_h = statistics.median(b[3] - b[1] for b in word_boxes)
    if word_h <= 0:
        return 1
    total_h = max(b[3] for b in word_boxes) - min(b[1] for b in word_boxes)
    return max(1, round(total_h / word_h))


def node_line_count(node_text: str, words: list[dict]) -> int:
    """Wrapped line count of a node from its rendered words. `node_text` is the
    node's `{...}` content; matches its whitespace tokens against the pdftotext
    `words` (pt bboxes — count_lines uses a height RATIO, so pt vs px cancels)."""
    tokens = set(node_text.split())
    boxes = [
        (word["xmin"], word["ymin"], word["xmax"], word["ymax"])
        for word in words
        if word.get("text") in tokens
    ]
    return count_lines(boxes) if boxes else 1


def derive_refit(
    node_line: str,
    tex_lines: list[str],
    lines_count: int,
) -> dict | None:
    """Derive a value-preserving label_refit proposal from the figure itself: widen
    the node so its `lines_count`-line wrap collapses to one line, and drop it just
    below the crossed reference line. Returns None when the node lacks a text-width
    or no crossed horizontal line is found."""
    parsed = parse_node(node_line)
    if parsed is None:
        return None
    node_x, node_y, current_width = parsed
    line_y = nearest_crossed_hline(node_x, node_y, tex_lines)
    if line_y is None:
        return None
    text_width_cm = round(lines_count * current_width * WIDTH_MARGIN, 2)
    dx_cm = round((line_y - CLEAR_MARGIN_CM) - node_y, 2)
    return {
        "edit_class": "label_refit",
        "text_width_cm": text_width_cm,
        "reposition": {"axis": "y", "dx_cm": dx_cm},
    }
