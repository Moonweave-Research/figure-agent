from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import matplotlib.ticker as mticker
import numpy as np

from engine.scene import Point, Rect


AxisName = Literal["x", "y"]


@dataclass(frozen=True)
class PlotTick:
    axis: AxisName
    value: float
    point: Point
    label: str | None
    major: bool


@dataclass(frozen=True)
class PlotLabel:
    value: str
    point: Point
    size: float
    anchor: Literal["start", "middle", "end"] = "start"


@dataclass(frozen=True)
class PlotSegment:
    start: Point
    end: Point


@dataclass(frozen=True)
class ScientificPlotPlan:
    frame: Rect
    major_ticks: tuple[PlotTick, ...]
    minor_ticks: tuple[PlotTick, ...]
    curve_points: tuple[Point, ...]
    curve_labels: tuple[PlotLabel, ...]
    axis_labels: tuple[PlotLabel, ...]
    guide_segments: tuple[PlotSegment, ...] = ()


def power_law_decay_plan(
    bounds: Rect,
    *,
    slope: float,
    log_t_min: float,
    log_t_max: float,
    log_i_top: float,
    log_i_bottom: float,
    samples: int,
    label: str,
) -> ScientificPlotPlan:
    frame = _frame(bounds, left=26, top=14, right=8, bottom=28)
    major_ticks = _log_ticks(
        frame,
        axis="x",
        log_min=log_t_min,
        log_max=log_t_max,
        label_stride=2,
    ) + _log_ticks(
        frame,
        axis="y",
        log_min=log_i_bottom,
        log_max=log_i_top,
        label_stride=4,
    )
    minor_ticks = _log_minor_ticks(frame, axis="x", log_min=log_t_min, log_max=log_t_max) + _log_minor_ticks(
        frame,
        axis="y",
        log_min=log_i_bottom,
        log_max=log_i_top,
    )

    log_t_values = np.linspace(log_t_min, log_t_max, max(2, samples))
    log_i_start = log_i_top - 0.34
    points = tuple(
        Point(
            _map_linear(float(log_t), log_t_min, log_t_max, frame.x, frame.right),
            _map_linear(
                max(log_i_bottom, min(log_i_top, float(log_i_start + slope * (log_t - log_t_min)))),
                log_i_top,
                log_i_bottom,
                frame.y,
                frame.bottom,
            ),
        )
        for log_t in log_t_values
    )
    label_anchor = points[min(len(points) - 1, max(0, int(len(points) * 0.36)))]
    curve_label = _label_inside(label, Point(label_anchor.x + 10, label_anchor.y - 8), frame, size=10.4)

    guide_anchor = points[min(len(points) - 1, max(0, int(len(points) * 0.43)))]
    guide_vertical_end = Point(guide_anchor.x, min(frame.bottom - 20, guide_anchor.y + 30))
    guide_horizontal_end = Point(min(frame.right - 8, guide_vertical_end.x + 42), guide_vertical_end.y)
    slope_label = _label_inside("slope -n", Point(guide_horizontal_end.x - 3, guide_horizontal_end.y - 5), frame, size=8.7, anchor="end")

    return ScientificPlotPlan(
        frame=frame,
        major_ticks=major_ticks,
        minor_ticks=minor_ticks,
        curve_points=points,
        curve_labels=(curve_label, slope_label),
        axis_labels=(
            PlotLabel("log t", Point(frame.right - 3, frame.bottom + 24), 8.8, "end"),
            PlotLabel("log I", Point(frame.x + 5, frame.y + 11), 8.8, "start"),
        ),
        guide_segments=(PlotSegment(guide_anchor, guide_vertical_end), PlotSegment(guide_vertical_end, guide_horizontal_end)),
    )


