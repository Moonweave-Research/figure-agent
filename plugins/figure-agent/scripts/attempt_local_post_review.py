"""Publish the v2 attempt-local post-repair visual-review request."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

import attempt_local_post_review_authority
import closed_loop_attempt_state
import closed_loop_current_state
import closed_loop_post_review_authority as authority
import closed_loop_post_review_crops
import repair_transaction

SCHEMA = "figure-agent.attempt-local-post-repair-review-request.v2"
ACTION = "attempt_local_post_repair_visual_review_request"
STOP_BOUNDARY = "host_llm"


class AttemptLocalPostReviewError(ValueError):
    """Raised when the v2 review request cannot be safely published."""


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _record(
    path: Path,
    root: Path,
    *,
    role: str | None = None,
    expected_sha256: str | None = None,
) -> dict[str, str]:
    actual_sha256 = authority.sha256_bytes(path.read_bytes())
    if expected_sha256 is not None and actual_sha256 != expected_sha256:
        raise AttemptLocalPostReviewError("post_review_authority_artifact_hash_drift")
    return {
        **({"role": role} if role else {}),
        "path": _relative(path, root),
        "sha256": actual_sha256,
    }


def _request(plan: dict[str, Any], *, root: Path, crop_manifest_path: Path) -> dict[str, Any]:
    manifest = authority.load_json(crop_manifest_path, label="attempt_local_crop_manifest")
    crops = manifest.get("crops")
    if not isinstance(crops, list):
        raise AttemptLocalPostReviewError("after_crop_manifest_invalid")
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "fixture": plan["fixture"],
        "selected_finding_id": plan["selected_finding_id"],
        "semantic_contract": plan["semantic_contract"],
        "publication_acceptance": "not_claimed",
        "review_kind": "human_or_host_post_repair_review",
        "before_render": _record(
            plan["before_render"],
            root,
            role="before_render",
            expected_sha256=plan["artifact_sha256"]["before_render"],
        ),
        "after_render": _record(
            plan["after_render"],
            root,
            role="after_render",
            expected_sha256=plan["artifact_sha256"]["after_render"],
        ),
        "materialized_output": _record(
            plan["output_path"],
            root,
            role="materialized_output",
            expected_sha256=plan["artifact_sha256"]["materialized_output"],
        ),
        "materialization_receipt": _record(
            plan["receipt_path"],
            root,
            role="materialization_receipt",
            expected_sha256=plan["artifact_sha256"]["materialization_receipt"],
        ),
        "initial_crops": [
            {
                "id": crop_id,
                **_record(
                    path,
                    root,
                    expected_sha256=plan["artifact_sha256"]["initial_crops"][crop_id],
                ),
            }
            for crop_id, path in sorted(plan["initial_crops"].items())
        ],
        "after_crop_manifest": _record(crop_manifest_path, root, role="after_crop_manifest"),
        "after_crops": crops,
        "required_verdicts": [
            "target_resolved",
            "no_new_local_defect",
            "unchanged_region_regression",
        ],
    }
    payload["request_sha256"] = authority.sha256_bytes(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )
    return payload


def _write_request(path: Path, payload: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise AttemptLocalPostReviewError("post_review_request_conflict")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_request(payload: dict[str, Any], *, root: Path, fixture: str) -> None:
    canonical = {key: value for key, value in payload.items() if key != "request_sha256"}
    expected_hash = authority.sha256_bytes(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )
    if (
        payload.get("schema") != SCHEMA
        or payload.get("fixture") != fixture
        or payload.get("publication_acceptance") != "not_claimed"
        or payload.get("review_kind") != "human_or_host_post_repair_review"
        or payload.get("request_sha256") != expected_hash
    ):
        raise AttemptLocalPostReviewError("post_review_request_semantics_invalid")
    records: list[dict[str, Any]] = []
    for key in (
        "before_render",
        "after_render",
        "materialized_output",
        "materialization_receipt",
        "after_crop_manifest",
    ):
        record = payload.get(key)
        if not isinstance(record, dict):
            raise AttemptLocalPostReviewError("post_review_request_record_invalid")
        records.append(record)
    initial_crops = payload.get("initial_crops")
    if (
        not isinstance(initial_crops, list)
        or {item.get("id") for item in initial_crops if isinstance(item, dict)}
        != {"full_q1", "full_q2", "full_q3", "full_q4", "print_178mm", "print_thumbnail"}
        or any(not isinstance(item, dict) or "bbox_px" in item for item in initial_crops)
    ):
        raise AttemptLocalPostReviewError("post_review_initial_crops_invalid")
    records.extend(initial_crops)
    for record in records:
        path = authority.workspace_file(
            root, str(record.get("path") or ""), label="attempt_local_review_artifact"
        )
        if record.get("sha256") != authority.sha256_bytes(path.read_bytes()):
            raise AttemptLocalPostReviewError("post_review_request_artifact_hash_drift")
    manifest = authority.load_json(
        authority.workspace_file(
            root,
            str(payload["after_crop_manifest"].get("path") or ""),
            label="attempt_local_crop_manifest",
        ),
        label="attempt_local_crop_manifest",
    )
    after_crops = payload.get("after_crops")
    if not isinstance(after_crops, list) or after_crops != manifest.get("crops"):
        raise AttemptLocalPostReviewError("post_review_after_crops_invalid")
    example_dir = root / "examples" / fixture
    for crop in after_crops:
        if not isinstance(crop, dict):
            raise AttemptLocalPostReviewError("post_review_after_crops_invalid")
        path = authority.workspace_file(
            root,
            example_dir / str(crop.get("path") or ""),
            label="attempt_local_after_crop",
        )
        if crop.get("sha256") != authority.sha256_bytes(path.read_bytes()):
            raise AttemptLocalPostReviewError("post_review_after_crop_hash_drift")


def _recover_existing(
    *, root: Path, fixture: str, next_state_path: Path, request_path: Path
) -> dict[str, Any]:
    state, published_path = authority.load_published_state(
        workspace_root=root, fixture=fixture, state_path=next_state_path
    )
    if published_path != next_state_path:
        raise AttemptLocalPostReviewError("post_review_state_path_mismatch")
    current = closed_loop_current_state.resolve_current_attempt(root, fixture)
    if (
        current.get("resolution") != "current"
        or current.get("path") != _relative(next_state_path, root)
        or current.get("state_sha256") != state.get("state_sha256")
    ):
        raise AttemptLocalPostReviewError("post_review_current_state_mismatch")
    record = authority.evidence_by_role(state).get("post_repair_visual_review_request")
    if not isinstance(record, dict):
        raise AttemptLocalPostReviewError("post_review_request_evidence_missing")
    existing = authority.workspace_file(
        root, str(record.get("path") or ""), label="attempt_local_review_request"
    )
    if existing != request_path or record.get("sha256") != authority.sha256_bytes(
        existing.read_bytes()
    ):
        raise AttemptLocalPostReviewError("post_review_request_evidence_drift")
    request = authority.load_json(existing, label="attempt_local_review_request")
    _validate_request(request, root=root, fixture=fixture)
    return {"state": state, "request": request}


def _revalidate_request_before_state_publish(
    request_path: Path,
    expected: dict[str, Any],
    *,
    root: Path,
    fixture: str,
) -> None:
    actual = authority.load_json(request_path, label="attempt_local_review_request")
    if actual != expected:
        raise AttemptLocalPostReviewError("post_review_request_drift_before_state_publish")
    _validate_request(actual, root=root, fixture=fixture)


def run_attempt_local_post_review(
    fixture: str,
    *,
    state_path: Path,
    execute: bool,
    workspace_root: Path,
) -> dict[str, Any]:
    """Plan or publish one v2 request, stopping before any reviewer invocation."""
    root = Path(os.path.abspath(workspace_root))
    machine_state, machine_state_path = authority.load_published_state(
        workspace_root=root, fixture=fixture, state_path=state_path
    )
    attempt_root = machine_state_path.parent
    review_root = attempt_root / "attempt-local-post-repair-review"
    request_path = review_root / "request.json"
    crop_manifest_path = review_root / "crops" / "manifest.json"
    next_state_path = attempt_root / (
        f"state-{machine_state['sequence'] + 1:03d}-post_review_requested.json"
    )
    if execute and (next_state_path.exists() or next_state_path.is_symlink()):
        try:
            with closed_loop_attempt_state.attempt_transition_lock(attempt_root):
                recovered = _recover_existing(
                    root=root,
                    fixture=fixture,
                    next_state_path=next_state_path,
                    request_path=request_path,
                )
        except (
            authority.ClosedLoopPostReviewError,
            closed_loop_attempt_state.ClosedLoopAttemptStateError,
            repair_transaction.RepairTransactionError,
            OSError,
            ValueError,
        ) as exc:
            if isinstance(exc, AttemptLocalPostReviewError):
                raise
            raise AttemptLocalPostReviewError(f"post_review_publication_failed:{exc}") from exc
        return {
            "action": ACTION,
            "created": False,
            "stop_boundary": STOP_BOUNDARY,
            "stop_reason": "host_boundary",
            "required_actor": "host_llm",
            "next_state": "post_review_requested",
            "next_state_path": next_state_path,
            "request_path": request_path,
            "crop_manifest_path": crop_manifest_path,
            "request": recovered["request"],
            "published_state": recovered["state"],
        }
    plan = attempt_local_post_review_authority.plan_attempt_local_post_review(
        fixture, state_path=state_path, workspace_root=root
    )
    if not execute:
        if review_root.exists() or review_root.is_symlink() or next_state_path.exists():
            raise AttemptLocalPostReviewError("post_review_output_already_exists")
        return {
            "action": ACTION,
            "created": False,
            "stop_boundary": STOP_BOUNDARY,
            "stop_reason": "plan_only",
            "required_actor": "workflow_agent",
            "next_state": "post_review_requested",
            "request_path": request_path,
            "crop_manifest_path": crop_manifest_path,
        }
    try:
        with closed_loop_attempt_state.attempt_transition_lock(attempt_root):
            if next_state_path.exists() or next_state_path.is_symlink():
                recovered = _recover_existing(
                    root=root,
                    fixture=fixture,
                    next_state_path=next_state_path,
                    request_path=request_path,
                )
                return {
                    "action": ACTION,
                    "created": False,
                    "stop_boundary": STOP_BOUNDARY,
                    "stop_reason": "host_boundary",
                    "required_actor": "host_llm",
                    "next_state": "post_review_requested",
                    "next_state_path": next_state_path,
                    "request_path": request_path,
                    "crop_manifest_path": crop_manifest_path,
                    "request": recovered["request"],
                    "published_state": recovered["state"],
                }
            plan = attempt_local_post_review_authority.plan_attempt_local_post_review(
                fixture, state_path=state_path, workspace_root=root
            )
            machine_state = authority.load_json(plan["state_path"], label="machine_repaired_state")
            after_sha = plan["artifact_sha256"]["after_render"]
            render_bytes, fingerprint = authority.capture_render_snapshot(
                plan["after_render"], expected_sha256=after_sha
            )
            example_dir = root / "examples" / fixture
            if crop_manifest_path.is_file():
                closed_loop_post_review_crops.verify_existing_generic_crop_pack(
                    example_dir=example_dir,
                    render=plan["after_render"],
                    render_bytes=render_bytes,
                    render_sha256=after_sha,
                    render_fingerprint=fingerprint,
                    attempt_root=attempt_root,
                    review_root=review_root,
                )
                expected = _request(plan, root=root, crop_manifest_path=crop_manifest_path)
                if (
                    authority.load_json(request_path, label="attempt_local_review_request")
                    != expected
                ):
                    raise AttemptLocalPostReviewError("post_review_existing_request_mismatch")
                request = expected
            elif review_root.exists() or review_root.is_symlink():
                raise AttemptLocalPostReviewError("post_review_output_conflict")
            else:
                staging_root = attempt_root / ".attempt-local-post-review-staging"
                try:
                    staging_root, _ = closed_loop_post_review_crops.generate_generic_crop_staging(
                        example_dir=example_dir,
                        render=plan["after_render"],
                        render_bytes=render_bytes,
                        render_sha256=after_sha,
                        render_fingerprint=fingerprint,
                        staging_root=staging_root,
                        review_root=review_root,
                    )
                    staged_manifest = staging_root / "crops" / "manifest.json"
                    request = _request(plan, root=root, crop_manifest_path=staged_manifest)
                    # The manifest record must bind its final published path and bytes.
                    request["after_crop_manifest"]["path"] = _relative(crop_manifest_path, root)
                    request["request_sha256"] = authority.sha256_bytes(
                        json.dumps(
                            {k: v for k, v in request.items() if k != "request_sha256"},
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode("utf-8")
                    )
                    _write_request(staging_root / "request.json", request)
                    authority.assert_render_unchanged(
                        plan["after_render"],
                        expected_sha256=after_sha,
                        expected_fingerprint=fingerprint,
                    )
                    os.replace(staging_root, review_root)
                except Exception:
                    if staging_root.is_dir() and not staging_root.is_symlink():
                        shutil.rmtree(staging_root)
                    raise
            _validate_request(request, root=root, fixture=fixture)
            next_state = closed_loop_attempt_state.transition_state(
                machine_state,
                next_state="post_review_requested",
                actor="fig_run",
                actor_role="workflow_agent",
                evidence={"post_repair_visual_review_request": request_path},
                workspace_root=root,
                previous_state_path=plan["state_path"],
            )
            authority.assert_render_unchanged(
                plan["after_render"],
                expected_sha256=after_sha,
                expected_fingerprint=fingerprint,
            )
            _revalidate_request_before_state_publish(
                request_path, request, root=root, fixture=fixture
            )
            published = closed_loop_attempt_state.publish_state(next_state, workspace_root=root)
            if published != next_state_path:
                raise AttemptLocalPostReviewError("post_review_state_path_mismatch")
    except (
        attempt_local_post_review_authority.AttemptLocalPostReviewAuthorityError,
        authority.ClosedLoopPostReviewError,
        closed_loop_attempt_state.ClosedLoopAttemptStateError,
        repair_transaction.RepairTransactionError,
        OSError,
        ValueError,
    ) as exc:
        if isinstance(exc, AttemptLocalPostReviewError):
            raise
        raise AttemptLocalPostReviewError(f"post_review_publication_failed:{exc}") from exc
    return {
        "action": ACTION,
        "created": True,
        "stop_boundary": STOP_BOUNDARY,
        "stop_reason": "host_boundary",
        "required_actor": "host_llm",
        "next_state": "post_review_requested",
        "next_state_path": next_state_path,
        "request_path": request_path,
        "crop_manifest_path": crop_manifest_path,
        "request": request,
        "published_state": next_state,
    }
