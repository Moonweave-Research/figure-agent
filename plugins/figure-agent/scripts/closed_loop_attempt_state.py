"""Fail-closed lineage state for one Figure Agent repair attempt.

This module deliberately owns only attempt identity, state transitions, artifact
freshness, and append-only publication.  Domain-specific artifact validation
remains with the artifact producers and validators that already own it.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator, Mapping, Sequence
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any

import repair_transaction

SCHEMA = "figure-agent.closed-loop-attempt-state.v1"
PUBLICATION_ACCEPTANCE = "not_claimed"
ATTEMPT_TRANSITION_LOCK = ".closed-loop-attempt-transition.lock"
ATTEMPT_TRANSITION_LOCK_OWNER = "figure_agent_closed_loop_attempt_transition"
_LEGACY_TRANSITION_LOCKS = (
    (".closed-loop-repair-authorization.lock", "closed_loop_repair_authorization"),
    (".closed-loop-machine-repair.lock", "closed_loop_machine_repair"),
    (".closed-loop-post-review.lock", "closed_loop_post_review"),
    (".closed-loop-post-review-response.lock", "closed_loop_post_review_response"),
)


@contextmanager
def attempt_transition_lock(attempt_root: Path) -> Iterator[None]:
    """Serialize current publishers and one-release legacy lock holders."""
    with ExitStack() as stack:
        stack.enter_context(
            repair_transaction.recoverable_exclusive_lock(
                attempt_root / ATTEMPT_TRANSITION_LOCK,
                owner=ATTEMPT_TRANSITION_LOCK_OWNER,
            )
        )
        for name, owner in _LEGACY_TRANSITION_LOCKS:
            stack.enter_context(
                repair_transaction.recoverable_exclusive_lock(
                    attempt_root / name,
                    owner=owner,
                )
            )
        yield

_STATE_POLICY: dict[str, tuple[str, str, bool]] = {
    "authored_rendered": ("continue", "workflow_agent", False),
    "critique_unadjudicated": (
        "human_review_required",
        "human_adjudicator",
        False,
    ),
    "adjudicated_unbound": (
        "human_review_required",
        "human_attributor",
        False,
    ),
    "repair_bound": ("continue", "workflow_agent", False),
    "repair_candidate_ready": (
        "human_review_required",
        "human_repair_authorizer",
        False,
    ),
    "repair_authorized": ("continue", "workflow_agent", False),
    "machine_repaired": ("continue", "workflow_agent", False),
    "post_review_requested": ("human_review_required", "host_llm", False),
    "visually_re_reviewed": (
        "human_review_required",
        "human_reviewer",
        False,
    ),
    "repair_required": ("repair_required", "none", True),
    "development_accepted": ("accepted", "none", True),
    "rejected": ("rejected", "none", True),
    "aborted": ("aborted", "none", True),
}

_LEGAL_TRANSITIONS: dict[str, frozenset[str]] = {
    "authored_rendered": frozenset({"critique_unadjudicated", "aborted"}),
    "critique_unadjudicated": frozenset(
        {"adjudicated_unbound", "repair_bound", "rejected", "aborted"}
    ),
    "adjudicated_unbound": frozenset({"repair_bound", "rejected", "aborted"}),
    "repair_bound": frozenset({"repair_candidate_ready", "aborted"}),
    "repair_candidate_ready": frozenset(
        {"repair_authorized", "rejected", "aborted"}
    ),
    "repair_authorized": frozenset(
        {"machine_repaired", "repair_required", "aborted"}
    ),
    "machine_repaired": frozenset({"post_review_requested", "repair_required", "aborted"}),
    "post_review_requested": frozenset(
        {
            "visually_re_reviewed",
            "repair_required",
            "aborted",
        }
    ),
    "visually_re_reviewed": frozenset(
        {
            "development_accepted",
            "rejected",
            "repair_required",
            "aborted",
        }
    ),
    "repair_required": frozenset(),
    "development_accepted": frozenset(),
    "rejected": frozenset(),
    "aborted": frozenset(),
}

_STATE_EVIDENCE_ROLES: dict[str, frozenset[str]] = {
    "authored_rendered": frozenset({"attempt_manifest", "authored_source", "render"}),
    "critique_unadjudicated": frozenset(
        {"critique", "host_review_execution_receipt"}
    ),
    "adjudicated_unbound": frozenset({"adjudication", "attribution_handoff"}),
    "repair_bound": frozenset({"adjudicated_repair_binding"}),
    "repair_candidate_ready": frozenset(
        {"repair_execution_packet", "repair_response", "materialization_preview"}
    ),
    "repair_authorized": frozenset({"human_authorization"}),
    "machine_repaired": frozenset(
        {"materialization_receipt", "machine_verification_receipt"}
    ),
    "post_review_requested": frozenset({"post_repair_visual_review_request"}),
    "visually_re_reviewed": frozenset(
        {
            "post_repair_visual_review_response",
            "host_review_execution_receipt",
            "post_repair_visual_review_receipt",
        }
    ),
    "development_accepted": frozenset({"human_decision_record"}),
    "rejected": frozenset({"human_decision_record"}),
    "repair_required": frozenset({"repair_failure_record"}),
    "aborted": frozenset({"abort_record"}),
}
_PRE_R4_8_CANDIDATE_EVIDENCE_ROLES = frozenset(
    {"repair_execution_packet", "materialization_preview"}
)


class ClosedLoopAttemptStateError(ValueError):
    """Raised when attempt state, evidence, or lineage is unsafe."""

    def __init__(self, message: str, *, path: Path | None = None) -> None:
        super().__init__(message)
        self.path = path


def _validate_attempt_id(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value.startswith("attempt-")
        or len(value) != 32
        or any(character not in "0123456789abcdef" for character in value[8:])
    ):
        raise ClosedLoopAttemptStateError("attempt_id_invalid")
    return value


def _canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def canonical_state_sha256(state: Mapping[str, Any]) -> str:
    payload = dict(state)
    payload.pop("state_sha256", None)
    return _canonical_hash(payload)


def _attempt_id(
    *,
    fixture: str,
    root_evidence: list[dict[str, str]],
    parent_record: dict[str, str] | None,
) -> str:
    ordered_evidence = sorted(root_evidence, key=lambda record: record["role"])
    identity = _canonical_hash(
        {
            "schema": SCHEMA,
            "fixture": fixture,
            "root_evidence": ordered_evidence,
            "parent_state": parent_record,
        }
    )
    return "attempt-" + identity.removeprefix("sha256:")[:24]


def _file_sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture_root(workspace_root: Path, fixture: str) -> Path:
    if (
        not isinstance(fixture, str)
        or not fixture
        or fixture in {".", ".."}
        or "/" in fixture
        or "\\" in fixture
    ):
        raise ClosedLoopAttemptStateError("fixture_invalid")
    root = Path(os.path.abspath(workspace_root))
    examples = root / "examples"
    fixture_root = examples / fixture
    if examples.is_symlink() or fixture_root.is_symlink():
        raise ClosedLoopAttemptStateError("fixture_symlink")
    if not fixture_root.is_dir():
        raise ClosedLoopAttemptStateError("fixture_missing")
    return fixture_root


def _workspace_artifact(
    workspace_root: Path,
    fixture: str,
    value: Path | str,
    *,
    label: str,
    require_file: bool = True,
) -> Path:
    root = Path(os.path.abspath(workspace_root))
    fixture_root = _fixture_root(root, fixture)
    candidate = Path(value)
    if candidate.is_absolute():
        candidate = Path(os.path.abspath(candidate))
    else:
        if not candidate.parts or any(part in {"", ".", ".."} for part in candidate.parts):
            raise ClosedLoopAttemptStateError(f"{label}_path_unsafe")
        candidate = root / candidate
    try:
        relative = candidate.relative_to(fixture_root)
    except ValueError as exc:
        raise ClosedLoopAttemptStateError(f"{label}_cross_fixture") from exc
    current = fixture_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ClosedLoopAttemptStateError(f"{label}_symlink")
    if require_file and not current.is_file():
        raise ClosedLoopAttemptStateError(f"{label}_missing")
    return current


def _evidence_records(
    evidence: Mapping[str, Path | str],
    *,
    workspace_root: Path,
    fixture: str,
) -> list[dict[str, str]]:
    if not isinstance(evidence, Mapping) or not evidence:
        raise ClosedLoopAttemptStateError("evidence_missing")
    records: list[dict[str, str]] = []
    root = Path(os.path.abspath(workspace_root))
    for role in sorted(evidence):
        if not isinstance(role, str) or not role.strip():
            raise ClosedLoopAttemptStateError("evidence_role_invalid")
        path = _workspace_artifact(
            root,
            fixture,
            evidence[role],
            label=f"evidence_{role}",
        )
        records.append(
            {
                "role": role,
                "path": path.relative_to(root).as_posix(),
                "sha256": _file_sha256(path),
            }
        )
    return records


def state_path(state: Mapping[str, Any], *, workspace_root: Path) -> Path:
    """Return the only legal publication path for a state record."""
    fixture = state.get("fixture")
    attempt_id = state.get("attempt_id")
    sequence = state.get("sequence")
    state_name = state.get("state")
    if not isinstance(fixture, str):
        raise ClosedLoopAttemptStateError("fixture_invalid")
    fixture_root = _fixture_root(workspace_root, fixture)
    if (
        isinstance(sequence, bool)
        or not isinstance(sequence, int)
        or sequence < 0
        or not isinstance(state_name, str)
        or state_name not in _STATE_POLICY
    ):
        raise ClosedLoopAttemptStateError("state_path_identity_invalid")
    _validate_attempt_id(attempt_id)
    output = (
        fixture_root
        / "review"
        / "closed-loop"
        / attempt_id
        / f"state-{sequence:03d}-{state_name}.json"
    )
    current = fixture_root
    for part in output.relative_to(fixture_root).parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ClosedLoopAttemptStateError("state_output_symlink")
    return output


def _published_state_record(
    state: Mapping[str, Any],
    state_file: Path | str,
    *,
    workspace_root: Path,
    label: str,
) -> dict[str, str]:
    payload = validate_state(state, workspace_root=workspace_root)
    expected_path = state_path(payload, workspace_root=workspace_root)
    actual_path = _workspace_artifact(
        workspace_root,
        payload["fixture"],
        state_file,
        label=label,
    )
    if actual_path != expected_path:
        raise ClosedLoopAttemptStateError(f"{label}_path_mismatch")
    try:
        published = json.loads(actual_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopAttemptStateError(f"{label}_json_invalid") from exc
    if published != payload:
        raise ClosedLoopAttemptStateError(f"{label}_payload_drift")
    root = Path(os.path.abspath(workspace_root))
    return {
        "path": actual_path.relative_to(root).as_posix(),
        "state_sha256": payload["state_sha256"],
        "file_sha256": _file_sha256(actual_path),
    }


def start_attempt(
    *,
    workspace_root: Path,
    fixture: str,
    actor: str,
    evidence: Mapping[str, Path | str],
    actor_role: str,
    parent_state: Mapping[str, Any] | None = None,
    parent_state_path: Path | str | None = None,
) -> dict[str, Any]:
    if not isinstance(actor, str) or not actor.strip():
        raise ClosedLoopAttemptStateError("actor_invalid")
    if not isinstance(actor_role, str) or not actor_role.strip():
        raise ClosedLoopAttemptStateError("actor_role_invalid")
    records = _evidence_records(
        evidence,
        workspace_root=workspace_root,
        fixture=fixture,
    )
    parent_record = None
    if parent_state is not None:
        if parent_state_path is None:
            raise ClosedLoopAttemptStateError("parent_state_path_missing")
        parent = validate_state(parent_state, workspace_root=workspace_root)
        if parent["fixture"] != fixture:
            raise ClosedLoopAttemptStateError("parent_fixture_mismatch")
        if parent["state"] != "repair_required":
            raise ClosedLoopAttemptStateError("parent_state_not_repair_required")
        parent_record = _published_state_record(
            parent,
            parent_state_path,
            workspace_root=workspace_root,
            label="parent_state",
        )
    elif parent_state_path is not None:
        raise ClosedLoopAttemptStateError("parent_state_missing")
    state: dict[str, Any] = {
        "schema": SCHEMA,
        "attempt_id": _attempt_id(
            fixture=fixture,
            root_evidence=records,
            parent_record=parent_record,
        ),
        "fixture": fixture,
        "sequence": 0,
        "state": "authored_rendered",
        "previous_state_sha256": None,
        "previous_state_path": None,
        "previous_state_file_sha256": None,
        "parent_state_sha256": (
            parent_record["state_sha256"] if parent_record is not None else None
        ),
        "parent_state_path": parent_record["path"] if parent_record is not None else None,
        "parent_state_file_sha256": (
            parent_record["file_sha256"] if parent_record is not None else None
        ),
        "actor": actor,
        "actor_role": actor_role,
        "evidence": records,
        "disposition": "continue",
        "required_actor": "workflow_agent",
        "terminal": False,
        "publication_acceptance": PUBLICATION_ACCEPTANCE,
    }
    state["state_sha256"] = canonical_state_sha256(state)
    return validate_state(state, workspace_root=workspace_root)


def validate_state(
    state: Mapping[str, Any],
    *,
    workspace_root: Path,
    _lineage_stack: frozenset[Path] = frozenset(),
    _require_live_evidence: bool = True,
    _expected_evidence_roles: frozenset[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(state, Mapping):
        raise ClosedLoopAttemptStateError("state_invalid")
    payload = dict(state)
    if payload.get("schema") != SCHEMA:
        raise ClosedLoopAttemptStateError("schema_invalid")
    if payload.get("publication_acceptance") != PUBLICATION_ACCEPTANCE:
        raise ClosedLoopAttemptStateError("publication_acceptance_claimed")
    if payload.get("state_sha256") != canonical_state_sha256(payload):
        raise ClosedLoopAttemptStateError("state_hash_invalid")
    expected_fields = {
        "schema",
        "attempt_id",
        "fixture",
        "sequence",
        "state",
        "previous_state_sha256",
        "previous_state_path",
        "previous_state_file_sha256",
        "parent_state_sha256",
        "parent_state_path",
        "parent_state_file_sha256",
        "actor",
        "actor_role",
        "evidence",
        "disposition",
        "required_actor",
        "terminal",
        "publication_acceptance",
        "state_sha256",
    }
    if set(payload) != expected_fields:
        raise ClosedLoopAttemptStateError("state_fields_invalid")
    _validate_attempt_id(payload.get("attempt_id"))
    sequence = payload.get("sequence")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise ClosedLoopAttemptStateError("sequence_invalid")
    state_name = payload.get("state")
    if not isinstance(state_name, str) or state_name not in _STATE_POLICY:
        raise ClosedLoopAttemptStateError("state_name_invalid")
    disposition, required_actor, terminal = _STATE_POLICY[state_name]
    if (
        payload.get("disposition") != disposition
        or payload.get("required_actor") != required_actor
        or payload.get("terminal") is not terminal
    ):
        raise ClosedLoopAttemptStateError("derived_state_fields_invalid")
    actor = payload.get("actor")
    if not isinstance(actor, str) or not actor.strip():
        raise ClosedLoopAttemptStateError("actor_invalid")
    actor_role = payload.get("actor_role")
    if not isinstance(actor_role, str) or not actor_role.strip():
        raise ClosedLoopAttemptStateError("actor_role_invalid")
    for field in (
        "previous_state_sha256",
        "previous_state_file_sha256",
        "parent_state_sha256",
        "parent_state_file_sha256",
    ):
        value = payload.get(field)
        if value is not None and (
            not isinstance(value, str)
            or not value.startswith("sha256:")
            or len(value) != 71
        ):
            raise ClosedLoopAttemptStateError(f"{field}_invalid")
    if sequence == 0:
        if state_name != "authored_rendered" or any(
            payload[field] is not None
            for field in (
                "previous_state_sha256",
                "previous_state_path",
                "previous_state_file_sha256",
            )
        ):
            raise ClosedLoopAttemptStateError("initial_state_invalid")
        if payload["actor_role"] != "authoring_agent":
            raise ClosedLoopAttemptStateError("initial_actor_role_invalid")
    elif payload["previous_state_sha256"] is None:
        raise ClosedLoopAttemptStateError("previous_state_missing")
    fixture = payload.get("fixture")
    if not isinstance(fixture, str):
        raise ClosedLoopAttemptStateError("fixture_invalid")
    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise ClosedLoopAttemptStateError("evidence_missing")
    seen_roles: set[str] = set()
    root = Path(os.path.abspath(workspace_root))
    for record in evidence:
        if not isinstance(record, dict) or set(record) != {"role", "path", "sha256"}:
            raise ClosedLoopAttemptStateError("evidence_record_invalid")
        role = record.get("role")
        if not isinstance(role, str) or not role or role in seen_roles:
            raise ClosedLoopAttemptStateError("evidence_role_invalid")
        seen_roles.add(role)
        path = _workspace_artifact(
            root,
            fixture,
            str(record.get("path") or ""),
            label=f"evidence_{role}",
            require_file=_require_live_evidence,
        )
        if _require_live_evidence and record.get("sha256") != _file_sha256(path):
            raise ClosedLoopAttemptStateError("evidence_hash_stale")
    if [record["role"] for record in evidence] != sorted(seen_roles):
        raise ClosedLoopAttemptStateError("evidence_order_invalid")
    expected_evidence_roles = (
        _STATE_EVIDENCE_ROLES[state_name]
        if _expected_evidence_roles is None
        else _expected_evidence_roles
    )
    if (
        _expected_evidence_roles is not None
        and state_name != "repair_candidate_ready"
    ):
        raise ClosedLoopAttemptStateError("legacy_candidate_state_invalid")
    if seen_roles != expected_evidence_roles:
        raise ClosedLoopAttemptStateError("evidence_roles_invalid")
    if sequence == 0:
        parent_record = None
        if payload["parent_state_sha256"] is not None:
            parent_record = {
                "path": payload["parent_state_path"],
                "state_sha256": payload["parent_state_sha256"],
                "file_sha256": payload["parent_state_file_sha256"],
            }
        if payload["attempt_id"] != _attempt_id(
            fixture=payload["fixture"],
            root_evidence=evidence,
            parent_record=parent_record,
        ):
            raise ClosedLoopAttemptStateError("attempt_id_root_evidence_mismatch")
    _validate_lineage_record(
        payload,
        prefix="previous_state",
        workspace_root=root,
        lineage_stack=_lineage_stack,
        require_live_evidence=_require_live_evidence,
    )
    _validate_lineage_record(
        payload,
        prefix="parent_state",
        workspace_root=root,
        lineage_stack=_lineage_stack,
        require_live_evidence=_require_live_evidence,
    )
    return payload


def validate_pre_r4_8_candidate_state(
    state: Mapping[str, Any],
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    """Validate only the retired candidate leaf shape for explicit quarantine."""
    payload = validate_state(
        state,
        workspace_root=workspace_root,
        _expected_evidence_roles=_PRE_R4_8_CANDIDATE_EVIDENCE_ROLES,
    )
    if payload["state"] != "repair_candidate_ready":
        raise ClosedLoopAttemptStateError("legacy_candidate_state_invalid")
    return payload


def _validate_lineage_record(
    payload: dict[str, Any],
    *,
    prefix: str,
    workspace_root: Path,
    lineage_stack: frozenset[Path],
    require_live_evidence: bool,
) -> None:
    path_value = payload.get(f"{prefix}_path")
    state_hash = payload.get(f"{prefix}_sha256")
    file_hash = payload.get(f"{prefix}_file_sha256")
    values = (path_value, state_hash, file_hash)
    if all(value is None for value in values):
        return
    if any(value is None for value in values) or not isinstance(path_value, str):
        raise ClosedLoopAttemptStateError(f"{prefix}_record_incomplete")
    path = _workspace_artifact(
        workspace_root,
        payload["fixture"],
        path_value,
        label=prefix,
    )
    if path in lineage_stack:
        raise ClosedLoopAttemptStateError("lineage_cycle")
    if file_hash != _file_sha256(path):
        raise ClosedLoopAttemptStateError(f"{prefix}_file_hash_stale")
    try:
        linked = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopAttemptStateError(f"{prefix}_json_invalid") from exc
    if not isinstance(linked, dict):
        raise ClosedLoopAttemptStateError(f"{prefix}_payload_invalid")
    if linked.get("state_sha256") != state_hash or state_hash != canonical_state_sha256(
        linked
    ):
        raise ClosedLoopAttemptStateError(f"{prefix}_state_hash_stale")
    if linked.get("fixture") != payload["fixture"]:
        raise ClosedLoopAttemptStateError(f"{prefix}_fixture_mismatch")
    if path != state_path(linked, workspace_root=workspace_root):
        raise ClosedLoopAttemptStateError(f"{prefix}_path_mismatch")
    if prefix == "previous_state":
        if (
            linked.get("attempt_id") != payload["attempt_id"]
            or linked.get("sequence") != payload["sequence"] - 1
        ):
            raise ClosedLoopAttemptStateError("previous_state_identity_mismatch")
    elif (
        linked.get("attempt_id") == payload["attempt_id"]
        or linked.get("state") != "repair_required"
    ):
        raise ClosedLoopAttemptStateError("parent_state_identity_mismatch")
    linked = validate_state(
        linked,
        workspace_root=workspace_root,
        _lineage_stack=lineage_stack | {path},
        _require_live_evidence=require_live_evidence,
    )
    if prefix == "previous_state":
        if payload["state"] not in _LEGAL_TRANSITIONS[linked["state"]]:
            raise ClosedLoopAttemptStateError("illegal_transition")
        if payload["actor_role"] != linked["required_actor"]:
            raise ClosedLoopAttemptStateError("actor_mismatch")


def transition_state(
    previous_state: Mapping[str, Any],
    *,
    next_state: str,
    actor: str,
    actor_role: str,
    evidence: Mapping[str, Path | str],
    workspace_root: Path,
    previous_state_path: Path | str,
) -> dict[str, Any]:
    previous = validate_state(previous_state, workspace_root=workspace_root)
    previous_record = _published_state_record(
        previous,
        previous_state_path,
        workspace_root=workspace_root,
        label="previous_state",
    )
    if previous["terminal"]:
        raise ClosedLoopAttemptStateError("terminal_state_continuation")
    if actor_role != previous["required_actor"]:
        raise ClosedLoopAttemptStateError("actor_mismatch")
    if next_state not in _STATE_POLICY:
        raise ClosedLoopAttemptStateError("next_state_invalid")
    if next_state not in _LEGAL_TRANSITIONS[previous["state"]]:
        raise ClosedLoopAttemptStateError("illegal_transition")
    records = _evidence_records(
        evidence,
        workspace_root=workspace_root,
        fixture=previous["fixture"],
    )
    disposition, required_actor, terminal = _STATE_POLICY[next_state]
    state: dict[str, Any] = {
        "schema": SCHEMA,
        "attempt_id": previous["attempt_id"],
        "fixture": previous["fixture"],
        "sequence": previous["sequence"] + 1,
        "state": next_state,
        "previous_state_sha256": previous_record["state_sha256"],
        "previous_state_path": previous_record["path"],
        "previous_state_file_sha256": previous_record["file_sha256"],
        "parent_state_sha256": previous["parent_state_sha256"],
        "parent_state_path": previous["parent_state_path"],
        "parent_state_file_sha256": previous["parent_state_file_sha256"],
        "actor": actor,
        "actor_role": actor_role,
        "evidence": records,
        "disposition": disposition,
        "required_actor": required_actor,
        "terminal": terminal,
        "publication_acceptance": PUBLICATION_ACCEPTANCE,
    }
    state["state_sha256"] = canonical_state_sha256(state)
    return validate_state(state, workspace_root=workspace_root)


def validate_chain(
    states: Sequence[Mapping[str, Any]],
    *,
    workspace_root: Path,
    parent_state: Mapping[str, Any] | None = None,
    parent_state_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(states, Sequence) or isinstance(states, (str, bytes)) or not states:
        raise ClosedLoopAttemptStateError("state_chain_missing")
    chain = [validate_state(state, workspace_root=workspace_root) for state in states]
    first = chain[0]
    if first["sequence"] != 0 or first["previous_state_sha256"] is not None:
        raise ClosedLoopAttemptStateError("chain_initial_state_invalid")
    expected_parent_record = None
    if parent_state is not None:
        if parent_state_path is None:
            raise ClosedLoopAttemptStateError("parent_state_path_missing")
        parent = validate_state(parent_state, workspace_root=workspace_root)
        if parent["fixture"] != first["fixture"]:
            raise ClosedLoopAttemptStateError("parent_fixture_mismatch")
        expected_parent_record = _published_state_record(
            parent,
            parent_state_path,
            workspace_root=workspace_root,
            label="parent_state",
        )
    elif parent_state_path is not None:
        raise ClosedLoopAttemptStateError("parent_state_missing")
    expected_parent = (
        (None, None, None)
        if expected_parent_record is None
        else (
            expected_parent_record["state_sha256"],
            expected_parent_record["path"],
            expected_parent_record["file_sha256"],
        )
    )
    if (
        first["parent_state_sha256"],
        first["parent_state_path"],
        first["parent_state_file_sha256"],
    ) != expected_parent:
        raise ClosedLoopAttemptStateError("parent_state_hash_mismatch")
    for previous, current in zip(chain, chain[1:], strict=False):
        if (
            current["attempt_id"] != first["attempt_id"]
            or current["fixture"] != first["fixture"]
            or (
                current["parent_state_sha256"],
                current["parent_state_path"],
                current["parent_state_file_sha256"],
            )
            != expected_parent
        ):
            raise ClosedLoopAttemptStateError("chain_identity_drift")
        if current["sequence"] != previous["sequence"] + 1:
            raise ClosedLoopAttemptStateError("sequence_drift")
        if current["previous_state_sha256"] != previous["state_sha256"]:
            raise ClosedLoopAttemptStateError("previous_state_hash_mismatch")
        previous_file = state_path(previous, workspace_root=workspace_root)
        if (
            current["previous_state_path"]
            != previous_file.relative_to(Path(os.path.abspath(workspace_root))).as_posix()
            or current["previous_state_file_sha256"] != _file_sha256(previous_file)
        ):
            raise ClosedLoopAttemptStateError("previous_state_file_mismatch")
        if previous["terminal"]:
            raise ClosedLoopAttemptStateError("terminal_state_continuation")
        if current["state"] not in _LEGAL_TRANSITIONS[previous["state"]]:
            raise ClosedLoopAttemptStateError("illegal_transition")
        if current["actor_role"] != previous["required_actor"]:
            raise ClosedLoopAttemptStateError("actor_mismatch")
    return chain


def publish_state(
    state: Mapping[str, Any],
    *,
    workspace_root: Path,
) -> Path:
    """Publish one canonical state path exactly once, without replacement."""
    payload = validate_state(state, workspace_root=workspace_root)
    output = state_path(payload, workspace_root=workspace_root)
    try:
        repair_transaction.atomic_create_json(output, payload)
    except FileExistsError as exc:
        raise ClosedLoopAttemptStateError("state_already_published") from exc
    try:
        _published_state_record(
            payload,
            output,
            workspace_root=workspace_root,
            label="published_state",
        )
    except ClosedLoopAttemptStateError as exc:
        root = Path(os.path.abspath(workspace_root))
        relative = output.relative_to(root).as_posix()
        raise ClosedLoopAttemptStateError(
            f"state_published_but_stale:{relative}",
            path=output,
        ) from exc
    return output
