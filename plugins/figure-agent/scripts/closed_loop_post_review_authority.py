"""Authority and lineage validation for closed-loop post-repair review."""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any

import closed_loop_attempt_state
import post_repair_visual_review
from PIL import Image


class ClosedLoopPostReviewError(ValueError):
    """Raised when the outbound review handoff cannot be proven current."""


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def stat_fingerprint(path: Path) -> tuple[int, int, int, int, int]:
    stat = path.stat()
    return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)


def capture_render_snapshot(
    path: Path, *, expected_sha256: str
) -> tuple[bytes, tuple[int, int, int, int, int]]:
    before = stat_fingerprint(path)
    data = path.read_bytes()
    after = stat_fingerprint(path)
    if before != after or sha256_bytes(data) != expected_sha256:
        raise ClosedLoopPostReviewError("verified_render_changed_during_snapshot")
    return data, after


def assert_render_unchanged(
    path: Path,
    *,
    expected_sha256: str,
    expected_fingerprint: tuple[int, int, int, int, int],
) -> None:
    data, fingerprint = capture_render_snapshot(
        path, expected_sha256=expected_sha256
    )
    if fingerprint != expected_fingerprint or sha256_bytes(data) != expected_sha256:
        raise ClosedLoopPostReviewError("verified_render_drift_detected")


def workspace_file(root: Path, value: Path | str, *, label: str) -> Path:
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


def load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ClosedLoopPostReviewError(f"{label}_json_invalid") from exc
    if not isinstance(payload, dict):
        raise ClosedLoopPostReviewError(f"{label}_payload_invalid")
    return payload


