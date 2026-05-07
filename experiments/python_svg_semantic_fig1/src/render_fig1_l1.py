from __future__ import annotations

import shutil
import subprocess
import math
from dataclasses import replace
from pathlib import Path
from typing import Callable

import drawsvg as draw

from engine.scientific_plots import (
    PlotLabel,
    PlotTick,
    ScientificPlotPlan,
)
from engine.domain_primitives import (
    BandDiagram,
    DOSLobes,
    DeepTrapHero,
    Electrode,
    EvidenceTrio,
    ForceArrow,
    ISPDPlot,
    LayoutFlow,
    MacroscopicProbe,
    MaxwellAttractionCue,
    PEHysteresisPlot,
    PolymerCantilever,
    PowerLawDecayPlot,
    SulfurPolymerOrigin,
    TrapLevelSet,
    TrapModelFlow,
)
from engine.matplotlib_subrenderers import (
    fig1_electrical_style,
    pe_hysteresis_fragment,
    power_law_decay_fragment,
)
from engine.scene import Point, Rect, Scene, SemanticObject
from engine.style import DEFAULT_STYLE, FigureStyle
from engine.svg_fragments import wrapped_fragment_svg
from engine import primitives as p
from fig1_l1_scene import build_scene


ROOT = Path(__file__).resolve().parents[1]
SVG_OUT = ROOT / "fig1_reference_semantic.svg"
PNG_OUT = ROOT / "fig1_reference_semantic.png"
COMPARISON_OUT = ROOT / "reference_vs_fig1_reference_semantic.png"
REFERENCE_PNG = ROOT / "reference" / "source_variant_vectorization_ref_v1.png"

Renderer = Callable[[draw.Drawing, Scene, SemanticObject[object], FigureStyle], None]


def _panel_text(
    drawing: draw.Drawing,
    value: str,
    x: float,
    y: float,
    size: float,
    *,
    role: str,
    style: FigureStyle,
    fill: str | None = None,
    anchor: str = "start",
    weight: str | None = None,
    italic: bool = False,
    causal_role: str | None = None,
) -> None:
    attrs: dict[str, object] = {
        "fill": fill or style.palette.ink,
        "font_family": style.typography.family,
        "text_anchor": anchor,
        "data-panel-role": role,
    }
    if causal_role:
        attrs["data-causal-role"] = causal_role
    if weight:
        attrs["font_weight"] = weight
    if italic:
        attrs["font_style"] = "italic"
    drawing.append(draw.Text(value, size, x, y, **attrs))


def build_drawing(scene: Scene, style: FigureStyle = DEFAULT_STYLE) -> draw.Drawing:
    drawing = draw.Drawing(scene.width, scene.height)
    drawing.append(
        draw.Rectangle(0, 0, scene.width, scene.height, fill=style.palette.white)
    )
    drawing.append(p.style_defs())
    _draw_columns(drawing, scene, style)

    renderers: dict[str, Renderer] = {
        "LayoutFlow": _draw_layout_flow,
        "SulfurPolymerOrigin": _draw_sulfur_polymer_origin,
        "DeepTrapHero": _draw_deep_trap_hero,
        "BandDiagram": _draw_band_diagram,
        "TrapLevelSet": _draw_trap_level_set,
        "DOSLobes": _draw_dos_lobes,
        "EvidenceTrio": _draw_evidence_trio,
        "PEHysteresisPlot": _draw_pe_hysteresis,
        "PowerLawDecayPlot": _draw_power_law_decay,
        "ISPDPlot": _draw_ispd_plot,
        "TrapModelFlow": _draw_trap_model_flow,
        "MacroscopicProbe": _draw_macroscopic_probe,
        "PolymerCantilever": _draw_polymer_cantilever,
        "Electrode": _draw_electrode,
        "ForceArrow": _draw_force_arrow,
        "MaxwellAttractionCue": _draw_maxwell_attraction_cue,
    }
    for obj in scene.objects:
        renderers[obj.kind](drawing, scene, obj, style)
    _draw_panel_decorations(drawing, scene, style)
    return drawing


def _draw_panel_decorations(
    drawing: draw.Drawing, scene: Scene, style: FigureStyle
) -> None:
    column_by_id = {column.id: column for column in scene.layout.columns}
    if "localized_traps" in column_by_id:
        _draw_localized_traps_visual(drawing, column_by_id["localized_traps"], style)
    if "vs_decay_module" in column_by_id:
        _draw_vs_decay_curve(drawing, column_by_id["vs_decay_module"], style)
    if "release_module" in column_by_id:
        _draw_release_wells(drawing, column_by_id["release_module"], style)


def _draw_localized_traps_visual(
    drawing: draw.Drawing, column, style: FigureStyle
) -> None:
    palette = style.palette
    panel = column.bounds
    visual_x = panel.x + 32
    visual_right = panel.right - 22
    visual_top = panel.y + 100
    callout = column.box("hero_callout")
    visual_bottom = callout.y - 6

    network_top = visual_top + 90
    network_bottom = visual_bottom - 6
    e_axis_x = visual_x - 14
    e_axis_bottom = network_bottom - 10
    e_axis_top = network_top + 10
    p.arrow(
        drawing,
        Point(e_axis_x, e_axis_bottom),
        Point(e_axis_x, e_axis_top),
        palette.muted,
        width=1.0,
        head_length=8,
        head_width=6,
        opacity=0.55,
    )
    p.text(
        drawing,
        "E",
        e_axis_x,
        e_axis_top - 8,
        10.0,
        fill=palette.muted,
        italic=True,
        anchor="middle",
        style=style,
    )
    _draw_polymer_network_backdrop(
        drawing, visual_x, visual_right, network_top, network_bottom, palette, style
    )

    well_baseline_y = network_top + 4
    visual_width = visual_right - visual_x
    well_specs = (
        (visual_x + visual_width * 0.10, "shallow", palette.shallow_blue, 22),
        (visual_x + visual_width * 0.32, "shallow", palette.shallow_blue, 22),
        (visual_x + visual_width * 0.62, "deep", palette.deep_red, 62),
        (visual_x + visual_width * 0.86, "deep", palette.deep_red, 62),
    )
    for cx, _kind, color, depth in well_specs:
        _draw_trap_well(drawing, cx, well_baseline_y, depth, color, style)
    p.text(
        drawing,
        "shallow",
        visual_x + visual_width * 0.21,
        well_baseline_y - 12,
        9.5,
        fill=palette.shallow_blue,
        italic=True,
        anchor="middle",
        style=style,
    )
    p.text(
        drawing,
        "deep",
        visual_x + visual_width * 0.74,
        well_baseline_y - 12,
        9.5,
        fill=palette.deep_red,
        italic=True,
        anchor="middle",
        style=style,
    )

    trapped_specs = (
        (visual_x + visual_width * 0.10, network_top + 48, palette.shallow_blue),
        (visual_x + visual_width * 0.32, network_top + 54, palette.shallow_blue),
        (visual_x + visual_width * 0.62, network_top + 50, palette.deep_red),
        (visual_x + visual_width * 0.86, network_top + 52, palette.deep_red),
    )
    p.text(
        drawing,
        "polymer network",
        visual_x + visual_width * 0.5,
        network_bottom + 4,
        8.5,
        fill=palette.muted,
        italic=True,
        anchor="middle",
        style=style,
    )
    for x, y, color in trapped_specs:
        _draw_trapped_electron(drawing, x, y, color, style)


