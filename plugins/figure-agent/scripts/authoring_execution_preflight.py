"""Preflight a pair of byte-bound authoring execution packets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import authoring_execution_packet

SCHEMA = "figure-agent.authoring-execution-preflight.v1"


class AuthoringExecutionPreflightError(ValueError):
    """Raised when a two-arm authoring contract is not execution-safe."""


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _prompt_path(packet_path: Path) -> Path:
    stem = packet_path.stem
    if stem.endswith("_packet"):
        return packet_path.with_name(stem.removesuffix("_packet") + "_prompt.md")
    if stem == "packet":
        return packet_path.with_name("prompt.md")
    raise AuthoringExecutionPreflightError("packet filename must identify its prompt")


def _load_packet(packet_path: Path) -> tuple[dict[str, Any], Path]:
    if packet_path.is_symlink() or not packet_path.is_file():
        raise AuthoringExecutionPreflightError("packet must be a regular file")
    payload = json.loads(packet_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != authoring_execution_packet.SCHEMA:
        raise AuthoringExecutionPreflightError("packet schema invalid")
    if payload.get("packet_sha256") != authoring_execution_packet.canonical_packet_sha256(
        payload
    ):
        raise AuthoringExecutionPreflightError("packet hash drift")
    prompt_path = _prompt_path(packet_path)
    if prompt_path.is_symlink() or not prompt_path.is_file():
        raise AuthoringExecutionPreflightError("prompt must be a regular file")
    prompt_bytes = prompt_path.read_bytes()
    prompt_record = payload.get("prompt")
    if (
        not isinstance(prompt_record, dict)
        or prompt_record.get("utf8") != prompt_bytes.decode("utf-8")
        or prompt_record.get("sha256") != _sha256_bytes(prompt_bytes)
    ):
        raise AuthoringExecutionPreflightError("prompt byte drift")
    try:
        authoring_execution_packet._validate_prompt_requirements(
            prompt_bytes.decode("utf-8")
        )
    except authoring_execution_packet.AuthoringExecutionPacketError as exc:
        raise AuthoringExecutionPreflightError(str(exc)) from exc
    return payload, prompt_path


def _equal_field(control: dict[str, Any], treatment: dict[str, Any], field: str) -> None:
    if control.get(field) != treatment.get(field):
        raise AuthoringExecutionPreflightError(f"{field} mismatch")


def _artifact_reference(packet: dict[str, Any], path: Path) -> str:
    return (Path(str(packet["output_path"])).parent / path.name).as_posix()


def preflight_authoring_pair(
    control_packet_path: Path,
    treatment_packet_path: Path,
) -> dict[str, object]:
    """Validate equal arm contracts and disjoint one-file write scopes."""
    control, control_prompt = _load_packet(control_packet_path)
    treatment, treatment_prompt = _load_packet(treatment_packet_path)
    for field in (
        "model_id",
        "execution_cwd",
        "budget_contract",
        "blank_start",
        "mandatory_source_requirements",
        "style_lock_authoring_requirements",
        "feedback_rounds",
        "manual_repairs",
        "forbidden_import_classes",
        "publication_acceptance",
    ):
        _equal_field(control, treatment, field)
    control_context = control.get("context_pack")
    treatment_context = treatment.get("context_pack")
    if not isinstance(control_context, dict) or not isinstance(treatment_context, dict):
        raise AuthoringExecutionPreflightError("context_pack invalid")
    if control_context.get("schema") != treatment_context.get("schema"):
        raise AuthoringExecutionPreflightError("context_pack schema mismatch")
    if control_context.get("base_sha256") != treatment_context.get("base_sha256"):
        raise AuthoringExecutionPreflightError("context_pack base_sha256 mismatch")
    output_paths = {control.get("output_path"), treatment.get("output_path")}
    if len(output_paths) != 2 or None in output_paths:
        raise AuthoringExecutionPreflightError("output_path must be disjoint")
    if control_packet_path.resolve() == treatment_packet_path.resolve():
        raise AuthoringExecutionPreflightError("packet paths must be disjoint")
    if control_prompt.resolve() == treatment_prompt.resolve():
        raise AuthoringExecutionPreflightError("prompt paths must be disjoint")
    return {
        "schema": SCHEMA,
        "decision": "pass",
        "filesystem_read_isolation": "unavailable",
        "control": {
            "packet_path": _artifact_reference(control, control_packet_path),
            "packet_sha256": control["packet_sha256"],
            "prompt_path": _artifact_reference(control, control_prompt),
            "prompt_sha256": control["prompt"]["sha256"],
            "output_path": control["output_path"],
        },
        "treatment": {
            "packet_path": _artifact_reference(treatment, treatment_packet_path),
            "packet_sha256": treatment["packet_sha256"],
            "prompt_path": _artifact_reference(treatment, treatment_prompt),
            "prompt_sha256": treatment["prompt"]["sha256"],
            "output_path": treatment["output_path"],
        },
    }
