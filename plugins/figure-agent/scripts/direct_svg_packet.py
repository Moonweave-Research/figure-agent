"""Validate isolated input packets for clean-room direct-SVG experiments."""

from __future__ import annotations

import hashlib
import re
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
EXPECTED_INPUT_ROLES = {
    "reconstruction": REQUIRED_INPUT_ROLES | TARGET_ROLES,
    "synthesis": REQUIRED_INPUT_ROLES,
}
EXPECTED_OUTPUT_ROOTS = {
    "reconstruction": "runs/test-a",
    "synthesis": "runs/test-b",
}
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
COMMON_PACKET_KEYS = {
    "schema",
    "test_kind",
    "panels",
    "denied_source_families",
    "allowed_inputs",
    "budgets",
    "model_contract",
    "font",
    "output_root",
    "path_base",
    "runnable",
    "blocked_reason",
    "publication_acceptance",
}
ALLOWED_INPUT_KEYS = {"role", "path", "sha256"}
BUDGET_KEYS = {"utility", "ceiling"}
BUDGET_TIER_KEYS = {"cycles", "wall_minutes_per_panel"}
FONT_CONTRACT_KEYS = {"role", "license", "sha256"}
SYNTHESIS_ISOLATION_DECLARATIONS = {
    "reference_pixels_available",
    "reference_hashes_available",
    "geometry_derivatives_available",
    "test_a_history_available",
    "test_a_outputs_available",
}
SYNTHESIS_LEAKAGE_CONCEPTS = {
    "target",
    "reference",
    "geometry",
    "testahistory",
    "testaoutput",
}


class DirectSvgPacketError(ValueError):
    """Raised when a clean-room packet violates its declared boundary."""


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DirectSvgPacketError(f"{field}_invalid")
    return value


def _validate_exact_keys(
    value: dict[str, Any],
    expected: set[str],
    *,
    unknown_error: str,
    incomplete_error: str,
) -> None:
    keys = set(value)
    if keys - expected:
        raise DirectSvgPacketError(unknown_error)
    if expected - keys:
        raise DirectSvgPacketError(incomplete_error)


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _validate_budgets(value: Any) -> None:
    budgets = _mapping(value, "budget_contract")
    _validate_exact_keys(
        budgets,
        BUDGET_KEYS,
        unknown_error="budget_unknown_field",
        incomplete_error="budget_contract_invalid",
    )
    for tier in BUDGET_KEYS:
        tier_contract = _mapping(budgets[tier], "budget_contract")
        _validate_exact_keys(
            tier_contract,
            BUDGET_TIER_KEYS,
            unknown_error="budget_unknown_field",
            incomplete_error="budget_contract_invalid",
        )
    if budgets != EXPECTED_BUDGETS:
        raise DirectSvgPacketError("budget_contract_invalid")


def _validate_model_contract(value: Any) -> None:
    contract = _mapping(value, "model_contract")
    _validate_exact_keys(
        contract,
        MODEL_CONTRACT_KEYS,
        unknown_error="model_contract_unknown_field",
        incomplete_error="model_contract_incomplete",
    )
    prompt_paths = contract["prompt_paths"]
    if not isinstance(prompt_paths, list):
        raise DirectSvgPacketError("prompt_paths_invalid")
    if prompt_paths:
        raise DirectSvgPacketError("prompt_paths_must_be_empty")
    if not isinstance(contract["tools"], list):
        raise DirectSvgPacketError("model_contract_invalid")


def _is_exact_unique_string_list(value: Any, expected: set[str]) -> bool:
    return (
        isinstance(value, list)
        and len(value) == len(expected)
        and all(isinstance(item, str) for item in value)
        and len(set(value)) == len(value)
        and set(value) == expected
    )


def _validate_font_contract(packet: dict[str, Any], inputs: list[dict[str, Any]]) -> None:
    font = _mapping(packet.get("font"), "font_contract")
    _validate_exact_keys(
        font,
        FONT_CONTRACT_KEYS,
        unknown_error="font_contract_unknown_field",
        incomplete_error="font_contract_incomplete",
    )
    if not isinstance(font.get("license"), str) or not font["license"]:
        raise DirectSvgPacketError("font_license_required")
    font_inputs = [item for item in inputs if item.get("role") == "licensed_font"]
    if len(font_inputs) != 1 or font.get("sha256") != font_inputs[0].get("sha256"):
        raise DirectSvgPacketError("font_hash_mismatch")


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _contains_synthesis_leakage(value: str) -> bool:
    normalized = _normalized(value)
    return any(concept in normalized for concept in SYNTHESIS_LEAKAGE_CONCEPTS)