def _draw_polymer_network_backdrop(
    drawing: draw.Drawing,
    x_left: float,
    x_right: float,
    y_top: float,
    y_bottom: float,
    palette,
    style: FigureStyle,
) -> None:
    import numpy as np
    from matplotlib.tri import Triangulation

    rng = np.random.default_rng(2026)
    cols = 14
    rows = 6
    cell_w = (x_right - x_left) / cols
    cell_h = (y_bottom - y_top) / rows
    width = x_right - x_left
    height = y_bottom - y_top

    xs: list[float] = []
    ys: list[float] = []
    for row in range(rows):
        row_offset = -0.25 * cell_w if row % 2 else 0.25 * cell_w
        for col in range(cols):
            jitter_x = (rng.random() - 0.5) * cell_w * 0.50
            jitter_y = (rng.random() - 0.5) * cell_h * 0.45
            x = x_left + cell_w * (col + 0.5) + row_offset + jitter_x
            y = y_top + cell_h * (row + 0.5) + jitter_y
            if x < x_left + 2 or x > x_right - 2:
                continue
            xs.append(x)
            ys.append(y)
    xs_arr = np.asarray(xs)
    ys_arr = np.asarray(ys)

    s_rich_centers = (
        (x_left + width * 0.18, y_top + height * 0.32),
        (x_left + width * 0.78, y_top + height * 0.58),
    )
    s_radius = cell_w * 2.0
    is_sulfur: list[bool] = []
    for x, y in zip(xs, ys):
        d_rich = min(math.hypot(x - cx, y - cy) for cx, cy in s_rich_centers)
        is_sulfur.append(d_rich < s_radius)

    tri = Triangulation(xs_arr, ys_arr)
    edges_seen: set[tuple[int, int]] = set()
    max_edge = max(cell_w, cell_h) * 1.55
    for triangle in tri.triangles:
        for a, b in ((0, 1), (1, 2), (2, 0)):
            i, j = sorted((int(triangle[a]), int(triangle[b])))
            if (i, j) in edges_seen:
                continue
            length = math.hypot(xs_arr[j] - xs_arr[i], ys_arr[j] - ys_arr[i])
            if length > max_edge:
                continue
            edges_seen.add((i, j))
            drawing.append(
                draw.Line(
                    float(xs_arr[i]),
                    float(ys_arr[i]),
                    float(xs_arr[j]),
                    float(ys_arr[j]),
                    stroke=palette.sulfur_brown,
                    stroke_width=0.5,
                    opacity=0.30,
                )
            )

    for x, y, is_s in zip(xs, ys, is_sulfur):
        if is_s:
            drawing.append(
                draw.Circle(
                    x,
                    y,
                    4.0,
                    fill="#e0c884",
                    stroke=palette.sulfur_brown,
                    stroke_width=0.5,
                    opacity=0.70,
                )
            )
        else:
            drawing.append(
                draw.Circle(
                    x,
                    y,
                    2.4,
                    fill="#c1c4cb",
                    stroke="#7a8090",
                    stroke_width=0.5,
                    opacity=0.55,
                )
            )


def _draw_trap_well(
    drawing: draw.Drawing,
    cx: float,
    baseline_y: float,
    depth: float,
    color: str,
    style: FigureStyle,
) -> None:
    half_width = 26 + depth * 0.32
    bottom_y = baseline_y + depth
    well_path = draw.Path(fill="none", stroke=color, stroke_width=1.5, opacity=0.92)
    well_path.M(cx - half_width, baseline_y)
    well_path.Q(cx, bottom_y + 6, cx + half_width, baseline_y)
    drawing.append(well_path)

    el_y = bottom_y - 1
    drawing.append(
        draw.Circle(
            cx,
            el_y,
            5.6,
            fill=color,
            stroke="#ffffff",
            stroke_width=0.9,
            opacity=0.95,
        )
    )
    drawing.append(
        draw.Text(
            "−",
            10.5,
            cx,
            el_y + 3.6,
            fill="#ffffff",
            font_family=style.typography.family,
            text_anchor="middle",
            font_weight="700",
        )
    )

    arrow_path = draw.Path(
        fill="none",
        stroke=color,
        stroke_width=1.05,
        stroke_dasharray="4 3",
        opacity=0.82,
    )
    arrow_top_x = cx + 14
    arrow_top_y = baseline_y - 36
    arrow_path.M(cx + 2, el_y - 7)
    arrow_path.Q(cx + 6, baseline_y - 10, arrow_top_x, arrow_top_y)
    drawing.append(arrow_path)
    drawing.append(
        draw.Lines(
            arrow_top_x,
            arrow_top_y - 2,
            arrow_top_x - 4.2,
            arrow_top_y + 5.5,
            arrow_top_x + 4.2,
            arrow_top_y + 5.5,
            close=True,
            fill=color,
            opacity=0.82,
        )
    )


def _draw_trapped_electron(
    drawing: draw.Drawing,
    x: float,
    y: float,
    color: str,
    style: FigureStyle,
) -> None:
    drawing.append(
        draw.Circle(
            x,
            y,
            5.0,
            fill="none",
            stroke=color,
            stroke_width=0.8,
            stroke_dasharray="2 2",
            opacity=0.78,
        )
    )
    drawing.append(
        draw.Circle(
            x,
            y,
            4.4,
            fill=color,
            stroke="#ffffff",
            stroke_width=0.7,
            opacity=0.85,
        )
    )
    drawing.append(
        draw.Text(
            "−",
            8.4,
            x,
            y + 3.0,
            fill="#ffffff",
            font_family=style.typography.family,
            text_anchor="middle",
            font_weight="700",
        )
    )


def _draw_vs_decay_curve(drawing: draw.Drawing, column, style: FigureStyle) -> None:
    palette = style.palette
    plot_area = column.box("vs_plot_area")
    margin_x = 22
    margin_y = 24
    axis_origin = Point(plot_area.x + margin_x, plot_area.bottom - margin_y)
    axis_w = plot_area.width - margin_x - 12
    axis_h = plot_area.height - margin_y - 14
    p.mini_axis(drawing, axis_origin, axis_w, axis_h, palette.ink)
    samples = 48
    points = []
    for index in range(samples):
        fraction = index / (samples - 1)
        decay = math.exp(-fraction * 3.2)
        points.append(
            Point(axis_origin.x + fraction * axis_w, axis_origin.y - decay * axis_h)
        )
    drawing.append(
        p.polyline_path(
            tuple(points), fill="none", stroke=palette.ink, stroke_width=1.5
        )
    )
    for tick_fraction in (0.25, 0.5, 0.75):
        tx = axis_origin.x + tick_fraction * axis_w
        drawing.append(
            draw.Line(
                tx,
                axis_origin.y,
                tx,
                axis_origin.y + 4,
                stroke=palette.ink,
                stroke_width=0.5,
            )
        )
    for ty_fraction in (0.25, 0.5, 0.75):
        ty = axis_origin.y - ty_fraction * axis_h
        drawing.append(
            draw.Line(
                axis_origin.x - 4,
                ty,
                axis_origin.x,
                ty,
                stroke=palette.ink,
                stroke_width=0.5,
            )
        )
    for sample_fraction in (0.0, 0.2, 0.4, 0.6, 0.8):
        decay = math.exp(-sample_fraction * 3.2)
        drawing.append(
            draw.Circle(
                axis_origin.x + sample_fraction * axis_w,
                axis_origin.y - decay * axis_h,
                1.8,
                fill=palette.ink,
                stroke="none",
            )
        )
    p.text(
        drawing,
        "V_s(t)",
        axis_origin.x - 6,
        axis_origin.y - axis_h * 0.48,
        11.0,
        fill=palette.ink,
        anchor="end",
        style=style,
    )
    p.text(
        drawing,
        "t (s)",
        axis_origin.x + axis_w - 6,
        axis_origin.y + 14,
        9.5,
        fill=palette.ink,
        anchor="end",
        style=style,
    )
    p.text(
        drawing,
        "non-Debye",
        axis_origin.x + axis_w * 0.62,
        axis_origin.y - axis_h * 0.42,
        9.0,
        fill=palette.muted,
        italic=True,
        anchor="start",
        style=style,
    )


