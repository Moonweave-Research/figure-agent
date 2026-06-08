"""Explicit candidate apply boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import candidate_contracts
import fixture_identity
import runtime_paths

SCHEMA = "figure-agent.candidate-apply-result.v1"


def _base_result(name: str, manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": name,
        "candidate_id": manifest.get("candidate_id"),
        "applied": False,
    }


def _effective_authority(manifest: dict[str, Any]) -> str:
    verification = manifest.get("verification")
    hard_gate_state = (
        verification.get("hard_gate_state")
        if isinstance(verification, dict)
        else "rejected"
    )
    effective = candidate_contracts.effective_apply_authority(
        str(manifest.get("apply_authority", "rejected")),
        str(hard_gate_state),
    )
    declared = manifest.get("effective_apply_authority")
    if declared is not None and declared != effective:
        raise candidate_contracts.CandidateContractError("effective_apply_authority_mismatch")
    return effective


def apply_candidate(
    name: str,
    manifest: dict[str, Any],
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    result = _base_result(name, manifest)
    if _effective_authority(manifest) != "apply_eligible":
        result["error"] = {"code": "not_apply_eligible"}
        return result
    if not apply:
        result["dry_run"] = True
        return result

    result["error"] = {"code": "apply_not_implemented_for_non_refusal_path"}
    result["workspace_root"] = str(paths.workspace_root)
    return result
