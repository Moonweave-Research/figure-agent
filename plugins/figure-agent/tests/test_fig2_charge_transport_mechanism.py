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
    assert "early-fit extrapolation" in source
    assert "{vs.}" not in source
    assert "storyRail" not in source
    assert "material contrast" not in source
    assert "comparisonArrow" not in source
    assert "trapAmber" not in source
    assert "localizedState" in source
    assert "sulfurTrace" in source
    assert "\\def\\mimCellWidth" in source
    assert source.count("\\mimCellWidth") >= 8
    assert "Conventional dielectric" not in source
    assert "charge drains" not in source
    assert "{$+$}" not in source
    assert "{$-$}" not in source


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
    }
    assert "rapid polarization" in source
    assert "localized states" in source
    assert "slow relaxation" in source
    assert "$E_\\mathrm{app}$" in source
    assert "{vs.}" not in source
    assert "charge drains" not in source


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
