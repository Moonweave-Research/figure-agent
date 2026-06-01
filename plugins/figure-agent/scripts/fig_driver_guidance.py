"""Operator-facing guidance helpers for fig_driver."""

from __future__ import annotations

from typing import Any

import fig_driver_commands as command_mod

OPERATOR_GUIDANCE_SCHEMA = "figure-agent.operator-guidance.v1"
FINAL_READINESS_SCHEMA = "figure-agent.final-readiness.v1"

ACTION_RUN_CRITIQUE = "run_critique"
ACTION_HUMAN_GATE_STOP = "human_gate_stop"
ACTION_POLISH_HANDOFF_STOP = "polish_handoff_stop"
ACTION_RELEASE_BLOCKED = "release_blocked"
ACTION_COMPLETE = "complete"

STOP_HOST_LLM_CRITIQUE = "host_llm_critique_required"
STOP_REFERENCE_MISSING = "reference_missing"
STOP_SEMANTIC_BACKPORT = "semantic_backport_required"
STOP_AMBIGUOUS_PATCH = "ambiguous_patch_selection"
STOP_HUMAN_GATE = "human_gate_required"
STOP_FORCE_GOLDEN = "force_golden_required"
STOP_ACCEPTED_OR_FINAL_READY = "accepted_or_final_ready_required"


def required_actor_for_summary(summary: dict[str, Any]) -> str:
    action = summary.get("action")
    stop_boundary = summary.get("stop_boundary")
    if action == ACTION_COMPLETE:
        return "none"
    if stop_boundary in {STOP_REFERENCE_MISSING, STOP_SEMANTIC_BACKPORT}:
        return "workflow_agent"
    if action == ACTION_RUN_CRITIQUE or stop_boundary == STOP_HOST_LLM_CRITIQUE:
        return "host_llm"
    if action == ACTION_HUMAN_GATE_STOP or stop_boundary in {
        STOP_HUMAN_GATE,
        STOP_AMBIGUOUS_PATCH,
    }:
        return "human"
    if action == ACTION_RELEASE_BLOCKED or stop_boundary in {
        STOP_FORCE_GOLDEN,
        STOP_ACCEPTED_OR_FINAL_READY,
    }:
        return "release_operator"
    if action == ACTION_POLISH_HANDOFF_STOP:
        return "svg_editor"
    return "workflow_agent"


def _operator_state(action: Any, stop_boundary: Any, actor: str) -> str:
    if action == ACTION_COMPLETE:
        return "complete"
    if actor in {"human", "release_operator"}:
        return "human_boundary"
    if actor == "host_llm":
        return "host_boundary"
    if actor == "svg_editor":
        return "polish_boundary"
    if isinstance(stop_boundary, str) and stop_boundary:
        return "blocked"
    return "next_action"


def _first_blocker_code(summary: dict[str, Any]) -> str | None:
    status_explanation = summary.get("status_explanation")
    if not isinstance(status_explanation, dict):
        return None
    first_blocker = status_explanation.get("first_blocker")
    if not isinstance(first_blocker, dict):
        return None
    code = first_blocker.get("code")
    return code if isinstance(code, str) and code else None


def _operator_next_step(summary: dict[str, Any], actor: str) -> str:
    fixture = str(summary.get("fixture") or "<name>")
    action = summary.get("action")
    command = summary.get("safe_command")
    status = summary.get("status")
    export_state = status.get("export_state") if isinstance(status, dict) else None
    if action == ACTION_COMPLETE:
        return "No required plugin action remains for this mode."
    if isinstance(command, str) and command:
        if command.startswith("FIGURE_AGENT_STRICT=1 "):
            return f"Run strict compile final check: `{command}`."
        return f"Run the selected command: `{command}`."
    first_blocker_code = _first_blocker_code(summary)
    if (
        action == ACTION_RELEASE_BLOCKED
        and export_state == "TRACKED_GOLDEN"
        and first_blocker_code in {None, "export_tracked_golden"}
    ):
        return (
            "Human release operator must decide whether to roll forward the "
            f"tracked golden export with `/fig_export {fixture} --force-golden`."
        )
    if summary.get("stop_boundary") == STOP_REFERENCE_MISSING:
        return (
            "Fix the declared reference path or add the missing reference file, "
            "then rerun /fig_drive."
        )
    if actor == "host_llm":
        return (
            f"Run `/fig_critique {fixture}` in the host vision session, "
            "then rerun /fig_drive."
        )
    if actor == "human":
        return "Record the required human decision, then rerun /fig_drive."
    if actor == "release_operator":
        return "Resolve accepted, golden, final-artifact, or publication gates manually."
    if actor == "svg_editor":
        return "Follow the SVG polish handoff; do not edit source under polish mode."
    return "Inspect the driver reason and rerun live /fig_status before continuing."


