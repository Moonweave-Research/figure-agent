from __future__ import annotations

from engine.domain_primitives import (
    BandDiagram,
    BandEdge,
    CompositionSwatch,
    DOSLobes,
    LayoutFlow,
    SulfurPolymerOrigin,
    TrapLevelSet,
    TrapModelFlow,
)
from engine.scene import Column, Layout, LayoutBox, Point, Rect, Reference, Scene, SemanticObject


WIDTH = 1200
HEIGHT = 620


def build_scene() -> Scene:
    columns = (
        Column(
            index=1,
            id="probe_material_context",
            title="Material context",
            role="supporting",
            ratio=1.0,
            bounds=Rect(42, 92, 318, 450),
            object_ids=("probe_material",),
            local_boxes=(
                LayoutBox("chain_area", Rect(76, 166, 250, 145)),
                LayoutBox("swatch_area", Rect(76, 344, 248, 92)),
            ),
        ),
        Column(
            index=2,
            id="probe_trap_model",
            title="Payload trap model",
            role="supporting",
            ratio=1.0,
            bounds=Rect(442, 72, 330, 490),
            object_ids=("probe_band", "probe_traps", "probe_dos"),
            local_boxes=(
                LayoutBox("band_area", Rect(480, 148, 132, 318)),
                LayoutBox("dos_area", Rect(604, 136, 142, 332)),
            ),
        ),
        Column(
            index=3,
            id="probe_readout",
            title="Interpretation cue",
            role="supporting",
            ratio=1.0,
            bounds=Rect(844, 92, 314, 450),
            object_ids=("probe_readout_flow",),
            local_boxes=(LayoutBox("flow_area", Rect(886, 176, 230, 258)),),
        ),
    )
    return Scene(
        id="fig_probe_01",
        width=WIDTH,
        height=HEIGHT,
        source_files=("framework_probe_01",),
        reference=Reference(
            source="none",
            authority="guidance_only",
            note="Second-figure framework probe; no reference image and no Fig1 policy import.",
        ),
        layout=Layout(
            kind="three_column_framework_probe",
            ratio=(1.0, 1.0, 1.0),
            columns=columns,
            flow_object_id="probe_layout_flow",
        ),
        objects=(
            SemanticObject(
                id="probe_layout_flow",
                kind="LayoutFlow",
                column=2,
                label="Framework probe flow",
                payload=LayoutFlow(
                    title="Probe flow",
                    arrow_pairs=(
                        (Point(368, 315), Point(430, 315)),
                        (Point(782, 315), Point(834, 315)),
                    ),
                    direction="material_to_payload_to_interpretation",
                ),
            ),
            SemanticObject(
                id="probe_material",
                kind="SulfurPolymerOrigin",
                column=1,
                label="Sulfur polymer material context",
                payload=SulfurPolymerOrigin(
                    s8_atom_count=6,
                    chain_atom_count=5,
                    heat_label="sulfur-rich feed",
                    chain_label="-Sx- network",
                    swatches=(
                        CompositionSwatch("low S", "#f5d97a"),
                        CompositionSwatch("mid S", "#d7a238"),
                        CompositionSwatch("high S", "#955f1e"),
                    ),
                    footer_label="composition drives trap density",
                ),
            ),
            SemanticObject(
                id="probe_band",
                kind="BandDiagram",
                column=2,
                label="Probe band diagram",
                payload=BandDiagram(
                    energy_axis_label="Energy",
                    lumo=BandEdge("LUMO", 0.16),
                    homo=BandEdge("HOMO", 0.86),
                    gap_label="transport gap",
                ),
            ),
            SemanticObject(
                id="probe_traps",
                kind="TrapLevelSet",
                column=2,
                label="Probe trap states",
                payload=TrapLevelSet(
                    shallow_positions=(0.31, 0.40),
                    deep_positions=(0.56, 0.64, 0.72, 0.80),
                    shallow_radius=3.8,
                    deep_radius=4.8,
                    shallow_label="shallow",
                    deep_label="deep",
                    depth_label="Et cue",
                    energy_reference="normalized_bandgap_lumo_to_homo",
                    deep_depth_range_ev=(0.45, 0.95),
                    quantitative_status="framework_probe_payload",
                ),
            ),
            SemanticObject(
                id="probe_dos",
                kind="DOSLobes",
                column=2,
                label="Probe DOS profile",
                payload=DOSLobes(
                    model="gaussian_mixture",
                    shallow_center_y=0.25,
                    deep_center_y=0.66,
                    shallow_width=38.0,
                    deep_width=78.0,
                    shallow_height=48.0,
                    deep_height=118.0,
                    shallow_area=1824.0,
                    deep_area=9204.0,
                    min_deep_to_shallow_ratio=1.4,
                    shallow_sigma=(0.24, 0.30),
                    deep_sigma=(0.28, 0.40),
                    samples=48,
                ),
            ),
            SemanticObject(
                id="probe_readout_flow",
                kind="TrapModelFlow",
                column=3,
                label="Probe readout flow",
                payload=TrapModelFlow(
                    title="Contract probe",
                    steps=("scene payload", "engine primitive", "semantic SVG"),
                    conclusion="Second figure exercises shared geometry without Fig1 policy roles.",
                ),
            ),
        ),
    )
