from __future__ import annotations

import difflib
import json
from pathlib import Path
from typing import Any, Final

import composition_acceptance
import composition_acceptance_support as support

SCHEMA: Final = "figure-agent.composition-apply-result.v1"


class CompositionApplyError(ValueError):
    pass


def _diagnostic(code: str, message: str, field: str | None = None) -> dict[str, str]:
    payload = {"code": code, "message": message}
    if field is not None:
        payload["field"] = field
    return payload


def _blocked(name: str, candidate_id: str, diagnostics: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": name,
        "candidate_id": candidate_id,
        "status": "blocked",
        "source_mutation_allowed": False,
        "changed_files": [],
        "rollback_patch": None,
        "diagnostics": diagnostics,
    }


def _rollback_patch(relative: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            after.splitlines(keepends=True),
            before.splitlines(keepends=True),
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
        )
    )


def _validate_acceptance(
    acceptance: dict[str, Any],
    *,
    name: str,
    candidate_id: str,
    candidate_set: dict[str, Any],
    workspace_root: Path | None,
) -> list[dict[str, str]]:
    if acceptance.get("schema") != composition_acceptance.ACCEPTANCE_SCHEMA:
        return [_diagnostic("acceptance_schema_invalid", "acceptance schema is invalid")]
    if acceptance.get("fixture") != name or acceptance.get("candidate_id") != candidate_id:
        return [_diagnostic("acceptance_identity_mismatch", "acceptance identity mismatch")]
    if acceptance.get("decision") != "accept":
        return [_diagnostic("acceptance_decision_not_accept", "acceptance is not an accept")]
    permissions = acceptance.get("permissions_granted")
    if not isinstance(permissions, list) or "apply_to_fixture_source" not in permissions:
        raise CompositionApplyError("apply_to_fixture_source")
    result = composition_acceptance.validate_composition_acceptance(
        acceptance,
        candidate_set=candidate_set,
        workspace_root=workspace_root,
    )
    if result["status"] == "accepted":
        return []
    diagnostics = result.get("diagnostics")
    if isinstance(diagnostics, list) and diagnostics:
        return [_diagnostic("acceptance_not_current", "accepted hashes are stale")]
    return [_diagnostic("acceptance_not_current", "acceptance is no longer current")]


def apply_composition_acceptance(
    name: str,
    candidate_id: str,
    *,
    candidate_set: dict[str, Any],
    candidate_set_path: Path,
    acceptance: dict[str, Any],
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    current_id = support.safe_id(candidate_id)
    diagnostics = _validate_acceptance(
        acceptance,
        name=name,
        candidate_id=current_id,
        candidate_set=candidate_set,
        workspace_root=workspace_root,
    )
    if diagnostics:
        return _blocked(name, current_id, diagnostics)

    facts = support.facts(name, current_id, candidate_set, workspace_root)
    source = facts["source"]
    source_copy = facts["source_copy"]
    fixture = facts["fixture"]
    sandbox = support.safe_fixture_path(fixture, fixture / "build" / "candidates" / current_id)
    rollback_path = support.safe_fixture_path(fixture, sandbox / "rollback.patch")
    result_path = support.safe_fixture_path(fixture, sandbox / "composition_apply_result.json")
    if rollback_path.is_symlink() or result_path.is_symlink():
        raise CompositionApplyError("sandbox_symlink_forbidden")

    before = source.read_text(encoding="utf-8")
    after = source_copy.read_text(encoding="utf-8")
    relative = support.fixture_relative(fixture, source)
    rollback_path.write_text(_rollback_patch(relative, before, after), encoding="utf-8")
    before_hash = support.hash_file(source)
    source.write_text(after, encoding="utf-8")
    result = {
        "schema": SCHEMA,
        "fixture": name,
        "candidate_id": current_id,
        "status": "applied_unverified",
        "source_mutation_allowed": True,
        "changed_files": [
            {
                "path": relative,
                "before_sha256": before_hash,
                "after_sha256": support.hash_file(source),
            }
        ],
        "rollback_patch": support.fixture_relative(fixture, rollback_path),
        "post_apply": {"status": "not_run"},
        "required_commands": [
            f"fig-agent compile {name} --strict",
            f"fig-agent export {name}",
        ],
        "diagnostics": [],
    }
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
