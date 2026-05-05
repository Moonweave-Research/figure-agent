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
    return drawing


def main() -> None:
    h.save_svg(build_panel(), OUT)


if __name__ == "__main__":
    main()
