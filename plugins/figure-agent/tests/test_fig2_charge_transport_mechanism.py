from __future__ import annotations

import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig2_charge_transport_mechanism"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

import composition_scene  # noqa: E402
from semantic_legibility_contract import validate_semantic_legibility_contract  # noqa: E402


def test_fig2_declares_a_parallel_material_comparison_contract() -> None:
    contract = yaml.safe_load((FIXTURE / "semantic_contract.yaml").read_text(encoding="utf-8"))

    result = validate_semantic_legibility_contract(contract)
    comparison = result["semantic_legibility"]["parallel_comparisons"][0]

    assert comparison["members"] == [
        "panel_a.ideal_dielectric",
        "panel_a.sulfur_copolymer",
    ]
    assert result["summary"]["parallel_comparison_count"] == 1
    assert "mim_comparison_uses_matched_footprints" in contract["protected_relations"]
    assert all(
        {connector["from_object"], connector["to_object"]}
        != {"panel_a.ideal_dielectric", "panel_a.sulfur_copolymer"}
        for connector in result["semantic_legibility"]["visible_connectors"]
    )


def test_fig2_redraw_uses_lateral_shared_field_comparison_without_legacy_copy() -> None:
    source = (FIXTURE / "fig2_charge_transport_mechanism.tex").read_text(encoding="utf-8")

    assert "$E_\\mathrm{app}=15\\,\\mathrm{MV\\,m^{-1}}$" in source
    assert "held during acquisition" in source
    assert "matched MIM cells under a held field" in source
    assert "fitReference/.style" in source
    assert "traceIdeal/.style" in source
    assert "early-fit projection" in source
    assert "ideal: rapid decay" in source
    assert "localized-state response" in source
    assert "$\\log I$" in source
    assert "$\\log(t/\\mathrm{s})$" in source
    assert "{9.22/2,12.12/30,15.30/300}" not in source
    assert "windowBoundary" not in source
    assert "{$t=0$}" not in source
    assert "{vs.}" not in source
    assert "storyRail" not in source
    assert "material contrast" not in source
    assert "comparisonArrow" not in source
    assert "trapAmber" not in source
    assert "localizedState" in source
    assert "localized charge capture" in source
    assert "reduces mobile leakage" in source
    assert "leakageSegment" not in source
    assert "leakageFading" not in source
    assert "sulfurTrace" in source
    assert "sulfurTraceFaint" in source
    assert "sulfurBead" in source
    assert "sulfurStateF" in source
    assert "sulfurStateA,sulfurStateB,sulfurStateC,sulfurStateD,sulfurStateE,sulfurStateF" in source
    assert "\\def\\mimCellWidth" in source
    assert source.count("\\mimCellWidth") >= 8
    assert "Conventional dielectric" not in source
    assert "charge drains" not in source
    sulfur_block = source.split("object=sulfur_working_state", 1)[1].split(
        "fig-agent:end object=sulfur_working_state", 1
    )[0]
    assert "{$+$}" in source
    assert "{$-$}" in source
    assert "{$+$}" not in sulfur_block
    assert "{$-$}" not in sulfur_block


def test_fig2_declares_the_parent_slot_and_a_single_panel_letter_owner() -> None:
    spec = yaml.safe_load((FIXTURE / "spec.yaml").read_text(encoding="utf-8"))
    source = (FIXTURE / "fig2_charge_transport_mechanism.tex").read_text(encoding="utf-8")

    integration = spec["panel_integration"]
    assert integration["host_layout"] == "fig2_charge_transport_4panel"
    assert integration["slot_size_mm"] == [166.53, 53.19]
    assert integration["panel_content_size_mm"] == spec["final_size_contract"]["natural_size_mm"]
    assert integration["panel_letter_owner"] == "host_data_pipeline"
    assert "\\resizebox{166.53mm}{!}{%" in source
    assert "\\node[panelLetter" not in source


def test_fig2_declares_rearrangeable_composition_units() -> None:
    scene = composition_scene.build_semantic_scene_model(
        "fig2_charge_transport_mechanism", workspace_root=PLUGIN_ROOT
    )

    assert scene["status"] == "ready"
    assert set(scene["objects"]) == {
        "comparison_frame",
        "ideal_baseline",
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


def test_fig2_declares_and_uses_an_editorial_material_grammar() -> None:
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
    assert "rapid polarization" in source
    assert "localized charge capture" in source
    assert "reduces mobile leakage" in source
    assert "slow relaxation" in source
    assert "$E_\\mathrm{app}$" in source
    assert "{vs.}" not in source
    assert "charge drains" not in source
    assert "top color=" not in source
    assert "bottom color=" not in source
    assert "dipoleBody" in source
    assert "ellipse [x radius=0.17, y radius=0.25]" in source
    assert "polarizationVector" not in source
    material_grammar = next(
        lever for lever in intent["aesthetic_levers"] if lever["id"] == "material_texture_authorship"
    )
    assert any("smooth worms" in signal for signal in material_grammar["positive_signals"])
    assert any("V-shaped scraps" in signal for signal in material_grammar["positive_signals"])


def test_fig2_declares_log_log_power_law_grammar_for_the_qualitative_readout() -> None:
    contract = yaml.safe_load((FIXTURE / "semantic_contract.yaml").read_text(encoding="utf-8"))
    source = (FIXTURE / "fig2_charge_transport_mechanism.tex").read_text(encoding="utf-8")

    assert "transient_readout_declares_log_log_power_law_geometry" in contract[
        "protected_relations"
    ]
    assert "panel_a.time_calibrated_mini_graph" in contract["forbidden_implications"]
    roles = {
        object_role["object_id"]: object_role["declared_role"]
        for object_role in contract["semantic_legibility"]["object_roles"]
    }
    assert roles["panel_a.log_log_axes"] == "symbolic_logarithmic_axis_grammar"
    assert roles["panel_a.ideal_current_decay"] == (
        "qualitative_rapid_ideal_polarization_current_decay"
    )
    assert roles["panel_a.sulfur_current_response"] == (
        "qualitative_delayed_sulfur_rich_current_response"
    )
    assert (
        "current_readout_contrasts_rapid_ideal_decay_with_delayed_sulfur_response"
        in contract["protected_relations"]
    )
    assert "\\draw[traceIdeal]" in source
    assert "\\draw[traceEarly] (9.22,3.16)--(12.12,2.50);" in source
    assert "\\draw[fitReference] (12.12,2.50)--(15.30,1.78);" in source
    assert "\\draw[traceLate] (12.12,2.50)--(15.30,2.16);" in source


def test_fig2_binds_localized_relaxation_to_the_late_readout_as_a_working_model() -> None:
    contract = yaml.safe_load((FIXTURE / "semantic_contract.yaml").read_text(encoding="utf-8"))

    assert (
        "localized_state_relaxation_is_the_qualitative_cause_of_the_late_residual"
        in contract["protected_relations"]
    )
    assert any(
        connector["connector_id"] == "panel_a.localized_relaxation_to_late_window"
        and connector["from_object"] == "panel_a.long_lived_relaxation"
        and connector["to_object"] == "panel_a.late_window"
        for connector in contract["semantic_legibility"]["visible_connectors"]
    )
    assert "panel_a.leakage_suppression" in contract["required_objects"]
    assert (
        "localized_capture_suppresses_mobile_leakage_before_slow_relaxation"
        in contract["protected_relations"]
    )
