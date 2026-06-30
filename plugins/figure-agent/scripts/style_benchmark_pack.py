"""Load and validate style benchmark candidate packs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import fixture_identity
import runtime_paths
import yaml

SCHEMA = "figure-agent.style-benchmark-candidate-pack.v1"
DEFAULT_PACK_SET = "2026-06-30-wave-c"
REQUIRED_CANDIDATE_SLOTS = frozenset(
    {
        "current_style",
        "restrained_tikz_refinement",
        "editorial_redesign",
        "svg_polish_handoff",
    }
)
MUTATION_BOUNDARIES = frozenset(
    {
        "no_source_mutation",
        "source_mutation_requires_separate_approval",
        "svg_artifact_mutation_requires_separate_approval",
    }
)
SAFETY_FALSE_KEYS = frozenset(
    {
        "source_mutation",
        "accepted_state_mutation",
        "release_state_mutation",
        "generated_export_mutation",
        "golden_mutation",
        "svg_polish_default",
    }
)


class StyleBenchmarkPackError(ValueError):
    """Raised when a style benchmark pack is malformed or leaves plugin bounds."""


def _as_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise StyleBenchmarkPackError(f"{key}_invalid")
    return value


def _as_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise StyleBenchmarkPackError(f"{key}_invalid")
    return list(value)


def _plugin_local_path(plugin_root: Path, raw_path: str, *, label: str) -> Path:
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise StyleBenchmarkPackError(f"{label}_path_escape")
    path = plugin_root / relative
    try:
        path.resolve().relative_to(plugin_root.resolve())
    except ValueError as exc:
        raise StyleBenchmarkPackError(f"{label}_path_escape") from exc
    for parent in [path, *path.parents]:
        if parent == plugin_root.parent:
            break
        if parent.is_symlink():
            raise StyleBenchmarkPackError(f"{label}_path_symlink")
    return path


def _resolve_pack_path(
    plugin_root: Path,
    fixture: str,
    *,
    pack_path: Path | None,
) -> tuple[Path, str]:
    if pack_path is None:
        relative = (
            Path("docs")
            / "style-benchmark-packs"
            / DEFAULT_PACK_SET
            / f"{fixture}.json"
        )
        return plugin_root / relative, relative.as_posix()
    if pack_path.is_absolute():
        try:
            relative = pack_path.resolve().relative_to(plugin_root.resolve())
        except ValueError as exc:
            raise StyleBenchmarkPackError("pack_path_escape") from exc
        return pack_path, relative.as_posix()
    return _plugin_local_path(plugin_root, pack_path.as_posix(), label="pack"), pack_path.as_posix()


def _load_yaml_mapping(path: Path, *, label: str) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise StyleBenchmarkPackError(f"{label}_yaml_invalid")
    return raw


def _validate_linked_files(
    plugin_root: Path,
    payload: dict[str, Any],
) -> tuple[dict[str, str], dict[str, Any], dict[str, Any]]:
    linked: dict[str, str] = {}
    for label in (
        "source_decision_packet",
        "source_decision_record",
        "benchmark_contract",
        "aesthetic_intent",
    ):
        raw = payload.get(label)
        if not isinstance(raw, str):
            raise StyleBenchmarkPackError(f"{label}_invalid")
        path = _plugin_local_path(plugin_root, raw, label=label)
        if not path.is_file():
            raise StyleBenchmarkPackError(f"{label}_missing")
        linked[label] = raw

    benchmark = _load_yaml_mapping(
        plugin_root / linked["benchmark_contract"],
        label="benchmark_contract",
    )
    aesthetic = _load_yaml_mapping(
        plugin_root / linked["aesthetic_intent"],
        label="aesthetic_intent",
    )
    return linked, benchmark, aesthetic


def _validate_candidate_slots(payload: dict[str, Any]) -> list[dict[str, str]]:
    raw_slots = payload.get("candidate_family_slots")
    if not isinstance(raw_slots, list):
        raise StyleBenchmarkPackError("candidate_family_slots_invalid")
    slots: list[dict[str, str]] = []
    ids: list[str] = []
    for raw in raw_slots:
        if not isinstance(raw, dict):
            raise StyleBenchmarkPackError("candidate_family_slots_invalid")
        values = {
            "id": raw.get("id"),
            "label": raw.get("label"),
            "mutation_boundary": raw.get("mutation_boundary"),
            "entry_condition": raw.get("entry_condition"),
            "acceptance_rule": raw.get("acceptance_rule"),
        }
        if not all(isinstance(value, str) and value.strip() for value in values.values()):
            raise StyleBenchmarkPackError("candidate_family_slots_invalid")
        slot = {key: value for key, value in values.items() if isinstance(value, str)}
        if slot["mutation_boundary"] not in MUTATION_BOUNDARIES:
            raise StyleBenchmarkPackError("mutation_boundary_invalid")
        ids.append(slot["id"])
        slots.append(slot)
    if len(ids) != len(set(ids)) or set(ids) != REQUIRED_CANDIDATE_SLOTS:
        raise StyleBenchmarkPackError("candidate_family_slots_invalid")
    by_id = {slot["id"]: slot for slot in slots}
    if by_id["current_style"]["mutation_boundary"] != "no_source_mutation":
        raise StyleBenchmarkPackError("current_style_boundary_invalid")
    svg_slot = by_id["svg_polish_handoff"]
    if svg_slot["mutation_boundary"] != "svg_artifact_mutation_requires_separate_approval":
        raise StyleBenchmarkPackError("svg_polish_boundary_invalid")
    if "ready_for_svg_polish" not in svg_slot["entry_condition"]:
        raise StyleBenchmarkPackError("svg_polish_entry_condition_invalid")
    return slots


def _validate_measurable_checks(
    payload: dict[str, Any],
    benchmark: dict[str, Any],
) -> list[dict[str, Any]]:
    raw_checks = payload.get("measurable_checks")
    if not isinstance(raw_checks, list) or not all(
        isinstance(item, dict) for item in raw_checks
    ):
        raise StyleBenchmarkPackError("measurable_checks_invalid")
    checks = {check.get("id"): check for check in raw_checks}
    text_delta = checks.get("text_boundary_delta")
    if not isinstance(text_delta, dict):
        raise StyleBenchmarkPackError("text_boundary_delta_missing")
    metric = text_delta.get("metric")
    if not isinstance(metric, str):
        raise StyleBenchmarkPackError("text_boundary_delta_invalid")
    expected_movement = benchmark.get("expected_movement")
    if not isinstance(expected_movement, dict):
        raise StyleBenchmarkPackError("benchmark_expected_movement_invalid")
    if text_delta.get("expected_movement") != expected_movement.get(metric):
        raise StyleBenchmarkPackError("text_boundary_delta_mismatch")

    hard_regression_check = checks.get("benchmark_contract_hard_regressions")
    if not isinstance(hard_regression_check, dict):
        raise StyleBenchmarkPackError("benchmark_contract_hard_regressions_missing")
    hard_regressions = benchmark.get("hard_regressions")
    if not isinstance(hard_regressions, list):
        raise StyleBenchmarkPackError("benchmark_hard_regressions_invalid")
    must_pass = hard_regression_check.get("must_pass")
    if not isinstance(must_pass, list) or not all(isinstance(item, str) for item in must_pass):
        raise StyleBenchmarkPackError("benchmark_contract_hard_regressions_invalid")
    missing_codes = [
        code
        for code in ("source_compile_failure", "candidate_hard_gate_rejected")
        if code not in hard_regressions or f"{code} absent" not in must_pass
    ]
    if missing_codes:
        raise StyleBenchmarkPackError("benchmark_contract_hard_regressions_mismatch")
    return list(raw_checks)


def _validate_safety(payload: dict[str, Any]) -> dict[str, bool]:
    safety = _as_mapping(payload, "safety")
    if set(safety) != SAFETY_FALSE_KEYS:
        raise StyleBenchmarkPackError("safety_invalid")
    for key in SAFETY_FALSE_KEYS:
        if safety[key] is not False:
            raise StyleBenchmarkPackError("safety_invalid")
    return {key: False for key in sorted(SAFETY_FALSE_KEYS)}


def load_pack(
    name: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    pack_path: Path | None = None,
) -> dict[str, Any]:
    """Load a style benchmark pack or return structured missing state."""
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise StyleBenchmarkPackError(str(exc)) from exc
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    pack, display_path = _resolve_pack_path(paths.plugin_root, name, pack_path=pack_path)
    if pack.is_symlink():
        raise StyleBenchmarkPackError("pack_symlink_forbidden")
    if not pack.is_file():
        return {
            "schema": SCHEMA,
            "state": "missing",
            "fixture": name,
            "path": display_path,
        }

    raw = json.loads(pack.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise StyleBenchmarkPackError("pack_json_invalid")
    if raw.get("schema") != SCHEMA:
        raise StyleBenchmarkPackError("schema_invalid")
    if raw.get("fixture") != name:
        raise StyleBenchmarkPackError("fixture_mismatch")
    linked, benchmark, aesthetic = _validate_linked_files(paths.plugin_root, raw)
    if benchmark.get("fixture") != name:
        raise StyleBenchmarkPackError("benchmark_fixture_mismatch")
    if aesthetic.get("fixture") != name:
        raise StyleBenchmarkPackError("aesthetic_fixture_mismatch")
    if not isinstance(raw.get("target_style_class"), str) or not raw["target_style_class"].strip():
        raise StyleBenchmarkPackError("target_style_class_invalid")
    if raw.get("default_recommendation") != "keep_current_style_until_candidate_beats_benchmark":
        raise StyleBenchmarkPackError("default_recommendation_invalid")
    forbidden = _as_string_list(raw, "forbidden_semantic_changes")
    for marker in (
        "panel roles",
        "rename symbols",
        "shallow/deep trap color semantics",
        "required labels",
        "SVG polish",
    ):
        if marker not in "\n".join(forbidden):
            raise StyleBenchmarkPackError("forbidden_semantic_changes_incomplete")
    slots = _validate_candidate_slots(raw)
    checks = _validate_measurable_checks(raw, benchmark)
    human_only_questions = _as_string_list(raw, "human_only_questions")
    candidate_rejection_rules = _as_string_list(raw, "candidate_rejection_rules")
    safety = _validate_safety(raw)
    if not human_only_questions:
        raise StyleBenchmarkPackError("human_only_questions_invalid")
    if "semantic" not in "\n".join(candidate_rejection_rules):
        raise StyleBenchmarkPackError("candidate_rejection_rules_incomplete")

    return {
        "schema": SCHEMA,
        "state": "present",
        "fixture": name,
        "path": display_path,
        "linked_files": linked,
        "target_style_class": raw["target_style_class"],
        "default_recommendation": raw["default_recommendation"],
        "candidate_family_slots": slots,
        "measurable_checks": checks,
        "human_only_questions": human_only_questions,
        "candidate_rejection_rules": candidate_rejection_rules,
        "safety": safety,
    }
