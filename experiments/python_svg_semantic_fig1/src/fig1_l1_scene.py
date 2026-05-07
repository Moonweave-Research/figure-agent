from __future__ import annotations

from pathlib import Path

from engine.domain_primitives import (
    BandDiagram,
    BandEdge,
    CompositionSwatch,
    DOSLobes,
    DeepTrapHero,
    Electrode,
    ForceArrow,
    ISPDPlot,
    LayoutFlow,
    MacroscopicProbe,
    MaxwellAttractionCue,
    PolymerCantilever,
    PowerLawDecayPlot,
    SulfurPolymerOrigin,
    TrapLevelSet,
    TrapModelFlow,
    VsDecayPlot,
)
from engine.scene import Column, Point, Rect, Reference, Scene, SemanticObject
from engine.scaffold import (
    ScaffoldContract,
    columns_from_scaffold,
    layout_from_scaffold,
    load_scaffold_contract,
)


ROOT = Path(__file__).resolve().parents[1]
VISUAL_LAYOUT = ROOT / "visual_layout.yaml"
CAUSAL_BINDING = ROOT / "causal_reference_binding_v16.md"

BRIEFING = ROOT / "README.md"
SPEC = ROOT / "reference_layout_spec_v1.md"


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
    col_synthesis = _region(columns, "top_synthesis")
    col_traps = _region(columns, "localized_traps")
    col_release = _region(columns, "release_module")
    col_vs_decay = _region(columns, "vs_decay_module")
    col_ispd = _region(columns, "ispd_module")
    col_probe = _region(columns, "probe_module")

    origin = SemanticObject(
        id="sulfur_polymer_origin",
        kind="SulfurPolymerOrigin",
        column=col_synthesis.index,
        label="Sulfur-rich network",
        payload=SulfurPolymerOrigin(
            s8_atom_count=8,
            chain_atom_count=7,
            heat_label="Δ 160 °C",
            chain_label="(-S-)ₓ",
            swatches=(
                CompositionSwatch("S60", "#f8dd72"),
                CompositionSwatch("S70", "#edc24f"),
                CompositionSwatch("S80", "#c98f2c"),
                CompositionSwatch("S85", "#8b571a"),
            ),
            footer_label="S-chain length",
            causal_segments=("S-rich segments",),
            trap_origin_mechanisms=(
                "chemical origin: electronegativity and polarizability of S",
                "physical origin: local potential fluctuations",
                "localized traps",
            ),
        ),
    )

    hero = SemanticObject(
        id="deep_trap_hero",
        kind="DeepTrapHero",
        column=col_traps.index,
        label="localized traps",
        payload=DeepTrapHero(
            title="localized traps",
            subtitle="qualitative trap landscape inside the polymer network",
            hero_ratio=2.0,
            band_object_id="band_diagram",
            trap_object_id="trap_level_set",
            dos_object_id="dos_lobes",
            message="shallow and deep trap sites embedded in the polymer chain.",
            causal_role="qualitative_localized_trap_landscape",
            converged_picture_label="qualitative trap landscape",
        ),
    )

    band = SemanticObject(
        id="band_diagram",
        kind="BandDiagram",
        column=col_traps.index,
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
        column=col_traps.index,
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
        column=col_traps.index,
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

    decay_plot = SemanticObject(
        id="power_law_decay",
        kind="PowerLawDecayPlot",
        column=col_release.index,
        label="Power-law current decay",
        payload=PowerLawDecayPlot(
            title="I(t) ~ t^-n",
            model="power_law_loglog",
            slope=-0.72,
            log_t_min=-3.0,
            log_t_max=3.0,
            log_i_top=0.0,
            log_i_bottom=-8.0,
            samples=56,
            label="I(t) ~ t^-n",
            color="#0b4bb3",
            causal_role="experiment_current_decay_to_power_law_exponent",
            extracted_parameter="n",
        ),
    )

    vs_decay_plot = SemanticObject(
        id="vs_decay_plot",
        kind="VsDecayPlot",
        column=col_vs_decay.index,
        label="V_s(t) decay",
        payload=VsDecayPlot(
            title="V_s(t) decay",
            model="non_debye_power_law",
            decay_form="non-debye-power-law",
            t_min=1.0,
            t_max=1.0e4,
            samples=64,
            color="#2f3b58",
            label="V_s(t)",
            axis_label_t="t (s)",
            axis_label_v="V_s",
            causal_role="surface_voltage_decay_envelope",
        ),
    )

    ispd_plot = SemanticObject(
        id="ispd_plot",
        kind="ISPDPlot",
        column=col_ispd.index,
        label="ISPD trap DOS",
        payload=ISPDPlot(
            title="ISPD-derived g(Et)",
            model="gaussian_mixture",
            shallow_width=62.0,
            deep_width=100.0,
            shallow_height=56.0,
            deep_height=76.0,
            shallow_sigma=(0.26, 0.32),
            deep_sigma=(0.20, 0.20),
            samples=56,
            color="#6f42c1",
            trap_depth_output="g(Et)",
        ),
    )

    trap_flow = SemanticObject(
        id="trap_model_flow",
        kind="TrapModelFlow",
        column=col_release.index,
        label="Trap model flow",
        payload=TrapModelFlow(
            title="distributed release narrative",
            steps=("I(t) ~ t^-n", "Debye\nexp(-t/tau)", "tau_d", "g(Et)"),
            conclusion="non-Debye power-law tail.",
            causal_chain=("I(t) ~ t^-n", "n", "Debye exp(-t/tau)", "tau_d", "g(Et)"),
            debye_reference_label="Discharge Debye reference",
            delay_parameter="tau_d",
            output_distribution="g(Et)",
        ),
    )

    cantilever_frame = col_probe.box("probe_frame")
    charges = (
        Point(cantilever_frame.x + 107, cantilever_frame.y + 268),
        Point(cantilever_frame.x + 103, cantilever_frame.y + 218),
        Point(cantilever_frame.x + 99, cantilever_frame.y + 168),
        Point(cantilever_frame.x + 95, cantilever_frame.y + 118),
        Point(cantilever_frame.x + 91, cantilever_frame.y + 68),
    )
    electrode_bounds = Rect(cantilever_frame.x + 286, cantilever_frame.y + 42, 30, 240)
    arrow_start = Point(cantilever_frame.x + 100, cantilever_frame.y + 175)
    arrow_end = Point(cantilever_frame.x + 18, cantilever_frame.y + 175)

    probe = SemanticObject(
        id="macroscopic_probe",
        kind="MacroscopicProbe",
        column=col_probe.index,
        label="Macroscopic probe",
        payload=MacroscopicProbe(
            title="Macroscopic probe",
            frames=("Vertical cantilever", "Coulomb repulsion vs Maxwell attraction"),
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
            frame_bounds=(cantilever_frame, cantilever_frame),
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
            force_target="cantilever",
        ),
    )

    maxwell = SemanticObject(
        id="maxwell_attraction_cue",
        kind="MaxwellAttractionCue",
        column=col_probe.index,
        label="Secondary Maxwell attraction cue",
        payload=MaxwellAttractionCue(
            start=Point(cantilever_frame.x + 110, cantilever_frame.y + 90),
            end=Point(cantilever_frame.x + 200, cantilever_frame.y + 90),
            label="Maxwell attraction",
            role="secondary_reference_cue",
        ),
    )

    flow = SemanticObject(
        id="layout_flow",
        kind="LayoutFlow",
        column=0,
        label="Vectorization narrative flow",
        payload=LayoutFlow(
            title="synthesis to traps then bottom row readouts",
            arrow_pairs=(
                *((anchor.start, anchor.end) for anchor in scaffold.flow_anchors),
            ),
            direction="synthesis_to_traps_then_bottom_row_readouts",
        ),
    )

    layout = layout_from_scaffold(scaffold, columns)

    return Scene(
        id="fig1_reference_semantic_scene_v1",
        width=canvas.width,
        height=canvas.height,
        source_files=(
            str(BRIEFING),
            str(SPEC),
            str(VISUAL_LAYOUT),
            str(CAUSAL_BINDING),
        ),
        reference=Reference(
            source="experiments/python_svg_semantic_fig1/reference/source_variant_vectorization_ref_v1.png",
            authority="style_layout_evidence",
            note="Reference PNG is the authoritative vectorization composition target, but remains non-traced visual evidence.",
        ),
        layout=layout,
        objects=(
            flow,
            origin,
            hero,
            band,
            traps,
            dos,
            decay_plot,
            vs_decay_plot,
            ispd_plot,
            trap_flow,
            probe,
            cantilever,
            electrode,
            repulsion,
            maxwell,
        ),
    )
