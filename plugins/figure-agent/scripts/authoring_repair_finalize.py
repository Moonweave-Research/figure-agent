"""Fail-closed post-render finalization for additive authoring repairs."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import authoring_repair_packet
import fixture_identity
import human_decision_record
import repair_transaction

RECEIPT_SCHEMA = "figure-agent.repair-materialization-receipt.v2"
STRICT_STATUS_SCHEMA = "figure-agent.strict-status.v1"
REPAIR_ATTEMPT = re.compile(r"execution-repair-v[1-9][0-9]*")
REQUIRED_DETECTOR_REPORTS = {
    "collisions": "figure-agent.text-collisions.v1",
    "visual_clash": None,
    "text_boundary_clash": "figure-agent.text-boundary-clash.v1",
    "label_path_proximity": "figure-agent.label-path-proximity.v1",
    "undeclared_geometry": "figure-agent.undeclared-geometry.v1",
    "label_hyphenation": "figure-agent.label-hyphenation.v1",
    "semantic_assertions": "figure-agent.semantic-assertions.v1",
    "vector_clearance": "figure-agent.vector-clearance.v1",
    "tex_assertions": "figure-agent.tex-assertions.v1",
    "physics_grounding": None,
}


class AuthoringRepairFinalizeError(ValueError):
    """Raised when repair verification cannot safely advance the receipt."""


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _mapping(path: Path, *, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise AuthoringRepairFinalizeError(f"{label} must be a regular file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthoringRepairFinalizeError(f"{label} is invalid") from exc
    if not isinstance(payload, dict):
        raise AuthoringRepairFinalizeError(f"{label} is invalid")
    return payload


def _safe_workspace_path(root: Path, value: object, *, label: str) -> Path:
    relative = Path(str(value or ""))
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise AuthoringRepairFinalizeError(f"{label} must be workspace-relative and safe")
    resolved = (root / relative).resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise AuthoringRepairFinalizeError(f"{label} must remain inside workspace")
    return resolved


def _evidence_path(path: Path, *, workspace_root: Path) -> Path:
    lexical = Path(os.path.abspath(path))
    if not lexical.is_relative_to(workspace_root):
        raise AuthoringRepairFinalizeError(
            "packet and receipt must remain inside workspace"
        )
    current = workspace_root
    for part in lexical.relative_to(workspace_root).parts:
        current = current / part
        if current.is_symlink():
            raise AuthoringRepairFinalizeError(
                "packet and receipt paths must not be symlinks"
            )
    return lexical


def _artifact(path: Path, *, workspace_root: Path) -> dict[str, str]:
    if path.is_symlink() or not path.is_file():
        raise AuthoringRepairFinalizeError(f"strict compile artifact missing: {path.name}")
    return {
        "path": path.relative_to(workspace_root).as_posix(),
        "sha256": _sha256_bytes(path.read_bytes()),
    }


def _detector_reports(build: Path, *, workspace_root: Path) -> dict[str, dict[str, str]]:
    reports: dict[str, dict[str, str]] = {}
    for name, expected_schema in REQUIRED_DETECTOR_REPORTS.items():
        path = build / f"{name}.json"
        payload = _mapping(path, label=f"{name} detector report")
        if expected_schema is not None and payload.get("schema") != expected_schema:
            raise AuthoringRepairFinalizeError(f"{name} detector report schema invalid")
        reports[name] = {
            **_artifact(path, workspace_root=workspace_root),
            **({"schema": expected_schema} if expected_schema is not None else {}),
        }
    return reports


def _failed_receipt(
    receipt: dict[str, Any],
    *,
    compile_evidence: dict[str, Any],
    failure_reason: str,
    receipt_path: Path,
) -> dict[str, Any]:
    failed = {
        **receipt,
        "decision": "materialized_verification_failed",
        "post_render_verification": "failed",
        "external_compile": {
            **compile_evidence,
            "failure_reason": failure_reason,
        },
        "human_review": "pending",
        "publication_acceptance": "not_claimed",
        "recovery_required": False,
    }
    repair_transaction.atomic_write_json(receipt_path, failed)
    return failed


def finalize_materialized_candidate(
    *,
    packet_path: Path,
    receipt_path: Path,
    authorization_path: Path,
    workspace_root: Path,
    plugin_root: Path,
) -> dict[str, Any]:
    """Run one strict compile and advance only explicit passed evidence."""
    workspace_root = workspace_root.resolve()
    plugin_root = plugin_root.resolve()
    packet_path = _evidence_path(packet_path, workspace_root=workspace_root)
    receipt_path = _evidence_path(receipt_path, workspace_root=workspace_root)
    authorization_path = _evidence_path(
        authorization_path, workspace_root=workspace_root
    )
    if not (
        packet_path.parent == receipt_path.parent == authorization_path.parent
    ):
        raise AuthoringRepairFinalizeError(
            "packet, receipt, and authorization must be adjacent"
        )

    packet = _mapping(packet_path, label="repair packet")
    receipt = _mapping(receipt_path, label="materialization receipt")
    authorization_record = _mapping(
        authorization_path, label="materialization authorization"
    )
    if packet.get("schema") != authoring_repair_packet.SCHEMA:
        raise AuthoringRepairFinalizeError("repair packet schema invalid")
    if packet.get("packet_sha256") != authoring_repair_packet.canonical_packet_sha256(
        packet
    ):
        raise AuthoringRepairFinalizeError("repair packet hash drift")
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise AuthoringRepairFinalizeError("materialization receipt schema invalid")
    decision = receipt.get("decision")
    recovery = decision == "materialized_verification_prepared"
    if decision not in {
        "materialized_verification_pending",
        "materialized_verification_prepared",
    }:
        raise AuthoringRepairFinalizeError("materialization receipt is not verification-pending")
    if receipt.get("recovery_required") is not recovery:
        raise AuthoringRepairFinalizeError("materialization recovery state is inconsistent")

    fixture = str(packet.get("fixture") or "")
    try:
        fixture_identity.validate_fixture_name(fixture)
    except ValueError as exc:
        raise AuthoringRepairFinalizeError("repair fixture invalid") from exc
    attempt_relative = packet_path.parent.relative_to(workspace_root)
    expected_attempt_root = Path("examples") / fixture / "review" / "failure-first"
    if (
        attempt_relative.parent != expected_attempt_root
        or REPAIR_ATTEMPT.fullmatch(attempt_relative.name) is None
    ):
        raise AuthoringRepairFinalizeError(
            "packet and receipt must be inside the exact execution-repair attempt"
        )

    output = _safe_workspace_path(
        workspace_root, receipt.get("output_path"), label="materialized output path"
    )
    if output.parent != receipt_path.parent or output.is_symlink() or not output.is_file():
        raise AuthoringRepairFinalizeError("materialized output must be adjacent and regular")
    output_sha256 = _sha256_bytes(output.read_bytes())
    authorization_receipt = receipt.get("authorization")
    if (
        receipt.get("fixture") != packet.get("fixture")
        or receipt.get("packet_sha256") != packet.get("packet_sha256")
        or receipt.get("output_path") != packet.get("output_path")
        or receipt.get("output_sha256") != output_sha256
        or not isinstance(authorization_receipt, dict)
    ):
        raise AuthoringRepairFinalizeError("materialization evidence binding mismatch")
    preview_sha256 = authoring_repair_packet.canonical_materialization_preview_sha256(
        receipt
    )
    try:
        normalized_authorization = (
            human_decision_record.validate_additive_materialization_authorization(
                authorization_record,
                fixture=fixture,
                packet_sha256=str(packet.get("packet_sha256") or ""),
                output_path=str(packet.get("output_path") or ""),
                output_sha256=output_sha256,
                preview_sha256=preview_sha256,
            )
        )
    except human_decision_record.HumanDecisionRecordError as exc:
        raise AuthoringRepairFinalizeError(
            "materialization authorization provenance mismatch"
        ) from exc
    expected_authorization_receipt = {
        "reviewer": normalized_authorization["reviewer"],
        "record_sha256": _sha256_bytes(_canonical_json_bytes(authorization_record)),
        "authorized_packet_sha256": normalized_authorization[
            "authorized_packet_sha256"
        ],
        "authorized_output_path": normalized_authorization["authorized_output_path"],
        "authorized_output_sha256": normalized_authorization[
            "authorized_output_sha256"
        ],
        "authorized_preview_sha256": normalized_authorization[
            "authorized_preview_sha256"
        ],
    }
    if (
        receipt.get("preview_sha256") != preview_sha256
        or authorization_receipt != expected_authorization_receipt
    ):
        raise AuthoringRepairFinalizeError(
            "materialization authorization provenance mismatch"
        )

    compile_script = plugin_root / "scripts" / "compile.sh"
    if compile_script.is_symlink() or not compile_script.is_file():
        raise AuthoringRepairFinalizeError("compile script missing")
    env = os.environ.copy()
    env["FIGURE_AGENT_STRICT"] = "1"
    env["FIGURE_AGENT_FIXTURE_NAME"] = str(packet.get("fixture") or "")
    env["FIGURE_AGENT_LIVE_REPAIR_VERIFY"] = "1"
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace_root)
    build = output.parent / "build"

    with repair_transaction.exclusive_lock(
        output.parent / ".materialization.lock",
        owner="authoring_repair_finalize",
    ):
        if _sha256_bytes(output.read_bytes()) != output_sha256:
            raise AuthoringRepairFinalizeError("materialized output hash drift")
        if recovery:
            prepared_compile = receipt.get("external_compile")
            if (
                not isinstance(prepared_compile, dict)
                or prepared_compile.get("state") != "prepared"
                or prepared_compile.get("candidate_sha256") != output_sha256
                or prepared_compile.get("build_path")
                != build.relative_to(workspace_root).as_posix()
            ):
                raise AuthoringRepairFinalizeError(
                    "verification recovery evidence is invalid"
                )
            if build.is_symlink() or (build.exists() and not build.is_dir()):
                raise AuthoringRepairFinalizeError(
                    "verification recovery build path is invalid"
                )
            if build.is_dir():
                shutil.rmtree(build)
        elif build.exists() or build.is_symlink():
            raise AuthoringRepairFinalizeError(
                "verification build directory must be absent for a clean run"
            )
        prepared = {
            **receipt,
            "decision": "materialized_verification_prepared",
            "post_render_verification": "pending",
            "external_compile": {
                "state": "prepared",
                "candidate_sha256": output_sha256,
                "build_path": build.relative_to(workspace_root).as_posix(),
            },
            "human_review": "pending",
            "publication_acceptance": "not_claimed",
            "recovery_required": True,
        }
        repair_transaction.atomic_write_json(receipt_path, prepared)
        receipt = prepared
        completed = subprocess.run(
            ["bash", str(compile_script), str(output)],
            cwd=plugin_root,
            env=env,
            capture_output=True,
            check=False,
        )
        if _sha256_bytes(output.read_bytes()) != output_sha256:
            raise AuthoringRepairFinalizeError("materialized output changed during compile")
        compile_evidence: dict[str, Any] = {
            "command": ["bash", "scripts/compile.sh", receipt["output_path"]],
            "returncode": completed.returncode,
            "stdout_sha256": _sha256_bytes(completed.stdout),
            "stderr_sha256": _sha256_bytes(completed.stderr),
        }
        if completed.returncode != 0:
            return _failed_receipt(
                receipt,
                compile_evidence=compile_evidence,
                failure_reason="strict_compile_nonzero",
                receipt_path=receipt_path,
            )
        strict_status_path = build / "strict_status.json"
        try:
            strict_status = _mapping(strict_status_path, label="strict status")
        except AuthoringRepairFinalizeError:
            return _failed_receipt(
                receipt,
                compile_evidence=compile_evidence,
                failure_reason="strict_status_missing_or_invalid",
                receipt_path=receipt_path,
            )
        if strict_status != {
            "schema": STRICT_STATUS_SCHEMA,
            "strict_requested": True,
            "detector_failed": False,
            "state": "passed",
        }:
            return _failed_receipt(
                receipt,
                compile_evidence=compile_evidence,
                failure_reason="strict_status_not_passed",
                receipt_path=receipt_path,
            )
        try:
            detector_reports = _detector_reports(
                build, workspace_root=workspace_root
            )
        except AuthoringRepairFinalizeError:
            return _failed_receipt(
                receipt,
                compile_evidence=compile_evidence,
                failure_reason="detector_report_missing_or_invalid",
                receipt_path=receipt_path,
            )
        try:
            pdf = _artifact(
                build / f"{output.stem}.pdf", workspace_root=workspace_root
            )
            png = _artifact(
                build / f"{output.stem}.png", workspace_root=workspace_root
            )
        except AuthoringRepairFinalizeError:
            return _failed_receipt(
                receipt,
                compile_evidence=compile_evidence,
                failure_reason="render_artifact_missing",
                receipt_path=receipt_path,
            )
        finalized = {
            **receipt,
            "decision": "materialized_machine_verified_human_review_pending",
            "post_render_verification": "passed",
            "external_compile": {
                **compile_evidence,
                "strict_status": {
                    **_artifact(strict_status_path, workspace_root=workspace_root),
                    "schema": STRICT_STATUS_SCHEMA,
                    "state": "passed",
                },
                "detector_reports": detector_reports,
                "pdf": pdf,
                "png": png,
            },
            "human_review": "pending",
            "publication_acceptance": "not_claimed",
            "recovery_required": False,
        }
        repair_transaction.atomic_write_json(receipt_path, finalized)
        return finalized
