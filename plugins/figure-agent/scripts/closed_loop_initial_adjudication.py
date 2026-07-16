"""Canonical human decision boundary after an initial visual review.

This adapter accepts one human-authored decision in the current attempt only.
It intentionally stops before repair binding: approval creates a constrained
attribution handoff and rejection closes the attempt.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import closed_loop_current_state
import critique_contract
import repair_transaction

SCHEMA = "figure-agent.initial-human-adjudication.v1"
HANDOFF_SCHEMA = "figure-agent.initial-attribution-handoff.v1"
ACTION = "closed_loop_initial_adjudication"
DECISION_DIRECTORY = "initial-adjudication"
DECISION_FILE = "decision.json"
DECISION_SNAPSHOT_FILE = "decision.snapshot.json"
HANDOFF_FILE = "attribution-handoff.json"
PUBLICATION_ACCEPTANCE = "not_claimed"
_RESPONSE_ROLES = (
    "critique",
    "host_review_execution_receipt",
    "host_review_transcript",
    "initial_visual_review_response",
)
_DECISION_KEYS = {
    "schema",
    "fixture",
    "attempt_id",
    "current_state",
    "response",
    "critique",
    "host_review_execution_receipt",
    "host_review_transcript",
    "reviewer",
    "rationale",
    "decision",
    "attribution",
    "publication_acceptance",
    "decision_sha256",
}


class ClosedLoopInitialAdjudicationError(ValueError):
    """Raised when a human decision cannot safely advance the current attempt."""


@dataclass(frozen=True)
class _DecisionSnapshot:
    path: Path
    payload: dict[str, Any]
    content: bytes
    fingerprint: tuple[int, int, int, int, int]

    @property
    def sha256(self) -> str:
        return _sha256_bytes(self.content)


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def canonical_decision_sha256(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "decision_sha256"}
    return _sha256_bytes(
        json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )


def _regular_file(path: Path, *, root: Path, label: str) -> Path:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ClosedLoopInitialAdjudicationError(f"{label}_outside_workspace") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ClosedLoopInitialAdjudicationError(f"{label}_symlink")
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        raise ClosedLoopInitialAdjudicationError(f"{label}_missing") from exc
    if not stat.S_ISREG(mode):
        raise ClosedLoopInitialAdjudicationError(f"{label}_not_regular")
    return path


def _load_json(path: Path, *, root: Path, label: str) -> tuple[dict[str, Any], bytes]:
    _regular_file(path, root=root, label=label)
    try:
        before = path.stat()
        content = path.read_bytes()
        after = path.stat()
        payload = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopInitialAdjudicationError(f"{label}_invalid") from exc
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise ClosedLoopInitialAdjudicationError(f"{label}_changed_during_snapshot")
    if not isinstance(payload, dict):
        raise ClosedLoopInitialAdjudicationError(f"{label}_invalid")
    return payload, content


def _snapshot_decision(path: Path, *, root: Path) -> _DecisionSnapshot:
    _regular_file(path, root=root, label="initial_adjudication_decision")
    try:
        before = path.stat()
        content = path.read_bytes()
        after = path.stat()
        payload = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_decision_invalid") from exc
    fingerprint = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    ) != fingerprint:
        raise ClosedLoopInitialAdjudicationError(
            "initial_adjudication_decision_changed_during_snapshot"
        )
    if not isinstance(payload, dict):
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_decision_invalid")
    return _DecisionSnapshot(path=path, payload=payload, content=content, fingerprint=fingerprint)


def _assert_snapshot_still_current(snapshot: _DecisionSnapshot, *, root: Path) -> None:
    _regular_file(snapshot.path, root=root, label="initial_adjudication_decision")
    try:
        before = snapshot.path.stat()
        content = snapshot.path.read_bytes()
        after = snapshot.path.stat()
    except OSError as exc:
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_decision_drift") from exc
    fingerprint = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if (
        (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        != fingerprint
        or fingerprint != snapshot.fingerprint
        or content != snapshot.content
    ):
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_decision_drift")


def _load_state(root: Path, fixture: str, state_path: Path) -> tuple[dict[str, Any], Path]:
    relative = Path(state_path)
    path = Path(os.path.abspath(relative if relative.is_absolute() else root / relative))
    payload, _ = _load_json(path, root=root, label="closed_loop_state")
    try:
        state = closed_loop_attempt_state.validate_state(payload, workspace_root=root)
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise ClosedLoopInitialAdjudicationError(f"closed_loop_state_invalid:{exc}") from exc
    if state["fixture"] != fixture:
        raise ClosedLoopInitialAdjudicationError("closed_loop_state_fixture_mismatch")
    if path != closed_loop_attempt_state.state_path(state, workspace_root=root):
        raise ClosedLoopInitialAdjudicationError("closed_loop_state_path_mismatch")
    return state, path


def _assert_current(root: Path, fixture: str, state: dict[str, Any], path: Path) -> None:
    current = closed_loop_current_state.resolve_current_attempt(root, fixture)
    if (
        current.get("resolution") != "current"
        or current.get("path") != path.relative_to(root).as_posix()
        or current.get("state_sha256") != state["state_sha256"]
    ):
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_current_state_mismatch")


def _evidence_by_role(state: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {str(record["role"]): record for record in state["evidence"]}


def _reference(value: Any, *, expected: dict[str, str], label: str) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != {"path", "sha256"}
        or value.get("path") != expected["path"]
        or value.get("sha256") != expected["sha256"]
    ):
        raise ClosedLoopInitialAdjudicationError(f"initial_adjudication_{label}_mismatch")


def _human(value: Any, *, label: str) -> dict[str, str]:
    if (
        not isinstance(value, dict)
        or set(value) != {"kind", "identity"}
        or value.get("kind") != "human"
        or not isinstance(value.get("identity"), str)
        or not value["identity"].strip()
    ):
        raise ClosedLoopInitialAdjudicationError(f"initial_adjudication_{label}_invalid")
    return {"kind": "human", "identity": value["identity"].strip()}


def _critique_finding_ids(path: Path, *, fixture: str) -> set[str]:
    try:
        frontmatter = critique_contract.load_critique_frontmatter(path)
        if frontmatter.get("fixture") != fixture:
            raise critique_contract.CritiqueContractError("fixture mismatch")
        ids = [
            critique_contract.critique_finding_id(item, "initial critique finding")
            for item in critique_contract.critique_findings(frontmatter)
        ]
    except (critique_contract.CritiqueContractError, ValueError) as exc:
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_critique_invalid") from exc
    if not ids or len(ids) != len(set(ids)):
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_critique_invalid")
    return set(ids)


def _nonempty_string_list(value: Any, *, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ClosedLoopInitialAdjudicationError(f"initial_adjudication_{label}_invalid")
    return [item.strip() for item in value]


def _validate_decision(
    *, root: Path, fixture: str, state: dict[str, Any], state_path: Path, decision_path: Path
) -> tuple[_DecisionSnapshot, dict[str, Any] | None]:
    expected_path = state_path.parent / DECISION_DIRECTORY / DECISION_FILE
    if decision_path != expected_path:
        raise ClosedLoopInitialAdjudicationError(
            "initial_adjudication_decision_path_outside_attempt"
        )
    if decision_path.parent.is_symlink() or not decision_path.parent.is_dir():
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_decision_directory_invalid")
    snapshot = _snapshot_decision(decision_path, root=root)
    decision = snapshot.payload
    if set(decision) != _DECISION_KEYS or decision.get("schema") != SCHEMA:
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_decision_schema_invalid")
    if decision.get("decision_sha256") != canonical_decision_sha256(decision):
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_decision_hash_invalid")
    if (
        decision.get("fixture") != fixture
        or decision.get("attempt_id") != state["attempt_id"]
        or decision.get("publication_acceptance") != PUBLICATION_ACCEPTANCE
        or not isinstance(decision.get("rationale"), str)
        or not decision["rationale"].strip()
    ):
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_decision_invalid")
    _reference(
        decision.get("current_state"),
        expected={"path": state_path.relative_to(root).as_posix(), "sha256": state["state_sha256"]},
        label="state",
    )
    evidence = _evidence_by_role(state)
    for role, key in (
        ("initial_visual_review_response", "response"),
        ("critique", "critique"),
        ("host_review_execution_receipt", "host_review_execution_receipt"),
        ("host_review_transcript", "host_review_transcript"),
    ):
        if role not in evidence:
            raise ClosedLoopInitialAdjudicationError(
                "initial_adjudication_response_provenance_missing"
            )
        _reference(decision.get(key), expected=evidence[role], label=key)
    _human(decision.get("reviewer"), label="reviewer")
    action = decision.get("decision")
    attribution = decision.get("attribution")
    if action == "reject_initial_review":
        if attribution is not None:
            raise ClosedLoopInitialAdjudicationError(
                "initial_adjudication_reject_attribution_invalid"
            )
        return snapshot, None
    if action != "approve_for_attribution" or not isinstance(attribution, dict):
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_action_invalid")
    expected_keys = {
        "selected_finding_ids",
        "human_attributor",
        "permitted_scope",
        "forbidden_scope",
        "source_mutation",
    }
    if set(attribution) != expected_keys or attribution.get("source_mutation") != "forbidden":
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_attribution_invalid")
    selected = _nonempty_string_list(
        attribution.get("selected_finding_ids"), label="selected_finding_ids"
    )
    if len(selected) != len(set(selected)):
        raise ClosedLoopInitialAdjudicationError(
            "initial_adjudication_selected_finding_ids_invalid"
        )
    critique_path = root / evidence["critique"]["path"]
    if not set(selected).issubset(_critique_finding_ids(critique_path, fixture=fixture)):
        raise ClosedLoopInitialAdjudicationError(
            "initial_adjudication_selected_finding_ids_invalid"
        )
    _human(attribution.get("human_attributor"), label="human_attributor")
    permitted = _nonempty_string_list(attribution.get("permitted_scope"), label="permitted_scope")
    forbidden = _nonempty_string_list(attribution.get("forbidden_scope"), label="forbidden_scope")
    if set(permitted) & set(forbidden):
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_scope_overlap")
    return snapshot, attribution


def _handoff_payload(
    *,
    decision: dict[str, Any],
    attribution: dict[str, Any],
    root: Path,
    decision_snapshot_path: Path,
    decision_snapshot_sha256: str,
) -> dict[str, Any]:
    return {
        "schema": HANDOFF_SCHEMA,
        "fixture": decision["fixture"],
        "attempt_id": decision["attempt_id"],
        "adjudication": {
            "path": decision_snapshot_path.relative_to(root).as_posix(),
            "sha256": decision_snapshot_sha256,
        },
        "selected_finding_ids": attribution["selected_finding_ids"],
        "human_attributor": attribution["human_attributor"],
        "permitted_scope": attribution["permitted_scope"],
        "forbidden_scope": attribution["forbidden_scope"],
        "source_mutation": "forbidden",
        "publication_acceptance": PUBLICATION_ACCEPTANCE,
    }


def _decision_snapshot_path(decision_path: Path) -> Path:
    return decision_path.parent / DECISION_SNAPSHOT_FILE


def _publish_decision_snapshot(path: Path, snapshot: _DecisionSnapshot, *, root: Path) -> None:
    if path.exists():
        _regular_file(path, root=root, label="initial_adjudication_decision_snapshot")
        try:
            existing = path.read_bytes()
        except OSError as exc:
            raise ClosedLoopInitialAdjudicationError(
                "initial_adjudication_decision_snapshot_invalid"
            ) from exc
        if existing != snapshot.content:
            raise ClosedLoopInitialAdjudicationError(
                "initial_adjudication_decision_snapshot_conflict"
            )
        return
    try:
        repair_transaction.atomic_create_text(path, snapshot.content.decode("utf-8"))
    except (FileExistsError, UnicodeDecodeError) as exc:
        if isinstance(exc, UnicodeDecodeError):
            raise ClosedLoopInitialAdjudicationError(
                "initial_adjudication_decision_snapshot_invalid"
            ) from exc
        _publish_decision_snapshot(path, snapshot, root=root)


def _assert_published_snapshot_matches(
    path: Path, snapshot: _DecisionSnapshot, *, root: Path
) -> None:
    _regular_file(path, root=root, label="initial_adjudication_decision_snapshot")
    try:
        existing = path.read_bytes()
    except OSError as exc:
        raise ClosedLoopInitialAdjudicationError(
            "initial_adjudication_decision_snapshot_invalid"
        ) from exc
    if existing != snapshot.content:
        raise ClosedLoopInitialAdjudicationError("initial_adjudication_decision_snapshot_conflict")


def _publish_handoff(path: Path, payload: dict[str, Any], *, root: Path) -> None:
    if path.exists():
        existing, _ = _load_json(path, root=root, label="initial_adjudication_handoff")
        if existing != payload:
            raise ClosedLoopInitialAdjudicationError("initial_adjudication_handoff_conflict")
        return
    try:
        repair_transaction.atomic_create_json(path, payload)
    except FileExistsError:
        existing, _ = _load_json(path, root=root, label="initial_adjudication_handoff")
        if existing != payload:
            raise ClosedLoopInitialAdjudicationError("initial_adjudication_handoff_conflict")


def _existing_matches(
    state: dict[str, Any],
    *,
    next_state: str,
    decision_snapshot_path: Path,
    decision_snapshot_sha256: str,
    handoff_path: Path | None,
    root: Path,
) -> bool:
    if state["state"] != next_state:
        return False
    records = _evidence_by_role(state)
    expected = {
        "adjudication": {
            "role": "adjudication",
            "path": decision_snapshot_path.relative_to(root).as_posix(),
            "sha256": decision_snapshot_sha256,
        },
    }
    if next_state == "adjudicated_unbound":
        assert handoff_path is not None
        expected["attribution_handoff"] = {
            "role": "attribution_handoff",
            "path": handoff_path.relative_to(root).as_posix(),
            "sha256": _sha256(handoff_path),
        }
    else:
        expected = {
            "human_decision_record": {
                "role": "human_decision_record",
                "path": decision_snapshot_path.relative_to(root).as_posix(),
                "sha256": decision_snapshot_sha256,
            }
        }
    for role in _RESPONSE_ROLES:
        record = records.get(role)
        if not isinstance(record, dict):
            return False
        expected[role] = record
    return all(records.get(role) == record for role, record in expected.items())


def run_initial_adjudication(
    fixture: str,
    *,
    state_path: Path,
    decision_path: Path,
    execute: bool,
    workspace_root: Path,
    expected_state_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate a human adjudication and publish reject or attribution-only state."""
    root = Path(os.path.abspath(workspace_root))
    requested = Path(
        os.path.abspath(decision_path if decision_path.is_absolute() else root / decision_path)
    )
    state, published_path = _load_state(root, fixture, state_path)
    if expected_state_sha256 is not None and state["state_sha256"] != expected_state_sha256:
        raise ClosedLoopInitialAdjudicationError("closed_loop_projected_state_hash_mismatch")
    _assert_current(root, fixture, state, published_path)
    if state["state"] in {"adjudicated_unbound", "rejected"}:
        previous = state.get("previous_state_path")
        if not isinstance(previous, str):
            raise ClosedLoopInitialAdjudicationError("initial_adjudication_parent_state_missing")
        parent, parent_path = _load_state(root, fixture, Path(previous))
        if parent["state"] != "critique_unadjudicated":
            raise ClosedLoopInitialAdjudicationError("initial_adjudication_parent_state_invalid")
        snapshot, attribution = _validate_decision(
            root=root,
            fixture=fixture,
            state=parent,
            state_path=parent_path,
            decision_path=requested,
        )
        decision_snapshot_path = _decision_snapshot_path(requested)
        _assert_published_snapshot_matches(decision_snapshot_path, snapshot, root=root)
        expected_next = "adjudicated_unbound" if attribution is not None else "rejected"
        handoff_path = requested.parent / HANDOFF_FILE if attribution is not None else None
        if handoff_path is not None:
            handoff = _handoff_payload(
                decision=snapshot.payload,
                attribution=attribution,
                root=root,
                decision_snapshot_path=decision_snapshot_path,
                decision_snapshot_sha256=snapshot.sha256,
            )
            existing, _ = _load_json(handoff_path, root=root, label="initial_adjudication_handoff")
            if existing != handoff:
                raise ClosedLoopInitialAdjudicationError("initial_adjudication_handoff_conflict")
        if not _existing_matches(
            state,
            next_state=expected_next,
            decision_snapshot_path=decision_snapshot_path,
            decision_snapshot_sha256=snapshot.sha256,
            handoff_path=handoff_path,
            root=root,
        ):
            raise ClosedLoopInitialAdjudicationError("initial_adjudication_published_state_stale")
        return {
            "action": ACTION,
            "created": False,
            "input_state": parent,
            "input_state_path": parent_path,
            "next_state": state["state"],
            "next_state_path": published_path,
            "decision_path": requested,
            "attribution_handoff_path": handoff_path,
            "published_state": state,
            "stop_boundary": state["required_actor"],
            "stop_reason": state["required_actor"],
        }
    if state["state"] != "critique_unadjudicated":
        raise ClosedLoopInitialAdjudicationError("closed_loop_state_not_critique_unadjudicated")
    snapshot, attribution = _validate_decision(
        root=root, fixture=fixture, state=state, state_path=published_path, decision_path=requested
    )
    decision_snapshot_path = _decision_snapshot_path(requested)
    next_name = "adjudicated_unbound" if attribution is not None else "rejected"
    next_path = published_path.parent / f"state-{state['sequence'] + 1:03d}-{next_name}.json"
    handoff_path = requested.parent / HANDOFF_FILE if attribution is not None else None
    if not execute:
        return {
            "action": ACTION,
            "created": False,
            "input_state": state,
            "input_state_path": published_path,
            "next_state": next_name,
            "next_state_path": next_path,
            "decision_path": requested,
            "attribution_handoff_path": handoff_path,
            "published_state": None,
            "stop_boundary": "human_attributor" if attribution else "none",
            "stop_reason": "plan_only",
        }
    try:
        with closed_loop_attempt_state.attempt_transition_lock(published_path.parent):
            current, current_path = _load_state(root, fixture, published_path)
            _assert_current(root, fixture, current, current_path)
            if current != state or current_path != published_path:
                raise ClosedLoopInitialAdjudicationError(
                    "initial_adjudication_state_drift_detected"
                )
            fresh_snapshot, fresh_attribution = _validate_decision(
                root=root,
                fixture=fixture,
                state=current,
                state_path=current_path,
                decision_path=requested,
            )
            if (
                fresh_snapshot.content != snapshot.content
                or fresh_snapshot.fingerprint != snapshot.fingerprint
                or fresh_attribution != attribution
            ):
                raise ClosedLoopInitialAdjudicationError(
                    "initial_adjudication_inputs_drift_detected"
                )
            _assert_snapshot_still_current(fresh_snapshot, root=root)
            _publish_decision_snapshot(decision_snapshot_path, fresh_snapshot, root=root)
            evidence: dict[str, Path] = {
                role: root / _evidence_by_role(current)[role]["path"] for role in _RESPONSE_ROLES
            }
            if attribution is None:
                evidence["human_decision_record"] = decision_snapshot_path
                next_state = closed_loop_attempt_state.transition_state(
                    current,
                    next_state="rejected",
                    actor=fresh_snapshot.payload["reviewer"]["identity"],
                    actor_role="human_adjudicator",
                    evidence=evidence,
                    workspace_root=root,
                    previous_state_path=current_path,
                )
            else:
                assert handoff_path is not None
                handoff = _handoff_payload(
                    decision=fresh_snapshot.payload,
                    attribution=attribution,
                    root=root,
                    decision_snapshot_path=decision_snapshot_path,
                    decision_snapshot_sha256=fresh_snapshot.sha256,
                )
                _publish_handoff(handoff_path, handoff, root=root)
                evidence["adjudication"] = decision_snapshot_path
                evidence["attribution_handoff"] = handoff_path
                next_state = closed_loop_attempt_state.transition_state(
                    current,
                    next_state="adjudicated_unbound",
                    actor=fresh_snapshot.payload["reviewer"]["identity"],
                    actor_role="human_adjudicator",
                    evidence=evidence,
                    workspace_root=root,
                    previous_state_path=current_path,
                )
            try:
                published_next = closed_loop_attempt_state.publish_state(
                    next_state, workspace_root=root
                )
            except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
                if str(exc) != "state_already_published":
                    raise
                existing, existing_path = _load_state(root, fixture, next_path)
                if not _existing_matches(
                    existing,
                    next_state=next_name,
                    decision_snapshot_path=decision_snapshot_path,
                    decision_snapshot_sha256=fresh_snapshot.sha256,
                    handoff_path=handoff_path,
                    root=root,
                ):
                    raise ClosedLoopInitialAdjudicationError(
                        "initial_adjudication_state_conflict"
                    ) from exc
                published_next = existing_path
                next_state = existing
    except (
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        repair_transaction.RepairTransactionError,
        OSError,
        ValueError,
    ) as exc:
        if isinstance(exc, ClosedLoopInitialAdjudicationError):
            raise
        raise ClosedLoopInitialAdjudicationError(
            f"initial_adjudication_publication_failed:{exc}"
        ) from exc
    return {
        "action": ACTION,
        "created": True,
        "input_state": state,
        "input_state_path": published_path,
        "next_state": next_state["state"],
        "next_state_path": published_next,
        "decision_path": requested,
        "attribution_handoff_path": handoff_path,
        "published_state": next_state,
        "stop_boundary": next_state["required_actor"],
        "stop_reason": next_state["required_actor"],
    }
