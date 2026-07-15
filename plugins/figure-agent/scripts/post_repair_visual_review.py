#!/usr/bin/env python3
"""Hash-bound fresh visual-review gate for one materialized repair."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import authoring_repair_finalize
import authoring_repair_packet
import critique_adjudication
import repair_transaction

REQUEST_SCHEMA = "figure-agent.post-repair-visual-review-request.v1"
RESPONSE_SCHEMA = "figure-agent.post-repair-visual-review-response.v1"
RECEIPT_SCHEMA = "figure-agent.post-repair-visual-review-receipt.v1"
EXECUTION_RECEIPT_SCHEMA = "figure-agent.host-review-execution-receipt.v1"
CROP_MANIFEST_SCHEMA = "figure-agent.audit-crop-manifest.v1"
REQUIRED_ROLES = frozenset(
    {"full_render", "target_crop", "neighbor_crop", "print_scale"}
)
CROP_ROLES = frozenset({"target_crop", "neighbor_crop", "print_scale"})
ROLE_KINDS = {
    "target_crop": frozenset(
        {"zoom_crop", "visual_clash_crop", "label_path_crop"}
    ),
    "neighbor_crop": frozenset(
        {"zoom_crop", "visual_clash_crop", "label_path_crop"}
    ),
    "print_scale": frozenset({"print_scale"}),
}
REQUIRED_VERDICTS = {
    "target_resolved": frozenset({"resolved", "still_present", "uncertain"}),
    "no_new_local_defect": frozenset({"pass", "fail", "uncertain"}),
    "unchanged_region_regression": frozenset({"none", "present", "uncertain"}),
}


class PostRepairVisualReviewError(ValueError):
    """Raised when post-repair review evidence is missing, stale, or malformed."""


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(payload: dict[str, Any], *, omitted: str) -> str:
    canonical = {key: value for key, value in payload.items() if key != omitted}
    data = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _workspace_file(root: Path, path: Path | str, *, label: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        lexical = Path(os.path.abspath(candidate))
    else:
        if not candidate.parts or any(
            part in {"", ".", ".."} for part in candidate.parts
        ):
            raise PostRepairVisualReviewError(
                f"{label} must be workspace-relative and safe"
            )
        lexical = root / candidate
    try:
        relative = lexical.relative_to(root)
    except ValueError as exc:
        raise PostRepairVisualReviewError(f"{label} must remain inside workspace") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise PostRepairVisualReviewError(f"{label} must not traverse a symlink")
    if not current.is_file():
        raise PostRepairVisualReviewError(f"{label} must be a regular file")
    return current


def _workspace_output(root: Path, path: Path | str) -> Path:
    relative = Path(path)
    if relative.is_absolute() or not relative.parts or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise PostRepairVisualReviewError(
            "review output must be workspace-relative and safe"
        )
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise PostRepairVisualReviewError(
                "review output must not traverse a symlink"
            )
    return root / relative


def _relative(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise PostRepairVisualReviewError("artifact must remain inside workspace") from exc


def _load_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PostRepairVisualReviewError(f"{label} must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise PostRepairVisualReviewError(f"{label} must be a JSON object")
    return payload


def _artifact(path: Path, *, root: Path, role: str | None = None) -> dict[str, str]:
    return {
        **({"role": role} if role is not None else {}),
        "path": _relative(path, root=root),
        "sha256": _sha256(path),
    }


def _fresh_binding_record(
    binding: dict[str, Any],
    key: str,
    *,
    workspace_root: Path,
    path_key: str = "path",
    hash_key: str = "sha256",
) -> Path:
    record = binding.get(key)
    if not isinstance(record, dict):
        raise PostRepairVisualReviewError(f"binding {key} record invalid")
    path = _workspace_file(
        workspace_root,
        str(record.get(path_key) or ""),
        label=f"binding {key}",
    )
    if record.get(hash_key) != _sha256(path):
        raise PostRepairVisualReviewError(f"binding {key} hash drift")
    return path


def _validate_binding_freshness(
    binding: dict[str, Any],
    *,
    workspace_root: Path,
) -> dict[str, Path]:
    if (
        binding.get("schema") != "figure-agent.adjudicated-repair-binding.v1"
        or binding.get("attribution_state") != "exact"
        or binding.get("publication_acceptance") != "not_claimed"
    ):
        raise PostRepairVisualReviewError("binding semantics invalid")
    paths = {
        "critique": _fresh_binding_record(
            binding, "critique", workspace_root=workspace_root
        ),
        "adjudication": _fresh_binding_record(
            binding, "adjudication", workspace_root=workspace_root
        ),
        "report": _fresh_binding_record(
            binding,
            "machine_finding",
            workspace_root=workspace_root,
            path_key="report_path",
            hash_key="report_sha256",
        ),
        "selector_registry": _fresh_binding_record(
            binding, "selector_registry", workspace_root=workspace_root
        ),
        "source": _fresh_binding_record(
            binding, "source", workspace_root=workspace_root
        ),
        "spec": _fresh_binding_record(
            binding, "spec", workspace_root=workspace_root
        ),
        "before_render": _fresh_binding_record(
            binding, "current_render", workspace_root=workspace_root
        ),
        "before_pdf": _fresh_binding_record(
            binding, "current_pdf", workspace_root=workspace_root
        ),
        "baseline_crop_manifest": _fresh_binding_record(
            binding, "crop_manifest", workspace_root=workspace_root
        ),
        "target_contract": _fresh_binding_record(
            binding, "target_contract", workspace_root=workspace_root
        ),
    }
    adjudication = critique_adjudication.load_adjudication(paths["adjudication"])
    critique_record = binding["critique"]
    finding_id = critique_record.get("finding_id")
    if (
        adjudication.get("fixture") != binding.get("fixture")
        or adjudication.get("source_critique_hash") != _sha256(paths["critique"])
        or binding["adjudication"].get("decision") != "apply"
    ):
        raise PostRepairVisualReviewError("binding adjudication lineage invalid")
    decisions = [
        item
        for item in adjudication.get("decisions", [])
        if isinstance(item, dict) and item.get("finding_id") == finding_id
    ]
    if len(decisions) != 1 or decisions[0].get("decision") != "apply":
        raise PostRepairVisualReviewError("binding adjudication apply decision invalid")
    evidence = decisions[0].get("repair_evidence")
    machine_finding = binding.get("machine_finding")
    selector_registry = binding.get("selector_registry")
    if (
        not isinstance(evidence, dict)
        or set(evidence)
        != {"report_path", "finding_id", "selector_registry_path"}
        or not isinstance(machine_finding, dict)
        or not isinstance(selector_registry, dict)
        or evidence.get("report_path") != machine_finding.get("report_path")
        or evidence.get("finding_id") != machine_finding.get("finding_id")
        or evidence.get("selector_registry_path") != selector_registry.get("path")
    ):
        raise PostRepairVisualReviewError("binding repair evidence lineage invalid")
    if paths["before_pdf"].stem != paths["before_render"].stem:
        raise PostRepairVisualReviewError("binding PDF/render generation mismatch")
    fixture = binding.get("fixture")
    if not isinstance(fixture, str) or not fixture:
        raise PostRepairVisualReviewError("binding fixture invalid")
    example_dir = workspace_root / "examples" / fixture
    report = _load_json(paths["report"], label="binding machine report")
    expected_render = paths["before_render"].relative_to(example_dir).as_posix()
    expected_pdf = paths["before_pdf"].relative_to(example_dir).as_posix()
    if (
        report.get("schema") != "figure-agent.text-collisions.v1"
        or report.get("fixture") != fixture
        or report.get("render_path") != expected_render
        or report.get("render_sha256") != _sha256(paths["before_render"])
        or report.get("render_pdf") != expected_pdf
        or report.get("render_pdf_sha256") != _sha256(paths["before_pdf"])
        or Path(expected_render).stem != Path(expected_pdf).stem
    ):
        raise PostRepairVisualReviewError("binding machine report lineage invalid")
    return paths


def _valid_geometry(item: dict[str, Any]) -> dict[str, list[int]] | None:
    bbox = item.get("bbox_px")
    if (
        isinstance(bbox, list)
        and len(bbox) == 4
        and all(isinstance(value, int) for value in bbox)
        and bbox[2] > bbox[0]
        and bbox[3] > bbox[1]
    ):
        return {"bbox_px": bbox}
    size = item.get("size_px")
    if (
        isinstance(size, list)
        and len(size) == 2
        and all(isinstance(value, int) and value > 0 for value in size)
    ):
        return {"size_px": size}
    return None


def _inspection_manifest(
    manifest_path: Path,
    *,
    fixture: str,
    verified_render: Path,
    crop_roles: dict[str, str],
    workspace_root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    manifest = _load_json(manifest_path, label="inspection crop manifest")
    if (
        manifest.get("schema") != CROP_MANIFEST_SCHEMA
        or manifest.get("fixture") != fixture
    ):
        raise PostRepairVisualReviewError("inspection crop manifest lineage invalid")
    example_dir = workspace_root / "examples" / fixture
    render_relative = Path(str(manifest.get("render_path") or ""))
    if render_relative.is_absolute() or not render_relative.parts or any(
        part in {"", ".", ".."} for part in render_relative.parts
    ):
        raise PostRepairVisualReviewError("inspection crop manifest render_path invalid")
    manifest_render = _workspace_file(
        workspace_root,
        (example_dir.relative_to(workspace_root) / render_relative).as_posix(),
        label="inspection manifest render",
    )
    if manifest_render != verified_render:
        raise PostRepairVisualReviewError(
            "inspection crop manifest is not bound to verified render"
        )
    crops = manifest.get("crops")
    required_ids = manifest.get("required_crop_ids")
    if not isinstance(crops, list) or any(not isinstance(item, dict) for item in crops):
        raise PostRepairVisualReviewError("inspection crop manifest crops invalid")
    if (
        not isinstance(required_ids, list)
        or any(not isinstance(item, str) or not item for item in required_ids)
        or len(set(required_ids)) != len(required_ids)
    ):
        raise PostRepairVisualReviewError("inspection crop manifest required ids invalid")
    crop_ids = [item.get("id") for item in crops]
    if (
        any(not isinstance(crop_id, str) or not crop_id for crop_id in crop_ids)
        or len(set(crop_ids)) != len(crop_ids)
    ):
        raise PostRepairVisualReviewError("inspection crop manifest ids invalid")
    if set(crop_roles) != CROP_ROLES or any(
        not isinstance(crop_id, str) or not crop_id for crop_id in crop_roles.values()
    ):
        raise PostRepairVisualReviewError("exact crop role mapping required")
    if crop_roles["target_crop"] == crop_roles["neighbor_crop"]:
        raise PostRepairVisualReviewError("target and neighbor crop ids must differ")
    crop_by_id = {item["id"]: item for item in crops}
    by_role: dict[str, dict[str, Any]] = {}
    for role, crop_id in crop_roles.items():
        item = crop_by_id.get(crop_id)
        if not isinstance(item, dict) or crop_id not in required_ids:
            raise PostRepairVisualReviewError("inspection crop id is not required")
        if item.get("kind") not in ROLE_KINDS[role]:
            raise PostRepairVisualReviewError("inspection crop role/kind mismatch")
        if item.get("source_path") != render_relative.as_posix():
            raise PostRepairVisualReviewError("inspection crop source_path drift")
        geometry = _valid_geometry(item)
        if geometry is None:
            raise PostRepairVisualReviewError("inspection crop geometry invalid")
        crop_relative = Path(str(item.get("path") or ""))
        if crop_relative.is_absolute() or not crop_relative.parts or any(
            part in {"", ".", ".."} for part in crop_relative.parts
        ):
            raise PostRepairVisualReviewError("inspection crop path invalid")
        crop_path = _workspace_file(
            workspace_root,
            (example_dir.relative_to(workspace_root) / crop_relative).as_posix(),
            label=f"{role} crop",
        )
        if item.get("sha256") != _sha256(crop_path):
            raise PostRepairVisualReviewError("inspection crop hash drift")
        by_role[role] = {
            "role": role,
            "crop_id": crop_id,
            "path": _relative(crop_path, root=workspace_root),
            "sha256": _sha256(crop_path),
            "source_path": _relative(verified_render, root=workspace_root),
            **geometry,
        }
    if set(by_role) != CROP_ROLES:
        raise PostRepairVisualReviewError("required inspection artifacts missing")
    return manifest, [by_role[role] for role in sorted(CROP_ROLES)]


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.startswith("sha256:")
        and len(value) == len("sha256:") + 64
        and all(character in "0123456789abcdef" for character in value[7:])
    )


def _validate_machine_verification_receipt(
    receipt: dict[str, Any],
    *,
    packet: dict[str, Any],
    workspace_root: Path,
) -> dict[str, Path]:
    if (
        receipt.get("schema") != authoring_repair_finalize.RECEIPT_SCHEMA
        or receipt.get("decision")
        != "materialized_machine_verified_human_review_pending"
        or receipt.get("post_render_verification") != "passed"
        or receipt.get("human_review") != "pending"
        or receipt.get("publication_acceptance") != "not_claimed"
        or receipt.get("recovery_required") is not False
        or receipt.get("packet_sha256") != packet.get("packet_sha256")
        or receipt.get("output_path") != packet.get("output_path")
    ):
        raise PostRepairVisualReviewError("machine verification receipt is not ready")
    source = _workspace_file(
        workspace_root,
        str(receipt.get("output_path") or ""),
        label="repaired source",
    )
    if receipt.get("output_sha256") != _sha256(source):
        raise PostRepairVisualReviewError("repaired source hash drift")
    build = source.parent / "build"
    external_compile = receipt.get("external_compile")
    required_compile_keys = {
        "command",
        "returncode",
        "stdout_sha256",
        "stderr_sha256",
        "strict_status",
        "detector_reports",
        "pdf",
        "png",
    }
    if (
        not isinstance(external_compile, dict)
        or set(external_compile) != required_compile_keys
        or external_compile.get("command")
        != ["bash", "scripts/compile.sh", receipt.get("output_path")]
        or external_compile.get("returncode") != 0
        or not _is_sha256(external_compile.get("stdout_sha256"))
        or not _is_sha256(external_compile.get("stderr_sha256"))
    ):
        raise PostRepairVisualReviewError("machine verification compile evidence invalid")

    strict_record = external_compile.get("strict_status")
    strict_path = build / "strict_status.json"
    if not isinstance(strict_record, dict) or strict_record != {
        **_artifact(strict_path, root=workspace_root),
        "schema": authoring_repair_finalize.STRICT_STATUS_SCHEMA,
        "state": "passed",
    }:
        raise PostRepairVisualReviewError("machine verification strict status invalid")
    strict_status = _load_json(strict_path, label="strict status")
    if strict_status != {
        "schema": authoring_repair_finalize.STRICT_STATUS_SCHEMA,
        "strict_requested": True,
        "detector_failed": False,
        "state": "passed",
    }:
        raise PostRepairVisualReviewError("machine verification strict status invalid")

    detector_records = external_compile.get("detector_reports")
    if (
        not isinstance(detector_records, dict)
        or set(detector_records)
        != set(authoring_repair_finalize.REQUIRED_DETECTOR_REPORTS)
    ):
        raise PostRepairVisualReviewError("machine verification detector reports invalid")
    for name, expected_schema in (
        authoring_repair_finalize.REQUIRED_DETECTOR_REPORTS.items()
    ):
        report_path = build / f"{name}.json"
        expected_record = {
            **_artifact(report_path, root=workspace_root),
            **({"schema": expected_schema} if expected_schema is not None else {}),
        }
        if detector_records.get(name) != expected_record:
            raise PostRepairVisualReviewError(
                "machine verification detector reports invalid"
            )
        report = _load_json(report_path, label=f"{name} detector report")
        if expected_schema is not None and report.get("schema") != expected_schema:
            raise PostRepairVisualReviewError(
                "machine verification detector reports invalid"
            )

    render_paths: dict[str, Path] = {"source": source}
    for kind in ("pdf", "png"):
        record = external_compile.get(kind)
        path = build / f"{source.stem}.{kind}"
        if not isinstance(record, dict) or record != _artifact(
            path, root=workspace_root
        ):
            raise PostRepairVisualReviewError(
                "machine verification render artifacts invalid"
            )
        render_paths[kind] = path
    return render_paths


def build_review_request(
    *,
    binding_path: Path,
    packet_path: Path,
    materialization_receipt_path: Path,
    crop_manifest_path: Path,
    crop_roles: dict[str, str],
    workspace_root: Path,
) -> dict[str, object]:
    """Build a fresh review request bound to machine-verified repair bytes."""
    workspace_root = workspace_root.resolve()
    binding_path = _workspace_file(workspace_root, binding_path, label="binding")
    packet_path = _workspace_file(workspace_root, packet_path, label="repair packet")
    materialization_receipt_path = _workspace_file(
        workspace_root,
        materialization_receipt_path,
        label="materialization receipt",
    )
    crop_manifest_path = _workspace_file(
        workspace_root,
        crop_manifest_path,
        label="inspection crop manifest",
    )
    binding = _load_json(binding_path, label="binding")
    packet = _load_json(packet_path, label="repair packet")
    receipt = _load_json(materialization_receipt_path, label="materialization receipt")
    if (
        binding.get("schema") != "figure-agent.adjudicated-repair-binding.v1"
        or binding.get("attribution_state") != "exact"
        or binding.get("publication_acceptance") != "not_claimed"
    ):
        raise PostRepairVisualReviewError("binding is not exact and non-accepting")
    binding_paths = _validate_binding_freshness(
        binding,
        workspace_root=workspace_root,
    )
    if (
        packet.get("schema") != "figure-agent.repair-execution-packet.v3"
        or packet.get("publication_acceptance") != "not_claimed"
        or packet.get("packet_sha256")
        != authoring_repair_packet.canonical_packet_sha256(packet)
    ):
        raise PostRepairVisualReviewError("repair packet is invalid")
    fixture = binding.get("fixture")
    if (
        not isinstance(fixture, str)
        or not fixture
        or packet.get("fixture") != fixture
        or receipt.get("fixture") != fixture
    ):
        raise PostRepairVisualReviewError("fixture lineage mismatch")
    binding_target = binding.get("target_contract")
    packet_target = packet.get("target_contract")
    if not isinstance(binding_target, dict) or packet_target != binding_target:
        raise PostRepairVisualReviewError("target contract lineage mismatch")
    verified_paths = _validate_machine_verification_receipt(
        receipt,
        packet=packet,
        workspace_root=workspace_root,
    )
    source = verified_paths["source"]
    render_pdf = verified_paths["pdf"]
    render = verified_paths["png"]
    _, artifacts = _inspection_manifest(
        crop_manifest_path,
        fixture=fixture,
        verified_render=render,
        crop_roles=crop_roles,
        workspace_root=workspace_root,
    )
    artifacts = [
        _artifact(render, root=workspace_root, role="full_render"),
        *artifacts,
    ]
    request: dict[str, Any] = {
        "schema": REQUEST_SCHEMA,
        "fixture": fixture,
        "binding": _artifact(binding_path, root=workspace_root),
        "repair_packet": {
            **_artifact(packet_path, root=workspace_root),
            "packet_sha256": packet.get("packet_sha256"),
        },
        "materialization_receipt": _artifact(
            materialization_receipt_path, root=workspace_root
        ),
        "repaired_source": _artifact(source, root=workspace_root),
        "before_render": _artifact(
            binding_paths["before_render"], root=workspace_root
        ),
        "render": _artifact(render, root=workspace_root),
        "render_pdf": _artifact(render_pdf, root=workspace_root),
        "crop_manifest": _artifact(crop_manifest_path, root=workspace_root),
        "crop_roles": dict(sorted(crop_roles.items())),
        "inspection_artifacts": artifacts,
        "required_checks": [
            "target_resolved",
            "no_new_local_defect",
            "unchanged_region_regression",
        ],
        "publication_acceptance": "not_claimed",
    }
    request["request_sha256"] = _canonical_hash(request, omitted="request_sha256")
    return request


def _validate_request_freshness(
    request: dict[str, Any], *, workspace_root: Path
) -> None:
    if request.get("schema") != REQUEST_SCHEMA:
        raise PostRepairVisualReviewError("review request schema invalid")
    if request.get("request_sha256") != _canonical_hash(
        request, omitted="request_sha256"
    ):
        raise PostRepairVisualReviewError("review request hash drift")
    if request.get("publication_acceptance") != "not_claimed":
        raise PostRepairVisualReviewError("publication acceptance must not be claimed")
    records: list[dict[str, Any]] = []
    for key in (
        "binding",
        "repair_packet",
        "materialization_receipt",
        "repaired_source",
        "before_render",
        "render",
        "render_pdf",
        "crop_manifest",
    ):
        value = request.get(key)
        if not isinstance(value, dict):
            raise PostRepairVisualReviewError("review request artifact invalid")
        records.append(value)
    artifacts = request.get("inspection_artifacts")
    if not isinstance(artifacts, list) or any(
        not isinstance(item, dict) for item in artifacts
    ):
        raise PostRepairVisualReviewError("review inspection artifacts invalid")
    roles = [item.get("role") for item in artifacts]
    if len(roles) != len(REQUIRED_ROLES) or set(roles) != REQUIRED_ROLES:
        raise PostRepairVisualReviewError("required inspection artifacts missing")
    if request.get("required_checks") != list(REQUIRED_VERDICTS):
        raise PostRepairVisualReviewError("required visual checks invalid")
    crop_roles = request.get("crop_roles")
    if not isinstance(crop_roles, dict):
        raise PostRepairVisualReviewError("review crop role mapping invalid")
    records.extend(artifacts)
    for record in records:
        path = _workspace_file(
            workspace_root, str(record.get("path") or ""), label="review artifact"
        )
        if record.get("sha256") != _sha256(path):
            raise PostRepairVisualReviewError("artifact hash drift")
    binding_record = request["binding"]
    binding_path = _workspace_file(
        workspace_root,
        str(binding_record.get("path") or ""),
        label="review binding",
    )
    binding = _load_json(binding_path, label="review binding")
    binding_paths = _validate_binding_freshness(
        binding, workspace_root=workspace_root
    )
    packet_record = request["repair_packet"]
    packet_path = _workspace_file(
        workspace_root,
        str(packet_record.get("path") or ""),
        label="review repair packet",
    )
    packet = _load_json(packet_path, label="review repair packet")
    receipt_record = request["materialization_receipt"]
    receipt_path = _workspace_file(
        workspace_root,
        str(receipt_record.get("path") or ""),
        label="review materialization receipt",
    )
    receipt = _load_json(receipt_path, label="review materialization receipt")
    fixture = request.get("fixture")
    if (
        not isinstance(fixture, str)
        or packet.get("schema") != "figure-agent.repair-execution-packet.v3"
        or packet.get("publication_acceptance") != "not_claimed"
        or receipt.get("schema")
        != "figure-agent.repair-materialization-receipt.v2"
        or receipt.get("decision")
        != "materialized_machine_verified_human_review_pending"
        or receipt.get("post_render_verification") != "passed"
        or receipt.get("publication_acceptance") != "not_claimed"
        or binding.get("fixture") != fixture
        or packet.get("fixture") != fixture
        or receipt.get("fixture") != fixture
        or packet.get("packet_sha256")
        != authoring_repair_packet.canonical_packet_sha256(packet)
        or packet_record.get("packet_sha256") != packet.get("packet_sha256")
        or receipt.get("packet_sha256") != packet.get("packet_sha256")
        or receipt.get("output_path") != packet.get("output_path")
        or binding.get("target_contract") != packet.get("target_contract")
    ):
        raise PostRepairVisualReviewError("review request lineage invalid")
    if request["repaired_source"].get("path") != receipt.get("output_path") or request[
        "repaired_source"
    ].get("sha256") != receipt.get("output_sha256"):
        raise PostRepairVisualReviewError("review repaired source lineage invalid")
    if request["before_render"] != _artifact(
        binding_paths["before_render"], root=workspace_root
    ):
        raise PostRepairVisualReviewError("review before-render lineage invalid")
    verified_paths = _validate_machine_verification_receipt(
        receipt,
        packet=packet,
        workspace_root=workspace_root,
    )
    if request["render"] != _artifact(
        verified_paths["png"], root=workspace_root
    ):
        raise PostRepairVisualReviewError("review render lineage invalid")
    if request["render_pdf"] != _artifact(
        verified_paths["pdf"], root=workspace_root
    ):
        raise PostRepairVisualReviewError("review PDF lineage invalid")
    render_path = _workspace_file(
        workspace_root,
        str(request["render"].get("path") or ""),
        label="review render",
    )
    manifest_path = _workspace_file(
        workspace_root,
        str(request["crop_manifest"].get("path") or ""),
        label="review crop manifest",
    )
    _, expected_artifacts = _inspection_manifest(
        manifest_path,
        fixture=fixture,
        verified_render=render_path,
        crop_roles=crop_roles,
        workspace_root=workspace_root,
    )
    expected_artifacts = [
        _artifact(render_path, root=workspace_root, role="full_render"),
        *expected_artifacts,
    ]
    if artifacts != expected_artifacts:
        raise PostRepairVisualReviewError("review inspection manifest binding invalid")


def _validate_execution_receipt(
    execution: object,
    *,
    request: dict[str, object],
    workspace_root: Path,
) -> bool:
    if execution is None:
        return False
    if not isinstance(execution, dict):
        raise PostRepairVisualReviewError("host review execution receipt invalid")
    actor = execution.get("actor")
    if (
        execution.get("schema") != EXECUTION_RECEIPT_SCHEMA
        or execution.get("request_sha256") != request.get("request_sha256")
        or not isinstance(actor, dict)
        or actor.get("kind") not in {"human", "model", "tool"}
        or not isinstance(actor.get("identity"), str)
        or not actor["identity"].strip()
        or not isinstance(actor.get("model_or_tool"), str)
        or not actor["model_or_tool"].strip()
    ):
        raise PostRepairVisualReviewError("host review execution receipt invalid")
    transcript = execution.get("transcript")
    if not isinstance(transcript, dict) or set(transcript) != {"path", "sha256"}:
        raise PostRepairVisualReviewError("host review transcript artifact invalid")
    transcript_path = _workspace_file(
        workspace_root,
        str(transcript.get("path") or ""),
        label="host review transcript",
    )
    if transcript.get("sha256") != _sha256(transcript_path):
        raise PostRepairVisualReviewError("host review transcript hash drift")
    expected_artifacts = [
        request.get("before_render"),
        *list(request.get("inspection_artifacts") or []),
    ]
    if execution.get("inspected_artifacts") != expected_artifacts:
        raise PostRepairVisualReviewError("execution receipt artifact lineage invalid")
    if execution.get("receipt_sha256") != _canonical_hash(
        execution, omitted="receipt_sha256"
    ):
        raise PostRepairVisualReviewError("execution receipt hash invalid")
    return True


def finalize_review_payload(
    request: dict[str, object],
    response: dict[str, object],
    *,
    workspace_root: Path,
) -> dict[str, object]:
    """Validate fresh host-vision evidence and emit a non-publication decision."""
    workspace_root = workspace_root.resolve()
    _validate_request_freshness(request, workspace_root=workspace_root)
    if response.get("schema") != RESPONSE_SCHEMA:
        raise PostRepairVisualReviewError("review response schema invalid")
    if response.get("request_sha256") != request.get("request_sha256"):
        raise PostRepairVisualReviewError("review response request hash mismatch")
    if response.get("publication_acceptance") != "not_claimed":
        raise PostRepairVisualReviewError("publication acceptance must not be claimed")
    reviewer = response.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise PostRepairVisualReviewError("reviewer must be non-empty")
    verdicts = response.get("verdicts")
    if not isinstance(verdicts, dict) or set(verdicts) != set(REQUIRED_VERDICTS):
        raise PostRepairVisualReviewError("three explicit verdicts are required")
    for key, allowed in REQUIRED_VERDICTS.items():
        if verdicts.get(key) not in allowed:
            raise PostRepairVisualReviewError(f"{key} verdict invalid")
    findings = response.get("findings")
    if not isinstance(findings, list) or any(
        not isinstance(item, dict) for item in findings
    ):
        raise PostRepairVisualReviewError("review findings must be a list of objects")
    expected_artifacts = request.get("inspection_artifacts")
    inspected_artifacts = response.get("inspected_artifacts")
    if inspected_artifacts != expected_artifacts:
        raise PostRepairVisualReviewError("required inspection artifacts were not inspected")
    if response.get("inspected_before_render") != request.get("before_render"):
        raise PostRepairVisualReviewError("before render was not inspected")
    has_execution_receipt = _validate_execution_receipt(
        response.get("execution_receipt"),
        request=request,
        workspace_root=workspace_root,
    )
    if not has_execution_receipt or "uncertain" in verdicts.values():
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
        "fixture": request.get("fixture"),
        "request_sha256": request.get("request_sha256"),
        "reviewer": reviewer.strip(),
        "verdicts": verdicts,
        "findings": findings,
        "execution_receipt": response.get("execution_receipt"),
        "decision": decision,
        "publication_acceptance": "not_claimed",
    }
    receipt["receipt_sha256"] = _canonical_hash(receipt, omitted="receipt_sha256")
    return receipt


def _write_once(
    path: Path,
    payload: dict[str, object],
    *,
    prepublish: Callable[[], dict[str, object]] | None = None,
) -> None:
    try:
        with repair_transaction.exclusive_lock(
            path.parent / ".post-repair-review.lock",
            owner="post_repair_visual_review",
        ):
            if path.exists() or path.is_symlink():
                raise PostRepairVisualReviewError("review output already exists")
            if prepublish is not None and prepublish() != payload:
                raise PostRepairVisualReviewError(
                    "review inputs drifted before publication"
                )
            repair_transaction.atomic_create_json(path, payload)
    except FileExistsError as exc:
        raise PostRepairVisualReviewError("review output already exists") from exc
    except repair_transaction.RepairTransactionError as exc:
        raise PostRepairVisualReviewError(
            "post-review transaction already active"
        ) from exc


def main(argv: list[str] | None = None, *, workspace_root: Path) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent authoring-repair-review")
    subparsers = parser.add_subparsers(dest="action", required=True)
    request_parser = subparsers.add_parser("request")
    request_parser.add_argument("--binding", required=True)
    request_parser.add_argument("--packet", required=True)
    request_parser.add_argument("--receipt", required=True)
    request_parser.add_argument("--crop-manifest", required=True)
    request_parser.add_argument(
        "--crop-role", action="append", required=True, metavar="ROLE=ID"
    )
    request_parser.add_argument("--out", required=True)
    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--request", required=True)
    finalize_parser.add_argument("--response", required=True)
    finalize_parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    workspace_root = workspace_root.resolve()
    try:
        if args.action == "request":
            crop_roles: dict[str, str] = {}
            for assignment in args.crop_role:
                role, separator, crop_id = assignment.partition("=")
                if not separator or role in crop_roles:
                    raise PostRepairVisualReviewError(
                        "crop roles must be unique ROLE=ID assignments"
                    )
                crop_roles[role] = crop_id
            def produce() -> dict[str, object]:
                return build_review_request(
                    binding_path=workspace_root / Path(args.binding),
                    packet_path=workspace_root / Path(args.packet),
                    materialization_receipt_path=workspace_root / Path(args.receipt),
                    crop_manifest_path=workspace_root / Path(args.crop_manifest),
                    crop_roles=crop_roles,
                    workspace_root=workspace_root,
                )
        else:
            def produce() -> dict[str, object]:
                request = _load_json(
                    _workspace_file(
                        workspace_root, args.request, label="review request"
                    ),
                    label="review request",
                )
                response = _load_json(
                    _workspace_file(
                        workspace_root, args.response, label="review response"
                    ),
                    label="review response",
                )
                return finalize_review_payload(
                    request, response, workspace_root=workspace_root
                )
        result = produce()
        output = _workspace_output(workspace_root, args.out)
        _write_once(output, result, prepublish=produce)
    except (OSError, UnicodeDecodeError, PostRepairVisualReviewError) as exc:
        print(f"fig-agent authoring-repair-review: {exc}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0
