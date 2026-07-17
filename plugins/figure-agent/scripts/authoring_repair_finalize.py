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


def _mapping_snapshot(path: Path, *, label: str) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise AuthoringRepairFinalizeError(f"{label} must be a regular file")
    try:
        data = path.read_bytes()
        payload = json.loads(data.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthoringRepairFinalizeError(f"{label} is invalid") from exc
    if not isinstance(payload, dict):
        raise AuthoringRepairFinalizeError(f"{label} is invalid")
    return payload, data


def _safe_workspace_path(root: Path, value: object, *, label: str) -> Path:
    relative = Path(str(value or ""))
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise AuthoringRepairFinalizeError(f"{label} must be workspace-relative and safe")
    return _lexical_workspace_path(
        root / relative,
        workspace_root=root,
        label=label,
    )


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


def _lexical_workspace_path(
    path: Path,
    *,
    workspace_root: Path,
    label: str,
) -> Path:
    lexical = Path(os.path.abspath(path))
    if not lexical.is_relative_to(workspace_root):
        raise AuthoringRepairFinalizeError(f"{label} must remain inside workspace")
    current = workspace_root
    for part in lexical.relative_to(workspace_root).parts:
        current = current / part
        if current.is_symlink():
            raise AuthoringRepairFinalizeError(f"{label} must not traverse a symlink")
    return lexical


def _artifact(path: Path, *, workspace_root: Path) -> dict[str, str]:
    if path.is_symlink() or not path.is_file():
        raise AuthoringRepairFinalizeError(f"strict compile artifact missing: {path.name}")
    return {
        "path": path.relative_to(workspace_root).as_posix(),
        "sha256": _sha256_bytes(path.read_bytes()),
    }


def _observed_artifact(
    path: Path,
    *,
    workspace_root: Path,
    expected_schema: str | None = None,
    expected_payload: dict[str, Any] | None = None,
    validate_json: bool = False,
) -> dict[str, str]:
    record = {"path": path.relative_to(workspace_root).as_posix()}
    if path.is_symlink() or (path.exists() and not path.is_file()):
        return {**record, "status": "invalid_file"}
    if not path.exists():
        return {**record, "status": "missing"}
    data = path.read_bytes()
    record["sha256"] = _sha256_bytes(data)
    if not validate_json and expected_schema is None and expected_payload is None:
        return {**record, "status": "present"}
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {**record, "status": "invalid_json"}
    if not isinstance(payload, dict):
        return {**record, "status": "invalid_json"}
    if expected_schema is not None and payload.get("schema") != expected_schema:
        return {**record, "status": "schema_mismatch"}
    if expected_payload is not None and payload != expected_payload:
        return {**record, "status": "not_passed"}
    return {**record, "status": "valid"}


def inspect_compile_evidence_manifest(
    *,
    build: Path,
    output: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    """Snapshot the exact post-compile artifacts, including failed evidence."""
    workspace_root = workspace_root.resolve()
    build = _lexical_workspace_path(
        build,
        workspace_root=workspace_root,
        label="verification build path",
    )
    output = _lexical_workspace_path(
        output,
        workspace_root=workspace_root,
        label="materialized output path",
    )
    strict_pass = {
        "schema": STRICT_STATUS_SCHEMA,
        "strict_requested": True,
        "detector_failed": False,
        "state": "passed",
    }
    return {
        "strict_status": _observed_artifact(
            build / "strict_status.json",
            workspace_root=workspace_root,
            expected_schema=STRICT_STATUS_SCHEMA,
            expected_payload=strict_pass,
        ),
        "detector_reports": {
            name: _observed_artifact(
                build / f"{name}.json",
                workspace_root=workspace_root,
                expected_schema=expected_schema,
                validate_json=True,
            )
            for name, expected_schema in REQUIRED_DETECTOR_REPORTS.items()
        },
        "pdf": _observed_artifact(
            build / f"{output.stem}.pdf", workspace_root=workspace_root
        ),
        "png": _observed_artifact(
            build / f"{output.stem}.png", workspace_root=workspace_root
        ),
    }


def derive_compile_failure_reason(
    *,
    returncode: int,
    evidence_manifest: dict[str, Any],
) -> str | None:
    """Derive the one fail-closed reason represented by compile evidence."""
    if not isinstance(returncode, int) or isinstance(returncode, bool):
        raise AuthoringRepairFinalizeError("compile returncode is invalid")
    if set(evidence_manifest) != {
        "strict_status",
        "detector_reports",
        "pdf",
        "png",
    }:
        raise AuthoringRepairFinalizeError("compile evidence manifest is invalid")
    strict_status = evidence_manifest.get("strict_status")
    detector_reports = evidence_manifest.get("detector_reports")
    pdf = evidence_manifest.get("pdf")
    png = evidence_manifest.get("png")
    if (
        not isinstance(strict_status, dict)
        or not isinstance(detector_reports, dict)
        or set(detector_reports) != set(REQUIRED_DETECTOR_REPORTS)
        or not isinstance(pdf, dict)
        or not isinstance(png, dict)
    ):
        raise AuthoringRepairFinalizeError("compile evidence manifest is invalid")
    if returncode != 0:
        return "strict_compile_nonzero"
    strict_state = strict_status.get("status")
    if strict_state in {"missing", "invalid_file", "invalid_json", "schema_mismatch"}:
        return "strict_status_missing_or_invalid"
    if strict_state == "not_passed":
        return "strict_status_not_passed"
    if strict_state != "valid":
        raise AuthoringRepairFinalizeError("compile evidence manifest is invalid")
    if any(
        not isinstance(record, dict) or record.get("status") != "valid"
        for record in detector_reports.values()
    ):
        return "detector_report_missing_or_invalid"
    if pdf.get("status") != "present" or png.get("status") != "present":
        return "render_artifact_missing"
    return None


def validate_failed_compile_evidence(
    receipt: dict[str, Any],
    *,
    workspace_root: Path,
) -> dict[str, Any]:
    """Revalidate an exact live failed-compile manifest for rollback."""
    workspace_root = workspace_root.resolve()
    external_compile = receipt.get("external_compile")
    if not isinstance(external_compile, dict):
        raise AuthoringRepairFinalizeError(
            "failed compile evidence is inconsistent"
        )
    recorded_manifest = external_compile.get("evidence_manifest")
    if not isinstance(recorded_manifest, dict):
        raise AuthoringRepairFinalizeError(
            "failed compile evidence is inconsistent"
        )
    output_relative = Path(str(receipt.get("output_path") or ""))
    if (
        output_relative.is_absolute()
        or not output_relative.parts
        or any(part in {"", ".", ".."} for part in output_relative.parts)
    ):
        raise AuthoringRepairFinalizeError(
            "materialized output path must be workspace-relative and safe"
        )
    output = _lexical_workspace_path(
        workspace_root / output_relative,
        workspace_root=workspace_root,
        label="materialized output path",
    )
    observed_manifest = inspect_compile_evidence_manifest(
        build=output.parent / "build",
        output=output,
        workspace_root=workspace_root,
    )
    if recorded_manifest != observed_manifest:
        raise AuthoringRepairFinalizeError("failed compile evidence hash drift")
    failure_reason = derive_compile_failure_reason(
        returncode=external_compile.get("returncode"),
        evidence_manifest=observed_manifest,
    )
    if (
        failure_reason is None
        or external_compile.get("failure_reason") != failure_reason
    ):
        raise AuthoringRepairFinalizeError(
            "failed compile evidence is inconsistent"
        )
    return observed_manifest


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
    evidence_manifest: dict[str, Any],
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
            "evidence_manifest": evidence_manifest,
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
    allow_legacy_packet: bool = False,
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

    packet, packet_bytes = _mapping_snapshot(packet_path, label="repair packet")
    receipt, receipt_bytes = _mapping_snapshot(
        receipt_path, label="materialization receipt"
    )
    authorization_record, authorization_bytes = _mapping_snapshot(
        authorization_path, label="materialization authorization"
    )
    if not authoring_repair_packet.is_supported_packet_schema(packet.get("schema")):
        raise AuthoringRepairFinalizeError("repair packet schema invalid")
    if packet.get("packet_sha256") != authoring_repair_packet.canonical_packet_sha256(
        packet
    ):
        raise AuthoringRepairFinalizeError("repair packet hash drift")
    try:
        authoring_repair_packet.validate_bound_packet_authority(
            packet,
            workspace_root,
            allow_legacy_packet=allow_legacy_packet,
        )
    except authoring_repair_packet.RepairExecutionPacketError as exc:
        raise AuthoringRepairFinalizeError(
            f"repair packet authority invalid: {exc}"
        ) from exc
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
    if authoring_repair_packet.is_attempt_local_packet_schema(packet.get("schema")):
        binding_record = packet.get("attempt_local_repair_binding")
        if not isinstance(binding_record, dict):
            raise AuthoringRepairFinalizeError("attempt-local packet binding invalid")
        binding_relative = Path(str(binding_record.get("path") or ""))
        expected_packet_root = binding_relative.parent
        expected_prefix = (
            Path("examples") / fixture / "review" / "closed-loop"
        )
        if (
            binding_relative.is_absolute()
            or binding_relative.name != "attempt-local-repair-binding.json"
            or expected_packet_root.name != "repair-packet"
            or expected_packet_root.parent.parent != expected_prefix
            or packet_path.parent.relative_to(workspace_root) != expected_packet_root
        ):
            raise AuthoringRepairFinalizeError(
                "packet and receipt must be inside the exact attempt-local repair packet"
            )
    else:
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
                packet_schema=str(packet.get("schema") or ""),
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

    with repair_transaction.recoverable_exclusive_lock(
        output.parent / ".materialization.lock",
        owner=repair_transaction.MATERIALIZATION_LOCK_OWNER,
    ):
        if packet_path.read_bytes() != packet_bytes:
            raise AuthoringRepairFinalizeError(
                "repair packet drifted during finalization"
            )
        if receipt_path.read_bytes() != receipt_bytes:
            raise AuthoringRepairFinalizeError(
                "receipt drifted during finalization"
            )
        if authorization_path.read_bytes() != authorization_bytes:
            raise AuthoringRepairFinalizeError(
                "authorization drifted during finalization"
            )
        try:
            authoring_repair_packet.validate_bound_packet_authority(
                packet,
                workspace_root,
                allow_legacy_packet=allow_legacy_packet,
            )
        except authoring_repair_packet.RepairExecutionPacketError as exc:
            raise AuthoringRepairFinalizeError(
                f"repair packet authority invalid: {exc}"
            ) from exc
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
        evidence_manifest = inspect_compile_evidence_manifest(
            build=build,
            output=output,
            workspace_root=workspace_root,
        )
        failure_reason = derive_compile_failure_reason(
            returncode=completed.returncode,
            evidence_manifest=evidence_manifest,
        )
        if failure_reason is not None:
            return _failed_receipt(
                receipt,
                compile_evidence=compile_evidence,
                evidence_manifest=evidence_manifest,
                failure_reason=failure_reason,
                receipt_path=receipt_path,
            )
        strict_status_path = build / "strict_status.json"
        detector_reports = _detector_reports(build, workspace_root=workspace_root)
        pdf = _artifact(
            build / f"{output.stem}.pdf", workspace_root=workspace_root
        )
        png = _artifact(
            build / f"{output.stem}.png", workspace_root=workspace_root
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
