"""Canonical repair-candidate-ready to repair-authorized adapter."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import authoring_repair_packet
import closed_loop_attempt_state
import closed_loop_current_state
import closed_loop_post_review_authority as authority
import human_decision_record
import repair_transaction

ACTION = "closed_loop_repair_authorize"
STOP_BOUNDARY = "workflow_agent"


class ClosedLoopRepairAuthorizationError(ValueError):
    """Raised when an explicit repair authorization cannot advance safely."""


def _json_snapshot(path: Path, *, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        content = path.read_bytes()
        payload = json.loads(content)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopRepairAuthorizationError(f"{label}_invalid") from exc
    if not isinstance(payload, dict):
        raise ClosedLoopRepairAuthorizationError(f"{label}_invalid")
    return payload, content


def _lineage_file(
    state: dict[str, Any],
    role: str,
    *,
    workspace_root: Path,
) -> Path:
    record = authority.lineage_evidence_record(
        state,
        role,
        workspace_root=workspace_root,
    )
    return authority.workspace_file(
        workspace_root,
        str(record.get("path") or ""),
        label=role,
    )


def _assert_current_state(
    state: dict[str, Any],
    state_path: Path,
    *,
    workspace_root: Path,
) -> None:
    projection = closed_loop_current_state.resolve_current_attempt(
        workspace_root,
        state["fixture"],
    )
    expected_path = state_path.relative_to(workspace_root).as_posix()
    if (
        projection.get("resolution") != "current"
        or projection.get("state") != "repair_candidate_ready"
        or projection.get("required_actor") != "human_repair_authorizer"
        or projection.get("terminal") is not False
        or projection.get("publication_acceptance") != "not_claimed"
        or projection.get("path") != expected_path
        or projection.get("state_sha256") != state["state_sha256"]
    ):
        raise ClosedLoopRepairAuthorizationError(
            "closed_loop_canonical_current_state_drift"
        )


def _validate_preview(
    preview: dict[str, Any],
    *,
    packet: dict[str, Any],
) -> None:
    try:
        authoring_repair_packet.validate_materialization_preview(
            preview,
            packet=packet,
        )
    except authoring_repair_packet.RepairExecutionPacketError as exc:
        raise ClosedLoopRepairAuthorizationError(
            "materialization_preview_invalid"
        ) from exc


def _validated_plan(
    fixture: str,
    *,
    state_path: Path,
    authorization_path: Path,
    workspace_root: Path,
    expected_state_sha256: str | None,
) -> dict[str, Any]:
    state, published_state_path = authority.load_published_state(
        workspace_root=workspace_root,
        fixture=fixture,
        state_path=state_path,
    )
    if expected_state_sha256 is not None and state["state_sha256"] != expected_state_sha256:
        raise ClosedLoopRepairAuthorizationError(
            "closed_loop_projected_state_hash_mismatch"
        )
    if state["state"] != "repair_candidate_ready":
        raise ClosedLoopRepairAuthorizationError(
            "closed_loop_state_not_repair_candidate_ready"
        )
    packet_path = _lineage_file(
        state,
        "repair_execution_packet",
        workspace_root=workspace_root,
    )
    preview_path = _lineage_file(
        state,
        "materialization_preview",
        workspace_root=workspace_root,
    )
    response_path = _lineage_file(
        state,
        "repair_response",
        workspace_root=workspace_root,
    )
    authorization_path = authority.workspace_file(
        workspace_root,
        authorization_path,
        label="human_authorization",
    )
    if not (
        packet_path.parent
        == response_path.parent
        == preview_path.parent
        == authorization_path.parent
    ):
        raise ClosedLoopRepairAuthorizationError(
            "repair_authorization_and_candidate_must_be_adjacent"
        )

    packet, packet_bytes = _json_snapshot(
        packet_path,
        label="repair_execution_packet",
    )
    response, response_bytes = _json_snapshot(
        response_path,
        label="repair_response",
    )
    preview, preview_bytes = _json_snapshot(
        preview_path,
        label="materialization_preview",
    )
    authorization, authorization_bytes = _json_snapshot(
        authorization_path,
        label="human_authorization",
    )
    if (
        packet.get("schema")
        not in {
            authoring_repair_packet.SCHEMA,
            authoring_repair_packet.ATTEMPT_LOCAL_PACKET_SCHEMA,
        }
        or packet.get("packet_sha256")
        != authoring_repair_packet.canonical_packet_sha256(packet)
    ):
        raise ClosedLoopRepairAuthorizationError("current_repair_packet_required")
    try:
        authoring_repair_packet.validate_bound_packet_authority(
            packet,
            workspace_root,
        )
    except authoring_repair_packet.RepairExecutionPacketError as exc:
        raise ClosedLoopRepairAuthorizationError(
            f"repair_packet_authority_invalid:{exc}"
        ) from exc
    _validate_preview(preview, packet=packet)
    try:
        expected_preview = authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace_root,
            apply=False,
        )
    except authoring_repair_packet.RepairExecutionPacketError as exc:
        raise ClosedLoopRepairAuthorizationError(
            f"repair_response_invalid:{exc}"
        ) from exc
    if expected_preview != preview:
        raise ClosedLoopRepairAuthorizationError(
            "repair_response_preview_mismatch"
        )
    try:
        normalized_authorization = (
            human_decision_record.validate_additive_materialization_authorization(
                authorization,
                fixture=fixture,
                packet_schema=str(packet.get("schema") or ""),
                packet_sha256=str(packet.get("packet_sha256") or ""),
                output_path=str(preview.get("output_path") or ""),
                output_sha256=str(preview.get("output_sha256") or ""),
                preview_sha256=str(preview.get("preview_sha256") or ""),
            )
        )
    except human_decision_record.HumanDecisionRecordError as exc:
        raise ClosedLoopRepairAuthorizationError(
            f"materialization_authorization_invalid:{exc}"
        ) from exc

    next_state_path = published_state_path.parent / (
        f"state-{state['sequence'] + 1:03d}-repair_authorized.json"
    )
    return {
        "state": state,
        "state_path": published_state_path,
        "packet_path": packet_path,
        "packet_bytes": packet_bytes,
        "response_bytes": response_bytes,
        "preview_path": preview_path,
        "preview_bytes": preview_bytes,
        "authorization_path": authorization_path,
        "authorization_bytes": authorization_bytes,
        "reviewer": normalized_authorization["reviewer"],
        "next_state_path": next_state_path,
    }


def _expected_authorized_state(
    plan: dict[str, Any],
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    return closed_loop_attempt_state.transition_state(
        plan["state"],
        next_state="repair_authorized",
        actor=str(plan["reviewer"]),
        actor_role="human_repair_authorizer",
        evidence={"human_authorization": plan["authorization_path"]},
        workspace_root=workspace_root,
        previous_state_path=plan["state_path"],
    )


def _matching_published_authorization(
    fixture: str,
    plan: dict[str, Any],
    *,
    workspace_root: Path,
) -> dict[str, Any] | None:
    next_state_path = plan["next_state_path"]
    if not next_state_path.exists() and not next_state_path.is_symlink():
        return None
    try:
        published, published_path = authority.load_published_state(
            workspace_root=workspace_root,
            fixture=fixture,
            state_path=next_state_path,
        )
        expected = _expected_authorized_state(plan, workspace_root=workspace_root)
    except (
        authority.ClosedLoopPostReviewError,
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        OSError,
        ValueError,
    ) as exc:
        raise ClosedLoopRepairAuthorizationError(
            f"repair_authorized_recovery_invalid:{exc}"
        ) from exc
    if published_path != next_state_path or published != expected:
        raise ClosedLoopRepairAuthorizationError("repair_authorized_state_conflict")
    projection = closed_loop_current_state.resolve_current_attempt(
        workspace_root,
        fixture,
    )
    if (
        projection.get("resolution") != "current"
        or projection.get("state") != "repair_authorized"
        or projection.get("required_actor") != "workflow_agent"
        or projection.get("terminal") is not False
        or projection.get("publication_acceptance") != "not_claimed"
        or projection.get("path")
        != published_path.relative_to(workspace_root).as_posix()
        or projection.get("state_sha256") != published["state_sha256"]
    ):
        raise ClosedLoopRepairAuthorizationError(
            "closed_loop_canonical_current_state_drift"
        )
    return published


def _recovered_result(plan: dict[str, Any], published: dict[str, Any]) -> dict[str, Any]:
    return {
        "action": ACTION,
        "stop_boundary": STOP_BOUNDARY,
        "stop_reason": "repair_authorized_recovered",
        "required_actor": "workflow_agent",
        "created": False,
        "input_state": plan["state"],
        "input_state_path": plan["state_path"],
        "next_state": "repair_authorized",
        "next_state_path": plan["next_state_path"],
        "authorization_path": plan["authorization_path"],
        "published_state": published,
        "publication_acceptance": "not_claimed",
    }


def run_authorization(
    fixture: str,
    *,
    state_path: Path,
    authorization_path: Path,
    execute: bool,
    workspace_root: Path,
    expected_state_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate or publish one explicitly supplied human repair authorization."""
    root = Path(os.path.abspath(workspace_root))
    try:
        plan = _validated_plan(
            fixture,
            state_path=state_path,
            authorization_path=authorization_path,
            workspace_root=root,
            expected_state_sha256=expected_state_sha256,
        )
        published = _matching_published_authorization(
            fixture,
            plan,
            workspace_root=root,
        )
        if published is not None:
            return _recovered_result(plan, published)
        _assert_current_state(
            plan["state"],
            plan["state_path"],
            workspace_root=root,
        )
        if not execute:
            return {
                "action": ACTION,
                "stop_boundary": STOP_BOUNDARY,
                "stop_reason": "plan_only",
                "required_actor": "workflow_agent",
                "created": False,
                "input_state": plan["state"],
                "input_state_path": plan["state_path"],
                "next_state": "repair_authorized",
                "next_state_path": plan["next_state_path"],
                "authorization_path": plan["authorization_path"],
                "publication_acceptance": "not_claimed",
            }

        with closed_loop_attempt_state.attempt_transition_lock(
            plan["state_path"].parent
        ):
            current = _validated_plan(
                fixture,
                state_path=state_path,
                authorization_path=authorization_path,
                workspace_root=root,
                expected_state_sha256=expected_state_sha256,
            )
            published = _matching_published_authorization(
                fixture,
                current,
                workspace_root=root,
            )
            if published is not None:
                return _recovered_result(current, published)
            _assert_current_state(
                current["state"],
                current["state_path"],
                workspace_root=root,
            )
            for key in (
                "packet_bytes",
                "response_bytes",
                "preview_bytes",
                "authorization_bytes",
            ):
                if current[key] != plan[key]:
                    raise ClosedLoopRepairAuthorizationError(
                        "repair_authorization_inputs_drifted"
                    )
            next_state = _expected_authorized_state(
                current,
                workspace_root=root,
            )
            next_state_path = closed_loop_attempt_state.publish_state(
                next_state,
                workspace_root=root,
            )
        return {
            "action": ACTION,
            "stop_boundary": STOP_BOUNDARY,
            "stop_reason": "repair_authorized",
            "required_actor": "workflow_agent",
            "created": True,
            "input_state": current["state"],
            "input_state_path": current["state_path"],
            "next_state": "repair_authorized",
            "next_state_path": next_state_path,
            "authorization_path": current["authorization_path"],
            "published_state": next_state,
            "publication_acceptance": "not_claimed",
        }
    except ClosedLoopRepairAuthorizationError:
        raise
    except (
        authoring_repair_packet.RepairExecutionPacketError,
        authority.ClosedLoopPostReviewError,
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        human_decision_record.HumanDecisionRecordError,
        repair_transaction.RepairTransactionError,
        OSError,
        ValueError,
    ) as exc:
        raise ClosedLoopRepairAuthorizationError(
            f"repair_authorization_failed:{exc}"
        ) from exc
