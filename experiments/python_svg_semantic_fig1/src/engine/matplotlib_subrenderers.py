from __future__ import annotations

import io
import re
from dataclasses import dataclass

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from engine.domain_primitives import PowerLawDecayPlot
from engine.svg_fragments import SvgFragment, prefix_svg_ids, strip_outer_svg


_VIEWBOX_RE = re.compile(r"""viewBox=["']([^"']+)["']""")


@dataclass(frozen=True)
class MatplotlibPlotStyle:
    font_size: float
    tick_label_size: float
    line_width: float
    axis_width: float
    tick_width: float
    tick_length: float
    grid_line_width: float
    grid_alpha: float
    show_numeric_tick_labels: bool
    show_grid: bool
    axis_color: str
    grid_color: str
    annotation_color: str
    label_pad: float
    decay_label_x: float
    decay_label_y: float
    decay_slope_label: str
    decay_slope_x: float
    decay_slope_y: float
    show_decay_markers: bool
    decay_marker_size: float


def fig1_electrical_style() -> MatplotlibPlotStyle:
    return MatplotlibPlotStyle(
        font_size=6.8,
        tick_label_size=5.6,
        line_width=1.65,
        axis_width=0.72,
        tick_width=0.55,
        tick_length=2.1,
        grid_line_width=0.28,
        grid_alpha=0.24,
        show_numeric_tick_labels=False,
        show_grid=True,
        axis_color="#1f2933",
        grid_color="#d7dde6",
        annotation_color="#5b6470",
        label_pad=0.8,
        decay_label_x=0.56,
        decay_label_y=0.68,
        decay_slope_label="slope -n",
        decay_slope_x=0.62,
        decay_slope_y=0.44,
        show_decay_markers=True,
        decay_marker_size=8.0,
    )


def _default_plot_style() -> MatplotlibPlotStyle:
    return MatplotlibPlotStyle(
        font_size=7.0,
        tick_label_size=6.0,
        line_width=1.8,
        axis_width=0.7,
        tick_width=0.6,
        tick_length=2.4,
        grid_line_width=0.35,
        grid_alpha=0.55,
        show_numeric_tick_labels=True,
        show_grid=True,
        axis_color="#5b6470",
        grid_color="#d7dde6",
        annotation_color="#5b6470",
        label_pad=1.0,
        decay_label_x=0.56,
        decay_label_y=0.68,
        decay_slope_label="slope -n",
        decay_slope_x=0.62,
        decay_slope_y=0.44,
        show_decay_markers=False,
        decay_marker_size=6.0,
    )


def power_law_decay_fragment(
    payload: PowerLawDecayPlot,
    *,
    width: float,
    height: float,
    style: MatplotlibPlotStyle | None = None,
) -> SvgFragment:
    plot_style = style or _default_plot_style()
    with mpl.rc_context(_rc_params(plot_style)):
        fig, ax = plt.subplots(figsize=(width / 100, height / 100), dpi=100)
        log_t = np.linspace(
            payload.log_t_min, payload.log_t_max, max(2, payload.samples)
        )
        log_i_start = payload.log_i_top - 0.34
        log_i = np.clip(
            log_i_start + payload.slope * (log_t - payload.log_t_min),
            payload.log_i_bottom,
            payload.log_i_top,
        )
        ax.plot(log_t, log_i, color=payload.color, lw=plot_style.line_width)
        if plot_style.show_decay_markers:
            marker_indices = np.linspace(5, len(log_t) - 6, 4, dtype=int)
            ax.scatter(
                log_t[marker_indices],
                log_i[marker_indices],
                s=plot_style.decay_marker_size,
                facecolor="#ffffff",
                edgecolor=payload.color,
                linewidth=0.45,
                zorder=4,
            )
        ax.set_xlabel("log t", labelpad=plot_style.label_pad)
        ax.set_ylabel("log I", labelpad=plot_style.label_pad, rotation=0)
        ax.yaxis.set_label_coords(-0.14, 0.92)
        ax.text(
            plot_style.decay_label_x,
            plot_style.decay_label_y,
            payload.label,
            transform=ax.transAxes,
            color=payload.color,
            fontsize=plot_style.font_size,
        )
        ax.text(
            plot_style.decay_slope_x,
            plot_style.decay_slope_y,
            plot_style.decay_slope_label,
            transform=ax.transAxes,
            color=plot_style.annotation_color,
            fontsize=plot_style.font_size - 0.5,
        )
        _style_small_axes(ax, plot_style)
        return _fragment_from_figure(
            fig,
            width=width,
            height=height,
            role="electrical-decay-plot",
            prefix="fig1_decay",
        )


def _rc_params(style: MatplotlibPlotStyle) -> dict[str, object]:
    return {
        "svg.fonttype": "none",
        "svg.hashsalt": "fig1-v27-library-subrenderers",
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": style.font_size,
        "axes.linewidth": style.axis_width,
        "xtick.major.width": style.tick_width,
        "ytick.major.width": style.tick_width,
        "xtick.major.size": style.tick_length,
        "ytick.major.size": style.tick_length,
    }


def _style_small_axes(ax: plt.Axes, style: MatplotlibPlotStyle) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(style.axis_color)
    ax.spines["bottom"].set_color(style.axis_color)
    ax.tick_params(labelsize=style.tick_label_size, pad=1, colors=style.axis_color)
    if not style.show_numeric_tick_labels:
        ax.tick_params(labelbottom=False, labelleft=False)
    ax.grid(
        style.show_grid,
        color=style.grid_color,
        lw=style.grid_line_width,
        alpha=style.grid_alpha,
    )
    ax.margins(x=0.04, y=0.08)


def _fragment_from_figure(
    fig: plt.Figure, *, width: float, height: float, role: str, prefix: str
) -> SvgFragment:
    buffer = io.StringIO()
    fig.savefig(
        buffer,
        format="svg",
        bbox_inches="tight",
        pad_inches=0.015,
        metadata={"Date": None},
    )
    plt.close(fig)
    svg = buffer.getvalue()
    view_box = _view_box(svg)
    inner = prefix_svg_ids(strip_outer_svg(svg), prefix)
    return SvgFragment(
        inner_svg=inner,
        view_box=view_box,
        width=width,
        height=height,
        subrenderer="matplotlib",
        role=role,
    )


def _view_box(svg_text: str) -> str:
    match = _VIEWBOX_RE.search(svg_text)
    if not match:
        raise RuntimeError("Matplotlib SVG did not include viewBox")
    return match.group(1)
