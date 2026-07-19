"""Truthful contracts for the initial internal compatibility command slice."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REGISTRY_SCHEMA = "figure-agent.compatibility-command-contract-registry.v1"


@dataclass(frozen=True)
class CompatibilityCommandContract:
    command: str
    disposition: str
    route_successor: tuple[str, ...]
    evidence_role: str
    evidence_schema: str
    write_authority: str
    fail_closed_on: tuple[str, ...]
    publication_acceptance: str

    def serialize(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "disposition": self.disposition,
            "route_successor": list(self.route_successor),
            "evidence_role": self.evidence_role,
            "evidence_schema": self.evidence_schema,
            "write_authority": self.write_authority,
            "fail_closed_on": list(self.fail_closed_on),
            "publication_acceptance": self.publication_acceptance,
        }


COMMAND_CONTRACTS = (
    CompatibilityCommandContract(
        command="loop",
        disposition="internal_compatibility",
        route_successor=("status", "run"),
        evidence_role="verify_only_checkpoint",
        evidence_schema="figure-agent.fig-loop-run.v1",
        write_authority="scratch_checkpoint_only",
        fail_closed_on=(
            "canonical_attempt_not_absent",
            "fixture_admission_busy",
            "unsafe_fixture_or_runs_root",
        ),
        publication_acceptance="not_claimed",
    ),
    CompatibilityCommandContract(
        command="improve",
        disposition="internal_compatibility",
        route_successor=("run",),
        evidence_role="canonical_run_wrapper_summary",
        evidence_schema="figure-agent.improve.v1",
        write_authority="delegated_run_allowlist_only",
        fail_closed_on=("retired_aggressive_search",),
        publication_acceptance="not_claimed",
    ),
    CompatibilityCommandContract(
        command="e2e-smoke",
        disposition="internal_compatibility",
        route_successor=("status", "run"),
        evidence_role="operational_smoke",
        evidence_schema="figure-agent.e2e-smoke.v1",
        write_authority="compile_export_and_scratch_smoke_only",
        fail_closed_on=(
            "canonical_attempt_not_absent",
            "fixture_admission_busy",
            "unsafe_fixture_or_runs_root",
            "pipeline_step_failure",
            "repeat_instability",
        ),
        publication_acceptance="not_claimed",
    ),
)


def command_names() -> frozenset[str]:
    return frozenset(contract.command for contract in COMMAND_CONTRACTS)


def serialize_registry() -> dict[str, Any]:
    return {
        "schema": REGISTRY_SCHEMA,
        "contracts": [contract.serialize() for contract in COMMAND_CONTRACTS],
    }
