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
        "panel_story_role_count": 0,
        "parallel_comparison_count": 0,
        "electrical_node_count": 2,
        "electrical_connection_count": 0,
        "floating_object_count": 1,
        "visual_review_required": True,
        "forbidden_implication_count": 0,
        "protected_relation_count": 0,
        "transfer_relations_required": False,
    }
    assert result["publication_acceptance"] == "not_claimed"


def test_accepts_non_electrical_figure_without_topology_section() -> None:
    contract = valid_contract()
    del contract["semantic_legibility"]["electrical_topology"]
    result = validate_semantic_legibility_contract(contract)
    assert result["summary"]["electrical_node_count"] == 0
    assert result["summary"]["electrical_connection_count"] == 0
    assert result["summary"]["floating_object_count"] == 0


def test_accepts_distinct_panel_reader_tasks_in_declared_order() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["panel_story"] = {
        "reading_order": ["A", "B"],
        "panels": [
            {"panel_id": "A", "role": "setup", "reader_task": "Establish the geometry."},
            {"panel_id": "B", "role": "result", "reader_task": "Show the response."},
        ],
    }

    result = validate_semantic_legibility_contract(contract)

    assert result["summary"]["panel_story_role_count"] == 2


def _parallel_comparison_contract() -> dict:
    contract = valid_contract()
    required = [
        "panel_a.measurement",
        "panel_a.conventional",
        "panel_a.sulfur",
        "panel_a.readout",
    ]
    contract["required_objects"] = required
    contract["semantic_legibility"]["object_roles"] = [
        {"object_id": object_id, "declared_role": "scientific_symbol", "forbidden_readings": []}
        for object_id in required
    ]
    contract["semantic_legibility"]["visible_connectors"] = [
        {
            "connector_id": "measurement_to_conventional",
            "from_object": "panel_a.measurement",
            "to_object": "panel_a.conventional",
            "declared_role": "story_stage_transition",
            "render_style": "stage_transition",
        },
        {
            "connector_id": "measurement_to_sulfur",
            "from_object": "panel_a.measurement",
            "to_object": "panel_a.sulfur",
            "declared_role": "story_stage_transition",
            "render_style": "stage_transition",
        },
        {
            "connector_id": "conventional_to_readout",
            "from_object": "panel_a.conventional",
            "to_object": "panel_a.readout",
            "declared_role": "readout_transition",
            "render_style": "stage_transition",
        },
        {
            "connector_id": "sulfur_to_readout",
            "from_object": "panel_a.sulfur",
            "to_object": "panel_a.readout",
            "declared_role": "readout_transition",
            "render_style": "stage_transition",
        },
    ]
    contract["semantic_legibility"]["forbidden_connectors"] = []
    contract["semantic_legibility"]["label_ownership"] = []
    contract["semantic_legibility"]["parallel_comparisons"] = [
        {
            "comparison_id": "materials",
            "members": ["panel_a.conventional", "panel_a.sulfur"],
            "shared_input": "panel_a.measurement",
            "shared_output": "panel_a.readout",
            "comparison_basis": "schematic_state",
            "input_connector_ids": ["measurement_to_conventional", "measurement_to_sulfur"],
            "output_connector_ids": ["conventional_to_readout", "sulfur_to_readout"],
        }
    ]
    contract["semantic_legibility"].pop("electrical_topology")
    return contract


def test_accepts_parallel_comparison_with_shared_fork_and_merge() -> None:
    result = validate_semantic_legibility_contract(_parallel_comparison_contract())

    assert result["summary"]["parallel_comparison_count"] == 1


def test_rejects_parallel_comparison_that_connects_member_states_directly() -> None:
    contract = _parallel_comparison_contract()
    contract["semantic_legibility"]["visible_connectors"].append(
        {
            "connector_id": "conventional_to_sulfur",
            "from_object": "panel_a.conventional",
            "to_object": "panel_a.sulfur",
            "declared_role": "conceptual_material_comparison",
            "render_style": "comparison_transition",
        }
    )

    with pytest.raises(
        SemanticLegibilityContractError,
        match="parallel_comparison_member_connector_forbidden",
    ):
        validate_semantic_legibility_contract(contract)


def test_rejects_parallel_comparison_without_both_shared_input_branches() -> None:
    contract = _parallel_comparison_contract()
    contract["semantic_legibility"]["parallel_comparisons"][0]["input_connector_ids"] = [
        "measurement_to_conventional",
        "conventional_to_readout",
    ]

    with pytest.raises(
        SemanticLegibilityContractError,
        match="parallel_comparison_connector_topology_invalid",
    ):
        validate_semantic_legibility_contract(contract)


def test_rejects_redundant_panel_story_roles() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["panel_story"] = {
        "reading_order": ["A", "B"],
        "panels": [
            {"panel_id": "A", "role": "setup", "reader_task": "Establish the geometry."},
            {"panel_id": "B", "role": "setup", "reader_task": "Repeat the geometry."},
        ],
    }

    with pytest.raises(SemanticLegibilityContractError, match="panel_story_panel_invalid"):
        validate_semantic_legibility_contract(contract)


def test_accepts_explicit_four_stage_causal_sequence() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["panel_story"] = {
        "reading_order": ["A", "B", "C", "D"],
        "panels": [
            {"panel_id": "A", "role": "setup", "reader_task": "Prepare the state."},
            {"panel_id": "B", "role": "workflow", "reader_task": "Isolate the state."},
            {"panel_id": "C", "role": "mechanism", "reader_task": "Perturb the state."},
            {"panel_id": "D", "role": "result", "reader_task": "Read the response."},
        ],
        "causal_sequence": {
            "stages": [
                {"panel_id": "A", "stage": "preparation"},
                {"panel_id": "B", "stage": "isolation"},
                {"panel_id": "C", "stage": "perturbation"},
                {"panel_id": "D", "stage": "response"},
            ]
        },
    }
    validate_semantic_legibility_contract(contract)


