from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import drawsvg as draw

from engine.domain_primitives import (
    BandDiagram,
    DOSLobes,
    Electrode,
    EvidenceTrio,
    ForceArrow,
    LayoutFlow,
    MacroscopicProbe,
    PEHysteresisPlot,
    PolymerCantilever,
    PowerLawDecayPlot,
    SulfurPolymerOrigin,
    TrapLevelSet,
    TrapModelFlow,
)
from engine.scene import Point, Rect, Scene, SemanticObject
from engine.scientific_plots import ScientificPlotPlan, pe_hysteresis_plan, power_law_decay_plan
from engine.style import DEFAULT_STYLE, FigureStyle
from engine import primitives as p
from fig_probe_02_scene import build_scene


ROOT = Path(__file__).resolve().parents[1]
SVG_OUT = ROOT / "fig_probe_02_semantic.svg"
PNG_OUT = ROOT / "fig_probe_02_semantic.png"


def _role(role: str, **extra: object) -> dict[str, object]:
    attrs: dict[str, object] = {"data-probe2-role": role}
    attrs.update(extra)
    return attrs


def build_drawing(scene: Scene, style: FigureStyle = DEFAULT_STYLE) -> draw.Drawing:
    drawing = draw.Drawing(scene.width, scene.height)
    drawing.append(draw.Rectangle(0, 0, scene.width, scene.height, fill=style.palette.white))
    drawing.append(p.style_defs())
    _draw_header(drawing, style)
    _draw_panels(drawing, scene, style)
    for obj in scene.objects:
        renderer = {
            "LayoutFlow": _draw_layout_flow,
            "SulfurPolymerOrigin": _draw_material_panel,
            "EvidenceTrio": _draw_evidence_panel,
            "PEHysteresisPlot": _draw_pe_plot,
            "PowerLawDecayPlot": _draw_decay_plot,
            "BandDiagram": _draw_band_diagram,
            "TrapLevelSet": _draw_trap_states,
            "DOSLobes": _draw_dos_profile,
            "TrapModelFlow": _draw_readout_panel,
            "MacroscopicProbe": _draw_device_panel,
            "PolymerCantilever": _draw_cantilever,
            "Electrode": _draw_electrode,
            "ForceArrow": _draw_force_arrow,
        }[obj.kind]
        renderer(drawing, scene, obj, style)
    return drawing


def render_all(scene: Scene | None = None) -> None:
    scene = build_scene() if scene is None else scene
    drawing = build_drawing(scene)
    p.save_svg(drawing, SVG_OUT)
    _render_png(SVG_OUT, PNG_OUT, scene.width, scene.height)


def _column(scene: Scene, index: int):
    return scene.layout.columns[index - 1]


def _draw_header(drawing: draw.Drawing, style: FigureStyle) -> None:
    p.text(drawing, "Probe 02 | Sulfur-network charge-retention mechanism", 54, 48, 24, fill=style.palette.ink, weight="700", style=style)
    p.text(
        drawing,
        "Composition, electrical retention, trap-spectrum readout, and device response converge on deep trap population.",
        54,
        74,
        12.8,
        fill=style.palette.muted,
        style=style,
    )


def _draw_panels(drawing: draw.Drawing, scene: Scene, style: FigureStyle) -> None:
    for column in scene.layout.columns:
        is_center = column.role == "hero"
        p.rounded_rect(
            drawing,
            column.bounds,
            fill=style.palette.panel_hero_fill if is_center else style.palette.panel_fill,
            stroke=style.palette.deep_red_light if is_center else style.palette.rule,
            radius=style.panel_radius,
            stroke_width=style.hero_stroke_width if is_center else style.panel_stroke_width,
        )
        drawing.append(
            draw.Rectangle(
                column.bounds.x,
                column.bounds.y,
                column.bounds.width,
                column.bounds.height,
                fill="none",
                stroke="none",
                **_role("panel-frame", panel_id=column.id, panel_role=column.role),
            )
        )
        p.rounded_rect(
            drawing,
            column.bounds.inset(12),
            fill="none",
            stroke="#fde8e5" if is_center else "#edf1f6",
            radius=style.panel_radius - 2,
            stroke_width=0.8,
            opacity=0.72,
        )
        drawing.append(
            draw.Text(
                column.title,
                style.typography.hero_title_size if is_center else style.typography.support_title_size,
                column.bounds.center.x,
                column.bounds.y + 44,
                fill=style.palette.deep_red if is_center else style.palette.ink,
                font_family=style.typography.family,
                font_weight="700",
                text_anchor="middle",
                **_role("panel-title", panel_id=column.id),
            )
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
            width=1.65,
            head_length=15,
            head_width=14,
            opacity=0.30,
            attrs=_role("support-to-center-flow"),
        )
    p.end_semantic_group(drawing)


