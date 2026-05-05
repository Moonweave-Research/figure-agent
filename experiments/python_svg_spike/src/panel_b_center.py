from __future__ import annotations

import io
from pathlib import Path

import drawsvg as draw

from stack import drawsvg_helpers as h
from stack.dvisvgm_math import math_svg


WIDTH = 560
HEIGHT = 640
OUT = Path(__file__).resolve().parents[1] / "panel_B_center.svg"


def build_panel() -> draw.Drawing:
    drawing = draw.Drawing(WIDTH, HEIGHT)
    h.card(drawing, WIDTH, HEIGHT, stroke="#ddb9b9", radius=28)
    add_title(drawing)
    add_energy_axis(drawing)
    add_lumo_box(drawing)
    add_homo_box(drawing)
    add_shallow_lines(drawing)
    add_deep_lines(drawing)
    add_dos_shallow(drawing)
    add_dos_deep(drawing)
    add_et_annotation(drawing)
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


def add_energy_axis(drawing: draw.Drawing) -> None:
    h.arrow(drawing, 78, 542, 78, 134, "#111111", width=2.0, head_length=16, head_width=13)
    drawing.append(
        draw.Text(
            "Energy",
            18,
            0,
            0,
            fill="#111111",
            font_family="Helvetica, Arial, sans-serif",
            transform="translate(48 356) rotate(-90)",
            text_anchor="middle",
        )
    )


def add_lumo_box(drawing: draw.Drawing) -> None:
    drawing.append(
        draw.Rectangle(116, 128, 166, 42, rx=5, ry=5, fill="#f1f4f7", stroke="#a8b0ba", stroke_width=1.2)
    )
    h.text(drawing, "LUMO", 199, 156, 23, fill="#111111", weight="700", anchor="middle")


def add_homo_box(drawing: draw.Drawing) -> None:
    drawing.append(
        draw.Rectangle(116, 492, 166, 42, rx=5, ry=5, fill="#f1f4f7", stroke="#a8b0ba", stroke_width=1.2)
    )
    h.text(drawing, "HOMO", 199, 520, 23, fill="#111111", weight="700", anchor="middle")


def add_shallow_lines(drawing: draw.Drawing) -> None:
    h.multiline_text(drawing, ["shallow", "states"], 122, 232, 17, 21, fill=h.BLUE_MID, anchor="start")
    for x1, x2, y in [(184, 268, 226), (178, 268, 250), (196, 268, 274)]:
        drawing.append(
            draw.Line(x1, y, x2, y, stroke=h.BLUE_MID, stroke_width=3.0, stroke_linecap="round")
        )


def add_deep_lines(drawing: draw.Drawing) -> None:
    h.multiline_text(drawing, ["deep", "states"], 120, 352, 17, 21, fill=h.RED, anchor="start")
    for y in [326, 346, 366, 386, 406, 426, 446]:
        drawing.append(draw.Line(176, y, 268, y, stroke=h.RED, stroke_width=3.5, stroke_linecap="round"))


def add_dos_shallow(drawing: draw.Drawing) -> None:
    drawing.append(_gaussian_lobe(fill="#dbeafe", stroke=h.BLUE_MID, x=318, y=184, width=92, height=82, sigma=0.28))
    h.text(drawing, "shallow", 420, 240, 17, fill=h.BLUE_MID)


def add_dos_deep(drawing: draw.Drawing) -> None:
    drawing.append(_gaussian_lobe(fill="#e9a5a5", stroke=h.RED, x=318, y=294, width=146, height=172, sigma=0.48))
    h.text(drawing, "deep", 458, 385, 19, fill=h.RED, weight="700")


def add_et_annotation(drawing: draw.Drawing) -> None:
    drawing.append(draw.Line(276, 298, 488, 298, stroke="#6f7780", stroke_width=1.2, stroke_dasharray="6 6"))
    drawing.append(draw.Line(488, 298, 488, 382, stroke="#111111", stroke_width=1.5))
    drawing.append(draw.Lines(488, 296, 482, 309, 494, 309, close=True, fill="#111111"))
    drawing.append(draw.Lines(488, 384, 482, 371, 494, 371, close=True, fill="#111111"))
    drawing.append(
        math_svg(
            r"E_t\sim 0.5\text{--}1.0\,\mathrm{eV}",
            x=410,
            y=326,
            width=128,
            prefix="b_et",
            color="#111111",
        )
    )


def _gaussian_lobe(
    *,
    fill: str,
    stroke: str,
    x: float,
    y: float,
    width: float,
    height: float,
    sigma: float,
) -> draw.Raw:
    import matplotlib

    matplotlib.use("svg")
    import matplotlib.pyplot as plt
    import numpy as np

    energy = np.linspace(-1.0, 1.0, 180)
    density = np.exp(-0.5 * (energy / sigma) ** 2)
    fig, ax = plt.subplots(figsize=(1.35, 1.4))
    ax.fill_betweenx(energy, 0, density, color=fill, alpha=0.95)
    ax.plot(density, energy, color=stroke, linewidth=1.4)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(-1.0, 1.0)
    ax.axis("off")
    buffer = io.StringIO()
    fig.savefig(buffer, format="svg", transparent=True, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return h.nested_svg(buffer.getvalue(), x, y, width, height)


def main() -> None:
    h.save_svg(build_panel(), OUT)


if __name__ == "__main__":
    main()
