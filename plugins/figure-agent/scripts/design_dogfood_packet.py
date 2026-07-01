"""Read-only human-gated design dogfood packets over live queue state."""

from __future__ import annotations

from typing import Any

import fig_driver

SCHEMA = "figure-agent.design-dogfood-packet.v1"
MUTATION_BOUNDARY = "no_source_mutation"
DEFAULT_MODE = "review"
DEFAULT_RECOMMENDATION = "keep_current_style"
DISALLOWED_ACTIONS = [
    "do not edit figure source files",
    "do not edit accepted state",
    "do not edit release state",
    "do not edit generated exports or tracked golden artifacts",
    "do not treat this packet as implicit human acceptance",
]


class DesignDogfoodPacketError(ValueError):
    """Raised when a design dogfood packet cannot be constructed."""


def build_design_dogfood_packet(
    fixture: str,
    *,
    queue: dict[str, Any],
    mode: str = DEFAULT_MODE,
    goal: str | None = None,
) -> dict[str, Any]:
    """Build a read-only design dogfood packet for one fixture."""

    if not fig_driver.is_safe_fixture_name(fixture):
        return _blocked_packet(
            fixture,
            mode=mode,
            goal=goal,
            state="blocked_invalid_fixture",
            blocking_reason="fixture name must be a single examples/<name> directory name",
            queue=queue,
        )

    row = _matching_row(queue, fixture)
    if row is None:
        return _blocked_packet(
            fixture,
            mode=mode,
            goal=goal,
            state="blocked_missing_queue_row",
            blocking_reason="live queue did not include the requested fixture",
            queue=queue,
        )

    choices = _normalized_choices(row)
    recommended_choice_id = _recommended_choice_id(row, choices)
    missing_evidence = _missing_evidence(row)
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "state": "ready_for_human_choice" if choices else "blocked_missing_choices",
        "mode": mode,
        "goal": goal,
        "mutation_boundary": MUTATION_BOUNDARY,
        "source_queue": _source_queue(queue, mode=mode, goal=goal),
        "evidence_summary": _evidence_summary(row),
        "human_question": _human_question(fixture, recommended_choice_id, missing_evidence),
        "agent_recommendation": _agent_recommendation(row, recommended_choice_id),
        "recommended_choice_id": recommended_choice_id,
        "choices": choices,
        "missing_evidence": missing_evidence,
        "disallowed_actions": list(DISALLOWED_ACTIONS),
        "follow_up": {
            "after_decision": (
                "record a human decision, then rerun fig-agent queue in the chosen mode"
            ),
            "do_not_do": [
                "do not mutate source or release state from this packet",
                "do not ask the human to inspect raw artifacts without a recommended path",
            ],
        },
    }


def _blocked_packet(
    fixture: str,
    *,
    mode: str,
    goal: str | None,
    state: str,
    blocking_reason: str,
    queue: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": fixture,
        "state": state,
        "mode": mode,
        "goal": goal,
        "mutation_boundary": MUTATION_BOUNDARY,
        "source_queue": _source_queue(queue, mode=mode, goal=goal),
        "evidence_summary": {"blocking_reason": blocking_reason},
        "human_question": "",
        "agent_recommendation": (
            "Do not ask for human art-direction approval until queue evidence exists."
        ),
        "recommended_choice_id": None,
        "choices": [],
        "missing_evidence": [],
        "disallowed_actions": list(DISALLOWED_ACTIONS),
        "follow_up": {
            "after_decision": "rerun fig-agent queue for this fixture",
            "do_not_do": ["do not mutate source or release state from this packet"],
        },
    }


def _source_queue(queue: dict[str, Any], *, mode: str, goal: str | None) -> dict[str, Any]:
    rows = queue.get("rows")
    return {
        "schema": queue.get("schema"),
        "mode": queue.get("mode", mode),
        "goal": queue.get("goal", goal),
        "row_count": len(rows) if isinstance(rows, list) else 0,
    }


def _matching_row(queue: dict[str, Any], fixture: str) -> dict[str, Any] | None:
    rows = queue.get("rows")
    if not isinstance(rows, list):
        return None
    for row in rows:
        if isinstance(row, dict) and row.get("fixture") == fixture:
            return row
    return None


def _evidence_summary(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "action",
        "first_blocker",
        "render_state",
        "critique_state",
        "export_state",
        "acceptance_state",
        "style_benchmark_pack_state",
        "style_benchmark_comparison_state",
        "design_direction_state",
        "design_direction_next_agent_action",
    )
    return {key: row.get(key) for key in keys if row.get(key) is not None}


def _normalized_choices(row: dict[str, Any]) -> list[dict[str, Any]]:
    packet = row.get("style_direction_packet")
    raw_choices: Any = None
    if isinstance(packet, dict):
        raw_choices = packet.get("choices")
    if not isinstance(raw_choices, list) or not raw_choices:
        raw_choices = _fallback_choices()
    return [_normalize_choice(choice, row) for choice in raw_choices if isinstance(choice, dict)]


