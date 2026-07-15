"""Inbound external host-review response for one closed-loop attempt."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import closed_loop_post_review_authority as authority
import post_repair_visual_review
import repair_transaction

ClosedLoopPostReviewError = authority.ClosedLoopPostReviewError

ACTION = "post_repair_visual_review_response"
HUMAN_BOUNDARY = "human_reviewer"
REPAIR_BOUNDARY = "repair_required"


def _attempt_file(root: Path, attempt_root: Path, value: Path | str, *, label: str) -> Path:
    path = authority.workspace_file(root, value, label=label)
    try:
        path.relative_to(attempt_root)
    except ValueError as exc:
        raise ClosedLoopPostReviewError(f"{label}_attempt_mismatch") from exc
    return path


def _load_snapshot(path: Path, *, label: str) -> tuple[dict[str, Any], bytes, tuple[int, ...]]:
    try:
        before = authority.stat_fingerprint(path)
        data = path.read_bytes()
        after = authority.stat_fingerprint(path)
        payload = json.loads(data.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopPostReviewError(f"{label}_json_invalid") from exc
    if before != after:
        raise ClosedLoopPostReviewError(f"{label}_changed_during_snapshot")
    if not isinstance(payload, dict):
        raise ClosedLoopPostReviewError(f"{label}_payload_invalid")
    return payload, data, after


def _validate_request(
    *,
    root: Path,
    fixture: str,
    attempt_root: Path,
    state: dict[str, Any],
) -> tuple[dict[str, Any], Path, bytes, tuple[int, ...]]:
    evidence = authority.evidence_by_role(state)
    record = evidence.get("post_repair_visual_review_request")
    if not isinstance(record, dict):
        raise ClosedLoopPostReviewError("post_review_request_evidence_missing")
    request_path = _attempt_file(
        root,
        attempt_root,
        str(record.get("path") or ""),
        label="post_review_request",
    )
    request, request_bytes, fingerprint = _load_snapshot(
        request_path, label="post_review_request"
    )
    if record.get("sha256") != authority.sha256_bytes(request_bytes):
        raise ClosedLoopPostReviewError("post_review_request_evidence_stale")
    try:
        post_repair_visual_review._validate_request_freshness(
            request, workspace_root=root
        )
    except post_repair_visual_review.PostRepairVisualReviewError as exc:
        raise ClosedLoopPostReviewError(f"post_review_request_invalid:{exc}") from exc
    if (
        request.get("fixture") != fixture
        or request.get("publication_acceptance") != "not_claimed"
    ):
        raise ClosedLoopPostReviewError("post_review_request_fixture_mismatch")
    authority.validate_request_against_machine_state(
        request, state, workspace_root=root
    )
    return request, request_path, request_bytes, fingerprint


def _validate_response(
    *,
    root: Path,
    attempt_root: Path,
    response_path: Path,
    request: dict[str, Any],
) -> tuple[dict[str, Any], bytes, tuple[int, ...], dict[str, Any]]:
    response_path = _attempt_file(
        root, attempt_root, response_path, label="response"
    )
    response, response_bytes, fingerprint = _load_snapshot(
        response_path, label="response"
    )
    execution = response.get("execution_receipt")
    if isinstance(execution, dict):
        transcript = execution.get("transcript")
        if isinstance(transcript, dict):
            _attempt_file(
                root,
                attempt_root,
                str(transcript.get("path") or ""),
                label="host_review_transcript",
            )
    try:
        receipt = post_repair_visual_review.finalize_review_payload(
            request, response, workspace_root=root
        )
    except post_repair_visual_review.PostRepairVisualReviewError as exc:
        raise ClosedLoopPostReviewError(f"post_review_response_invalid:{exc}") from exc
    receipt = {
        **receipt,
        "response": {
            "path": response_path.relative_to(root).as_posix(),
            "sha256": authority.sha256_bytes(response_bytes),
        },
    }
    receipt["receipt_sha256"] = post_repair_visual_review._canonical_hash(
        receipt, omitted="receipt_sha256"
    )
    return response, response_bytes, fingerprint, receipt


def _revalidate_exact_inputs(
    *,
    root: Path,
    fixture: str,
    attempt_root: Path,
    state: dict[str, Any],
    request_path: Path,
    request_bytes: bytes,
    request_fingerprint: tuple[int, ...],
    response_path: Path,
    response_bytes: bytes,
    response_fingerprint: tuple[int, ...],
    receipt: dict[str, Any],
) -> dict[str, Any]:
    (
        current_request,
        current_request_path,
        current_request_bytes,
        current_request_fingerprint,
    ) = _validate_request(
        root=root,
        fixture=fixture,
        attempt_root=attempt_root,
        state=state,
    )
    (
        current_response,
        current_response_bytes,
        current_response_fingerprint,
        current_receipt,
    ) = _validate_response(
        root=root,
        attempt_root=attempt_root,
        response_path=response_path,
        request=current_request,
    )
    if (
        current_request_path != request_path
        or current_request_bytes != request_bytes
        or current_request_fingerprint != request_fingerprint
        or current_response_bytes != response_bytes
        or current_response_fingerprint != response_fingerprint
        or current_receipt != receipt
    ):
        raise ClosedLoopPostReviewError("post_review_inputs_drift_detected")
    return current_response


def _external_actor(response: dict[str, Any]) -> str:
    execution = response.get("execution_receipt")
    actor = execution.get("actor") if isinstance(execution, dict) else None
    if not isinstance(actor, dict):
        raise ClosedLoopPostReviewError("host_review_actor_missing")
    return ":".join(
        (
            str(actor["kind"]),
            str(actor["identity"]),
            str(actor["model_or_tool"]),
        )
    )


def _existing_or_publish_receipt(path: Path, expected: dict[str, Any]) -> bool:
    if path.is_symlink():
        raise ClosedLoopPostReviewError("review_receipt_symlink")
    if path.exists():
        if not path.is_file():
            raise ClosedLoopPostReviewError("review_receipt_conflict")
        if authority.load_json(path, label="review_receipt") != expected:
            raise ClosedLoopPostReviewError("review_receipt_mismatch")
        return False
    try:
        repair_transaction.atomic_create_json(path, expected)
    except FileExistsError as exc:
        raise ClosedLoopPostReviewError("review_receipt_conflict") from exc
    return True


def _validate_receipt_if_present(path: Path, expected: dict[str, Any]) -> None:
    if path.is_symlink():
        raise ClosedLoopPostReviewError("review_receipt_symlink")
    if not path.exists():
        return
    if not path.is_file():
        raise ClosedLoopPostReviewError("review_receipt_conflict")
    if authority.load_json(path, label="review_receipt") != expected:
        raise ClosedLoopPostReviewError("review_receipt_mismatch")


def _existing_or_publish_state(
    state: dict[str, Any], *, workspace_root: Path
) -> tuple[Path, bool]:
    path = closed_loop_attempt_state.state_path(
        state, workspace_root=workspace_root
    )
    if path.is_symlink():
        raise ClosedLoopPostReviewError("post_review_state_symlink")
    if path.exists():
        if authority.load_json(path, label="post_review_state") != state:
            raise ClosedLoopPostReviewError("post_review_state_mismatch")
        try:
            closed_loop_attempt_state.validate_state(
                state, workspace_root=workspace_root
            )
        except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
            raise ClosedLoopPostReviewError(f"post_review_state_invalid:{exc}") from exc
        return path, False
    try:
        return (
            closed_loop_attempt_state.publish_state(
                state, workspace_root=workspace_root
            ),
            True,
        )
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise ClosedLoopPostReviewError(
            f"post_review_state_publication_failed:{exc}"
        ) from exc


def run_inbound_response(
    fixture: str,
    *,
    state_path: Path,
    response_path: Path,
    execute: bool,
    workspace_root: Path,
) -> dict[str, Any]:
    """Validate an external response and optionally publish the next state."""
    root = Path(os.path.abspath(workspace_root))
    state, published_state_path = authority.load_published_state(
        workspace_root=root,
        fixture=fixture,
        state_path=state_path,
    )
    if state["state"] != "post_review_requested":
        raise ClosedLoopPostReviewError("closed_loop_state_not_post_review_requested")
    attempt_root = published_state_path.parent
    response_path = _attempt_file(
        root, attempt_root, response_path, label="response"
    )
    request, request_path, request_bytes, request_fingerprint = _validate_request(
        root=root,
        fixture=fixture,
        attempt_root=attempt_root,
        state=state,
    )
    response, response_bytes, response_fingerprint, receipt = _validate_response(
        root=root,
        attempt_root=attempt_root,
        response_path=response_path,
        request=request,
    )
    decision = str(receipt["decision"])
    receipt_path = attempt_root / "post-repair-review" / "review-receipt.json"
    if decision == "human_review_required":
        if receipt_path.exists() or receipt_path.is_symlink():
            raise ClosedLoopPostReviewError("human_review_output_conflict")
        return {
            "action": ACTION,
            "stop_boundary": HUMAN_BOUNDARY,
            "stop_reason": "human_review_boundary" if execute else "plan_only",
            "required_actor": "human_reviewer",
            "created": False,
            "decision": decision,
            "input_state": state,
            "input_state_path": published_state_path,
            "next_state": "post_review_requested",
            "next_state_path": published_state_path,
            "request_path": request_path,
            "response_path": response_path,
            "receipt_path": receipt_path,
            "published_state": state,
        }
    next_state_name = (
        "repair_required"
        if decision == "repair_required"
        else "visually_re_reviewed"
    )
    stop_boundary = (
        REPAIR_BOUNDARY if next_state_name == "repair_required" else HUMAN_BOUNDARY
    )
    if not execute:
        _validate_receipt_if_present(receipt_path, receipt)
        return {
            "action": ACTION,
            "stop_boundary": stop_boundary,
            "stop_reason": "plan_only",
            "required_actor": (
                "none" if next_state_name == "repair_required" else "human_reviewer"
            ),
            "created": False,
            "decision": decision,
            "input_state": state,
            "input_state_path": published_state_path,
            "next_state": next_state_name,
            "next_state_path": attempt_root
            / f"state-{state['sequence'] + 1:03d}-{next_state_name}.json",
            "request_path": request_path,
            "response_path": response_path,
            "receipt_path": receipt_path,
            "published_state": None,
        }

    try:
        with repair_transaction.exclusive_lock(
            attempt_root / ".closed-loop-post-review-response.lock",
            owner="closed_loop_post_review_response",
        ):
            current_state, current_state_path = authority.load_published_state(
                workspace_root=root,
                fixture=fixture,
                state_path=published_state_path,
            )
            if current_state != state or current_state_path != published_state_path:
                raise ClosedLoopPostReviewError("post_review_state_drift_detected")
            current_response = _revalidate_exact_inputs(
                root=root,
                fixture=fixture,
                attempt_root=attempt_root,
                state=current_state,
                request_path=request_path,
                request_bytes=request_bytes,
                request_fingerprint=request_fingerprint,
                response_path=response_path,
                response_bytes=response_bytes,
                response_fingerprint=response_fingerprint,
                receipt=receipt,
            )
            if current_response != response:
                raise ClosedLoopPostReviewError("post_review_response_drift_detected")
            receipt_created = _existing_or_publish_receipt(receipt_path, receipt)
            current_response = _revalidate_exact_inputs(
                root=root,
                fixture=fixture,
                attempt_root=attempt_root,
                state=current_state,
                request_path=request_path,
                request_bytes=request_bytes,
                request_fingerprint=request_fingerprint,
                response_path=response_path,
                response_bytes=response_bytes,
                response_fingerprint=response_fingerprint,
                receipt=receipt,
            )
            evidence = (
                {"repair_failure_record": receipt_path}
                if next_state_name == "repair_required"
                else {
                    "post_repair_visual_review_response": response_path,
                    "host_review_execution_receipt": response_path,
                    "post_repair_visual_review_receipt": receipt_path,
                }
            )
            next_state = closed_loop_attempt_state.transition_state(
                state,
                next_state=next_state_name,
                actor=_external_actor(current_response),
                actor_role="host_llm",
                evidence=evidence,
                workspace_root=root,
                previous_state_path=published_state_path,
            )
            next_state_path, state_created = _existing_or_publish_state(
                next_state, workspace_root=root
            )
            try:
                _revalidate_exact_inputs(
                    root=root,
                    fixture=fixture,
                    attempt_root=attempt_root,
                    state=current_state,
                    request_path=request_path,
                    request_bytes=request_bytes,
                    request_fingerprint=request_fingerprint,
                    response_path=response_path,
                    response_bytes=response_bytes,
                    response_fingerprint=response_fingerprint,
                    receipt=receipt,
                )
            except ClosedLoopPostReviewError as exc:
                raise ClosedLoopPostReviewError(
                    "post_review_state_published_but_stale:"
                    f"{next_state_path.relative_to(root).as_posix()}:{exc}"
                ) from exc
    except (
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        repair_transaction.RepairTransactionError,
        OSError,
        ValueError,
    ) as exc:
        if isinstance(exc, ClosedLoopPostReviewError):
            raise
        raise ClosedLoopPostReviewError(
            f"post_review_response_publication_failed:{exc}"
        ) from exc
    return {
        "action": ACTION,
        "stop_boundary": stop_boundary,
        "stop_reason": (
            "repair_required"
            if next_state_name == "repair_required"
            else "human_review_boundary"
        ),
        "required_actor": (
            "none" if next_state_name == "repair_required" else "human_reviewer"
        ),
        "created": receipt_created or state_created,
        "decision": decision,
        "input_state": state,
        "input_state_path": published_state_path,
        "next_state": next_state_name,
        "next_state_path": next_state_path,
        "request_path": request_path,
        "response_path": response_path,
        "receipt_path": receipt_path,
        "published_state": next_state,
    }
