#!/usr/bin/env python3
"""Draw a Python/matplotlib ISPD apparatus figure."""

from __future__ import annotations

from pathlib import Path as FilePath

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patheffects
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, PathPatch, Polygon, Rectangle
from matplotlib.path import Path as MplPath

OUT_DIR = FilePath(__file__).resolve().parent
W, H = 1200, 900


def rgb(hex_color: str) -> tuple[float, float, float]:
    return mcolors.to_rgb(hex_color)


def gradient_fill(
    ax: plt.Axes,
    patch,
    color_a: str,
    color_b: str,
    *,
    direction: str = "vertical",
    zorder: float = 1,
    alpha: float = 1.0,
) -> None:
    """Fill a patch with a clipped two-color gradient."""
    verts = patch.get_path().vertices
    trans = patch.get_patch_transform()
    if trans is not None:
        verts = trans.transform(verts)
    xmin, ymin = verts.min(axis=0)
    xmax, ymax = verts.max(axis=0)

    n = 256
    c0 = np.array(rgb(color_a))
    c1 = np.array(rgb(color_b))
    ramp = np.linspace(0, 1, n)
    colors = c0 * (1 - ramp[:, None]) + c1 * ramp[:, None]
    if direction == "horizontal":
        img = np.tile(colors[None, :, :], (4, 1, 1))
    else:
        img = np.tile(colors[:, None, :], (1, 4, 1))
    im = ax.imshow(img, extent=(xmin, xmax, ymax, ymin), origin="upper", zorder=zorder, alpha=alpha)
    ax.add_patch(patch)
    im.set_clip_path(patch)


def stroke_patch(patch, *, shadow: bool = False):
    if shadow:
        patch.set_path_effects(
            [
                patheffects.SimplePatchShadow(offset=(7, -7), alpha=0.14, rho=0.96),
                patheffects.Normal(),
            ]
        )
    return patch


def add_poly(ax: plt.Axes, pts, fill, edge, lw=2.5, z=1, shadow=False, alpha=1.0):
    patch = Polygon(
        pts,
        closed=True,
        facecolor=fill,
        edgecolor=edge,
        lw=lw,
        joinstyle="round",
        alpha=alpha,
        zorder=z,
    )
    ax.add_patch(stroke_patch(patch, shadow=shadow))
    return patch


def add_gradient_poly(
    ax: plt.Axes, pts, c0, c1, edge, lw=2.5, z=1, direction="vertical", shadow=False
):
    patch = Polygon(
        pts, closed=True, facecolor="none", edgecolor=edge, lw=lw, joinstyle="round", zorder=z
    )
    gradient_fill(ax, patch, c0, c1, direction=direction, zorder=z)
    patch.set_facecolor("none")
    if shadow:
        patch.set_path_effects(
            [
                patheffects.SimplePatchShadow(offset=(7, -7), alpha=0.14, rho=0.96),
                patheffects.Normal(),
            ]
        )
    return patch


def add_text(ax: plt.Axes, x: float, y: float, text: str, **kwargs) -> None:
    defaults = dict(fontfamily="DejaVu Sans", fontsize=16, color="#3E454D", zorder=20)
    defaults.update(kwargs)
    ax.text(x, y, text, **defaults)