def _string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _string_values(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _string_values(item)]
    return []


def _validate_synthesis_isolation(packet: dict[str, Any]) -> None:
    def inspect(value: Any) -> None:
        if isinstance(value, dict):
            for raw_key, nested in value.items():
                key = str(raw_key)
                if key not in SYNTHESIS_ISOLATION_DECLARATIONS:
                    if _contains_synthesis_leakage(key):
                        raise DirectSvgPacketError("synthesis_source_leakage")
                    normalized_key = _normalized(key)
                    if normalized_key.endswith(("path", "paths", "role", "roles")):
                        if any(
                            _contains_synthesis_leakage(item)
                            for item in _string_values(nested)
                        ):
                            raise DirectSvgPacketError("synthesis_source_leakage")
                inspect(nested)
        elif isinstance(value, list):
            for item in value:
                inspect(item)

    inspect(packet)


def validate_packet(path: Path) -> dict[str, Any]:
    """Validate packet structure and every allowed input path and hash."""
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise DirectSvgPacketError("packet_invalid") from exc
    packet = _mapping(loaded, "packet")
    packet_root = path.parent.resolve()
    path_base = packet.get("path_base", "packet_root")
    if path_base == "packet_root":
        root = packet_root
    elif path_base == "fixture_root":
        root = packet_root.parent
    else:
        raise DirectSvgPacketError("path_base_invalid")

    if packet.get("schema") != SCHEMA:
        raise DirectSvgPacketError("unsupported_schema")
    test_kind = packet.get("test_kind")
    if test_kind not in {"reconstruction", "synthesis"}:
        raise DirectSvgPacketError("invalid_test_kind")
    packet_keys = COMMON_PACKET_KEYS
    if test_kind == "synthesis":
        packet_keys = packet_keys | SYNTHESIS_ISOLATION_DECLARATIONS
    if set(packet) - packet_keys:
        raise DirectSvgPacketError("packet_unknown_field")
    if test_kind == "synthesis" and not SYNTHESIS_ISOLATION_DECLARATIONS.issubset(
        packet
    ):
        raise DirectSvgPacketError("synthesis_isolation_declaration_required")
    _validate_exact_keys(
        packet,
        packet_keys,
        unknown_error="packet_unknown_field",
        incomplete_error="packet_incomplete",
    )
    if not _is_exact_unique_string_list(packet.get("panels"), PANELS):
        raise DirectSvgPacketError("panels_must_be_unique_C_and_F")
    if not _is_exact_unique_string_list(
        packet.get("denied_source_families"), DENIED_SOURCE_FAMILIES
    ):
        raise DirectSvgPacketError("denied_source_families_must_be_unique_complete")
    if packet.get("publication_acceptance") != "not_claimed":
        raise DirectSvgPacketError("publication_acceptance_must_not_be_claimed")
    if packet.get("output_root") != EXPECTED_OUTPUT_ROOTS[test_kind]:
        raise DirectSvgPacketError("output_root_invalid")
    if packet.get("runnable") is not True:
        raise DirectSvgPacketError("packet_not_runnable")
    if packet.get("blocked_reason") is not None:
        raise DirectSvgPacketError("packet_blocked")
    if test_kind == "synthesis" and any(
        packet.get(key) is not False for key in SYNTHESIS_ISOLATION_DECLARATIONS
    ):
        raise DirectSvgPacketError("synthesis_isolation_declaration_required")

    raw_inputs = packet.get("allowed_inputs")
    if not isinstance(raw_inputs, list):
        raise DirectSvgPacketError("allowed_inputs_invalid")
    inputs = [_mapping(item, "allowed_input") for item in raw_inputs]
    for item in inputs:
        _validate_exact_keys(
            item,
            ALLOWED_INPUT_KEYS,
            unknown_error="allowed_input_unknown_field",
            incomplete_error="allowed_input_incomplete",
        )
    roles = [item.get("role") for item in inputs]
    if any(not isinstance(role, str) or not role for role in roles):
        raise DirectSvgPacketError("input_role_invalid")
    if len(roles) != len(set(roles)):
        raise DirectSvgPacketError("input_role_duplicate")
    role_set = set(roles)
    if test_kind == "reconstruction" and not TARGET_ROLES.issubset(role_set):
        raise DirectSvgPacketError("target_crop_required")
    if test_kind == "synthesis" and role_set & TARGET_ROLES:
        raise DirectSvgPacketError("target_crop_forbidden")
    if role_set != EXPECTED_INPUT_ROLES[test_kind]:
        raise DirectSvgPacketError("input_roles_invalid")
    if test_kind == "synthesis":
        _validate_synthesis_isolation(packet)

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
