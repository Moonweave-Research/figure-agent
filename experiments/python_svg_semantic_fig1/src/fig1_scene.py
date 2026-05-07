from __future__ import annotations

from semantic_scene import Label, Panel, Rect, Reference, Scene, SemanticAssertion, SemanticObject


WIDTH = 1595
HEIGHT = 986


def build_scene() -> Scene:
    panels = (
        Panel(
            id="polymer_card",
            bounds=Rect(22, 30, 455, 394),
            title="Sulfur polymer origin",
            label="",
            role="support",
            source_region=Rect(22, 30, 455, 394),
        ),
        Panel(
            id="trap_hero_card",
            bounds=Rect(548, 173, 468, 613),
            title="Converged deep charge trapping",
            label="",
            role="hero",
            source_region=Rect(548, 173, 468, 613),
        ),
        Panel(
            id="electrical_card",
            bounds=Rect(1076, 30, 497, 394),
            title="Electrical evidence",
            label="",
            role="support",
            source_region=Rect(1076, 30, 497, 394),
        ),
        Panel(
            id="model_card",
            bounds=Rect(22, 464, 475, 470),
            title="Interpretation",
            label="",
            role="support",
            source_region=Rect(22, 464, 475, 470),
        ),
        Panel(
            id="probe_card",
            bounds=Rect(1054, 464, 519, 470),
            title="Macroscopic probe",
            label="",
            role="support",
            source_region=Rect(1054, 464, 519, 470),
        ),
    )

    objects = (
        SemanticObject(
            id="polymer_origin",
            role="visual_anchor",
            panel_id="polymer_card",
            summary="S8 ring transforms into sulfur-rich linear chain with S60-S85 composition ramp.",
            must_depict=(
                "S8 ring at left with sulfur atom labels.",
                "Heat/delta arrow from ring to linear Sx chain.",
                "S60 to S85 horizontal sulfur-content arrow with yellow-to-red ramp.",
                "Three checkmark bullets linking sulfur fraction to deeper traps.",
            ),
            must_avoid=(
                "Composition sweep curves or trap-density plots in the polymer-origin card.",
                "Featureless polymer block without S8-to-chain origin story.",
            ),
            labels=(
                Label("Sulfur polymer origin", 108, 68, 22, "blue", "bold"),
                Label("(composition tuning)", 108, 95, 22, "blue", "bold"),
                Label("S8", 82, 231, 18),
                Label("Sx", 444, 197, 18),
                Label("S60", 53, 270, 18),
                Label("S85", 434, 270, 18),
            ),
        ),
        SemanticObject(
            id="deep_trap_hero",
            role="data_visualization",
            panel_id="trap_hero_card",
            summary="Dominant central band/DOS hero showing deep states near midgap and deep DOS lobe dominance.",
            must_depict=(
                "Hero card occupies the visual center and is larger than support cards.",
                "LUMO and HOMO horizontal blocks with vertical energy axis.",
                "Blue shallow trap levels above dark-red deep trap levels.",
                "Deep trap levels are more numerous and visually stronger than shallow levels.",
                "Sideways DOS g(E_t) has small blue shallow lobe and large red deep lobe.",
                "E_t depth annotation spans shallow-to-deep region and labels approximately 0.5-1.0 eV.",
            ),
            must_avoid=(
                "Deep and shallow lobes drawn with equal visual weight.",
                "Deep levels placed closer to LUMO than shallow levels.",
            ),
            labels=(
                Label("Converged deep charge trapping", 608, 224, 27, "red", "bold"),
                Label("LUMO", 653, 296, 20, "ink", "bold"),
                Label("HOMO", 651, 619, 20, "ink", "bold"),
                Label("shallow", 843, 360, 16, "blue"),
                Label("deep", 913, 520, 17, "red"),
            ),
        ),
        SemanticObject(
            id="electrical_evidence",
            role="data_visualization",
            panel_id="electrical_card",
            summary="Electrical evidence card pairs P-E hysteresis and current power-law decay.",
            must_depict=(
                "P-E response mini plot at left.",
                "Current decay log-log plot at right with I(t) proportional to t^-n.",
                "Both plots share support-card visual weight.",
            ),
            must_avoid=("A single evidence modality dominating the card.",),
            labels=(
                Label("Electrical evidence", 1169, 84, 22, "blue", "bold"),
                Label("P-E response", 1128, 135, 16),
                Label("Current decay", 1397, 135, 16, "blue"),
            ),
        ),
        SemanticObject(
            id="trap_model",
            role="process_flow",
            panel_id="model_card",
            summary="Interpretation card shows power-law model flowing through Debye/tau-d into trap DOS.",
            must_depict=(
                "A left-to-right model flow: I(t) proportional to t^-n, Debye exponential, tau-d, g(E_t).",
                "Power-law decay plot with slope annotation.",
                "Trap DOS inset with shallow and deep lobes.",
                "Bottom callout says convergence to deep traps explains extended repulsion.",
            ),
            must_avoid=("Replacing the flow with a generic block diagram unrelated to trap model.",),
            labels=(
                Label("Interpretation (converged trap model)", 108, 511, 18, "blue", "bold"),
                Label("Convergence to deep traps explains the", 66, 874, 16, "blue"),
                Label("extended repulsion.", 179, 902, 16, "blue"),
            ),
        ),
        SemanticObject(
            id="macroscopic_probe",
            role="mechanism",
            panel_id="probe_card",
            summary="Cantilever probe card links trapped charges to repulsion force away from electrode.",
            must_depict=(
                "Cantilever clamp at upper left and curved sulfur-polymer beam below it.",
                "Multiple same-sign trapped charges along the polymer beam.",
                "Vertical electrode on right marked +V.",
                "Large red repulsion arrow points away from electrode.",
                "Blue Maxwell attraction cue is secondary and smaller.",
                "Bottom callout says charge-trapping-induced repulsion dominates.",
            ),
            must_avoid=(
                "Repulsion arrow pointing toward the electrode.",
                "Actuator or bidirectional-actuation framing.",
            ),
            labels=(
                Label("Macroscopic probe", 1135, 511, 22, "blue", "bold"),
                Label("Repulsion", 1354, 611, 17, "red", "bold"),
                Label("force", 1370, 635, 17, "red", "bold"),
                Label("+ V", 1508, 601, 16, "red"),
            ),
        ),
        SemanticObject(
            id="layout_flow",
            role="annotation",
            panel_id="trap_hero_card",
            summary="Subtle gray arrows route supporting cards into the central deep-trap hero.",
            must_depict=(
                "Top-left support card points to hero.",
                "Top-right support card points to hero.",
                "Bottom-left support card points to hero.",
                "Bottom-right support card points to hero.",
            ),
            labels=(),
        ),
    )

    assertions = (
        SemanticAssertion(
            id="deep_dominates_shallow",
            on="deep_trap_hero",
            statement="Deep trap levels and DOS lobe are visually more dominant than shallow states.",
            severity="BLOCKER",
        ),
        SemanticAssertion(
            id="hero_is_visual_focus",
            on="deep_trap_hero",
            statement="The deep-trap hero card is the visual focal point of the figure.",
            severity="MAJOR",
        ),
        SemanticAssertion(
            id="repulsion_points_away_from_electrode",
            on="macroscopic_probe",
            statement="The repulsion arrow points from trapped charges away from the right-side electrode.",
            severity="BLOCKER",
        ),
        SemanticAssertion(
            id="evidence_trio_is_distinct",
            on="electrical_evidence",
            statement="P-E and current-decay evidence remain visually distinct evidence modes.",
            severity="MAJOR",
        ),
    )

    return Scene(
        id="fig1_semantic_redraw",
        width=WIDTH,
        height=HEIGHT,
        reference=Reference(
            source="reference/source_variant_aesthetic_ref.png",
            authority="guidance_only",
            width=1595,
            height=986,
        ),
        panels=panels,
        objects=objects,
        assertions=assertions,
    )
