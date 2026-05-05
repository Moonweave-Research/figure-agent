from __future__ import annotations

from pathlib import Path

import drawsvg as draw

from stack import drawsvg_helpers as h
from stack.dvisvgm_math import math_svg


WIDTH = 1780
HEIGHT = 1000
OUT = Path(__file__).resolve().parents[1] / "full_figure.svg"

TL = (26, 28, 510, 425)
TR = (1214, 28, 540, 425)
CENTER = (615, 185, 530, 640)
BL = (26, 498, 532, 460)
BR = (1190, 498, 564, 460)


def build_figure() -> draw.Drawing:
    drawing = draw.Drawing(WIDTH, HEIGHT)
    drawing.append(draw.Rectangle(0, 0, WIDTH, HEIGHT, fill="#ffffff"))
    add_layout_cards(drawing)
    add_tl_s8_ring(drawing)
    add_tl_polymer_chain(drawing)
    add_tl_composition_swatch(drawing)
    add_tl_bullets(drawing)
    add_center_energy_bands(drawing)
    return drawing


def add_center_energy_bands(drawing: draw.Drawing) -> None:
    x, y, width, _ = CENTER
    h.text(drawing, "Converged deep charge trapping", x + width / 2, y + 55, 30, fill=h.RED, weight="700", anchor="middle")
    bx = x + 80
    h.arrow(drawing, bx, y + 450, bx, y + 115, "#111111", width=2.0, head_length=16, head_width=13)
    drawing.append(
        draw.Text(
            "Energy",
            18,
            0,
            0,
            fill="#111111",
            font_family="Helvetica, Arial, sans-serif",
            transform=f"translate({bx - 34} {y + 285}) rotate(-90)",
            text_anchor="middle",
        )
    )
    _label_box(drawing, x + 108, y + 120, 170, 45, "LUMO")
    _label_box(drawing, x + 108, y + 445, 170, 45, "HOMO")
    h.multiline_text(drawing, ["shallow", "states"], x + 112, y + 225, 17, 21, fill=h.BLUE_MID, anchor="start")
    for x1, x2, yy in [(x + 188, x + 262, y + 220), (x + 182, x + 262, y + 244), (x + 202, x + 262, y + 268)]:
        drawing.append(draw.Line(x1, yy, x2, yy, stroke=h.BLUE_MID, stroke_width=3.0, stroke_linecap="round"))
    h.multiline_text(drawing, ["deep", "states"], x + 112, y + 330, 17, 21, fill=h.RED, anchor="start")
    for yy in [y + 315, y + 335, y + 355, y + 375, y + 395, y + 415]:
        drawing.append(draw.Line(x + 178, yy, x + 262, yy, stroke=h.RED, stroke_width=3.5, stroke_linecap="round"))


def _label_box(drawing: draw.Drawing, x: float, y: float, width: float, height: float, label: str) -> None:
    drawing.append(draw.Rectangle(x, y, width, height, rx=5, ry=5, fill="#f1f4f7", stroke="#a8b0ba", stroke_width=1.2))
    h.text(drawing, label, x + width / 2, y + 30, 23, fill="#111111", weight="700", anchor="middle")


def add_tl_bullets(drawing: draw.Drawing) -> None:
    x, y, _, _ = TL
    items = ["Higher sulfur fraction", "Longer S-S sequences", "More deep trapping sites"]
    for index, item in enumerate(items):
        yy = y + 335 + index * 32
        h.text(drawing, "✓", x + 86, yy, 22, fill="#b87914", weight="700", anchor="middle")
        h.text(drawing, item, x + 112, yy, 18, fill="#111111", italic=True)


def add_tl_composition_swatch(drawing: draw.Drawing) -> None:
    x, y, _, _ = TL
    colors = ["#ffe27a", "#f4be45", "#dc752b", "#c71912"]
    sx, sy, sw, sh = x + 88, y + 265, 348, 16
    for index, color in enumerate(colors):
        drawing.append(draw.Rectangle(sx + index * sw / 4, sy, sw / 4, sh, fill=color, stroke="none"))
    h.arrow(drawing, sx + sw - 18, sy + sh / 2, sx + sw + 36, sy + sh / 2, "#d01812", width=16, head_length=30, head_width=40)
    drawing.append(draw.Rectangle(sx, sy, sw, sh, fill="none", stroke="#7a5018", stroke_width=1.0))
    h.text(drawing, "S60", sx - 34, sy + 8, 20, fill="#111111", anchor="middle")
    h.text(drawing, "S85", sx + sw + 58, sy + 8, 20, fill="#111111", anchor="middle")
    h.text(drawing, "Increasing sulfur content", sx + sw / 2, sy + 43, 17, fill="#111111", italic=True, anchor="middle")


