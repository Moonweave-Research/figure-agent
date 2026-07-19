"""Preserve and remove one retired pre-R4.8 candidate leaf from discovery."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import closed_loop_current_state
import repair_transaction

ACTION = "closed_loop_legacy_candidate_quarantine"
AUTHORIZATION_SCHEMA = (
    "figure-agent.legacy-candidate-quarantine-authorization.v1"
)
AUTHORIZATION_DECISION = "quarantine_and_restart_from_repair_bound"


class ClosedLoopLegacyCandidateQuarantineError(ValueError):
    """Raised when an explicit retired candidate leaf cannot be preserved safely."""


def canonical_authorization_sha256(payload: dict[str, Any]) -> str:
    canonical = dict(payload)
    canonical.pop("authorization_sha256", None)
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _file_sha256_bytes(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _json_snapshot(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        content = path.read_bytes()
        payload = json.loads(content)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopLegacyCandidateQuarantineError(
            "legacy_candidate_state_invalid"
        ) from exc
    if not isinstance(payload, dict):
        raise ClosedLoopLegacyCandidateQuarantineError(
            "legacy_candidate_state_invalid"
        )
    return payload, content


def _lexical_workspace_path(root: Path, value: Path) -> Path:
    path = Path(os.path.abspath(value if value.is_absolute() else root / value))
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ClosedLoopLegacyCandidateQuarantineError(
            "legacy_candidate_state_outside_workspace"
        ) from exc
    return path


def _reject_symlink_chain(root: Path, path: Path, *, label: str) -> None:
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise ClosedLoopLegacyCandidateQuarantineError(f"{label}_symlink")


def _validated_plan(
    fixture: str,
    *,
    state_path: Path,
    authorization_path: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    root = Path(os.path.abspath(workspace_root))
    source = _lexical_workspace_path(root, state_path)
    _reject_symlink_chain(root, source, label="legacy_candidate_state")
    if not source.is_file():
        raise ClosedLoopLegacyCandidateQuarantineError(
            "legacy_candidate_state_missing"
        )
    payload, content = _json_snapshot(source)
    try:
        state = closed_loop_attempt_state.validate_pre_r4_8_candidate_state(
            payload,
            workspace_root=root,
        )
        canonical_source = closed_loop_attempt_state.state_path(
            state,
            workspace_root=root,
        )
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise ClosedLoopLegacyCandidateQuarantineError(
            f"legacy_candidate_state_invalid:{exc}"
        ) from exc
    if state["fixture"] != fixture or source != canonical_source:
        raise ClosedLoopLegacyCandidateQuarantineError(
            "legacy_candidate_state_identity_mismatch"
        )
    state_files = sorted(source.parent.glob("state-*.json"))
    if not state_files or state_files[-1] != source:
        raise ClosedLoopLegacyCandidateQuarantineError(
            "legacy_candidate_state_not_leaf"
        )
    previous_path = root / str(state["previous_state_path"])
    try:
        previous_payload, _ = _json_snapshot(previous_path)
        previous = closed_loop_attempt_state.validate_state(
            previous_payload,
            workspace_root=root,
        )
    except (
        ClosedLoopLegacyCandidateQuarantineError,
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
    ) as exc:
        raise ClosedLoopLegacyCandidateQuarantineError(
            f"legacy_candidate_parent_invalid:{exc}"
        ) from exc
    if (
        previous["state"] != "repair_bound"
        or previous["attempt_id"] != state["attempt_id"]
        or previous["sequence"] != state["sequence"] - 1
    ):
        raise ClosedLoopLegacyCandidateQuarantineError(
            "legacy_candidate_parent_not_repair_bound"
        )
    fixture_root = root / "examples" / fixture
    authorization = _lexical_workspace_path(root, authorization_path)
    _reject_symlink_chain(
        root,
        authorization,
        label="legacy_candidate_authorization",
    )
    try:
        authorization_payload, authorization_bytes = _json_snapshot(authorization)
    except ClosedLoopLegacyCandidateQuarantineError as exc:
        raise ClosedLoopLegacyCandidateQuarantineError(
            f"legacy_candidate_authorization_invalid:{exc}"
        ) from exc
    try:
        authorization.relative_to(fixture_root)
    except ValueError as exc:
        raise ClosedLoopLegacyCandidateQuarantineError(
            "legacy_candidate_authorization_cross_fixture"
        ) from exc
    expected_authorization_fields = {
        "schema",
        "fixture",
        "legacy_state",
        "decision",
        "authorized_by",
        "rationale",
        "publication_acceptance",
        "authorization_sha256",
    }
    legacy_state_authority = authorization_payload.get("legacy_state")
    if (
        set(authorization_payload) != expected_authorization_fields
        or authorization_payload.get("schema") != AUTHORIZATION_SCHEMA
        or authorization_payload.get("fixture") != fixture
        or authorization_payload.get("decision") != AUTHORIZATION_DECISION
        or authorization_payload.get("publication_acceptance") != "not_claimed"
        or not isinstance(authorization_payload.get("authorized_by"), str)
        or not authorization_payload["authorized_by"].strip()
        or not isinstance(authorization_payload.get("rationale"), str)
        or not authorization_payload["rationale"].strip()
        or not isinstance(legacy_state_authority, dict)
        or set(legacy_state_authority)
        != {"path", "state_sha256", "file_sha256"}
        or legacy_state_authority.get("path")
        != source.relative_to(root).as_posix()
        or legacy_state_authority.get("state_sha256") != state["state_sha256"]
        or legacy_state_authority.get("file_sha256")
        != _file_sha256_bytes(content)
        or authorization_payload.get("authorization_sha256")
        != canonical_authorization_sha256(authorization_payload)
    ):
        raise ClosedLoopLegacyCandidateQuarantineError(
            "legacy_candidate_authorization_invalid"
        )
    quarantine_root = fixture_root / "review" / "closed-loop-legacy"
    quarantine_path = quarantine_root / state["attempt_id"] / source.name
    quarantine_authorization_path = (
        quarantine_path.parent / "quarantine_authorization.json"
    )
    for path in (fixture_root / "review", quarantine_root, quarantine_path.parent):
        if path.is_symlink():
            raise ClosedLoopLegacyCandidateQuarantineError(
                "legacy_candidate_quarantine_symlink"
            )
    quarantine_linked = quarantine_path.exists()
    if quarantine_path.is_symlink() or (
        quarantine_linked and quarantine_path.read_bytes() != content
    ):
        raise ClosedLoopLegacyCandidateQuarantineError(
            "legacy_candidate_quarantine_conflict"
        )
    if quarantine_authorization_path.is_symlink() or (
        quarantine_authorization_path.exists()
        and (
            not quarantine_authorization_path.is_file()
            or quarantine_authorization_path.read_bytes() != authorization_bytes
        )
    ):
        raise ClosedLoopLegacyCandidateQuarantineError(
            "legacy_candidate_authorization_quarantine_conflict"
        )
    return {
        "state": state,
        "state_path": source,
        "state_bytes": content,
        "parent_state": previous,
        "parent_state_path": previous_path,
        "quarantine_path": quarantine_path,
        "quarantine_linked": quarantine_linked,
        "authorization_path": authorization,
        "authorization_bytes": authorization_bytes,
        "quarantine_authorization_path": quarantine_authorization_path,
    }


def _result(plan: dict[str, Any], *, created: bool) -> dict[str, Any]:
    return {
        "action": ACTION,
        "created": created,
        "state_path": plan["state_path"],
        "quarantine_path": plan["quarantine_path"],
        "quarantine_authorization_path": plan[
            "quarantine_authorization_path"
        ],
        "restart_state_path": plan["parent_state_path"],
        "restart_state_sha256": plan["parent_state"]["state_sha256"],
        "publication_acceptance": "not_claimed",
    }


def quarantine_legacy_candidate(
    fixture: str,
    *,
    state_path: Path,
    authorization_path: Path,
    execute: bool,
    workspace_root: Path,
) -> dict[str, Any]:
    """Plan or preserve one retired leaf so its repair-bound parent can restart."""
    root = Path(os.path.abspath(workspace_root))
    plan = _validated_plan(
        fixture,
        state_path=state_path,
        authorization_path=authorization_path,
        workspace_root=root,
    )
    if not execute:
        return _result(plan, created=False)

    with closed_loop_attempt_state.attempt_transition_lock(
        plan["state_path"].parent
    ):
        current = _validated_plan(
            fixture,
            state_path=state_path,
            authorization_path=authorization_path,
            workspace_root=root,
        )
        if (
            current["state_bytes"] != plan["state_bytes"]
            or current["authorization_bytes"] != plan["authorization_bytes"]
        ):
            raise ClosedLoopLegacyCandidateQuarantineError(
                "legacy_candidate_inputs_drifted"
            )
        destination = current["quarantine_path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.parent.is_dir() or destination.parent.is_symlink():
            raise ClosedLoopLegacyCandidateQuarantineError(
                "legacy_candidate_quarantine_directory_invalid"
            )
        authorization_destination = current["quarantine_authorization_path"]
        if not authorization_destination.exists():
            repair_transaction.atomic_create_text(
                authorization_destination,
                current["authorization_bytes"].decode("utf-8"),
            )
        try:
            if not current["quarantine_linked"]:
                os.link(current["state_path"], destination)
            current["state_path"].unlink()
        except OSError:
            if (
                not current["quarantine_linked"]
                and destination.exists()
                and destination.read_bytes() == current["state_bytes"]
            ):
                destination.unlink()
            raise

    projection = closed_loop_current_state.resolve_current_attempt(root, fixture)
    parent = current["parent_state"]
    if (
        projection.get("resolution") != "current"
        or projection.get("state") != "repair_bound"
        or projection.get("path")
        != current["parent_state_path"].relative_to(root).as_posix()
        or projection.get("state_sha256") != parent["state_sha256"]
    ):
        raise ClosedLoopLegacyCandidateQuarantineError(
            "legacy_candidate_parent_restart_not_current"
        )
    return _result(current, created=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="closed_loop_legacy_candidate_quarantine.py")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    result = quarantine_legacy_candidate(
        args.fixture,
        state_path=args.state,
        authorization_path=args.authorization,
        execute=args.execute,
        workspace_root=args.workspace_root,
    )
    print(
        json.dumps(
            {
                **result,
                "state_path": str(result["state_path"]),
                "quarantine_path": str(result["quarantine_path"]),
                "quarantine_authorization_path": str(
                    result["quarantine_authorization_path"]
                ),
                "restart_state_path": str(result["restart_state_path"]),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
