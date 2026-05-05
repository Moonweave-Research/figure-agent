from __future__ import annotations

import io
from pathlib import Path

import drawsvg as draw
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from stack import drawsvg_helpers as h
from stack.dvisvgm_math import math_svg


matplotlib.use("Agg")
matplotlib.rcParams["svg.fonttype"] = "none"
matplotlib.rcParams["svg.hashsalt"] = "python-svg-style-capability"

WIDTH = 1780
HEIGHT = 1000
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "style_capability.svg"

A = (30, 30, 540, 430)
B = (620, 30, 540, 430)
C = (1210, 30, 540, 430)
D = (30, 510, 540, 430)
E = (620, 510, 540, 430)
F = (1210, 510, 540, 430)


def build_figure() -> draw.Drawing:
    drawing = draw.Drawing(WIDTH, HEIGHT)
    drawing.append(draw.Rectangle(0, 0, WIDTH, HEIGHT, fill="#f6f8fb"))
    drawing.append(h.style_defs())
    add_cards(drawing)
    add_material_beam(drawing)
    add_isometric_device(drawing)
    add_energy_surface(drawing)
    add_plot_schematic_fusion(drawing)
    add_texture_swatches(drawing)
    add_print_readiness(drawing)
    return drawing


def add_cards(drawing: draw.Drawing) -> None:
    h.card(drawing, *A, "A", "Material texture")
    h.card(drawing, *B, "B", "Pseudo-3D device stack")
    h.card(drawing, *C, "C", "Energy surface and masks")
    h.card(drawing, *D, "D", "Plot + schematic fusion")
    h.card(drawing, *E, "E", "Vector texture swatches")
    h.card(drawing, *F, "F", "Print-readiness stress")


def add_material_beam(drawing: draw.Drawing) -> None:
    x, y, _, _ = A
    drawing.append(draw.Ellipse(x + 278, y + 294, 205, 31, fill="#18283d", opacity=0.12))
    clamp_x, clamp_y = x + 84, y + 122
    drawing.append(
        draw.Rectangle(
            clamp_x,
            clamp_y,
            94,
            74,
            rx=5,
            ry=5,
            fill="url(#metalSheen)",
            stroke="#596575",
            stroke_width=1.2,
            filter="url(#tightShadow)",
        )
    )
    drawing.append(draw.Rectangle(clamp_x + 6, clamp_y + 7, 82, 60, fill="url(#brushedMetal)", opacity=0.72))
    drawing.append(draw.Rectangle(clamp_x + 86, clamp_y + 22, 34, 30, fill="#7b8796", stroke="#4a5565"))

    beam = draw.Path(fill="none", stroke="url(#polymerGloss)", stroke_width=42, stroke_linecap="round")
    beam.M(x + 190, y + 156)
    beam.C(x + 265, y + 180, x + 334, y + 246, x + 434, y + 306)
    drawing.append(beam)

    grain = draw.Path(fill="none", stroke="url(#polymerGrain)", stroke_width=36, stroke_linecap="round", opacity=0.55)
    grain.M(x + 190, y + 156)
    grain.C(x + 265, y + 180, x + 334, y + 246, x + 434, y + 306)
    drawing.append(grain)

    highlight = draw.Path(fill="none", stroke="#fff4c8", stroke_width=7, stroke_linecap="round", opacity=0.72)
    highlight.M(x + 198, y + 144)
    highlight.C(x + 276, y + 171, x + 344, y + 230, x + 426, y + 282)
    drawing.append(highlight)

    edge = draw.Path(fill="none", stroke="#6f4d12", stroke_width=2.0, stroke_linecap="round", opacity=0.55)
    edge.M(x + 188, y + 179)
    edge.C(x + 262, y + 204, x + 327, y + 267, x + 425, y + 327)
    drawing.append(edge)

    for cx, cy, scale in [(x + 272, y + 196, 1.0), (x + 336, y + 238, 0.82), (x + 393, y + 278, 0.68)]:
        drawing.append(draw.Circle(cx, cy, 24 * scale, fill="url(#trapGlow)", opacity=0.95))
        drawing.append(draw.Circle(cx, cy, 5.6 * scale, fill=h.RED_MID, stroke="#7c0909", stroke_width=0.8))
        drawing.append(draw.Line(cx - 2.7 * scale, cy, cx + 2.7 * scale, cy, stroke="#ffffff", stroke_width=1.6))

    h.arrow(drawing, x + 410, y + 128, x + 356, y + 208, h.BLUE_MID, width=2.2, head_length=13, head_width=11)
    h.multiline_text(
        drawing,
        ["gradient stroke", "+ grain pattern", "+ trap glow"],
        x + 376,
        y + 90,
        15,
        20,
        fill=h.BLUE,
        anchor="middle",
    )
    h.rounded_rect(drawing, x + 64, y + 340, 416, 50, fill="#fff9e8", stroke="#ead9a8", radius=6)
    h.text(drawing, "Single semantic beam, layered with SVG-native styling", x + 84, y + 371, 16, fill="#50360b")