def pe_hysteresis_plan(
    bounds: Rect,
    *,
    loop_width: float,
    loop_height: float,
    remanence: float,
    samples_per_branch: int,
    label: str,
) -> ScientificPlotPlan:
    frame = _frame(bounds, left=28, top=14, right=8, bottom=28)
    major_ticks = _linear_ticks(frame, axis="x", low=-1.0, high=1.0, nbins=4) + _linear_ticks(
        frame,
        axis="y",
        low=-1.0,
        high=1.0,
        nbins=4,
    )
    field_scale = min(0.92, max(0.52, loop_width / 170.0))
    polarization_scale = min(0.90, max(0.52, loop_height / 112.0))
    coercive = max(0.12, min(0.43, remanence * 0.62))
    saturation = 0.94
    branch_samples = max(24, samples_per_branch)
    forward = np.linspace(-1.0, 1.0, branch_samples)
    reverse = np.linspace(1.0, -1.0, branch_samples)
    points: list[Point] = []
    for value in forward:
        polarization = saturation * math.tanh(2.85 * (float(value) + coercive))
        points.append(_map_pe_point(frame, float(value), polarization, field_scale, polarization_scale))
    for value in reverse:
        polarization = saturation * math.tanh(2.85 * (float(value) - coercive))
        points.append(_map_pe_point(frame, float(value), polarization, field_scale, polarization_scale))

    return ScientificPlotPlan(
        frame=frame,
        major_ticks=major_ticks,
        minor_ticks=(),
        curve_points=tuple(points),
        curve_labels=(_label_inside(label, Point(frame.x + frame.width * 0.55, frame.y + 20), frame, size=9.0),),
        axis_labels=(
            PlotLabel("E", Point(frame.right - 3, frame.bottom + 24), 9.0, "end"),
            PlotLabel("P", Point(frame.x + 5, frame.y + 11), 9.0, "start"),
        ),
    )


def ispd_dos_plan(
    bounds: Rect,
    *,
    shallow_width: float,
    deep_width: float,
    shallow_height: float,
    deep_height: float,
    samples: int,
    label: str,
) -> ScientificPlotPlan:
    frame = _frame(bounds, left=22, top=12, right=8, bottom=26)
    major_ticks = _linear_ticks(frame, axis="x", low=0.0, high=1.0, nbins=3) + _linear_ticks(
        frame,
        axis="y",
        low=0.0,
        high=1.0,
        nbins=3,
    )
    y = np.linspace(0.0, 1.0, max(24, samples))
    shallow_center = 0.36
    deep_center = 0.68
    shallow_profile = _asymmetric_gaussian(y, shallow_center, shallow_height / max(deep_height, 1.0), shallow_width / max(deep_width, 1.0))
    deep_profile = _asymmetric_gaussian(y, deep_center, 1.0, 1.0)
    shallow_points = tuple(_map_dos_point(frame, y_value, profile, 0.38) for y_value, profile in zip(y, shallow_profile, strict=True))
    deep_points = tuple(_map_dos_point(frame, y_value, profile, 0.84) for y_value, profile in zip(y, deep_profile, strict=True))
    curve_points = shallow_points + deep_points
    return ScientificPlotPlan(
        frame=frame,
        major_ticks=major_ticks,
        minor_ticks=(),
        curve_points=curve_points,
        curve_labels=(_label_inside(label, Point(frame.x + frame.width * 0.40, frame.y + 14), frame, size=8.7),),
        axis_labels=(
            PlotLabel("Et", Point(frame.right - 3, frame.bottom + 23), 8.5, "end"),
            PlotLabel("g(Et)", Point(frame.x + 4, frame.y + 10), 8.5, "start"),
        ),
    )


def _frame(bounds: Rect, *, left: float, top: float, right: float, bottom: float) -> Rect:
    return Rect(bounds.x + left, bounds.y + top, bounds.width - left - right, bounds.height - top - bottom)


def _log_ticks(
    frame: Rect,
    *,
    axis: AxisName,
    log_min: float,
    log_max: float,
    label_stride: int,
) -> tuple[PlotTick, ...]:
    locator = mticker.LogLocator(base=10.0, subs=(1.0,), numticks=16)
    formatter = mticker.FuncFormatter(lambda value, _position=None: f"10^{int(round(math.log10(value)))}")
    values = locator.tick_values(10.0**log_min, 10.0**log_max)
    ticks: list[PlotTick] = []
    exponents = sorted(
        {
            int(round(math.log10(float(value))))
            for value in values
            if value > 0 and log_min - 1e-9 <= math.log10(float(value)) <= log_max + 1e-9
        }
    )
    for index, exponent in enumerate(exponents):
        point = _log_tick_point(frame, axis, float(exponent), log_min, log_max)
        label = _format_power_tick(exponent, formatter) if index % label_stride == 0 or index == len(exponents) - 1 else None
        ticks.append(PlotTick(axis=axis, value=float(exponent), point=point, label=label, major=True))
    return tuple(ticks)


