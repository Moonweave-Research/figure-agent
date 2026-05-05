from __future__ import annotations

import html
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

import drawsvg as draw


BLUE = "#12366e"
BLUE_MID = "#0b4ca8"
BLUE_LIGHT = "#dbeafe"
RED = "#a41010"
RED_MID = "#c31717"
RED_LIGHT = "#f8dedd"
GREEN = "#0f7b62"
TEAL = "#158f9c"
AMBER = "#c79623"
AMBER_DARK = "#8d6414"
GRAY = "#5f6670"
GRAY_LIGHT = "#eef1f4"
INK = "#111111"
WHITE = "#ffffff"


def save_svg(drawing: draw.Drawing, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    drawing.save_svg(target)


def style_defs() -> draw.Raw:
    return draw.Raw(
        """
<defs>
  <linearGradient id="polymerGloss" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#fff2bd"/>
    <stop offset="28%" stop-color="#d7aa3a"/>
    <stop offset="68%" stop-color="#b9841b"/>
    <stop offset="100%" stop-color="#6f4d12"/>
  </linearGradient>
  <linearGradient id="metalSheen" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#8793a3"/>
    <stop offset="22%" stop-color="#f7f9fb"/>
    <stop offset="48%" stop-color="#a9b2bf"/>
    <stop offset="78%" stop-color="#e4e8ed"/>
    <stop offset="100%" stop-color="#667282"/>
  </linearGradient>
  <linearGradient id="energyRamp" x1="0%" y1="100%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#eaf3ff"/>
    <stop offset="35%" stop-color="#78a7df"/>
    <stop offset="68%" stop-color="#f3d075"/>
    <stop offset="100%" stop-color="#c31717"/>
  </linearGradient>
  <linearGradient id="maskFadeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="white" stop-opacity="0.08"/>
    <stop offset="38%" stop-color="white" stop-opacity="0.85"/>
    <stop offset="100%" stop-color="white" stop-opacity="0.18"/>
  </linearGradient>
  <radialGradient id="trapGlow" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#c31717" stop-opacity="0.85"/>
    <stop offset="45%" stop-color="#f2aaa3" stop-opacity="0.35"/>
    <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="blueHalo" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#0b4ca8" stop-opacity="0.46"/>
    <stop offset="100%" stop-color="#0b4ca8" stop-opacity="0"/>
  </radialGradient>
  <filter id="softShadow" x="-25%" y="-25%" width="150%" height="150%">
    <feDropShadow dx="0" dy="8" stdDeviation="8" flood-color="#07162d" flood-opacity="0.16"/>
  </filter>
  <filter id="tightShadow" x="-18%" y="-18%" width="136%" height="136%">
    <feDropShadow dx="2" dy="4" stdDeviation="3" flood-color="#07162d" flood-opacity="0.22"/>
  </filter>
  <pattern id="polymerGrain" patternUnits="userSpaceOnUse" width="18" height="18">
    <path d="M1 13 C5 10, 9 16, 17 8" fill="none" stroke="#8d6414" stroke-width="0.8" opacity="0.45"/>
    <circle cx="5" cy="5" r="0.9" fill="#fff2bd" opacity="0.55"/>
    <circle cx="13" cy="14" r="0.7" fill="#6f4d12" opacity="0.28"/>
  </pattern>
  <pattern id="brushedMetal" patternUnits="userSpaceOnUse" width="14" height="14">
    <path d="M0 3 H14 M0 8 H14 M0 13 H14" stroke="#ffffff" stroke-width="0.8" opacity="0.45"/>
    <path d="M0 5 H14 M0 11 H14" stroke="#4d5968" stroke-width="0.5" opacity="0.38"/>
  </pattern>
  <pattern id="trapDots" patternUnits="userSpaceOnUse" width="22" height="22">
    <circle cx="5" cy="6" r="2" fill="#c31717" opacity="0.42"/>
    <circle cx="16" cy="13" r="1.4" fill="#0b4ca8" opacity="0.35"/>
    <circle cx="10" cy="18" r="0.9" fill="#111111" opacity="0.18"/>
  </pattern>
  <clipPath id="plotClip">
    <rect x="72" y="626" width="355" height="220" rx="4" ry="4"/>
  </clipPath>
  <clipPath id="surfaceClip">
    <path d="M1262 224 L1510 122 L1714 260 L1466 362 Z"/>
  </clipPath>
  <mask id="surfaceFadeMask">
    <rect x="1210" y="30" width="540" height="430" fill="url(#maskFadeGradient)"/>
  </mask>
</defs>
"""
    )


def card(drawing: draw.Drawing, x: float, y: float, width: float, height: float, label: str, title: str) -> None:
    drawing.append(
        draw.Rectangle(
            x,
            y,
            width,
            height,
            rx=8,
            ry=8,
            fill=WHITE,
            stroke="#e0e5eb",
            stroke_width=1.2,
            filter="url(#softShadow)",
        )
    )
    text(drawing, label, x + 20, y + 36, 24, fill=INK, weight="700")
    text(drawing, title, x + 55, y + 35, 20, fill=BLUE, weight="700")


def text(
    drawing: draw.Drawing,
    value: str,
    x: float,
    y: float,
    size: float,
    fill: str = INK,
    weight: str | None = None,
    italic: bool = False,
    anchor: str = "start",
    family: str = "Helvetica, Arial, sans-serif",
) -> None:
    attrs: dict[str, object] = {
        "fill": fill,
        "font_family": family,
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
    fill: str = INK,
    weight: str | None = None,
    italic: bool = False,
    anchor: str = "start",
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
        )


def arrow(
    drawing: draw.Drawing,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str,
    width: float = 2.0,
    head_length: float = 16.0,
    head_width: float = 12.0,
    opacity: float = 1.0,
) -> None:
    angle = math.atan2(y2 - y1, x2 - x1)
    back_x = x2 - head_length * math.cos(angle)
    back_y = y2 - head_length * math.sin(angle)
    nx = math.sin(angle)
    ny = -math.cos(angle)
    drawing.append(
        draw.Line(
            x1,
            y1,
            back_x,
            back_y,
            stroke=color,
            stroke_width=width,
            stroke_linecap="round",
            opacity=opacity,
        )
    )
    drawing.append(
        draw.Lines(
            x2,
            y2,
            back_x + nx * head_width * 0.5,
            back_y + ny * head_width * 0.5,
            back_x - nx * head_width * 0.5,
            back_y - ny * head_width * 0.5,
            close=True,
            fill=color,
            opacity=opacity,
        )
    )


def rounded_rect(
    drawing: draw.Drawing,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str,
    radius: float = 6.0,
    stroke_width: float = 1.0,
    opacity: float = 1.0,
) -> None:
    drawing.append(
        draw.Rectangle(
            x,
            y,
            width,
            height,
            rx=radius,
            ry=radius,
            fill=fill,
            stroke=stroke,
            stroke_width=stroke_width,
            opacity=opacity,
        )
    )


def iso_box(
    drawing: draw.Drawing,
    x: float,
    y: float,
    width: float,
    depth: float,
    height: float,
    *,
    top_fill: str,
    left_fill: str,
    right_fill: str,
    stroke: str = "#506070",
    opacity: float = 1.0,
) -> None:
    dx = depth
    dy = depth * 0.48
    top = [(x, y), (x + width, y - dy), (x + width + dx, y), (x + dx, y + dy)]
    left = [(x, y), (x + dx, y + dy), (x + dx, y + dy + height), (x, y + height)]
    right = [
        (x + dx, y + dy),
        (x + width + dx, y),
        (x + width + dx, y + height),
        (x + dx, y + dy + height),
    ]
    for points, fill in [(left, left_fill), (right, right_fill), (top, top_fill)]:
        drawing.append(
            draw.Lines(
                *[coord for point in points for coord in point],
                close=True,
                fill=fill,
                stroke=stroke,
                stroke_width=1.0,
                opacity=opacity,
            )
        )


def deterministic_dots(
    drawing: draw.Drawing,
    points: Iterable[tuple[float, float, float, str, float]],
) -> None:
    for x, y, r, color, opacity in points:
        drawing.append(draw.Circle(x, y, r, fill=color, opacity=opacity))


def hatching(
    drawing: draw.Drawing,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    step: float = 8.0,
    color: str = "#7b8490",
    stroke_width: float = 1.0,
) -> None:
    pos = -height
    while pos < width:
        x1 = x + max(pos, 0)
        y1 = y + max(-pos, 0)
        x2 = x + min(pos + height, width)
        y2 = y + height - max(pos + height - width, 0)
        drawing.append(draw.Line(x1, y1, x2, y2, stroke=color, stroke_width=stroke_width))
        pos += step


def nested_svg(
    svg_text: str,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    prefix: str,
) -> draw.Raw:
    cleaned = _without_xml_declaration(svg_text)
    root = ET.fromstring(cleaned)
    view_box = root.attrib.get("viewBox")
    if not view_box:
        raise ValueError("nested SVG requires a viewBox")
    body = re.sub(r"^<svg[^>]*>", "", cleaned.strip(), count=1)
    body = re.sub(r"</svg>\s*$", "", body)
    body = re.sub(r"\s*<metadata>.*?</metadata>\s*", "", body, flags=re.DOTALL)
    body = _prefix_svg_ids(body, prefix)
    return draw.Raw(
        f'<svg x="{x:.3f}" y="{y:.3f}" width="{width:.3f}" height="{height:.3f}" '
        f'viewBox="{escape_attr(view_box)}" overflow="visible">{body}</svg>'
    )


def _without_xml_declaration(svg_text: str) -> str:
    text_without_decl = re.sub(r"^\s*<\?xml[^>]*>\s*", "", svg_text)
    text_without_comment = re.sub(r"^\s*<!--.*?-->\s*", "", text_without_decl, flags=re.DOTALL)
    return re.sub(r"^\s*<!DOCTYPE\s+svg[^>]*(?:\[[\s\S]*?\]\s*)?>\s*", "", text_without_comment)


def escape_attr(value: str) -> str:
    return html.escape(value, quote=True)


def _prefix_svg_ids(svg_body: str, prefix: str) -> str:
    ids = re.findall(r"id=\"([^\"]+)\"|id='([^']+)'", svg_body)
    updated = svg_body
    seen: list[str] = []
    for double_quoted, single_quoted in ids:
        old_id = double_quoted or single_quoted
        if old_id in seen:
            continue
        seen.append(old_id)
        new_id = f"{prefix}_{old_id}"
        updated = updated.replace(f'id="{old_id}"', f'id="{new_id}"')
        updated = updated.replace(f"id='{old_id}'", f"id='{new_id}'")
        updated = updated.replace(f'url(#{old_id})', f'url(#{new_id})')
        updated = updated.replace(f"#{old_id}\"", f"#{new_id}\"")
        updated = updated.replace(f"#{old_id}'", f"#{new_id}'")
    return updated
