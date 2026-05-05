from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import drawsvg as draw


BLUE = "#12366e"
BLUE_MID = "#0b4ca8"
BLUE_LIGHT = "#dbeafe"
RED = "#a41010"
RED_MID = "#c31717"
RED_LIGHT = "#f8dedd"
AMBER = "#c79623"
AMBER_DARK = "#8d6414"
SULFUR = "#f2b93b"
GRAY = "#5f6670"
GRAY_LIGHT = "#eef1f4"
INK = "#111111"
WHITE = "#ffffff"


def save_svg(drawing: draw.Drawing, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    drawing.save_svg(target)


def semantic_marker(object_id: str) -> draw.Raw:
    return draw.Raw(f"<!-- semantic_object:{object_id} -->")


def style_defs() -> draw.Raw:
    return draw.Raw(
        """
<defs>
  <linearGradient id="cardShade" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#ffffff"/>
    <stop offset="100%" stop-color="#fafcff"/>
  </linearGradient>
  <linearGradient id="sulfurRamp" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#f8d56a"/>
    <stop offset="45%" stop-color="#e3a331"/>
    <stop offset="100%" stop-color="#d7191c"/>
  </linearGradient>
  <linearGradient id="polymerBeam" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#f4d77e"/>
    <stop offset="42%" stop-color="#c79623"/>
    <stop offset="100%" stop-color="#8d6414"/>
  </linearGradient>
  <linearGradient id="metalSheen" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" stop-color="#8793a3"/>
    <stop offset="22%" stop-color="#f7f9fb"/>
    <stop offset="48%" stop-color="#a9b2bf"/>
    <stop offset="78%" stop-color="#e4e8ed"/>
    <stop offset="100%" stop-color="#667282"/>
  </linearGradient>
  <radialGradient id="softBlue" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#0b4ca8" stop-opacity="0.40"/>
    <stop offset="100%" stop-color="#0b4ca8" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="softRed" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#c31717" stop-opacity="0.48"/>
    <stop offset="100%" stop-color="#c31717" stop-opacity="0"/>
  </radialGradient>
  <filter id="cardShadow" x="-12%" y="-12%" width="124%" height="124%">
    <feDropShadow dx="0" dy="6" stdDeviation="7" flood-color="#10203d" flood-opacity="0.10"/>
  </filter>
  <filter id="tightShadow" x="-18%" y="-18%" width="136%" height="136%">
    <feDropShadow dx="1" dy="3" stdDeviation="3" flood-color="#07162d" flood-opacity="0.22"/>
  </filter>
  <pattern id="beamGrain" patternUnits="userSpaceOnUse" width="18" height="18">
    <path d="M1 13 C5 10, 9 16, 17 8" fill="none" stroke="#8d6414" stroke-width="0.75" opacity="0.45"/>
    <circle cx="5" cy="5" r="0.8" fill="#fff2bd" opacity="0.55"/>
    <circle cx="13" cy="14" r="0.7" fill="#6f4d12" opacity="0.28"/>
  </pattern>
</defs>
"""
    )


def text(
    drawing: draw.Drawing,
    value: str,
    x: float,
    y: float,
    size: float,
    *,
    fill: str = INK,
    weight: str | None = None,
    italic: bool = False,
    anchor: str = "start",
) -> None:
    attrs: dict[str, object] = {
        "fill": fill,
        "font_family": "Helvetica, Arial, sans-serif",
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
        text(drawing, line, x, y + index * line_height, size, fill=fill, weight=weight, italic=italic, anchor=anchor)


def rounded_rect(
    drawing: draw.Drawing,
    x: float,
    y: float,
    width: float,
    height: float,
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
            **attrs,
        )
    )


def arrow(
    drawing: draw.Drawing,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: str,
    *,
    width: float = 2.0,
    head_length: float = 15.0,
    head_width: float = 11.0,
    opacity: float = 1.0,
    dash: str | None = None,
) -> None:
    angle = math.atan2(y2 - y1, x2 - x1)
    back_x = x2 - head_length * math.cos(angle)
    back_y = y2 - head_length * math.sin(angle)
    nx = math.sin(angle)
    ny = -math.cos(angle)
    attrs: dict[str, object] = {}
    if dash:
        attrs["stroke_dasharray"] = dash
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
            **attrs,
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


def curved_arrow(
    drawing: draw.Drawing,
    start: tuple[float, float],
    controls: tuple[float, float, float, float, float, float],
    color: str,
    *,
    width: float = 2.0,
    opacity: float = 1.0,
) -> None:
    path = draw.Path(fill="none", stroke=color, stroke_width=width, stroke_linecap="round", opacity=opacity)
    path.M(*start)
    path.C(*controls)
    drawing.append(path)
    x1, y1 = controls[2], controls[3]
    x2, y2 = controls[4], controls[5]
    arrow(drawing, x1, y1, x2, y2, color, width=0, head_length=15, head_width=11, opacity=opacity)


def mini_axis(drawing: draw.Drawing, x: float, y: float, width: float, height: float) -> None:
    arrow(drawing, x, y + height, x, y, INK, width=1.3, head_length=10, head_width=8)
    arrow(drawing, x, y + height, x + width, y + height, INK, width=1.3, head_length=10, head_width=8)


def sulfur_atom(drawing: draw.Drawing, x: float, y: float, r: float = 8.0) -> None:
    drawing.append(draw.Circle(x, y, r, fill="#ffd05d", stroke="#8d6414", stroke_width=1.2))
    text(drawing, "S", x, y + 4.2, r * 1.05, fill="#5c3b04", weight="700", anchor="middle")


def minus_charge(drawing: draw.Drawing, x: float, y: float, r: float = 11.0) -> None:
    drawing.append(draw.Circle(x, y, r, fill=RED_MID, stroke="#7c0909", stroke_width=1.2))
    drawing.append(draw.Line(x - r * 0.45, y, x + r * 0.45, y, stroke=WHITE, stroke_width=2.2, stroke_linecap="round"))
