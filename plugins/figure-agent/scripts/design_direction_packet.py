"""Build read-only design-direction packets for human visual choices."""

from __future__ import annotations

import fixture_identity

SCHEMA = "figure-agent.design-direction-packet.v1"
MUTATION_BOUNDARY = "no_source_mutation"
DEFAULT_RECOMMENDATION = "keep_current_style_until_candidate_beats_benchmark"
ALTERNATIVES = [
    "current_style",
    "bounded_tikz_refinement",
    "editorial_redesign",
    "svg_polish_handoff",
]
HUMAN_QUESTION = (
    "I recommend keeping the current style unless a candidate beats the "
    "benchmark. Which direction should I prepare next?"
)


class DesignDirectionPacketError(ValueError):
    """Raised when a design-direction packet cannot be built safely."""


def _validate_fixture(fixture: str) -> None:
    try:
        fixture_identity.validate_fixture_name(fixture)
    except ValueError as exc:
        raise DesignDirectionPacketError(f"fixture_invalid:{fixture}") from exc


def _is_present(payload: dict[str, object] | None) -> bool:
    return isinstance(payload, dict) and payload.get("state") == "present"


def _evidence_refs(
    style_pack: dict[str, object], comparison: dict[str, object]
) -> list[str]:
    refs: list[str] = []
    for prefix, payload in (
        ("style_benchmark_pack", style_pack),
        ("style_benchmark_comparison", comparison),
    ):
        path = payload.get("path")
        if isinstance(path, str) and path:
            refs.append(f"{prefix}:{path}")
    linked_files = style_pack.get("linked_files")
    if isinstance(linked_files, dict):
        for label in ("benchmark_contract", "aesthetic_intent"):
            path = linked_files.get(label)
            if isinstance(path, str) and path:
                refs.append(f"{label}:{path}")
    return refs


def build_design_direction_packet(
    fixture: str,
    *,
    queue_row: dict[str, object],
    style_pack: dict[str, object] | None,
    comparison: dict[str, object] | None,
    svg_polish_state: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return a normalized, read-only packet for a bounded human style choice."""
    _validate_fixture(fixture)
    if not _is_present(style_pack):
        return {
            "schema": SCHEMA,
            "fixture": fixture,
            "state": "blocked_missing_style_pack",
            "mutation_boundary": MUTATION_BOUNDARY,
            "alternatives": [],
            "blocking_reasons": ["style_benchmark_pack_missing"],
            "next_agent_action": "create_style_benchmark_pack",
        }
    if not _is_present(comparison):
        return {
            "schema": SCHEMA,
            "fixture": fixture,
            "state": "blocked_missing_comparison",
            "mutation_boundary": MUTATION_BOUNDARY,
            "alternatives": [],
            "blocking_reasons": ["style_benchmark_comparison_missing"],
            "next_agent_action": "create_style_benchmark_comparison",
        }
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "state": "ready_for_human_choice",
        "default_recommendation": comparison.get(
            "default_recommendation",
            DEFAULT_RECOMMENDATION,
        ),
        "alternatives": ALTERNATIVES.copy(),
        "mutation_boundary": MUTATION_BOUNDARY,
        "human_question": HUMAN_QUESTION,
        "next_agent_action": "prepare_bounded_candidate_or_stop_for_human_choice",
        "source_queue_action": queue_row.get("action"),
        "svg_polish_state": (svg_polish_state or {}).get("state", "not_checked"),
        "evidence_refs": _evidence_refs(style_pack, comparison),
    }