def draw_sample_stack(ax: plt.Axes) -> None:
    # Polymer film
    add_gradient_poly(
        ax,
        [(175, 610), (715, 610), (755, 635), (215, 635)],
        "#E3C47A",
        "#C8A055",
        "#8B6827",
        lw=2.6,
        z=7,
        shadow=True,
    )
    ax.plot(
        [188, 707, 739],
        [614, 614, 633],
        color="#F4D98A",
        lw=1.9,
        solid_capstyle="round",
        alpha=0.82,
        zorder=9,
    )
    add_gradient_poly(
        ax,
        [(215, 635), (755, 635), (755, 674), (215, 674)],
        "#B68A3A",
        "#805E24",
        "#7D5D23",
        lw=2.6,
        z=6,
    )
    add_poly(
        ax, [(175, 610), (215, 635), (215, 674), (175, 649)], "#A17831", "#7D5D23", lw=2.6, z=6
    )

    # Silicon substrate
    add_gradient_poly(
        ax,
        [(160, 674), (790, 674), (842, 708), (212, 708)],
        "#4B535E",
        "#303640",
        "#20252C",
        lw=3.0,
        z=4,
        shadow=True,
    )
    ax.plot(
        [176, 781, 823],
        [679, 679, 706],
        color="#65707D",
        lw=1.8,
        solid_capstyle="round",
        alpha=0.66,
        zorder=8,
    )
    front_face = add_gradient_poly(
        ax,
        [(212, 708), (842, 708), (842, 826), (212, 826)],
        "#343A43",
        "#242932",
        "#20252C",
        lw=3.0,
        z=3,
    )
    for x in np.arange(238, 845, 22):
        (line,) = ax.plot(
            [x - 45, x + 28], [826, 708], color="#6C7683", lw=0.75, alpha=0.22, zorder=5
        )
        line.set_clip_path(front_face)
    add_poly(
        ax, [(160, 674), (212, 708), (212, 826), (160, 792)], "#303640", "#20252C", lw=3.0, z=3
    )
    ax.plot([160, 790, 842, 212, 160], [674, 674, 708, 708, 674], color="#252B34", lw=3.0, zorder=9)


def draw_hv_and_corona(ax: plt.Axes) -> None:
    hv = FancyBboxPatch(
        (160, 80),
        98,
        54,
        boxstyle="round,pad=0,rounding_size=2",
        facecolor="#F7F8F9",
        edgecolor="#8C9298",
        lw=1.9,
        zorder=12,
    )
    ax.add_patch(hv)
    add_text(
        ax,
        209,
        115,
        "HV+",
        fontsize=15,
        fontweight="bold",
        color="#2D3339",
        ha="center",
        va="center",
        zorder=20,
    )
    ax.plot([209, 209], [134, 256], color="#8C9298", lw=2.0, solid_capstyle="round", zorder=11)

    needle = PathPatch(
        MplPath([(197, 256), (221, 256), (215, 486), (209, 524), (203, 486), (197, 256)]),
        facecolor="none",
        edgecolor="#5F6870",
        lw=2.4,
        joinstyle="round",
        zorder=12,
    )
    gradient_fill(ax, needle, "#F4F5F5", "#69727B", direction="horizontal", zorder=11)
    ax.add_patch(
        Ellipse((209, 256), 26, 10, facecolor="#D8DCDD", edgecolor="#778087", lw=1.6, zorder=13)
    )
    for x0, y0, x1, y1 in [
        (190, 523, 169, 554),
        (204, 533, 197, 566),
        (215, 533, 229, 563),
        (228, 521, 253, 547),
    ]:
        ax.plot([x0, x1], [y0, y1], color="#D84436", lw=3.1, solid_capstyle="round", zorder=14)
    for x, y, r, a in [(182, 570, 2.6, 0.72), (219, 576, 2.3, 0.62), (244, 565, 2.1, 0.54)]:
        ax.add_patch(Circle((x, y), r, facecolor="#D84436", edgecolor="none", alpha=a, zorder=14))


def draw_charges(ax: plt.Axes) -> None:
    for x in [222, 294, 366, 438, 510]:
        add_text(
            ax,
            x,
            598,
            "+",
            fontsize=20,
            fontweight="bold",
            color="#D4483A",
            ha="center",
            va="center",
            zorder=18,
        )


