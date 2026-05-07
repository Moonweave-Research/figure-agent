from __future__ import annotations

import shutil
import subprocess
import math
from pathlib import Path
from typing import Callable

import drawsvg as draw

from engine.scientific_geometry import power_law_loglog_points
from engine.scientific_plots import (
    PlotLabel,
    PlotTick,
    ScientificPlotPlan,
    pe_hysteresis_plan,
    power_law_decay_plan,
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
from engine.scene import Point, Rect, Scene, SemanticObject
from engine.style import DEFAULT_STYLE, FigureStyle
from engine import primitives as p
from fig1_l1_scene import build_scene


ROOT = Path(__file__).resolve().parents[1]
SVG_OUT = ROOT / "fig1_reference_semantic.svg"
PNG_OUT = ROOT / "fig1_reference_semantic.png"
COMPARISON_OUT = ROOT / "reference_vs_fig1_reference_semantic.png"
REFERENCE_PNG = ROOT / "reference" / "source_variant_aesthetic_ref.png"

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
    drawing.append(draw.Rectangle(0, 0, scene.width, scene.height, fill=style.palette.white))
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
    return drawing


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


def _draw_figure_header(drawing: draw.Drawing, scene: Scene, style: FigureStyle) -> None:
    palette = style.palette
    p.text(drawing, "Fig. 1 | Sulfur-rich polymer charge trapping overview", 52, 42, 24, fill=palette.ink, weight="700", style=style)


def _draw_columns(drawing: draw.Drawing, scene: Scene, style: FigureStyle) -> None:
    palette = style.palette
    for column in scene.layout.columns:
        is_hero = column.role == "hero"
        fill = palette.panel_hero_fill if is_hero else palette.panel_fill
        stroke = palette.deep_red_light if is_hero else palette.rule
        stroke_width = style.hero_stroke_width if is_hero else style.panel_stroke_width
        p.rounded_rect(
            drawing,
            column.bounds,
            fill=fill,
            stroke=stroke,
            radius=style.panel_radius,
            stroke_width=stroke_width,
        )
        inner = column.bounds.inset(12, 12)
        p.rounded_rect(
            drawing,
            inner,
            fill="none",
            stroke="#eef2f7" if not is_hero else "#fde6e3",
            radius=style.panel_radius - 2,
            stroke_width=0.8,
            opacity=0.72,
        )
        title_size = style.typography.hero_title_size if is_hero else style.typography.support_title_size
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


def _draw_layout_flow(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: LayoutFlow = obj.payload
    p.begin_semantic_group(drawing, obj, f"direction={payload.direction} arrow_count={len(payload.arrow_pairs)}")
    for start, end in payload.arrow_pairs:
        p.arrow(
            drawing,
            start,
            end,
            style.palette.muted,
            width=1.7,
            head_length=15,
            head_width=15,
            opacity=0.25,
            attrs={"data-panel-role": "global-flow-arrow", "data-flow-role": payload.direction},
        )
    p.end_semantic_group(drawing)


def _draw_sulfur_polymer_origin(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: SulfurPolymerOrigin = obj.payload
    col = _column(scene, obj.column)
    column = _column_model(scene, obj.column)
    palette = style.palette
    p.begin_semantic_group(
        drawing,
        obj,
        f"s8_atoms={payload.s8_atom_count} chain_atoms={payload.chain_atom_count} swatches={len(payload.swatches)} local_boxes={len(column.local_boxes)}",
    )

    icon = column.box("origin_icon")
    p.rounded_rect(drawing, icon, fill="#173967", stroke="#0d2341", radius=3, stroke_width=1.0)
    for node in (Point(icon.x + 14, icon.y + 18), Point(icon.x + 30, icon.y + 18), Point(icon.x + 22, icon.y + 32)):
        drawing.append(draw.Circle(node.x, node.y, 5, fill="#ffffff", opacity=0.9))
    drawing.append(draw.Line(icon.x + 14, icon.y + 18, icon.x + 30, icon.y + 18, stroke="#ffffff", stroke_width=1.4))
    drawing.append(draw.Line(icon.x + 14, icon.y + 18, icon.x + 22, icon.y + 32, stroke="#ffffff", stroke_width=1.4))
    drawing.append(draw.Line(icon.x + 30, icon.y + 18, icon.x + 22, icon.y + 32, stroke="#ffffff", stroke_width=1.4))

    ring_box = column.box("s8_ring")
    ring_center = ring_box.center
    ring_radius = min(ring_box.width, ring_box.height) * 0.41
    ring_points = [
        Point(
            ring_center.x + ring_radius * math.cos(2 * math.pi * i / payload.s8_atom_count),
            ring_center.y + ring_radius * math.sin(2 * math.pi * i / payload.s8_atom_count),
        )
        for i in range(payload.s8_atom_count)
    ]
    for index, current in enumerate(ring_points):
        nxt = ring_points[(index + 1) % len(ring_points)]
        drawing.append(draw.Line(current.x, current.y, nxt.x, nxt.y, stroke=palette.sulfur_brown, stroke_width=1.55))
    for atom in ring_points:
        p.sulfur_atom(drawing, atom, 6.7, style)
    p.text(drawing, "S8", ring_center.x, ring_center.y + 82, 16, fill=palette.ink, anchor="middle", style=style)

    reaction = column.box("reaction_arrow")
    arrow_y = reaction.center.y
    p.arrow(drawing, Point(reaction.x, arrow_y), Point(reaction.right, arrow_y), palette.ink, width=1.4, head_length=12, head_width=9)
    p.text(drawing, payload.heat_label, reaction.center.x, reaction.y - 3, 12.8, fill=palette.ink, anchor="middle", style=style)

    chain_box = column.box("sulfur_chain")
    chain_start = Point(chain_box.x, chain_box.center.y)
    spacing = chain_box.width / max(payload.chain_atom_count - 1, 1)
    chain_points = [
        Point(chain_start.x + i * spacing, chain_start.y + (14 if i % 2 else -2))
        for i in range(payload.chain_atom_count)
    ]
    for start, end in zip(chain_points, chain_points[1:], strict=False):
        drawing.append(draw.Line(start.x, start.y, end.x, end.y, stroke=palette.sulfur_brown, stroke_width=1.6))
    for atom in chain_points:
        p.sulfur_atom(drawing, atom, 6.2, style)
    p.text(drawing, payload.chain_label, chain_box.center.x, chain_box.bottom + 15, 12.2, fill=palette.ink, anchor="middle", style=style)

    ramp = column.box("composition_ramp")
    p.text(drawing, "S60", col.x + 38, ramp.y + 7, 15, fill=palette.ink, anchor="middle", style=style)
    p.text(drawing, "S85", ramp.right + 38, ramp.y + 7, 15, fill=palette.ink, anchor="middle", style=style)
    drawing.append(draw.Rectangle(ramp.x, ramp.y, ramp.width, ramp.height, fill="url(#sulfurSwatch)", stroke=palette.sulfur_brown, stroke_width=0.9))
    p.arrow(drawing, Point(ramp.right - 3, ramp.center.y), Point(ramp.right + 22, ramp.center.y), palette.deep_red_mid, width=8, head_length=18, head_width=20)
    p.text(drawing, "Increasing sulfur content", ramp.center.x, ramp.y + 31, 12.2, fill=palette.ink, italic=True, anchor="middle", style=style)

    bullet_box = column.box("bullet_list")
    relation_y = bullet_box.y + 30
    relation_labels = (
        ("S-rich segments", bullet_box.x + 45, "origin-s-rich-segments"),
        ("S-chain length", bullet_box.center.x, None),
        ("localized traps", bullet_box.right - 52, "origin-localized-traps"),
    )
    for index, (label, x, causal_role) in enumerate(relation_labels):
        drawing.append(draw.Circle(x, relation_y, 3.0, fill=palette.sulfur_brown, opacity=0.72))
        _panel_text(
            drawing,
            label,
            x,
            relation_y + 27,
            12.6,
            role="origin-relation",
            fill=palette.ink if index < 2 else palette.deep_red,
            italic=True,
            anchor="middle",
            weight="700" if index == 2 else None,
            causal_role=causal_role,
            style=style,
        )
    p.arrow(drawing, Point(relation_labels[0][1] + 48, relation_y), Point(relation_labels[1][1] - 45, relation_y), palette.muted, width=1.0, head_length=7, head_width=6, opacity=0.62)
    p.arrow(drawing, Point(relation_labels[1][1] + 42, relation_y), Point(relation_labels[2][1] - 48, relation_y), palette.deep_red_mid, width=1.1, head_length=7, head_width=6, opacity=0.72)
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


def _draw_deep_trap_hero(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: DeepTrapHero = obj.payload
    col = _column(scene, obj.column)
    palette = style.palette
    p.begin_semantic_group(
        drawing,
        obj,
        f"hero_ratio={payload.hero_ratio:g} band_id={payload.band_object_id} trap_id={payload.trap_object_id} dos_id={payload.dos_object_id}",
    )
    p.text(drawing, payload.subtitle, col.center.x, col.y + 78, style.typography.subtitle_size, fill=palette.muted, anchor="middle", style=style)
    callout = _local_box(scene, obj.column, "hero_callout")
    compact_callout = Rect(callout.x + 18, callout.y + 5, callout.width - 36, callout.height - 16)
    p.rounded_rect(drawing, compact_callout, fill="#fff8f7", stroke=palette.deep_red_light, radius=6, stroke_width=0.75, opacity=0.82)
    caption_lines = (
        (payload.converged_picture_label.replace("converged", "Converged", 1), "hero-converged-picture"),
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


def _draw_band_diagram(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: BandDiagram = obj.payload
    area = _band_area(scene)
    palette = style.palette
    p.begin_semantic_group(drawing, obj, f"lumo_y={payload.lumo.y:.2f} homo_y={payload.homo.y:.2f}")
    p.arrow(drawing, Point(area.x + 20, area.bottom - 2), Point(area.x + 20, area.y + 6), palette.ink, width=style.schematic_stroke_width)
    drawing.append(draw.Line(area.x + 20, area.bottom - 2, area.x + 20, area.y + 20, stroke="none", **_hero_attrs("energy-axis")))
    drawing.append(draw.Text(payload.energy_axis_label, 11.5, 0, 0, fill=palette.ink, font_family=style.typography.family, text_anchor="middle", transform=f"translate({area.x - 5} {area.center.y}) rotate(-90)", **_hero_attrs("energy-axis")))
    for edge in (payload.lumo, payload.homo):
        y = area.y + edge.y * area.height
        rect = Rect(area.x + 72, y - 15, area.width - 100, 30)
        p.rounded_rect(drawing, rect, fill="#ffffff", stroke="#b9c0ca", radius=3, stroke_width=0.85, opacity=0.96)
        drawing.append(draw.Rectangle(rect.x, rect.y, rect.width, rect.height, rx=3, ry=3, fill="none", stroke="none", **_hero_attrs("band-edge", source=edge.label)))
        p.text(drawing, edge.label, rect.center.x, rect.y + 20.5, 15.0, fill=palette.ink, weight="700", anchor="middle", style=style)
    gap_y = area.center.y
    drawing.append(draw.Line(area.x + 76, gap_y, area.right - 18, gap_y, stroke=palette.muted, stroke_width=1.0, stroke_dasharray="5 5", opacity=0.42, **_hero_attrs("trap-track", source=payload.gap_label)))
    p.end_semantic_group(drawing)


def _draw_trap_level_set(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
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
    shallow_points = _draw_reference_trap_states(
        drawing,
        area,
        payload.shallow_positions,
        center_x=shallow_x,
        width=68,
        color=palette.shallow_blue,
        marker_radius=payload.shallow_radius * 0.88,
        state_role="shallow-trap-state",
        track_role="trap-track",
        opacity=0.78,
    )
    deep_points = _draw_reference_trap_states(
        drawing,
        area,
        payload.deep_positions,
        center_x=deep_x,
        width=96,
        color=palette.deep_red,
        marker_radius=payload.deep_radius * 0.88,
        state_role="deep-trap-state",
        track_role="trap-track",
        opacity=0.82,
    )
    shallow_label_y = area.y + payload.shallow_positions[0] * area.height + 6
    deep_label_y = area.y + payload.deep_positions[2] * area.height + 8
    p.multiline_text(drawing, (payload.shallow_label.lower(), "states"), shallow_x - 88, shallow_label_y - 7, 13.0, 15.5, fill=palette.shallow_blue, style=style)
    p.multiline_text(drawing, (payload.deep_label.lower(), "states"), deep_x - 99, deep_label_y - 8, 13.5, 16.0, fill=palette.deep_red, style=style)

    p.end_semantic_group(drawing)


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
        drawing.append(draw.Line(start.x, start.y, end.x, end.y, stroke=color, stroke_width=1.15, stroke_dasharray="10 8", opacity=opacity, **_hero_attrs(track_role)))
        jitter = ((index % 3) - 1) * marker_radius * 0.55
        marker_x = start.x + width * 0.18 + jitter
        drawing.append(draw.Circle(marker_x, y, marker_radius, fill=color, stroke="#ffffff", stroke_width=0.65, opacity=opacity, **_hero_attrs(state_role)))
        points.append(Point(marker_x, y))
    return tuple(points)


def _double_arrow(drawing: draw.Drawing, start: Point, end: Point, color: str, *, role: str) -> None:
    drawing.append(draw.Line(start.x, start.y, end.x, end.y, stroke=color, stroke_width=1.0, opacity=0.82, **_hero_attrs(role)))
    for tip, base in ((start, end), (end, start)):
        angle = math.atan2(base.y - tip.y, base.x - tip.x)
        head_length = 8.0
        head_width = 7.0
        back = Point(tip.x + head_length * math.cos(angle), tip.y + head_length * math.sin(angle))
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


def _draw_dos_lobes(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
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
    p.draw_reference_dos_schematic(
        drawing,
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
    p.end_semantic_group(drawing)


def _evidence_badge_rect(scene: Scene, object_id: str) -> Rect:
    obj = scene.object_by_id(object_id)
    col = _column(scene, obj.column)
    trio: EvidenceTrio = scene.object_by_kind("EvidenceTrio").payload
    index_by_id = {modality.object_id: index for index, modality in enumerate(trio.modalities)}
    if object_id in index_by_id and len(trio.modalities) == 2:
        index = index_by_id[object_id]
        return _local_box(scene, obj.column, "pe_plot" if index == 0 else "decay_plot")
    if object_id == "ispd_plot":
        return _local_box(scene, obj.column, "ispd_plot")
    return Rect(col.x + 48, col.y + 164, 214, 214)


def _draw_evidence_trio(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: EvidenceTrio = obj.payload
    col = _column(scene, obj.column)
    palette = style.palette
    modalities = ",".join(modality.label for modality in payload.modalities)
    p.begin_semantic_group(drawing, obj, f"modalities={modalities} badge_count={len(payload.modalities)}")
    for modality in payload.modalities:
        rect = _evidence_badge_rect(scene, modality.object_id)
        title = modality.title.replace("hysteresis", "response").replace("I(t) proportional t^-n", "Current decay")
        title_color = modality.accent if modality.label == "I(t)" else palette.ink
        p.text(
            drawing,
            title,
            rect.center.x,
            rect.y - 17,
            style.typography.section_label_size,
            fill=title_color,
            anchor="middle",
            style=style,
        )
        drawing.append(
            draw.Line(
                rect.x + 22,
                rect.y - 8,
                rect.right - 22,
                rect.y - 8,
                stroke=modality.accent,
                stroke_width=1.0,
                opacity=0.30,
            )
        )
    cue_y = col.bottom - 30
    drawing.append(draw.Line(col.x + 72, cue_y - 24, col.right - 72, cue_y - 24, stroke=palette.rule, stroke_width=0.9, opacity=0.74))
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


def _plot_attrs(plot_id: str, role: str, *, axis: str | None = None) -> dict[str, object]:
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
        _draw_plot_text(drawing, plot_id, "axis-label", label, fill=palette.ink, style=style)


def _draw_plot_grid(drawing: draw.Drawing, tick: PlotTick, frame: Rect, color: str) -> None:
    if tick.axis == "x":
        drawing.append(draw.Line(tick.point.x, frame.y, tick.point.x, frame.bottom, stroke=color, stroke_width=0.45, opacity=0.55))
    else:
        drawing.append(draw.Line(frame.x, tick.point.y, frame.right, tick.point.y, stroke=color, stroke_width=0.45, opacity=0.55))


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


def _draw_plot_tick_label(drawing: draw.Drawing, plot_id: str, tick: PlotTick, frame: Rect, *, style: FigureStyle) -> None:
    if tick.label is None:
        return
    if tick.axis == "x":
        label = PlotLabel(tick.label, Point(tick.point.x, frame.bottom + 16), 7.4, "middle")
    else:
        label = PlotLabel(tick.label, Point(frame.x - 7, tick.point.y + 2.7), 7.4, "end")
    _draw_plot_text(drawing, plot_id, "tick-label", label, fill=style.palette.ink, style=style, axis=tick.axis)


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
    drawing.append(draw.Text(label.value, label.size, label.point.x, label.point.y, **attrs))


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
    back = Point(end.x - head_length * math.cos(angle), end.y - head_length * math.sin(angle))
    nx = math.sin(angle)
    ny = -math.cos(angle)
    _plot_line(drawing, plot_id, "schematic-axis", start, back, color=color, width=width, opacity=opacity)
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


def _draw_pe_hysteresis(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: PEHysteresisPlot = obj.payload
    bounds = _evidence_badge_rect(scene, obj.id).inset(4, 16)
    plan = pe_hysteresis_plan(
        bounds,
        loop_width=payload.loop_width,
        loop_height=payload.loop_height,
        remanence=payload.remanence,
        samples_per_branch=payload.samples_per_branch,
        label="P-E loop",
    )
    p.begin_semantic_group(
        drawing,
        obj,
        "pe_model={} loop_width={:g} loop_height={:g} remanence={:g} samples={} "
        "plot_grammar=matplotlib_schematic_calculator major_ticks={} minor_ticks={}".format(
            payload.model,
            payload.loop_width,
            payload.loop_height,
            payload.remanence,
            payload.samples_per_branch,
            len(plan.major_ticks),
            len(plan.minor_ticks),
        ),
    )
    frame = plan.frame
    palette = style.palette
    _plot_arrow_axis(drawing, obj.id, Point(frame.x + 8, frame.center.y), Point(frame.right - 4, frame.center.y), color=palette.ink, width=1.1, opacity=0.80)
    _plot_arrow_axis(drawing, obj.id, Point(frame.center.x, frame.bottom - 6), Point(frame.center.x, frame.y + 4), color=palette.ink, width=1.1, opacity=0.80)
    _plot_line(drawing, obj.id, "schematic-guide", Point(frame.x + 8, frame.center.y), Point(frame.right - 12, frame.center.y), color=palette.muted, width=0.9, opacity=0.42, dash="5 4")
    _plot_line(drawing, obj.id, "schematic-guide", Point(frame.center.x, frame.y + 8), Point(frame.center.x, frame.bottom - 8), color=palette.muted, width=0.9, opacity=0.42, dash="5 4")
    drawing.append(
        _plot_polyline(
            plan.curve_points,
            plot_id=obj.id,
            role="schematic-curve",
            fill="none",
            stroke=payload.color,
            stroke_width=style.plot_stroke_width + 0.35,
            close=True,
            opacity=0.96,
        )
    )
    remanent_x = frame.center.x + frame.width * 0.13
    remanent_y = frame.center.y - frame.height * 0.20
    _plot_line(
        drawing,
        obj.id,
        "schematic-guide",
        Point(remanent_x, frame.center.y),
        Point(remanent_x, remanent_y),
        color=payload.color,
        width=0.85,
        opacity=0.58,
        dash="4 3",
    )
    _plot_label(drawing, obj.id, "Pr", Point(remanent_x + 5, remanent_y - 4), 9.8, fill=payload.color, style=style, italic=True)
    _plot_label(drawing, obj.id, "P", Point(frame.x + 1, frame.y + 16), 12.8, fill=palette.ink, style=style, italic=True)
    _plot_label(drawing, obj.id, "E", Point(frame.right - 3, frame.center.y - 7), 12.8, fill=palette.ink, style=style, italic=True, anchor="end")
    p.end_semantic_group(drawing)


def _draw_power_law_decay(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: PowerLawDecayPlot = obj.payload
    bounds = _evidence_badge_rect(scene, obj.id).inset(4, 16)
    plan = power_law_decay_plan(
        bounds,
        slope=payload.slope,
        log_t_min=payload.log_t_min,
        log_t_max=payload.log_t_max,
        log_i_top=payload.log_i_top,
        log_i_bottom=payload.log_i_bottom,
        samples=payload.samples,
        label=payload.label,
    )
    p.begin_semantic_group(
        drawing,
        obj,
        "decay_model={} slope={:g} log_t={:g}:{:g} samples={} label={} "
        "plot_grammar=matplotlib_schematic_loglog_calculator major_ticks={} minor_ticks={}".format(
            payload.model,
            payload.slope,
            payload.log_t_min,
            payload.log_t_max,
            payload.samples,
            payload.label,
            len(plan.major_ticks),
            len(plan.minor_ticks),
        ),
    )
    frame = plan.frame
    palette = style.palette
    _plot_arrow_axis(drawing, obj.id, Point(frame.x + 8, frame.bottom - 6), Point(frame.right - 3, frame.bottom - 6), color=palette.ink, width=1.1, opacity=0.80)
    _plot_arrow_axis(drawing, obj.id, Point(frame.x + 8, frame.bottom - 6), Point(frame.x + 8, frame.y + 4), color=palette.ink, width=1.1, opacity=0.80)
    x_tick_candidates = [tick for tick in plan.major_ticks if tick.axis == "x"]
    for tick in x_tick_candidates[:: max(1, len(x_tick_candidates) // 4)]:
        _plot_line(
            drawing,
            obj.id,
            "schematic-decade-hint",
            Point(tick.point.x, frame.bottom - 6),
            Point(tick.point.x, frame.bottom - 1),
            color=palette.muted,
            width=0.78,
            opacity=0.55,
        )
    y_tick_candidates = [tick for tick in plan.major_ticks if tick.axis == "y"]
    for tick in y_tick_candidates[:: max(1, len(y_tick_candidates) // 4)]:
        _plot_line(
            drawing,
            obj.id,
            "schematic-decade-hint",
            Point(frame.x + 3, tick.point.y),
            Point(frame.x + 8, tick.point.y),
            color=palette.muted,
            width=0.78,
            opacity=0.55,
        )
    for segment in plan.guide_segments:
        _plot_line(drawing, obj.id, "schematic-guide", segment.start, segment.end, color=payload.color, width=1.15, opacity=0.72, dash="4 3")
    drawing.append(_plot_polyline(plan.curve_points, plot_id=obj.id, role="schematic-curve", fill="none", stroke=payload.color, stroke_width=style.plot_stroke_width + 0.55))
    highlight = tuple(Point(point.x, point.y + 0.9) for point in plan.curve_points)
    drawing.append(_plot_polyline(highlight, plot_id=obj.id, role="schematic-curve", fill="none", stroke="#ffffff", stroke_width=0.65, opacity=0.42))
    _plot_label(drawing, obj.id, payload.label, Point(frame.x + frame.width * 0.50, frame.y + 28), 12.0, fill=payload.color, style=style, weight="700")
    _plot_label(drawing, obj.id, "slope = -n", Point(frame.x + frame.width * 0.36, frame.y + frame.height * 0.73), 9.8, fill=payload.color, style=style)
    _plot_label(
        drawing,
        obj.id,
        "extract n",
        Point(frame.x + frame.width * 0.70, frame.y + frame.height * 0.64),
        10.8,
        fill=payload.color,
        style=style,
        italic=True,
        causal_role="decay-extract-n",
    )
    _plot_label(drawing, obj.id, "log t", Point(frame.right - 4, frame.bottom + 13), 10.0, fill=palette.ink, style=style, anchor="end", italic=True)
    _plot_label(drawing, obj.id, "log I", Point(frame.x - 1, frame.y + 17), 10.0, fill=palette.ink, style=style, italic=True)
    p.end_semantic_group(drawing)


def _draw_ispd_plot(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
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
        shallow_label="",
        deep_label="",
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
        title="",
        show_lobe_labels=False,
        depth_label_side="right",
        compact=True,
        style=style,
    )
    p.end_semantic_group(drawing)


def _draw_trap_model_flow(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: TrapModelFlow = obj.payload
    col = _column(scene, obj.column)
    palette = style.palette
    display_steps = payload.causal_chain or payload.steps
    causal_roles = (
        "interpretation-step-power-law",
        "interpretation-step-exponent-n",
        "interpretation-step-debye",
        "interpretation-step-tau-d",
        "interpretation-step-trap-depth-distribution",
    )
    p.begin_semantic_group(drawing, obj, f"step_count={len(display_steps)} causal_chain={'|'.join(display_steps)}")
    flow_strip = _local_box(scene, obj.column, "flow_strip")
    box_w = flow_strip.width / len(display_steps)
    baseline_y = flow_strip.bottom - 5
    drawing.append(draw.Line(flow_strip.x + 8, baseline_y, flow_strip.right - 8, baseline_y, stroke=palette.rule, stroke_width=1.15, opacity=0.88))
    previous_center: Point | None = None
    for index, step in enumerate(display_steps):
        center = Point(flow_strip.x + index * box_w + box_w / 2 - 4, flow_strip.center.y)
        step_box = Rect(center.x - box_w * 0.39, flow_strip.y - 8, box_w * 0.78, flow_strip.height + 10)
        p.rounded_rect(
            drawing,
            step_box,
            fill="#ffffff",
            stroke=palette.shallow_blue if index == 0 else palette.rule,
            radius=4,
            stroke_width=0.85 if index == 0 else 0.72,
            opacity=0.94,
        )
        if step == "I(t) ~ t^-n":
            display_step = "I(t) ~\nt^-n"
        elif step == "Debye exp(-t/tau)":
            display_step = "Debye\nexp(-t/tau)"
        else:
            display_step = step
        lines = display_step.split("\n")
        causal_role = causal_roles[index] if index < len(causal_roles) else None
        if len(lines) == 1:
            _panel_text(
                drawing,
                step,
                center.x,
                flow_strip.y + 14,
                12.0 if len(step) <= 8 else 10.8,
                role="interpretation-causal-step",
                fill=palette.ink,
                anchor="middle",
                weight="700" if step == "n" else None,
                causal_role=causal_role,
                style=style,
            )
        else:
            for line_index, line in enumerate(lines):
                _panel_text(
                    drawing,
                    line,
                    center.x,
                    flow_strip.y + 9 + line_index * 12.0,
                    10.8,
                    role="interpretation-causal-step",
                    fill=palette.ink,
                    anchor="middle",
                    causal_role=causal_role,
                    style=style,
                )
        drawing.append(draw.Circle(center.x, baseline_y, 3.1, fill=palette.muted, opacity=0.62))
        if previous_center:
            p.arrow(drawing, Point(previous_center.x + 13, baseline_y), Point(center.x - 15, baseline_y), palette.muted, width=1.05, head_length=8, head_width=6.5, opacity=0.72)
        previous_center = center

    decay: PowerLawDecayPlot = scene.object_by_kind("PowerLawDecayPlot").payload
    plot = _local_box(scene, obj.column, "decay_plot")
    axis_origin = Point(plot.x + 18, plot.y + 18)
    axis_w = plot.width - 32
    axis_h = plot.height - 28
    p.mini_axis(drawing, axis_origin, axis_w, axis_h, palette.ink)
    for fraction in (0.22, 0.42, 0.62, 0.82):
        tick_x = axis_origin.x + axis_w * fraction
        drawing.append(draw.Line(tick_x, axis_origin.y + axis_h, tick_x, axis_origin.y + axis_h + 5, stroke=palette.muted, stroke_width=0.7, opacity=0.48))
    for fraction in (0.24, 0.45, 0.66, 0.84):
        tick_y = axis_origin.y + axis_h * fraction
        drawing.append(draw.Line(axis_origin.x - 5, tick_y, axis_origin.x, tick_y, stroke=palette.muted, stroke_width=0.7, opacity=0.48))
    curve_points = power_law_loglog_points(
        Rect(axis_origin.x, axis_origin.y, axis_w, axis_h),
        slope=decay.slope,
        log_t_min=decay.log_t_min,
        log_t_max=decay.log_t_max,
        log_i_top=decay.log_i_top,
        log_i_bottom=decay.log_i_bottom,
        samples=decay.samples,
    )
    drawing.append(p.polyline_path(curve_points, fill="none", stroke=decay.color, stroke_width=2.8))
    guide_point = curve_points[int(len(curve_points) * 0.28)]
    drawing.append(
        draw.Line(
            guide_point.x,
            guide_point.y,
            guide_point.x,
            guide_point.y + 52,
            stroke=decay.color,
            stroke_width=1.2,
            stroke_dasharray="6 4",
            opacity=0.75,
        )
    )
    p.text(drawing, decay.label, curve_points[0].x + 64, curve_points[0].y + 24, 13.2, fill=decay.color, weight="700", style=style)
    p.text(drawing, "slope = -n", guide_point.x - 22, guide_point.y + 70, 10.4, fill=decay.color, style=style)
    p.text(drawing, "t (s)", axis_origin.x + plot.width - 48, axis_origin.y + plot.height - 5, 10.2, fill=palette.ink, style=style)

    deb = _local_box(scene, obj.column, "debye_tau")
    deb_box = Rect(deb.x - 11, deb.y - 14, deb.width + 22, 43)
    p.rounded_rect(drawing, deb_box, fill="#ffffff", stroke=palette.rule, radius=4, stroke_width=0.8, opacity=0.96)
    p.text(drawing, "Debye", deb.center.x, deb.y - 1, 10.8, fill=palette.ink, italic=True, anchor="middle", style=style)
    p.text(drawing, "exp(-t/tau)", deb.center.x, deb.y + 16, 10.2, fill=palette.ink, italic=True, anchor="middle", style=style)
    p.arrow(drawing, Point(deb.center.x, deb.y + 53), Point(deb.center.x, deb.y + 86), palette.ink, width=1.25, head_length=9, head_width=8)
    p.text(drawing, "tau_d", deb.center.x, deb.y + 112, 14.0, fill=palette.ink, italic=True, anchor="middle", style=style)

    callout = _local_box(scene, obj.column, "interpretation_callout")
    conclusion_band = Rect(callout.x + 10, callout.y + 2, callout.width - 20, callout.height - 8)
    p.rounded_rect(drawing, conclusion_band, fill="#f7f9fc", stroke="#dfe6f1", radius=5, stroke_width=0.85, opacity=0.96)
    for index, line in enumerate(("Convergence to deep traps (tau_d) explains the", "extended repulsion.")):
        _panel_text(
            drawing,
            line,
            callout.center.x,
            callout.y + 25 + index * 18,
            13.4,
            role="interpretation-conclusion panel-conclusion",
            fill=palette.ink if index == 0 else palette.muted,
            italic=True,
            anchor="middle",
            style=style,
        )
    p.end_semantic_group(drawing)


def _draw_macroscopic_probe(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: MacroscopicProbe = obj.payload
    col = _column(scene, obj.column)
    palette = style.palette
    p.begin_semantic_group(drawing, obj, f"frames={len(payload.frames)} force_id={payload.force_object_id} visual_layout=reference_probe")
    cantilever: PolymerCantilever = scene.object_by_id(payload.cantilever_object_id).payload
    frame = cantilever.frame_bounds[-1]
    p.text(drawing, "Cantilever", frame.x + 84, frame.y + 40, 14, fill=palette.ink, anchor="middle", style=style)
    p.text(drawing, "(probe)", frame.x + 84, frame.y + 58, 12.5, fill=palette.ink, anchor="middle", style=style)
    callout = _local_box(scene, obj.column, "probe_callout")
    drawing.append(draw.Line(callout.x + 22, callout.y + 4, callout.right - 22, callout.y + 4, stroke=palette.deep_red_light, stroke_width=1.0, opacity=0.84))
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
        "Like-charge repulsion drives the cantilever away from +V.",
        callout.center.x,
        callout.y + 56,
        12.8,
        role="probe-conclusion panel-conclusion",
        fill=palette.ink,
        anchor="middle",
        style=style,
    )
    p.end_semantic_group(drawing)


def _draw_polymer_cantilever(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: PolymerCantilever = obj.payload
    palette = style.palette
    p.begin_semantic_group(
        drawing,
        obj,
        f"charge_sign={payload.charge_sign} charge_count={len(payload.charge_positions)} initial_bend={payload.initial_bend} repulsive_bend={payload.repulsive_bend}",
    )
    frame = payload.frame_bounds[-1]
    _cantilever_frame(drawing, frame, payload, style=style)
    for index, charge in enumerate(payload.charge_positions):
        color = palette.deep_red_mid if index < len(payload.charge_positions) - 1 else palette.sulfur_brown
        p.charge_marker(drawing, charge, payload.charge_sign, 9.2, color, style)
    p.end_semantic_group(drawing)


def _cantilever_frame(drawing: draw.Drawing, frame: Rect, payload: PolymerCantilever, *, style: FigureStyle) -> None:
    palette = style.palette
    arm = draw.Path(fill="none", stroke="#657182", stroke_width=9, stroke_linecap="square")
    arm.M(frame.x + 32, frame.y + 30)
    arm.L(frame.x + 86, frame.y + 2)
    drawing.append(arm)
    p.rounded_rect(drawing, Rect(frame.x + 24, frame.y + 34, 56, 9), fill="#8e98a6", stroke="#5c6672", radius=1, stroke_width=0.8)
    ground_x = frame.x + 74
    ground_y = frame.y + 76
    drawing.append(draw.Line(ground_x, frame.y + 44, ground_x, ground_y, stroke=palette.ink, stroke_width=1.4))
    for index, width in enumerate((28, 18, 8)):
        yy = ground_y + index * 8
        drawing.append(draw.Line(ground_x - width / 2, yy, ground_x + width / 2, yy, stroke=palette.ink, stroke_width=1.2))

    clamp = Rect(frame.x + 130, frame.y + 64, 76, 21)
    p.rounded_rect(drawing, clamp, fill="#a3acb7", stroke="#5d6670", radius=2, stroke_width=0.9)
    for xx in (clamp.x + 14, clamp.x + 30, clamp.x + 46, clamp.x + 62):
        drawing.append(draw.Line(xx, clamp.y + 3, xx, clamp.bottom - 3, stroke="#ffffff", stroke_width=0.6, opacity=0.32))

    beam = draw.Path(fill="none", stroke="#d5a534", stroke_width=23, stroke_linecap="round")
    beam.M(frame.x + 158, frame.y + 82)
    beam.C(frame.x + 160, frame.y + 140, frame.x + 190, frame.y + 224, frame.x + 268, frame.y + 274)
    drawing.append(beam)
    beam_highlight = draw.Path(fill="none", stroke="#f0d779", stroke_width=6, stroke_linecap="round", opacity=0.46)
    beam_highlight.M(frame.x + 159, frame.y + 83)
    beam_highlight.C(frame.x + 160, frame.y + 141, frame.x + 190, frame.y + 222, frame.x + 266, frame.y + 270)
    drawing.append(beam_highlight)

    electrode_x = frame.right - 48
    for dy, pull in ((108, -8), (135, 2), (162, 10), (190, 16), (220, 22)):
        field = draw.Path(fill="none", stroke="#b5bcc7", stroke_width=0.8, stroke_dasharray="5 7", opacity=0.36)
        field.M(electrode_x - 12, frame.y + dy)
        field.C(electrode_x - 92, frame.y + dy + 30, frame.x + 258, frame.y + dy + pull, frame.x + 196, frame.y + dy - 6)
        drawing.append(field)


def _draw_electrode(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: Electrode = obj.payload
    palette = style.palette
    p.begin_semantic_group(
        drawing,
        obj,
        f"sign={payload.sign} center_x={payload.center.x:.1f} center_y={payload.center.y:.1f}",
    )
    p.rounded_rect(drawing, payload.bounds, fill="#9aa4af", stroke="#505965", radius=2, stroke_width=1.0)
    for yy in (payload.bounds.y + 34, payload.bounds.y + 86, payload.bounds.y + 138, payload.bounds.y + 190, payload.bounds.y + 242):
        drawing.append(draw.Line(payload.bounds.x + 7, yy, payload.bounds.right - 7, yy, stroke="#ffffff", stroke_width=0.9, opacity=0.38))
    p.text(drawing, f"{payload.sign} V", payload.bounds.right + 10, payload.bounds.y + 54, 16, fill=palette.deep_red, weight="700", style=style)
    p.end_semantic_group(drawing)


def _draw_force_arrow(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
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
    p.arrow(drawing, payload.start, payload.end, style.palette.deep_red, width=7.2, head_length=26, head_width=27)
    _panel_text(
        drawing,
        "Force on cantilever",
        (payload.start.x + payload.end.x) / 2,
        payload.start.y - 34,
        16,
        role="probe-force-label",
        fill=style.palette.deep_red,
        weight="700",
        italic=True,
        anchor="middle",
        style=style,
    )
    p.end_semantic_group(drawing)


def _draw_maxwell_attraction_cue(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: MaxwellAttractionCue = obj.payload
    p.begin_semantic_group(
        drawing,
        obj,
        f"maxwell_role={payload.role} start_x={payload.start.x:.1f} end_x={payload.end.x:.1f}",
    )
    p.arrow(drawing, payload.start, payload.end, style.palette.shallow_blue, width=2.4, head_length=15, head_width=13, opacity=0.62)
    p.text(
        drawing,
        payload.label,
        payload.end.x + 18,
        payload.end.y + 26,
        11.2,
        fill=style.palette.shallow_blue,
        anchor="middle",
        style=style,
    )
    p.end_semantic_group(drawing)


def _render_png(svg_path: Path, png_path: Path, width: int, height: int) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("rsvg-convert"):
        subprocess.run(
            ["rsvg-convert", "-w", str(width), "-h", str(height), str(svg_path), "-o", str(png_path)],
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
