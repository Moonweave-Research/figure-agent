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
    add_probe_icon(drawing)
    add_cantilever_beam(drawing)
    add_clamp(drawing)
    add_charges(drawing)
    add_electrode(drawing)
    add_field_lines(drawing)
    add_repulsion_arrow(drawing)
    add_maxwell_arrow(drawing)
    add_callout(drawing)
    return drawing


def add_probe_icon(drawing: draw.Drawing) -> None:
    drawing.append(draw.Rectangle(35, 36, 54, 54, rx=5, ry=5, fill="#eef3f8", stroke="#203a59", stroke_width=1.2))
    drawing.append(draw.Rectangle(47, 67, 38, 6, fill="#697789", stroke="#2d3845", stroke_width=0.9))
    arm = draw.Path(fill="#64748b", stroke="#2d3845", stroke_width=1.2)
    arm.M(52, 62)
    arm.L(78, 45)
    arm.L(84, 54)
    arm.L(58, 71)
    arm.Z()
    drawing.append(arm)
    drawing.append(draw.Line(60, 76, 60, 100, stroke="#111111", stroke_width=1.7))
    drawing.append(draw.Line(49, 100, 71, 100, stroke="#111111", stroke_width=1.7))
    drawing.append(draw.Line(53, 108, 67, 108, stroke="#111111", stroke_width=1.7))
    drawing.append(draw.Line(57, 116, 63, 116, stroke="#111111", stroke_width=1.7))
    h.text(drawing, "Macroscopic probe", 108, 67, 22, fill=h.BLUE, weight="700")


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


def add_field_lines(drawing: draw.Drawing) -> None:
    for y0, y1, lift in [(138, 130, -20), (176, 174, -8), (218, 218, 6), (268, 262, 18)]:
        path = draw.Path(
            fill="none",
            stroke="#aeb7c2",
            stroke_width=1.4,
            stroke_dasharray="8 8",
            opacity=0.75,
        )
        path.M(280, y0)
        path.C(342, y0 + lift, 430, y1 + lift, 508, y1)
        drawing.append(path)


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


def add_maxwell_arrow(drawing: draw.Drawing) -> None:
    h.arrow(
        drawing,
        330,
        255,
        413,
        255,
        h.BLUE_MID,
        width=7,
        head_length=19,
        head_width=19,
        opacity=0.85,
    )
    h.multiline_text(
        drawing,
        ["Maxwell attraction", "(suppressed)"],
        392,
        286,
        14,
        18,
        fill=h.BLUE_MID,
        anchor="middle",
    )


def add_callout(drawing: draw.Drawing) -> None:
    drawing.append(
        draw.Rectangle(
            32,
            350,
            556,
            48,
            rx=8,
            ry=8,
            fill="#fff4f2",
            stroke="#f0ccc7",
            stroke_width=1.2,
        )
    )
    h.text(
        drawing,
        "Charge-trapping-induced repulsion",
        WIDTH / 2,
        371,
        17,
        fill=h.RED,
        weight="700",
        italic=True,
        anchor="middle",
    )
    h.text(drawing, "Repulsion", 216, 391, 15, fill="#111111", anchor="middle")
    h.text(drawing, "dominates", 298, 391, 15, fill=h.RED, weight="700", anchor="middle")
    h.text(drawing, "over Maxwell attraction.", 412, 391, 15, fill="#111111", anchor="middle")


def main() -> None:
    h.save_svg(build_panel(), OUT)


if __name__ == "__main__":
    main()