def add_isometric_device(drawing: draw.Drawing) -> None:
    x, y, _, _ = B
    base_x, base_y = x + 108, y + 250
    h.iso_box(
        drawing,
        base_x,
        base_y + 80,
        300,
        78,
        44,
        top_fill="#dce4ee",
        left_fill="#aab6c5",
        right_fill="#8794a6",
        stroke="#546173",
        opacity=1,
    )
    h.iso_box(
        drawing,
        base_x + 34,
        base_y + 34,
        260,
        70,
        42,
        top_fill="url(#polymerGloss)",
        left_fill="#a87419",
        right_fill="#7c5818",
        stroke="#6d501a",
    )
    h.iso_box(
        drawing,
        base_x + 68,
        base_y - 12,
        220,
        60,
        28,
        top_fill="url(#metalSheen)",
        left_fill="#7f8b99",
        right_fill="#636e7c",
        stroke="#46505e",
    )

    trap_points = [
        (base_x + 152, base_y + 40, 12, h.RED_MID, 0.75),
        (base_x + 210, base_y + 18, 8, h.RED_MID, 0.55),
        (base_x + 275, base_y + 44, 10, h.RED_MID, 0.62),
        (base_x + 238, base_y + 82, 6, h.BLUE_MID, 0.5),
        (base_x + 330, base_y + 64, 7, h.BLUE_MID, 0.48),
    ]
    for cx, cy, r, color, opacity in trap_points:
        drawing.append(draw.Circle(cx, cy, r * 2.5, fill="url(#trapGlow)" if color == h.RED_MID else "url(#blueHalo)"))
        drawing.append(draw.Circle(cx, cy, r, fill=color, opacity=opacity, stroke="#ffffff", stroke_width=0.7))

    h.arrow(drawing, x + 132, y + 120, x + 194, y + 188, h.RED_MID, width=3, head_length=15, head_width=12)
    h.arrow(drawing, x + 468, y + 143, x + 408, y + 223, h.BLUE_MID, width=3, head_length=15, head_width=12)
    drawing.append(math_svg(r"V(t)", x=x + 92, y=y + 86, width=48, prefix="iso_voltage", color=h.RED_MID))
    drawing.append(math_svg(r"\rho_t(x,z)", x=x + 390, y=y + 100, width=82, prefix="iso_rho", color=h.BLUE))
    h.rounded_rect(drawing, x + 78, y + 350, 394, 44, fill="#f7fbff", stroke="#d5e3f2", radius=6)
    h.text(drawing, "Depth is encoded by shaded faces, not bitmap rendering", x + 98, y + 378, 15, fill=h.BLUE)