def test_rejects_causal_sequence_that_collapses_isolation_after_perturbation() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["panel_story"] = {
        "reading_order": ["A", "B", "C", "D"],
        "panels": [
            {"panel_id": "A", "role": "setup", "reader_task": "Prepare the state."},
            {"panel_id": "B", "role": "workflow", "reader_task": "Isolate the state."},
            {"panel_id": "C", "role": "mechanism", "reader_task": "Perturb the state."},
            {"panel_id": "D", "role": "result", "reader_task": "Read the response."},
        ],
        "causal_sequence": {
            "stages": [
                {"panel_id": "A", "stage": "preparation"},
                {"panel_id": "B", "stage": "perturbation"},
                {"panel_id": "C", "stage": "isolation"},
                {"panel_id": "D", "stage": "response"},
            ]
        },
    }
    with pytest.raises(SemanticLegibilityContractError, match="causal_sequence_order_invalid"):
        validate_semantic_legibility_contract(contract)


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


def test_rejects_force_direction_without_epistemic_status() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["visible_connectors"] = [
        {
            "connector_id": "panel_f.force",
            "from_object": "panel_f.mechanical_jig",
            "to_object": "panel_f.cantilever",
            "declared_role": "force_direction",
            "render_style": "force_directional",
        }
    ]

    with pytest.raises(
        SemanticLegibilityContractError, match="force_direction_epistemic_status_invalid"
    ):
        validate_semantic_legibility_contract(contract)


def test_rejects_conditional_force_without_condition_or_conditional_style() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["visible_connectors"] = [
        {
            "connector_id": "panel_f.force",
            "from_object": "panel_f.mechanical_jig",
            "to_object": "panel_f.cantilever",
            "declared_role": "force_direction",
            "render_style": "force_directional",
            "epistemic_status": "conditional",
        }
    ]

    with pytest.raises(
        SemanticLegibilityContractError, match="force_direction_condition_missing"
    ):
        validate_semantic_legibility_contract(contract)


def test_accepts_explicitly_conditional_force_direction() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["visible_connectors"] = [
        {
            "connector_id": "panel_f.force",
            "from_object": "panel_f.mechanical_jig",
            "to_object": "panel_f.cantilever",
            "declared_role": "force_direction",
            "render_style": "force_conditional",
            "epistemic_status": "conditional",
            "condition": "Illustrated polarity only.",
        }
    ]

    validate_semantic_legibility_contract(contract)


def test_rejects_observed_comparison_without_evidence_source() -> None:
    contract = valid_contract()
    contract["semantic_legibility"]["panel_story"] = {
        "reading_order": ["A", "B"],
        "panels": [
            {"panel_id": "A", "role": "setup", "reader_task": "Establish the geometry."},
            {
                "panel_id": "B",
                "role": "comparison",
                "reader_task": "Compare observed response states.",
                "comparison_basis": "observed_evidence",
            },
        ],
    }

    with pytest.raises(
        SemanticLegibilityContractError, match="panel_story_evidence_source_missing"
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


def test_contract_cli_writes_hash_bound_validation_evidence(tmp_path: Path) -> None:
    contract_path = tmp_path / "semantic_contract.yaml"
    evidence_path = tmp_path / "build" / "semantic_contract.json"
    contract_path.write_text(yaml.safe_dump(valid_contract(), sort_keys=False), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(contract_path),
            "--json-output",
            str(evidence_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    evidence = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
    assert evidence["schema"] == "figure-agent.semantic-contract-evidence.v1"
    assert evidence["validated"] is True
    assert len(evidence["source_sha256"]) == 64
    assert evidence["publication_acceptance"] == "not_claimed"


def test_required_transfer_relations_reject_missing_lists(tmp_path: Path) -> None:
    path = tmp_path / "semantic_contract.yaml"
    path.write_text(yaml.safe_dump(valid_contract(), sort_keys=False), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(path), "--require-transfer-relations"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "forbidden_implications_invalid" in result.stderr


def test_compile_pipeline_runs_opt_in_contract_gate_before_tex_lint() -> None:
    script = COMPILE_SCRIPT.read_text(encoding="utf-8")
    contract_gate = script.index("semantic_legibility_contract.py")
    tex_lint = script.index("scripts/lint_tex.py")
    assert contract_gate < tex_lint
    assert 'if [[ -f "$SEMANTIC_CONTRACT" ]]' in script
    assert '--json-output "${BUILD_DIR}/semantic_contract.json"' in script


def test_compile_pipeline_falls_back_to_fixture_semantic_contract_for_nested_repairs() -> None:
    script = COMPILE_SCRIPT.read_text(encoding="utf-8")

    assert 'SEMANTIC_CONTRACT="$(dirname "$TEX_INPUT")/semantic_contract.yaml"' in script
    assert (
        'if [[ ! -f "$SEMANTIC_CONTRACT" && -n "$FIXTURE_ROOT" && '
        '-f "$FIXTURE_ROOT/semantic_contract.yaml" ]]; then'
        in script
    )
    assert 'SEMANTIC_CONTRACT="$FIXTURE_ROOT/semantic_contract.yaml"' in script
