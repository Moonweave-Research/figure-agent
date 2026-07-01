"""Build read-only bounded TikZ refinement request packets."""

from __future__ import annotations

from typing import Any

import fixture_identity

SCHEMA = "figure-agent.bounded-tikz-refinement-packet.v1"
MUTATION_BOUNDARY = "no_source_mutation"
CANDIDATE_FAMILY_ID = "restrained_tikz_refinement"
SOURCE_MUTATION_BOUNDARY = "source_mutation_requires_separate_approval"
ALLOWED_REFINEMENT_CLASSES = [
    "label_spacing",
    "stroke_hierarchy",
    "trap_level_clarity",
    "panel_spacing",
]
DISALLOWED_ACTIONS = [
    "do not edit figure source files from this packet",
    "do not edit generated exports or tracked golden artifacts",
    "do not change semantic labels, panel roles, or trap physics",
    "do not treat this request as human source-mutation approval",
]


class BoundedTikzRefinementPacketError(ValueError):
    """Raised when a bounded TikZ refinement packet cannot be built safely."""


def build_bounded_tikz_refinement_packet(
    fixture: str,
    *,
    style_pack: dict[str, Any] | None,
    comparison: dict[str, Any] | None,
    queue_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a request packet that prepares, but does not authorize, source polish."""

    _validate_fixture(fixture)
    pack_state = _state(style_pack)
    if pack_state != "present":
        return _blocked_packet(
            fixture,
            state="blocked_missing_style_benchmark_pack",
            next_agent_action="create_style_benchmark_pack",
        )
    comparison_state = _state(comparison)
    if comparison_state != "present":
        return _blocked_packet(
            fixture,
            state="blocked_missing_style_benchmark_comparison",
            next_agent_action="create_style_benchmark_comparison",
        )
    slot = _candidate_slot(style_pack or {})
    candidate = _candidate_comparison(comparison or {})
    if slot is None or candidate is None:
        return _blocked_packet(
            fixture,
            state="blocked_missing_restrained_tikz_candidate_family",
            next_agent_action="repair_style_benchmark_candidate_family",
        )

    target_style_class = _string_or_default(
        (style_pack or {}).get("target_style_class"),
        "restrained scientific mechanism schematic",
    )
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "state": "ready_for_human_source_mutation_choice",
        "mutation_boundary": MUTATION_BOUNDARY,
        "authorizes_source_mutation": False,
        "requires_human_decision": True,
        "candidate_family": {
            "id": CANDIDATE_FAMILY_ID,
            "target_style_class": target_style_class,
            "source_mutation_boundary": SOURCE_MUTATION_BOUNDARY,
            "comparison_result": candidate.get("result"),
            "entry_condition": slot.get("entry_condition"),
            "acceptance_rule": slot.get("acceptance_rule"),
        },
        "allowed_refinement_classes": list(ALLOWED_REFINEMENT_CLASSES),
        "must_preserve": _must_preserve(comparison or {}),
        "evidence_summary": _evidence_summary(queue_row or {}, candidate),
        "required_candidate_evidence": [
            "exact source selector or marker-delimited patch target",
            "source hash before candidate preparation",
            "rollback strategy",
            "expected visual delta tied to benchmark measurable checks",
            "post-candidate compile/status verification commands",
        ],
        "human_question": (
            f"I can prepare one bounded TikZ refinement candidate for `{fixture}` "
            "under the benchmark guardrails. Should I prepare that candidate packet?"
        ),
        "next_agent_action": "prepare_bounded_tikz_candidate_packet_after_human_choice",
        "disallowed_actions": list(DISALLOWED_ACTIONS),
        "follow_up": {
            "if_human_approves": (
                "prepare candidate evidence only; source mutation remains separate"
            ),
            "if_human_rejects": "keep current style as benchmark and proceed to release/final gate",
        },
    }


def _validate_fixture(fixture: str) -> None:
    try:
        fixture_identity.validate_fixture_name(fixture)
    except ValueError as exc:
        raise BoundedTikzRefinementPacketError(f"fixture_invalid:{fixture}") from exc


def _blocked_packet(
    fixture: str,
    *,
    state: str,
    next_agent_action: str,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "state": state,
        "mutation_boundary": MUTATION_BOUNDARY,
        "authorizes_source_mutation": False,
        "requires_human_decision": False,
        "candidate_family": None,
        "allowed_refinement_classes": [],
        "must_preserve": [],
        "evidence_summary": {},
        "required_candidate_evidence": [],
        "human_question": "",
        "next_agent_action": next_agent_action,
        "disallowed_actions": list(DISALLOWED_ACTIONS),
        "follow_up": {
            "if_human_approves": "not available until benchmark evidence is present",
            "if_human_rejects": "keep current style as benchmark",
        },
    }


def _state(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    state = payload.get("state")
    if isinstance(state, str):
        return state
    if isinstance(payload.get("schema"), str) and isinstance(payload.get("fixture"), str):
        return "present"
    return None


def _candidate_slot(style_pack: dict[str, Any]) -> dict[str, Any] | None:
    slots = style_pack.get("candidate_family_slots")
    if not isinstance(slots, list):
        return None
    for slot in slots:
        if isinstance(slot, dict) and slot.get("id") == CANDIDATE_FAMILY_ID:
            if slot.get("mutation_boundary") != SOURCE_MUTATION_BOUNDARY:
                return None
            return slot
    return None


def _candidate_comparison(comparison: dict[str, Any]) -> dict[str, Any] | None:
    candidates = comparison.get("candidate_family_comparisons")
    if not isinstance(candidates, list):
        return None
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("id") == CANDIDATE_FAMILY_ID:
            if candidate.get("mutation_boundary") != SOURCE_MUTATION_BOUNDARY:
                return None
            if candidate.get("authorizes_mutation") is not False:
                return None
            if candidate.get("semantic_change_allowed") is not False:
                return None
            return candidate
    return None


def _must_preserve(comparison: dict[str, Any]) -> list[str]:
    value = comparison.get("forbidden_semantic_changes")
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _evidence_summary(queue_row: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "candidate_result": candidate.get("result"),
        "comparison_basis": _string_list(candidate.get("comparison_basis")),
        "failure_modes": _string_list(candidate.get("failure_modes")),
        "prerequisite_evidence": _string_list(candidate.get("prerequisite_evidence")),
    }
    for key in (
        "render_state",
        "critique_state",
        "export_state",
        "design_direction_state",
    ):
        value = queue_row.get(key)
        if value is not None:
            summary[key] = value
    return summary


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _string_or_default(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value
    return default
