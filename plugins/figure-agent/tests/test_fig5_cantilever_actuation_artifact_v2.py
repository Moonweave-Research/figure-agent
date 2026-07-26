from __future__ import annotations

import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN_ROOT / "examples" / "fig5_cantilever_actuation_artifact_v2"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

from semantic_legibility_contract import (  # noqa: E402
    validate_semantic_legibility_contract,
)


def _yaml(name: str) -> dict:
    return yaml.safe_load((FIXTURE / name).read_text(encoding="utf-8"))


def test_fig5_requires_a_transferable_mechanism_contract() -> None:
    spec = _yaml("spec.yaml")
    assert spec["semantic_contract_required"] is True

    contract = validate_semantic_legibility_contract(_yaml("semantic_contract.yaml"))
    assert contract["publication_acceptance"] == "not_claimed"
    assert contract["summary"]["object_role_count"] == 14
    assert contract["summary"]["visible_connector_count"] == 7
    assert contract["summary"]["label_ownership_count"] == 9
    assert contract["summary"]["panel_story_role_count"] == 4


def test_fig5_contract_separates_actuation_charge_from_measurement_meanings() -> None:
    contract = _yaml("semantic_contract.yaml")
    protected = set(contract["protected_relations"])
    forbidden = set(contract["forbidden_implications"])

    assert "charge_phase_is_actuation_state" in protected
    assert "cantilever_faces_drive_electrode_across_air_gap" in protected
    assert "air_gap_coupling_is_capacitor_like_schematic_only" in protected
    assert "conditional_reverse_bend_owns_force_hierarchy" in protected
    assert "clamp_axis_aligns_with_cantilever_centerline" in protected
    assert "panel_a.standalone_two_terminal_charger" in forbidden
    assert "panel_a.polarization_measurement_instrument" in forbidden
    assert "panel_a.esvm_measurement_head" in forbidden
    assert "panel_a.corona_needle" in forbidden


def test_fig5_marks_reverse_force_as_conditional_after_isolation() -> None:
    contract = _yaml("semantic_contract.yaml")
    connectors = {
        item["connector_id"]: item
        for item in contract["semantic_legibility"]["visible_connectors"]
    }
    panel_story = {
        item["panel_id"]: item
        for item in contract["semantic_legibility"]["panel_story"]["panels"]
    }

    coulomb = connectors["panel_b.isolation_enables_reversed_force"]
    assert coulomb["epistemic_status"] == "conditional"
    assert coulomb["render_style"] == "force_conditional"
    assert coulomb["condition"]
    assert panel_story["B"]["role"] == "workflow"
    assert panel_story["C"]["role"] == "mechanism"
    sequence = contract["semantic_legibility"]["panel_story"]["causal_sequence"]
    assert [item["stage"] for item in sequence["stages"]] == [
        "preparation",
        "isolation",
        "perturbation",
        "response",
    ]


def test_fig5_declares_the_reverse_bend_as_conditional_not_a_second_snapshot() -> None:
    contract = _yaml("semantic_contract.yaml")
    roles = {
        item["object_id"]: item
        for item in contract["semantic_legibility"]["object_roles"]
    }

    reverse_bend = roles["panel_c.conditional_reverse_bend"]
    assert reverse_bend["declared_role"] == "conditional_reverse_bend_response"
    assert "observed_comparison" in reverse_bend["forbidden_readings"]


def test_fig5_declares_rendered_charge_to_isolation_and_response_stages() -> None:
    spec = _yaml("spec.yaml")
    checks = {item["id"]: item for item in spec["process_stage_visibility_checks"]}

    assert [stage["id"] for stage in checks["isolation-boundary-state"]["stages"]] == [
        "source-off",
        "clip-open",
    ]
    assert [stage["id"] for stage in checks["qualitative-response-sequence"]["stages"]] == [
        "observation-origin",
        "reversed-drive",
        "recovery",
    ]
    origin_phrases = checks["qualitative-response-sequence"]["stages"][0]["text_phrases"]
    assert {tuple(item["words"]) for item in origin_phrases} == {
        ("t", "=", "0"),
        ("OFF",),
    }


def test_fig5_declares_deterministic_clamp_axis_geometry_check() -> None:
    spec = _yaml("spec.yaml")
    assertions = {item["id"]: item for item in spec["tex_assertions"]}
    alignment = assertions["clamp-axis-bisects-cantilever-fixed-end"]
    assert alignment["kind"] == "centerline_aligned"
    assert alignment["edge_coordinates"] == [
        "panel-c-cantilever-left",
        "panel-c-cantilever-right",
    ]
    assert alignment["reference_coordinate"] == "panel-c-clamp-axis"


def test_fig5_contract_keeps_style_free_and_coordinates_free() -> None:
    contract = _yaml("semantic_contract.yaml")

    def keys(value: object) -> set[str]:
        if isinstance(value, dict):
            result = set(value)
            for child in value.values():
                result.update(keys(child))
            return {str(item) for item in result}
        if isinstance(value, list):
            result: set[str] = set()
            for child in value:
                result.update(keys(child))
            return result
        return set()

    forbidden_keys = {item.lower() for item in keys(contract)}
    assert "tikz" not in forbidden_keys
    assert "coordinates" not in forbidden_keys
    assert "primitive" not in forbidden_keys
