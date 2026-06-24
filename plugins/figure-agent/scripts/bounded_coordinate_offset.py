"""Bounded, value-preserving TikZ coordinate translation primitive."""

from __future__ import annotations

import re

MAX_TRANSLATE_CM = 0.10
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
