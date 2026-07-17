"""Canonical repair-bound to repair-candidate-ready adapter."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import authoring_repair_packet
import closed_loop_attempt_state
import closed_loop_current_state
import closed_loop_post_review_authority as authority
import repair_transaction

ACTION = "closed_loop_repair_candidate"
STOP_WORKFLOW_BOUNDARY = "workflow_agent"
STOP_HUMAN_BOUNDARY = "human_boundary"


class ClosedLoopRepairCandidateError(ValueError):
    """Raised when explicit repair-candidate evidence is not current and bound."""


def _json_snapshot(path: Path, *, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        content = path.read_bytes()
        payload = json.loads(content)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopRepairCandidateError(f"{label}_invalid") from exc
    if not isinstance(payload, dict):
        raise ClosedLoopRepairCandidateError(f"{label}_invalid")
    return payload, content


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
    if (
        projection.get("resolution") != "current"
        or projection.get("state") != "repair_bound"
        or projection.get("disposition") != "continue"
        or projection.get("required_actor") != "workflow_agent"
        or projection.get("terminal") is not False
        or projection.get("publication_acceptance") != "not_claimed"
        or projection.get("path") != state_path.relative_to(workspace_root).as_posix()
        or projection.get("state_sha256") != state["state_sha256"]
    ):
        raise ClosedLoopRepairCandidateError("closed_loop_canonical_current_state_drift")


def _safe_unmaterialized_output(
    packet: dict[str, Any],
    *,
    workspace_root: Path,
) -> Path:
    relative = Path(str(packet.get("output_path") or ""))
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ClosedLoopRepairCandidateError("repair_candidate_output_path_unsafe")
    current = workspace_root
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ClosedLoopRepairCandidateError("repair_candidate_output_path_symlink")
    output = workspace_root / relative
    if output.exists() or output.is_symlink():
        raise ClosedLoopRepairCandidateError("repair_candidate_output_already_materialized")
    return output


def _validated_plan(
    fixture: str,
    *,
    state_path: Path,
    packet_path: Path,
    response_path: Path,
    preview_path: Path,
    workspace_root: Path,
    expected_state_sha256: str | None,
) -> dict[str, Any]:
    state, published_state_path = authority.load_published_state(
        workspace_root=workspace_root,
        fixture=fixture,
        state_path=state_path,
    )
    if state["state"] != "repair_bound":
        raise ClosedLoopRepairCandidateError("closed_loop_state_not_repair_bound")
    if expected_state_sha256 is not None and state["state_sha256"] != expected_state_sha256:
        raise ClosedLoopRepairCandidateError("closed_loop_projected_state_hash_mismatch")
    packet_path = authority.workspace_file(
        workspace_root,
        packet_path,
        label="repair_execution_packet",
    )
    preview_path = authority.workspace_file(
        workspace_root,
        preview_path,
        label="materialization_preview",
    )
    response_path = authority.workspace_file(
        workspace_root,
        response_path,
        label="repair_response",
    )
    binding_record = authority.lineage_evidence_record(
        state,
        "adjudicated_repair_binding",
        workspace_root=workspace_root,
    )
    binding_path = authority.workspace_file(
        workspace_root,
        str(binding_record.get("path") or ""),
        label="adjudicated_repair_binding",
    )
    binding, _binding_bytes = _json_snapshot(
        binding_path,
        label="adjudicated_repair_binding",
    )
    if binding.get("schema") == "figure-agent.initial-attribution-binding.v2":
        raise ClosedLoopRepairCandidateError("initial_attribution_binding_v2_requires_r4_13")
    if not (
        packet_path.parent == response_path.parent == preview_path.parent == binding_path.parent
    ):
        raise ClosedLoopRepairCandidateError("repair_candidate_artifacts_must_be_binding_adjacent")
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
    if packet.get("schema") != authoring_repair_packet.SCHEMA or packet.get(
        "packet_sha256"
    ) != authoring_repair_packet.canonical_packet_sha256(packet):
        raise ClosedLoopRepairCandidateError("current_repair_packet_required")
    output_path = _safe_unmaterialized_output(
        packet,
        workspace_root=workspace_root,
    )
    try:
        expected_packet, _expected_prompt = (
            authoring_repair_packet.compile_adjudicated_repair_execution_packet(
                fixture,
                workspace_root=workspace_root,
                model_id=str(packet.get("model_id") or ""),
                binding_path=binding_path.relative_to(workspace_root).as_posix(),
                output_path=str(packet.get("output_path") or ""),
                execution_cwd=str(packet.get("execution_cwd") or ""),
            )
        )
        if packet != expected_packet:
            raise ClosedLoopRepairCandidateError("repair_packet_not_canonical_from_binding")
        authoring_repair_packet.validate_bound_packet_authority(
            packet,
            workspace_root,
        )
        authoring_repair_packet.validate_materialization_preview(
            preview,
            packet=packet,
        )
        expected_preview = authoring_repair_packet.materialize_repair_candidate(
            packet,
            response,
            workspace_root=workspace_root,
            apply=False,
        )
    except authoring_repair_packet.RepairExecutionPacketError as exc:
        label = (
            "materialization_preview_invalid"
            if "preview" in str(exc)
            else "repair_packet_authority_invalid"
        )
        raise ClosedLoopRepairCandidateError(f"{label}:{exc}") from exc
    if preview != expected_preview:
        raise ClosedLoopRepairCandidateError("materialization_preview_response_mismatch")
    if packet.get("adjudicated_repair_binding") != {
        "path": binding_record.get("path"),
        "sha256": binding_record.get("sha256"),
    }:
        raise ClosedLoopRepairCandidateError("repair_packet_state_binding_mismatch")
    return {
        "state": state,
        "state_path": published_state_path,
        "packet_path": packet_path,
        "packet_bytes": packet_bytes,
        "response_path": response_path,
        "response_bytes": response_bytes,
        "preview_path": preview_path,
        "preview_bytes": preview_bytes,
        "output_path": output_path,
        "next_state_path": published_state_path.parent
        / f"state-{state['sequence'] + 1:03d}-repair_candidate_ready.json",
    }


def _expected_candidate_state(
    plan: dict[str, Any],
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    return closed_loop_attempt_state.transition_state(
        plan["state"],
        next_state="repair_candidate_ready",
        actor="fig_run",
        actor_role="workflow_agent",
        evidence={
            "repair_execution_packet": plan["packet_path"],
            "repair_response": plan["response_path"],
            "materialization_preview": plan["preview_path"],
        },
        workspace_root=workspace_root,
        previous_state_path=plan["state_path"],
    )


def _matching_published_candidate(
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
        expected = _expected_candidate_state(plan, workspace_root=workspace_root)
    except (
        authority.ClosedLoopPostReviewError,
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        OSError,
        ValueError,
    ) as exc:
        raise ClosedLoopRepairCandidateError(f"repair_candidate_recovery_invalid:{exc}") from exc
    if published_path != next_state_path or published != expected:
        raise ClosedLoopRepairCandidateError("repair_candidate_state_conflict")
    projection = closed_loop_current_state.resolve_current_attempt(
        workspace_root,
        fixture,
    )
    if (
        projection.get("resolution") != "current"
        or projection.get("state") != "repair_candidate_ready"
        or projection.get("required_actor") != "human_repair_authorizer"
        or projection.get("terminal") is not False
        or projection.get("publication_acceptance") != "not_claimed"
        or projection.get("path") != published_path.relative_to(workspace_root).as_posix()
        or projection.get("state_sha256") != published["state_sha256"]
    ):
        raise ClosedLoopRepairCandidateError("closed_loop_canonical_current_state_drift")
    return published


def _matching_or_assert_current(
    fixture: str,
    plan: dict[str, Any],
    *,
    workspace_root: Path,
) -> dict[str, Any] | None:
    published = _matching_published_candidate(
        fixture,
        plan,
        workspace_root=workspace_root,
    )
    if published is not None:
        return published
    try:
        _assert_current_state(
            plan["state"],
            plan["state_path"],
            workspace_root=workspace_root,
        )
    except ClosedLoopRepairCandidateError as exc:
        if str(exc) != "closed_loop_canonical_current_state_drift":
            raise
        published = _matching_published_candidate(
            fixture,
            plan,
            workspace_root=workspace_root,
        )
        if published is not None:
            return published
        raise
    return None


def _result(
    plan: dict[str, Any],
    *,
    created: bool,
    published: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "action": ACTION,
        "stop_boundary": (
            STOP_HUMAN_BOUNDARY if created or published is not None else STOP_WORKFLOW_BOUNDARY
        ),
        "stop_reason": "repair_candidate_ready" if created else "plan_only",
        "required_actor": "human_repair_authorizer" if created else "workflow_agent",
        "created": created,
        "input_state": plan["state"],
        "input_state_path": plan["state_path"],
        "next_state": "repair_candidate_ready",
        "next_state_path": plan["next_state_path"],
        "packet_path": plan["packet_path"],
        "response_path": plan["response_path"],
        "preview_path": plan["preview_path"],
        "publication_acceptance": "not_claimed",
    }
    if published is not None:
        result["published_state"] = published
    return result


def run_repair_candidate(
    fixture: str,
    *,
    state_path: Path,
    packet_path: Path,
    response_path: Path,
    preview_path: Path,
    execute: bool,
    workspace_root: Path,
    expected_state_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate or publish one explicit packet, response, and exact preview."""
    root = Path(os.path.abspath(workspace_root))
    try:
        plan = _validated_plan(
            fixture,
            state_path=state_path,
            packet_path=packet_path,
            response_path=response_path,
            preview_path=preview_path,
            workspace_root=root,
            expected_state_sha256=expected_state_sha256,
        )
        published = _matching_or_assert_current(
            fixture,
            plan,
            workspace_root=root,
        )
        if published is not None:
            result = _result(plan, created=False, published=published)
            result["stop_reason"] = "repair_candidate_ready_recovered"
            result["required_actor"] = "human_repair_authorizer"
            return result
        if not execute:
            return _result(plan, created=False)

        with closed_loop_attempt_state.attempt_transition_lock(plan["state_path"].parent):
            with repair_transaction.recoverable_exclusive_lock(
                plan["output_path"].parent / ".materialization.lock",
                owner=repair_transaction.MATERIALIZATION_LOCK_OWNER,
            ):
                current = _validated_plan(
                    fixture,
                    state_path=state_path,
                    packet_path=packet_path,
                    response_path=response_path,
                    preview_path=preview_path,
                    workspace_root=root,
                    expected_state_sha256=expected_state_sha256,
                )
                published = _matching_or_assert_current(
                    fixture,
                    current,
                    workspace_root=root,
                )
                if published is not None:
                    result = _result(current, created=False, published=published)
                    result["stop_reason"] = "repair_candidate_ready_recovered"
                    result["required_actor"] = "human_repair_authorizer"
                    return result
                for key in ("packet_bytes", "response_bytes", "preview_bytes"):
                    if current[key] != plan[key]:
                        raise ClosedLoopRepairCandidateError("repair_candidate_inputs_drifted")
                next_state = _expected_candidate_state(
                    current,
                    workspace_root=root,
                )
                next_state_path = closed_loop_attempt_state.publish_state(
                    next_state,
                    workspace_root=root,
                )
        current["next_state_path"] = next_state_path
        return _result(current, created=True, published=next_state)
    except ClosedLoopRepairCandidateError:
        raise
    except (
        authority.ClosedLoopPostReviewError,
        authoring_repair_packet.RepairExecutionPacketError,
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        repair_transaction.RepairTransactionError,
        OSError,
        ValueError,
    ) as exc:
        raise ClosedLoopRepairCandidateError(f"repair_candidate_failed:{exc}") from exc
