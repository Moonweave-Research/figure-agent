"""Bind actual authoring execution artifacts to an immutable receipt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import authoring_execution_packet

SCHEMA = "figure-agent.authoring-execution-receipt.v1"


class AuthoringExecutionReceiptError(ValueError):
    """Raised when runtime evidence does not match its declared packet."""


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _canonical_hash(payload: dict[str, object]) -> str:
    unhashed = {key: value for key, value in payload.items() if key != "receipt_sha256"}
    encoded = json.dumps(
        unhashed,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _regular_repo_file(workspace_root: Path, path: Path, *, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise AuthoringExecutionReceiptError(f"{label} must be a regular file")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(workspace_root.resolve()):
        raise AuthoringExecutionReceiptError(f"{label} must remain inside the workspace")
    current = workspace_root.resolve()
    relative = resolved.relative_to(workspace_root.resolve())
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise AuthoringExecutionReceiptError(f"{label} must not traverse a symlink")
    return resolved


def _load_packet(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != authoring_execution_packet.SCHEMA:
        raise AuthoringExecutionReceiptError("packet schema invalid")
    if payload.get("packet_sha256") != authoring_execution_packet.canonical_packet_sha256(
        payload
    ):
        raise AuthoringExecutionReceiptError("packet hash drift")
    return payload


def _expected_touched_files(packet: dict[str, Any]) -> list[str]:
    """Return the one-file write scope in repository-relative coordinates."""
    execution_cwd = Path(str(packet.get("execution_cwd", ".")))
    output_path = Path(str(packet["output_path"]))
    return [(execution_cwd / output_path).as_posix()]


def record_authoring_execution_receipt(
    *,
    workspace_root: Path,
    repository_root: Path | None = None,
    packet_path: Path,
    prompt_path: Path,
    transcript_path: Path,
    generated_source_path: Path,
    touched_files_path: Path,
    receipt_path: Path,
    actual_model_id: str,
    actual_token_usage: int | None,
    token_usage_unavailable_reason: str | None,
    forbidden_input_audit: str,
) -> dict[str, object]:
    """Validate actual runtime bytes and persist a one-write receipt."""
    workspace_root = workspace_root.resolve()
    repository_root = (repository_root or workspace_root).resolve()
    if not workspace_root.is_relative_to(repository_root):
        raise AuthoringExecutionReceiptError(
            "repository root must contain the Figure Agent workspace"
        )
    packet_path = _regular_repo_file(workspace_root, packet_path, label="packet")
    prompt_path = _regular_repo_file(workspace_root, prompt_path, label="prompt")
    transcript_path = _regular_repo_file(
        repository_root, transcript_path, label="transcript"
    )
    generated_source_path = _regular_repo_file(
        workspace_root, generated_source_path, label="generated source"
    )
    touched_files_path = _regular_repo_file(
        workspace_root, touched_files_path, label="touched files"
    )
    packet = _load_packet(packet_path)
    if actual_model_id != packet.get("model_id"):
        raise AuthoringExecutionReceiptError("model mismatch")
    prompt_bytes = prompt_path.read_bytes()
    prompt_record = packet.get("prompt")
    if (
        not isinstance(prompt_record, dict)
        or prompt_record.get("utf8") != prompt_bytes.decode("utf-8")
        or prompt_record.get("sha256") != _sha256_bytes(prompt_bytes)
    ):
        raise AuthoringExecutionReceiptError("prompt byte mismatch")
    expected_source = (workspace_root / str(packet.get("output_path"))).resolve(
        strict=False
    )
    if generated_source_path != expected_source:
        raise AuthoringExecutionReceiptError("generated source path mismatch")
    touched_files = json.loads(touched_files_path.read_text(encoding="utf-8"))
    expected_touched = _expected_touched_files(packet)
    if touched_files != expected_touched:
        raise AuthoringExecutionReceiptError("touched files differ from one-file scope")
    if actual_token_usage is not None:
        if (
            isinstance(actual_token_usage, bool)
            or actual_token_usage < 0
            or token_usage_unavailable_reason
        ):
            raise AuthoringExecutionReceiptError("token usage contract is ambiguous")
    elif not token_usage_unavailable_reason or not token_usage_unavailable_reason.strip():
        raise AuthoringExecutionReceiptError("token usage unavailable reason is required")
    if not forbidden_input_audit.strip():
        raise AuthoringExecutionReceiptError("forbidden input audit is required")
    if receipt_path.exists() or receipt_path.is_symlink():
        raise AuthoringExecutionReceiptError("receipt already exists")
    receipt_relative = receipt_path.resolve(strict=False).relative_to(workspace_root)
    attempt_parent = generated_source_path.parent
    if (
        receipt_path.resolve(strict=False).parent != attempt_parent
        or receipt_path.suffix != ".json"
    ):
        raise AuthoringExecutionReceiptError("receipt must be adjacent to generated source")
    receipt: dict[str, object] = {
        "schema": SCHEMA,
        "packet_path": packet_path.relative_to(workspace_root).as_posix(),
        "packet_sha256": _sha256_bytes(packet_path.read_bytes()),
        "declared_packet_sha256": packet["packet_sha256"],
        "prompt_path": prompt_path.relative_to(workspace_root).as_posix(),
        "prompt_sha256": _sha256_bytes(prompt_bytes),
        "transcript_root": (
            "workspace" if repository_root == workspace_root else "repository"
        ),
        "transcript_path": transcript_path.relative_to(repository_root).as_posix(),
        "transcript_sha256": _sha256_bytes(transcript_path.read_bytes()),
        "generated_source_path": generated_source_path.relative_to(
            workspace_root
        ).as_posix(),
        "generated_source_sha256": _sha256_bytes(generated_source_path.read_bytes()),
        "touched_files_path": touched_files_path.relative_to(workspace_root).as_posix(),
        "touched_files_sha256": _sha256_bytes(touched_files_path.read_bytes()),
        "touched_files": touched_files,
        "actual_model_id": actual_model_id,
        "actual_token_usage": actual_token_usage,
        "token_usage_unavailable_reason": token_usage_unavailable_reason,
        "feedback_rounds": packet["feedback_rounds"],
        "manual_repairs": packet["manual_repairs"],
        "filesystem_read_isolation": "unavailable",
        "forbidden_input_audit": forbidden_input_audit,
        "publication_acceptance": "not_claimed",
        "receipt_path": receipt_relative.as_posix(),
    }
    receipt["receipt_sha256"] = _canonical_hash(receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    persisted = json.loads(receipt_path.read_text(encoding="utf-8"))
    if persisted != receipt or persisted.get("receipt_sha256") != _canonical_hash(
        persisted
    ):
        raise AuthoringExecutionReceiptError("persisted receipt drift")
    return receipt
