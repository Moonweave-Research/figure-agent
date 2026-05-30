"""Shared actor classification for dry-run driver summaries."""

from __future__ import annotations

from typing import Any

import fig_driver

STOP_HOST_BOUNDARY = "host_boundary"


def _next_action(summary: dict[str, Any]) -> dict[str, Any]:
    value = summary.get("next_action_summary")
    return value if isinstance(value, dict) else {}


def blocking_source_for_driver_summary(summary: dict[str, Any]) -> str:
    next_action = _next_action(summary)
    blocking_source = next_action.get("blocking_source")
    if isinstance(blocking_source, str) and blocking_source:
        return blocking_source
    stop_boundary = summary.get("stop_boundary")
    if isinstance(stop_boundary, str) and stop_boundary:
        return stop_boundary
    action = summary.get("action")
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
    action = summary.get("action")
    stop_boundary = summary.get("stop_boundary")
    if stop_boundary in {fig_driver.STOP_REFERENCE_MISSING, fig_driver.STOP_SEMANTIC_BACKPORT}:
        return "workflow_agent"
    if (
        action == fig_driver.ACTION_RUN_CRITIQUE
        or stop_boundary == fig_driver.STOP_HOST_LLM_CRITIQUE
    ):
        return "host_llm"
    if action == fig_driver.ACTION_HUMAN_GATE_STOP or stop_boundary in {
        fig_driver.STOP_HUMAN_GATE,
        fig_driver.STOP_AMBIGUOUS_PATCH,
    }:
        return "human"
    if action == fig_driver.ACTION_RELEASE_BLOCKED or stop_boundary in {
        fig_driver.STOP_FORCE_GOLDEN,
        fig_driver.STOP_ACCEPTED_OR_FINAL_READY,
    }:
        return "release_operator"
    if action == fig_driver.ACTION_POLISH_HANDOFF_STOP:
        return "svg_editor"
    if final_stop_reason == STOP_HOST_BOUNDARY:
        return "host_llm"
    return "workflow_agent"
