from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

import composition_acceptance_support as support

READINESS_SCHEMA: Final = "figure-agent.composition-apply-readiness.v1"
ACCEPTANCE_SCHEMA: Final = "figure-agent.composition-acceptance.v1"
WRITE_RESULT_SCHEMA: Final = "figure-agent.composition-acceptance-write-result.v1"
CompositionAcceptanceError = support.CompositionAcceptanceError


def _blocking_reasons(facts: dict[str, Any], candidate_set: dict[str, Any]) -> list[str]:
    manifest = facts["manifest"]
    operation = facts["operation"]
    source = facts["source"]
    blocking: list[str] = []
    if support.has_stale_evidence(candidate_set):
        blocking.append("refresh_required")
    if support.stage_status(manifest, "prepare") != "success":
        blocking.append("prepare_required")
    if any(support.stage_status(manifest, stage) != "not_run" for stage in support.LATE_STAGES):
        blocking.append("unexpected_render_stage_state")
    if operation.get("kind") != "replace_semantic_block":
        blocking.append("operation_kind_unsupported")
    if not source.is_file():
        blocking.append("base_source_missing")
    elif operation.get("base_source_hash") != support.hash_file(source):
        blocking.append("source_hash_drift")
    expected_copy = manifest.get("hash_evidence", {}).get("source_copy")
    if isinstance(expected_copy, str):
        if expected_copy != support.hash_file(facts["source_copy"]):
            blocking.append("candidate_source_copy_hash_mismatch")
    return blocking


def _not_run_diagnostics(manifest: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "code": f"{stage}_not_run",
            "message": f"{stage} has not run; fixture source mutation remains disabled",
        }
        for stage in support.LATE_STAGES
        if support.stage_status(manifest, stage) == "not_run"
    ]


def _accept_command(
    name: str,
    candidate_id: str,
    candidate_set_path: Path,
    required_permissions: list[str],
) -> str:
    permission_flags = " ".join(f"--permission {item}" for item in required_permissions)
    return " ".join(
        part
        for part in (
            f"fig-agent compose-accept {name}",
            f"--candidate-set {candidate_set_path.as_posix()}",
            f"--candidate-id {candidate_id}",
            "--decision accept --reviewer <reviewer>",
            "--rationale <rationale>",
            permission_flags,
            "--json",
        )
        if part
    )


