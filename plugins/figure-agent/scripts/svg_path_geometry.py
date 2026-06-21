"""Pure geometry for the truth lock: canonical sampling + shape signature.

No SVG-tree or file I/O here — input is a path 'd' string, output is plain
numbers. Keeps the geometry math testable in isolation.
"""

from __future__ import annotations

from svgpathtools import parse_path


def canonical_polyline(d: str, *, samples: int = 256) -> list[complex]:
    """Resample every subpath of `d` to `samples` points by arc length.

    Arc-length sampling is representation-invariant: two `d` strings that draw
    the same curve return near-identical point lists regardless of how many
    segments or control points each uses. Subpaths are concatenated in order.
    """
    path = parse_path(d)
    if path.length() == 0:
        # Degenerate (point/empty): repeat the start so callers get `samples` pts.
        start = path.start if len(path) else 0j
        return [start] * samples
    return [path.point(i / (samples - 1)) for i in range(samples)]