def _fallback_choices() -> list[dict[str, Any]]:
    return [
        {
            "id": "keep_current_style",
            "label": "Keep current style",
            "next_slice": "proceed to release queue",
            "risk": "may remain solid-manuscript rather than flagship polish",
            "scope_change": False,
        },
        {
            "id": "bounded_tikz_source_polish",
            "label": "Bounded TikZ source polish",
            "next_slice": "open one targeted typography/spacing/stroke polish task",
            "risk": "can improve hierarchy but should stay one local pass",
            "scope_change": False,
        },
        {
            "id": "svg_polish_handoff",
            "label": "SVG polish handoff",
            "next_slice": "run polish queue and require can_start_svg_polish=true",
            "risk": "requires positive ready_for_svg_polish evidence",
            "scope_change": True,
        },
        {
            "id": "full_style_redesign",
            "label": "Full style redesign",
            "next_slice": "create redesign alternatives against the benchmark fixture",
            "risk": "changes visual language and needs benchmark comparison",
            "scope_change": True,
        },
    ]


def _normalize_choice(choice: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    choice_id = _string_or_default(choice.get("id"), "unknown_choice")
    follow_up = _string_or_default(choice.get("next_slice"), "record decision and rerun queue")
    if choice_id == "full_style_redesign" and _style_benchmark_missing(row):
        follow_up = (
            "create style benchmark pack and comparison before any source, release, "
            "export, or golden mutation"
        )
    if choice_id == "svg_polish_handoff" and row.get("svg_polish_evidence_state") != "ready":
        follow_up = "collect positive SVG polish readiness evidence before SVG editing"
    return {
        "id": choice_id,
        "label": _string_or_default(choice.get("label"), choice_id.replace("_", " ").title()),
        "agent_position": _agent_position(choice_id),
        "follow_up": follow_up,
        "risk": _string_or_default(choice.get("risk"), "risk not stated by source packet"),
        "scope_change": bool(choice.get("scope_change")),
        "authorizes_mutation": False,
    }


def _agent_position(choice_id: str) -> str:
    positions = {
        "keep_current_style": (
            "Recommended default when no queue-visible defect blocker remains; use the "
            "current figure as a manuscript baseline until a benchmarked candidate beats it."
        ),
        "bounded_tikz_source_polish": (
            "Useful for one local typography, spacing, or stroke pass without changing the "
            "visual language."
        ),
        "svg_polish_handoff": (
            "Only open after positive SVG polish readiness evidence exists; otherwise it "
            "becomes an ungrounded art pass."
        ),
        "full_style_redesign": (
            "Reasonable only as a separate benchmarked design slice, not as an implicit "
            "rewrite of the current source."
        ),
    }
    return positions.get(choice_id, "Require an explicit human decision before follow-up work.")


def _recommended_choice_id(row: dict[str, Any], choices: list[dict[str, Any]]) -> str | None:
    packet = row.get("style_direction_packet")
    if isinstance(packet, dict):
        recommended = packet.get("recommended_choice_id")
        if isinstance(recommended, str) and recommended:
            return recommended
    choice_ids = {choice.get("id") for choice in choices}
    if row.get("action") == "complete" and DEFAULT_RECOMMENDATION in choice_ids:
        return DEFAULT_RECOMMENDATION
    if choices:
        first_id = choices[0].get("id")
        return first_id if isinstance(first_id, str) else None
    return None


def _missing_evidence(row: dict[str, Any]) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    pack_state = row.get("style_benchmark_pack_state")
    if _state_missing_or_blocked(pack_state):
        missing.append(
            {
                "id": "style_benchmark_pack",
                "state": str(pack_state),
                "next_agent_action": "create_style_benchmark_pack",
            }
        )
    comparison_state = row.get("style_benchmark_comparison_state")
    if _state_missing_or_blocked(comparison_state):
        missing.append(
            {
                "id": "style_benchmark_comparison",
                "state": str(comparison_state),
                "next_agent_action": "create_style_benchmark_comparison",
            }
        )
    design_state = row.get("design_direction_state")
    if isinstance(design_state, str) and design_state != "ready_for_human_choice":
        missing.append(
            {
                "id": "design_direction",
                "state": design_state,
                "next_agent_action": _string_or_default(
                    row.get("design_direction_next_agent_action"),
                    "create_style_benchmark_pack",
                ),
            }
        )
    return missing


def _state_missing_or_blocked(state: Any) -> bool:
    if not isinstance(state, str):
        return False
    return state in {"missing", "invalid"} or state.startswith("blocked_")


def _style_benchmark_missing(row: dict[str, Any]) -> bool:
    return _state_missing_or_blocked(row.get("style_benchmark_pack_state")) or (
        _state_missing_or_blocked(row.get("style_benchmark_comparison_state"))
    )


def _human_question(
    fixture: str,
    recommended_choice_id: str | None,
    missing_evidence: list[dict[str, str]],
) -> str:
    if missing_evidence:
        return (
            f"I recommend `{recommended_choice_id}` for `{fixture}` as the safe next "
            "design direction, while creating the missing style benchmark evidence "
            "before any broader redesign. Which option should I prepare next?"
        )
    return (
        f"I recommend `{recommended_choice_id}` for `{fixture}`. Which bounded design "
        "direction should I prepare next?"
    )


def _agent_recommendation(row: dict[str, Any], recommended_choice_id: str | None) -> str:
    source_packet = row.get("style_direction_packet")
    if isinstance(source_packet, dict):
        source_recommendation = source_packet.get("agent_recommendation")
        if isinstance(source_recommendation, str) and source_recommendation:
            return source_recommendation
    if recommended_choice_id == "keep_current_style":
        return (
            "Keep the current style as the default manuscript baseline unless a "
            "benchmarked candidate beats it on explicit visual criteria."
        )
    return "Use the recommended option as a bounded follow-up, not as mutation authority."


def _string_or_default(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value
    return default
