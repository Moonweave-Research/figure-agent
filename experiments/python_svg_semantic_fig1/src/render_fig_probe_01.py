from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import drawsvg as draw

from engine.domain_primitives import BandDiagram, DOSLobes, LayoutFlow, SulfurPolymerOrigin, TrapLevelSet, TrapModelFlow
from engine.scene import Point, Rect, Scene, SemanticObject
from engine.style import DEFAULT_STYLE, FigureStyle
from engine import primitives as p
from fig_probe_01_scene import build_scene


ROOT = Path(__file__).resolve().parents[1]
SVG_OUT = ROOT / "fig_probe_01_semantic.svg"
PNG_OUT = ROOT / "fig_probe_01_semantic.png"


def _role(role: str) -> dict[str, object]:
    return {"data-probe-role": role}


def build_drawing(scene: Scene, style: FigureStyle = DEFAULT_STYLE) -> draw.Drawing:
    drawing = draw.Drawing(scene.width, scene.height)
    drawing.append(draw.Rectangle(0, 0, scene.width, scene.height, fill=style.palette.white))
    drawing.append(p.style_defs())
    _draw_header(drawing, scene, style)
    _draw_columns(drawing, scene, style)
    for obj in scene.objects:
        if obj.kind == "LayoutFlow":
            _draw_layout_flow(drawing, obj, style)
        elif obj.kind == "SulfurPolymerOrigin":
            _draw_material_context(drawing, scene, obj, style)
        elif obj.kind == "BandDiagram":
            _draw_band_diagram(drawing, scene, obj, style)
        elif obj.kind == "TrapLevelSet":
            _draw_trap_states(drawing, scene, obj, style)
        elif obj.kind == "DOSLobes":
            _draw_dos_profile(drawing, scene, obj, style)
        elif obj.kind == "TrapModelFlow":
            _draw_readout_flow(drawing, scene, obj, style)
        else:
            raise KeyError(obj.kind)
    return drawing


def render_all(scene: Scene | None = None) -> None:
    scene = build_scene() if scene is None else scene
    drawing = build_drawing(scene)
    p.save_svg(drawing, SVG_OUT)
    _render_png(SVG_OUT, PNG_OUT, scene.width, scene.height)


def _column(scene: Scene, index: int):
    return scene.layout.columns[index - 1]


def _draw_header(drawing: draw.Drawing, scene: Scene, style: FigureStyle) -> None:
    p.text(drawing, "Framework probe 01 | second semantic figure", 52, 48, 23, fill=style.palette.ink, weight="700", style=style)
    p.text(
        drawing,
        "No reference image, no Fig1 policy roles; shared engine primitives only.",
        52,
        72,
        12.5,
        fill=style.palette.muted,
        style=style,
    )
    drawing.append(
        draw.Text(
            scene.id,
            1,
            8,
            8,
            fill="none",
            font_family=style.typography.family,
            **_role("probe-scene-id"),
        )
    )


def _draw_columns(drawing: draw.Drawing, scene: Scene, style: FigureStyle) -> None:
    for column in scene.layout.columns:
        p.rounded_rect(
            drawing,
            column.bounds,
            fill=style.palette.panel_fill,
            stroke=style.palette.rule,
            radius=style.panel_radius,
            stroke_width=style.panel_stroke_width,
        )
        p.rounded_rect(
            drawing,
            column.bounds.inset(12),
            fill="none",
            stroke="#edf1f6",
            radius=style.panel_radius - 2,
            stroke_width=0.8,
            opacity=0.72,
        )
        drawing.append(
            draw.Text(
                column.title,
                17,
                column.bounds.center.x,
                column.bounds.y + 42,
                fill=style.palette.ink,
                font_family=style.typography.family,
                font_weight="700",
                text_anchor="middle",
                **_role("column-title"),
            )
        )


