from __future__ import annotations

import io
from pathlib import Path

import drawsvg as draw

from stack import drawsvg_helpers as h
from stack.dvisvgm_math import math_svg


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
    add_tl_polymer_chain(drawing)
    add_tl_composition_swatch(drawing)
    add_tl_bullets(drawing)
    add_center_energy_bands(drawing)
    add_center_dos_math(drawing)
    add_center_callout(drawing)
    add_tr_pe_loop(drawing)
    add_tr_current_decay(drawing)
    add_bl_model_flow(drawing)
    add_bl_current_decay_plot(drawing)
    add_bl_dos_plot(drawing)
    return drawing


def add_bl_dos_plot(drawing: draw.Drawing) -> None:
    x, y, _, _ = BL
    px, py = x + 330, y + 220
    h.arrow(drawing, px, py + 160, px, py + 20, "#111111", width=1.4, head_length=11, head_width=9)
    h.arrow(drawing, px, py + 160, px + 132, py + 160, "#111111", width=1.4, head_length=11, head_width=9)
    drawing.append(_gaussian_lobe(fill="#dbeafe", stroke=h.BLUE_MID, x=px + 8, y=py + 35, width=78, height=58, sigma=0.26, id_prefix="bl_shallow"))
    drawing.append(_gaussian_lobe(fill="#e9a5a5", stroke=h.RED, x=px + 8, y=py + 84, width=110, height=90, sigma=0.46, id_prefix="bl_deep"))
    h.text(drawing, "shallow", px + 90, py + 58, 14, fill=h.BLUE_MID, italic=True)
    h.text(drawing, "deep", px + 102, py + 135, 14, fill=h.RED, italic=True)
    drawing.append(draw.Line(px, py + 98, px + 118, py + 98, stroke="#777777", stroke_width=1.0, stroke_dasharray="5 5"))
    h.arrow(drawing, px + 118, py + 98, px + 118, py + 148, "#111111", width=1.1, head_length=8, head_width=7)
    h.arrow(drawing, px + 118, py + 148, px + 118, py + 98, "#111111", width=1.1, head_length=8, head_width=7)
    drawing.append(math_svg(r"E_t", x=px + 128, y=py + 112, width=22, prefix="bl_et"))
    drawing.append(math_svg(r"g(E_t)", x=px + 58, y=py + 176, width=54, prefix="bl_g_axis"))
    drawing.append(
        draw.Text(
            "Energy",
            13,
            0,
            0,
            fill="#111111",
            font_family="Helvetica, Arial, sans-serif",
            transform=f"translate({px - 30} {py + 90}) rotate(-90)",
            text_anchor="middle",
        )
    )


def add_bl_current_decay_plot(drawing: draw.Drawing) -> None:
    x, y, _, _ = BL
    px, py = x + 58, y + 220
    h.arrow(drawing, px, py + 160, px, py + 20, "#111111", width=1.4, head_length=11, head_width=9)
    h.arrow(drawing, px, py + 160, px + 170, py + 160, "#111111", width=1.4, head_length=11, head_width=9)
    drawing.append(draw.Line(px + 10, py + 38, px + 158, py + 146, stroke=h.BLUE_MID, stroke_width=2.4))
    drawing.append(draw.Line(px + 55, py + 85, px + 55, py + 148, stroke=h.BLUE_MID, stroke_width=1.3, stroke_dasharray="6 6"))
    drawing.append(draw.Line(px + 55, py + 148, px + 120, py + 148, stroke=h.BLUE_MID, stroke_width=1.3, stroke_dasharray="6 6"))
    drawing.append(math_svg(r"I(t)\propto t^{-n}", x=px + 76, y=py + 65, width=104, prefix="bl_decay_it", color=h.BLUE_MID))
    h.text(drawing, "slope = -n", px + 54, py + 136, 14, fill=h.BLUE_MID, italic=True, anchor="middle")
    h.text(drawing, "t (s)", px + 98, py + 193, 14, fill="#111111", italic=True, anchor="middle")
    drawing.append(
        draw.Text(
            "I(t)",
            14,
            0,
            0,
            fill="#111111",
            font_family="Helvetica, Arial, sans-serif",
            transform=f"translate({px - 34} {py + 86}) rotate(-90)",
            text_anchor="middle",
        )
    )


