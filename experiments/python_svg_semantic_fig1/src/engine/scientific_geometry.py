from __future__ import annotations

import math

from engine.scene import Point, Rect


def gaussian_lobe_points(
    anchor: Point,
    *,
    width: float,
    height: float,
    samples: int = 48,
    upper_sigma: float = 0.34,
    lower_sigma: float = 0.46,
) -> tuple[Point, ...]:
    points: list[Point] = []
    for index in range(samples):
        fraction = index / (samples - 1)
        offset = fraction - 0.5
        sigma = upper_sigma if offset < 0 else lower_sigma
        profile = math.exp(-0.5 * (offset / sigma) ** 2)
        # Taper the lobe to meet the energy axis cleanly at both ends.
        taper = math.sin(math.pi * fraction) ** 0.34
        x = anchor.x + width * profile * taper
        y = anchor.y - height / 2 + fraction * height
        points.append(Point(x, y))
    return tuple(points)


def pe_hysteresis_points(
    center: Point,
    *,
    width: float,
    height: float,
    remanence: float,
    samples_per_branch: int = 40,
) -> tuple[Point, ...]:
    coercive = max(0.12, min(0.42, remanence * 0.62))
    saturation = 0.92
    points: list[Point] = []
    for index in range(samples_per_branch):
        u = -1.0 + 2.0 * index / (samples_per_branch - 1)
        polarization = saturation * math.tanh(2.55 * (u + coercive))
        points.append(_map_pe(center, width, height, u, polarization))
    for index in range(samples_per_branch):
        u = 1.0 - 2.0 * index / (samples_per_branch - 1)
        polarization = saturation * math.tanh(2.55 * (u - coercive))
        points.append(_map_pe(center, width, height, u, polarization))
    return tuple(points)


def power_law_loglog_points(
    rect: Rect,
    *,
    slope: float,
    log_t_min: float = -3.0,
    log_t_max: float = 3.0,
    log_i_top: float = 0.0,
    log_i_bottom: float = -8.0,
    samples: int = 42,
) -> tuple[Point, ...]:
    usable = rect.inset(18, 18)
    log_t_span = log_t_max - log_t_min
    log_i_start = log_i_top - 0.35
    points: list[Point] = []
    for index in range(samples):
        fraction = index / (samples - 1)
        log_t = log_t_min + fraction * log_t_span
        log_i = log_i_start + slope * (log_t - log_t_min)
        y_fraction = (log_i_top - log_i) / (log_i_top - log_i_bottom)
        y_fraction = max(0.04, min(0.96, y_fraction))
        points.append(Point(usable.x + fraction * usable.width, usable.y + y_fraction * usable.height))
    return tuple(points)


def _map_pe(center: Point, width: float, height: float, field: float, polarization: float) -> Point:
    return Point(center.x + field * width / 2, center.y - polarization * height / 2)
