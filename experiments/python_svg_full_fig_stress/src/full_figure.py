from __future__ import annotations

from pathlib import Path

import drawsvg as draw

from stack import drawsvg_helpers as h


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
    return drawing


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