def add_bl_model_flow(drawing: draw.Drawing) -> None:
    x, y, _, _ = BL
    brain_x, brain_y = x + 32, y + 30
    drawing.append(draw.Circle(brain_x + 18, brain_y + 24, 20, fill="#eef5fb", stroke=h.BLUE, stroke_width=1.2))
    drawing.append(draw.Circle(brain_x + 36, brain_y + 24, 20, fill="#eef5fb", stroke=h.BLUE, stroke_width=1.2))
    drawing.append(draw.Line(brain_x + 27, brain_y + 7, brain_x + 27, brain_y + 42, stroke=h.BLUE, stroke_width=1.1))
    h.text(drawing, "Interpretation (converged trap model)", x + 96, y + 58, 22, fill=h.BLUE, weight="700")
    items = [
        (x + 28, y + 112, 105, 46, r"I(t)\propto t^{-n}", "blue"),
        (x + 168, y + 108, 96, 56, r"\mathrm{Debye}\ e^{-t/\tau}", "gray"),
        (x + 302, y + 112, 75, 46, r"\tau_d", "gray"),
        (x + 420, y + 112, 78, 46, r"g(E_t)", "gray"),
    ]
    for index, (ix, iy, iw, ih, label, tone) in enumerate(items):
        stroke = h.BLUE_MID if tone == "blue" else "#b9c0c8"
        fill = "#f7fbff" if tone == "blue" else "#f7f7f7"
        drawing.append(draw.Rectangle(ix, iy, iw, ih, rx=5, ry=5, fill=fill, stroke=stroke, stroke_width=1.2))
        drawing.append(math_svg(label, x=ix + 12, y=iy + 15, width=iw - 24, prefix=f"bl_flow_{index}", color=h.BLUE_MID if tone == "blue" else "#222222"))
    for x1, x2 in [(x + 138, x + 166), (x + 268, x + 300), (x + 382, x + 416)]:
        h.arrow(drawing, x1, y + 135, x2, y + 135, "#6f7780", width=1.5, head_length=10, head_width=8)


def add_tr_current_decay(drawing: draw.Drawing) -> None:
    x, y, _, _ = TR
    h.text(drawing, "Current decay", x + 394, y + 122, 18, fill=h.BLUE_MID, anchor="middle")
    px, py = x + 315, y + 145
    h.arrow(drawing, px, py + 250, px, py + 38, "#111111", width=1.4, head_length=12, head_width=10)
    h.arrow(drawing, px, py + 250, px + 220, py + 250, "#111111", width=1.4, head_length=12, head_width=10)
    for index, label in enumerate(["10^-3", "10^-2", "10^-1", "10^0", "10^1", "10^2"]):
        xx = px + 16 + index * 34
        drawing.append(draw.Line(xx, py + 250, xx, py + 256, stroke="#111111", stroke_width=0.8))
        h.text(drawing, label, xx, py + 274, 11, fill="#111111", anchor="middle")
    for index, label in enumerate(["10^0", "10^-2", "10^-4", "10^-6", "10^-8"]):
        yy = py + 50 + index * 43
        drawing.append(draw.Line(px - 6, yy, px, yy, stroke="#111111", stroke_width=0.8))
        h.text(drawing, label, px - 10, yy + 4, 11, fill="#111111", anchor="end")
    drawing.append(draw.Line(px + 14, py + 60, px + 208, py + 230, stroke=h.BLUE_MID, stroke_width=2.5))
    drawing.append(draw.Line(px + 82, py + 102, px + 82, py + 175, stroke=h.BLUE_MID, stroke_width=1.5, stroke_dasharray="6 6"))
    drawing.append(draw.Line(px + 82, py + 175, px + 154, py + 175, stroke=h.BLUE_MID, stroke_width=1.5, stroke_dasharray="6 6"))
    drawing.append(math_svg(r"I(t)\propto t^{-n}", x=px + 128, y=py + 88, width=108, prefix="tr_decay_it", color=h.BLUE_MID))
    h.text(drawing, "slope = -n", px + 96, py + 210, 15, fill=h.BLUE_MID, italic=True)
    h.text(drawing, "t (s)", px + 115, py + 306, 15, fill="#111111", italic=True, anchor="middle")
    drawing.append(
        draw.Text(
            "I (A)",
            15,
            0,
            0,
            fill="#111111",
            font_family="Helvetica, Arial, sans-serif",
            transform=f"translate({px - 58} {py + 153}) rotate(-90)",
            text_anchor="middle",
        )
    )


