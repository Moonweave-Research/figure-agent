from __future__ import annotations

import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PLUGIN_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT))

import compatibility_command_contracts  # noqa: E402
import fig_e2e_smoke  # noqa: E402
import fig_improve  # noqa: E402
import fig_loop  # noqa: E402

EXPECTED_FIELDS = {
    "command",
    "disposition",
    "route_successor",
    "evidence_role",
    "evidence_schema",
    "write_authority",
    "fail_closed_on",
    "publication_acceptance",
}


def test_registry_has_exact_initial_membership_and_schema() -> None:
    registry = compatibility_command_contracts.serialize_registry()

    assert registry["schema"] == (
        "figure-agent.compatibility-command-contract-registry.v1"
    )
    assert registry["contracts"] == [
        {
            "command": "loop",
            "disposition": "internal_compatibility",
            "route_successor": ["status", "run"],
            "evidence_role": "verify_only_checkpoint",
            "evidence_schema": "figure-agent.fig-loop-run.v1",
            "write_authority": "scratch_checkpoint_only",
            "fail_closed_on": [
                "canonical_attempt_not_absent",
                "fixture_admission_busy",
                "unsafe_fixture_or_runs_root",
            ],
            "publication_acceptance": "not_claimed",
        },
        {
            "command": "improve",
            "disposition": "internal_compatibility",
            "route_successor": ["run"],
            "evidence_role": "canonical_run_wrapper_summary",
            "evidence_schema": "figure-agent.improve.v1",
            "write_authority": "delegated_run_allowlist_only",
            "fail_closed_on": ["retired_aggressive_search"],
            "publication_acceptance": "not_claimed",
        },
        {
            "command": "e2e-smoke",
            "disposition": "internal_compatibility",
            "route_successor": ["status", "run"],
            "evidence_role": "operational_smoke",
            "evidence_schema": "figure-agent.e2e-smoke.v1",
            "write_authority": "compile_export_and_scratch_smoke_only",
            "fail_closed_on": [
                "canonical_attempt_not_absent",
                "fixture_admission_busy",
                "unsafe_fixture_or_runs_root",
                "pipeline_step_failure",
                "repeat_instability",
            ],
            "publication_acceptance": "not_claimed",
        },
    ]
    assert len({contract["command"] for contract in registry["contracts"]}) == 3
    assert all(set(contract) == EXPECTED_FIELDS for contract in registry["contracts"])


def test_registry_contracts_are_truthful_and_bounded() -> None:
    schemas = {
        "loop": fig_loop.RUN_SCHEMA,
        "improve": fig_improve.SCHEMA,
        "e2e-smoke": fig_e2e_smoke.SCHEMA,
    }

    for contract in compatibility_command_contracts.serialize_registry()["contracts"]:
        assert contract["disposition"] == "internal_compatibility"
        assert contract["route_successor"]
        assert set(contract["route_successor"]) <= {"status", "run"}
        assert contract["evidence_schema"] == schemas[contract["command"]]
        assert contract["publication_acceptance"] == "not_claimed"


def test_registry_contract_representation_is_immutable() -> None:
    contract = compatibility_command_contracts.COMMAND_CONTRACTS[0]

    with pytest.raises(FrozenInstanceError):
        contract.command = "changed"

    assert isinstance(contract.route_successor, tuple)
    assert isinstance(contract.fail_closed_on, tuple)
