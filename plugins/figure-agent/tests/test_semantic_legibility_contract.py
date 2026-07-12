from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "quality"))

from semantic_legibility_contract import (  # noqa: E402
    SemanticLegibilityContractError,
    validate_semantic_legibility_contract,
)

SCRIPT = PLUGIN_ROOT / "scripts" / "quality" / "semantic_legibility_contract.py"
COMPILE_SCRIPT = PLUGIN_ROOT / "scripts" / "compile.sh"


def valid_contract() -> dict:
    return {
        "schema": "figure-agent.failure-first-semantic-contract.v1",
        "required_objects": [
            "panel_f.mechanical_jig",
            "panel_f.cantilever",
            "panel_f.trapped_charge_markers",
        ],
        "semantic_legibility": {
            "object_roles": [
                {
                    "object_id": "panel_f.mechanical_jig",
                    "declared_role": "mechanical_fixture",
                    "forbidden_readings": ["electrical_contact"],
                },
                {
                    "object_id": "panel_f.cantilever",
                    "declared_role": "mechanical_member",
                    "forbidden_readings": [],
                },
                {
                    "object_id": "panel_f.trapped_charge_markers",
                    "declared_role": "scientific_symbol",
                    "forbidden_readings": ["decorative_bead"],
                },
            ],
            "visible_connectors": [
                {
                    "connector_id": "panel_f.jig_holds_cantilever",
                    "from_object": "panel_f.mechanical_jig",
                    "to_object": "panel_f.cantilever",
                    "declared_role": "mechanical_attachment",
                    "render_style": "mechanical_structural",
                }
            ],
            "forbidden_connectors": [
                {
                    "from_object": "panel_f.mechanical_jig",
                    "to_object": "panel_f.cantilever",
                    "declared_role": "electrical_contact",
                }
            ],
            "label_ownership": [
                {
                    "label_id": "panel_f.trapped_charge_label",
                    "owner": "panel_f.trapped_charge_markers",
                }
            ],
            "electrical_topology": {
                "nodes": [
                    {
                        "object_id": "panel_f.cantilever",
                        "declared_state": "floating",
                    },
                    {
                        "object_id": "panel_f.mechanical_jig",
                        "declared_state": "electrically_unmodeled",
                    },
                ],
                "connections": [],
            },
        },
        "publication_acceptance": "not_claimed",
    }


def test_accepts_declared_object_connector_and_label_roles() -> None:
    result = validate_semantic_legibility_contract(valid_contract())
    assert result["summary"] == {
        "object_role_count": 3,
        "visible_connector_count": 1,
        "forbidden_connector_count": 1,
        "label_ownership_count": 1,
        "electrical_node_count": 2,
        "electrical_connection_count": 0,
        "floating_object_count": 1,
        "visual_review_required": True,
    }
    assert result["publication_acceptance"] == "not_claimed"


def test_accepts_non_electrical_figure_without_topology_section() -> None:
    contract = valid_contract()
    del contract["semantic_legibility"]["electrical_topology"]
    result = validate_semantic_legibility_contract(contract)
    assert result["summary"]["electrical_node_count"] == 0
    assert result["summary"]["electrical_connection_count"] == 0
    assert result["summary"]["floating_object_count"] == 0


def test_rejects_required_object_without_declared_role() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["object_roles"].pop()
    with pytest.raises(
        SemanticLegibilityContractError,
        match="required_object_role_missing",
    ):
        validate_semantic_legibility_contract(contract)


def test_rejects_visible_connector_without_both_endpoints() -> None:
    contract = valid_contract()
    del contract["semantic_legibility"]["visible_connectors"][0]["to_object"]
    with pytest.raises(
        SemanticLegibilityContractError,
        match="visible_connector_endpoint_invalid",
    ):
        validate_semantic_legibility_contract(contract)


def test_rejects_mechanical_attachment_with_electrical_render_style() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["visible_connectors"][0][
        "render_style"
    ] = "electrical_bias_lead"
    with pytest.raises(
        SemanticLegibilityContractError,
        match="visible_connector_style_role_mismatch",
    ):
        validate_semantic_legibility_contract(contract)


@pytest.mark.parametrize("owner", [None, ["panel_f.cantilever", "panel_f.mechanical_jig"]])
def test_rejects_label_without_one_declared_owner(owner: object) -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["label_ownership"][0]["owner"] = owner
    with pytest.raises(
        SemanticLegibilityContractError,
        match="label_owner_invalid",
    ):
        validate_semantic_legibility_contract(contract)


def test_rejects_declared_role_as_its_own_forbidden_reading() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["object_roles"][0][
        "forbidden_readings"
    ] = ["mechanical_fixture"]
    with pytest.raises(
        SemanticLegibilityContractError,
        match="object_role_contradiction",
    ):
        validate_semantic_legibility_contract(contract)


def test_rejects_electrical_connection_to_floating_object() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["electrical_topology"]["connections"] = [
        {
            "connection_id": "panel_f.false_sample_ground",
            "from_object": "panel_f.cantilever",
            "to_object": "panel_f.mechanical_jig",
            "declared_role": "ground_return",
        }
    ]
    with pytest.raises(
        SemanticLegibilityContractError,
        match="floating_object_connected",
    ):
        validate_semantic_legibility_contract(contract)


def test_rejects_electrical_connection_to_unmodeled_fixture() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["electrical_topology"]["nodes"][0][
        "declared_state"
    ] = "source"
    contract["semantic_legibility"]["electrical_topology"]["connections"] = [
        {
            "connection_id": "panel_f.false_fixture_bias",
            "from_object": "panel_f.cantilever",
            "to_object": "panel_f.mechanical_jig",
            "declared_role": "electrical_contact",
        }
    ]
    with pytest.raises(
        SemanticLegibilityContractError,
        match="electrically_unmodeled_object_connected",
    ):
        validate_semantic_legibility_contract(contract)


def test_rejects_visible_electrical_connector_omitted_from_topology() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["visible_connectors"].append(
            {
                "connector_id": "panel_f.hidden_sample_lead",
                "from_object": "panel_f.cantilever",
                "to_object": "panel_f.mechanical_jig",
                "declared_role": "electrical_lead",
                "render_style": "electrical_bias_lead",
            }
    )
    with pytest.raises(
        SemanticLegibilityContractError,
        match="electrical_connector_topology_missing",
    ):
        validate_semantic_legibility_contract(contract)


def test_rejects_unknown_electrical_state() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["electrical_topology"]["nodes"][0][
        "declared_state"
    ] = "probably_grounded"
    with pytest.raises(
        SemanticLegibilityContractError,
        match="electrical_node_invalid",
    ):
        validate_semantic_legibility_contract(contract)


def test_contract_cli_fails_closed_on_missing_role(tmp_path: Path) -> None:
    path = tmp_path / "semantic_contract.yaml"
    contract = valid_contract()
    contract["semantic_legibility"]["object_roles"].pop()
    path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "required_object_role_missing" in result.stderr


def test_compile_pipeline_runs_opt_in_contract_gate_before_tex_lint() -> None:
    script = COMPILE_SCRIPT.read_text(encoding="utf-8")
    contract_gate = script.index("semantic_legibility_contract.py")
    tex_lint = script.index("scripts/lint_tex.py")
    assert contract_gate < tex_lint
    assert 'if [[ -f "$SEMANTIC_CONTRACT" ]]' in script
