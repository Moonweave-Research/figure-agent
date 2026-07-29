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
    assert all(
        {connector["from_object"], connector["to_object"]}
        != {"panel_a.ideal_dielectric", "panel_a.sulfur_copolymer"}
        for connector in result["semantic_legibility"]["visible_connectors"]
    )


def test_fig2_redraw_uses_lateral_shared_field_comparison_without_legacy_copy() -> None:
    source = (FIXTURE / "fig2_charge_transport_mechanism.tex").read_text(encoding="utf-8")

    assert "held ON during acquisition" in source
    assert "same MIM geometry" in source
    assert "storyRail" not in source
    assert "material contrast" not in source
    assert "comparisonArrow" not in source
    assert "trapAmber" not in source
    assert "localizedState" in source
    assert "sulfurTrace" in source
    assert "Conventional dielectric" not in source
    assert "charge drains" not in source
    assert "{$+$}" not in source
    assert "{$-$}" not in source


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
