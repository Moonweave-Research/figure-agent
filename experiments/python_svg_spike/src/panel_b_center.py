from __future__ import annotations

from pathlib import Path

import drawsvg as draw

from stack import drawsvg_helpers as h


WIDTH = 560
HEIGHT = 640
OUT = Path(__file__).resolve().parents[1] / "panel_B_center.svg"


def build_panel() -> draw.Drawing:
    drawing = draw.Drawing(WIDTH, HEIGHT)
    h.card(drawing, WIDTH, HEIGHT, stroke="#ddb9b9", radius=28)
    add_title(drawing)
    return drawing


def add_title(drawing: draw.Drawing) -> None:
    drawing.append(
        draw.Rectangle(
            36,
            28,
            WIDTH - 72,
            80,
            rx=14,
            ry=14,
            fill="#fffafa",
            stroke="#efd6d6",
            stroke_width=1.0,
        )
    )
    h.text(
        drawing,
        "Converged deep charge trapping",
        WIDTH / 2,
        80,
        29,
        fill=h.RED,
        weight="700",
        anchor="middle",
    )


def main() -> None:
    h.save_svg(build_panel(), OUT)


if __name__ == "__main__":
    main()
