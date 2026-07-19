"""Canonical repair-authorized to machine-repaired adapter."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import authoring_repair_finalize
import authoring_repair_packet
import authoring_repair_rollback
import closed_loop_attempt_state
import closed_loop_current_state
import closed_loop_post_review_authority as authority
import human_decision_record
import post_repair_visual_review
import repair_transaction

ACTION = "authoring_repair_materialize_and_verify"
PLAN_STOP_BOUNDARY = "workflow_agent"
FAILURE_STOP_BOUNDARY = "repair_required"
ATTEMPT_LOCAL_POST_REPAIR_BOUNDARY = "human_or_host_post_repair_review"
RECEIPT_NAME = "materialization_receipt.json"


class ClosedLoopMachineRepairError(ValueError):
    """Raised when an authorized repair cannot advance safely."""


def _post_repair_boundary(plan: dict[str, Any]) -> tuple[str, str]:
    """Keep v2 at a human/host boundary until R4.14 is implemented."""
    if authoring_repair_packet.is_attempt_local_packet_schema(
        plan["packet"].get("schema")
    ):
        return ATTEMPT_LOCAL_POST_REPAIR_BOUNDARY, "human_or_host"
    return PLAN_STOP_BOUNDARY, "workflow_agent"


def _json_snapshot(path: Path, *, label: str) -> tuple[dict[str, Any], str]:
    try:
        content = path.read_bytes()
        payload = json.loads(content)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopMachineRepairError(f"{label}_invalid") from exc
    if not isinstance(payload, dict):
        raise ClosedLoopMachineRepairError(f"{label}_invalid")
    return payload, "sha256:" + hashlib.sha256(content).hexdigest()


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
        or projection.get("state") != "repair_authorized"
        or projection.get("required_actor") != "workflow_agent"
        or projection.get("terminal") is not False
        or projection.get("publication_acceptance") != "not_claimed"
        or projection.get("path") != expected_path
        or projection.get("state_sha256") != state["state_sha256"]
    ):
        raise ClosedLoopMachineRepairError("closed_loop_canonical_current_state_drift")


def _existing_receipt_recovery(
    *,
    packet: dict[str, Any],
    preview: dict[str, Any],
    response_record: dict[str, Any],
    output_path: Path,
    receipt_path: Path,
    workspace_root: Path,
) -> tuple[str, dict[str, Any]] | None:
    if not (receipt_path.exists() or receipt_path.is_symlink()):
        return None
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise ClosedLoopMachineRepairError("materialization_receipt_invalid")
    receipt = authority.load_json(receipt_path, label="materialization_receipt")
    if receipt.get("recovery_required") is True:
        if (
            receipt.get("schema") != authoring_repair_finalize.RECEIPT_SCHEMA
            or receipt.get("packet_sha256") != packet.get("packet_sha256")
            or receipt.get("output_path") != packet.get("output_path")
            or receipt.get("output_sha256") != preview.get("output_sha256")
            or receipt.get("preview_sha256") != preview.get("preview_sha256")
            or receipt.get("repair_response") != response_record
            or receipt.get("publication_acceptance") != "not_claimed"
        ):
            raise ClosedLoopMachineRepairError("prepared_receipt_recovery_invalid")
        if receipt.get("decision") == "materialized_verification_prepared":
            return "resume_finalize", receipt
        if receipt.get("decision") == authoring_repair_rollback.PREPARED_DECISION:
            return "resume_rollback", receipt
        raise ClosedLoopMachineRepairError("machine_repair_recovery_required")
    terminal_state = (
        "machine_repaired"
        if receipt.get("decision")
        == "materialized_machine_verified_human_review_pending"
        else "repair_required"
    )
    _validate_terminal_receipt(
        receipt,
        next_state=terminal_state,
        packet=packet,
        preview=preview,
        response_record=response_record,
        output_path=output_path,
        workspace_root=workspace_root,
    )
    return terminal_state, receipt


def _validate_terminal_receipt(
    receipt: dict[str, Any],
    *,
    next_state: str,
    packet: dict[str, Any],
    preview: dict[str, Any],
    response_record: dict[str, Any],
    output_path: Path,
    workspace_root: Path,
) -> None:
    if (
        receipt.get("schema") != authoring_repair_finalize.RECEIPT_SCHEMA
        or receipt.get("packet_sha256") != packet.get("packet_sha256")
        or receipt.get("output_path") != packet.get("output_path")
        or receipt.get("output_sha256") != preview.get("output_sha256")
        or receipt.get("preview_sha256") != preview.get("preview_sha256")
        or receipt.get("repair_response") != response_record
        or receipt.get("publication_acceptance") != "not_claimed"
        or receipt.get("recovery_required") is not False
    ):
        raise ClosedLoopMachineRepairError("materialization_receipt_recovery_invalid")

    decision = receipt.get("decision")
    if next_state == "machine_repaired":
        if decision != "materialized_machine_verified_human_review_pending":
            raise ClosedLoopMachineRepairError("machine_repaired_receipt_invalid")
        post_repair_visual_review._validate_machine_verification_receipt(
            receipt,
            packet=packet,
            workspace_root=workspace_root,
        )
        return
    if next_state != "repair_required":
        raise ClosedLoopMachineRepairError("terminal_recovery_state_invalid")
    if decision != authoring_repair_rollback.ROLLED_BACK_DECISION:
        raise ClosedLoopMachineRepairError("materialization_receipt_already_exists")
    rollback = receipt.get("rollback")
    if (
        output_path.exists()
        or output_path.is_symlink()
        or receipt.get("post_render_verification") != "failed"
        or not isinstance(rollback, dict)
        or rollback.get("strategy")
        != authoring_repair_rollback.ROLLBACK_STRATEGY
        or rollback.get("pre_transaction_state") != "absent"
        or rollback.get("output_path") != packet.get("output_path")
        or rollback.get("output_sha256") != preview.get("output_sha256")
        or rollback.get("status") != "completed"
    ):
        raise ClosedLoopMachineRepairError("rolled_back_receipt_recovery_invalid")
    authoring_repair_finalize.validate_failed_compile_evidence(
        receipt,
        workspace_root=workspace_root,
    )


def _ensure_fresh_outputs(
    *,
    output_path: Path,
    receipt_path: Path,
) -> None:
    if output_path.exists() or output_path.is_symlink():
        raise ClosedLoopMachineRepairError("materialized_output_already_exists")
    build_path = output_path.parent / "build"
    if build_path.exists() or build_path.is_symlink():
        raise ClosedLoopMachineRepairError("verification_build_already_exists")


def _validated_plan(
    fixture: str,
    *,
    state_path: Path,
    response_path: Path,
    workspace_root: Path,
    expected_state_sha256: str | None,
) -> dict[str, Any]:
    state, published_state_path = authority.load_published_state(
        workspace_root=workspace_root,
        fixture=fixture,
        state_path=state_path,
    )
    if expected_state_sha256 is not None and state["state_sha256"] != expected_state_sha256:
        raise ClosedLoopMachineRepairError("closed_loop_projected_state_hash_mismatch")
    if state["state"] != "repair_authorized":
        raise ClosedLoopMachineRepairError("closed_loop_state_not_repair_authorized")
    _assert_current_state(
        state,
        published_state_path,
        workspace_root=workspace_root,
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
    authorization_path = _lineage_file(
        state,
        "human_authorization",
        workspace_root=workspace_root,
    )
    lineage_response_path = _lineage_file(
        state,
        "repair_response",
        workspace_root=workspace_root,
    )
    response_path = authority.workspace_file(
        workspace_root,
        response_path,
        label="repair_response",
    )
    if response_path != lineage_response_path:
        raise ClosedLoopMachineRepairError(
            "repair_response_state_binding_mismatch"
        )
    if not (
        packet_path.parent
        == preview_path.parent
        == authorization_path.parent
        == response_path.parent
    ):
        raise ClosedLoopMachineRepairError("repair_response_and_authority_must_be_adjacent")

    packet = authority.load_json(packet_path, label="repair_execution_packet")
    if packet.get("schema") not in {
        authoring_repair_packet.SCHEMA,
        authoring_repair_packet.ATTEMPT_LOCAL_PACKET_SCHEMA,
    }:
        raise ClosedLoopMachineRepairError("current_repair_packet_required")
    stored_preview = authority.load_json(
        preview_path,
        label="materialization_preview",
    )
    authorization = authority.load_json(
        authorization_path,
        label="human_authorization",
    )
    response, response_sha256 = _json_snapshot(
        response_path,
        label="repair_response",
    )
    try:
        computed_preview = authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace_root,
            apply=False,
        )
    except authoring_repair_packet.RepairExecutionPacketError as exc:
        raise ClosedLoopMachineRepairError(f"repair_response_invalid:{exc}") from exc
    if computed_preview != stored_preview:
        raise ClosedLoopMachineRepairError("repair_response_preview_mismatch")
    try:
        human_decision_record.validate_additive_materialization_authorization(
            authorization,
            fixture=fixture,
            packet_schema=str(packet.get("schema") or ""),
            packet_sha256=str(packet.get("packet_sha256") or ""),
            output_path=str(computed_preview.get("output_path") or ""),
            output_sha256=str(computed_preview.get("output_sha256") or ""),
            preview_sha256=str(computed_preview.get("preview_sha256") or ""),
            expected_packet_path=packet_path.relative_to(workspace_root).as_posix(),
        )
    except human_decision_record.HumanDecisionRecordError as exc:
        raise ClosedLoopMachineRepairError(f"materialization_authorization_invalid:{exc}") from exc

    output_path = workspace_root / str(packet.get("output_path") or "")
    receipt_path = packet_path.parent / RECEIPT_NAME
    if output_path.parent != packet_path.parent:
        raise ClosedLoopMachineRepairError("repair_output_not_adjacent")
    response_record = {
        "path": response_path.relative_to(workspace_root).as_posix(),
        "sha256": response_sha256,
        "payload": response,
    }
    recovery = _existing_receipt_recovery(
        packet=packet,
        preview=stored_preview,
        response_record=response_record,
        output_path=output_path,
        receipt_path=receipt_path,
        workspace_root=workspace_root,
    )
    if recovery is None:
        _ensure_fresh_outputs(
            output_path=output_path,
            receipt_path=receipt_path,
        )
    recovery_state, recovery_receipt = recovery or (None, None)
    planned_state = (
        "repair_required"
        if recovery_state in {"repair_required", "resume_rollback"}
        else "machine_repaired"
    )
    next_state_path = published_state_path.parent / (
        f"state-{state['sequence'] + 1:03d}-{planned_state}.json"
    )
    return {
        "state": state,
        "state_path": published_state_path,
        "packet": packet,
        "packet_path": packet_path,
        "preview": stored_preview,
        "preview_path": preview_path,
        "authorization": authorization,
        "authorization_path": authorization_path,
        "response": response,
        "response_record": response_record,
        "response_path": response_path,
        "output_path": output_path,
        "receipt_path": receipt_path,
        "recovery_state": recovery_state,
        "recovery_receipt": recovery_receipt,
        "next_state_path": next_state_path,
    }


def _publish_result_state(
    plan: dict[str, Any],
    *,
    next_state: str,
    evidence: dict[str, Path],
    workspace_root: Path,
    expected_evidence_sha256: str,
) -> tuple[dict[str, Any], Path]:
    _assert_current_state(
        plan["state"],
        plan["state_path"],
        workspace_root=workspace_root,
    )
    state = closed_loop_attempt_state.transition_state(
        plan["state"],
        next_state=next_state,
        actor="fig_run",
        actor_role="workflow_agent",
        evidence=evidence,
        workspace_root=workspace_root,
        previous_state_path=plan["state_path"],
    )
    if any(
        record.get("sha256") != expected_evidence_sha256
        for record in state["evidence"]
    ):
        raise ClosedLoopMachineRepairError("terminal_receipt_changed_during_transition")
    return state, closed_loop_attempt_state.publish_state(
        state,
        workspace_root=workspace_root,
    )


def _publish_terminal_receipt_state(
    plan: dict[str, Any],
    *,
    next_state: str,
    expected_receipt: dict[str, Any],
    workspace_root: Path,
) -> tuple[dict[str, Any], Path]:
    evidence = (
        {
            "materialization_receipt": plan["receipt_path"],
            "machine_verification_receipt": plan["receipt_path"],
        }
        if next_state == "machine_repaired"
        else {"repair_failure_record": plan["receipt_path"]}
    )
    with repair_transaction.recoverable_exclusive_lock(
        plan["receipt_path"].parent / ".materialization.lock",
        owner=repair_transaction.MATERIALIZATION_LOCK_OWNER,
    ):
        disk_receipt, receipt_sha256 = _json_snapshot(
            plan["receipt_path"],
            label="terminal_materialization_receipt",
        )
        if disk_receipt != expected_receipt:
            raise ClosedLoopMachineRepairError("terminal_materialization_receipt_drift")
        _validate_terminal_receipt(
            disk_receipt,
            next_state=next_state,
            packet=plan["packet"],
            preview=plan["preview"],
            response_record=plan["response_record"],
            output_path=plan["output_path"],
            workspace_root=workspace_root,
        )
        return _publish_result_state(
            plan,
            next_state=next_state,
            evidence=evidence,
            workspace_root=workspace_root,
            expected_evidence_sha256=receipt_sha256,
        )


def run_machine_repair(
    fixture: str,
    *,
    state_path: Path,
    response_path: Path,
    execute: bool,
    workspace_root: Path,
    plugin_root: Path,
    expected_state_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate or execute one explicitly supplied authorized repair response."""
    root = Path(os.path.abspath(workspace_root))
    plugin_root = Path(os.path.abspath(plugin_root))
    try:
        plan = _validated_plan(
            fixture,
            state_path=state_path,
            response_path=response_path,
            workspace_root=root,
            expected_state_sha256=expected_state_sha256,
        )
        if not execute:
            next_state = (
                "repair_required"
                if plan["recovery_state"] in {"repair_required", "resume_rollback"}
                else "machine_repaired"
            )
            decision = (
                plan["recovery_receipt"]["decision"]
                if plan["recovery_receipt"] is not None
                else "planned_materialize_strict_verify"
            )
            return {
                "action": ACTION,
                "stop_boundary": PLAN_STOP_BOUNDARY,
                "stop_reason": "plan_only",
                "required_actor": "workflow_agent",
                "created": False,
                "decision": decision,
                "input_state": plan["state"],
                "input_state_path": plan["state_path"],
                "next_state": next_state,
                "next_state_path": plan["next_state_path"],
                "response_path": plan["response_path"],
                "receipt_path": plan["receipt_path"],
                "publication_acceptance": "not_claimed",
            }

        attempt_root = plan["state_path"].parent
        with closed_loop_attempt_state.attempt_transition_lock(attempt_root):
            plan = _validated_plan(
                fixture,
                state_path=state_path,
                response_path=response_path,
                workspace_root=root,
                expected_state_sha256=expected_state_sha256,
            )
            if plan["recovery_state"] in {"machine_repaired", "repair_required"}:
                recovery_state = plan["recovery_state"]
                published_state, published_state_path = (
                    _publish_terminal_receipt_state(
                        plan,
                        next_state=recovery_state,
                        expected_receipt=plan["recovery_receipt"],
                        workspace_root=root,
                    )
                )
                return {
                    "action": ACTION,
                    "stop_boundary": (
                        FAILURE_STOP_BOUNDARY
                        if recovery_state == "repair_required"
                        else _post_repair_boundary(plan)[0]
                    ),
                    "stop_reason": f"{recovery_state}_recovered",
                    "required_actor": (
                        "none"
                        if recovery_state == "repair_required"
                        else _post_repair_boundary(plan)[1]
                    ),
                    "created": True,
                    "decision": plan["recovery_receipt"]["decision"],
                    "input_state": plan["state"],
                    "input_state_path": plan["state_path"],
                    "next_state": recovery_state,
                    "next_state_path": published_state_path,
                    "published_state": published_state,
                    "response_path": plan["response_path"],
                    "receipt_path": plan["receipt_path"],
                    "publication_acceptance": "not_claimed",
                }
            if plan["recovery_state"] == "resume_rollback":
                rolled_back = authoring_repair_rollback.rollback_failed_materialized_candidate(
                    packet_path=plan["packet_path"],
                    receipt_path=plan["receipt_path"],
                    authorization_path=plan["authorization_path"],
                    workspace_root=root,
                )
                published_state, published_state_path = (
                    _publish_terminal_receipt_state(
                        plan,
                        next_state="repair_required",
                        expected_receipt=rolled_back,
                        workspace_root=root,
                    )
                )
                return {
                    "action": ACTION,
                    "stop_boundary": FAILURE_STOP_BOUNDARY,
                    "stop_reason": "repair_required_recovered",
                    "required_actor": "none",
                    "created": True,
                    "decision": rolled_back["decision"],
                    "input_state": plan["state"],
                    "input_state_path": plan["state_path"],
                    "next_state": "repair_required",
                    "next_state_path": published_state_path,
                    "published_state": published_state,
                    "response_path": plan["response_path"],
                    "receipt_path": plan["receipt_path"],
                    "publication_acceptance": "not_claimed",
                }
            if plan["recovery_state"] == "resume_finalize":
                finalized = authoring_repair_finalize.finalize_materialized_candidate(
                    packet_path=plan["packet_path"],
                    receipt_path=plan["receipt_path"],
                    authorization_path=plan["authorization_path"],
                    workspace_root=root,
                    plugin_root=plugin_root,
                )
            else:
                authoring_repair_packet.materialize_repair_candidate(
                    plan["packet"],
                    plan["response"],
                    workspace_root=root,
                    authorization=plan["authorization"],
                    receipt_path=plan["receipt_path"],
                    response_provenance=plan["response_record"],
                )
                finalized = authoring_repair_finalize.finalize_materialized_candidate(
                    packet_path=plan["packet_path"],
                    receipt_path=plan["receipt_path"],
                    authorization_path=plan["authorization_path"],
                    workspace_root=root,
                    plugin_root=plugin_root,
                )
            if finalized.get("post_render_verification") != "passed":
                rolled_back = authoring_repair_rollback.rollback_failed_materialized_candidate(
                    packet_path=plan["packet_path"],
                    receipt_path=plan["receipt_path"],
                    authorization_path=plan["authorization_path"],
                    workspace_root=root,
                )
                if (
                    rolled_back.get("recovery_required") is not False
                    or rolled_back.get("publication_acceptance") != "not_claimed"
                ):
                    raise ClosedLoopMachineRepairError("machine_repair_rollback_incomplete")
                published_state, published_state_path = (
                    _publish_terminal_receipt_state(
                        plan,
                        next_state="repair_required",
                        expected_receipt=rolled_back,
                        workspace_root=root,
                    )
                )
                return {
                    "action": ACTION,
                    "stop_boundary": FAILURE_STOP_BOUNDARY,
                    "stop_reason": "strict_verification_failed",
                    "required_actor": "none",
                    "created": True,
                    "decision": rolled_back["decision"],
                    "input_state": plan["state"],
                    "input_state_path": plan["state_path"],
                    "next_state": "repair_required",
                    "next_state_path": published_state_path,
                    "published_state": published_state,
                    "response_path": plan["response_path"],
                    "receipt_path": plan["receipt_path"],
                    "publication_acceptance": "not_claimed",
                }

            published_state, published_state_path = _publish_terminal_receipt_state(
                plan,
                next_state="machine_repaired",
                expected_receipt=finalized,
                workspace_root=root,
            )
            return {
                "action": ACTION,
                "stop_boundary": _post_repair_boundary(plan)[0],
                "stop_reason": "machine_repaired",
                "required_actor": _post_repair_boundary(plan)[1],
                "created": True,
                "decision": finalized["decision"],
                "input_state": plan["state"],
                "input_state_path": plan["state_path"],
                "next_state": "machine_repaired",
                "next_state_path": published_state_path,
                "published_state": published_state,
                "response_path": plan["response_path"],
                "receipt_path": plan["receipt_path"],
                "publication_acceptance": "not_claimed",
            }
    except ClosedLoopMachineRepairError:
        raise
    except (
        authoring_repair_finalize.AuthoringRepairFinalizeError,
        authoring_repair_packet.RepairExecutionPacketError,
        authoring_repair_rollback.AuthoringRepairRollbackError,
        authority.ClosedLoopPostReviewError,
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        human_decision_record.HumanDecisionRecordError,
        post_repair_visual_review.PostRepairVisualReviewError,
        repair_transaction.RepairTransactionError,
        OSError,
        ValueError,
    ) as exc:
        raise ClosedLoopMachineRepairError(f"machine_repair_failed:{exc}") from exc
