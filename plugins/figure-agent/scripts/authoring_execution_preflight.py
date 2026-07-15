"""Preflight a pair of byte-bound authoring execution packets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import authoring_execution_packet

SCHEMA = "figure-agent.authoring-execution-preflight.v1"
INTERVENTION_FIELDS = ("shape_profile", "composition_profile")


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
    output_path = payload.get("output_path")
    repository_output_path = payload.get("repository_output_path")
    execution_cwd = payload.get("execution_cwd")
    if not all(
        isinstance(value, str) and value
        for value in (output_path, repository_output_path, execution_cwd)
    ):
        raise AuthoringExecutionPreflightError("packet output path invalid")
    expected_repository_output = (Path(execution_cwd) / Path(output_path)).as_posix()
    if repository_output_path != expected_repository_output:
        raise AuthoringExecutionPreflightError("repository output path drift")
    expected_output_instruction = (
        f"- Write exactly one new source to [{repository_output_path}]."
    )
    if prompt_bytes.decode("utf-8").count(expected_output_instruction) != 1:
        raise AuthoringExecutionPreflightError("prompt output path drift")
    try:
        authoring_execution_packet.validate_visual_asset_bindings(payload)
    except (authoring_execution_packet.AuthoringExecutionPacketError, OSError) as exc:
        raise AuthoringExecutionPreflightError(str(exc)) from exc
    return payload, prompt_path


def _equal_field(control: dict[str, Any], treatment: dict[str, Any], field: str) -> None:
    if control.get(field) != treatment.get(field):
        raise AuthoringExecutionPreflightError(f"{field} mismatch")


def _artifact_reference(packet: dict[str, Any], path: Path) -> str:
    return (Path(str(packet["output_path"])).parent / path.name).as_posix()


def _preflight_authoring_conditions(
    packet_paths: dict[str, Path],
) -> tuple[dict[str, dict[str, object]], str | None]:
    """Validate one equal-input authoring comparison before any model runs."""
    if len(packet_paths) < 2 or any(not name for name in packet_paths):
        raise AuthoringExecutionPreflightError("at least two named conditions are required")

    loaded = {
        name: _load_packet(packet_path)
        for name, packet_path in packet_paths.items()
    }
    baseline_name = next(iter(packet_paths))
    baseline, _ = loaded[baseline_name]
    intervention_fields: set[str] = set()
    for name, (packet, _) in loaded.items():
        if name == baseline_name:
            continue
        for field in (
            "model_id",
            "execution_cwd",
            "budget_contract",
            "blank_start",
            "mandatory_source_requirements",
            "style_lock_authoring_requirements",
            "allowed_repository_read_paths",
            "feedback_rounds",
            "manual_repairs",
            "forbidden_import_classes",
            "publication_acceptance",
        ):
            _equal_field(baseline, packet, field)
        baseline_context = baseline.get("context_pack")
        context = packet.get("context_pack")
        if not isinstance(baseline_context, dict) or not isinstance(context, dict):
            raise AuthoringExecutionPreflightError("context_pack invalid")
        if baseline_context.get("schema") != context.get("schema"):
            raise AuthoringExecutionPreflightError("context_pack schema mismatch")
        if baseline_context.get("base_sha256") != context.get("base_sha256"):
            raise AuthoringExecutionPreflightError("context_pack base_sha256 mismatch")
        intervention_fields.update(
            field
            for field in INTERVENTION_FIELDS
            if baseline.get(field) != packet.get(field)
        )

    if len(intervention_fields) > 1:
        raise AuthoringExecutionPreflightError(
            "multiple intervention fields differ: "
            + ", ".join(sorted(intervention_fields))
        )
    intervention_field = next(iter(intervention_fields), None)

    outputs = {packet.get("output_path") for packet, _ in loaded.values()}
    if len(outputs) != len(loaded) or None in outputs:
        raise AuthoringExecutionPreflightError("output_path must be disjoint")
    resolved_packets = [path.resolve() for path in packet_paths.values()]
    if len(set(resolved_packets)) != len(resolved_packets):
        raise AuthoringExecutionPreflightError("packet paths must be disjoint")
    resolved_prompts = [prompt.resolve() for _, prompt in loaded.values()]
    if len(set(resolved_prompts)) != len(resolved_prompts):
        raise AuthoringExecutionPreflightError("prompt paths must be disjoint")

    conditions = {
        name: {
            "packet_path": _artifact_reference(packet, packet_paths[name]),
            "packet_sha256": packet["packet_sha256"],
            "prompt_path": _artifact_reference(packet, prompt),
            "prompt_sha256": packet["prompt"]["sha256"],
            "output_path": packet["output_path"],
        }
        for name, (packet, prompt) in loaded.items()
    }
    return conditions, intervention_field


def preflight_authoring_pair(
    control_packet_path: Path,
    treatment_packet_path: Path,
) -> dict[str, object]:
    """Validate equal arm contracts and disjoint one-file write scopes."""
    conditions, intervention_field = _preflight_authoring_conditions(
        {"control": control_packet_path, "treatment": treatment_packet_path}
    )
    return {
        "schema": SCHEMA,
        "decision": "pass",
        "filesystem_read_isolation": "unavailable",
        "intervention_field": intervention_field,
        **conditions,
    }


def preflight_authoring_triplet(
    raw_packet_path: Path,
    verified_packet_path: Path,
    repaired_packet_path: Path,
) -> dict[str, object]:
    """Validate an equal-input raw/verified/repaired comparison preflight."""
    conditions, intervention_field = _preflight_authoring_conditions(
        {
            "raw": raw_packet_path,
            "verified": verified_packet_path,
            "repaired": repaired_packet_path,
        }
    )
    return {
        "schema": SCHEMA,
        "decision": "pass",
        "filesystem_read_isolation": "unavailable",
        "intervention_field": intervention_field,
        "conditions": conditions,
    }