def _draw_material_panel(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: SulfurPolymerOrigin = obj.payload
    column = _column(scene, obj.column)
    chain = column.box("chain_area")
    swatches = column.box("swatch_area")
    p.begin_semantic_group(
        drawing,
        obj,
        f"s8_atoms={payload.s8_atom_count} chain_atoms={payload.chain_atom_count} swatches={len(payload.swatches)}",
    )
    centers = [Point(chain.x + 26 + index * 43, chain.y + 48 + (index % 2) * 22) for index in range(payload.chain_atom_count)]
    for start, end in zip(centers, centers[1:]):
        drawing.append(draw.Line(start.x, start.y, end.x, end.y, stroke=style.palette.sulfur_brown, stroke_width=2.3, opacity=0.80))
    for center in centers:
        p.sulfur_atom(drawing, center, 13.5, style)
    p.text(drawing, payload.heat_label, chain.x, chain.bottom + 26, 12.2, fill=style.palette.muted, style=style)
    p.text(drawing, payload.chain_label, chain.x, chain.bottom + 48, 13.5, fill=style.palette.sulfur_brown, weight="700", style=style)
    swatch_w = swatches.width / len(payload.swatches)
    for index, swatch in enumerate(payload.swatches):
        rect = Rect(swatches.x + index * swatch_w, swatches.y, swatch_w - 7, 31)
        p.rounded_rect(drawing, rect, fill=swatch.color, stroke="#ffffff", radius=3, stroke_width=1.0)
        drawing.append(draw.Rectangle(rect.x, rect.y, rect.width, rect.height, fill="none", stroke="none", **_role("composition-swatch")))
        p.text(drawing, swatch.label, rect.center.x, rect.bottom + 18, 10.2, fill=style.palette.muted, anchor="middle", style=style)
    p.text(drawing, payload.footer_label, swatches.x, swatches.bottom + 22, 11.4, fill=style.palette.ink, italic=True, style=style)
    p.end_semantic_group(drawing)


def _draw_evidence_panel(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: EvidenceTrio = obj.payload
    column = _column(scene, obj.column)
    p.begin_semantic_group(drawing, obj, f"modalities={len(payload.modalities)} badge_gap={payload.badge_gap:g}")
    p.text(drawing, payload.title, column.bounds.x + 36, column.bounds.y + 72, 13.4, fill=style.palette.ink, weight="700", style=style)
    for modality, box_id in zip(payload.modalities, ("pe_plot", "decay_plot"), strict=True):
        box = column.box(box_id)
        p.rounded_rect(drawing, box, fill="#ffffff", stroke="#dfe4ec", radius=5, stroke_width=0.9)
        p.text(drawing, modality.label, box.x + 12, box.y + 22, 12, fill=modality.accent, weight="700", style=style)
        p.text(drawing, modality.title, box.x + 12, box.bottom - 12, 9.2, fill=style.palette.muted, style=style)
    cue = column.box("electrical_cue")
    p.text(drawing, "paired electrical signatures point to long-lived stored charge", cue.center.x, cue.y + 28, 10.8, fill=style.palette.muted, italic=True, anchor="middle", style=style)
    p.end_semantic_group(drawing)


def _draw_pe_plot(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: PEHysteresisPlot = obj.payload
    box = _column(scene, obj.column).box("pe_plot").inset(14, 28)
    plan = pe_hysteresis_plan(
        box,
        loop_width=payload.loop_width,
        loop_height=payload.loop_height,
        remanence=payload.remanence,
        samples_per_branch=payload.samples_per_branch,
        label="P-E",
    )
    p.begin_semantic_group(drawing, obj, f"model={payload.model} samples={payload.samples_per_branch} remanence={payload.remanence:g}")
    _draw_simple_axes(drawing, plan, style)
    drawing.append(_polyline(plan.curve_points, "plot-curve", stroke=payload.color, stroke_width=1.8, close=True))
    p.text(drawing, "Pr", plan.frame.center.x + 14, plan.frame.center.y - 18, 8.8, fill=payload.color, italic=True, style=style)
    p.end_semantic_group(drawing)


def _draw_decay_plot(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: PowerLawDecayPlot = obj.payload
    box = _column(scene, obj.column).box("decay_plot").inset(14, 28)
    plan = power_law_decay_plan(
        box,
        slope=payload.slope,
        log_t_min=payload.log_t_min,
        log_t_max=payload.log_t_max,
        log_i_top=payload.log_i_top,
        log_i_bottom=payload.log_i_bottom,
        samples=payload.samples,
        label=payload.label,
    )
    p.begin_semantic_group(drawing, obj, f"model={payload.model} slope={payload.slope:g} samples={payload.samples}")
    _draw_simple_axes(drawing, plan, style)
    drawing.append(_polyline(plan.curve_points, "plot-curve", stroke=payload.color, stroke_width=1.95))
    p.text(drawing, payload.label, plan.frame.x + 32, plan.frame.y + 20, 9.2, fill=payload.color, weight="700", style=style)
    p.end_semantic_group(drawing)


def _draw_simple_axes(drawing: draw.Drawing, plan: ScientificPlotPlan, style: FigureStyle) -> None:
    frame = plan.frame
    p.arrow(drawing, Point(frame.x, frame.bottom), Point(frame.right, frame.bottom), style.palette.ink, width=0.9, head_length=7, head_width=6, opacity=0.75, attrs=_role("plot-axis"))
    p.arrow(drawing, Point(frame.x, frame.bottom), Point(frame.x, frame.y), style.palette.ink, width=0.9, head_length=7, head_width=6, opacity=0.75, attrs=_role("plot-axis"))


def _polyline(points: tuple[Point, ...], role: str, *, stroke: str, stroke_width: float, close: bool = False) -> draw.Path:
    return p.polyline_path(points, fill="none", stroke=stroke, stroke_width=stroke_width, close=close, attrs=_role(role))


def _draw_band_diagram(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: BandDiagram = obj.payload
    area = _column(scene, obj.column).box("band_area")
    axis_x = area.x + 28
    p.begin_semantic_group(drawing, obj, f"lumo={payload.lumo.y:.2f} homo={payload.homo.y:.2f}")
    p.arrow(drawing, Point(axis_x, area.bottom), Point(axis_x, area.y), style.palette.ink, width=1.2, head_length=10, head_width=8, attrs=_role("energy-axis"))
    for edge, role in ((payload.lumo, "band-edge"), (payload.homo, "band-edge")):
        y = area.y + edge.y * area.height
        drawing.append(draw.Line(axis_x + 26, y, area.right - 10, y, stroke=style.palette.ink, stroke_width=1.8, **_role(role)))
        p.text(drawing, edge.label, area.right + 8, y + 4, 12.5, fill=style.palette.ink, weight="700", style=style)
    p.text(drawing, payload.energy_axis_label, axis_x - 12, area.y - 8, 11, fill=style.palette.muted, anchor="middle", style=style)
    p.end_semantic_group(drawing)


def _draw_trap_states(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: TrapLevelSet = obj.payload
    area = _column(scene, obj.column).box("band_area")
    p.begin_semantic_group(
        drawing,
        obj,
        f"shallow={len(payload.shallow_positions)} deep={len(payload.deep_positions)} reference={payload.energy_reference}",
    )
    for index, position in enumerate(payload.shallow_positions):
        _trap_line(drawing, area, position, 56 + index * 8, style.palette.shallow_blue, "trap-shallow", 1.8)
    for index, position in enumerate(payload.deep_positions):
        _trap_line(drawing, area, position, 76 + index * 9, style.palette.deep_red, "trap-deep", 2.15)
    p.text(drawing, payload.shallow_label, area.x + 76, area.y + 150, 12.3, fill=style.palette.shallow_blue, italic=True, style=style)
    p.text(drawing, payload.deep_label, area.x + 84, area.y + 318, 13.2, fill=style.palette.deep_red, italic=True, weight="700", style=style)
    p.end_semantic_group(drawing)


def _trap_line(drawing: draw.Drawing, area: Rect, position: float, width: float, color: str, role: str, stroke_width: float) -> None:
    y = area.y + area.height * position
    center_x = area.x + area.width * 0.56
    drawing.append(draw.Line(center_x - width / 2, y, center_x + width / 2, y, stroke=color, stroke_width=stroke_width, stroke_linecap="round", **_role(role)))


def _draw_dos_profile(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: DOSLobes = obj.payload
    area = _column(scene, obj.column).box("dos_area")
    p.begin_semantic_group(drawing, obj, f"model={payload.model} deep_width={payload.deep_width:g} samples={payload.samples}")
    p.draw_reference_dos_schematic(
        drawing,
        area,
        shallow_center_y=payload.shallow_center_y,
        deep_center_y=payload.deep_center_y,
        shallow_width=payload.shallow_width,
        deep_width=payload.deep_width,
        shallow_height=payload.shallow_height,
        deep_height=payload.deep_height,
        shallow_label="shallow",
        deep_label="deep",
        depth_label=scene.object_by_kind("TrapLevelSet").payload.depth_label,
        attrs_for_role=_role,
        axis_role="dos-axis",
        shallow_lobe_role="dos-lobe-shallow",
        deep_lobe_role="dos-lobe-deep",
        threshold_role="dos-threshold",
        depth_guide_role="dos-depth-guide",
        depth_label_role="dos-depth-label",
        label_role="dos-label",
        axis_label_role="dos-axis-label",
        shallow_sigma=payload.shallow_sigma,
        deep_sigma=payload.deep_sigma,
        samples=payload.samples,
        title="DOS",
        axis_label="g(Et)",
        show_lobe_labels=True,
        show_energy_label=False,
        depth_label_side="right",
        compact=False,
        style=style,
    )
    caption = _column(scene, obj.column).box("mechanism_caption")
    p.rounded_rect(drawing, caption, fill="#fffdfc", stroke="#f3d9d6", radius=5, stroke_width=0.8)
    p.multiline_text(
        drawing,
        ("Payload controls trap count, energy placement, and DOS silhouette.", "Support panels constrain the mechanism without overriding geometry."),
        caption.x + 20,
        caption.y + 32,
        12.2,
        18,
        fill=style.palette.ink,
        style=style,
    )
    p.end_semantic_group(drawing)


def _draw_readout_panel(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: TrapModelFlow = obj.payload
    column = _column(scene, obj.column)
    strip = column.box("readout_strip")
    mini = column.box("readout_dos")
    note = column.box("readout_note")
    p.begin_semantic_group(drawing, obj, f"steps={len(payload.steps)}")
    p.text(drawing, payload.title, strip.x, strip.y - 18, 13.4, fill=style.palette.ink, weight="700", style=style)
    step_gap = strip.width / len(payload.steps)
    baseline = strip.center.y
    for index, step in enumerate(payload.steps):
        center = Point(strip.x + step_gap * index + step_gap / 2, baseline)
        drawing.append(draw.Circle(center.x, center.y, 16, fill="#f4f7fb", stroke=style.palette.rule, stroke_width=0.9, **_role("readout-step")))
        p.text(drawing, step, center.x, center.y + 39, 9.4, fill=style.palette.muted, anchor="middle", style=style)
        if index < len(payload.steps) - 1:
            p.arrow(drawing, Point(center.x + 19, center.y), Point(center.x + step_gap - 19, center.y), style.palette.muted, width=0.85, head_length=6, head_width=6, opacity=0.55)
    p.draw_reference_dos_schematic(
        drawing,
        mini,
        shallow_center_y=0.23,
        deep_center_y=0.61,
        shallow_width=30,
        deep_width=72,
        shallow_height=42,
        deep_height=88,
        shallow_label="",
        deep_label="",
        depth_label="Et",
        attrs_for_role=_role,
        axis_role="mini-dos-axis",
        shallow_lobe_role="mini-dos-shallow",
        deep_lobe_role="mini-dos-deep",
        threshold_role="mini-dos-threshold",
        depth_guide_role="mini-dos-guide",
        depth_label_role="mini-dos-depth",
        label_role="mini-dos-label",
        axis_label_role="mini-dos-axis-label",
        samples=40,
        title="",
        show_lobe_labels=False,
        compact=True,
        style=style,
    )
    p.multiline_text(drawing, ("compact", "readout"), note.x, note.y + 26, 11.5, 15, fill=style.palette.muted, style=style)
    p.end_semantic_group(drawing)


def _draw_device_panel(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: MacroscopicProbe = obj.payload
    frame = _column(scene, obj.column).box("device_frame")
    cue = _column(scene, obj.column).box("device_cue")
    p.begin_semantic_group(drawing, obj, f"frames={payload.frames[0]}:{payload.frames[1]}")
    p.rounded_rect(drawing, frame, fill="#f8fafc", stroke="#dbe1ea", radius=5, stroke_width=0.9)
    p.text(drawing, payload.title, frame.x + 14, frame.y + 24, 12.8, fill=style.palette.ink, weight="700", style=style)
    p.text(drawing, "stored charge produces retained bending response", cue.center.x, cue.y + 25, 10.8, fill=style.palette.muted, italic=True, anchor="middle", style=style)
    p.end_semantic_group(drawing)


def _draw_cantilever(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: PolymerCantilever = obj.payload
    frame = payload.frame_bounds[-1]
    p.begin_semantic_group(drawing, obj, f"charges={len(payload.charge_positions)} bend={payload.repulsive_bend}")
    drawing.append(draw.Line(frame.x + 26, frame.y + 102, frame.x + 90, frame.y + 102, stroke="#7d8794", stroke_width=12, stroke_linecap="square"))
    beam = draw.Path(fill="none", stroke="#d5a534", stroke_width=22, stroke_linecap="round")
    beam.M(frame.x + 86, frame.y + 102)
    beam.C(frame.x + 128, frame.y + 100, frame.x + 172, frame.y + 128, frame.x + 218, frame.y + 154)
    drawing.append(beam)
    highlight = draw.Path(fill="none", stroke="#f2da80", stroke_width=5, stroke_linecap="round", opacity=0.48)
    highlight.M(frame.x + 88, frame.y + 96)
    highlight.C(frame.x + 130, frame.y + 96, frame.x + 173, frame.y + 124, frame.x + 215, frame.y + 150)
    drawing.append(highlight)
    for charge in payload.charge_positions:
        p.charge_marker(drawing, charge, payload.charge_sign, 7.5, style.palette.deep_red_mid, style)
    p.end_semantic_group(drawing)


def _draw_electrode(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: Electrode = obj.payload
    p.begin_semantic_group(drawing, obj, f"sign={payload.sign} x={payload.center.x:g}")
    p.rounded_rect(drawing, payload.bounds, fill="#9aa4af", stroke="#505965", radius=2, stroke_width=1.0)
    p.text(drawing, f"{payload.sign} V", payload.bounds.right + 8, payload.bounds.y + 34, 12.5, fill=style.palette.deep_red, weight="700", style=style)
    p.end_semantic_group(drawing)


def _draw_force_arrow(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: ForceArrow = obj.payload
    p.begin_semantic_group(drawing, obj, f"condition={payload.sign_condition} label={payload.label}")
    p.arrow(drawing, payload.start, payload.end, style.palette.deep_red, width=5.8, head_length=22, head_width=21, attrs=_role("device-force"))
    p.text(drawing, payload.label, payload.end.x - 8, payload.end.y - 18, 11.2, fill=style.palette.deep_red, weight="700", anchor="end", style=style)
    p.end_semantic_group(drawing)


def _render_png(svg_path: Path, png_path: Path, width: int, height: int) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("rsvg-convert"):
        subprocess.run(["rsvg-convert", "-w", str(width), "-h", str(height), str(svg_path), "-o", str(png_path)], check=True)
        return
    build_drawing(build_scene()).save_png(png_path)


def main() -> None:
    render_all()
    print(SVG_OUT)
    print(PNG_OUT)


if __name__ == "__main__":
    main()
