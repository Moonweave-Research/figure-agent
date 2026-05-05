from __future__ import annotations

import html
import math
import re
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

import drawsvg as draw


BLUE = "#12366e"
BLUE_MID = "#0b4ca8"
BLUE_LIGHT = "#dbeafe"
RED = "#a41010"
RED_MID = "#c31717"
RED_LIGHT = "#f8dedd"
GRAY = "#5f6670"
GRAY_LIGHT = "#eef1f4"
AMBER = "#c79623"
AMBER_DARK = "#8d6414"
WHITE = "#ffffff"


def save_svg(drawing: draw.Drawing, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    drawing.save_svg(target)


def card(
    drawing: draw.Drawing,
    width: float,
    height: float,
    stroke: str = "#e3e6eb",
    fill: str = WHITE,
    radius: float = 22,
) -> None:
    drawing.append(
        draw.Rectangle(
            1,
            1,
            width - 2,
            height - 2,
            rx=radius,
            ry=radius,
            fill=fill,
            stroke=stroke,
            stroke_width=1.4,
        )
    )


def text(
    drawing: draw.Drawing,
    value: str,
    x: float,
    y: float,
    size: float,
    fill: str = "#111111",
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
    fill: str = "#111111",
    weight: str | None = None,
    italic: bool = False,
    anchor: str = "middle",
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


def hatching(
    drawing: draw.Drawing,
    x: float,
    y: float,
    width: float,
    height: float,
    step: float = 8.0,
    color: str = "#7b8490",
    stroke_width: float = 1.0,
) -> None:
    start = -height
    end = width
    pos = start
    while pos < end:
        x1 = x + max(pos, 0)
        y1 = y + max(-pos, 0)
        x2 = x + min(pos + height, width)
        y2 = y + height - max(pos + height - width, 0)
        drawing.append(draw.Line(x1, y1, x2, y2, stroke=color, stroke_width=stroke_width))
        pos += step


def cubic_path(
    start: tuple[float, float],
    controls: tuple[float, float, float, float, float, float],
    **attrs: object,
) -> draw.Path:
    path = draw.Path(**attrs)
    path.M(*start)
    path.C(*controls)
    return path


def minus_charge(drawing: draw.Drawing, x: float, y: float, r: float = 11.0) -> None:
    drawing.append(draw.Circle(x, y, r, fill=RED_MID, stroke="#7c0909", stroke_width=1.2))
    drawing.append(
        draw.Line(
            x - r * 0.45,
            y,
            x + r * 0.45,
            y,
            stroke=WHITE,
            stroke_width=2.4,
            stroke_linecap="round",
        )
    )


def nested_svg(svg_text: str, x: float, y: float, width: float, height: float) -> draw.Raw:
    cleaned = _without_xml_declaration(svg_text)
    root = ET.fromstring(cleaned)
    view_box = root.attrib.get("viewBox")
    if not view_box:
        raise ValueError("nested SVG requires a viewBox")
    body = re.sub(r"^<svg[^>]*>", "", cleaned.strip(), count=1)
    body = re.sub(r"</svg>\s*$", "", body)
    return draw.Raw(
        f'<svg x="{x:.3f}" y="{y:.3f}" width="{width:.3f}" height="{height:.3f}" '
        f'viewBox="{escape_attr(view_box)}" overflow="visible">{body}</svg>'
    )


def raw_nested_from_file(path: str | Path, x: float, y: float, width: float, height: float) -> draw.Raw:
    return nested_svg(Path(path).read_text(), x, y, width, height)


def _without_xml_declaration(svg_text: str) -> str:
    text_without_decl = re.sub(r"^\s*<\?xml[^>]*>\s*", "", svg_text)
    text_without_comment = re.sub(r"^\s*<!--.*?-->\s*", "", text_without_decl, flags=re.DOTALL)
    return re.sub(r"^\s*<!DOCTYPE\s+svg[^>]*(?:\[[\s\S]*?\]\s*)?>\s*", "", text_without_comment)


def escape_attr(value: str) -> str:
    return html.escape(value, quote=True)
