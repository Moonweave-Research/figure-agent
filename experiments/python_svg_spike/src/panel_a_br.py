from __future__ import annotations

from pathlib import Path

import drawsvg as draw

from stack import drawsvg_helpers as h


WIDTH = 620
HEIGHT = 420
OUT = Path(__file__).resolve().parents[1] / "panel_A_BR.svg"


def build_panel() -> draw.Drawing:
    drawing = draw.Drawing(WIDTH, HEIGHT)
    h.card(drawing, WIDTH, HEIGHT)
    add_cantilever_beam(drawing)
    return drawing


def add_cantilever_beam(drawing: draw.Drawing) -> None:
    beam = ((258, 108), (244, 176, 214, 262, 154, 326))
    drawing.append(
        h.cubic_path(
            beam[0],
            beam[1],
            fill="none",
            stroke=h.AMBER,
            stroke_width=28,
            stroke_linecap="round",
            opacity=0.35,
        )
    )
    drawing.append(
        h.cubic_path(
            beam[0],
            beam[1],
            fill="none",
            stroke="#d0a538",
            stroke_width=20,
            stroke_linecap="round",
        )
    )
    drawing.append(
        h.cubic_path(
            beam[0],
            beam[1],
            fill="none",
            stroke=h.AMBER_DARK,
            stroke_width=1.4,
            stroke_linecap="round",
            opacity=0.55,
        )
    )


def main() -> None:
    h.save_svg(build_panel(), OUT)


if __name__ == "__main__":
    main()
