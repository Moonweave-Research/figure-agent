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
    return drawing


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