def add_tl_polymer_chain(drawing: draw.Drawing) -> None:
    x, y, _, _ = TL
    h.text(drawing, "Delta", x + 178, y + 155, 17, fill="#111111", anchor="middle")
    h.arrow(drawing, x + 140, y + 178, x + 225, y + 178, "#111111", width=2.4, head_length=16, head_width=13)
    chain = [(x + 260, y + 172), (x + 295, y + 150), (x + 330, y + 172), (x + 365, y + 150), (x + 400, y + 172)]
    for i, (x1, y1) in enumerate(chain[:-1]):
        x2, y2 = chain[i + 1]
        drawing.append(draw.Line(x1, y1, x2, y2, stroke=h.AMBER_DARK, stroke_width=2.4))
    for px, py in chain:
        drawing.append(draw.Circle(px, py, 10, fill="#ffd45a", stroke=h.AMBER_DARK, stroke_width=1.5))
        h.text(drawing, "S", px, py + 4, 11, fill="#5b3512", weight="700", anchor="middle")
    drawing.append(draw.Line(x + 238, y + 190, x + 255, y + 180, stroke="#111111", stroke_width=2.0))
    drawing.append(draw.Line(x + 413, y + 164, x + 430, y + 154, stroke="#111111", stroke_width=2.0))
    h.text(drawing, "Sx", x + 460, y + 182, 20, fill="#111111", anchor="middle")


def add_tl_s8_ring(drawing: draw.Drawing) -> None:
    x, y, _, _ = TL
    icon_x, icon_y = x + 30, y + 28
    drawing.append(
        draw.Rectangle(icon_x, icon_y, 50, 50, rx=4, ry=4, fill="#173763", stroke="#0b2342", stroke_width=1.2)
    )
    for dx, dy in [(16, 16), (34, 16), (25, 30)]:
        drawing.append(draw.Circle(icon_x + dx, icon_y + dy, 6, fill="#eef6ff"))
    drawing.append(draw.Line(icon_x + 16, icon_y + 16, icon_x + 25, icon_y + 30, stroke="#eef6ff", stroke_width=2))
    drawing.append(draw.Line(icon_x + 34, icon_y + 16, icon_x + 25, icon_y + 30, stroke="#eef6ff", stroke_width=2))
    h.multiline_text(
        drawing,
        ["Sulfur polymer origin", "(composition tuning)"],
        x + 100,
        y + 52,
        25,
        30,
        fill=h.BLUE,
        weight="700",
        anchor="start",
    )

    cx, cy, r = x + 82, y + 178, 58
    points = [
        (cx + r * 0.78, cy),
        (cx + r * 0.50, cy + r * 0.72),
        (cx - r * 0.25, cy + r * 0.82),
        (cx - r * 0.82, cy + r * 0.30),
        (cx - r * 0.78, cy - r * 0.45),
        (cx - r * 0.18, cy - r * 0.86),
        (cx + r * 0.56, cy - r * 0.64),
        (cx + r * 0.88, cy - r * 0.05),
    ]
    for i, (x1, y1) in enumerate(points):
        x2, y2 = points[(i + 1) % len(points)]
        drawing.append(draw.Line(x1, y1, x2, y2, stroke=h.AMBER_DARK, stroke_width=2.0))
    for px, py in points:
        drawing.append(draw.Circle(px, py, 10, fill="#ffd45a", stroke=h.AMBER_DARK, stroke_width=1.6))
        h.text(drawing, "S", px, py + 4, 11, fill="#5b3512", weight="700", anchor="middle")
    h.text(drawing, "S8", cx, cy + 92, 20, fill="#111111", anchor="middle")


def add_layout_cards(drawing: draw.Drawing) -> None:
    for x, y, width, height in [TL, TR, BL, BR]:
        rounded_rect(drawing, x, y, width, height, fill="#fbfcfe", stroke="#e4e7eb", radius=30)
    rounded_rect(drawing, *CENTER, fill="#fffefe", stroke="#ddb9b9", radius=36, stroke_width=2.0)


def rounded_rect(
    drawing: draw.Drawing,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str,
    radius: float,
    stroke_width: float = 1.4,
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
        )
    )


def main() -> None:
    h.save_svg(build_figure(), OUT)


if __name__ == "__main__":
    main()