def add_energy_surface(drawing: draw.Drawing) -> None:
    x, y, _, _ = C
    surface = draw.Path(fill="url(#energyRamp)", stroke="#51606f", stroke_width=1.1, filter="url(#tightShadow)")
    surface.M(x + 52, y + 194)
    surface.L(x + 300, y + 92)
    surface.L(x + 504, y + 230)
    surface.L(x + 256, y + 332)
    surface.Z()
    drawing.append(surface)

    drawing.append(
        draw.Rectangle(
            x + 10,
            y + 52,
            510,
            330,
            fill="url(#trapDots)",
            opacity=0.74,
            clip_path="url(#surfaceClip)",
            mask="url(#surfaceFadeMask)",
        )
    )
    for offset, opacity in [(0, 0.9), (34, 0.74), (68, 0.58), (102, 0.42)]:
        path = draw.Path(fill="none", stroke="#ffffff", stroke_width=1.6, opacity=opacity, clip_path="url(#surfaceClip)")
        path.M(x + 102 + offset, y + 211 - offset * 0.18)
        path.C(x + 192 + offset, y + 170 - offset * 0.2, x + 284 + offset, y + 174, x + 424 + offset * 0.55, y + 242)
        drawing.append(path)

    h.arrow(drawing, x + 96, y + 348, x + 472, y + 348, "#111111", width=1.5, head_length=11, head_width=9)
    h.arrow(drawing, x + 96, y + 348, x + 96, y + 104, "#111111", width=1.5, head_length=11, head_width=9)
    h.text(drawing, "position", x + 286, y + 378, 14, anchor="middle")
    h.text(drawing, "energy", x + 64, y + 216, 14, anchor="middle")
    drawing.append(math_svg(r"\Delta E_t", x=x + 304, y=y + 320, width=70, prefix="surface_delta", color="#111111"))
    h.multiline_text(
        drawing,
        ["masked texture falloff", "inside clipped energy plane"],
        x + 376,
        y + 98,
        15,
        19,
        fill=h.BLUE,
        anchor="middle",
    )


def add_plot_schematic_fusion(drawing: draw.Drawing) -> None:
    x, y, _, _ = D
    drawing.append(h.nested_svg(_matplotlib_decay_svg(), x + 42, y + 105, 395, 255, prefix="decay_plot"))

    band = draw.Path(fill="none", stroke=h.AMBER, stroke_width=18, stroke_linecap="round", opacity=0.52, clip_path="url(#plotClip)")
    band.M(x + 64, y + 282)
    band.C(x + 150, y + 210, x + 230, y + 192, x + 418, y + 148)
    drawing.append(band)

    drawing.append(draw.Rectangle(x + 384, y + 116, 82, 188, fill="url(#metalSheen)", stroke="#5b6674", stroke_width=1.0))
    drawing.append(draw.Rectangle(x + 390, y + 122, 18, 176, fill="#ffffff", opacity=0.48))
    for cy in [y + 156, y + 198, y + 242]:
        drawing.append(draw.Circle(x + 356, cy, 20, fill="url(#trapGlow)"))
        drawing.append(draw.Circle(x + 356, cy, 6, fill=h.RED_MID, stroke="#ffffff", stroke_width=0.8))
        h.arrow(drawing, x + 370, cy, x + 414, cy - 8, h.RED_MID, width=1.8, head_length=10, head_width=8, opacity=0.78)

    h.rounded_rect(drawing, x + 64, y + 362, 424, 36, fill="#f7fbff", stroke="#d7e2f2", radius=6)
    drawing.append(math_svg(r"I(t)\propto t^{-n}", x=x + 88, y=y + 369, width=102, prefix="fusion_it", color=h.BLUE_MID))
    h.text(drawing, "co-rendered with device schematic", x + 208, y + 386, 14, fill=h.BLUE)


