from __future__ import annotations

import html
import math
from pathlib import Path
from typing import Callable, Iterable

import drawsvg as draw

from engine.scene import Point, Rect, SemanticObject
from engine.scientific_geometry import gaussian_lobe_points
from engine.style import DEFAULT_STYLE, FigureStyle


def save_svg(drawing: draw.Drawing, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(drawing.as_svg())


def style_defs() -> draw.Raw:
    return draw.Raw(
        """
<defs>
  <linearGradient id="sulfurSwatch" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#f8d86b"/>
    <stop offset="38%" stop-color="#e8b640"/>
    <stop offset="70%" stop-color="#c88a27"/>
    <stop offset="100%" stop-color="#825218"/>
  </linearGradient>
  <linearGradient id="badgeSheen" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#ffffff"/>
    <stop offset="100%" stop-color="#f5f8fc"/>
  </linearGradient>
  <linearGradient id="bandFill" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="#ffffff"/>
    <stop offset="100%" stop-color="#e9edf2"/>
  </linearGradient>
  <linearGradient id="deepDosFill" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#fbe1df" stop-opacity="0.92"/>
    <stop offset="64%" stop-color="#dc6868" stop-opacity="0.66"/>
    <stop offset="100%" stop-color="#a81016" stop-opacity="0.28"/>
  </linearGradient>
  <linearGradient id="shallowDosFill" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#e8f2ff" stop-opacity="0.92"/>
    <stop offset="100%" stop-color="#1f6fd0" stop-opacity="0.28"/>
  </linearGradient>
  <linearGradient id="polymerBeam" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#f4d46c"/>
    <stop offset="55%" stop-color="#c28a25"/>
    <stop offset="100%" stop-color="#8a5b18"/>
  </linearGradient>
  <linearGradient id="metalSheen" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#677282"/>
    <stop offset="42%" stop-color="#edf1f5"/>
    <stop offset="100%" stop-color="#7b8594"/>
  </linearGradient>
  <filter id="subtleShadow" x="-10%" y="-10%" width="120%" height="120%">
    <feDropShadow dx="0" dy="4" stdDeviation="4" flood-color="#182032" flood-opacity="0.10"/>
  </filter>
  <filter id="softInsetShadow" x="-15%" y="-15%" width="130%" height="130%">
    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#182032" flood-opacity="0.12"/>
  </filter>
  <filter id="deepGlow" x="-55%" y="-55%" width="210%" height="210%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur"/>
    <feColorMatrix in="blur" type="matrix" values="0.65 0 0 0 0.35  0 0.05 0 0 0  0 0 0.05 0 0  0 0 0 0.45 0" result="glow"/>
    <feMerge>
      <feMergeNode in="glow"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
  <pattern id="polymerGrain" patternUnits="userSpaceOnUse" width="18" height="18">
    <path d="M2 12 C6 8, 11 16, 17 7" fill="none" stroke="#fff0b8" stroke-width="0.9" opacity="0.42"/>
    <circle cx="5" cy="5" r="0.75" fill="#6b4211" opacity="0.28"/>
    <circle cx="13" cy="14" r="0.7" fill="#fff4cb" opacity="0.55"/>
  </pattern>
</defs>
"""
    )


def begin_semantic_group(drawing: draw.Drawing, obj: SemanticObject[object], payload_geometry: str) -> None:
    group_id = f"semantic-{obj.id}"
    drawing.append(
        draw.Raw(
            '<g id="{group_id}" data-semantic-id="{semantic_id}" '
            'data-semantic-kind="{kind}" data-payload-geometry="{geometry}">'.format(
                group_id=html.escape(group_id, quote=True),
                semantic_id=html.escape(obj.id, quote=True),
                kind=html.escape(obj.kind, quote=True),
                geometry=html.escape(payload_geometry, quote=True),
            )
        )
    )
    drawing.append(draw.Raw(f"<title>{html.escape(obj.kind)}:{html.escape(obj.id)}</title>"))


def end_semantic_group(drawing: draw.Drawing) -> None:
    drawing.append(draw.Raw("</g>"))


def text(
    drawing: draw.Drawing,
    value: str,
    x: float,
    y: float,
    size: float,
    *,
    fill: str | None = None,
    weight: str | None = None,
    italic: bool = False,
    anchor: str = "start",
    style: FigureStyle = DEFAULT_STYLE,
) -> None:
    attrs: dict[str, object] = {
        "fill": fill or style.palette.ink,
        "font_family": style.typography.family,
        "text_anchor": anchor,
    }
    if weight:
        attrs["font_weight"] = weight
    if italic:
        attrs["font_style"] = "italic"
    drawing.append(draw.Text(value, size, x, y, **attrs))


def multiline_text(
    drawing: draw.Drawing,
    lines: Iterable[str],
    x: float,
    y: float,
    size: float,
    line_height: float,
    *,
    fill: str | None = None,
    weight: str | None = None,
    italic: bool = False,
    anchor: str = "start",
    style: FigureStyle = DEFAULT_STYLE,
) -> None:
    for index, line in enumerate(lines):
        text(
            drawing,
            line,
            x,
            y + index * line_height,
            size,
            fill=fill,
            weight=weight,
            italic=italic,
            anchor=anchor,
            style=style,
        )


def rounded_rect(
    drawing: draw.Drawing,
    rect: Rect,
    *,
    fill: str,
    stroke: str,
    radius: float = 8,
    stroke_width: float = 1.0,
    opacity: float = 1.0,
    filter_: str | None = None,
) -> None:
    attrs: dict[str, object] = {}
    if filter_:
        attrs["filter"] = filter_
    drawing.append(
        draw.Rectangle(
            rect.x,
            rect.y,
            rect.width,
            rect.height,
            rx=radius,
            ry=radius,
            fill=fill,
            stroke=stroke,
            stroke_width=stroke_width,
            opacity=opacity,
            **attrs,
        )
    )


def arrow(
    drawing: draw.Drawing,
    start: Point,
    end: Point,
    color: str,
    *,
    width: float = 2.0,
    head_length: float = 15.0,
    head_width: float = 11.0,
    opacity: float = 1.0,
    dash: str | None = None,
    attrs: dict[str, object] | None = None,
) -> None:
    angle = math.atan2(end.y - start.y, end.x - start.x)
    back = Point(end.x - head_length * math.cos(angle), end.y - head_length * math.sin(angle))
    nx = math.sin(angle)
    ny = -math.cos(angle)
    line_attrs: dict[str, object] = dict(attrs or {})
    if dash:
        line_attrs["stroke_dasharray"] = dash
    if width > 0:
        drawing.append(
            draw.Line(
                start.x,
                start.y,
                back.x,
                back.y,
                stroke=color,
                stroke_width=width,
                stroke_linecap="round",
                opacity=opacity,
                **line_attrs,
            )
        )
    drawing.append(
        draw.Lines(
            end.x,
            end.y,
            back.x + nx * head_width * 0.5,
            back.y + ny * head_width * 0.5,
            back.x - nx * head_width * 0.5,
            back.y - ny * head_width * 0.5,
            close=True,
            fill=color,
            opacity=opacity,
            **(attrs or {}),
        )
    )


def mini_axis(drawing: draw.Drawing, origin: Point, width: float, height: float, color: str) -> None:
    arrow(drawing, Point(origin.x, origin.y + height), Point(origin.x, origin.y), color, width=1.2, head_length=9, head_width=7)
    arrow(drawing, Point(origin.x, origin.y + height), Point(origin.x + width, origin.y + height), color, width=1.2, head_length=9, head_width=7)


def draw_level_stack(
    drawing: draw.Drawing,
    area: Rect,
    positions: tuple[float, ...],
    *,
    center_x: float,
    base_width: float,
    width_step: float,
    color: str,
    stroke_width: float,
    style: FigureStyle = DEFAULT_STYLE,
    glow: bool = False,
    opacity: float = 0.92,
) -> tuple[Point, ...]:
    points: list[Point] = []
    for index, position in enumerate(positions):
        y = area.y + position * area.height
        level_width = base_width + index * width_step
        start_x = center_x - level_width / 2
        end_x = center_x + level_width / 2
        drawing.append(draw.Line(start_x, y, end_x, y, stroke=color, stroke_width=stroke_width, opacity=opacity))
        drawing.append(draw.Line(start_x, y + stroke_width * 0.72, end_x, y + stroke_width * 0.72, stroke="#ffffff", stroke_width=0.65, opacity=0.36))
        if glow and index in (1, max(1, len(positions) // 2), len(positions) - 2):
            drawing.append(draw.Circle(center_x, y, stroke_width * 3.2, fill=color, opacity=0.12, filter="url(#deepGlow)"))
        points.append(Point(center_x, y))
    return tuple(points)


def polyline_path(
    points: Iterable[Point],
    *,
    close: bool = False,
    fill: str = "none",
    stroke: str = "#000000",
    stroke_width: float = 1.0,
    opacity: float = 1.0,
    attrs: dict[str, object] | None = None,
) -> draw.Path:
    points = tuple(points)
    path = draw.Path(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity, **(attrs or {}))
    if not points:
        return path
    path.M(points[0].x, points[0].y)
    for point in points[1:]:
        path.L(point.x, point.y)
    if close:
        path.Z()
    return path


def dos_lobe(
    drawing: draw.Drawing,
    anchor: Point,
    width: float,
    height: float,
    fill: str,
    stroke: str,
    opacity: float,
    *,
    sigma: tuple[float, float] = (0.34, 0.46),
    samples: int = 48,
    attrs: dict[str, object] | None = None,
) -> None:
    profile = gaussian_lobe_points(
        anchor,
        width=width,
        height=height,
        samples=samples,
        upper_sigma=sigma[0],
        lower_sigma=sigma[1],
    )
    points = (Point(anchor.x, anchor.y - height / 2), *profile, Point(anchor.x, anchor.y + height / 2))
    path = polyline_path(points, close=True, fill=fill, stroke=stroke, stroke_width=2.0, opacity=opacity, attrs=attrs)
    drawing.append(path)


def bezier_dos_lobe(drawing: draw.Drawing, anchor: Point, width: float, height: float, fill: str, stroke: str, opacity: float) -> None:
    path = draw.Path(fill=fill, stroke=stroke, stroke_width=2.0, opacity=opacity)
    path.M(anchor.x, anchor.y - height / 2)
    path.C(anchor.x + width * 0.60, anchor.y - height * 0.48, anchor.x + width * 1.02, anchor.y - height * 0.10, anchor.x + width, anchor.y)
    path.C(anchor.x + width * 0.96, anchor.y + height * 0.30, anchor.x + width * 0.36, anchor.y + height * 0.46, anchor.x, anchor.y + height / 2)
    path.Z()
    drawing.append(path)


def draw_dos_pair(
    drawing: draw.Drawing,
    area: Rect,
    *,
    shallow_center_y: float,
    shallow_width: float,
    shallow_height: float,
    deep_center_y: float,
    deep_width: float,
    deep_height: float,
    shallow_label: str,
    deep_label: str,
    shallow_sigma: tuple[float, float] = (0.26, 0.32),
    deep_sigma: tuple[float, float] = (0.42, 0.52),
    samples: int = 72,
    style: FigureStyle = DEFAULT_STYLE,
) -> None:
    palette = style.palette
    hero_attr = "data-hero-role"
    axis_x = area.x + 32
    origin = Point(axis_x, area.y + 16)
    mini_axis(drawing, origin, area.width - 52, area.height - 38, palette.ink)
    drawing.append(draw.Line(origin.x, origin.y, origin.x, origin.y + area.height - 38, stroke="none", **{hero_attr: "dos-axis"}))
    drawing.append(draw.Line(origin.x, origin.y + area.height - 38, origin.x + area.width - 52, origin.y + area.height - 38, stroke="none", **{hero_attr: "dos-axis"}))
    drawing.append(draw.Text("DOS  g(Et)", 15, axis_x + 92, area.y + 28, fill=palette.ink, font_family=style.typography.family, text_anchor="start", font_weight="700", **{hero_attr: "dos-label"}))
    mid_y = area.y + 16 + 0.48 * (area.height - 38)
    drawing.append(draw.Line(axis_x, mid_y, axis_x + area.width - 58, mid_y, stroke=palette.ink, stroke_width=1.0, stroke_dasharray="5 5", opacity=0.52))
    dos_lobe(
        drawing,
        Point(axis_x, area.y + shallow_center_y * area.height),
        shallow_width,
        shallow_height,
        "url(#shallowDosFill)",
        palette.shallow_blue,
        0.9,
        sigma=shallow_sigma,
        samples=samples,
        attrs={hero_attr: "dos-lobe-shallow"},
    )
    dos_lobe(
        drawing,
        Point(axis_x, area.y + deep_center_y * area.height),
        deep_width,
        deep_height,
        "url(#deepDosFill)",
        palette.deep_red,
        0.94,
        sigma=deep_sigma,
        samples=samples,
        attrs={hero_attr: "dos-lobe-deep"},
    )
    text(drawing, shallow_label, axis_x + shallow_width + 18, area.y + shallow_center_y * area.height + 5, 13, fill=palette.shallow_blue, style=style)
    deep_label_x = min(axis_x + deep_width - 8, area.right - 8)
    text(drawing, deep_label, deep_label_x, area.y + deep_center_y * area.height + 34, 16, fill=palette.deep_red, weight="700", anchor="end", style=style)


def draw_reference_dos_schematic(
    drawing: draw.Drawing,
    area: Rect,
    *,
    shallow_center_y: float,
    deep_center_y: float,
    shallow_width: float,
    deep_width: float,
    shallow_height: float,
    deep_height: float,
    shallow_label: str,
    deep_label: str,
    depth_label: str,
    attrs_for_role: Callable[[str], dict[str, object]],
    axis_role: str,
    shallow_lobe_role: str,
    deep_lobe_role: str,
    threshold_role: str,
    depth_guide_role: str,
    depth_label_role: str,
    label_role: str,
    axis_label_role: str,
    shallow_sigma: tuple[float, float] = (0.26, 0.32),
    deep_sigma: tuple[float, float] = (0.42, 0.52),
    samples: int = 72,
    title: str = "DOS  g(Et)",
    axis_label: str = "g(Et)",
    show_lobe_labels: bool = True,
    show_energy_label: bool = False,
    depth_label_side: str = "left",
    compact: bool = False,
    style: FigureStyle = DEFAULT_STYLE,
) -> None:
    palette = style.palette
    axis_x = area.x + (7 if compact else 8)
    axis_top = area.y + (18 if compact else 28)
    axis_bottom = area.bottom - (20 if compact else 24)
    axis_right = area.right - (14 if compact else 24)
    axis_height = axis_bottom - axis_top
    axis_width = axis_right - axis_x
    axis_color = palette.ink

    arrow(drawing, Point(axis_x, axis_bottom), Point(axis_x, axis_top), axis_color, width=1.0 if compact else 1.2, head_length=8, head_width=7)
    arrow(drawing, Point(axis_x, axis_bottom), Point(axis_right, axis_bottom), axis_color, width=1.0 if compact else 1.2, head_length=8, head_width=7)
    drawing.append(draw.Line(axis_x, axis_bottom, axis_x, axis_top, stroke="none", **attrs_for_role(axis_role)))
    drawing.append(draw.Line(axis_x, axis_bottom, axis_right, axis_bottom, stroke="none", **attrs_for_role(axis_role)))

    title_size = 9.6 if compact else 15.0
    if title:
        text(drawing, title, axis_x + (12 if compact else 18), area.y + (11 if compact else 28), title_size, fill=axis_color, weight="700", style=style, anchor="start")
        drawing.append(draw.Text(title, title_size, axis_x + (12 if compact else 18), area.y + (11 if compact else 28), fill="none", font_family=style.typography.family, text_anchor="start", **attrs_for_role(label_role)))
    label_size = 8.2 if compact else 14.0
    text(drawing, axis_label, axis_x + axis_width * 0.60, axis_bottom + (13 if compact else 20), label_size, fill=axis_color, italic=True, anchor="middle", style=style)
    drawing.append(draw.Text(axis_label, label_size, axis_x + axis_width * 0.60, axis_bottom + (13 if compact else 20), fill="none", font_family=style.typography.family, text_anchor="middle", **attrs_for_role(axis_label_role)))
    if show_energy_label:
        drawing.append(
            draw.Text(
                "Energy",
                8.2 if compact else 12,
                0,
                0,
                fill=axis_color,
                font_family=style.typography.family,
                text_anchor="middle",
                transform=f"translate({axis_x - (15 if compact else 23)} {axis_top + axis_height * 0.52}) rotate(-90)",
            )
        )

    shallow_center = area.y + shallow_center_y * area.height
    shallow_half_height = min(shallow_height, axis_height * 0.30) / 2.0
    shallow_top = max(axis_top + 5, shallow_center - shallow_half_height)
    shallow_bottom = min(axis_bottom - axis_height * 0.56, shallow_center + shallow_half_height)
    threshold_y = min(max(shallow_bottom + (7 if compact else 9), axis_top + axis_height * 0.24), axis_bottom - axis_height * 0.44)

    deep_center = area.y + deep_center_y * area.height
    deep_top = threshold_y
    deep_bottom = min(axis_bottom - 4, deep_center + min(deep_height, axis_height * 0.72) / 2.0)
    if deep_bottom - deep_top < axis_height * 0.42:
        deep_bottom = min(axis_bottom - 4, deep_top + axis_height * 0.55)
    deep_peak_y = min(max(deep_center, deep_top + (deep_bottom - deep_top) * 0.45), deep_bottom - 12)

    guide_x = area.right - (26 if compact else 14)
    max_lobe_extent = max(18.0, guide_x - axis_x - (20 if compact else 30))
    shallow_extent = min(max_lobe_extent * 0.48, max(axis_width * 0.16, shallow_width * (0.34 if compact else 0.55)))
    deep_extent = min(max_lobe_extent, max(axis_width * 0.34, deep_width * (0.52 if compact else 0.54)))

    drawing.append(
        draw.Line(
            axis_x + 8,
            threshold_y,
            guide_x,
            threshold_y,
            stroke=axis_color,
            stroke_width=0.85 if compact else 1.0,
            stroke_dasharray="5 5",
            opacity=0.68,
            **attrs_for_role(threshold_role),
        )
    )
    shallow_path = _sampled_asymmetric_dos_lobe_path(
        axis_x,
        shallow_top,
        shallow_bottom,
        shallow_center,
        shallow_extent,
        shallow_sigma,
        samples,
        fill=style.palette.shallow_blue_light,
        stroke=style.palette.shallow_blue,
        attrs=attrs_for_role(shallow_lobe_role),
        opacity=0.88,
        stroke_width=1.35 if compact else 1.75,
        polish_strength=0.62 if compact else 0.72,
    )
    deep_path = _sampled_asymmetric_dos_lobe_path(
        axis_x,
        deep_top,
        deep_bottom,
        deep_peak_y,
        deep_extent,
        deep_sigma,
        samples,
        fill="#d98787" if compact else "url(#deepDosFill)",
        stroke=style.palette.deep_red,
        attrs=attrs_for_role(deep_lobe_role),
        opacity=0.78 if compact else 0.88,
        stroke_width=1.45 if compact else 1.9,
        polish_strength=0.82 if compact else 0.90,
    )
    drawing.append(shallow_path)
    drawing.append(deep_path)

    if show_lobe_labels:
        label_shallow_size = 8.0 if compact else 13.0
        shallow_label_x = axis_x + shallow_extent + (7 if compact else 14)
        shallow_label_y = shallow_top + (shallow_bottom - shallow_top) * 0.62
        text(drawing, shallow_label, shallow_label_x, shallow_label_y, label_shallow_size, fill=style.palette.shallow_blue, italic=True, style=style)
        drawing.append(draw.Text(shallow_label, label_shallow_size, shallow_label_x, shallow_label_y, fill="none", font_family=style.typography.family, **attrs_for_role(label_role)))
        label_deep_size = 8.4 if compact else 13.5
        deep_label_x = axis_x + deep_extent + (8 if compact else 20)
        deep_label_y = deep_peak_y + (8 if compact else 14)
        text(drawing, deep_label, deep_label_x, deep_label_y, label_deep_size, fill=style.palette.deep_red, italic=True, weight="700" if not compact else None, style=style)
        drawing.append(draw.Text(deep_label, label_deep_size, deep_label_x, deep_label_y, fill="none", font_family=style.typography.family, **attrs_for_role(label_role)))

    guide_top = threshold_y + (4 if compact else 2)
    guide_bottom = min(axis_bottom - 24, threshold_y + (deep_bottom - threshold_y) * 0.60)
    _reference_double_arrow(drawing, Point(guide_x, guide_top), Point(guide_x, guide_bottom), axis_color, attrs_for_role(depth_guide_role), compact=compact)
    depth_size = 7.5 if compact else 11.0
    depth_lines = tuple(line for line in depth_label.split("\n") if line)
    if depth_label_side == "right":
        depth_anchor_x = guide_x + (4 if compact else 6)
        depth_anchor = "start"
    else:
        depth_anchor_x = guide_x - (5 if compact else 7)
        depth_anchor = "end"
    depth_y = guide_top + (guide_bottom - guide_top) * 0.48 - (len(depth_lines) - 1) * depth_size * 0.55
    for index, line in enumerate(depth_lines):
        y = depth_y + index * depth_size * 1.05
        text(drawing, line, depth_anchor_x, y, depth_size, fill=axis_color, italic=True, anchor=depth_anchor, style=style)
        drawing.append(draw.Text(line, depth_size, depth_anchor_x, y, fill="none", font_family=style.typography.family, text_anchor=depth_anchor, **attrs_for_role(depth_label_role)))


def _sampled_asymmetric_dos_lobe_path(
    axis_x: float,
    top: float,
    bottom: float,
    center_y: float,
    extent: float,
    sigma: tuple[float, float],
    samples: int,
    *,
    fill: str,
    stroke: str,
    attrs: dict[str, object],
    opacity: float,
    stroke_width: float,
    polish_strength: float = 0.0,
) -> draw.Path:
    height = bottom - top
    profile_attrs = {
        **attrs,
        "data-dos-profile": "payload-sampled-asymmetric",
        "data-dos-polish": "schematic-v11",
        "data-dos-samples": str(max(24, samples)),
    }
    path = draw.Path(fill=fill, stroke=stroke, stroke_width=stroke_width, opacity=opacity, **profile_attrs)
    path.M(axis_x, top)
    center_y = min(max(center_y, top + height * 0.16), bottom - height * 0.16)
    sample_count = max(24, samples)
    for index in range(sample_count):
        fraction = index / (sample_count - 1)
        y = top + fraction * height
        offset = (y - center_y) / max(height, 1.0)
        sigma_value = sigma[0] if y < center_y else sigma[1]
        profile = math.exp(-0.5 * (offset / max(sigma_value, 0.08)) ** 2)
        if polish_strength:
            upper_shoulder = max(0.0, -offset)
            lower_tail = max(0.0, offset)
            profile_power = 1.0 - 0.20 * polish_strength + 0.10 * polish_strength * lower_tail
            profile = profile ** max(profile_power, 0.68)
            profile *= 1.0 + 0.10 * polish_strength * upper_shoulder
            profile *= 1.0 - 0.08 * polish_strength * lower_tail
        taper = math.sin(math.pi * fraction) ** (0.30 + 0.16 * polish_strength)
        x = axis_x + extent * profile * taper
        path.L(x, y)
    path.L(axis_x, bottom)
    path.Z()
    return path

def _reference_double_arrow(
    drawing: draw.Drawing,
    start: Point,
    end: Point,
    color: str,
    attrs: dict[str, object],
    *,
    compact: bool,
) -> None:
    drawing.append(draw.Line(start.x, start.y, end.x, end.y, stroke=color, stroke_width=0.9 if compact else 1.0, opacity=0.86, **attrs))
    head_length = 6.5 if compact else 8.0
    head_width = 5.8 if compact else 7.0
    for tip, base in ((start, end), (end, start)):
        angle = math.atan2(base.y - tip.y, base.x - tip.x)
        back = Point(tip.x + head_length * math.cos(angle), tip.y + head_length * math.sin(angle))
        nx = math.sin(angle)
        ny = -math.cos(angle)
        drawing.append(
            draw.Lines(
                tip.x,
                tip.y,
                back.x + nx * head_width * 0.5,
                back.y + ny * head_width * 0.5,
                back.x - nx * head_width * 0.5,
                back.y - ny * head_width * 0.5,
                close=True,
                fill=color,
                opacity=0.86,
                **attrs,
            )
        )


def sulfur_atom(drawing: draw.Drawing, center: Point, radius: float, style: FigureStyle = DEFAULT_STYLE) -> None:
    palette = style.palette
    drawing.append(draw.Circle(center.x, center.y, radius, fill=palette.sulfur_yellow, stroke=palette.sulfur_brown, stroke_width=1.0))
    drawing.append(draw.Circle(center.x - radius * 0.28, center.y - radius * 0.28, radius * 0.24, fill="#fff3b7", opacity=0.7))
    text(drawing, "S", center.x, center.y + radius * 0.36, radius * 0.95, fill=palette.sulfur_brown, weight="700", anchor="middle", style=style)


def charge_marker(
    drawing: draw.Drawing,
    center: Point,
    sign: str,
    radius: float,
    color: str,
    style: FigureStyle = DEFAULT_STYLE,
) -> None:
    drawing.append(draw.Circle(center.x, center.y, radius, fill=color, stroke="#6c0d0d", stroke_width=1.0))
    text(drawing, sign, center.x, center.y + radius * 0.38, radius * 1.35, fill=style.palette.white, weight="700", anchor="middle", style=style)


def checkmark(drawing: draw.Drawing, x: float, y: float, color: str, *, size: float = 9.0) -> None:
    path = draw.Path(fill="none", stroke=color, stroke_width=2.0, stroke_linecap="round", stroke_linejoin="round")
    path.M(x, y)
    path.L(x + size * 0.38, y + size * 0.42)
    path.L(x + size, y - size * 0.52)
    drawing.append(path)
