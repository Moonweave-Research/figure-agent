"""Load and validate read-only style benchmark comparison packets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import fixture_identity
import human_decision_record
import runtime_paths
import style_benchmark_pack

SCHEMA = "figure-agent.style-benchmark-comparison-packet.v1"
DEFAULT_COMPARISON_SET = "2026-07-01-wave-f"
REQUIRED_CANDIDATE_FAMILIES = style_benchmark_pack.REQUIRED_CANDIDATE_SLOTS
MUTATION_BOUNDARIES = style_benchmark_pack.MUTATION_BOUNDARIES
RESULTS = frozenset(
    {
        "winner_candidate",
        "eligible",
        "rejected_semantic_risk",
        "blocked_requires_separate_approval",
        "blocked_missing_evidence",
    }
)


class StyleBenchmarkComparisonError(ValueError):
    """Raised when a style benchmark comparison packet is malformed."""


def _plugin_local_path(plugin_root: Path, raw_path: str, *, label: str) -> Path:
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise StyleBenchmarkComparisonError(f"{label}_path_escape")
    path = plugin_root / relative
    try:
        path.resolve().relative_to(plugin_root.resolve())
    except ValueError as exc:
        raise StyleBenchmarkComparisonError(f"{label}_path_escape") from exc
    for parent in [path, *path.parents]:
        if parent == plugin_root.parent:
            break
        if parent.is_symlink():
            raise StyleBenchmarkComparisonError(f"{label}_path_symlink")
    return path


def _resolve_comparison_path(
    plugin_root: Path,
    fixture: str,
    *,
    comparison_path: Path | None,
) -> tuple[Path, str]:
    if comparison_path is None:
        relative = (
            Path("docs")
            / "style-benchmark-comparisons"
            / DEFAULT_COMPARISON_SET
            / f"{fixture}.json"
        )
        return plugin_root / relative, relative.as_posix()
    if comparison_path.is_absolute():
        try:
            relative = comparison_path.resolve().relative_to(plugin_root.resolve())
        except ValueError as exc:
            raise StyleBenchmarkComparisonError("comparison_path_escape") from exc
        return comparison_path, relative.as_posix()
    return (
        _plugin_local_path(plugin_root, comparison_path.as_posix(), label="comparison"),
        comparison_path.as_posix(),
    )


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise StyleBenchmarkComparisonError(f"{key}_invalid")
    return value


def _string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise StyleBenchmarkComparisonError(f"{key}_invalid")
    return list(value)


def _load_json_mapping(path: Path, *, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise StyleBenchmarkComparisonError(f"{label}_symlink_forbidden")
    if not path.is_file():
        raise StyleBenchmarkComparisonError(f"{label}_missing")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise StyleBenchmarkComparisonError(f"{label}_json_invalid")
    return raw


def _validate_linked_pack(
    plugin_root: Path,
    fixture: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    raw_path = _required_string(payload, "source_style_benchmark_pack")
    path = _plugin_local_path(plugin_root, raw_path, label="source_style_benchmark_pack")
    pack = style_benchmark_pack.load_pack(fixture, plugin_root=plugin_root, pack_path=path)
    if pack.get("state") != "present":
        raise StyleBenchmarkComparisonError("source_style_benchmark_pack_not_present")
    return pack


def _validate_linked_decision(
    plugin_root: Path,
    fixture: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    raw_path = _required_string(payload, "source_human_decision_record")
    path = _plugin_local_path(plugin_root, raw_path, label="source_human_decision_record")
    record = human_decision_record.validate_decision_record(
        _load_json_mapping(path, label="source_human_decision_record")
    )
    if record["fixture"] != fixture:
        raise StyleBenchmarkComparisonError("source_human_decision_record_fixture_mismatch")
    if record["packet_schema"] != human_decision_record.STYLE_DIRECTION_PACKET_SCHEMA:
        raise StyleBenchmarkComparisonError("source_human_decision_record_not_style_direction")
    if record["mutation_boundary"] != "no_source_mutation":
        raise StyleBenchmarkComparisonError("source_human_decision_record_authorizes_mutation")
    return record


def _validate_candidates(
    payload: dict[str, Any],
    pack: dict[str, Any],
) -> list[dict[str, Any]]:
    raw_candidates = payload.get("candidate_family_comparisons")
    if not isinstance(raw_candidates, list) or not all(
        isinstance(item, dict) for item in raw_candidates
    ):
        raise StyleBenchmarkComparisonError("candidate_family_comparisons_invalid")
    candidates = list(raw_candidates)
    ids = [_required_string(candidate, "id") for candidate in candidates]
    if len(ids) != len(set(ids)) or set(ids) != REQUIRED_CANDIDATE_FAMILIES:
        raise StyleBenchmarkComparisonError("candidate_family_comparisons_invalid")

    pack_slots = {
        slot["id"]: slot
        for slot in pack.get("candidate_family_slots", [])
        if isinstance(slot, dict) and isinstance(slot.get("id"), str)
    }
    normalized: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = _required_string(candidate, "id")
        result = _required_string(candidate, "result")
        if result not in RESULTS:
            raise StyleBenchmarkComparisonError("candidate_result_invalid")
        boundary = _required_string(candidate, "mutation_boundary")
        if boundary not in MUTATION_BOUNDARIES:
            raise StyleBenchmarkComparisonError("candidate_mutation_boundary_invalid")
        slot_boundary = pack_slots.get(candidate_id, {}).get("mutation_boundary")
        if boundary != slot_boundary:
            raise StyleBenchmarkComparisonError("candidate_mutation_boundary_mismatch")
        if candidate.get("authorizes_mutation") is not False:
            raise StyleBenchmarkComparisonError("candidate_authorizes_mutation")
        if candidate.get("semantic_change_allowed") is not False:
            raise StyleBenchmarkComparisonError("candidate_semantic_change_allowed")
        if result == "winner_candidate" and candidate_id != "current_style":
            raise StyleBenchmarkComparisonError("non_current_winner_requires_real_candidate")
        if result == "winner_candidate" and boundary != "no_source_mutation":
            raise StyleBenchmarkComparisonError("winner_candidate_authorizes_mutation")
        if candidate_id == "svg_polish_handoff":
            prerequisites = "\n".join(_string_list(candidate, "prerequisite_evidence"))
            if "ready_for_svg_polish" not in prerequisites:
                raise StyleBenchmarkComparisonError("svg_polish_prerequisite_missing")
        normalized.append(
            {
                "id": candidate_id,
                "result": result,
                "mutation_boundary": boundary,
                "authorizes_mutation": False,
                "semantic_change_allowed": False,
                "comparison_basis": _string_list(candidate, "comparison_basis"),
                "failure_modes": _string_list(candidate, "failure_modes"),
                "prerequisite_evidence": _string_list(candidate, "prerequisite_evidence"),
            }
        )
    return normalized


def load_comparison(
    fixture: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    comparison_path: Path | None = None,
) -> dict[str, Any]:
    """Load a read-only style comparison packet for candidate families."""
    try:
        fixture_identity.validate_fixture_name(fixture)
    except ValueError as exc:
        raise StyleBenchmarkComparisonError(str(exc)) from exc
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    path, display_path = _resolve_comparison_path(
        paths.plugin_root,
        fixture,
        comparison_path=comparison_path,
    )
    payload = _load_json_mapping(path, label="comparison")
    if payload.get("schema") != SCHEMA:
        raise StyleBenchmarkComparisonError("schema_invalid")
    if payload.get("fixture") != fixture:
        raise StyleBenchmarkComparisonError("fixture_mismatch")

    pack = _validate_linked_pack(paths.plugin_root, fixture, payload)
    decision = _validate_linked_decision(paths.plugin_root, fixture, payload)
    candidates = _validate_candidates(payload, pack)
    forbidden_semantic_changes = _string_list(payload, "forbidden_semantic_changes")
    measurable_checks = _string_list(payload, "benchmark_measurable_checks")
    measurable_text = "\n".join(measurable_checks)
    if (
        "style_lock_typography" not in measurable_text
        or "tiny/scriptsize/huge" not in measurable_text
    ):
        raise StyleBenchmarkComparisonError("style_lock_typography_check_missing")
    human_only_questions = _string_list(payload, "human_only_questions")
    rejection_rules = _string_list(payload, "candidate_rejection_rules")
    if "semantic" not in "\n".join(rejection_rules):
        raise StyleBenchmarkComparisonError("candidate_rejection_rules_incomplete")
    if "current_style" not in {candidate["id"] for candidate in candidates}:
        raise StyleBenchmarkComparisonError("current_style_missing")
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "path": display_path,
        "source_style_benchmark_pack": payload["source_style_benchmark_pack"],
        "source_human_decision_record": payload["source_human_decision_record"],
        "human_style_decision": decision["decision_kind"],
        "target_style_class": pack["target_style_class"],
        "default_recommendation": pack["default_recommendation"],
        "forbidden_semantic_changes": forbidden_semantic_changes,
        "benchmark_measurable_checks": measurable_checks,
        "human_only_questions": human_only_questions,
        "candidate_rejection_rules": rejection_rules,
        "candidate_family_comparisons": candidates,
    }