def draw_probe(ax: plt.Axes) -> None:
    shaft = PathPatch(
        MplPath(
            [
                (652, 168),
                (660, 166),
                (674, 166),
                (682, 168),
                (682, 496),
                (674, 501),
                (660, 501),
                (652, 496),
                (652, 168),
            ]
        ),
        facecolor="none",
        edgecolor="#6D767E",
        lw=2.4,
        zorder=13,
    )
    gradient_fill(ax, shaft, "#F7F8F8", "#858E96", direction="horizontal", zorder=12)
    ax.add_patch(
        Ellipse((667, 168), 30, 11, facecolor="#D8DDDF", edgecolor="#7B858D", lw=1.6, zorder=14)
    )
    ax.add_patch(
        Rectangle((655, 475), 24, 28, facecolor="#AEB6BC", edgecolor="#737D85", lw=1.6, zorder=13)
    )
    ax.add_patch(
        Ellipse((667, 500), 108, 32, facecolor="#D4B355", edgecolor="#8D6D1D", lw=2.4, zorder=15)
    )
    ax.add_patch(
        Ellipse((667, 495), 84, 17, facecolor="#E8CA66", edgecolor="none", alpha=0.75, zorder=16)
    )
    add_poly(
        ax,
        [(614, 501), (720, 501), (716, 515), (703, 526), (631, 526), (618, 515)],
        "#B69034",
        "#8D6D1D",
        lw=1.7,
        z=14,
        alpha=0.76,
    )
    ax.add_patch(
        Ellipse(
            (667, 500),
            108,
            32,
            facecolor="none",
            edgecolor="#F1DE94",
            lw=1.0,
            alpha=0.78,
            zorder=17,
        )
    )
    add_text(ax, 600, 176, "Probe", fontsize=14, fontstyle="italic", color="#3E454D", zorder=20)

    ax.annotate(
        "",
        xy=(626, 246),
        xytext=(626, 326),
        arrowprops=dict(arrowstyle="<|-|>", color="#6B727A", lw=1.6, mutation_scale=17),
        zorder=17,
    )
    ax.plot(
        [607, 621, 636, 651],
        [288, 279, 279, 288],
        color="#A0A6AC",
        lw=1.1,
        solid_capstyle="round",
        zorder=16,
    )
    ax.plot(
        [607, 621, 636, 651],
        [303, 312, 312, 303],
        color="#A0A6AC",
        lw=1.1,
        solid_capstyle="round",
        zorder=16,
    )


def draw_gap_and_ground(ax: plt.Axes) -> None:
    ax.annotate(
        "",
        xy=(746, 532),
        xytext=(746, 608),
        arrowprops=dict(
            arrowstyle="<|-|>", color="#8A9198", lw=1.5, linestyle=(0, (4, 4)), mutation_scale=15
        ),
        zorder=17,
    )
    ax.plot([690, 756], [532, 532], color="#AAB0B5", lw=1.4, linestyle=(0, (3, 4)), zorder=16)
    ax.plot([690, 756], [608, 608], color="#AAB0B5", lw=1.4, linestyle=(0, (3, 4)), zorder=16)
    add_text(ax, 758, 579, "d", fontsize=12, fontstyle="italic", color="#4A4F55", zorder=20)

    ax.plot(
        [842, 898, 898], [753, 753, 777], color="#444B53", lw=2.0, solid_capstyle="round", zorder=18
    )
    for y, x0, x1 in [(777, 876, 920), (790, 883, 913), (803, 891, 905)]:
        ax.plot([x0, x1], [y, y], color="#444B53", lw=2.2, solid_capstyle="round", zorder=18)


