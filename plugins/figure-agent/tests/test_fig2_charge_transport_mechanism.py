from __future__ import annotations

import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig2_charge_transport_mechanism"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

import composition_scene  # noqa: E402
import aesthetic_intent  # noqa: E402
from briefing_grounding import has_reference_free_grounding_context  # noqa: E402
import paper_aesthetic_context  # noqa: E402
from semantic_legibility_contract import validate_semantic_legibility_contract  # noqa: E402


def test_fig2_declares_a_parallel_material_comparison_contract() -> None:
    contract = yaml.safe_load((FIXTURE / "semantic_contract.yaml").read_text(encoding="utf-8"))

    result = validate_semantic_legibility_contract(contract)
    comparison = result["semantic_legibility"]["parallel_comparisons"][0]

    assert comparison["members"] == [
        "panel_a.reference_dielectric",
        "panel_a.sulfur_trap_sequence",
    ]
    assert result["summary"]["parallel_comparison_count"] == 1
    assert "mim_comparison_uses_matched_footprints" in contract["protected_relations"]


def test_fig2_critique_inputs_are_loadable_and_registered_in_nc_context() -> None:
    intent = aesthetic_intent.load_aesthetic_intent(FIXTURE / "aesthetic_intent.yaml")
    spec = yaml.safe_load((FIXTURE / "spec.yaml").read_text(encoding="utf-8"))
    context = paper_aesthetic_context.load_optional_paper_aesthetic_context(FIXTURE, spec)

    assert intent["fixture"] == "fig2_charge_transport_mechanism"
    assert context is not None
    role = paper_aesthetic_context.matching_figure_role(
        context, "fig2_charge_transport_mechanism"
    )
    assert role["role"] == "overview_mechanism"


def test_fig2_briefing_requires_host_critique_when_reference_is_absent() -> None:
    """Reference-free intent/rules must still make the critique gate explicit."""
    assert has_reference_free_grounding_context(FIXTURE)


def test_fig2_uses_progressive_trapping_sequence_and_standard_output() -> None:
    source = (FIXTURE / "fig2_charge_transport_mechanism.tex").read_text(encoding="utf-8")
    contract = yaml.safe_load((FIXTURE / "semantic_contract.yaml").read_text(encoding="utf-8"))

    assert "$E_\\mathrm{app}=15\\,\\mathrm{MV\\,m^{-1}}$" in source
    assert "held during acquisition" in source
    assert "same MIM geometry; held field and time progress left to right" in source
    assert "Idealized dielectric" in source
    assert "bound polarization reference" in source
    assert "Sulfur-rich copolymer: progressive trapping" in source
    assert "early field-on" in source
    assert "progressive trapping" in source
    assert "long-lived occupied state" in source
    assert "trapState" in source
    assert "currentDot" in source
    assert "captureCue" in source
    assert "currentStrong" in source
    assert "currentSoft" in source
    assert "{empty}" in source
    assert "{occupied}" in source
    assert "Qualitative output" in source
    assert "$\\log I$" in source
    assert "$\\log t$" in source
    assert "early power law" in source
    assert "persistent relaxation" in source
    assert "traceEarly" in source
    assert "traceLate" in source
    assert "fitReference" in source
    assert "at (12.20,2.35)" in source
    assert "ideal: rapid decay" not in source
    assert "localized charge capture" not in source
    assert "reduces mobile leakage" not in source
    assert "traceIdeal" not in source
    assert "traceControl" not in source
    assert "referenceRule" not in source
    assert "$I_\\mathrm{meas}/I_\\mathrm{early}$" not in source
    assert "PI/PTFE: below reference" not in source
    assert "complete current blockage" not in source
    assert "panel_a.source_polarity_claim" in contract["forbidden_implications"]
    assert "panel_a.unmeasured_ideal_current_control" in contract["forbidden_implications"]
    assert "panel_a.direct_mobile_leakage_suppression_claim" in contract["forbidden_implications"]
    assert "transient_readout_uses_standard_log_log_current_grammar" in contract[
        "protected_relations"
    ]