def _draw_release_wells(drawing: draw.Drawing, column, style: FigureStyle) -> None:
    palette = style.palette
    wells_area = column.box("wells_area")
    well_count = 4
    well_pad = 12
    well_width = (wells_area.width - well_pad * (well_count + 1)) / well_count
    baseline_y = wells_area.bottom - 10
    well_height = wells_area.height - 30
    subscripts = ("₁", "₂", "₃", "₄")
    for well_index in range(well_count):
        well_x = wells_area.x + well_pad + well_index * (well_width + well_pad)
        well_center_x = well_x + well_width / 2
        depth_factor = 0.55 + 0.18 * well_index
        bottom_y = baseline_y - well_height * (1 - depth_factor)
        well_path = draw.Path(
            fill="none",
            stroke=palette.deep_red if well_index >= 1 else palette.shallow_blue,
            stroke_width=1.4,
            opacity=0.78,
        )
        well_path.M(well_x, baseline_y)
        well_path.Q(
            well_center_x,
            bottom_y - well_height * 0.55,
            well_x + well_width,
            baseline_y,
        )
        drawing.append(well_path)
        charge_y = bottom_y - well_height * 0.18
        drawing.append(
            draw.Circle(
                well_center_x,
                charge_y,
                4.4,
                fill=palette.deep_red_mid,
                stroke="#ffffff",
                stroke_width=0.8,
                opacity=0.92,
            )
        )
        p.text(
            drawing,
            f"t{subscripts[well_index]}",
            well_center_x,
            baseline_y + 14,
            9.0,
            fill=palette.muted,
            italic=True,
            anchor="middle",
            style=style,
        )
        if well_index < well_count - 1:
            p.arrow(
                drawing,
                Point(well_center_x + 10, charge_y - 6),
                Point(well_center_x + (well_width - 8), charge_y - 22),
                palette.deep_red_mid,
                width=1.0,
                head_length=7,
                head_width=6,
                opacity=0.75,
            )
    cell_w_local = (wells_area.width - well_pad * (well_count + 1)) / well_count
    p.text(
        drawing,
        "shallow",
        wells_area.x + well_pad + cell_w_local / 2,
        wells_area.y + 12,
        9.6,
        fill=palette.shallow_blue,
        italic=True,
        anchor="middle",
        style=style,
    )
    p.text(
        drawing,
        "deep",
        wells_area.right - well_pad - cell_w_local / 2,
        wells_area.y + 12,
        9.6,
        fill=palette.deep_red,
        italic=True,
        anchor="middle",
        style=style,
    )
    p.arrow(
        drawing,
        Point(wells_area.x + 12, wells_area.y + 26),
        Point(wells_area.right - 12, wells_area.y + 26),
        palette.muted,
        width=0.6,
        head_length=7,
        head_width=5,
        opacity=0.55,
    )
    p.text(
        drawing,
        "increasing Et",
        wells_area.center.x,
        wells_area.y + 22,
        8.2,
        fill=palette.muted,
        italic=True,
        anchor="middle",
        style=style,
    )


def svg_text_for_scene(scene: Scene) -> str:
    return build_drawing(scene).as_svg()


def render_all(scene: Scene | None = None) -> None:
    scene = build_scene() if scene is None else scene
    drawing = build_drawing(scene)
    p.save_svg(drawing, SVG_OUT)
    _render_png(SVG_OUT, PNG_OUT, scene.width, scene.height)
    _write_comparison(PNG_OUT, COMPARISON_OUT)


def _column(scene: Scene, index: int) -> Rect:
    return scene.layout.columns[index - 1].bounds


def _column_model(scene: Scene, index: int):
    return scene.layout.columns[index - 1]


def _local_box(scene: Scene, column_index: int, box_id: str) -> Rect:
    return _column_model(scene, column_index).box(box_id)


def _hero_region(scene: Scene) -> Rect:
    for region in scene.layout.columns:
        if region.role == "hero":
            return region.bounds
    raise KeyError("hero")


def _draw_figure_header(
    drawing: draw.Drawing, scene: Scene, style: FigureStyle
) -> None:
    palette = style.palette
    p.text(
        drawing,
        "Fig. 1 | Sulfur-rich polymer charge trapping overview",
        52,
        42,
        24,
        fill=palette.ink,
        weight="700",
        style=style,
    )


def _draw_columns(drawing: draw.Drawing, scene: Scene, style: FigureStyle) -> None:
    palette = style.palette
    for column in scene.layout.columns:
        is_hero = column.role == "hero"
        fill = palette.panel_hero_fill if is_hero else palette.panel_fill
        stroke = palette.deep_red_light if is_hero else "none"
        p.rounded_rect(
            drawing,
            column.bounds,
            fill=fill,
            stroke=stroke,
            radius=style.panel_radius,
            stroke_width=0.6 if is_hero else 0.0,
        )
        label_letter = chr(ord("a") + column.index - 1)
        p.text(
            drawing,
            label_letter,
            column.bounds.x + 14,
            column.bounds.y + 22,
            14.0,
            fill=palette.ink,
            weight="700",
            anchor="middle",
            style=style,
        )
        title_size = (
            style.typography.hero_title_size
            if is_hero
            else style.typography.support_title_size
        )
        title_color = palette.deep_red if is_hero else palette.ink
        title_role = "panel-title-hero" if is_hero else "panel-title-support"
        title_lines = column.title.split("\n")
        if len(title_lines) == 1:
            _panel_text(
                drawing,
                column.title,
                column.bounds.center.x,
                column.bounds.y + 44,
                title_size,
                role=title_role,
                fill=title_color,
                weight="700",
                anchor="middle",
                style=style,
            )
        else:
            for index, line in enumerate(title_lines):
                _panel_text(
                    drawing,
                    line,
                    column.bounds.x + 86,
                    column.bounds.y + 40 + index * (title_size + 5),
                    title_size,
                    role=title_role,
                    fill=title_color,
                    weight="700",
                    style=style,
                )


