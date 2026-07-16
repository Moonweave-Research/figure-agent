"""Admit one explicit fresh authored render as a canonical root attempt."""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import closed_loop_current_state
import repair_transaction

SCHEMA = "figure-agent.root-attempt-manifest.v1"
ACTION = "admit_authored_rendered"
STOP_REASON = "authored_rendered_admitted"


class ClosedLoopAttemptAdmissionError(ValueError):
    """Raised when an explicit root-attempt admission is not safe."""


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _fixture_artifact(workspace_root: Path, fixture: str, value: str, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ClosedLoopAttemptAdmissionError(f"{label}_path_invalid")
    try:
        return closed_loop_attempt_state._workspace_artifact(  # noqa: SLF001
            workspace_root, fixture, value, label=label
        )
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise ClosedLoopAttemptAdmissionError(str(exc)) from exc


def _read_manifest(
    path: Path, *, workspace_root: Path, fixture: str
) -> tuple[dict[str, Any], Path]:
    manifest_path = _fixture_artifact(workspace_root, fixture, str(path), "attempt_manifest")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopAttemptAdmissionError("attempt_manifest_json_invalid") from exc
    if not isinstance(payload, dict):
        raise ClosedLoopAttemptAdmissionError("attempt_manifest_invalid")
    return payload, manifest_path


def _provenance(payload: Mapping[str, Any], field: str) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, dict) or not value:
        raise ClosedLoopAttemptAdmissionError(f"attempt_manifest_{field}_missing")
    return dict(value)


def _bound_artifact(
    payload: Mapping[str, Any],
    field: str,
    *,
    workspace_root: Path,
    fixture: str,
) -> Path:
    record = payload.get(field)
    if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
        raise ClosedLoopAttemptAdmissionError(f"attempt_manifest_{field}_invalid")
    path = _fixture_artifact(workspace_root, fixture, record["path"], field)
    if record["sha256"] != _sha256(path):
        raise ClosedLoopAttemptAdmissionError(f"attempt_manifest_{field}_hash_stale")
    return path


def _validated_state(
    fixture: str, manifest_path: Path, *, workspace_root: Path
) -> dict[str, Any]:
    payload, actual_manifest_path = _read_manifest(
        manifest_path, workspace_root=workspace_root, fixture=fixture
    )
    if set(payload) != {
        "schema",
        "fixture",
        "author",
        "source",
        "render",
        "task",
        "model",
        "budget",
        "publication_acceptance",
        "manifest_sha256",
    }:
        raise ClosedLoopAttemptAdmissionError("attempt_manifest_fields_invalid")
    if payload.get("schema") != SCHEMA or payload.get("fixture") != fixture:
        raise ClosedLoopAttemptAdmissionError("attempt_manifest_fixture_mismatch")
    if payload.get("publication_acceptance") != "not_claimed":
        raise ClosedLoopAttemptAdmissionError("publication_acceptance_claimed")
    expected_hash = payload.get("manifest_sha256")
    unsigned = dict(payload)
    unsigned.pop("manifest_sha256", None)
    if expected_hash != _canonical_sha256(unsigned):
        raise ClosedLoopAttemptAdmissionError("attempt_manifest_hash_invalid")
    author = payload.get("author")
    if (
        not isinstance(author, dict)
        or set(author) != {"identity", "role"}
        or not isinstance(author["identity"], str)
        or not author["identity"].strip()
        or author["role"] != "authoring_agent"
    ):
        raise ClosedLoopAttemptAdmissionError("attempt_manifest_author_invalid")
    _provenance(payload, "task")
    _provenance(payload, "model")
    _provenance(payload, "budget")
    source = _bound_artifact(payload, "source", workspace_root=workspace_root, fixture=fixture)
    render = _bound_artifact(payload, "render", workspace_root=workspace_root, fixture=fixture)
    try:
        return closed_loop_attempt_state.start_attempt(
            workspace_root=workspace_root,
            fixture=fixture,
            actor=author["identity"],
            actor_role=author["role"],
            evidence={
                "attempt_manifest": actual_manifest_path,
                "authored_source": source,
                "render": render,
            },
        )
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise ClosedLoopAttemptAdmissionError(str(exc)) from exc


