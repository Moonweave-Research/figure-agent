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
    return drawing


def main() -> None:
    h.save_svg(build_panel(), OUT)


if __name__ == "__main__":
    main()
