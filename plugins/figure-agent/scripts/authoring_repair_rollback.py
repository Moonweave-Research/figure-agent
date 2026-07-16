"""Hash-guarded rollback for a failed additive authoring repair."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
from pathlib import Path
from typing import Any

import authoring_repair_finalize
import authoring_repair_packet
import human_decision_record
import repair_transaction

RECEIPT_SCHEMA = "figure-agent.repair-materialization-receipt.v2"
FAILED_DECISION = "materialized_verification_failed"
PREPARED_DECISION = "materialized_rollback_prepared"
ROLLED_BACK_DECISION = "materialized_rolled_back_after_verification_failure"
ROLLBACK_STRATEGY = "delete_materialized_output_if_hash_matches"


class AuthoringRepairRollbackError(ValueError):
    """Raised when a failed materialization cannot be rolled back safely."""


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _workspace_file(root: Path, path: Path, *, label: str) -> Path:
    lexical = Path(os.path.abspath(path))
    if not lexical.is_relative_to(root):
        raise AuthoringRepairRollbackError(f"{label} must remain inside workspace")
    current = root
    for part in lexical.relative_to(root).parts:
        current = current / part
        if current.is_symlink():
            raise AuthoringRepairRollbackError(f"{label} must not traverse a symlink")
    if not lexical.is_file():
        raise AuthoringRepairRollbackError(f"{label} must be a regular file")
    return lexical


def _load_snapshot(path: Path, *, label: str) -> tuple[dict[str, Any], bytes]:
    data = path.read_bytes()
    try:
        payload = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthoringRepairRollbackError(f"{label} is invalid") from exc
    if not isinstance(payload, dict):
        raise AuthoringRepairRollbackError(f"{label} is invalid")
    return payload, data


def _safe_output(root: Path, value: object, *, parent: Path) -> Path:
    relative = Path(str(value or ""))
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise AuthoringRepairRollbackError("rollback output path is invalid")
    output = Path(os.path.abspath(root / relative))
    if not output.is_relative_to(root) or output.parent != parent:
        raise AuthoringRepairRollbackError("rollback output path is invalid")
    return output


def _entry_identity(parent_fd: int, name: str) -> os.stat_result:
    return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)


def _entry_identity_or_none(parent_fd: int, name: str) -> os.stat_result | None:
    try:
        return _entry_identity(parent_fd, name)
    except FileNotFoundError:
        return None


def _reserve_quarantine(output: Path) -> str:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    parent_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    parent_flags |= getattr(os, "O_NOFOLLOW", 0)
    parent_fd = os.open(output.parent, parent_flags)
    try:
        while True:
            name = f".{output.name}.rollback-{secrets.token_hex(16)}"
            try:
                fd = os.open(name, flags, 0o600, dir_fd=parent_fd)
            except FileExistsError:
                continue
            os.close(fd)
            os.fsync(parent_fd)
            return name
    finally:
        os.close(parent_fd)


def _quarantine_name(output: Path, value: object) -> str:
    name = str(value or "")
    prefix = f".{output.name}.rollback-"
    token = name.removeprefix(prefix)
    if (
        not name.startswith(prefix)
        or Path(name).name != name
        or len(token) != 32
        or any(character not in "0123456789abcdef" for character in token)
    ):
        raise AuthoringRepairRollbackError("rollback quarantine path is invalid")
    return name


def _preserve_or_restore_quarantine(
    parent_fd: int, quarantine_name: str, output_name: str
) -> None:
    if _entry_identity_or_none(parent_fd, output_name) is not None:
        return
    try:
        os.link(
            quarantine_name,
            output_name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
            follow_symlinks=False,
        )
    except OSError:
        return
    os.fsync(parent_fd)


def _unlink_hash_bound_output(
    output: Path,
    expected_sha256: str,
    *,
    quarantine_name: str,
    missing_ok: bool,
) -> None:
    parent_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    parent_flags |= getattr(os, "O_NOFOLLOW", 0)
    file_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    file_flags |= getattr(os, "O_NONBLOCK", 0)
    parent_fd = os.open(output.parent, parent_flags)
    try:
        output_entry = _entry_identity_or_none(parent_fd, output.name)
        quarantine_entry = _entry_identity_or_none(parent_fd, quarantine_name)
        if quarantine_entry is None:
            if output_entry is None:
                if missing_ok:
                    return
                raise AuthoringRepairRollbackError(
                    "materialized output identity drift"
                )
            os.rename(
                output.name,
                quarantine_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            os.fsync(parent_fd)
        elif (
            stat.S_ISREG(quarantine_entry.st_mode)
            and quarantine_entry.st_size == 0
            and output_entry is not None
        ):
            os.replace(
                output.name,
                quarantine_name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
            )
            os.fsync(parent_fd)
        try:
            output_fd = os.open(quarantine_name, file_flags, dir_fd=parent_fd)
        except FileNotFoundError:
            if missing_ok:
                return
            raise AuthoringRepairRollbackError(
                "materialized output identity drift"
            ) from None
        except OSError as exc:
            _preserve_or_restore_quarantine(
                parent_fd, quarantine_name, output.name
            )
            raise AuthoringRepairRollbackError(
                "materialized output identity drift"
            ) from exc
        try:
            opened = os.fstat(output_fd)
            if not stat.S_ISREG(opened.st_mode):
                _preserve_or_restore_quarantine(
                    parent_fd, quarantine_name, output.name
                )
                raise AuthoringRepairRollbackError(
                    "materialized output must be regular"
                )
            digest = hashlib.sha256()
            while chunk := os.read(output_fd, 1024 * 1024):
                digest.update(chunk)
            if "sha256:" + digest.hexdigest() != expected_sha256:
                _preserve_or_restore_quarantine(
                    parent_fd, quarantine_name, output.name
                )
                raise AuthoringRepairRollbackError("materialized output hash drift")
            current = _entry_identity_or_none(parent_fd, quarantine_name)
            if current is None or (current.st_dev, current.st_ino) != (
                opened.st_dev,
                opened.st_ino,
            ):
                _preserve_or_restore_quarantine(
                    parent_fd, quarantine_name, output.name
                )
                raise AuthoringRepairRollbackError(
                    "materialized output identity drift"
                )
            if _entry_identity_or_none(parent_fd, output.name) is not None:
                raise AuthoringRepairRollbackError(
                    "materialized output identity drift"
                )
            os.unlink(quarantine_name, dir_fd=parent_fd)
            os.fsync(parent_fd)
            if _entry_identity_or_none(parent_fd, output.name) is not None:
                raise AuthoringRepairRollbackError(
                    "materialized output identity drift"
                )
        finally:
            os.close(output_fd)
    finally:
        os.close(parent_fd)


def _validate_authority(
    *,
    packet: dict[str, Any],
    receipt: dict[str, Any],
    authorization: dict[str, Any],
    output: Path,
    workspace_root: Path,
    allow_legacy_packet: bool,
) -> None:
    if not authoring_repair_packet.is_supported_packet_schema(packet.get("schema")):
        raise AuthoringRepairRollbackError("repair packet schema invalid")
    if packet.get("packet_sha256") != authoring_repair_packet.canonical_packet_sha256(
        packet
    ):
        raise AuthoringRepairRollbackError("repair packet hash drift")
    try:
        authoring_repair_packet.validate_bound_packet_authority(
            packet,
            workspace_root,
            allow_legacy_packet=allow_legacy_packet,
        )
    except authoring_repair_packet.RepairExecutionPacketError as exc:
        raise AuthoringRepairRollbackError(
            f"repair packet authority invalid: {exc}"
        ) from exc
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise AuthoringRepairRollbackError("materialization receipt schema invalid")
    rollback = receipt.get("rollback")
    expected_rollback = {
        "strategy": ROLLBACK_STRATEGY,
        "pre_transaction_state": "absent",
        "output_path": receipt.get("output_path"),
        "output_sha256": receipt.get("output_sha256"),
    }
    if not isinstance(rollback, dict) or {
        key: rollback.get(key) for key in expected_rollback
    } != expected_rollback:
        raise AuthoringRepairRollbackError("rollback authority is invalid")
    if receipt.get("decision") not in {FAILED_DECISION, PREPARED_DECISION}:
        raise AuthoringRepairRollbackError("receipt is not rollback-eligible")
    if receipt.get("post_render_verification") != "failed":
        raise AuthoringRepairRollbackError("receipt is not a failed verification")
    if output.is_symlink():
        raise AuthoringRepairRollbackError("materialized output must not be a symlink")
    try:
        authoring_repair_finalize.validate_failed_compile_evidence(
            receipt,
            workspace_root=workspace_root,
        )
    except authoring_repair_finalize.AuthoringRepairFinalizeError as exc:
        raise AuthoringRepairRollbackError(str(exc)) from exc
    if (
        receipt.get("fixture") != packet.get("fixture")
        or receipt.get("packet_sha256") != packet.get("packet_sha256")
        or receipt.get("output_path") != packet.get("output_path")
        or rollback.get("output_path") != packet.get("output_path")
    ):
        raise AuthoringRepairRollbackError("materialization evidence binding mismatch")
    preview_sha256 = authoring_repair_packet.canonical_materialization_preview_sha256(
        receipt
    )
    try:
        normalized = human_decision_record.validate_additive_materialization_authorization(
            authorization,
            fixture=str(packet.get("fixture") or ""),
            packet_schema=str(packet.get("schema") or ""),
            packet_sha256=str(packet.get("packet_sha256") or ""),
            output_path=str(packet.get("output_path") or ""),
            output_sha256=str(receipt.get("output_sha256") or ""),
            preview_sha256=preview_sha256,
        )
    except human_decision_record.HumanDecisionRecordError as exc:
        raise AuthoringRepairRollbackError(
            "materialization authorization provenance mismatch"
        ) from exc
    expected_authorization = {
        "reviewer": normalized["reviewer"],
        "record_sha256": _sha256_bytes(_canonical_json_bytes(authorization)),
        "authorized_packet_sha256": normalized["authorized_packet_sha256"],
        "authorized_output_path": normalized["authorized_output_path"],
        "authorized_output_sha256": normalized["authorized_output_sha256"],
        "authorized_preview_sha256": normalized["authorized_preview_sha256"],
    }
    if (
        receipt.get("preview_sha256") != preview_sha256
        or receipt.get("authorization") != expected_authorization
    ):
        raise AuthoringRepairRollbackError(
            "materialization authorization provenance mismatch"
        )
    if output.exists():
        if not output.is_file():
            raise AuthoringRepairRollbackError("materialized output must be regular")
        if _sha256_bytes(output.read_bytes()) != receipt.get("output_sha256"):
            raise AuthoringRepairRollbackError("materialized output hash drift")
    elif receipt.get("decision") != PREPARED_DECISION:
        raise AuthoringRepairRollbackError("materialized output is missing")
    if receipt.get("decision") == PREPARED_DECISION:
        if (
            receipt.get("recovery_required") is not True
            or rollback.get("status") != "pending"
        ):
            raise AuthoringRepairRollbackError("rollback recovery state is invalid")
        _quarantine_name(output, rollback.get("quarantine_name"))
    elif rollback.get("quarantine_name") is not None:
        raise AuthoringRepairRollbackError("rollback recovery state is invalid")
    elif receipt.get("recovery_required") is not False:
        raise AuthoringRepairRollbackError("rollback recovery state is invalid")


def rollback_failed_materialized_candidate(
    *,
    packet_path: Path,
    receipt_path: Path,
    authorization_path: Path,
    workspace_root: Path,
    allow_legacy_packet: bool = False,
) -> dict[str, Any]:
    """Delete only the authorized failed output while retaining render evidence."""
    workspace_root = workspace_root.resolve()
    packet_path = _workspace_file(workspace_root, packet_path, label="repair packet")
    receipt_path = _workspace_file(
        workspace_root, receipt_path, label="materialization receipt"
    )
    authorization_path = _workspace_file(
        workspace_root, authorization_path, label="materialization authorization"
    )
    if not (
        packet_path.parent == receipt_path.parent == authorization_path.parent
    ):
        raise AuthoringRepairRollbackError(
            "packet, receipt, and authorization must be adjacent"
        )
    packet, packet_bytes = _load_snapshot(packet_path, label="repair packet")
    receipt, receipt_bytes = _load_snapshot(
        receipt_path, label="materialization receipt"
    )
    authorization, authorization_bytes = _load_snapshot(
        authorization_path, label="materialization authorization"
    )
    output = _safe_output(
        workspace_root, receipt.get("output_path"), parent=receipt_path.parent
    )
    _validate_authority(
        packet=packet,
        receipt=receipt,
        authorization=authorization,
        output=output,
        workspace_root=workspace_root,
        allow_legacy_packet=allow_legacy_packet,
    )

    try:
        with repair_transaction.recoverable_exclusive_lock(
            receipt_path.parent / ".materialization.lock",
            owner=repair_transaction.MATERIALIZATION_LOCK_OWNER,
        ):
            if packet_path.read_bytes() != packet_bytes:
                raise AuthoringRepairRollbackError("repair packet drifted during rollback")
            if receipt_path.read_bytes() != receipt_bytes:
                raise AuthoringRepairRollbackError("receipt drifted during rollback")
            if authorization_path.read_bytes() != authorization_bytes:
                raise AuthoringRepairRollbackError(
                    "authorization drifted during rollback"
                )
            _validate_authority(
                packet=packet,
                receipt=receipt,
                authorization=authorization,
                output=output,
                workspace_root=workspace_root,
                allow_legacy_packet=allow_legacy_packet,
            )
            prepared = receipt
            if receipt["decision"] == FAILED_DECISION:
                quarantine_name = _reserve_quarantine(output)
                prepared = {
                    **receipt,
                    "decision": PREPARED_DECISION,
                    "rollback": {
                        **receipt["rollback"],
                        "status": "pending",
                        "quarantine_name": quarantine_name,
                    },
                    "recovery_required": True,
                }
                repair_transaction.atomic_write_json(receipt_path, prepared)
            quarantine_name = _quarantine_name(
                output, prepared["rollback"].get("quarantine_name")
            )
            _unlink_hash_bound_output(
                output,
                prepared["output_sha256"],
                quarantine_name=quarantine_name,
                missing_ok=receipt["decision"] == PREPARED_DECISION,
            )
            completed = {
                **prepared,
                "decision": ROLLED_BACK_DECISION,
                "rollback": {**prepared["rollback"], "status": "completed"},
                "recovery_required": False,
                "publication_acceptance": "not_claimed",
            }
            repair_transaction.atomic_write_json(receipt_path, completed)
            return completed
    except repair_transaction.RepairTransactionError as exc:
        raise AuthoringRepairRollbackError(
            "materialization transaction already active"
        ) from exc
