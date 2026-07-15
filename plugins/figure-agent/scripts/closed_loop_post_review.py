"""Canonical outbound handoff from machine repair to host visual review."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import closed_loop_post_review_authority as authority
import closed_loop_post_review_crops as crop_packs
import post_repair_visual_review
import repair_transaction

ClosedLoopPostReviewError = authority.ClosedLoopPostReviewError

ACTION = "post_repair_visual_review_request"
STOP_BOUNDARY = "host_llm"


def run_outbound_handoff(
    fixture: str,
    *,
    state_path: Path,
    execute: bool,
    workspace_root: Path,
) -> dict[str, Any]:
    """Validate or publish one post-repair host-review handoff."""
    root = Path(os.path.abspath(workspace_root))
    state, published_state_path = authority.load_published_state(
        workspace_root=root,
        fixture=fixture,
        state_path=state_path,
    )
    if state["state"] == "post_review_requested":
        evidence = authority.evidence_by_role(state)
        request_record = evidence.get("post_repair_visual_review_request")
        if not isinstance(request_record, dict):
            raise ClosedLoopPostReviewError("post_review_request_evidence_missing")
        request_path = authority.workspace_file(
            root,
            str(request_record.get("path") or ""),
            label="post_repair_visual_review_request",
        )
        request = authority.load_json(
            request_path, label="post_repair_visual_review_request"
        )
        try:
            post_repair_visual_review._validate_request_freshness(
                request, workspace_root=root
            )
        except post_repair_visual_review.PostRepairVisualReviewError as exc:
            raise ClosedLoopPostReviewError(
                f"post_review_request_invalid:{exc}"
            ) from exc
        if (
            request.get("fixture") != fixture
            or request.get("publication_acceptance") != "not_claimed"
        ):
            raise ClosedLoopPostReviewError("post_review_request_fixture_mismatch")
        authority.validate_request_against_machine_state(
            request, state, workspace_root=root
        )
        return {
            "action": ACTION,
            "stop_boundary": STOP_BOUNDARY,
            "stop_reason": "host_boundary",
            "required_actor": "host_llm",
            "created": False,
            "input_state": state,
            "input_state_path": published_state_path,
            "next_state": "post_review_requested",
            "next_state_path": published_state_path,
            "request_path": request_path,
            "crop_manifest_path": root / str(request["crop_manifest"]["path"]),
            "request": request,
            "published_state": state,
        }
    if state["state"] != "machine_repaired":
        raise ClosedLoopPostReviewError("closed_loop_state_not_machine_repaired")
    lineage = authority.validate_machine_repair_lineage(state, workspace_root=root)
    attempt_root = published_state_path.parent
    review_root = attempt_root / "post-repair-review"
    request_path = review_root / "request.json"
    crop_manifest_path = review_root / "crops" / "manifest.json"
    next_state_path = attempt_root / (
        f"state-{state['sequence'] + 1:03d}-post_review_requested.json"
    )
    request: dict[str, Any] | None = None
    next_state: dict[str, Any] | None = None
    if not execute and (
        review_root.exists() or review_root.is_symlink() or next_state_path.exists()
    ):
        raise ClosedLoopPostReviewError("post_review_output_already_exists")
    if execute:
        example_dir = root / "examples" / fixture
        try:
            with repair_transaction.exclusive_lock(
                attempt_root / ".closed-loop-post-review.lock",
                owner="closed_loop_post_review",
            ):
                if next_state_path.is_file():
                    return run_outbound_handoff(
                        fixture,
                        state_path=next_state_path,
                        execute=execute,
                        workspace_root=root,
                    )
                render_bytes, render_fingerprint = authority.capture_render_snapshot(
                    lineage["render"],
                    expected_sha256=lineage["render_sha256"],
                )
                crop_roles = authority.bound_generic_crop_roles(
                    lineage, workspace_root=root
                )
                if crop_manifest_path.is_file():
                    crops = crop_packs.verify_existing_generic_crop_pack(
                        example_dir=example_dir,
                        render=lineage["render"],
                        render_bytes=render_bytes,
                        render_sha256=lineage["render_sha256"],
                        render_fingerprint=render_fingerprint,
                        attempt_root=attempt_root,
                        review_root=review_root,
                    )
                elif review_root.exists() or review_root.is_symlink():
                    raise ClosedLoopPostReviewError("post_review_output_conflict")
                else:
                    crops = crop_packs.publish_generic_crops(
                        example_dir=example_dir,
                        render=lineage["render"],
                        render_bytes=render_bytes,
                        render_sha256=lineage["render_sha256"],
                        render_fingerprint=render_fingerprint,
                        attempt_root=attempt_root,
                        review_root=review_root,
                    )
                crop_ids = {
                    str(crop.get("id") or "")
                    for crop in crops
                    if isinstance(crop, dict)
                }
                if not set(crop_roles.values()).issubset(crop_ids):
                    raise ClosedLoopPostReviewError(
                        "post_review_required_generic_crops_missing"
                    )

                def build_current_request() -> dict[str, object]:
                    return post_repair_visual_review.build_review_request(
                        binding_path=lineage["binding"],
                        packet_path=lineage["packet"],
                        materialization_receipt_path=lineage["receipt"],
                        crop_manifest_path=crop_manifest_path,
                        crop_roles=crop_roles,
                        workspace_root=root,
                    )

                expected_request = dict(build_current_request())
                authority.assert_render_unchanged(
                    lineage["render"],
                    expected_sha256=lineage["render_sha256"],
                    expected_fingerprint=render_fingerprint,
                )
                if request_path.is_file():
                    request = authority.load_json(
                        request_path, label="post_review_request"
                    )
                    if request != expected_request:
                        raise ClosedLoopPostReviewError(
                            "post_review_existing_request_mismatch"
                        )
                else:
                    request = expected_request
                    post_repair_visual_review._write_once(
                        request_path,
                        request,
                        prepublish=build_current_request,
                    )
                next_state = closed_loop_attempt_state.transition_state(
                    state,
                    next_state="post_review_requested",
                    actor="fig_run",
                    actor_role="workflow_agent",
                    evidence={"post_repair_visual_review_request": request_path},
                    workspace_root=root,
                    previous_state_path=published_state_path,
                )
                authority.assert_render_unchanged(
                    lineage["render"],
                    expected_sha256=lineage["render_sha256"],
                    expected_fingerprint=render_fingerprint,
                )
                published_next_state_path = closed_loop_attempt_state.publish_state(
                    next_state, workspace_root=root
                )
        except (
            closed_loop_attempt_state.ClosedLoopAttemptStateError,
            post_repair_visual_review.PostRepairVisualReviewError,
            repair_transaction.RepairTransactionError,
            OSError,
            ValueError,
        ) as exc:
            raise ClosedLoopPostReviewError(f"post_review_publication_failed:{exc}") from exc
        if published_next_state_path != next_state_path:
            raise ClosedLoopPostReviewError("post_review_state_path_mismatch")
    return {
        "action": ACTION,
        "stop_boundary": STOP_BOUNDARY,
        "stop_reason": "host_boundary" if execute else "plan_only",
        "required_actor": "host_llm" if execute else "workflow_agent",
        "created": execute,
        "input_state": state,
        "input_state_path": published_state_path,
        "next_state": "post_review_requested",
        "next_state_path": next_state_path,
        "request_path": request_path,
        "crop_manifest_path": crop_manifest_path,
        "request": request,
        "published_state": next_state,
    }
