"""Read-only authority plan for R4.14 attempt-local post-repair review."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import authoring_repair_packet
import closed_loop_current_state
import closed_loop_post_review_authority as authority


class AttemptLocalPostReviewAuthorityError(ValueError):
    """Raised when a v2 repair cannot enter the post-review request boundary."""


def _file(root: Path, record: dict[str, object], *, label: str) -> Path:
    path = authority.workspace_file(root, str(record.get("path") or ""), label=label)
    if record.get("sha256") != authority.sha256_bytes(path.read_bytes()):
        raise AttemptLocalPostReviewAuthorityError(f"{label}_hash_drift")
    return path


def plan_attempt_local_post_review(
    fixture: str, *, state_path: Path, workspace_root: Path
) -> dict[str, Any]:
    """Reconstruct only the v2 evidence that a later review-request publisher may use.

    This function is deliberately write-free: it neither creates crops nor advances
    ``machine_repaired``.  A separate R4.14 publisher must consume this exact plan.
    """
    root = workspace_root.resolve()
    state, published_path = authority.load_published_state(
        workspace_root=root, fixture=fixture, state_path=state_path
    )
    current = closed_loop_current_state.resolve_current_attempt(root, fixture)
    if (
        state.get("state") != "machine_repaired"
        or current.get("resolution") != "current"
        or current.get("path") != published_path.relative_to(root).as_posix()
        or current.get("state_sha256") != state.get("state_sha256")
        or current.get("publication_acceptance") != "not_claimed"
    ):
        raise AttemptLocalPostReviewAuthorityError("current_machine_repaired_required")
    evidence = authority.evidence_by_role(state)
    receipt_record = evidence.get("materialization_receipt")
    verification_record = evidence.get("machine_verification_receipt")
    if (
        not isinstance(receipt_record, dict)
        or not isinstance(verification_record, dict)
        or (receipt_record.get("path"), receipt_record.get("sha256"))
        != (verification_record.get("path"), verification_record.get("sha256"))
    ):
        raise AttemptLocalPostReviewAuthorityError("machine_receipt_evidence_mismatch")
    receipt_path = _file(root, receipt_record, label="materialization_receipt")
    receipt = authority.load_json(receipt_path, label="materialization_receipt")
    packet_record = authority.lineage_evidence_record(
        state, "repair_execution_packet", workspace_root=root
    )
    packet_path = _file(root, packet_record, label="repair_packet")
    packet = authority.load_json(packet_path, label="repair_packet")
    try:
        packet = authoring_repair_packet.validate_attempt_local_repair_packet_v2(
            packet, workspace_root=root
        )
    except authoring_repair_packet.RepairExecutionPacketError as exc:
        raise AttemptLocalPostReviewAuthorityError(f"attempt_local_packet_invalid:{exc}") from exc
    binding_record = packet["attempt_local_repair_binding"]
    assert isinstance(binding_record, dict)
    # This record carries the canonical binding hash, not the serialized JSON
    # byte hash.  ``validate_attempt_local_repair_packet_v2`` above owns that
    # semantic validation; only re-check the safe regular workspace path here.
    binding_path = authority.workspace_file(
        root, str(binding_record.get("path") or ""), label="attempt_local_binding"
    )
    output_record = {"path": receipt.get("output_path"), "sha256": receipt.get("output_sha256")}
    output_path = _file(root, output_record, label="materialized_output")
    external = receipt.get("external_compile")
    if (
        receipt.get("schema") != "figure-agent.repair-materialization-receipt.v2"
        or receipt.get("fixture") != fixture
        or receipt.get("decision") != "materialized_machine_verified_human_review_pending"
        or receipt.get("post_render_verification") != "passed"
        or receipt.get("publication_acceptance") != "not_claimed"
        or receipt.get("packet_sha256") != packet.get("packet_sha256")
        or receipt.get("output_path") != packet.get("output_path")
        or not isinstance(external, dict)
    ):
        raise AttemptLocalPostReviewAuthorityError("machine_receipt_lineage_invalid")
    render = packet["render"]
    assert isinstance(render, dict)
    before_render = _file(root, render, label="before_render")
    crops = packet["crops"]
    crop_ids = (
        {item.get("id") for item in crops if isinstance(item, dict)}
        if isinstance(crops, list)
        else set()
    )
    if crop_ids != {
        "full_q1",
        "full_q2",
        "full_q3",
        "full_q4",
        "print_178mm",
        "print_thumbnail",
    }:
        raise AttemptLocalPostReviewAuthorityError("initial_crop_authority_invalid")
    crop_paths = {
        str(item["id"]): _file(root, item, label=f"initial_crop_{item['id']}")
        for item in crops
        if isinstance(item, dict)
    }
    after_png = external.get("png")
    after_pdf = external.get("pdf")
    if not isinstance(after_png, dict) or not isinstance(after_pdf, dict):
        raise AttemptLocalPostReviewAuthorityError("machine_render_evidence_missing")
    return {
        "fixture": fixture,
        "state_path": published_path,
        "packet_path": packet_path,
        "binding_path": binding_path,
        "receipt_path": receipt_path,
        "output_path": output_path,
        "before_render": before_render,
        "initial_crops": crop_paths,
        "after_render": _file(root, after_png, label="after_render"),
        "after_pdf": _file(root, after_pdf, label="after_pdf"),
        "selected_finding_id": packet["selected_finding_id"],
        "semantic_contract": packet["editable_target"]["semantic_contract"],
        "publication_acceptance": "not_claimed",
        "artifact_sha256": {
            "before_render": render["sha256"],
            "after_render": after_png["sha256"],
            "after_pdf": after_pdf["sha256"],
            "materialized_output": output_record["sha256"],
            "materialization_receipt": receipt_record["sha256"],
            "initial_crops": {
                str(item["id"]): item["sha256"] for item in crops if isinstance(item, dict)
            },
        },
    }
