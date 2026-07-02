"""Bounded, value-preserving TikZ text-width primitive.

Changing a node's `text width` reflows its wrap (e.g. collapses a 2-line caption to
1 line) without touching the rendered text — a footprint edit the coordinate-offset
family cannot author. Its safety is the post-apply verifier (labels_unchanged +
finding-recheck + auto-rollback); this delta cap only stops an absurd width change.
"""

from __future__ import annotations

import re

MAX_TEXT_WIDTH_DELTA_CM = 4.0
_TEXT_WIDTH_RE = re.compile(r"text width\s*=\s*(?P<w>-?\d+(?:\.\d+)?)\s*cm")


def set_text_width(line: str, *, target_cm: float) -> str | None:
    """Replace the node's `text width=Xcm` with target_cm. Returns None when the
    line has no text-width key, the target is non-positive, or the change exceeds
    MAX_TEXT_WIDTH_DELTA_CM from the current width."""
    if target_cm <= 0:
        return None
    match = _TEXT_WIDTH_RE.search(line)
    if match is None:
        return None
    current = float(match.group("w"))
    if abs(target_cm - current) > MAX_TEXT_WIDTH_DELTA_CM:
        return None
    return _TEXT_WIDTH_RE.sub(f"text width={target_cm:.2f}cm", line, count=1)