def operator_guidance(summary: dict[str, Any]) -> dict[str, Any]:
    action = summary.get("action")
    stop_boundary = summary.get("stop_boundary")
    actor = required_actor_for_summary(summary)
    return {
        "schema": OPERATOR_GUIDANCE_SCHEMA,
        "state": _operator_state(action, stop_boundary, actor),
        "required_actor": actor,
        "next_step": _operator_next_step(summary, actor),
    }


def _profile_step(state: str, *, reason: str, command: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "state": state,
        "reason": reason,
    }
    if command is not None:
        payload["command"] = command
    return payload


def final_readiness_profile(
    name: str,
    *,
    status: dict[str, Any],
    summary: dict[str, Any],
    loop_checkpoint: dict[str, Any] | None,
) -> dict[str, Any]:
    render = status.get("render_state")
    critique = status.get("critique_state")
    export = status.get("export_state")
    publication = status.get("publication_gate_state")
    release_ready = status.get("release_ready") is True
    actor = required_actor_for_summary(summary)
    action = summary.get("action")

    strict_compile = _profile_step(
        "pass" if render == "FRESH" else "needs_action",
        command=command_mod.strict_compile_command(name),
        reason=(
            "render is fresh; strict compile is available as the final manual render check."
            if render == "FRESH"
            else "render is not fresh; final mode starts with strict compile."
        ),
    )
    critique_check = _profile_step(
        "pass"
        if critique in {"FRESH", "NOT_REQUIRED"}
        else "human_required"
        if critique == "REFERENCE_MISSING"
        else "needs_action",
        reason=f"critique_state is {critique}.",
    )
    loop_state = "pass"
    loop_reason = "latest loop checkpoint is clean."
    if loop_checkpoint is None:
        loop_state = "needs_action"
        loop_reason = "no latest loop checkpoint is available."
    elif loop_checkpoint.get("final_stop_reason") not in {
        "verify_only_complete",
        "no_actionable_findings",
    }:
        loop_state = (
            "human_required" if actor in {"human", "release_operator"} else "needs_action"
        )
        loop_reason = f"latest loop stop is {loop_checkpoint.get('final_stop_reason')}."
    export_check = _profile_step(
        "pass"
        if export == "FRESH"
        else "human_required"
        if export == "TRACKED_GOLDEN"
        else "needs_action",
        reason=f"export_state is {export}.",
    )
    publication_check = _profile_step(
        "pass" if publication in {None, "OK"} else "human_required",
        reason=f"publication_gate_state is {publication}.",
    )
    release_gate = _profile_step(
        "pass"
        if release_ready
        else "human_required"
        if actor == "release_operator"
        else "needs_action",
        reason=(
            "release_ready is true."
            if release_ready
            else "release requires explicit accepted/golden/final-artifact closure."
        ),
    )
    if action == ACTION_COMPLETE:
        overall = "pass"
    elif actor in {"human", "release_operator"}:
        overall = "human_required"
    else:
        overall = "needs_action"
    return {
        "schema": FINAL_READINESS_SCHEMA,
        "overall_state": overall,
        "strict_compile": strict_compile,
        "critique": critique_check,
        "loop_checkpoint": _profile_step(loop_state, reason=loop_reason),
        "export": export_check,
        "publication_gate": publication_check,
        "release_gate": release_gate,
        "non_mutating_driver": True,
    }