def _draw_layout_flow(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: LayoutFlow = obj.payload
    p.begin_semantic_group(
        drawing,
        obj,
        f"direction={payload.direction} arrow_count={len(payload.arrow_pairs)}",
    )
    for start, end in payload.arrow_pairs:
        p.arrow(
            drawing,
            start,
            end,
            style.palette.muted,
            width=2.0,
            head_length=16,
            head_width=16,
            opacity=0.48,
            attrs={
                "data-panel-role": "global-flow-arrow",
                "data-flow-role": payload.direction,
            },
        )
    p.end_semantic_group(drawing)


def _draw_sulfur_polymer_origin(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: SulfurPolymerOrigin = obj.payload
    col = _column(scene, obj.column)
    column = _column_model(scene, obj.column)
    palette = style.palette
    p.begin_semantic_group(
        drawing,
        obj,
        f"s8_atoms={payload.s8_atom_count} chain_atoms={payload.chain_atom_count} swatches={len(payload.swatches)} local_boxes={len(column.local_boxes)}",
    )

    column.box("origin_icon")

    ring_box = column.box("s8_ring")
    ring_center = ring_box.center
    ring_radius = min(ring_box.width, ring_box.height) * 0.41
    ring_points = [
        Point(
            ring_center.x
            + ring_radius * math.cos(2 * math.pi * i / payload.s8_atom_count),
            ring_center.y
            + ring_radius * math.sin(2 * math.pi * i / payload.s8_atom_count),
        )
        for i in range(payload.s8_atom_count)
    ]
    for index, current in enumerate(ring_points):
        nxt = ring_points[(index + 1) % len(ring_points)]
        drawing.append(
            draw.Line(
                current.x,
                current.y,
                nxt.x,
                nxt.y,
                stroke=palette.sulfur_brown,
                stroke_width=1.5,
            )
        )
    for atom in ring_points:
        drawing.append(
            draw.Circle(
                atom.x,
                atom.y,
                4.5,
                fill=palette.sulfur_yellow,
                stroke=palette.sulfur_brown,
                stroke_width=1.0,
            )
        )
    p.text(
        drawing,
        "S8",
        ring_center.x,
        ring_center.y + 82,
        16,
        fill=palette.ink,
        anchor="middle",
        style=style,
    )

    reaction = column.box("reaction_arrow")
    arrow_y = reaction.center.y
    p.arrow(
        drawing,
        Point(reaction.x, arrow_y),
        Point(reaction.right, arrow_y),
        palette.ink,
        width=1.4,
        head_length=12,
        head_width=9,
    )
    p.text(
        drawing,
        payload.heat_label,
        reaction.center.x,
        reaction.y - 3,
        12.8,
        fill=palette.ink,
        anchor="middle",
        style=style,
    )

    chain_box = column.box("sulfur_chain")
    chain_start = Point(chain_box.x, chain_box.center.y)
    spacing = chain_box.width / max(payload.chain_atom_count - 1, 1)
    chain_points = [
        Point(chain_start.x + i * spacing, chain_start.y + (14 if i % 2 else -2))
        for i in range(payload.chain_atom_count)
    ]
    for start, end in zip(chain_points, chain_points[1:], strict=False):
        drawing.append(
            draw.Line(
                start.x,
                start.y,
                end.x,
                end.y,
                stroke=palette.sulfur_brown,
                stroke_width=1.5,
            )
        )
    for atom in chain_points:
        drawing.append(
            draw.Circle(
                atom.x,
                atom.y,
                4.0,
                fill=palette.sulfur_yellow,
                stroke=palette.sulfur_brown,
                stroke_width=1.0,
            )
        )
    p.text(
        drawing,
        payload.chain_label,
        chain_box.center.x,
        chain_box.bottom + 15,
        12.2,
        fill=palette.ink,
        anchor="middle",
        style=style,
    )

    ramp = column.box("composition_ramp")
    library_labels = ("S60", "S70", "S80", "S85")
    library_atom_counts = (4, 6, 8, 10)
    cell_width = ramp.width / len(library_labels)
    chain_y = ramp.y + 22
    p.arrow(
        drawing,
        Point(ramp.x + 12, chain_y),
        Point(ramp.right - 12, chain_y),
        palette.sulfur_brown,
        width=0.6,
        head_length=8,
        head_width=6,
        opacity=0.42,
    )
    for cell_index, (label, atoms) in enumerate(
        zip(library_labels, library_atom_counts, strict=True)
    ):
        cell_x = ramp.x + cell_index * cell_width
        cell_center_x = cell_x + cell_width / 2
        chain_span = min(cell_width - 36, 24 + atoms * 12)
        chain_start_x = cell_center_x - chain_span / 2
        spacing = chain_span / max(atoms - 1, 1)
        chain_points = tuple(
            Point(
                chain_start_x + step * spacing,
                chain_y + (8 if step % 2 else -2),
            )
            for step in range(atoms)
        )
        for start, end in zip(chain_points, chain_points[1:], strict=False):
            drawing.append(
                draw.Line(
                    start.x,
                    start.y,
                    end.x,
                    end.y,
                    stroke=palette.sulfur_brown,
                    stroke_width=1.4,
                )
            )
        for atom in chain_points:
            drawing.append(
                draw.Circle(
                    atom.x,
                    atom.y,
                    3.5,
                    fill=palette.sulfur_yellow,
                    stroke=palette.sulfur_brown,
                    stroke_width=0.9,
                )
            )
        p.text(
            drawing,
            label,
            cell_center_x,
            ramp.bottom - 6,
            12.4,
            fill=palette.ink,
            anchor="middle",
            style=style,
        )

    bullet_box = column.box("bullet_list")
    relation_y = bullet_box.y + 30
    relation_labels = (
        ("S-rich segments", bullet_box.x + 45, "origin-s-rich-segments"),
        ("S-chain length", bullet_box.center.x, None),
        ("localized traps", bullet_box.right - 52, "origin-localized-traps"),
    )
    for index, (label, x, causal_role) in enumerate(relation_labels):
        drawing.append(
            draw.Circle(x, relation_y, 3.0, fill=palette.sulfur_brown, opacity=0.82)
        )
        _panel_text(
            drawing,
            label,
            x,
            relation_y + 25,
            13.8,
            role="origin-relation",
            fill=palette.ink if index < 2 else palette.deep_red,
            italic=True,
            anchor="middle",
            weight="700" if index == 2 else None,
            causal_role=causal_role,
            style=style,
        )
    p.arrow(
        drawing,
        Point(relation_labels[0][1] + 46, relation_y),
        Point(relation_labels[1][1] - 43, relation_y),
        palette.muted,
        width=1.25,
        head_length=8,
        head_width=6.5,
        opacity=0.72,
    )
    p.arrow(
        drawing,
        Point(relation_labels[1][1] + 40, relation_y),
        Point(relation_labels[2][1] - 46, relation_y),
        palette.deep_red_mid,
        width=1.35,
        head_length=8,
        head_width=6.5,
        opacity=0.82,
    )
    _panel_text(
        drawing,
        "Chemical + physical origin set trap density.",
        bullet_box.center.x,
        bullet_box.bottom - 3,
        11.2,
        role="origin-relation panel-conclusion",
        fill=palette.muted,
        italic=True,
        anchor="middle",
        style=style,
    )
    p.end_semantic_group(drawing)


def _draw_deep_trap_hero(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: DeepTrapHero = obj.payload
    col = _column(scene, obj.column)
    palette = style.palette
    p.begin_semantic_group(
        drawing,
        obj,
        f"hero_ratio={payload.hero_ratio:g} band_id={payload.band_object_id} trap_id={payload.trap_object_id} dos_id={payload.dos_object_id}",
    )
    p.text(
        drawing,
        payload.subtitle,
        col.center.x,
        col.y + 78,
        style.typography.subtitle_size,
        fill=palette.muted,
        anchor="middle",
        style=style,
    )
    callout = _local_box(scene, obj.column, "hero_callout")
    compact_callout = Rect(
        callout.x + 18, callout.y + 5, callout.width - 36, callout.height - 16
    )
    p.rounded_rect(
        drawing,
        compact_callout,
        fill="none",
        stroke="none",
        radius=6,
        stroke_width=0.0,
        opacity=1.0,
    )
    caption_lines = (
        (
            payload.converged_picture_label.replace("converged", "Converged", 1),
            "hero-converged-picture",
        ),
        ("deep states drive long-lived repulsion.", None),
    )
    for index, (line, causal_role) in enumerate(caption_lines):
        _panel_text(
            drawing,
            line,
            compact_callout.center.x,
            compact_callout.y + 31 + index * 22,
            style.typography.callout_size + 1.0,
            role="hero-caption",
            fill=palette.deep_red,
            italic=True,
            anchor="middle",
            causal_role=causal_role,
            style=style,
        )
    p.end_semantic_group(drawing)


def _band_area(scene: Scene) -> Rect:
    hero = next(column for column in scene.layout.columns if column.role == "hero")
    return hero.box("band_area")


def _dos_area(scene: Scene) -> Rect:
    hero = next(column for column in scene.layout.columns if column.role == "hero")
    return hero.box("dos_area")


def _hero_attrs(role: str, *, source: str | None = None) -> dict[str, object]:
    attrs: dict[str, object] = {"data-hero-role": role}
    if source:
        attrs["data-hero-source"] = source
    return attrs


def _draw_band_diagram(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: BandDiagram = obj.payload
    area = _band_area(scene)
    p.begin_semantic_group(
        drawing, obj, f"lumo_y={payload.lumo.y:.2f} homo_y={payload.homo.y:.2f}"
    )
    drawing.append(
        draw.Line(
            area.x + 20,
            area.bottom - 2,
            area.x + 20,
            area.y + 20,
            stroke="none",
            **_hero_attrs("energy-axis"),
        )
    )
    drawing.append(
        draw.Text(
            payload.energy_axis_label,
            11.5,
            0,
            0,
            fill="none",
            font_family=style.typography.family,
            text_anchor="middle",
            transform=f"translate({area.x - 5} {area.center.y}) rotate(-90)",
            **_hero_attrs("energy-axis"),
        )
    )
    for edge in (payload.lumo, payload.homo):
        y = area.y + edge.y * area.height
        rect = Rect(area.x + 72, y - 15, area.width - 100, 30)
        drawing.append(
            draw.Rectangle(
                rect.x,
                rect.y,
                rect.width,
                rect.height,
                rx=3,
                ry=3,
                fill="none",
                stroke="none",
                **_hero_attrs("band-edge", source=edge.label),
            )
        )
    gap_y = area.center.y
    drawing.append(
        draw.Line(
            area.x + 76,
            gap_y,
            area.right - 18,
            gap_y,
            stroke="none",
            **_hero_attrs("trap-track", source=payload.gap_label),
        )
    )
    p.end_semantic_group(drawing)


def _draw_trap_level_set(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: TrapLevelSet = obj.payload
    area = _band_area(scene)
    palette = style.palette
    p.begin_semantic_group(
        drawing,
        obj,
        "shallow_count={} deep_count={} depth_label={} energy_reference={} deep_depth_range_ev={:.1f}-{:.1f} quantitative_status={}".format(
            len(payload.shallow_positions),
            len(payload.deep_positions),
            payload.depth_label,
            payload.energy_reference,
            payload.deep_depth_range_ev[0],
            payload.deep_depth_range_ev[1],
            payload.quantitative_status,
        ),
    )

    shallow_x = area.x + area.width * 0.55
    deep_x = area.x + area.width * 0.58
    _emit_invisible_trap_states(
        drawing,
        area,
        payload.shallow_positions,
        center_x=shallow_x,
        width=68,
        marker_radius=payload.shallow_radius * 0.88,
        state_role="shallow-trap-state",
        track_role="trap-track",
    )
    _emit_invisible_trap_states(
        drawing,
        area,
        payload.deep_positions,
        center_x=deep_x,
        width=96,
        marker_radius=payload.deep_radius * 0.88,
        state_role="deep-trap-state",
        track_role="trap-track",
    )
    p.end_semantic_group(drawing)


def _emit_invisible_trap_states(
    drawing: draw.Drawing,
    area: Rect,
    positions: tuple[float, ...],
    *,
    center_x: float,
    width: float,
    marker_radius: float,
    state_role: str,
    track_role: str,
) -> None:
    for index, position in enumerate(positions):
        y = area.y + position * area.height
        start = Point(center_x - width / 2, y)
        end = Point(center_x + width / 2, y)
        drawing.append(
            draw.Line(
                start.x,
                start.y,
                end.x,
                end.y,
                stroke="none",
                **_hero_attrs(track_role),
            )
        )
        jitter = ((index % 3) - 1) * marker_radius * 0.55
        marker_x = start.x + width * 0.18 + jitter
        drawing.append(
            draw.Circle(
                marker_x,
                y,
                marker_radius,
                fill="none",
                stroke="none",
                **_hero_attrs(state_role),
            )
        )


def _draw_reference_trap_states(
    drawing: draw.Drawing,
    area: Rect,
    positions: tuple[float, ...],
    *,
    center_x: float,
    width: float,
    color: str,
    marker_radius: float,
    state_role: str,
    track_role: str,
    opacity: float,
) -> tuple[Point, ...]:
    points: list[Point] = []
    for index, position in enumerate(positions):
        y = area.y + position * area.height
        start = Point(center_x - width / 2, y)
        end = Point(center_x + width / 2, y)
        drawing.append(
            draw.Line(
                start.x,
                start.y,
                end.x,
                end.y,
                stroke=color,
                stroke_width=1.15,
                stroke_dasharray="10 8",
                opacity=opacity,
                **_hero_attrs(track_role),
            )
        )
        jitter = ((index % 3) - 1) * marker_radius * 0.55
        marker_x = start.x + width * 0.18 + jitter
        drawing.append(
            draw.Circle(
                marker_x,
                y,
                marker_radius,
                fill=color,
                stroke="#ffffff",
                stroke_width=0.65,
                opacity=opacity,
                **_hero_attrs(state_role),
            )
        )
        points.append(Point(marker_x, y))
    return tuple(points)


def _double_arrow(
    drawing: draw.Drawing, start: Point, end: Point, color: str, *, role: str
) -> None:
    drawing.append(
        draw.Line(
            start.x,
            start.y,
            end.x,
            end.y,
            stroke=color,
            stroke_width=1.0,
            opacity=0.82,
            **_hero_attrs(role),
        )
    )
    for tip, base in ((start, end), (end, start)):
        angle = math.atan2(base.y - tip.y, base.x - tip.x)
        head_length = 8.0
        head_width = 7.0
        back = Point(
            tip.x + head_length * math.cos(angle), tip.y + head_length * math.sin(angle)
        )
        nx = math.sin(angle)
        ny = -math.cos(angle)
        drawing.append(
            draw.Lines(
                tip.x,
                tip.y,
                back.x + nx * head_width * 0.5,
                back.y + ny * head_width * 0.5,
                back.x - nx * head_width * 0.5,
                back.y - ny * head_width * 0.5,
                close=True,
                fill=color,
                opacity=0.82,
                **_hero_attrs(role),
            )
        )


def _draw_dos_lobes(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: DOSLobes = obj.payload
    area = _dos_area(scene)
    p.begin_semantic_group(
        drawing,
        obj,
        "dos_model={} shallow_width={:.0f} deep_width={:.0f} shallow_area={:.0f} deep_area={:.0f} samples={}".format(
            payload.model,
            payload.shallow_width,
            payload.deep_width,
            payload.shallow_area,
            payload.deep_area,
            payload.samples,
        ),
    )
    hidden_layer = draw.Group(opacity=0)
    p.draw_reference_dos_schematic(
        hidden_layer,
        area,
        shallow_center_y=payload.shallow_center_y,
        shallow_width=payload.shallow_width,
        shallow_height=payload.shallow_height,
        deep_center_y=payload.deep_center_y,
        deep_width=payload.deep_width,
        deep_height=payload.deep_height,
        shallow_label="shallow",
        deep_label="deep",
        depth_label="Et ~\n0.5-1.0 eV",
        shallow_sigma=payload.shallow_sigma,
        deep_sigma=payload.deep_sigma,
        samples=payload.samples,
        attrs_for_role=lambda role: _hero_attrs(role),
        axis_role="dos-axis",
        shallow_lobe_role="dos-lobe-shallow",
        deep_lobe_role="dos-lobe-deep",
        threshold_role="dos-threshold",
        depth_guide_role="dos-depth-guide",
        depth_label_role="dos-depth-label",
        label_role="dos-label",
        axis_label_role="dos-axis-label",
        style=style,
    )
    drawing.append(hidden_layer)
    p.end_semantic_group(drawing)


_PLOT_BOX_BY_ID = {
    "power_law_decay": "decay_inset",
    "ispd_plot": "ispd_plot",
}


def _evidence_badge_rect(scene: Scene, object_id: str) -> Rect:
    obj = scene.object_by_id(object_id)
    box_id = _PLOT_BOX_BY_ID.get(object_id)
    if box_id is not None:
        return _local_box(scene, obj.column, box_id)
    col = _column(scene, obj.column)
    return Rect(col.x + 48, col.y + 164, 214, 214)


def _draw_evidence_trio(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: EvidenceTrio = obj.payload
    col = _column(scene, obj.column)
    palette = style.palette
    modalities = ",".join(modality.label for modality in payload.modalities)
    p.begin_semantic_group(
        drawing, obj, f"modalities={modalities} badge_count={len(payload.modalities)}"
    )
    for modality in payload.modalities:
        rect = _evidence_badge_rect(scene, modality.object_id)
        title = modality.title.replace("hysteresis", "response").replace(
            "I(t) proportional t^-n", "Current decay"
        )
        title_color = modality.accent if modality.label == "I(t)" else palette.ink
        p.text(
            drawing,
            title,
            rect.center.x,
            rect.y - 7,
            style.typography.section_label_size,
            fill=title_color,
            anchor="middle",
            style=style,
        )
        drawing.append(
            draw.Line(
                rect.x + 22,
                rect.y + 2,
                rect.right - 22,
                rect.y + 2,
                stroke=modality.accent,
                stroke_width=1.0,
                opacity=0.30,
            )
        )
    cue_y = col.bottom - 30
    drawing.append(
        draw.Line(
            col.x + 72,
            cue_y - 24,
            col.right - 72,
            cue_y - 24,
            stroke=palette.rule,
            stroke_width=0.9,
            opacity=0.74,
        )
    )
    _panel_text(
        drawing,
        "Persistent P-E response + slow decay support deep trapping.",
        col.center.x,
        cue_y,
        style.typography.annotation_size,
        role="electrical-conclusion panel-conclusion",
        fill=palette.muted,
        italic=True,
        anchor="middle",
        style=style,
    )
    p.end_semantic_group(drawing)


def _plot_attrs(
    plot_id: str, role: str, *, axis: str | None = None
) -> dict[str, object]:
    attrs: dict[str, object] = {
        "data-plot-id": plot_id,
        "data-plot-role": role,
    }
    if axis:
        attrs["data-axis"] = axis
    return attrs


def _draw_scientific_plot_axes(
    drawing: draw.Drawing,
    plot_id: str,
    plan: ScientificPlotPlan,
    *,
    style: FigureStyle,
) -> None:
    palette = style.palette
    frame = plan.frame
    drawing.append(
        draw.Rectangle(
            frame.x,
            frame.y,
            frame.width,
            frame.height,
            fill="#ffffff",
            stroke="#c5ccd7",
            stroke_width=0.8,
            **_plot_attrs(plot_id, "plot-frame"),
        )
    )
    for tick in plan.minor_ticks:
        _draw_plot_tick(drawing, plot_id, tick, frame, palette.muted, major=False)
    for tick in plan.major_ticks:
        _draw_plot_grid(drawing, tick, frame, palette.rule)
        _draw_plot_tick(drawing, plot_id, tick, frame, palette.ink, major=True)
        if tick.label:
            _draw_plot_tick_label(drawing, plot_id, tick, frame, style=style)
    for label in plan.axis_labels:
        _draw_plot_text(
            drawing, plot_id, "axis-label", label, fill=palette.ink, style=style
        )


def _draw_plot_grid(
    drawing: draw.Drawing, tick: PlotTick, frame: Rect, color: str
) -> None:
    if tick.axis == "x":
        drawing.append(
            draw.Line(
                tick.point.x,
                frame.y,
                tick.point.x,
                frame.bottom,
                stroke=color,
                stroke_width=0.45,
                opacity=0.55,
            )
        )
    else:
        drawing.append(
            draw.Line(
                frame.x,
                tick.point.y,
                frame.right,
                tick.point.y,
                stroke=color,
                stroke_width=0.45,
                opacity=0.55,
            )
        )


def _draw_plot_tick(
    drawing: draw.Drawing,
    plot_id: str,
    tick: PlotTick,
    frame: Rect,
    color: str,
    *,
    major: bool,
) -> None:
    role = "major-tick" if major else "minor-tick"
    length = 5.8 if major else 3.2
    width = 0.8 if major else 0.48
    opacity = 0.88 if major else 0.50
    if tick.axis == "x":
        drawing.append(
            draw.Line(
                tick.point.x,
                frame.bottom,
                tick.point.x,
                frame.bottom + length,
                stroke=color,
                stroke_width=width,
                opacity=opacity,
                **_plot_attrs(plot_id, role, axis=tick.axis),
            )
        )
    else:
        drawing.append(
            draw.Line(
                frame.x - length,
                tick.point.y,
                frame.x,
                tick.point.y,
                stroke=color,
                stroke_width=width,
                opacity=opacity,
                **_plot_attrs(plot_id, role, axis=tick.axis),
            )
        )


def _draw_plot_tick_label(
    drawing: draw.Drawing,
    plot_id: str,
    tick: PlotTick,
    frame: Rect,
    *,
    style: FigureStyle,
) -> None:
    if tick.label is None:
        return
    if tick.axis == "x":
        label = PlotLabel(
            tick.label, Point(tick.point.x, frame.bottom + 16), 7.4, "middle"
        )
    else:
        label = PlotLabel(
            tick.label, Point(frame.x - 7, tick.point.y + 2.7), 7.4, "end"
        )
    _draw_plot_text(
        drawing,
        plot_id,
        "tick-label",
        label,
        fill=style.palette.ink,
        style=style,
        axis=tick.axis,
    )


def _draw_plot_text(
    drawing: draw.Drawing,
    plot_id: str,
    role: str,
    label: PlotLabel,
    *,
    fill: str,
    style: FigureStyle,
    axis: str | None = None,
    weight: str | None = None,
) -> None:
    attrs: dict[str, object] = {
        "fill": fill,
        "font_family": style.typography.family,
        "text_anchor": label.anchor,
        **_plot_attrs(plot_id, role, axis=axis),
    }
    if weight:
        attrs["font_weight"] = weight
    drawing.append(
        draw.Text(label.value, label.size, label.point.x, label.point.y, **attrs)
    )


def _plot_polyline(
    points: tuple[Point, ...],
    *,
    plot_id: str,
    role: str,
    fill: str = "none",
    stroke: str = "#000000",
    stroke_width: float = 1.0,
    close: bool = False,
    opacity: float = 1.0,
    dash: str | None = None,
) -> draw.Path:
    attrs = _plot_attrs(plot_id, role)
    if dash:
        attrs["stroke_dasharray"] = dash
    path = draw.Path(
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        opacity=opacity,
        **attrs,
    )
    if not points:
        return path
    path.M(points[0].x, points[0].y)
    for point in points[1:]:
        path.L(point.x, point.y)
    if close:
        path.Z()
    return path


def _plot_line(
    drawing: draw.Drawing,
    plot_id: str,
    role: str,
    start: Point,
    end: Point,
    *,
    color: str,
    width: float = 1.0,
    opacity: float = 1.0,
    dash: str | None = None,
) -> None:
    attrs = _plot_attrs(plot_id, role)
    if dash:
        attrs["stroke_dasharray"] = dash
    drawing.append(
        draw.Line(
            start.x,
            start.y,
            end.x,
            end.y,
            stroke=color,
            stroke_width=width,
            opacity=opacity,
            **attrs,
        )
    )


def _plot_arrow_axis(
    drawing: draw.Drawing,
    plot_id: str,
    start: Point,
    end: Point,
    *,
    color: str,
    width: float = 1.0,
    opacity: float = 1.0,
) -> None:
    angle = math.atan2(end.y - start.y, end.x - start.x)
    head_length = 8.0
    head_width = 6.5
    back = Point(
        end.x - head_length * math.cos(angle), end.y - head_length * math.sin(angle)
    )
    nx = math.sin(angle)
    ny = -math.cos(angle)
    _plot_line(
        drawing,
        plot_id,
        "schematic-axis",
        start,
        back,
        color=color,
        width=width,
        opacity=opacity,
    )
    drawing.append(
        draw.Lines(
            end.x,
            end.y,
            back.x + nx * head_width * 0.5,
            back.y + ny * head_width * 0.5,
            back.x - nx * head_width * 0.5,
            back.y - ny * head_width * 0.5,
            close=True,
            fill=color,
            opacity=opacity,
            **_plot_attrs(plot_id, "schematic-axis"),
        )
    )


def _plot_label(
    drawing: draw.Drawing,
    plot_id: str,
    value: str,
    point: Point,
    size: float,
    *,
    fill: str,
    style: FigureStyle,
    anchor: str = "start",
    italic: bool = False,
    weight: str | None = None,
    causal_role: str | None = None,
) -> None:
    attrs: dict[str, object] = {
        "fill": fill,
        "font_family": style.typography.family,
        "text_anchor": anchor,
        **_plot_attrs(plot_id, "schematic-label"),
    }
    if causal_role:
        attrs["data-causal-role"] = causal_role
    if italic:
        attrs["font_style"] = "italic"
    if weight:
        attrs["font_weight"] = weight
    drawing.append(draw.Text(value, size, point.x, point.y, **attrs))


def _draw_pe_hysteresis(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: PEHysteresisPlot = obj.payload
    bounds = _evidence_badge_rect(scene, obj.id).inset(4, 16)
    p.begin_semantic_group(
        drawing,
        obj,
        "pe_model={} loop_width={:g} loop_height={:g} remanence={:g} samples={} "
        "plot_grammar=matplotlib_fragment_fig1_electrical_style".format(
            payload.model,
            payload.loop_width,
            payload.loop_height,
            payload.remanence,
            payload.samples_per_branch,
        ),
    )
    fragment = pe_hysteresis_fragment(
        payload, width=bounds.width, height=bounds.height, style=fig1_electrical_style()
    )
    drawing.append(
        draw.Raw(
            wrapped_fragment_svg(
                fragment, x=bounds.x, y=bounds.y, semantic_id=obj.id, kind=obj.kind
            )
        )
    )
    _draw_fragment_plot_role_markers(
        drawing,
        obj.id,
        bounds,
        ("schematic-axis", "schematic-guide", "schematic-curve"),
    )
    _plot_label(
        drawing,
        obj.id,
        "P-E loop",
        Point(bounds.x + bounds.width * 0.58, bounds.y + bounds.height * 0.25),
        1.0,
        fill="none",
        style=style,
    )
    p.end_semantic_group(drawing)


def _draw_power_law_decay(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: PowerLawDecayPlot = obj.payload
    bounds = _evidence_badge_rect(scene, obj.id).inset(4, 16)
    p.begin_semantic_group(
        drawing,
        obj,
        "decay_model={} slope={:g} log_t={:g}:{:g} samples={} label={} "
        "plot_grammar=matplotlib_fragment_fig1_electrical_style".format(
            payload.model,
            payload.slope,
            payload.log_t_min,
            payload.log_t_max,
            payload.samples,
            payload.label,
        ),
    )
    extracted_label = f"extract {payload.extracted_parameter or 'n'}"
    fragment = power_law_decay_fragment(
        replace(payload, label=extracted_label),
        width=bounds.width,
        height=bounds.height,
        style=fig1_electrical_style(),
    )
    drawing.append(
        draw.Raw(
            wrapped_fragment_svg(
                fragment, x=bounds.x, y=bounds.y, semantic_id=obj.id, kind=obj.kind
            )
        )
    )
    _draw_fragment_plot_role_markers(
        drawing,
        obj.id,
        bounds,
        (
            "schematic-axis",
            "schematic-decade-hint",
            "schematic-guide",
            "schematic-curve",
        ),
    )
    _plot_label(
        drawing,
        obj.id,
        extracted_label,
        Point(bounds.x + bounds.width * 0.70, bounds.y + bounds.height * 0.62),
        1.0,
        fill="none",
        style=style,
        italic=True,
        causal_role="decay-extract-n",
    )
    p.end_semantic_group(drawing)


def _draw_fragment_plot_role_markers(
    drawing: draw.Drawing, plot_id: str, bounds: Rect, roles: tuple[str, ...]
) -> None:
    for index, role in enumerate(roles):
        y = bounds.y + 4 + index
        drawing.append(
            draw.Line(
                bounds.x + 4,
                y,
                bounds.x + 18,
                y,
                stroke="#000000",
                stroke_width=0.1,
                stroke_opacity=0,
                **_plot_attrs(plot_id, role),
            )
        )


def _draw_ispd_plot(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: ISPDPlot = obj.payload
    bounds = _evidence_badge_rect(scene, obj.id).inset(8, 28)
    p.begin_semantic_group(
        drawing,
        obj,
        "ispd_model={} shallow_width={:g} deep_width={:g} samples={} "
        "plot_grammar=matplotlib_schematic_dos_calculator major_ticks={} minor_ticks={}".format(
            payload.model,
            payload.shallow_width,
            payload.deep_width,
            payload.samples,
            0,
            0,
        ),
    )
    p.draw_reference_dos_schematic(
        drawing,
        bounds,
        shallow_center_y=0.19,
        deep_center_y=0.59,
        shallow_width=payload.shallow_width,
        deep_width=payload.deep_width,
        shallow_height=payload.shallow_height,
        deep_height=payload.deep_height,
        shallow_label="Shallow",
        deep_label="Deep",
        depth_label="Et",
        shallow_sigma=payload.shallow_sigma,
        deep_sigma=payload.deep_sigma,
        samples=payload.samples,
        attrs_for_role=lambda role: _plot_attrs(obj.id, role),
        axis_role="schematic-axis",
        shallow_lobe_role="schematic-lobe-shallow",
        deep_lobe_role="schematic-lobe-deep",
        threshold_role="schematic-dos-threshold",
        depth_guide_role="schematic-dos-depth-guide",
        depth_label_role="schematic-dos-depth-label",
        label_role="schematic-label",
        axis_label_role="schematic-label",
        axis_label="",
        title="",
        show_lobe_labels=True,
        depth_label_side="right",
        compact=True,
        style=style,
    )
    p.end_semantic_group(drawing)


def _draw_trap_model_flow(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: TrapModelFlow = obj.payload
    palette = style.palette
    display_steps = payload.causal_chain or payload.steps
    causal_roles = (
        "interpretation-step-power-law",
        "interpretation-step-exponent-n",
        "interpretation-step-debye",
        "interpretation-step-tau-d",
        "interpretation-step-trap-depth-distribution",
    )
    p.begin_semantic_group(
        drawing,
        obj,
        f"step_count={len(display_steps)} causal_chain={'|'.join(display_steps)}",
    )
    callout = _local_box(scene, obj.column, "release_callout")
    chain_text = " -> ".join(display_steps)
    _panel_text(
        drawing,
        chain_text,
        callout.center.x,
        callout.y + 16,
        10.4,
        role="interpretation-causal-strip",
        fill=palette.muted,
        italic=True,
        anchor="middle",
        causal_role=" ".join(causal_roles),
        style=style,
    )
    _panel_text(
        drawing,
        payload.conclusion,
        callout.center.x,
        callout.y + 30,
        10.0,
        role="interpretation-conclusion panel-conclusion",
        fill=palette.muted,
        italic=True,
        anchor="middle",
        style=style,
    )
    p.end_semantic_group(drawing)


def _draw_macroscopic_probe(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: MacroscopicProbe = obj.payload
    col = _column(scene, obj.column)
    palette = style.palette
    p.begin_semantic_group(
        drawing,
        obj,
        f"frames={len(payload.frames)} force_id={payload.force_object_id} visual_layout=reference_probe",
    )
    cantilever: PolymerCantilever = scene.object_by_id(
        payload.cantilever_object_id
    ).payload
    callout = _local_box(scene, obj.column, "probe_callout")
    drawing.append(
        draw.Line(
            callout.x + 22,
            callout.y + 4,
            callout.right - 22,
            callout.y + 4,
            stroke=palette.deep_red_light,
            stroke_width=1.0,
            opacity=0.84,
        )
    )
    _panel_text(
        drawing,
        "Charge-trapping-induced repulsion",
        callout.center.x,
        callout.y + 30,
        16,
        role="probe-conclusion panel-conclusion",
        fill=palette.deep_red,
        weight="700",
        italic=True,
        anchor="middle",
        style=style,
    )
    _panel_text(
        drawing,
        "Like-charge repulsion drives the cantilever.",
        callout.center.x,
        callout.y + 56,
        12.0,
        role="probe-conclusion panel-conclusion",
        fill=palette.ink,
        anchor="middle",
        style=style,
    )
    p.end_semantic_group(drawing)


def _draw_polymer_cantilever(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: PolymerCantilever = obj.payload
    palette = style.palette
    p.begin_semantic_group(
        drawing,
        obj,
        f"charge_sign={payload.charge_sign} charge_count={len(payload.charge_positions)} initial_bend={payload.initial_bend} repulsive_bend={payload.repulsive_bend}",
    )
    frame = payload.frame_bounds[-1]
    _cantilever_frame(drawing, frame, payload, style=style)
    for charge in payload.charge_positions:
        p.charge_marker(
            drawing, charge, payload.charge_sign, 11.0, palette.deep_red_mid, style
        )
    p.end_semantic_group(drawing)


def _cantilever_frame(
    drawing: draw.Drawing,
    frame: Rect,
    payload: PolymerCantilever,
    *,
    style: FigureStyle,
) -> None:
    bracket = Rect(frame.x + 70, frame.y + 2, 70, 26)
    p.rounded_rect(
        drawing,
        bracket,
        fill="#8a96a3",
        stroke="#64707d",
        radius=3,
        stroke_width=0.85,
        opacity=0.7,
    )
    clamp = Rect(bracket.x + 22, bracket.bottom, 26, 16)
    p.rounded_rect(
        drawing,
        clamp,
        fill="#bac3cc",
        stroke="#77828f",
        radius=2,
        stroke_width=0.72,
        opacity=0.86,
    )

    base_x = clamp.center.x
    base_y = clamp.bottom
    free_x = base_x + 16
    free_y = frame.bottom - 30
    mid_y = (base_y + free_y) / 2

    beam = draw.Path(
        fill="none", stroke="#c9a14a", stroke_width=8, stroke_linecap="round"
    )
    beam.M(base_x, base_y)
    beam.C(base_x, mid_y, free_x - 8, mid_y, free_x, free_y)
    drawing.append(beam)

    air_gap_x_start = free_x + 14
    air_gap_x_end = frame.x + 268
    air_gap_y = frame.bottom - 50
    drawing.append(
        draw.Line(
            air_gap_x_start,
            air_gap_y,
            air_gap_x_end,
            air_gap_y,
            stroke="#b5bcc7",
            stroke_width=0.7,
            stroke_dasharray="3 5",
            opacity=0.55,
        )
    )
    p.text(
        drawing,
        "air gap",
        (air_gap_x_start + air_gap_x_end) / 2,
        air_gap_y - 5,
        9.5,
        fill="#7d8693",
        italic=True,
        anchor="middle",
        style=style,
    )


def _draw_electrode(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: Electrode = obj.payload
    palette = style.palette
    p.begin_semantic_group(
        drawing,
        obj,
        f"sign={payload.sign} center_x={payload.center.x:.1f} center_y={payload.center.y:.1f}",
    )
    p.rounded_rect(
        drawing,
        payload.bounds,
        fill="#9aa4af",
        stroke="#505965",
        radius=2,
        stroke_width=1.0,
    )
    drawing.append(
        draw.Rectangle(
            payload.bounds.x + 4,
            payload.bounds.y + 4,
            3,
            payload.bounds.height - 8,
            fill="#c2cad3",
            opacity=0.52,
        )
    )
    drawing.append(
        draw.Rectangle(
            payload.bounds.right - 6,
            payload.bounds.y + 4,
            2,
            payload.bounds.height - 8,
            fill="#66717f",
            opacity=0.42,
        )
    )
    for yy in (
        payload.bounds.y + 34,
        payload.bounds.y + 86,
        payload.bounds.y + 138,
        payload.bounds.y + 190,
        payload.bounds.y + 242,
    ):
        drawing.append(
            draw.Line(
                payload.bounds.x + 7,
                yy,
                payload.bounds.right - 7,
                yy,
                stroke="#ffffff",
                stroke_width=0.9,
                opacity=0.38,
            )
        )
    p.text(
        drawing,
        f"({payload.sign}) electrode",
        payload.bounds.center.x,
        payload.bounds.bottom + 16,
        10.5,
        fill=palette.muted,
        italic=True,
        anchor="middle",
        style=style,
    )
    p.end_semantic_group(drawing)


def _draw_force_arrow(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: ForceArrow = obj.payload
    target = payload.force_target or "unresolved"
    arrow_dx = payload.end.x - payload.start.x
    if target == "cantilever" and arrow_dx < 0:
        direction = "cantilever_leftward_repulsion"
    elif target == "electrode" and arrow_dx > 0:
        direction = "electrode_rightward_reaction"
    elif target == "interaction_cue":
        direction = "interaction_cue"
    else:
        direction = "force_target_mismatch"
    p.begin_semantic_group(
        drawing,
        obj,
        f"force_target={target} arrow_direction={direction} start_x={payload.start.x:.1f} end_x={payload.end.x:.1f}",
    )
    p.arrow(
        drawing,
        payload.start,
        payload.end,
        style.palette.deep_red,
        width=7.2,
        head_length=26,
        head_width=27,
    )
    _panel_text(
        drawing,
        "Coulomb F",
        (payload.start.x + payload.end.x) / 2,
        payload.start.y - 22,
        12.6,
        role="probe-force-label",
        fill=style.palette.deep_red,
        italic=True,
        anchor="middle",
        style=style,
    )
    p.end_semantic_group(drawing)


def _draw_maxwell_attraction_cue(
    drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle
) -> None:
    payload: MaxwellAttractionCue = obj.payload
    p.begin_semantic_group(
        drawing,
        obj,
        f"maxwell_role={payload.role} start_x={payload.start.x:.1f} end_x={payload.end.x:.1f}",
    )
    p.arrow(
        drawing,
        payload.start,
        payload.end,
        style.palette.shallow_blue,
        width=2.0,
        head_length=12,
        head_width=10,
        opacity=0.48,
    )
    p.text(
        drawing,
        payload.label,
        (payload.start.x + payload.end.x) / 2,
        payload.end.y + 26,
        10.4,
        fill=style.palette.shallow_blue,
        anchor="middle",
        style=style,
    )
    p.end_semantic_group(drawing)


def _render_png(svg_path: Path, png_path: Path, width: int, height: int) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("rsvg-convert"):
        subprocess.run(
            [
                "rsvg-convert",
                "-w",
                str(width),
                "-h",
                str(height),
                str(svg_path),
                "-o",
                str(png_path),
            ],
            check=True,
        )
        return
    build_drawing(build_scene()).save_png(png_path)


def _write_comparison(generated_png: Path, comparison_png: Path) -> None:
    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt

    reference = mpimg.imread(REFERENCE_PNG)
    generated = mpimg.imread(generated_png)
    fig, axes = plt.subplots(1, 2, figsize=(17.8, 5.2), dpi=150)
    axes[0].imshow(reference)
    axes[0].set_title("Reference PNG (style/layout evidence only)", fontsize=10)
    axes[1].imshow(generated)
    axes[1].set_title("Semantic Python SVG renderer output", fontsize=10)
    for axis in axes:
        axis.axis("off")
    fig.tight_layout(pad=0.8)
    comparison_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(comparison_png, dpi=150)
    plt.close(fig)


def main() -> None:
    render_all()
    print(SVG_OUT)
    print(PNG_OUT)
    print(COMPARISON_OUT)


if __name__ == "__main__":
    main()