def _draw_layout_flow(drawing: draw.Drawing, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: LayoutFlow = obj.payload
    p.begin_semantic_group(drawing, obj, f"direction={payload.direction} arrow_count={len(payload.arrow_pairs)}")
    for start, end in payload.arrow_pairs:
        p.arrow(
            drawing,
            start,
            end,
            style.palette.muted,
            width=1.5,
            head_length=14,
            head_width=13,
            opacity=0.34,
            attrs=_role("flow-arrow"),
        )
    p.end_semantic_group(drawing)


def _draw_material_context(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: SulfurPolymerOrigin = obj.payload
    column = _column(scene, obj.column)
    chain_area = column.box("chain_area")
    swatch_area = column.box("swatch_area")
    p.begin_semantic_group(
        drawing,
        obj,
        f"s8_atoms={payload.s8_atom_count} chain_atoms={payload.chain_atom_count} swatches={len(payload.swatches)}",
    )
    _draw_chain(drawing, chain_area, payload, style)
    p.text(drawing, payload.heat_label, chain_area.x, chain_area.bottom + 30, 13, fill=style.palette.muted, style=style)
    p.text(drawing, payload.chain_label, chain_area.x, chain_area.bottom + 52, 14, fill=style.palette.sulfur_brown, weight="700", style=style)
    swatch_width = swatch_area.width / len(payload.swatches)
    for index, swatch in enumerate(payload.swatches):
        rect = Rect(swatch_area.x + index * swatch_width, swatch_area.y, swatch_width - 6, 28)
        p.rounded_rect(drawing, rect, fill=swatch.color, stroke="#ffffff", radius=3, stroke_width=1.0)
        p.text(drawing, swatch.label, rect.center.x, rect.bottom + 18, 10.5, fill=style.palette.muted, anchor="middle", style=style)
    p.text(drawing, payload.footer_label, swatch_area.x, swatch_area.bottom + 26, 12.5, fill=style.palette.ink, style=style)
    p.end_semantic_group(drawing)


def _draw_chain(drawing: draw.Drawing, area: Rect, payload: SulfurPolymerOrigin, style: FigureStyle) -> None:
    centers = [Point(area.x + 25 + index * 42, area.y + 52 + (index % 2) * 20) for index in range(payload.chain_atom_count)]
    for start, end in zip(centers, centers[1:]):
        drawing.append(draw.Line(start.x, start.y, end.x, end.y, stroke=style.palette.sulfur_brown, stroke_width=2.2, opacity=0.78))
    for center in centers:
        p.sulfur_atom(drawing, center, 13, style)


def _draw_band_diagram(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: BandDiagram = obj.payload
    band_area = _column(scene, obj.column).box("band_area")
    axis_x = band_area.x + 18
    p.begin_semantic_group(drawing, obj, f"lumo={payload.lumo.y:.2f} homo={payload.homo.y:.2f}")
    p.arrow(drawing, Point(axis_x, band_area.bottom), Point(axis_x, band_area.y), style.palette.ink, width=1.1, head_length=9, head_width=8)
    p.text(drawing, payload.energy_axis_label, axis_x - 8, band_area.y - 12, 11, fill=style.palette.muted, anchor="middle", style=style)
    for edge, role in ((payload.lumo, "band-lumo"), (payload.homo, "band-homo")):
        y = band_area.y + edge.y * band_area.height
        drawing.append(draw.Line(axis_x + 18, y, band_area.right - 6, y, stroke=style.palette.ink, stroke_width=1.6, **_role(role)))
        p.text(drawing, edge.label, band_area.right + 8, y + 4, 11.5, fill=style.palette.ink, weight="700", style=style)
    p.end_semantic_group(drawing)


def _draw_trap_states(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: TrapLevelSet = obj.payload
    band_area = _column(scene, obj.column).box("band_area")
    p.begin_semantic_group(
        drawing,
        obj,
        f"shallow_count={len(payload.shallow_positions)} deep_count={len(payload.deep_positions)} energy_reference={payload.energy_reference}",
    )
    for index, position in enumerate(payload.shallow_positions):
        _draw_trap_line(drawing, band_area, position, 42 + index * 6, style.palette.shallow_blue, "trap-shallow", 1.7)
    for index, position in enumerate(payload.deep_positions):
        _draw_trap_line(drawing, band_area, position, 58 + index * 6, style.palette.deep_red, "trap-deep", 2.0)
    p.text(drawing, payload.shallow_label, band_area.x + 40, band_area.y + 128, 11, fill=style.palette.shallow_blue, italic=True, style=style)
    p.text(drawing, payload.deep_label, band_area.x + 46, band_area.y + 232, 12, fill=style.palette.deep_red, italic=True, weight="700", style=style)
    p.end_semantic_group(drawing)


def _draw_trap_line(drawing: draw.Drawing, area: Rect, position: float, width: float, color: str, role: str, stroke_width: float) -> None:
    y = area.y + area.height * position
    center_x = area.x + area.width * 0.54
    drawing.append(
        draw.Line(
            center_x - width / 2,
            y,
            center_x + width / 2,
            y,
            stroke=color,
            stroke_width=stroke_width,
            stroke_linecap="round",
            opacity=0.92,
            **_role(role),
        )
    )


def _draw_dos_profile(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: DOSLobes = obj.payload
    dos_area = _column(scene, obj.column).box("dos_area")
    p.begin_semantic_group(
        drawing,
        obj,
        f"model={payload.model} shallow_sigma={payload.shallow_sigma} deep_sigma={payload.deep_sigma} samples={payload.samples}",
    )
    p.draw_reference_dos_schematic(
        drawing,
        dos_area,
        shallow_center_y=payload.shallow_center_y,
        deep_center_y=payload.deep_center_y,
        shallow_width=payload.shallow_width,
        deep_width=payload.deep_width,
        shallow_height=payload.shallow_height,
        deep_height=payload.deep_height,
        shallow_label="",
        deep_label="",
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
        title="",
        axis_label="g(Et)",
        show_lobe_labels=False,
        show_energy_label=False,
        depth_label_side="right",
        compact=True,
        style=style,
    )
    p.end_semantic_group(drawing)


def _draw_readout_flow(drawing: draw.Drawing, scene: Scene, obj: SemanticObject[object], style: FigureStyle) -> None:
    payload: TrapModelFlow = obj.payload
    flow_area = _column(scene, obj.column).box("flow_area")
    p.begin_semantic_group(drawing, obj, f"steps={len(payload.steps)}")
    p.text(drawing, payload.title, flow_area.x, flow_area.y, 14, fill=style.palette.ink, weight="700", style=style)
    y = flow_area.y + 50
    for index, step in enumerate(payload.steps):
        center = Point(flow_area.x + 56 + index * 70, y)
        drawing.append(draw.Circle(center.x, center.y, 22, fill="#f4f7fb", stroke=style.palette.rule, stroke_width=1.0, **_role("readout-step")))
        p.text(drawing, str(index + 1), center.x, center.y + 5, 12, fill=style.palette.ink, weight="700", anchor="middle", style=style)
        p.text(drawing, step, center.x, center.y + 45, 10.5, fill=style.palette.muted, anchor="middle", style=style)
        if index < len(payload.steps) - 1:
            p.arrow(drawing, Point(center.x + 26, center.y), Point(center.x + 48, center.y), style.palette.muted, width=1.0, head_length=7, head_width=7, opacity=0.52)
    p.rounded_rect(drawing, Rect(flow_area.x, flow_area.bottom - 78, flow_area.width, 58), fill="#fff8f7", stroke="#f1d4d2", radius=5, stroke_width=0.8)
    p.multiline_text(
        drawing,
        ("Probe criterion:", payload.conclusion),
        flow_area.x + 16,
        flow_area.bottom - 50,
        10.5,
        15,
        fill=style.palette.ink,
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


def main() -> None:
    render_all()
    print(SVG_OUT)
    print(PNG_OUT)


if __name__ == "__main__":
    main()