def add_tr_pe_loop(drawing: draw.Drawing) -> None:
    x, y, _, _ = TR
    drawing.append(draw.Rectangle(x + 28, y + 28, 66, 50, rx=5, ry=5, fill="#eef4fb", stroke="#173763", stroke_width=1.4))
    path = draw.Path(fill="none", stroke=h.BLUE, stroke_width=2.2)
    path.M(x + 42, y + 58)
    path.C(x + 50, y + 38, x + 70, y + 38, x + 78, y + 58)
    path.C(x + 84, y + 75, x + 57, y + 75, x + 62, y + 58)
    drawing.append(path)
    drawing.append(draw.Circle(x + 84, y + 43, 4, fill=h.BLUE))
    drawing.append(draw.Circle(x + 84, y + 62, 4, fill="none", stroke=h.BLUE, stroke_width=1.8))
    h.text(drawing, "Electrical evidence", x + 112, y + 64, 25, fill=h.BLUE, weight="700")
    h.text(drawing, "P-E response", x + 150, y + 122, 18, fill="#111111", anchor="middle")
    px, py = x + 48, y + 150
    drawing.append(draw.Line(px, py + 150, px + 190, py + 150, stroke="#111111", stroke_width=1.3, stroke_dasharray="7 7"))
    drawing.append(draw.Line(px + 94, py + 28, px + 94, py + 252, stroke="#111111", stroke_width=1.3, stroke_dasharray="7 7"))
    h.arrow(drawing, px + 10, py + 150, px + 194, py + 150, "#111111", width=1.3, head_length=12, head_width=10)
    h.arrow(drawing, px + 94, py + 240, px + 94, py + 30, "#111111", width=1.3, head_length=12, head_width=10)
    loop = draw.Path(fill="none", stroke=h.RED_MID, stroke_width=2.5)
    loop.M(px + 4, py + 220)
    loop.C(px + 80, py + 210, px + 38, py + 55, px + 180, py + 38)
    loop.C(px + 92, py + 54, px + 142, py + 210, px + 4, py + 220)
    drawing.append(loop)
    h.text(drawing, "P", px + 82, py + 25, 17, fill="#111111", italic=True, anchor="end")
    h.text(drawing, "E", px + 198, py + 157, 17, fill="#111111", italic=True)


def add_center_callout(drawing: draw.Drawing) -> None:
    x, y, width, _ = CENTER
    rounded_rect(drawing, x + 36, y + 535, width - 72, 78, fill="#fff5f3", stroke="#f0ccc7", radius=10)
    h.multiline_text(
        drawing,
        ["Deep states dominate the trap landscape", "near midgap, driving the long-lived", "repulsive response."],
        x + width / 2,
        y + 562,
        18,
        20,
        fill=h.RED,
        italic=True,
        anchor="middle",
    )


def add_center_dos_math(drawing: draw.Drawing) -> None:
    x, y, _, _ = CENTER
    ax = x + 308
    h.arrow(drawing, ax, y + 445, ax, y + 155, "#111111", width=1.7, head_length=13, head_width=11)
    h.arrow(drawing, ax, y + 445, ax + 170, y + 445, "#111111", width=1.7, head_length=13, head_width=11)
    h.text(drawing, "DOS", ax + 28, y + 135, 18, fill="#111111")
    drawing.append(math_svg(r"g(E_t)", x=ax + 82, y=y + 118, width=56, prefix="center_top_g"))
    drawing.append(math_svg(r"g(E_t)", x=ax + 80, y=y + 462, width=60, prefix="center_axis_g"))
    drawing.append(_gaussian_lobe(fill="#dbeafe", stroke=h.BLUE_MID, x=ax + 12, y=y + 170, width=90, height=84, sigma=0.28, id_prefix="center_shallow"))
    h.text(drawing, "shallow", ax + 120, y + 230, 17, fill=h.BLUE_MID)
    drawing.append(_gaussian_lobe(fill="#e9a5a5", stroke=h.RED, x=ax + 8, y=y + 300, width=155, height=155, sigma=0.48, id_prefix="center_deep"))
    h.text(drawing, "deep", ax + 138, y + 383, 19, fill=h.RED, weight="700")
    drawing.append(draw.Line(x + 278, y + 292, ax + 176, y + 292, stroke="#6f7780", stroke_width=1.1, stroke_dasharray="6 6"))
    h.arrow(drawing, ax + 176, y + 292, ax + 176, y + 383, "#111111", width=1.4, head_length=12, head_width=10)
    h.arrow(drawing, ax + 176, y + 383, ax + 176, y + 292, "#111111", width=1.4, head_length=12, head_width=10)
    drawing.append(math_svg(r"E_t\sim 0.5\text{--}1.0\,\mathrm{eV}", x=ax + 98, y=y + 337, width=102, prefix="center_et"))


