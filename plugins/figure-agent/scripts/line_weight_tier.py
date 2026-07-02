"""Bounded, value-preserving line-weight tier primitive.

Rewrites a TikZ path's `line width=Xpt` stroke to one of three NAMED narrative
tiers, addressing the uniform_line_weight_monotony anti-pattern. Only the width
numeral changes; geometry, color, and labels are untouched.
"""

from __future__ import annotations

import re

TIERS: dict[str, float] = {"primary": 0.9, "annotation": 0.7, "secondary": 0.55}
FLOOR_PT = 0.5
_WIDTH_RE = re.compile(r"line width\s*=\s*(?P<w>\d*\.?\d+)pt")


def retier_line_width(line: str, *, tier: str) -> str | None:
    if tier not in TIERS:
        return None
    if _WIDTH_RE.search(line) is None:
        return None
    replacement = f"line width={TIERS[tier]:.2f}pt"
    return _WIDTH_RE.sub(replacement, line, count=1)
