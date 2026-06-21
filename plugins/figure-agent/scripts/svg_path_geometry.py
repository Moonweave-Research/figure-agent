"""Pure geometry for the truth lock: canonical sampling + shape signature.

No SVG-tree or file I/O here — input is a path 'd' string, output is plain
numbers. Keeps the geometry math testable in isolation.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass

from svgpathtools import parse_path

CORNER_TURN_THRESHOLD = math.radians(35.0)  # turning angle that counts as a corner
_FLAT = 1e-3  # below this |turn| the segment is treated as straight


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


@dataclass(frozen=True)
class ShapeSignature:
    corner_count: int
    sign_pattern: tuple[int, ...]  # consecutive distinct turn-signs (inflection structure)


def _turn_angles(points: list[complex]) -> list[float]:
    """Signed turn angle at each interior vertex (left = +, right = -)."""
    angles: list[float] = []
    for i in range(1, len(points) - 1):
        v1 = points[i] - points[i - 1]
        v2 = points[i + 1] - points[i]
        if v1 == 0 or v2 == 0:
            angles.append(0.0)
            continue
        angles.append(cmath.phase(v2 / v1))  # signed turn in (-pi, pi]
    return angles


def shape_signature(d: str, *, samples: int = 256) -> ShapeSignature:
    pts = canonical_polyline(d, samples=samples)
    turns = _turn_angles(pts)
    # Count corner *runs*: consecutive above-threshold samples that straddle the
    # same geometric corner count as one, not as many individual points.
    corner_count = 0
    in_corner = False
    for a in turns:
        if abs(a) >= CORNER_TURN_THRESHOLD:
            if not in_corner:
                corner_count += 1
                in_corner = True
        else:
            in_corner = False
    # Collapse consecutive equal turn-signs to one entry. The PATTERN of
    # left/straight/right transitions is resample-invariant (run *lengths* are
    # not, so they are dropped); it captures inflection structure.
    pattern: list[int] = []
    for a in turns:
        sign = (a > _FLAT) - (a < -_FLAT)  # +1 / 0 / -1
        if not pattern or pattern[-1] != sign:
            pattern.append(sign)
    return ShapeSignature(corner_count=corner_count, sign_pattern=tuple(pattern))


def frechet_distance(p: list[complex], q: list[complex]) -> float:
    """Discrete Fréchet distance between two polylines (iterative, O(n*m))."""
    n, m = len(p), len(q)
    if n == 0 or m == 0:
        return float("inf")
    prev = [0.0] * m
    for i in range(n):
        cur = [0.0] * m
        for j in range(m):
            d = abs(p[i] - q[j])
            if i == 0 and j == 0:
                cur[j] = d
            elif i == 0:
                cur[j] = max(cur[j - 1], d)
            elif j == 0:
                cur[j] = max(prev[j], d)
            else:
                cur[j] = max(min(prev[j], prev[j - 1], cur[j - 1]), d)
        prev = cur
    return prev[-1]