def add_texture_swatches(drawing: draw.Drawing) -> None:
    x, y, _, _ = E
    swatches = [
        ("polymer gloss", "url(#polymerGloss)", "url(#polymerGrain)"),
        ("brushed metal", "url(#metalSheen)", "url(#brushedMetal)"),
        ("trap density", "#fff3f0", "url(#trapDots)"),
        ("field ramp", "url(#energyRamp)", None),
    ]
    for index, (label, fill, overlay) in enumerate(swatches):
        sx = x + 64 + (index % 2) * 220
        sy = y + 102 + (index // 2) * 122
        drawing.append(draw.Rectangle(sx, sy, 164, 62, rx=6, ry=6, fill=fill, stroke="#56606d", stroke_width=1.0))
        if overlay:
            drawing.append(draw.Rectangle(sx + 3, sy + 3, 158, 56, rx=5, ry=5, fill=overlay, opacity=0.68))
        h.text(drawing, label, sx, sy + 88, 14, fill=h.INK)

    drawing.append(draw.Rectangle(x + 66, y + 320, 374, 48, rx=6, ry=6, fill="#ffffff", stroke="#cfd7e1"))
    for i, yy in enumerate(range(int(y + 328), int(y + 362), 8)):
        drawing.append(draw.Line(x + 78, yy, x + 424, yy, stroke=[h.BLUE_MID, h.RED_MID, h.GREEN, h.AMBER][i % 4], stroke_width=1.1))
    h.text(drawing, "all texture remains vector-addressable", x + 96, y + 398, 15, fill=h.BLUE)


def add_print_readiness(drawing: draw.Drawing) -> None:
    x, y, _, _ = F
    h.multiline_text(
        drawing,
        ["The risk is not whether Python can draw it.", "The risk is style discipline and layout automation."],
        x + 58,
        y + 92,
        17,
        23,
        fill=h.INK,
    )

    colors = [h.BLUE_MID, h.RED_MID, h.GREEN, h.AMBER, "#6f7780"]
    labels = ["blue", "red", "green", "amber", "gray"]
    for index, color in enumerate(colors):
        cx = x + 84 + index * 76
        drawing.append(draw.Circle(cx, y + 184, 18, fill=color, stroke="#ffffff", stroke_width=1.4, filter="url(#tightShadow)"))
        h.text(drawing, labels[index], cx, y + 222, 12, fill=h.INK, anchor="middle")

    for index, stroke_width in enumerate([0.6, 0.9, 1.2, 1.8, 2.6, 4.0]):
        yy = y + 266 + index * 18
        drawing.append(draw.Line(x + 70, yy, x + 274, yy, stroke="#111111", stroke_width=stroke_width))
        h.text(drawing, f"{stroke_width:.1f}px", x + 292, yy + 4, 12, fill=h.GRAY)

    h.rounded_rect(drawing, x + 362, y + 252, 96, 96, fill="#ffffff", stroke="#c9d2dd", radius=6)
    for i in range(7):
        shade = 248 - i * 24
        drawing.append(draw.Rectangle(x + 366 + i * 12, y + 256, 12, 88, fill=f"rgb({shade},{shade},{shade})"))
    h.text(drawing, "gray ramp", x + 410, y + 370, 12, fill=h.GRAY, anchor="middle")
    h.rounded_rect(drawing, x + 62, y + 382, 418, 30, fill="#fff4f2", stroke="#f0ccc7", radius=6)
    h.text(drawing, "Conclusion depends on visual audit, not only XML validity", x + 82, y + 403, 14, fill=h.RED)


def _matplotlib_decay_svg() -> str:
    t = np.logspace(-3, 2, 180)
    shallow = 1.6e-2 * t ** -0.38
    deep = 2.2e-2 * t ** -0.22
    fig, ax = plt.subplots(figsize=(3.9, 2.35))
    fig.patch.set_alpha(0)
    ax.loglog(t, shallow, color=h.BLUE_MID, lw=1.8, label="shallow")
    ax.loglog(t, deep, color=h.RED_MID, lw=1.8, label="deep")
    ax.fill_between(t, deep, shallow, where=shallow > deep, color=h.BLUE_LIGHT, alpha=0.35)
    ax.set_xlabel("time (s)", fontsize=7)
    ax.set_ylabel("current (a.u.)", fontsize=7)
    ax.tick_params(axis="both", labelsize=6, length=2.5, width=0.6)
    ax.grid(True, which="major", color="#d7dce3", lw=0.45)
    ax.grid(True, which="minor", color="#edf0f4", lw=0.3)
    ax.legend(frameon=False, fontsize=6, loc="lower left")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_linewidth(0.7)
    ax.spines["left"].set_linewidth(0.7)
    fig.tight_layout(pad=0.45)
    buffer = io.StringIO()
    fig.savefig(buffer, format="svg", transparent=True, metadata={"Date": None})
    plt.close(fig)
    return buffer.getvalue()


def main() -> None:
    h.save_svg(build_figure(), OUT)


if __name__ == "__main__":
    main()