def build_composition_apply_readiness(
    name: str,
    candidate_id: str,
    *,
    candidate_set: dict[str, Any],
    candidate_set_path: Path | None = None,
    acceptance_path: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    facts = support.facts(name, candidate_id, candidate_set, workspace_root)
    path = candidate_set_path or support.DEFAULT_SET
    blocking = _blocking_reasons(facts, candidate_set)
    required = support.required_permissions(facts["candidate"])
    return {
        "schema": READINESS_SCHEMA,
        "fixture": name,
        "candidate_id": facts["id"],
        "candidate_set_path": path.as_posix(),
        "status": "blocked" if blocking else "ready_for_local_acceptance",
        "source_mutation_allowed": False,
        "blocking_reasons": blocking,
        "required_permissions": required,
        "required_commands": [_accept_command(name, facts["id"], path, required)],
        "diagnostics": _not_run_diagnostics(facts["manifest"]),
        "evidence_hashes": support.evidence_hashes(facts, candidate_set, candidate_set_path),
        "acceptance_path": (
            acceptance_path
            or Path(f"build/candidates/{facts['id']}/composition_acceptance.json")
        ).as_posix(),
    }


def _acceptance_payload(
    name: str,
    candidate_id: str,
    *,
    candidate_set: dict[str, Any],
    candidate_set_path: Path,
    reviewer: str,
    rationale: str,
    permissions_granted: list[str],
    workspace_root: Path | None,
) -> dict[str, Any]:
    facts = support.facts(name, candidate_id, candidate_set, workspace_root)
    hashes = support.evidence_hashes(facts, candidate_set, candidate_set_path)
    fixture = facts["fixture"]
    return {
        "schema": ACCEPTANCE_SCHEMA,
        "fixture": name,
        "candidate_id": facts["id"],
        "candidate_set_path": candidate_set_path.as_posix(),
        "candidate_set_sha256": hashes["candidate_set"],
        "render_manifest_path": support.fixture_relative(fixture, facts["manifest_path"]),
        "render_manifest_sha256": hashes["render_manifest"],
        "candidate_source_copy_path": support.fixture_relative(fixture, facts["source_copy"]),
        "candidate_source_copy_sha256": hashes["candidate_source_copy"],
        "base_source_path": support.fixture_relative(fixture, facts["source"]),
        "base_source_sha256": hashes["base_source"],
        "operations_sha256": hashes["operations"],
        "decision": "accept",
        "reviewer": reviewer,
        "reviewed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "rationale": rationale,
        "permissions_granted": permissions_granted,
        "human_review_required": True,
        "source_mutation_allowed": False,
        "hash_evidence": {
            "candidate_set": hashes["candidate_set"],
            "render_manifest": hashes["render_manifest"],
            "candidate_source_copy": hashes["candidate_source_copy"],
            "source": hashes["base_source"],
            "operations": hashes["operations"],
        },
    }


def write_composition_acceptance(
    name: str,
    candidate_id: str,
    *,
    candidate_set: dict[str, Any],
    candidate_set_path: Path,
    decision: str = "accept",
    reviewer: str,
    rationale: str,
    permissions_granted: list[str],
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    if decision != "accept":
        raise CompositionAcceptanceError("decision_unsupported")
    readiness = build_composition_apply_readiness(
        name,
        candidate_id,
        candidate_set=candidate_set,
        candidate_set_path=candidate_set_path,
        workspace_root=workspace_root,
    )
    if readiness["status"] != "ready_for_local_acceptance":
        raise CompositionAcceptanceError(",".join(readiness["blocking_reasons"]))
    missing = sorted(set(readiness["required_permissions"]) - set(permissions_granted))
    if missing:
        raise CompositionAcceptanceError(",".join(missing))

    workspace = support.root(workspace_root)
    fixture = workspace / "examples" / name
    safe_id = support.safe_id(candidate_id)
    path = support.safe_fixture_path(fixture, fixture / "build" / "candidates" / safe_id)
    path = support.safe_fixture_path(fixture, path / "composition_acceptance.json")
    acceptance = _acceptance_payload(
        name,
        safe_id,
        candidate_set=candidate_set,
        candidate_set_path=candidate_set_path,
        reviewer=reviewer,
        rationale=rationale,
        permissions_granted=permissions_granted,
        workspace_root=workspace,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(acceptance, indent=2, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")
    return {
        "schema": WRITE_RESULT_SCHEMA,
        "fixture": name,
        "candidate_id": safe_id,
        "path": support.fixture_relative(fixture, path),
        "acceptance": acceptance,
    }


def validate_composition_acceptance(
    acceptance: dict[str, Any],
    *,
    candidate_set: dict[str, Any],
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    name = str(acceptance.get("fixture") or "")
    candidate_id = support.safe_id(str(acceptance.get("candidate_id") or ""))
    readiness = build_composition_apply_readiness(
        name,
        candidate_id,
        candidate_set=candidate_set,
        candidate_set_path=Path(str(acceptance.get("candidate_set_path") or "")),
        workspace_root=workspace_root,
    )
    expected = readiness["evidence_hashes"]
    actual = {
        "candidate_set": acceptance.get("candidate_set_sha256"),
        "render_manifest": acceptance.get("render_manifest_sha256"),
        "candidate_source_copy": acceptance.get("candidate_source_copy_sha256"),
        "base_source": acceptance.get("base_source_sha256"),
        "operations": acceptance.get("operations_sha256"),
    }
    mismatches = [key for key, value in expected.items() if actual.get(key) != value]
    ready = readiness["status"] == "ready_for_local_acceptance"
    return {
        "status": "accepted" if not mismatches and ready else "blocked",
        "accepted_hashes": actual,
        "permissions_granted": acceptance.get("permissions_granted", []),
        "diagnostics": [
            {"code": "acceptance_hash_mismatch", "field": key} for key in mismatches
        ],
    }