def admit_root_attempt(
    fixture: str,
    *,
    manifest_path: Path,
    execute: bool,
    workspace_root: Path,
) -> dict[str, Any]:
    """Validate explicit evidence; publish only the root state when requested."""
    root = Path(os.path.abspath(workspace_root))
    state = _validated_state(fixture, manifest_path, workspace_root=root)
    initial_current = closed_loop_current_state.resolve_current_attempt(root, fixture)
    if initial_current.get("resolution") != "absent":
        if initial_current.get("resolution") == "current":
            try:
                proposed_path = closed_loop_attempt_state.state_path(
                    state, workspace_root=root
                )
            except closed_loop_attempt_state.ClosedLoopAttemptStateError:
                proposed_path = None
            if (
                proposed_path is not None
                and initial_current.get("path") == proposed_path.relative_to(root).as_posix()
                and initial_current.get("state_sha256") == state["state_sha256"]
            ):
                return {
                    "state": state,
                    "next_state_path": proposed_path,
                    "created": False,
                }
        raise ClosedLoopAttemptAdmissionError(
            "existing_current_attempt:"
            f"{initial_current.get('resolution')}:{initial_current.get('reason')}"
        )
    proposed_path = closed_loop_attempt_state.state_path(state, workspace_root=root)
    if not execute:
        return {"state": state, "next_state_path": proposed_path, "created": False}

    # Root admission has no attempt directory yet; lock the shared closed-loop
    # publication root so the lock itself cannot masquerade as an attempt.
    for _ in range(25):
        try:
            with closed_loop_attempt_state.attempt_transition_lock(proposed_path.parent.parent):
                # Re-read all explicit inputs after taking the publication lock so a
                # source/render/manifest replacement between plan and execute fails closed.
                state = _validated_state(fixture, manifest_path, workspace_root=root)
                proposed_path = closed_loop_attempt_state.state_path(
                    state, workspace_root=root
                )
                current = closed_loop_current_state.resolve_current_attempt(root, fixture)
                if current.get("resolution") != "absent":
                    if (
                        current.get("resolution") == "current"
                        and current.get("path")
                        == proposed_path.relative_to(root).as_posix()
                        and current.get("state_sha256") == state["state_sha256"]
                    ):
                        return {
                            "state": state,
                            "next_state_path": proposed_path,
                            "created": False,
                        }
                    raise ClosedLoopAttemptAdmissionError(
                        "existing_current_attempt:"
                        f"{current.get('resolution')}:{current.get('reason')}"
                    )
                try:
                    published = closed_loop_attempt_state.publish_state(
                        state, workspace_root=root
                    )
                except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
                    if str(exc) != "state_already_published":
                        raise ClosedLoopAttemptAdmissionError(str(exc)) from exc
                    current = closed_loop_current_state.resolve_current_attempt(root, fixture)
                    if (
                        current.get("resolution") == "current"
                        and current.get("path")
                        == proposed_path.relative_to(root).as_posix()
                        and current.get("state_sha256") == state["state_sha256"]
                    ):
                        return {
                            "state": state,
                            "next_state_path": proposed_path,
                            "created": False,
                        }
                    raise ClosedLoopAttemptAdmissionError("conflicting_state_publication") from exc
                return {"state": state, "next_state_path": published, "created": True}
        except repair_transaction.RepairTransactionError as exc:
            if str(exc) != "transaction lock exists":
                raise ClosedLoopAttemptAdmissionError(str(exc)) from exc
            time.sleep(0.01)
    current = closed_loop_current_state.resolve_current_attempt(root, fixture)
    if (
        current.get("resolution") == "current"
        and current.get("path") == proposed_path.relative_to(root).as_posix()
        and current.get("state_sha256") == state["state_sha256"]
    ):
        return {"state": state, "next_state_path": proposed_path, "created": False}
    raise ClosedLoopAttemptAdmissionError("attempt_transition_lock_busy")
