"""Canonical outbound handoff from machine repair to host visual review."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import critique_zoom_crops
import post_repair_visual_review
import repair_transaction
from PIL import Image

ACTION = "post_repair_visual_review_request"
STOP_BOUNDARY = "host_llm"


class ClosedLoopPostReviewError(ValueError):
    """Raised when the outbound review handoff cannot be proven current."""


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _stat_fingerprint(path: Path) -> tuple[int, int, int, int, int]:
    stat = path.stat()
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def _capture_render_snapshot(
    path: Path, *, expected_sha256: str
) -> tuple[bytes, tuple[int, int, int, int, int]]:
    before = _stat_fingerprint(path)
    data = path.read_bytes()
    after = _stat_fingerprint(path)
    if before != after or _sha256_bytes(data) != expected_sha256:
        raise ClosedLoopPostReviewError("verified_render_changed_during_snapshot")
    return data, after


def _assert_render_unchanged(
    path: Path,
    *,
    expected_sha256: str,
    expected_fingerprint: tuple[int, int, int, int, int],
) -> None:
    data, fingerprint = _capture_render_snapshot(
        path, expected_sha256=expected_sha256
    )
    if fingerprint != expected_fingerprint or _sha256_bytes(data) != expected_sha256:
        raise ClosedLoopPostReviewError("verified_render_drift_detected")


def _workspace_file(root: Path, value: Path | str, *, label: str) -> Path:
    candidate = Path(value)
    lexical = Path(os.path.abspath(candidate if candidate.is_absolute() else root / candidate))
    try:
        relative = lexical.relative_to(root)
    except ValueError as exc:
        raise ClosedLoopPostReviewError(f"{label}_outside_workspace") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ClosedLoopPostReviewError(f"{label}_symlink")
    if not current.is_file():
        raise ClosedLoopPostReviewError(f"{label}_missing")
    return current


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopPostReviewError(f"{label}_json_invalid") from exc
    if not isinstance(payload, dict):
        raise ClosedLoopPostReviewError(f"{label}_payload_invalid")
    return payload


def _evidence_by_role(state: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {str(record["role"]): record for record in state["evidence"]}


def _lineage_evidence_record(
    state: dict[str, Any],
    role: str,
    *,
    workspace_root: Path,
) -> dict[str, str]:
    current = state
    while True:
        record = _evidence_by_role(current).get(role)
        if isinstance(record, dict):
            return record
        previous_path = current.get("previous_state_path")
        if not isinstance(previous_path, str):
            raise ClosedLoopPostReviewError(f"lineage_evidence_missing:{role}")
        path = _workspace_file(
            workspace_root, previous_path, label=f"lineage_state_{role}"
        )
        linked = _load_json(path, label=f"lineage_state_{role}")
        try:
            current = closed_loop_attempt_state.validate_state(
                linked, workspace_root=workspace_root
            )
        except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
            raise ClosedLoopPostReviewError(
                f"lineage_state_invalid:{role}:{exc}"
            ) from exc


def _load_published_state(
    *, workspace_root: Path, fixture: str, state_path: Path
) -> tuple[dict[str, Any], Path]:
    path = _workspace_file(workspace_root, state_path, label="closed_loop_state")
    state = _load_json(path, label="closed_loop_state")
    try:
        state = closed_loop_attempt_state.validate_state(
            state, workspace_root=workspace_root
        )
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise ClosedLoopPostReviewError(f"closed_loop_state_invalid:{exc}") from exc
    if state["fixture"] != fixture:
        raise ClosedLoopPostReviewError("closed_loop_state_fixture_mismatch")
    if path != closed_loop_attempt_state.state_path(
        state, workspace_root=workspace_root
    ):
        raise ClosedLoopPostReviewError("closed_loop_state_path_mismatch")
    return state, path


def _validate_machine_repair_lineage(
    state: dict[str, Any], *, workspace_root: Path
) -> dict[str, Any]:
    evidence = _evidence_by_role(state)
    materialization = evidence.get("materialization_receipt")
    verification = evidence.get("machine_verification_receipt")
    if not isinstance(materialization, dict) or not isinstance(verification, dict):
        raise ClosedLoopPostReviewError("machine_receipt_evidence_mismatch")
    if (
        materialization.get("path"),
        materialization.get("sha256"),
    ) != (
        verification.get("path"),
        verification.get("sha256"),
    ):
        raise ClosedLoopPostReviewError("machine_receipt_evidence_mismatch")
    receipt_path = _workspace_file(
        workspace_root,
        materialization.get("path", ""),
        label="materialization_receipt",
    )
    receipt = _load_json(receipt_path, label="materialization_receipt")
    packet_record = _lineage_evidence_record(
        state, "repair_execution_packet", workspace_root=workspace_root
    )
    packet_path = _workspace_file(
        workspace_root,
        str(packet_record.get("path") or ""),
        label="repair_packet",
    )
    packet = _load_json(packet_path, label="repair_packet")
    state_binding_record = _lineage_evidence_record(
        state, "adjudicated_repair_binding", workspace_root=workspace_root
    )
    binding_record = packet.get("adjudicated_repair_binding")
    if not isinstance(binding_record, dict):
        raise ClosedLoopPostReviewError("repair_packet_binding_missing")
    binding_path = _workspace_file(
        workspace_root,
        str(binding_record.get("path") or ""),
        label="adjudicated_repair_binding",
    )
    if binding_record.get("sha256") != post_repair_visual_review._sha256(binding_path):
        raise ClosedLoopPostReviewError("repair_packet_binding_hash_stale")
    if (
        binding_record.get("path"),
        binding_record.get("sha256"),
    ) != (
        state_binding_record.get("path"),
        state_binding_record.get("sha256"),
    ):
        raise ClosedLoopPostReviewError("repair_packet_state_binding_mismatch")
    try:
        post_repair_visual_review._validate_current_bound_repair_packet(
            packet,
            binding_path=binding_path,
            workspace_root=workspace_root,
        )
        render_paths = post_repair_visual_review._validate_machine_verification_receipt(
            receipt,
            packet=packet,
            workspace_root=workspace_root,
        )
    except post_repair_visual_review.PostRepairVisualReviewError as exc:
        raise ClosedLoopPostReviewError(f"machine_repair_lineage_invalid:{exc}") from exc
    if receipt.get("packet_sha256") != packet.get("packet_sha256"):
        raise ClosedLoopPostReviewError("machine_receipt_packet_hash_mismatch")
    png_record = receipt.get("external_compile", {}).get("png")
    if not isinstance(png_record, dict) or not isinstance(
        png_record.get("sha256"), str
    ):
        raise ClosedLoopPostReviewError("machine_receipt_render_hash_missing")
    return {
        "binding": binding_path,
        "packet": packet_path,
        "receipt": receipt_path,
        "render": render_paths["png"],
        "render_sha256": png_record["sha256"],
    }


def _find_finding_bbox(payload: object, finding_id: str) -> list[int] | None:
    if isinstance(payload, dict):
        bbox = payload.get("bbox_px")
        if payload.get("id") == finding_id and (
            isinstance(bbox, list)
            and len(bbox) == 4
            and all(isinstance(value, int) for value in bbox)
            and bbox[2] > bbox[0]
            and bbox[3] > bbox[1]
        ):
            return bbox
        for value in payload.values():
            found = _find_finding_bbox(value, finding_id)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = _find_finding_bbox(value, finding_id)
            if found is not None:
                return found
    return None


def _bound_generic_crop_roles(
    lineage: dict[str, Any], *, workspace_root: Path
) -> dict[str, str]:
    binding = _load_json(lineage["binding"], label="adjudicated_repair_binding")
    target_record = binding.get("target_contract")
    if not isinstance(target_record, dict):
        raise ClosedLoopPostReviewError("target_contract_record_missing")
    target_path = _workspace_file(
        workspace_root,
        str(target_record.get("path") or ""),
        label="target_contract",
    )
    target_contract = _load_json(target_path, label="target_contract")
    targets = target_contract.get("targets")
    if not isinstance(targets, list) or len(targets) != 1 or not isinstance(targets[0], dict):
        raise ClosedLoopPostReviewError("target_contract_not_singular")
    finding = targets[0].get("finding")
    if not isinstance(finding, dict):
        raise ClosedLoopPostReviewError("target_finding_missing")
    finding_id = str(finding.get("id") or "")
    report_path = _workspace_file(
        workspace_root,
        str(finding.get("report_path") or ""),
        label="target_finding_report",
    )
    report = _load_json(report_path, label="target_finding_report")
    bbox = _find_finding_bbox(report, finding_id)
    if bbox is None:
        raise ClosedLoopPostReviewError("target_finding_bbox_missing")
    before_record = binding.get("current_render")
    if not isinstance(before_record, dict):
        raise ClosedLoopPostReviewError("target_coordinate_provenance_missing")
    before_path = _workspace_file(
        workspace_root,
        str(before_record.get("path") or ""),
        label="target_coordinate_render",
    )
    example_dir = workspace_root / "examples" / str(binding.get("fixture") or "")
    report_render = example_dir / str(report.get("render_path") or "")
    if (
        report_render != before_path
        or report.get("render_sha256") != before_record.get("sha256")
    ):
        raise ClosedLoopPostReviewError("target_coordinate_provenance_mismatch")
    before_bytes, _ = _capture_render_snapshot(
        before_path, expected_sha256=str(before_record.get("sha256") or "")
    )
    current_bytes, _ = _capture_render_snapshot(
        lineage["render"], expected_sha256=lineage["render_sha256"]
    )
    with Image.open(io.BytesIO(before_bytes)) as image:
        before_size = image.size
    with Image.open(io.BytesIO(current_bytes)) as image:
        current_size = image.size
    if before_size != current_size:
        raise ClosedLoopPostReviewError("target_coordinate_space_incompatible")
    width, height = current_size
    if not (0 <= bbox[0] < bbox[2] <= width and 0 <= bbox[1] < bbox[3] <= height):
        raise ClosedLoopPostReviewError("target_finding_bbox_outside_render")
    x_mid = round(width / 2)
    y_mid = round(height / 2)
    if bbox[2] <= x_mid:
        column = 0
    elif bbox[0] >= x_mid:
        column = 1
    else:
        raise ClosedLoopPostReviewError(
            "target_finding_bbox_crosses_crop_boundary"
        )
    if bbox[3] <= y_mid:
        row = 0
    elif bbox[1] >= y_mid:
        row = 1
    else:
        raise ClosedLoopPostReviewError(
            "target_finding_bbox_crosses_crop_boundary"
        )
    crop_bbox = [column * x_mid, row * y_mid, width if column else x_mid, height if row else y_mid]
    if not (
        crop_bbox[0] <= bbox[0]
        and crop_bbox[1] <= bbox[1]
        and crop_bbox[2] >= bbox[2]
        and crop_bbox[3] >= bbox[3]
    ):
        raise ClosedLoopPostReviewError("target_crop_does_not_contain_finding")
    target_index = 1 + column + 2 * row
    neighbor_index = target_index + 1 if target_index % 2 == 1 else target_index - 1
    return {
        "target_crop": f"full_q{target_index}",
        "neighbor_crop": f"full_q{neighbor_index}",
        "print_scale": "print_thumbnail",
    }


def _validate_request_against_machine_state(
    request: dict[str, Any],
    state: dict[str, Any],
    *,
    workspace_root: Path,
) -> None:
    previous_path = state.get("previous_state_path")
    if not isinstance(previous_path, str):
        raise ClosedLoopPostReviewError("post_review_machine_state_missing")
    machine_path = _workspace_file(
        workspace_root, previous_path, label="post_review_machine_state"
    )
    machine_state = _load_json(machine_path, label="post_review_machine_state")
    try:
        machine_state = closed_loop_attempt_state.validate_state(
            machine_state, workspace_root=workspace_root
        )
    except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
        raise ClosedLoopPostReviewError(
            f"post_review_machine_state_invalid:{exc}"
        ) from exc
    if machine_state.get("state") != "machine_repaired":
        raise ClosedLoopPostReviewError("post_review_machine_state_invalid")
    lineage = _validate_machine_repair_lineage(
        machine_state, workspace_root=workspace_root
    )
    expected = {
        "binding": post_repair_visual_review._artifact(
            lineage["binding"], root=workspace_root
        ),
        "materialization_receipt": post_repair_visual_review._artifact(
            lineage["receipt"], root=workspace_root
        ),
    }
    packet = _load_json(lineage["packet"], label="repair_packet")
    expected["repair_packet"] = {
        **post_repair_visual_review._artifact(
            lineage["packet"], root=workspace_root
        ),
        "packet_sha256": packet.get("packet_sha256"),
    }
    if any(request.get(key) != value for key, value in expected.items()):
        raise ClosedLoopPostReviewError("post_review_request_machine_lineage_mismatch")
    expected_crop_roles = _bound_generic_crop_roles(
        lineage, workspace_root=workspace_root
    )
    if request.get("crop_roles") != expected_crop_roles:
        raise ClosedLoopPostReviewError("post_review_request_crop_role_mismatch")
    manifest_record = request.get("crop_manifest")
    if not isinstance(manifest_record, dict):
        raise ClosedLoopPostReviewError("post_review_crop_manifest_missing")
    manifest_path = _workspace_file(
        workspace_root,
        str(manifest_record.get("path") or ""),
        label="post_review_crop_manifest",
    )
    _validate_crop_manifest_source(
        manifest_path,
        render=lineage["render"],
        render_sha256=lineage["render_sha256"],
        example_dir=workspace_root / "examples" / str(request.get("fixture") or ""),
    )


def _generate_generic_crop_staging(
    *,
    example_dir: Path,
    render: Path,
    render_bytes: bytes,
    render_sha256: str,
    render_fingerprint: tuple[int, int, int, int, int],
    staging_root: Path,
    review_root: Path,
) -> tuple[Path, list[dict[str, Any]]]:
    if staging_root.is_symlink():
        raise ClosedLoopPostReviewError("post_review_staging_symlink")
    if staging_root.exists():
        shutil.rmtree(staging_root)
    _assert_render_unchanged(
        render,
        expected_sha256=render_sha256,
        expected_fingerprint=render_fingerprint,
    )
    staging_root.mkdir()
    render_snapshot = staging_root / "verified-render-snapshot.png"
    render_snapshot.write_bytes(render_bytes)
    staging_crops = staging_root / "crops"
    staging_manifest = staging_crops / "manifest.json"
    try:
        crops = critique_zoom_crops.build_zoom_crop_pack(
            example_dir,
            render_snapshot,
            panel_crop_paths=(),
            output_dir=staging_crops,
            manifest_path=staging_manifest,
            include_detector_crops=False,
        )
        manifest = _load_json(staging_manifest, label="staged_crop_manifest")
        old_prefix = staging_crops.relative_to(example_dir).as_posix() + "/"
        new_prefix = (review_root / "crops").relative_to(example_dir).as_posix() + "/"
        for crop in manifest.get("crops", []):
            path = crop.get("path") if isinstance(crop, dict) else None
            if not isinstance(path, str) or not path.startswith(old_prefix):
                raise ClosedLoopPostReviewError("staged_crop_path_invalid")
            crop["path"] = new_prefix + path.removeprefix(old_prefix)
            crop["source_path"] = render.relative_to(example_dir).as_posix()
        manifest["render_path"] = render.relative_to(example_dir).as_posix()
        manifest["render_sha256"] = render_sha256
        staging_manifest.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _assert_render_unchanged(
            render,
            expected_sha256=render_sha256,
            expected_fingerprint=render_fingerprint,
        )
        render_snapshot.unlink()
        return staging_root, crops
    except Exception:
        if staging_root.is_dir() and not staging_root.is_symlink():
            shutil.rmtree(staging_root)
        raise


def _publish_generic_crops(
    *,
    example_dir: Path,
    render: Path,
    render_bytes: bytes,
    render_sha256: str,
    render_fingerprint: tuple[int, int, int, int, int],
    attempt_root: Path,
    review_root: Path,
) -> list[dict[str, Any]]:
    staging_root, crops = _generate_generic_crop_staging(
        example_dir=example_dir,
        render=render,
        render_bytes=render_bytes,
        render_sha256=render_sha256,
        render_fingerprint=render_fingerprint,
        staging_root=attempt_root / ".post-repair-review-staging",
        review_root=review_root,
    )
    try:
        if review_root.exists() or review_root.is_symlink():
            raise ClosedLoopPostReviewError("post_review_output_conflict")
        os.replace(staging_root, review_root)
        return crops
    except Exception:
        if staging_root.is_dir() and not staging_root.is_symlink():
            shutil.rmtree(staging_root)
        raise


def _verify_existing_generic_crop_pack(
    *,
    example_dir: Path,
    render: Path,
    render_bytes: bytes,
    render_sha256: str,
    render_fingerprint: tuple[int, int, int, int, int],
    attempt_root: Path,
    review_root: Path,
) -> list[dict[str, Any]]:
    staging_root, crops = _generate_generic_crop_staging(
        example_dir=example_dir,
        render=render,
        render_bytes=render_bytes,
        render_sha256=render_sha256,
        render_fingerprint=render_fingerprint,
        staging_root=attempt_root / ".post-repair-review-verify-staging",
        review_root=review_root,
    )
    expected_root = staging_root / "crops"
    actual_root = review_root / "crops"
    try:
        if actual_root.is_symlink() or not actual_root.is_dir():
            raise ClosedLoopPostReviewError("post_review_crop_pack_mismatch")
        expected_paths = {
            path.relative_to(expected_root)
            for path in expected_root.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        actual_paths = {
            path.relative_to(actual_root)
            for path in actual_root.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        if (
            expected_paths != actual_paths
            or any(path.is_symlink() for path in actual_root.rglob("*"))
            or any(
                (expected_root / relative).read_bytes()
                != (actual_root / relative).read_bytes()
                for relative in expected_paths
            )
        ):
            raise ClosedLoopPostReviewError("post_review_crop_pack_mismatch")
        return crops
    finally:
        if staging_root.is_dir() and not staging_root.is_symlink():
            shutil.rmtree(staging_root)


def _validate_crop_manifest_source(
    manifest_path: Path,
    *,
    render: Path,
    render_sha256: str,
    example_dir: Path,
) -> dict[str, Any]:
    manifest = _load_json(manifest_path, label="post_review_crop_manifest")
    if (
        manifest.get("render_path") != render.relative_to(example_dir).as_posix()
        or manifest.get("render_sha256") != render_sha256
    ):
        raise ClosedLoopPostReviewError("post_review_crop_manifest_render_drift")
    return manifest


def run_outbound_handoff(
    fixture: str,
    *,
    state_path: Path,
    execute: bool,
    workspace_root: Path,
) -> dict[str, Any]:
    """Validate or publish one post-repair host-review handoff."""
    root = Path(os.path.abspath(workspace_root))
    state, published_state_path = _load_published_state(
        workspace_root=root,
        fixture=fixture,
        state_path=state_path,
    )
    if state["state"] == "post_review_requested":
        evidence = _evidence_by_role(state)
        request_record = evidence.get("post_repair_visual_review_request")
        if not isinstance(request_record, dict):
            raise ClosedLoopPostReviewError("post_review_request_evidence_missing")
        request_path = _workspace_file(
            root,
            str(request_record.get("path") or ""),
            label="post_repair_visual_review_request",
        )
        request = _load_json(request_path, label="post_repair_visual_review_request")
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
        _validate_request_against_machine_state(
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
    lineage = _validate_machine_repair_lineage(state, workspace_root=root)
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
                render_bytes, render_fingerprint = _capture_render_snapshot(
                    lineage["render"],
                    expected_sha256=lineage["render_sha256"],
                )
                crop_roles = _bound_generic_crop_roles(lineage, workspace_root=root)
                if crop_manifest_path.is_file():
                    crops = _verify_existing_generic_crop_pack(
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
                    crops = _publish_generic_crops(
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
                _assert_render_unchanged(
                    lineage["render"],
                    expected_sha256=lineage["render_sha256"],
                    expected_fingerprint=render_fingerprint,
                )
                if request_path.is_file():
                    request = _load_json(request_path, label="post_review_request")
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
                _assert_render_unchanged(
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