def draw_meter_and_cable(ax: plt.Axes) -> None:
    add_poly(
        ax, [(900, 300), (1078, 300), (1116, 329), (938, 329)], "#E7DCC7", "#8E8371", lw=2.1, z=10
    )
    add_gradient_poly(
        ax,
        [(938, 329), (1116, 329), (1116, 548), (938, 548)],
        "#C8B89A",
        "#A18E70",
        "#8E8371",
        lw=2.2,
        z=9,
    )
    body = FancyBboxPatch(
        (900, 300),
        178,
        222,
        boxstyle="round,pad=0,rounding_size=7",
        facecolor="#E6D7B9",
        edgecolor="#8E8371",
        lw=2.4,
        zorder=11,
    )
    body.set_path_effects(
        [
            patheffects.SimplePatchShadow(offset=(6, -6), alpha=0.09, rho=0.98),
            patheffects.Normal(),
        ]
    )
    ax.add_patch(body)
    ax.plot([914, 1064], [314, 314], color="#F7E9C8", lw=2.0, alpha=0.55, zorder=12)
    ax.add_patch(
        Circle((912, 330), 5.0, facecolor="#6F7A82", edgecolor="#4F5960", lw=1.2, zorder=18)
    )

    screen = FancyBboxPatch(
        (927, 337),
        128,
        62,
        boxstyle="round,pad=0,rounding_size=5",
        facecolor="#F8FAF8",
        edgecolor="#9A9D9A",
        lw=1.6,
        zorder=12,
    )
    ax.add_patch(screen)
    decay = MplPath(
        [(941, 350), (956, 371), (977, 386), (1042, 386)],
        [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4],
    )
    ax.add_patch(
        PathPatch(decay, facecolor="none", edgecolor="#517D8D", lw=2.4, capstyle="round", zorder=14)
    )
    ax.plot([939, 1044], [381, 381], color="#C4C8C8", lw=1.0, zorder=13)
    ax.plot([939, 939], [346, 383], color="#C4C8C8", lw=1.0, zorder=13)
    add_text(
        ax,
        989,
        450,
        r"V$_s$ meter",
        fontsize=14,
        fontweight="semibold",
        color="#3D3D39",
        ha="center",
        va="center",
        zorder=20,
    )
    ax.add_patch(
        Circle((940, 494), 8.2, facecolor="#7C8B94", edgecolor="#59646B", lw=1.4, zorder=14)
    )
    ax.add_patch(
        Circle((974, 494), 8.2, facecolor="#D2B35A", edgecolor="#8A6E22", lw=1.4, zorder=14)
    )
    ax.plot([920, 1060], [512, 512], color="#AFA18A", lw=1.4, zorder=14)

    ax.add_patch(
        Circle((682, 232), 4.6, facecolor="#78828A", edgecolor="#59636B", lw=1.2, zorder=19)
    )
    ax.add_patch(
        Circle((912, 330), 4.6, facecolor="#78828A", edgecolor="#59636B", lw=1.2, zorder=19)
    )
    cable = MplPath(
        [(686, 232), (778, 198), (858, 222), (912, 330)],
        [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4],
    )
    ax.add_patch(
        PathPatch(cable, facecolor="none", edgecolor="#6B737A", lw=2.8, capstyle="round", zorder=18)
    )
    ax.add_patch(
        PathPatch(
            cable,
            facecolor="none",
            edgecolor="#EEF0F1",
            lw=0.9,
            capstyle="round",
            alpha=0.75,
            zorder=19,
        )
    )


def draw_labels(ax: plt.Axes) -> None:
    ax.plot([300, 350], [838, 838], color="#C8A055", lw=3.3, solid_capstyle="round", zorder=20)
    add_text(
        ax,
        458,
        850,
        "polymer film",
        fontsize=14,
        fontstyle="italic",
        color="#8B6827",
        ha="center",
        va="center",
        zorder=20,
    )


def draw() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])

    draw_sample_stack(ax)
    draw_charges(ax)
    draw_hv_and_corona(ax)
    draw_probe(ax)
    draw_gap_and_ground(ax)
    draw_meter_and_cable(ax)
    draw_labels(ax)
    return fig


def main() -> None:
    fig = draw()
    png_path = OUT_DIR / "ispd_measurement_setup_python.png"
    svg_path = OUT_DIR / "ispd_measurement_setup_python.svg"
    fig.savefig(png_path, dpi=160, facecolor="white", pad_inches=0)
    fig.savefig(svg_path, facecolor="white", pad_inches=0)
    plt.close(fig)
    print(png_path)
    print(svg_path)


if __name__ == "__main__":
    main()