def _gaussian_lobe(
    *,
    fill: str,
    stroke: str,
    x: float,
    y: float,
    width: float,
    height: float,
    sigma: float,
    id_prefix: str,
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
    return h.nested_svg(buffer.getvalue(), x, y, width, height, prefix=id_prefix)


def add_center_energy_bands(drawing: draw.Drawing) -> None:
    x, y, width, _ = CENTER
    h.text(drawing, "Converged deep charge trapping", x + width / 2, y + 55, 30, fill=h.RED, weight="700", anchor="middle")
    bx = x + 80
    h.arrow(drawing, bx, y + 450, bx, y + 115, "#111111", width=2.0, head_length=16, head_width=13)
    drawing.append(
        draw.Text(
            "Energy",
            18,
            0,
            0,
            fill="#111111",
            font_family="Helvetica, Arial, sans-serif",
            transform=f"translate({bx - 34} {y + 285}) rotate(-90)",
            text_anchor="middle",
        )
    )
    _label_box(drawing, x + 108, y + 120, 170, 45, "LUMO")
    _label_box(drawing, x + 108, y + 445, 170, 45, "HOMO")
    h.multiline_text(drawing, ["shallow", "states"], x + 112, y + 225, 17, 21, fill=h.BLUE_MID, anchor="start")
    for x1, x2, yy in [(x + 188, x + 262, y + 220), (x + 182, x + 262, y + 244), (x + 202, x + 262, y + 268)]:
        drawing.append(draw.Line(x1, yy, x2, yy, stroke=h.BLUE_MID, stroke_width=3.0, stroke_linecap="round"))
    h.multiline_text(drawing, ["deep", "states"], x + 112, y + 330, 17, 21, fill=h.RED, anchor="start")
    for yy in [y + 315, y + 335, y + 355, y + 375, y + 395, y + 415]:
        drawing.append(draw.Line(x + 178, yy, x + 262, yy, stroke=h.RED, stroke_width=3.5, stroke_linecap="round"))


def _label_box(drawing: draw.Drawing, x: float, y: float, width: float, height: float, label: str) -> None:
    drawing.append(draw.Rectangle(x, y, width, height, rx=5, ry=5, fill="#f1f4f7", stroke="#a8b0ba", stroke_width=1.2))
    h.text(drawing, label, x + width / 2, y + 30, 23, fill="#111111", weight="700", anchor="middle")


def add_tl_bullets(drawing: draw.Drawing) -> None:
    x, y, _, _ = TL
    items = ["Higher sulfur fraction", "Longer S-S sequences", "More deep trapping sites"]
    for index, item in enumerate(items):
        yy = y + 335 + index * 32
        h.text(drawing, "✓", x + 86, yy, 22, fill="#b87914", weight="700", anchor="middle")
        h.text(drawing, item, x + 112, yy, 18, fill="#111111", italic=True)


def add_tl_composition_swatch(drawing: draw.Drawing) -> None:
    x, y, _, _ = TL
    colors = ["#ffe27a", "#f4be45", "#dc752b", "#c71912"]
    sx, sy, sw, sh = x + 88, y + 265, 348, 16
    for index, color in enumerate(colors):
        drawing.append(draw.Rectangle(sx + index * sw / 4, sy, sw / 4, sh, fill=color, stroke="none"))
    h.arrow(drawing, sx + sw - 18, sy + sh / 2, sx + sw + 36, sy + sh / 2, "#d01812", width=16, head_length=30, head_width=40)
    drawing.append(draw.Rectangle(sx, sy, sw, sh, fill="none", stroke="#7a5018", stroke_width=1.0))
    h.text(drawing, "S60", sx - 34, sy + 8, 20, fill="#111111", anchor="middle")
    h.text(drawing, "S85", sx + sw + 58, sy + 8, 20, fill="#111111", anchor="middle")
    h.text(drawing, "Increasing sulfur content", sx + sw / 2, sy + 43, 17, fill="#111111", italic=True, anchor="middle")


def add_tl_polymer_chain(drawing: draw.Drawing) -> None:
    x, y, _, _ = TL
    h.text(drawing, "Delta", x + 178, y + 155, 17, fill="#111111", anchor="middle")
    h.arrow(drawing, x + 140, y + 178, x + 225, y + 178, "#111111", width=2.4, head_length=16, head_width=13)
    chain = [(x + 260, y + 172), (x + 295, y + 150), (x + 330, y + 172), (x + 365, y + 150), (x + 400, y + 172)]
    for i, (x1, y1) in enumerate(chain[:-1]):
        x2, y2 = chain[i + 1]
        drawing.append(draw.Line(x1, y1, x2, y2, stroke=h.AMBER_DARK, stroke_width=2.4))
    for px, py in chain:
        drawing.append(draw.Circle(px, py, 10, fill="#ffd45a", stroke=h.AMBER_DARK, stroke_width=1.5))
        h.text(drawing, "S", px, py + 4, 11, fill="#5b3512", weight="700", anchor="middle")
    drawing.append(draw.Line(x + 238, y + 190, x + 255, y + 180, stroke="#111111", stroke_width=2.0))
    drawing.append(draw.Line(x + 413, y + 164, x + 430, y + 154, stroke="#111111", stroke_width=2.0))
    h.text(drawing, "Sx", x + 460, y + 182, 20, fill="#111111", anchor="middle")


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
