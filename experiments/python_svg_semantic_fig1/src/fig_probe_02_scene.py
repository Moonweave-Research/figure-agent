from __future__ import annotations

from engine.domain_primitives import (
    BandDiagram,
    BandEdge,
    CompositionSwatch,
    DOSLobes,
    Electrode,
    EvidenceModality,
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
from engine.scene import Column, Layout, LayoutBox, Point, Rect, Reference, Scene, SemanticObject


WIDTH = 1595
HEIGHT = 986


def build_scene() -> Scene:
    material = Column(
        index=1,
        id="composition_panel",
        title="Composition tuning",
        role="supporting",
        ratio=1.0,
        bounds=Rect(56, 114, 360, 336),
        object_ids=("probe2_material",),
        local_boxes=(
            LayoutBox("chain_area", Rect(92, 190, 284, 118)),
            LayoutBox("swatch_area", Rect(92, 342, 280, 64)),
        ),
    )
    electrical = Column(
        index=2,
        id="electrical_panel",
        title="Electrical retention",
        role="supporting",
        ratio=1.0,
        bounds=Rect(56, 532, 360, 340),
        object_ids=("probe2_evidence", "probe2_pe", "probe2_decay"),
        local_boxes=(
            LayoutBox("pe_plot", Rect(90, 614, 144, 134)),
            LayoutBox("decay_plot", Rect(242, 614, 140, 134)),
            LayoutBox("electrical_cue", Rect(92, 786, 286, 52)),
        ),
    )
    center = Column(
        index=3,
        id="trap_mechanism_panel",
        title="Trap distribution mechanism",
        role="hero",
        ratio=1.8,
        bounds=Rect(492, 132, 610, 722),
        object_ids=("probe2_band", "probe2_traps", "probe2_dos"),
        local_boxes=(
            LayoutBox("band_area", Rect(546, 224, 222, 456)),
            LayoutBox("dos_area", Rect(790, 214, 258, 474)),
            LayoutBox("mechanism_caption", Rect(560, 718, 476, 84)),
        ),
    )
    spectrum = Column(
        index=4,
        id="spectrum_panel",
        title="Trap-spectrum readout",
        role="supporting",
        ratio=1.0,
        bounds=Rect(1180, 114, 360, 336),
        object_ids=("probe2_readout"),
        local_boxes=(
            LayoutBox("readout_strip", Rect(1224, 188, 270, 84)),
            LayoutBox("readout_dos", Rect(1220, 296, 132, 116)),
            LayoutBox("readout_note", Rect(1368, 304, 118, 96)),
        ),
    )
    device = Column(
        index=5,
        id="device_panel",
        title="Device response",
        role="supporting",
        ratio=1.0,
        bounds=Rect(1180, 532, 360, 340),
        object_ids=("probe2_device", "probe2_cantilever", "probe2_electrode", "probe2_force"),
        local_boxes=(
            LayoutBox("device_frame", Rect(1216, 608, 274, 178)),
            LayoutBox("device_cue", Rect(1224, 806, 260, 42)),
        ),
    )
    columns = (material, electrical, center, spectrum, device)

    return Scene(
        id="fig_probe_02",
        width=WIDTH,
        height=HEIGHT,
        source_files=("framework_probe_02",),
        reference=Reference(
            source="none",
            authority="guidance_only",
            note="Fig1-scale second-figure composition probe with no reference image.",
        ),
        layout=Layout(
            kind="five_panel_center_mechanism_probe",
            ratio=(1.0, 1.0, 1.8, 1.0, 1.0),
            columns=columns,
            flow_object_id="probe2_layout_flow",
        ),
        objects=(
            SemanticObject(
                id="probe2_layout_flow",
                kind="LayoutFlow",
                column=center.index,
                label="Support panels converge to center mechanism",
                payload=LayoutFlow(
                    title="Multi-panel flow",
                    arrow_pairs=(
                        (Point(material.bounds.right + 8, material.bounds.center.y), Point(center.bounds.x - 14, center.bounds.y + 172)),
                        (Point(electrical.bounds.right + 8, electrical.bounds.center.y), Point(center.bounds.x - 14, center.bounds.y + 492)),
                        (Point(spectrum.bounds.x - 10, spectrum.bounds.center.y), Point(center.bounds.right + 14, center.bounds.y + 172)),
                        (Point(device.bounds.x - 10, device.bounds.center.y), Point(center.bounds.right + 14, center.bounds.y + 492)),
                    ),
                    direction="support_panels_to_center_mechanism",
                ),
            ),
            SemanticObject(
                id="probe2_material",
                kind="SulfurPolymerOrigin",
                column=material.index,
                label="Sulfur-rich network tuning",
                payload=SulfurPolymerOrigin(
                    s8_atom_count=8,
                    chain_atom_count=6,
                    heat_label="thermal copolymerization",
                    chain_label="-Sx- network fraction",
                    swatches=(
                        CompositionSwatch("S50", "#f8dc77"),
                        CompositionSwatch("S65", "#e7b947"),
                        CompositionSwatch("S80", "#ba7c25"),
                        CompositionSwatch("S90", "#764616"),
                    ),
                    footer_label="richer sulfur network raises trap-state density",
                ),
            ),
            SemanticObject(
                id="probe2_evidence",
                kind="EvidenceTrio",
                column=electrical.index,
                label="Electrical evidence pair",
                payload=EvidenceTrio(
                    title="Retention signatures",
                    modalities=(
                        EvidenceModality("P-E", "PEHysteresisPlot", "probe2_pe", "hysteresis memory", "#b20f16"),
                        EvidenceModality("I(t)", "PowerLawDecayPlot", "probe2_decay", "slow current decay", "#0b4bb3"),
                    ),
                    badge_gap=14.0,
                ),
            ),
            SemanticObject(
                id="probe2_pe",
                kind="PEHysteresisPlot",
                column=electrical.index,
                label="Probe P-E hysteresis",
                payload=PEHysteresisPlot(
                    title="P-E hysteresis",
                    model="parametric_hysteresis",
                    loop_width=128.0,
                    loop_height=76.0,
                    remanence=0.36,
                    samples_per_branch=42,
                    color="#b20f16",
                ),
            ),
            SemanticObject(
                id="probe2_decay",
                kind="PowerLawDecayPlot",
                column=electrical.index,
                label="Probe current decay",
                payload=PowerLawDecayPlot(
                    title="current decay",
                    model="power_law_loglog",
                    slope=-0.64,
                    log_t_min=-2.0,
                    log_t_max=4.0,
                    log_i_top=0.0,
                    log_i_bottom=-7.0,
                    samples=52,
                    label="t^-n",
                    color="#0b4bb3",
                ),
            ),
            SemanticObject(
                id="probe2_band",
                kind="BandDiagram",
                column=center.index,
                label="Center band diagram",
                payload=BandDiagram(
                    energy_axis_label="Energy",
                    lumo=BandEdge("LUMO", 0.16),
                    homo=BandEdge("HOMO", 0.84),
                    gap_label="transport gap",
                ),
            ),
            SemanticObject(
                id="probe2_traps",
                kind="TrapLevelSet",
                column=center.index,
                label="Center trap population",
                payload=TrapLevelSet(
                    shallow_positions=(0.29, 0.36, 0.43),
                    deep_positions=(0.53, 0.58, 0.63, 0.68, 0.73, 0.78),
                    shallow_radius=4.0,
                    deep_radius=5.0,
                    shallow_label="shallow traps",
                    deep_label="deep traps",
                    depth_label="Et window",
                    energy_reference="normalized_bandgap_lumo_to_homo",
                    deep_depth_range_ev=(0.45, 1.05),
                    quantitative_status="framework_probe_payload",
                ),
            ),
            SemanticObject(
                id="probe2_dos",
                kind="DOSLobes",
                column=center.index,
                label="Center DOS population",
                payload=DOSLobes(
                    model="gaussian_mixture",
                    shallow_center_y=0.22,
                    deep_center_y=0.62,
                    shallow_width=50.0,
                    deep_width=132.0,
                    shallow_height=62.0,
                    deep_height=168.0,
                    shallow_area=3100.0,
                    deep_area=22176.0,
                    min_deep_to_shallow_ratio=1.5,
                    shallow_sigma=(0.24, 0.30),
                    deep_sigma=(0.25, 0.34),
                    samples=64,
                ),
            ),
            SemanticObject(
                id="probe2_readout",
                kind="TrapModelFlow",
                column=spectrum.index,
                label="Trap spectrum readout",
                payload=TrapModelFlow(
                    title="Readout chain",
                    steps=("decay", "tau", "Et", "g(Et)"),
                    conclusion="Extraction path should stay compact while the center carries the mechanism.",
                ),
            ),
            SemanticObject(
                id="probe2_device",
                kind="MacroscopicProbe",
                column=device.index,
                label="Device readout",
                payload=MacroscopicProbe(
                    title="Probe response",
                    frames=("neutral", "charged"),
                    cantilever_object_id="probe2_cantilever",
                    electrode_object_id="probe2_electrode",
                    force_object_id="probe2_force",
                ),
            ),
            SemanticObject(
                id="probe2_cantilever",
                kind="PolymerCantilever",
                column=device.index,
                label="Sulfur polymer cantilever",
                payload=PolymerCantilever(
                    charge_sign="-",
                    initial_bend="relaxed",
                    repulsive_bend="retained_outward_bend",
                    charge_positions=(
                        Point(1338, 666),
                        Point(1360, 692),
                        Point(1380, 720),
                        Point(1400, 748),
                    ),
                    frame_bounds=(device.box("device_frame"), device.box("device_frame")),
                ),
            ),
            SemanticObject(
                id="probe2_electrode",
                kind="Electrode",
                column=device.index,
                label="Bias electrode",
                payload=Electrode(
                    sign="-",
                    label="biased electrode",
                    center=Point(1460, 694),
                    bounds=Rect(1450, 620, 28, 150),
                ),
            ),
            SemanticObject(
                id="probe2_force",
                kind="ForceArrow",
                column=device.index,
                label="Retained repulsive force",
                payload=ForceArrow(
                    start=Point(1388, 704),
                    end=Point(1300, 704),
                    label="retained repulsion",
                    sign_condition="like_charge_repulsion",
                ),
            ),
        ),
    )
