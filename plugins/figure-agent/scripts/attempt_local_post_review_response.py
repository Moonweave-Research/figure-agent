"""Bind one v2 attempt-local post-repair review response."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import attempt_local_post_review
import closed_loop_attempt_state
import closed_loop_current_state
import closed_loop_post_review_authority as authority
import repair_transaction

RESPONSE_SCHEMA = "figure-agent.attempt-local-post-repair-review-response.v2"
RECEIPT_SCHEMA = "figure-agent.attempt-local-post-repair-review-receipt.v2"
EXECUTION_RECEIPT_SCHEMA = "figure-agent.attempt-local-host-review-execution-receipt.v2"
ACTION = "attempt_local_post_repair_visual_review_response"
REQUIRED_VERDICTS = {
    "target_resolved": frozenset({"resolved", "still_present", "uncertain"}),
    "no_new_local_defect": frozenset({"pass", "fail", "uncertain"}),
    "unchanged_region_regression": frozenset({"none", "present", "uncertain"}),
}


class AttemptLocalPostReviewResponseError(ValueError):
    """Raised when a v2 response cannot be safely bound."""


def canonical_hash(payload: dict[str, Any], *, omitted: str) -> str:
    canonical = {key: value for key, value in payload.items() if key != omitted}
    encoded = json.dumps(
        canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _attempt_file(root: Path, attempt_root: Path, value: Path | str, *, label: str) -> Path:
    path = authority.workspace_file(root, value, label=label)
    try:
        path.relative_to(attempt_root)
    except ValueError as exc:
        raise AttemptLocalPostReviewResponseError(f"{label}_attempt_mismatch") from exc
    return path


def _snapshot(path: Path, *, label: str) -> tuple[dict[str, Any], bytes, tuple[int, ...]]:
    try:
        before = authority.stat_fingerprint(path)
        data = path.read_bytes()
        after = authority.stat_fingerprint(path)
        payload = json.loads(data.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AttemptLocalPostReviewResponseError(f"{label}_json_invalid") from exc
    if before != after:
        raise AttemptLocalPostReviewResponseError(f"{label}_changed_during_snapshot")
    if not isinstance(payload, dict):
        raise AttemptLocalPostReviewResponseError(f"{label}_payload_invalid")
    return payload, data, after


def _request_inspections(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "before_render": request["before_render"],
        "after_render": request["after_render"],
        "materialized_output": request["materialized_output"],
        "materialization_receipt": request["materialization_receipt"],
        "initial_crops": request["initial_crops"],
        "after_crop_manifest": request["after_crop_manifest"],
        "after_crops": request["after_crops"],
    }


def _validate_request(
    root: Path, fixture: str, attempt_root: Path, state: dict[str, Any]
) -> tuple[dict[str, Any], Path, bytes, tuple[int, ...]]:
    record = authority.evidence_by_role(state).get("post_repair_visual_review_request")
    if not isinstance(record, dict):
        raise AttemptLocalPostReviewResponseError("post_review_request_evidence_missing")
    path = _attempt_file(root, attempt_root, str(record.get("path") or ""), label="request")
    request, data, fingerprint = _snapshot(path, label="request")
    if record.get("sha256") != authority.sha256_bytes(data):
        raise AttemptLocalPostReviewResponseError("post_review_request_evidence_drift")
    try:
        attempt_local_post_review.validate_request(request, root=root, fixture=fixture)
    except (attempt_local_post_review.AttemptLocalPostReviewError, OSError, ValueError) as exc:
        raise AttemptLocalPostReviewResponseError(f"post_review_request_invalid:{exc}") from exc
    return request, path, data, fingerprint


def _validate_execution(
    execution: object,
    *,
    request: dict[str, Any],
    inspections: dict[str, Any],
    root: Path,
    attempt_root: Path,
) -> bool:
    if execution is None:
        return False
    if not isinstance(execution, dict):
        raise AttemptLocalPostReviewResponseError("execution_receipt_invalid")
    actor = execution.get("actor")
    if (
        execution.get("schema") != EXECUTION_RECEIPT_SCHEMA
        or execution.get("request_sha256") != request.get("request_sha256")
        or execution.get("inspected_artifacts") != inspections
        or not isinstance(actor, dict)
        or actor.get("kind") not in {"human", "model", "tool"}
        or not isinstance(actor.get("identity"), str)
        or not actor["identity"].strip()
        or not isinstance(actor.get("model_or_tool"), str)
        or not actor["model_or_tool"].strip()
        or execution.get("receipt_sha256")
        != canonical_hash(execution, omitted="receipt_sha256")
    ):
        raise AttemptLocalPostReviewResponseError("execution_receipt_invalid")
    transcript = execution.get("transcript")
    if not isinstance(transcript, dict) or set(transcript) != {"path", "sha256"}:
        raise AttemptLocalPostReviewResponseError("execution_transcript_invalid")
    transcript_path = _attempt_file(
        root, attempt_root, str(transcript.get("path") or ""), label="execution_transcript"
    )
    if transcript.get("sha256") != authority.sha256_bytes(transcript_path.read_bytes()):
        raise AttemptLocalPostReviewResponseError("execution_transcript_hash_drift")
    return True


def _validate_response(
    *,
    root: Path,
    fixture: str,
    attempt_root: Path,
    response_path: Path,
    request: dict[str, Any],
) -> tuple[dict[str, Any], bytes, tuple[int, ...], dict[str, Any]]:
    response_path = _attempt_file(root, attempt_root, response_path, label="response")
    response, data, fingerprint = _snapshot(response_path, label="response")
    verdicts = response.get("verdicts")
    findings = response.get("findings")
    reviewer = response.get("reviewer")
    inspections = _request_inspections(request)
    if (
        response.get("schema") != RESPONSE_SCHEMA
        or response.get("request_sha256") != request.get("request_sha256")
        or response.get("publication_acceptance") != "not_claimed"
        or not isinstance(reviewer, str)
        or not reviewer.strip()
        or not isinstance(verdicts, dict)
        or set(verdicts) != set(REQUIRED_VERDICTS)
        or any(verdicts.get(key) not in allowed for key, allowed in REQUIRED_VERDICTS.items())
        or not isinstance(findings, list)
        or any(not isinstance(item, dict) for item in findings)
        or response.get("inspected_artifacts") != inspections
    ):
        raise AttemptLocalPostReviewResponseError("post_review_response_invalid")
    has_execution = _validate_execution(
        response.get("execution_receipt"),
        request=request,
        inspections=inspections,
        root=root,
        attempt_root=attempt_root,
    )
    if not has_execution or "uncertain" in verdicts.values():
        decision = "human_review_required"
    elif (
        verdicts["target_resolved"] == "still_present"
        or verdicts["no_new_local_defect"] == "fail"
        or verdicts["unchanged_region_regression"] == "present"
    ):
        decision = "repair_required"
    else:
        decision = "visually_rechecked_human_review_pending"
    receipt: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "fixture": fixture,
        "request_sha256": request["request_sha256"],
        "response": {
            "path": response_path.relative_to(root).as_posix(),
            "sha256": authority.sha256_bytes(data),
        },
        "reviewer": reviewer.strip(),
        "verdicts": verdicts,
        "findings": findings,
        "execution_receipt": response.get("execution_receipt"),
        "decision": decision,
        "publication_acceptance": "not_claimed",
    }
    receipt["receipt_sha256"] = canonical_hash(receipt, omitted="receipt_sha256")
    return response, data, fingerprint, receipt


def _actor(response: dict[str, Any]) -> str:
    execution = response["execution_receipt"]
    actor = execution["actor"]
    return ":".join((actor["kind"], actor["identity"], actor["model_or_tool"]))


def _canonical_current(root: Path, fixture: str, state: dict[str, Any], path: Path) -> None:
    current = closed_loop_current_state.resolve_current_attempt(root, fixture)
    if (
        current.get("resolution") != "current"
        or current.get("path") != path.relative_to(root).as_posix()
        or current.get("state_sha256") != state.get("state_sha256")
        or current.get("publication_acceptance") != "not_claimed"
    ):
        raise AttemptLocalPostReviewResponseError("canonical_current_state_drift")


def _same_snapshot(path: Path, data: bytes, fingerprint: tuple[int, ...], *, label: str) -> None:
    try:
        current_fingerprint = authority.stat_fingerprint(path)
        current_data = path.read_bytes()
    except OSError as exc:
        raise AttemptLocalPostReviewResponseError(f"{label}_drift") from exc
    if current_fingerprint != fingerprint or current_data != data:
        raise AttemptLocalPostReviewResponseError(f"{label}_drift")


def _revalidate_exact_inputs(
    *,
    root: Path,
    fixture: str,
    attempt_root: Path,
    request: dict[str, Any],
    request_path: Path,
    request_data: bytes,
    request_fingerprint: tuple[int, ...],
    response: dict[str, Any],
    response_path: Path,
    response_data: bytes,
    response_fingerprint: tuple[int, ...],
    receipt: dict[str, Any],
) -> None:
    _same_snapshot(request_path, request_data, request_fingerprint, label="request")
    _same_snapshot(response_path, response_data, response_fingerprint, label="response")
    attempt_local_post_review.validate_request(request, root=root, fixture=fixture)
    current_response, current_data, current_fingerprint, current_receipt = _validate_response(
        root=root,
        fixture=fixture,
        attempt_root=attempt_root,
        response_path=response_path,
        request=request,
    )
    if (
        current_response != response
        or current_data != response_data
        or current_fingerprint != response_fingerprint
        or current_receipt != receipt
    ):
        raise AttemptLocalPostReviewResponseError("post_review_inputs_drift")


def _publish_receipt(path: Path, receipt: dict[str, Any]) -> bool:
    if path.is_symlink():
        raise AttemptLocalPostReviewResponseError("review_receipt_symlink")
    if path.exists():
        if not path.is_file() or authority.load_json(path, label="review_receipt") != receipt:
            raise AttemptLocalPostReviewResponseError("review_receipt_conflict")
        return False
    try:
        repair_transaction.atomic_create_json(path, receipt)
    except FileExistsError as exc:
        raise AttemptLocalPostReviewResponseError("review_receipt_conflict") from exc
    return True


def run_inbound_response(
    fixture: str,
    *,
    state_path: Path,
    response_path: Path,
    execute: bool,
    workspace_root: Path,
    expected_state_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate v2 host evidence and optionally publish exactly one next state."""
    root = Path(os.path.abspath(workspace_root))
    state, published_path = authority.load_published_state(
        workspace_root=root, fixture=fixture, state_path=state_path
    )
    if state.get("state") != "post_review_requested":
        raise AttemptLocalPostReviewResponseError("post_review_requested_state_required")
    if expected_state_sha256 is not None and state.get("state_sha256") != expected_state_sha256:
        raise AttemptLocalPostReviewResponseError("projected_state_hash_mismatch")
    attempt_root = published_path.parent
    request, request_path, request_data, request_fingerprint = _validate_request(
        root, fixture, attempt_root, state
    )
    response_path = _attempt_file(root, attempt_root, response_path, label="response")
    response, response_data, response_fingerprint, receipt = _validate_response(
        root=root,
        fixture=fixture,
        attempt_root=attempt_root,
        response_path=response_path,
        request=request,
    )
    decision = receipt["decision"]
    receipt_path = attempt_root / "attempt-local-post-repair-review" / "review-receipt.json"
    if decision == "human_review_required":
        if receipt_path.exists() or receipt_path.is_symlink():
            raise AttemptLocalPostReviewResponseError("human_review_output_conflict")
        _canonical_current(root, fixture, state, published_path)
        return {
            "action": ACTION,
            "created": False,
            "decision": decision,
            "next_state": "post_review_requested",
            "next_state_path": published_path,
            "required_actor": "human_reviewer",
            "stop_boundary": "human_reviewer",
            "stop_reason": "human_review_boundary" if execute else "plan_only",
            "receipt_path": receipt_path,
            "published_state": state,
        }
    next_state_name = (
        "repair_required" if decision == "repair_required" else "visually_re_reviewed"
    )
    next_path = attempt_root / f"state-{state['sequence'] + 1:03d}-{next_state_name}.json"
    if not execute:
        _canonical_current(root, fixture, state, published_path)
        if (
            receipt_path.exists()
            or receipt_path.is_symlink()
            or next_path.exists()
            or next_path.is_symlink()
        ):
            raise AttemptLocalPostReviewResponseError("post_review_output_conflict")
        return {
            "action": ACTION,
            "created": False,
            "decision": decision,
            "next_state": next_state_name,
            "next_state_path": next_path,
            "required_actor": "none" if next_state_name == "repair_required" else "human_reviewer",
            "stop_reason": "plan_only",
            "receipt_path": receipt_path,
            "published_state": None,
        }
    try:
        with closed_loop_attempt_state.attempt_transition_lock(attempt_root):
            if next_path.exists() or next_path.is_symlink():
                recovered, recovered_path = authority.load_published_state(
                    workspace_root=root, fixture=fixture, state_path=next_path
                )
                _canonical_current(root, fixture, recovered, recovered_path)
                if recovered.get("state") != next_state_name:
                    raise AttemptLocalPostReviewResponseError("recovered_state_mismatch")
                receipt_created = _publish_receipt(receipt_path, receipt)
                state_created = False
            else:
                _canonical_current(root, fixture, state, published_path)
                current_state, current_path = authority.load_published_state(
                    workspace_root=root, fixture=fixture, state_path=published_path
                )
                if current_state != state or current_path != published_path:
                    raise AttemptLocalPostReviewResponseError("input_state_drift")
                current_request, _, current_request_data, current_request_fp = _validate_request(
                    root, fixture, attempt_root, current_state
                )
                current_response, current_response_data, current_response_fp, current_receipt = (
                    _validate_response(
                        root=root,
                        fixture=fixture,
                        attempt_root=attempt_root,
                        response_path=response_path,
                        request=current_request,
                    )
                )
                if (
                    current_request != request
                    or current_request_data != request_data
                    or current_request_fp != request_fingerprint
                    or current_response != response
                    or current_response_data != response_data
                    or current_response_fp != response_fingerprint
                    or current_receipt != receipt
                ):
                    raise AttemptLocalPostReviewResponseError("post_review_inputs_drift")
                receipt_created = _publish_receipt(receipt_path, receipt)
                _revalidate_exact_inputs(
                    root=root,
                    fixture=fixture,
                    attempt_root=attempt_root,
                    request=request,
                    request_path=request_path,
                    request_data=request_data,
                    request_fingerprint=request_fingerprint,
                    response=response,
                    response_path=response_path,
                    response_data=response_data,
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
                    actor=_actor(response),
                    actor_role="host_llm",
                    evidence=evidence,
                    workspace_root=root,
                    previous_state_path=published_path,
                )
                _revalidate_exact_inputs(
                    root=root,
                    fixture=fixture,
                    attempt_root=attempt_root,
                    request=request,
                    request_path=request_path,
                    request_data=request_data,
                    request_fingerprint=request_fingerprint,
                    response=response,
                    response_path=response_path,
                    response_data=response_data,
                    response_fingerprint=response_fingerprint,
                    receipt=receipt,
                )
                published = closed_loop_attempt_state.publish_state(next_state, workspace_root=root)
                if published != next_path:
                    raise AttemptLocalPostReviewResponseError("post_review_state_path_mismatch")
                recovered = next_state
                state_created = True
            return {
                "action": ACTION,
                "created": state_created or receipt_created,
                "decision": decision,
                "next_state": next_state_name,
                "next_state_path": next_path,
                "required_actor": (
                    "none" if next_state_name == "repair_required" else "human_reviewer"
                ),
                "stop_boundary": (
                    "repair_required"
                    if next_state_name == "repair_required"
                    else "human_reviewer"
                ),
                "stop_reason": next_state_name,
                "receipt_path": receipt_path,
                "published_state": recovered,
            }
    except (
        attempt_local_post_review.AttemptLocalPostReviewError,
        authority.ClosedLoopPostReviewError,
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        repair_transaction.RepairTransactionError,
        OSError,
        ValueError,
    ) as exc:
        if isinstance(exc, AttemptLocalPostReviewResponseError):
            raise
        raise AttemptLocalPostReviewResponseError(
            f"post_review_response_publication_failed:{exc}"
        ) from exc
