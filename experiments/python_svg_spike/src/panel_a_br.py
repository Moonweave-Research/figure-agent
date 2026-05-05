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
    add_clamp(drawing)
    add_charges(drawing)
    add_electrode(drawing)
    add_repulsion_arrow(drawing)
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


def add_clamp(drawing: draw.Drawing) -> None:
    drawing.append(draw.Rectangle(222, 82, 86, 24, fill="#c8cdd3", stroke="#66707b", stroke_width=1.2))
    h.hatching(drawing, 224, 84, 82, 20, step=8, color="#ffffff", stroke_width=1.1)
    drawing.append(draw.Rectangle(242, 106, 38, 22, fill="#737d88", stroke="#4e5964", stroke_width=1.0))
    drawing.append(draw.Line(224, 132, 298, 132, stroke="#30363d", stroke_width=2.0))
    h.multiline_text(
        drawing,
        ["Cantilever", "(probe)"],
        194,
        101,
        14,
        18,
        fill="#111111",
        anchor="middle",
    )


def add_charges(drawing: draw.Drawing) -> None:
    for x, y in [(250, 145), (235, 189), (215, 235), (190, 281), (161, 318)]:
        h.minus_charge(drawing, x, y, r=12)


def add_electrode(drawing: draw.Drawing) -> None:
    drawing.append(draw.Rectangle(510, 86, 38, 250, fill="#cdd4dc", stroke="#43505c", stroke_width=1.3))
    drawing.append(draw.Rectangle(513, 90, 16, 242, fill="#eef2f6", opacity=0.6))
    for y in range(122, 310, 34):
        drawing.append(draw.Line(517, y, 541, y, stroke="#ffffff", stroke_width=1.2, opacity=0.9))
    h.hatching(drawing, 510, 86, 38, 250, step=16, color="#7a8490", stroke_width=0.7)
    h.text(drawing, "+ V", 560, 166, 18, fill=h.RED_MID, italic=True)


def add_repulsion_arrow(drawing: draw.Drawing) -> None:
    h.arrow(
        drawing,
        430,
        186,
        324,
        186,
        h.RED_MID,
        width=14,
        head_length=28,
        head_width=34,
    )
    h.multiline_text(
        drawing,
        ["Repulsion", "(dominant)"],
        386,
        143,
        18,
        22,
        fill=h.RED,
        weight="700",
        italic=True,
        anchor="middle",
    )


def main() -> None:
    h.save_svg(build_panel(), OUT)


if __name__ == "__main__":
    main()
