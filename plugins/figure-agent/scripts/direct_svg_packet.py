"""Validate isolated input packets for clean-room direct-SVG experiments."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "figure-agent.direct-svg-packet.v1"
PANELS = {"C", "F"}
DENIED_SOURCE_FAMILIES = {
    "tex",
    "whole_figure_svg",
    "candidate_patch",
    "experience_log",
    "illustration_grammar",
}
TARGET_ROLES = {"panel_c_target_crop", "panel_f_target_crop"}
REQUIRED_INPUT_ROLES = {"semantic_packet", "licensed_font"}
EXPECTED_BUDGETS = {
    "utility": {"cycles": 3, "wall_minutes_per_panel": 30},
    "ceiling": {"cycles": 8, "wall_minutes_per_panel": 120},
}
MODEL_CONTRACT_KEYS = {
    "provider",
    "model",
    "snapshot",
    "reasoning",
    "prompt_paths",
    "tools",
    "token_cap",
    "compute_cap",
}


class DirectSvgPacketError(ValueError):
    """Raised when a clean-room packet violates its declared boundary."""


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DirectSvgPacketError(f"{field}_invalid")
    return value


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _validate_budgets(value: Any) -> None:
    if value != EXPECTED_BUDGETS:
        raise DirectSvgPacketError("budget_contract_invalid")


def _validate_model_contract(value: Any) -> None:
    contract = _mapping(value, "model_contract")
    if not MODEL_CONTRACT_KEYS.issubset(contract):
        raise DirectSvgPacketError("model_contract_incomplete")
    if not isinstance(contract["prompt_paths"], list) or not isinstance(
        contract["tools"], list
    ):
        raise DirectSvgPacketError("model_contract_invalid")


def _validate_font_contract(packet: dict[str, Any], inputs: list[dict[str, Any]]) -> None:
    font = _mapping(packet.get("font"), "font_contract")
    if not isinstance(font.get("license"), str) or not font["license"]:
        raise DirectSvgPacketError("font_license_required")
    font_inputs = [item for item in inputs if item.get("role") == "licensed_font"]
    if len(font_inputs) != 1 or font.get("sha256") != font_inputs[0].get("sha256"):
        raise DirectSvgPacketError("font_hash_mismatch")


def validate_packet(path: Path) -> dict[str, Any]:
    """Validate packet structure and every allowed input path and hash."""
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise DirectSvgPacketError("packet_invalid") from exc
    packet = _mapping(loaded, "packet")
    root = path.parent.resolve()

    if packet.get("schema") != SCHEMA:
        raise DirectSvgPacketError("unsupported_schema")
    test_kind = packet.get("test_kind")
    if test_kind not in {"reconstruction", "synthesis"}:
        raise DirectSvgPacketError("invalid_test_kind")
    if set(packet.get("panels") or []) != PANELS:
        raise DirectSvgPacketError("panels_must_be_C_and_F")
    if set(packet.get("denied_source_families") or []) != DENIED_SOURCE_FAMILIES:
        raise DirectSvgPacketError("denied_source_families_incomplete")
    if packet.get("publication_acceptance") != "not_claimed":
        raise DirectSvgPacketError("publication_acceptance_must_not_be_claimed")

    raw_inputs = packet.get("allowed_inputs")
    if not isinstance(raw_inputs, list):
        raise DirectSvgPacketError("allowed_inputs_invalid")
    inputs = [_mapping(item, "allowed_input") for item in raw_inputs]
    roles = [item.get("role") for item in inputs]
    if any(not isinstance(role, str) or not role for role in roles):
        raise DirectSvgPacketError("input_role_invalid")
    if len(roles) != len(set(roles)):
        raise DirectSvgPacketError("input_role_duplicate")
    role_set = set(roles)
    if not REQUIRED_INPUT_ROLES.issubset(role_set):
        raise DirectSvgPacketError("required_input_missing")
    if test_kind == "reconstruction" and not TARGET_ROLES.issubset(role_set):
        raise DirectSvgPacketError("target_crop_required")
    forbidden_synthesis_roles = TARGET_ROLES | {
        role for role in role_set if "geometry" in role or "target" in role
    }
    if test_kind == "synthesis" and role_set & forbidden_synthesis_roles:
        raise DirectSvgPacketError("target_crop_forbidden")

    for item in inputs:
        raw_path = item.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            raise DirectSvgPacketError("input_path_invalid")
        relative = Path(raw_path)
        candidate = (root / relative).resolve()
        if relative.is_absolute() or not candidate.is_relative_to(root):
            raise DirectSvgPacketError("unsafe_input_path")
        if candidate.is_symlink() or not candidate.is_file():
            raise DirectSvgPacketError("input_missing")
        if item.get("sha256") != _sha256(candidate):
            raise DirectSvgPacketError("input_hash_mismatch")

    _validate_budgets(packet.get("budgets"))
    _validate_model_contract(packet.get("model_contract"))
    _validate_font_contract(packet, inputs)
    return packet
