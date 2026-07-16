"""Accept a supplied initial visual-review response without invoking a host.

This is deliberately a narrow inbound boundary.  The caller supplies a
complete, hash-bound response pack; this module validates it against the
current outbound request and publishes only ``critique_unadjudicated``.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import closed_loop_current_state
import closed_loop_initial_review
import critique_adjudication
import critique_contract
import post_repair_visual_review
import repair_transaction

SCHEMA = "figure-agent.initial-visual-review-response.v1"
ACTION = "initial_visual_review_response"
STOP_BOUNDARY = "human_adjudicator"
RESPONSE_PACK = "initial-review-response"
RESPONSE_FILE = "response.json"
CRITIQUE_FILE = "critique.md"
HOST_RECEIPT_FILE = "host-review-execution-receipt.json"
TRANSCRIPT_FILE = "host-review-transcript.md"
EXPECTED_CROP_IDS = (
    "full_q1",
    "full_q2",
    "full_q3",
    "full_q4",
    "print_178mm",
    "print_thumbnail",
)


class ClosedLoopInitialReviewResponseError(ValueError):
    """Raised when supplied initial-review evidence is not current and bound."""


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_hash(payload: dict[str, Any], *, omitted: str) -> str:
    canonical = {key: value for key, value in payload.items() if key != omitted}
    return _sha256_bytes(
        json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    )


def _load_state(root: Path, fixture: str, state_path: Path) -> tuple[dict[str, Any], Path]:
    try:
        state, path = closed_loop_initial_review._load_published_state(  # noqa: SLF001
            workspace_root=root, fixture=fixture, state_path=state_path
        )
    except closed_loop_initial_review.ClosedLoopInitialReviewError as exc:
        raise ClosedLoopInitialReviewResponseError(str(exc)) from exc
    return state, path


def _assert_current(root: Path, fixture: str, state: dict[str, Any], path: Path) -> None:
    current = closed_loop_current_state.resolve_current_attempt(root, fixture)
    if current.get("resolution") != "current":
        raise ClosedLoopInitialReviewResponseError(
            f"initial_review_response_current_resolution:{current.get('resolution')}"
        )
    if (
        current.get("path") != path.relative_to(root).as_posix()
        or current.get("state_sha256") != state["state_sha256"]
    ):
        raise ClosedLoopInitialReviewResponseError("initial_review_response_current_state_mismatch")


def _regular(path: Path, *, root: Path, label: str) -> Path:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ClosedLoopInitialReviewResponseError(f"{label}_outside_workspace") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ClosedLoopInitialReviewResponseError(f"{label}_symlink")
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        raise ClosedLoopInitialReviewResponseError(f"{label}_missing") from exc
    if not stat.S_ISREG(mode):
        raise ClosedLoopInitialReviewResponseError(f"{label}_not_regular")
    return path


def _load_json(
    path: Path, *, root: Path, label: str
) -> tuple[dict[str, Any], bytes, tuple[int, ...]]:
    _regular(path, root=root, label=label)
    try:
        before = path.stat()
        data = path.read_bytes()
        after = path.stat()
        payload = json.loads(data.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopInitialReviewResponseError(f"{label}_json_invalid") from exc
    fingerprint = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    ) != fingerprint:
        raise ClosedLoopInitialReviewResponseError(f"{label}_changed_during_snapshot")
    if not isinstance(payload, dict):
        raise ClosedLoopInitialReviewResponseError(f"{label}_payload_invalid")
    return payload, data, fingerprint


def _artifact(path: Path, sha256: str, *, root: Path, role: str) -> dict[str, str]:
    return {"role": role, "path": path.relative_to(root).as_posix(), "sha256": sha256}


def _validate_outbound(
    *, root: Path, fixture: str, state: dict[str, Any], state_path: Path
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    if state["state"] != "initial_review_requested":
        raise ClosedLoopInitialReviewResponseError("closed_loop_state_not_initial_review_requested")
    try:
        request_path, manifest_path, request = (
            closed_loop_initial_review.validate_outbound_request_pack(
                state=state, state_path=state_path, workspace_root=root
            )
        )
    except closed_loop_initial_review.ClosedLoopInitialReviewError as exc:
        raise ClosedLoopInitialReviewResponseError(f"initial_review_request_invalid:{exc}") from exc
    if request_path.parent.name != "initial-review" or request.get("fixture") != fixture:
        raise ClosedLoopInitialReviewResponseError("initial_review_request_fixture_mismatch")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopInitialReviewResponseError("initial_review_crop_manifest_invalid") from exc
    crops = manifest.get("crops") if isinstance(manifest, dict) else None
    if not isinstance(crops, list):
        raise ClosedLoopInitialReviewResponseError("initial_review_crop_manifest_invalid")
    by_id = {item.get("id"): item for item in crops if isinstance(item, dict)}
    if set(by_id) != set(EXPECTED_CROP_IDS):
        raise ClosedLoopInitialReviewResponseError("initial_review_required_crops_missing")
    render = request.get("render")
    if (
        not isinstance(render, dict)
        or not isinstance(render.get("path"), str)
        or not isinstance(render.get("sha256"), str)
    ):
        raise ClosedLoopInitialReviewResponseError("initial_review_render_invalid")
    render_path = _regular(root / render["path"], root=root, label="initial_review_render")
    if _sha256(render_path) != render["sha256"]:
        raise ClosedLoopInitialReviewResponseError("initial_review_render_hash_stale")
    artifacts = [_artifact(render_path, render["sha256"], root=root, role="full_render")]
    for crop_id in EXPECTED_CROP_IDS:
        crop = by_id[crop_id]
        path_value, sha = crop.get("path"), crop.get("sha256")
        if not isinstance(path_value, str) or not isinstance(sha, str):
            raise ClosedLoopInitialReviewResponseError("initial_review_crop_record_invalid")
        crop_path = _regular(
            root / "examples" / fixture / path_value,
            root=root,
            label=f"initial_review_crop_{crop_id}",
        )
        if _sha256(crop_path) != sha:
            raise ClosedLoopInitialReviewResponseError("initial_review_crop_hash_stale")
        artifacts.append(_artifact(crop_path, sha, root=root, role=crop_id))
    return request, artifacts


def _response_pack(attempt_root: Path, response_path: Path, *, root: Path) -> dict[str, Path]:
    pack = attempt_root / RESPONSE_PACK
    expected = {
        "response": pack / RESPONSE_FILE,
        "critique": pack / CRITIQUE_FILE,
        "host": pack / HOST_RECEIPT_FILE,
        "transcript": pack / TRANSCRIPT_FILE,
    }
    if response_path != expected["response"]:
        raise ClosedLoopInitialReviewResponseError("initial_review_response_path_outside_attempt")
    if pack.is_symlink() or not pack.is_dir():
        raise ClosedLoopInitialReviewResponseError("initial_review_response_pack_missing")
    try:
        names = {item.name for item in pack.iterdir()}
    except OSError as exc:
        raise ClosedLoopInitialReviewResponseError("initial_review_response_pack_missing") from exc
    if names != {path.name for path in expected.values()}:
        raise ClosedLoopInitialReviewResponseError("initial_review_response_pack_layout_invalid")
    for label, path in expected.items():
        _regular(path, root=root, label=f"initial_review_{label}")
    return expected


def _validate_critique(path: Path, *, fixture: str, root: Path) -> None:
    _regular(path, root=root, label="initial_review_critique")
    try:
        frontmatter = critique_contract.load_critique_frontmatter(path)
        critique_adjudication.validate_critique_schema(frontmatter)  # type: ignore[attr-defined]
        findings = critique_contract.critique_findings(frontmatter)
        identifiers = [
            critique_contract.critique_finding_id(item, "initial critique finding")
            for item in findings
        ]
    except (critique_contract.CritiqueContractError, ValueError) as exc:
        raise ClosedLoopInitialReviewResponseError("initial_review_critique_invalid") from exc
    if frontmatter.get("fixture") != fixture or len(identifiers) != len(set(identifiers)):
        raise ClosedLoopInitialReviewResponseError("initial_review_critique_invalid")


def _validate_response(
    *,
    root: Path,
    fixture: str,
    attempt_root: Path,
    response_path: Path,
    request: dict[str, Any],
    artifacts: list[dict[str, str]],
) -> tuple[dict[str, Any], bytes, tuple[int, ...], Path, Path]:
    paths = _response_pack(attempt_root, response_path, root=root)
    response, response_bytes, fingerprint = _load_json(
        paths["response"], root=root, label="initial_review_response"
    )
    expected_keys = {
        "schema",
        "fixture",
        "request_sha256",
        "critique",
        "host_review_execution_receipt",
        "publication_acceptance",
        "response_sha256",
    }
    if (
        set(response) != expected_keys
        or response.get("schema") != SCHEMA
        or response.get("fixture") != fixture
        or response.get("request_sha256") != request.get("request_sha256")
        or response.get("publication_acceptance") != "not_claimed"
    ):
        raise ClosedLoopInitialReviewResponseError("initial_review_response_invalid")
    if response.get("response_sha256") != _canonical_hash(response, omitted="response_sha256"):
        raise ClosedLoopInitialReviewResponseError("initial_review_response_hash_invalid")
    critique_ref = response.get("critique")
    host_ref = response.get("host_review_execution_receipt")
    expected_refs = (
        (critique_ref, paths["critique"], "critique"),
        (host_ref, paths["host"], "host_review_execution_receipt"),
    )
    for ref, path, label in expected_refs:
        if (
            not isinstance(ref, dict)
            or set(ref) != {"path", "sha256"}
            or ref.get("path") != path.relative_to(root).as_posix()
            or ref.get("sha256") != _sha256(path)
        ):
            raise ClosedLoopInitialReviewResponseError(f"initial_review_response_{label}_mismatch")
    _validate_critique(paths["critique"], fixture=fixture, root=root)
    host, _, _ = _load_json(
        paths["host"], root=root, label="initial_review_host_review_execution_receipt"
    )
    if set(host) != {
        "schema",
        "request_sha256",
        "actor",
        "transcript",
        "inspected_artifacts",
        "receipt_sha256",
    }:
        raise ClosedLoopInitialReviewResponseError("initial_review_host_receipt_invalid")
    transcript = host.get("transcript")
    if (
        not isinstance(transcript, dict)
        or transcript.get("path") != paths["transcript"].relative_to(root).as_posix()
        or transcript.get("sha256") != _sha256(paths["transcript"])
    ):
        raise ClosedLoopInitialReviewResponseError("initial_review_host_transcript_mismatch")
    adapter_request: dict[str, object] = {
        "request_sha256": request["request_sha256"],
        "before_render": artifacts[0],
        "inspection_artifacts": artifacts[1:],
    }
    try:
        post_repair_visual_review._validate_execution_receipt(  # noqa: SLF001
            host, request=adapter_request, workspace_root=root
        )
    except post_repair_visual_review.PostRepairVisualReviewError as exc:
        raise ClosedLoopInitialReviewResponseError("initial_review_host_receipt_invalid") from exc
    return response, response_bytes, fingerprint, paths["critique"], paths["host"]


def _revalidate(
    *, root: Path, fixture: str, state: dict[str, Any], state_path: Path, response_path: Path
) -> tuple[dict[str, Any], bytes, tuple[int, ...], Path, Path]:
    request, artifacts = _validate_outbound(
        root=root, fixture=fixture, state=state, state_path=state_path
    )
    return _validate_response(
        root=root,
        fixture=fixture,
        attempt_root=state_path.parent,
        response_path=response_path,
        request=request,
        artifacts=artifacts,
    )


def _existing_state_matches(
    state: dict[str, Any],
    *,
    response: Path,
    critique: Path,
    host: Path,
    transcript: Path,
    root: Path,
) -> bool:
    records = {record["role"]: record for record in state["evidence"]}
    return records.get("critique") == {
        "role": "critique",
        "path": critique.relative_to(root).as_posix(),
        "sha256": _sha256(critique),
    } and records.get("host_review_execution_receipt") == {
        "role": "host_review_execution_receipt",
        "path": host.relative_to(root).as_posix(),
        "sha256": _sha256(host),
    } and records.get("initial_visual_review_response") == {
        "role": "initial_visual_review_response",
        "path": response.relative_to(root).as_posix(),
        "sha256": _sha256(response),
    } and records.get("host_review_transcript") == {
        "role": "host_review_transcript",
        "path": transcript.relative_to(root).as_posix(),
        "sha256": _sha256(transcript),
    }


def run_inbound_response(
    fixture: str,
    *,
    state_path: Path,
    response_path: Path,
    execute: bool,
    workspace_root: Path,
    expected_state_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate supplied host evidence and publish only the adjudication stop."""
    root = Path(os.path.abspath(workspace_root))
    response_path = Path(
        os.path.abspath(response_path if response_path.is_absolute() else root / response_path)
    )
    try:
        response_path.relative_to(root)
    except ValueError as exc:
        raise ClosedLoopInitialReviewResponseError(
            "initial_review_response_outside_workspace"
        ) from exc
    state, published_path = _load_state(root, fixture, state_path)
    if expected_state_sha256 is not None and state["state_sha256"] != expected_state_sha256:
        raise ClosedLoopInitialReviewResponseError("closed_loop_projected_state_hash_mismatch")
    _assert_current(root, fixture, state, published_path)
    if state["state"] == "critique_unadjudicated":
        previous = state.get("previous_state_path")
        if not isinstance(previous, str):
            raise ClosedLoopInitialReviewResponseError(
                "initial_review_response_parent_state_missing"
            )
        parent, parent_path = _load_state(root, fixture, Path(previous))
        if parent["state"] != "initial_review_requested":
            raise ClosedLoopInitialReviewResponseError(
                "initial_review_response_parent_state_invalid"
            )
        response, _, _, critique, host = _revalidate(
            root=root,
            fixture=fixture,
            state=parent,
            state_path=parent_path,
            response_path=response_path,
        )
        if not _existing_state_matches(
            state,
            response=response_path,
            critique=critique,
            host=host,
            transcript=response_path.parent / TRANSCRIPT_FILE,
            root=root,
        ):
            raise ClosedLoopInitialReviewResponseError(
                "initial_review_response_published_state_stale"
            )
        return {
            "action": ACTION,
            "stop_boundary": STOP_BOUNDARY,
            "stop_reason": "human_adjudicator",
            "required_actor": STOP_BOUNDARY,
            "created": False,
            "input_state": parent,
            "input_state_path": parent_path,
            "next_state": state["state"],
            "next_state_path": published_path,
            "response_path": response_path,
            "response": response,
            "published_state": state,
        }
    if state["state"] != "initial_review_requested":
        raise ClosedLoopInitialReviewResponseError("closed_loop_state_not_initial_review_requested")
    response, response_bytes, fingerprint, critique, host = _revalidate(
        root=root,
        fixture=fixture,
        state=state,
        state_path=published_path,
        response_path=response_path,
    )
    next_path = (
        published_path.parent / f"state-{state['sequence'] + 1:03d}-critique_unadjudicated.json"
    )
    if not execute:
        return {
            "action": ACTION,
            "stop_boundary": STOP_BOUNDARY,
            "stop_reason": "plan_only",
            "required_actor": "workflow_agent",
            "created": False,
            "input_state": state,
            "input_state_path": published_path,
            "next_state": "critique_unadjudicated",
            "next_state_path": next_path,
            "response_path": response_path,
            "response": response,
            "published_state": None,
        }
    try:
        with closed_loop_attempt_state.attempt_transition_lock(published_path.parent):
            current, current_path = _load_state(root, fixture, published_path)
            _assert_current(root, fixture, current, current_path)
            if current != state or current_path != published_path:
                raise ClosedLoopInitialReviewResponseError(
                    "initial_review_response_state_drift_detected"
                )
            fresh_response, fresh_bytes, fresh_fingerprint, fresh_critique, fresh_host = (
                _revalidate(
                    root=root,
                    fixture=fixture,
                    state=current,
                    state_path=current_path,
                    response_path=response_path,
                )
            )
            if (
                fresh_response != response
                or fresh_bytes != response_bytes
                or fresh_fingerprint != fingerprint
                or fresh_critique != critique
                or fresh_host != host
            ):
                raise ClosedLoopInitialReviewResponseError(
                    "initial_review_response_inputs_drift_detected"
                )
            next_state = closed_loop_attempt_state.transition_state(
                current,
                next_state="critique_unadjudicated",
                actor="host_review_response",
                actor_role="host_llm",
                evidence={
                    "critique": critique,
                    "host_review_execution_receipt": host,
                    "initial_visual_review_response": response_path,
                    "host_review_transcript": response_path.parent / TRANSCRIPT_FILE,
                },
                workspace_root=root,
                previous_state_path=current_path,
            )
            published_next = closed_loop_attempt_state.publish_state(
                next_state, workspace_root=root
            )
    except (
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        repair_transaction.RepairTransactionError,
        OSError,
        ValueError,
    ) as exc:
        if isinstance(exc, ClosedLoopInitialReviewResponseError):
            raise
        raise ClosedLoopInitialReviewResponseError(
            f"initial_review_response_publication_failed:{exc}"
        ) from exc
    return {
        "action": ACTION,
        "stop_boundary": STOP_BOUNDARY,
        "stop_reason": "human_adjudicator",
        "required_actor": STOP_BOUNDARY,
        "created": True,
        "input_state": state,
        "input_state_path": published_path,
        "next_state": next_state["state"],
        "next_state_path": published_next,
        "response_path": response_path,
        "response": response,
        "published_state": next_state,
    }
