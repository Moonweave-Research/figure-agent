"""Shared actor classification for dry-run driver summaries."""

from __future__ import annotations

from typing import Any

import fig_driver_guidance as guidance_mod

STOP_HOST_BOUNDARY = "host_boundary"


def _next_action(summary: dict[str, Any]) -> dict[str, Any]:
    value = summary.get("next_action_summary")
    return value if isinstance(value, dict) else {}


def blocking_source_for_driver_summary(summary: dict[str, Any]) -> str | None:
    action = summary.get("action")
    if action == "complete":
        return None
    next_action = _next_action(summary)
    blocking_source = next_action.get("blocking_source")
    if isinstance(blocking_source, str) and blocking_source:
        return blocking_source
    stop_boundary = summary.get("stop_boundary")
    if isinstance(stop_boundary, str) and stop_boundary:
        return stop_boundary
    if isinstance(action, str) and action:
        return "driver.action"
    return "driver.unknown"


def requires_human_for_driver_summary(summary: dict[str, Any]) -> bool:
    next_action = _next_action(summary)
    requires_human = next_action.get("requires_human")
    if isinstance(requires_human, bool):
        return requires_human
    return required_actor_for_driver_summary(summary) in {"human", "release_operator"}


def required_actor_for_driver_summary(
    summary: dict[str, Any],
    *,
    final_stop_reason: str | None = None,
) -> str:
    actor = guidance_mod.required_actor_for_summary(summary)
    if actor != "workflow_agent":
        return actor
    if (
        final_stop_reason == STOP_HOST_BOUNDARY
        and summary.get("stop_boundary") != guidance_mod.STOP_REFERENCE_MISSING
    ):
        return "host_llm"
    return actor
