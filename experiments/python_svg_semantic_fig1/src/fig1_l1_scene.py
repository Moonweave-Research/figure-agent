from __future__ import annotations

from pathlib import Path

from engine.domain_primitives import (
    BandDiagram,
    BandEdge,
    CompositionSwatch,
    DOSLobes,
    DeepTrapHero,
    Electrode,
    EvidenceModality,
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
from engine.scene import Column, Point, Rect, Reference, Scene, SemanticObject
from engine.scaffold import ScaffoldContract, columns_from_scaffold, layout_from_scaffold, load_scaffold_contract


ROOT = Path(__file__).resolve().parents[1]
VISUAL_LAYOUT = ROOT / "visual_layout.yaml"

BRIEFING = "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/examples/fig1_overview/briefing.md"
SPEC = "/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/examples/fig1_overview/spec.yaml"


def load_fig1_scaffold() -> ScaffoldContract:
    return load_scaffold_contract(VISUAL_LAYOUT)


def _region(columns: tuple[Column, ...], region_id: str) -> Column:
    for column in columns:
        if column.id == region_id:
            return column
    raise KeyError(region_id)


def build_scene() -> Scene:
    scaffold = load_fig1_scaffold()
    columns = columns_from_scaffold(scaffold)
    canvas = scaffold.canvas
    col_polymer = _region(columns, "polymer_origin_card")
    col_electrical = _region(columns, "electrical_evidence_card")
    col_hero = _region(columns, "deep_trap_hero_card")
    col_interpretation = _region(columns, "interpretation_card")
    col_probe = _region(columns, "macroscopic_probe_card")

    origin = SemanticObject(
        id="sulfur_polymer_origin",
        kind="SulfurPolymerOrigin",
        column=col_polymer.index,
        label="Sulfur polymer origin",
        payload=SulfurPolymerOrigin(
            s8_atom_count=8,
            chain_atom_count=7,
            heat_label="Heat 160 C",
            chain_label="-Sx- chain",
            swatches=(
                CompositionSwatch("S60", "#f8dd72"),
                CompositionSwatch("S70", "#edc24f"),
                CompositionSwatch("S80", "#c98f2c"),
                CompositionSwatch("S85", "#8b571a"),
            ),
            footer_label="Tunable composition",
        ),
    )

    hero = SemanticObject(
        id="deep_trap_hero",
        kind="DeepTrapHero",
        column=col_hero.index,
        label="Deep charge trapping",
        payload=DeepTrapHero(
            title="Converged deep charge trapping",
            subtitle="Deep traps dominate the sulfur-polymer gap",
            hero_ratio=2.0,
            band_object_id="band_diagram",
            trap_object_id="trap_level_set",
            dos_object_id="dos_lobes",
            message="DEEP mid-gap states anchor long-lived charge storage.",
        ),
    )

    band = SemanticObject(
        id="band_diagram",
        kind="BandDiagram",
        column=col_hero.index,
        label="Band diagram",
        payload=BandDiagram(
            energy_axis_label="Energy",
            lumo=BandEdge("LUMO", 0.18),
            homo=BandEdge("HOMO", 0.82),
            gap_label="bandgap",
        ),
    )

    traps = SemanticObject(
        id="trap_level_set",
        kind="TrapLevelSet",
        column=col_hero.index,
        label="Trap level set",
        payload=TrapLevelSet(
            shallow_positions=(0.31, 0.38, 0.45),
            deep_positions=(0.50, 0.54, 0.58, 0.62, 0.66, 0.70, 0.74),
            shallow_radius=4.0,
            deep_radius=5.0,
            shallow_label="Shallow",
            deep_label="DEEP",
            depth_label="Et ~ 0.5-1.0 eV",
            energy_reference="normalized_bandgap_lumo_to_homo",
            deep_depth_range_ev=(0.5, 1.0),
            quantitative_status="schematic_placeholder_until_fig3_ispd",
        ),
    )

    dos = SemanticObject(
        id="dos_lobes",
        kind="DOSLobes",
        column=col_hero.index,
        label="DOS lobes",
        payload=DOSLobes(
            model="gaussian_mixture",
            shallow_center_y=0.21,
            deep_center_y=0.62,
            shallow_width=54.0,
            deep_width=140.0,
            shallow_height=64.0,
            deep_height=174.0,
            shallow_area=3456.0,
            deep_area=24360.0,
            min_deep_to_shallow_ratio=1.5,
            shallow_sigma=(0.26, 0.32),
            deep_sigma=(0.24, 0.28),
            samples=72,
        ),
    )

    trio = SemanticObject(
        id="evidence_trio",
        kind="EvidenceTrio",
        column=col_electrical.index,
        label="Evidence trio",
        payload=EvidenceTrio(
            title="Electrical evidence",
            modalities=(
                EvidenceModality("P-E", "PEHysteresisPlot", "pe_hysteresis", "P-E hysteresis", "#b20f16"),
                EvidenceModality("I(t)", "PowerLawDecayPlot", "power_law_decay", "I(t) proportional t^-n", "#0b4bb3"),
            ),
            badge_gap=18.0,
        ),
    )

    pe_plot = SemanticObject(
        id="pe_hysteresis",
        kind="PEHysteresisPlot",
        column=col_electrical.index,
        label="P-E hysteresis",
        payload=PEHysteresisPlot(
            title="P-E hysteresis",
            model="parametric_hysteresis",
            loop_width=145.0,
            loop_height=82.0,
            remanence=0.42,
            samples_per_branch=48,
            color="#b20f16",
        ),
    )

    decay_plot = SemanticObject(
        id="power_law_decay",
        kind="PowerLawDecayPlot",
        column=col_electrical.index,
        label="Power-law current decay",
        payload=PowerLawDecayPlot(
            title="I(t) proportional t^-n",
            model="power_law_loglog",
            slope=-0.72,
            log_t_min=-3.0,
            log_t_max=3.0,
            log_i_top=0.0,
            log_i_bottom=-8.0,
            samples=56,
            label="I(t) ~ t^-n",
            color="#0b4bb3",
        ),
    )

    ispd_plot = SemanticObject(
        id="ispd_plot",
        kind="ISPDPlot",
        column=col_interpretation.index,
        label="ISPD trap DOS",
        payload=ISPDPlot(
            title="ISPD g(Et)",
            model="gaussian_mixture",
            shallow_width=46.0,
            deep_width=100.0,
            shallow_height=42.0,
            deep_height=76.0,
            shallow_sigma=(0.26, 0.32),
            deep_sigma=(0.24, 0.28),
            samples=56,
            color="#6f42c1",
        ),
    )

    trap_flow = SemanticObject(
        id="trap_model_flow",
        kind="TrapModelFlow",
        column=col_interpretation.index,
        label="Trap model flow",
        payload=TrapModelFlow(
            title="Trap model",
            steps=("I(t) ~ t^-n", "Debye\nexp(-t/tau)", "tau_d", "g(Et)"),
            conclusion="Convergence to deep traps explains the extended repulsion.",
        ),
    )

    cantilever_frame_1 = col_probe.box("probe_frame")
    cantilever_frame_2 = cantilever_frame_1
    charges = (
        Point(cantilever_frame_2.x + 140, cantilever_frame_2.y + 126),
        Point(cantilever_frame_2.x + 155, cantilever_frame_2.y + 165),
        Point(cantilever_frame_2.x + 178, cantilever_frame_2.y + 205),
        Point(cantilever_frame_2.x + 211, cantilever_frame_2.y + 244),
        Point(cantilever_frame_2.x + 246, cantilever_frame_2.y + 276),
    )
    electrode_bounds = Rect(cantilever_frame_2.right - 48, cantilever_frame_2.y + 62, 34, 270)
    arrow_start = Point(cantilever_frame_2.x + 250, cantilever_frame_2.y + 160)
    arrow_end = Point(cantilever_frame_2.x + 360, cantilever_frame_2.y + 160)

    probe = SemanticObject(
        id="macroscopic_probe",
        kind="MacroscopicProbe",
        column=col_probe.index,
        label="Macroscopic probe",
        payload=MacroscopicProbe(
            title="Macroscopic probe",
            frames=("Cantilever probe", "Charge-trapping-induced repulsion"),
            cantilever_object_id="polymer_cantilever",
            electrode_object_id="electrode",
            force_object_id="repulsion_arrow",
        ),
    )

    cantilever = SemanticObject(
        id="polymer_cantilever",
        kind="PolymerCantilever",
        column=col_probe.index,
        label="Polymer cantilever",
        payload=PolymerCantilever(
            charge_sign="+",
            initial_bend="toward_electrode",
            repulsive_bend="away_from_electrode",
            charge_positions=charges,
            frame_bounds=(cantilever_frame_1, cantilever_frame_2),
        ),
    )

    electrode = SemanticObject(
        id="electrode",
        kind="Electrode",
        column=col_probe.index,
        label="Electrode",
        payload=Electrode(
            sign="+",
            label="+ electrode",
            center=electrode_bounds.center,
            bounds=electrode_bounds,
        ),
    )

    repulsion = SemanticObject(
        id="repulsion_arrow",
        kind="ForceArrow",
        column=col_probe.index,
        label="Coulomb repulsion",
        payload=ForceArrow(
            start=arrow_start,
            end=arrow_end,
            label="Coulomb qE",
            sign_condition="trapped charge sign equals electrode sign",
        ),
    )

    maxwell = SemanticObject(
        id="maxwell_attraction_cue",
        kind="MaxwellAttractionCue",
        column=col_probe.index,
        label="Secondary Maxwell attraction cue",
        payload=MaxwellAttractionCue(
            start=Point(cantilever_frame_2.x + 350, cantilever_frame_2.y + 220),
            end=Point(cantilever_frame_2.x + 270, cantilever_frame_2.y + 220),
            label="Maxwell attraction",
            role="secondary_reference_cue",
        ),
    )

    flow = SemanticObject(
        id="layout_flow",
        kind="LayoutFlow",
        column=0,
        label="Reference support-to-hero flow",
        payload=LayoutFlow(
            title="Reference support cards route into center hero",
            arrow_pairs=(
                *(
                    (anchor.start, anchor.end)
                    for anchor in scaffold.flow_anchors
                ),
            ),
            direction="support_to_center_hero",
        ),
    )

    layout = layout_from_scaffold(scaffold, columns)

    return Scene(
        id="fig1_reference_semantic_scene_v1",
        width=canvas.width,
        height=canvas.height,
        source_files=(BRIEFING, SPEC, str(VISUAL_LAYOUT)),
        reference=Reference(
            source="experiments/python_svg_semantic_fig1/reference/source_variant_aesthetic_ref.png",
            authority="style_layout_evidence",
            note="Reference PNG is the authoritative visual layout target, but remains non-traced visual evidence.",
        ),
        layout=layout,
        objects=(
            flow,
            origin,
            hero,
            band,
            traps,
            dos,
            trio,
            pe_plot,
            decay_plot,
            ispd_plot,
            trap_flow,
            probe,
            cantilever,
            electrode,
            repulsion,
            maxwell,
        ),
    )
