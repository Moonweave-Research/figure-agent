from __future__ import annotations

from pathlib import Path

import drawsvg as draw

from stack import drawsvg_helpers as h


WIDTH = 1780
HEIGHT = 1000
OUT = Path(__file__).resolve().parents[1] / "full_figure.svg"


def build_figure() -> draw.Drawing:
    drawing = draw.Drawing(WIDTH, HEIGHT)
    drawing.append(draw.Rectangle(0, 0, WIDTH, HEIGHT, fill="#ffffff"))
    return drawing


def main() -> None:
    h.save_svg(build_figure(), OUT)


if __name__ == "__main__":
    main()