def evidence_by_role(state: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {str(record["role"]): record for record in state["evidence"]}


def lineage_evidence_record(
    state: dict[str, Any],
    role: str,
    *,
    workspace_root: Path,
) -> dict[str, str]:
    current = state
    while True:
        record = evidence_by_role(current).get(role)
        if isinstance(record, dict):
            return record
        previous_path = current.get("previous_state_path")
        if not isinstance(previous_path, str):
            raise ClosedLoopPostReviewError(f"lineage_evidence_missing:{role}")
        path = workspace_file(
            workspace_root, previous_path, label=f"lineage_state_{role}"
        )
        linked = load_json(path, label=f"lineage_state_{role}")
        try:
            current = closed_loop_attempt_state.validate_state(
                linked, workspace_root=workspace_root
            )
        except closed_loop_attempt_state.ClosedLoopAttemptStateError as exc:
            raise ClosedLoopPostReviewError(
                f"lineage_state_invalid:{role}:{exc}"
            ) from exc


def load_published_state(
    *, workspace_root: Path, fixture: str, state_path: Path
) -> tuple[dict[str, Any], Path]:
    path = workspace_file(workspace_root, state_path, label="closed_loop_state")
    state = load_json(path, label="closed_loop_state")
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


def validate_machine_repair_lineage(
    state: dict[str, Any], *, workspace_root: Path
) -> dict[str, Any]:
    evidence = evidence_by_role(state)
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
    receipt_path = workspace_file(
        workspace_root,
        materialization.get("path", ""),
        label="materialization_receipt",
    )
    receipt = load_json(receipt_path, label="materialization_receipt")
    packet_record = lineage_evidence_record(
        state, "repair_execution_packet", workspace_root=workspace_root
    )
    packet_path = workspace_file(
        workspace_root,
        str(packet_record.get("path") or ""),
        label="repair_packet",
    )
    packet = load_json(packet_path, label="repair_packet")
    state_binding_record = lineage_evidence_record(
        state, "adjudicated_repair_binding", workspace_root=workspace_root
    )
    binding_record = packet.get("adjudicated_repair_binding")
    if not isinstance(binding_record, dict):
        raise ClosedLoopPostReviewError("repair_packet_binding_missing")
    binding_path = workspace_file(
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


def find_finding_bbox(payload: object, finding_id: str) -> list[int] | None:
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
            found = find_finding_bbox(value, finding_id)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = find_finding_bbox(value, finding_id)
            if found is not None:
                return found
    return None


def bound_generic_crop_roles(
    lineage: dict[str, Any], *, workspace_root: Path
) -> dict[str, str]:
    binding = load_json(lineage["binding"], label="adjudicated_repair_binding")
    target_record = binding.get("target_contract")
    if not isinstance(target_record, dict):
        raise ClosedLoopPostReviewError("target_contract_record_missing")
    target_path = workspace_file(
        workspace_root,
        str(target_record.get("path") or ""),
        label="target_contract",
    )
    target_contract = load_json(target_path, label="target_contract")
    targets = target_contract.get("targets")
    if not isinstance(targets, list) or len(targets) != 1 or not isinstance(targets[0], dict):
        raise ClosedLoopPostReviewError("target_contract_not_singular")
    finding = targets[0].get("finding")
    if not isinstance(finding, dict):
        raise ClosedLoopPostReviewError("target_finding_missing")
    finding_id = str(finding.get("id") or "")
    report_path = workspace_file(
        workspace_root,
        str(finding.get("report_path") or ""),
        label="target_finding_report",
    )
    report = load_json(report_path, label="target_finding_report")
    bbox = find_finding_bbox(report, finding_id)
    if bbox is None:
        raise ClosedLoopPostReviewError("target_finding_bbox_missing")
    before_record = binding.get("current_render")
    if not isinstance(before_record, dict):
        raise ClosedLoopPostReviewError("target_coordinate_provenance_missing")
    before_path = workspace_file(
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
    before_bytes, _ = capture_render_snapshot(
        before_path, expected_sha256=str(before_record.get("sha256") or "")
    )
    current_bytes, _ = capture_render_snapshot(
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
    crop_bbox = [
        column * x_mid,
        row * y_mid,
        width if column else x_mid,
        height if row else y_mid,
    ]
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


def validate_crop_manifest_source(
    manifest_path: Path,
    *,
    render: Path,
    render_sha256: str,
    example_dir: Path,
) -> dict[str, Any]:
    manifest = load_json(manifest_path, label="post_review_crop_manifest")
    if (
        manifest.get("render_path") != render.relative_to(example_dir).as_posix()
        or manifest.get("render_sha256") != render_sha256
    ):
        raise ClosedLoopPostReviewError("post_review_crop_manifest_render_drift")
    return manifest


def validate_request_against_machine_state(
    request: dict[str, Any],
    state: dict[str, Any],
    *,
    workspace_root: Path,
) -> None:
    previous_path = state.get("previous_state_path")
    if not isinstance(previous_path, str):
        raise ClosedLoopPostReviewError("post_review_machine_state_missing")
    machine_path = workspace_file(
        workspace_root, previous_path, label="post_review_machine_state"
    )
    machine_state = load_json(machine_path, label="post_review_machine_state")
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
    lineage = validate_machine_repair_lineage(
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
    packet = load_json(lineage["packet"], label="repair_packet")
    expected["repair_packet"] = {
        **post_repair_visual_review._artifact(
            lineage["packet"], root=workspace_root
        ),
        "packet_sha256": packet.get("packet_sha256"),
    }
    if any(request.get(key) != value for key, value in expected.items()):
        raise ClosedLoopPostReviewError("post_review_request_machine_lineage_mismatch")
    expected_crop_roles = bound_generic_crop_roles(
        lineage, workspace_root=workspace_root
    )
    if request.get("crop_roles") != expected_crop_roles:
        raise ClosedLoopPostReviewError("post_review_request_crop_role_mismatch")
    manifest_record = request.get("crop_manifest")
    if not isinstance(manifest_record, dict):
        raise ClosedLoopPostReviewError("post_review_crop_manifest_missing")
    manifest_path = workspace_file(
        workspace_root,
        str(manifest_record.get("path") or ""),
        label="post_review_crop_manifest",
    )
    validate_crop_manifest_source(
        manifest_path,
        render=lineage["render"],
        render_sha256=lineage["render_sha256"],
        example_dir=workspace_root / "examples" / str(request.get("fixture") or ""),
    )