def _log_minor_ticks(frame: Rect, *, axis: AxisName, log_min: float, log_max: float) -> tuple[PlotTick, ...]:
    locator = mticker.LogLocator(base=10.0, subs=(2.0, 5.0), numticks=100)
    values = locator.tick_values(10.0**log_min, 10.0**log_max)
    ticks: list[PlotTick] = []
    for value in values:
        log_value = math.log10(float(value))
        if log_min + 1e-9 < log_value < log_max - 1e-9:
            ticks.append(PlotTick(axis=axis, value=log_value, point=_log_tick_point(frame, axis, log_value, log_min, log_max), label=None, major=False))
    return tuple(ticks)


def _linear_ticks(frame: Rect, *, axis: AxisName, low: float, high: float, nbins: int) -> tuple[PlotTick, ...]:
    locator = mticker.MaxNLocator(nbins=nbins)
    formatter = mticker.FormatStrFormatter("%g")
    values = [float(value) for value in locator.tick_values(low, high) if low - 1e-9 <= value <= high + 1e-9]
    ticks: list[PlotTick] = []
    for value in values:
        if axis == "x":
            point = Point(_map_linear(value, low, high, frame.x, frame.right), frame.bottom)
        else:
            point = Point(frame.x, _map_linear(value, high, low, frame.y, frame.bottom))
        label = formatter(value)
        ticks.append(PlotTick(axis=axis, value=value, point=point, label=label, major=True))
    return tuple(ticks)


def _log_tick_point(frame: Rect, axis: AxisName, log_value: float, log_min: float, log_max: float) -> Point:
    if axis == "x":
        return Point(_map_linear(log_value, log_min, log_max, frame.x, frame.right), frame.bottom)
    return Point(frame.x, _map_linear(log_value, log_max, log_min, frame.y, frame.bottom))


def _format_power_tick(exponent: int, formatter: mticker.Formatter) -> str:
    # The formatter object keeps tick-label generation in the Matplotlib grammar
    # layer while preserving editable deterministic ASCII text in the SVG.
    return formatter(10.0**exponent)


def _map_pe_point(frame: Rect, field: float, polarization: float, field_scale: float, polarization_scale: float) -> Point:
    return Point(
        frame.center.x + field * frame.width * field_scale / 2.0,
        frame.center.y - polarization * frame.height * polarization_scale / 2.0,
    )


def _map_dos_point(frame: Rect, y_value: float, profile: float, x_scale: float) -> Point:
    return Point(frame.x + profile * frame.width * x_scale, _map_linear(y_value, 0.0, 1.0, frame.y, frame.bottom))


def _asymmetric_gaussian(values: np.ndarray, center: float, height_scale: float, width_scale: float) -> np.ndarray:
    sigma_left = 0.18 * max(0.42, width_scale)
    sigma_right = 0.28 * max(0.42, width_scale)
    sigma = np.where(values < center, sigma_left, sigma_right)
    return height_scale * np.exp(-0.5 * ((values - center) / sigma) ** 2)


def _label_inside(
    value: str,
    desired: Point,
    frame: Rect,
    *,
    size: float,
    anchor: Literal["start", "middle", "end"] = "start",
) -> PlotLabel:
    width = max(size * 0.6, len(value) * size * 0.55)
    min_x = frame.x + 4
    max_x = frame.right - 4
    x = desired.x
    if anchor == "start":
        x = min(max(desired.x, min_x), max_x - width)
    elif anchor == "middle":
        x = min(max(desired.x, min_x + width / 2), max_x - width / 2)
    else:
        x = min(max(desired.x, min_x + width), max_x)
    y = min(max(desired.y, frame.y + size * 1.05), frame.bottom - size * 0.4)
    return PlotLabel(value, Point(x, y), size, anchor)


def _map_linear(value: float, source_min: float, source_max: float, target_min: float, target_max: float) -> float:
    if source_max == source_min:
        return (target_min + target_max) / 2.0
    fraction = (value - source_min) / (source_max - source_min)
    return target_min + fraction * (target_max - target_min)