def test_fig2_declares_the_parent_slot_and_a_single_panel_letter_owner() -> None:
    spec = yaml.safe_load((FIXTURE / "spec.yaml").read_text(encoding="utf-8"))
    source = (FIXTURE / "fig2_charge_transport_mechanism.tex").read_text(encoding="utf-8")

    contract = spec["final_size_contract"]
    assert contract["target_width_mm"] == 180.0
    assert contract["natural_size_mm"] == [180.0, 51.02]
    assert contract["double_column_reference_mm"]["nature_communications"] == 180.0

    integration = spec["panel_integration"]
    assert integration["host_layout"] == "fig2_charge_transport_4panel"
    assert integration["slot_size_mm"] == [180.0, 53.19]
    assert integration["panel_content_size_mm"] == spec["final_size_contract"]["natural_size_mm"]
    assert integration["panel_letter_owner"] == "host_data_pipeline"
    assert "\\resizebox{180.0mm}{!}{%" in source
    assert "\\node[panelLetter" not in source


def test_fig2_declares_rearrangeable_composition_units() -> None:
    scene = composition_scene.build_semantic_scene_model(
        "fig2_charge_transport_mechanism", workspace_root=PLUGIN_ROOT
    )

    assert scene["status"] == "ready"
    assert set(scene["objects"]) == {
        "comparison_frame",
        "reference_dielectric",
        "sulfur_working_state",
        "qualitative_current_readout",
    }
    assert scene["objects"]["qualitative_current_readout"]["anchor_target"] == (
        "sulfur_working_state"
    )


def test_fig2_binds_the_comparison_arrow_to_the_readout_boundary() -> None:
    spec = yaml.safe_load((FIXTURE / "spec.yaml").read_text(encoding="utf-8"))
    source = (FIXTURE / "fig2_charge_transport_mechanism.tex").read_text(encoding="utf-8")

    assert "(comparison_out)--(readout_entry)" in source
    assertion = spec["named_endpoint_assertions"][0]
    assert assertion["anchor_style"] == "storyArrow"
    assert assertion["required_anchors"] == ["comparison_out", "readout_entry"]


def test_fig2_declares_material_and_readout_grammar() -> None:
    intent = yaml.safe_load((FIXTURE / "aesthetic_intent.yaml").read_text(encoding="utf-8"))
    source = (FIXTURE / "fig2_charge_transport_mechanism.tex").read_text(encoding="utf-8")

    assert intent["reference_style"] == "mechanism_schematic"
    assert {
        lever["id"] for lever in intent["aesthetic_levers"]
    } >= {
        "causal_hierarchy",
        "material_texture_authorship",
        "color_and_stroke_economy",
        "print_scale_typography",
        "field_condition_embodiment",
        "log_log_power_law_grammar",
        "flat_mim_layer_hierarchy",
        "bound_dipole_pairing",
    }
    assert "dipoleBody" in source
    assert "ellipse [x radius=0.15, y radius=0.22]" in source
    assert "circle [radius=0.042]" in source
    assert "trapState" in source
    assert "currentDot" in source
    assert "captureCue" in source
    assert "leakageSegment" not in source
    assert "leakageFading" not in source
    assert "top color=" not in source
    assert "bottom color=" not in source


def test_fig2_binds_qualified_localized_state_model_to_progressive_output() -> None:
    contract = yaml.safe_load((FIXTURE / "semantic_contract.yaml").read_text(encoding="utf-8"))

    assert "localized_states_are_a_qualified_working_model_not_direct_proof" in contract[
        "protected_relations"
    ]
    assert any(
        connector["connector_id"] == "panel_a.localized_states_to_mobile_current"
        and connector["from_object"] == "panel_a.localized_charge_states"
        and connector["to_object"] == "panel_a.mobile_current_cue"
        and connector["epistemic_status"] == "qualified_inference"
        for connector in contract["semantic_legibility"]["visible_connectors"]
    )


def test_fig2_progressive_trapping_rule_is_preserved_in_figure_agent_skill() -> None:
    skill = (PLUGIN_ROOT / "skills" / "figure-agent" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "do not let one static trap field stand in for time" in skill
    assert "repeated matched MIM states" in skill
    assert "mobile-current contribution visibly weaken" in skill
    assert "qualified working model" in skill
