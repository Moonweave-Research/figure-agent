"""Compact read-only next-action summaries for figure-agent commands."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SCHEMA = "figure-agent.next-action-summary.v1"
DECISION_BOUNDARY_SCHEMA = "figure-agent.decision-boundary.v1"

ACTION_CREATE_OR_FIX_SOURCE = "create_or_fix_source"
ACTION_RUN_COMPILE = "run_compile"
ACTION_RUN_CRITIQUE = "run_critique"
ACTION_RUN_ADJUDICATE = "run_adjudicate"
ACTION_RUN_FIG_LOOP = "run_fig_loop"
ACTION_RUN_EXPORT = "run_export"
ACTION_PATCH_HANDOFF_STOP = "patch_handoff_stop"
ACTION_HUMAN_GATE_STOP = "human_gate_stop"
ACTION_POLISH_HANDOFF_STOP = "polish_handoff_stop"
ACTION_RELEASE_BLOCKED = "release_blocked"
ACTION_COMPLETE = "complete"

STOP_SEMANTIC_BACKPORT = "semantic_backport_required"

_HUMAN_ACTIONS = {
    ACTION_HUMAN_GATE_STOP,
    ACTION_RELEASE_BLOCKED,
}
_HUMAN_STOP_BOUNDARIES = {
    "human_gate_required",
    "force_golden_required",
    "accepted_or_final_ready_required",
}
_HUMAN_BLOCKER_CODES = {
    "critique_reference_missing",
    "export_tracked_golden",
    "not_accepted",
    "publication_gate_required",
    "final_artifact_blocked",
}
_DEFAULT_FORBIDDEN_SCOPE = [
    "accepted/golden state without explicit human approval",
    "unrelated examples",
    "hidden source edits",
    "generated artifacts outside the selected command",
]


def _decision_boundary(
    *,
    action: str,
    blocking_source: str,
    requires_human: bool,
) -> dict[str, Any]:
    if action == ACTION_COMPLETE:
        return {
            "schema": DECISION_BOUNDARY_SCHEMA,
            "kind": "none",
            "authority": "none",
            "blocks_progress": False,
            "blocks_release": False,
            "explanation": "No required plugin action remains for this mode.",
        }
    if blocking_source in {"reference_missing", "critique_reference_missing"}:
        if requires_human:
            return {
                "schema": DECISION_BOUNDARY_SCHEMA,
                "kind": "human_decision",
                "authority": "human",
                "blocks_progress": True,
                "blocks_release": True,
                "explanation": "A human domain or art-direction decision is required.",
            }
        return {
            "schema": DECISION_BOUNDARY_SCHEMA,
            "kind": "deterministic_plugin_gate",
            "authority": "plugin",
            "blocks_progress": True,
            "blocks_release": True,
            "explanation": (
                "Declared reference inputs must be fixed before host vision critique can run."
            ),
        }
    if action == ACTION_RUN_CRITIQUE or blocking_source == "host_llm_critique_required":
        return {
            "schema": DECISION_BOUNDARY_SCHEMA,
            "kind": "host_vision_gate",
            "authority": "host_llm",
            "blocks_progress": True,
            "blocks_release": True,
            "explanation": "Host vision critique is required before this workflow can close.",
        }
    if action == ACTION_RELEASE_BLOCKED or blocking_source in {
        "force_golden_required",
        "accepted_or_final_ready_required",
    }:
        return {
            "schema": DECISION_BOUNDARY_SCHEMA,
            "kind": "release_decision",
            "authority": "release_operator",
            "blocks_progress": True,
            "blocks_release": True,
            "explanation": (
                "Release, accepted, golden, or final-artifact state needs explicit human closure."
            ),
        }
    if requires_human:
        return {
            "schema": DECISION_BOUNDARY_SCHEMA,
            "kind": "human_decision",
            "authority": "human",
            "blocks_progress": True,
            "blocks_release": True,
            "explanation": "A human domain or art-direction decision is required.",
        }
    if action == ACTION_POLISH_HANDOFF_STOP:
        if blocking_source == STOP_SEMANTIC_BACKPORT:
            return {
                "schema": DECISION_BOUNDARY_SCHEMA,
                "kind": "deterministic_plugin_gate",
                "authority": "plugin",
                "blocks_progress": True,
                "blocks_release": True,
                "explanation": (
                    "A polish-mode semantic backport repairs source/spec semantics "
                    "and is release-blocking, not a bounded SVG editor handoff."
                ),
            }
        return {
            "schema": DECISION_BOUNDARY_SCHEMA,
            "kind": "polish_handoff",
            "authority": "svg_editor",
            "blocks_progress": True,
            "blocks_release": False,
            "explanation": "SVG polish is a bounded editor handoff, not hidden source mutation.",
        }
    return {
        "schema": DECISION_BOUNDARY_SCHEMA,
        "kind": "deterministic_plugin_gate",
        "authority": "plugin",
        "blocks_progress": True,
        "blocks_release": True,
        "explanation": "A deterministic plugin workflow step must run before continuing.",
    }


def _advisory_only_boundary() -> dict[str, Any]:
    return {
        "schema": DECISION_BOUNDARY_SCHEMA,
        "kind": "advisory_only",
        "authority": "plugin",
        "blocks_progress": False,
        "blocks_release": False,
        "explanation": (
            "The required workflow is complete; optional improvement candidates "
            "are advisory and do not block release."
        ),
    }


def _string(value: Any, fallback: str = "") -> str:
    return value if isinstance(value, str) and value else fallback


def _fixture(payload: Mapping[str, Any]) -> str:
    name = payload.get("fixture") or payload.get("name")
    if isinstance(name, str) and name:
        return name
    status = payload.get("status")
    if isinstance(status, Mapping):
        status_name = status.get("name")
        if isinstance(status_name, str) and status_name:
            return status_name
    return "<name>"


def _action_from_command(command: str | None) -> str | None:
    if not command:
        return None
    if command.startswith("/fig_compile ") or command.startswith("bash scripts/compile.sh "):
        return ACTION_RUN_COMPILE
    if "scripts/text_boundary_spec_helper.py" in command:
        return ACTION_CREATE_OR_FIX_SOURCE
    if command.startswith("/fig_critique "):
        return ACTION_RUN_CRITIQUE
    if command.startswith("/fig_adjudicate ") or "scripts/critique_adjudication.py" in command:
        return ACTION_RUN_ADJUDICATE
    if command.startswith("/fig_loop ") or "scripts/fig_loop.py" in command:
        return ACTION_RUN_FIG_LOOP
    if command.startswith("/fig_export ") or "scripts/run_export.py" in command:
        return ACTION_RUN_EXPORT
    if "svg_polish" in command:
        return ACTION_POLISH_HANDOFF_STOP
    return None


def _action_from_status(status: Mapping[str, Any]) -> str:
    render = status.get("render_state")
    critique = status.get("critique_state")
    export = status.get("export_state")
    final_artifact = status.get("final_artifact_state")
    if render in {"NOT_SCAFFOLDED", "NOT_AUTHORED"}:
        return ACTION_CREATE_OR_FIX_SOURCE
    if render in {"MISSING", "STALE"}:
        return ACTION_RUN_COMPILE
    if critique in {"REFERENCE_MISSING", "MISSING", "STALE"}:
        return ACTION_RUN_CRITIQUE
    if export in {"MISSING", "STALE"}:
        return ACTION_RUN_EXPORT
    if export == "TRACKED_GOLDEN":
        return ACTION_RELEASE_BLOCKED
    if final_artifact in {"MISSING", "INVALID", "STALE", "BLOCKED"}:
        return ACTION_POLISH_HANDOFF_STOP
    if status.get("release_ready") is True or status.get("workflow_ready") is True:
        return ACTION_COMPLETE
    return ACTION_RUN_FIG_LOOP


def _allowed_scope(
    action: str,
    fixture: str,
    patch_handoff: Mapping[str, Any] | None,
    blocking_source: str = "",
) -> list[str]:
    if action == ACTION_CREATE_OR_FIX_SOURCE or (
        action == ACTION_POLISH_HANDOFF_STOP and blocking_source == STOP_SEMANTIC_BACKPORT
    ):
        return [
            f"examples/{fixture}/spec.yaml",
            f"examples/{fixture}/briefing.md",
            f"examples/{fixture}/{fixture}.tex",
        ]
    if action == ACTION_RUN_COMPILE:
        return [f"examples/{fixture}/build/", "compile reports"]
    if action == ACTION_RUN_CRITIQUE:
        return [
            f"examples/{fixture}/critique.md",
            f"examples/{fixture}/build/audit_crops/",
        ]
    if action == ACTION_RUN_ADJUDICATE:
        return [f"examples/{fixture}/critique_adjudication.yaml"]
    if action == ACTION_RUN_FIG_LOOP:
        return [".scratch/fig-loop-runs/"]
    if action == ACTION_RUN_EXPORT:
        return [f"examples/{fixture}/exports/"]
    if action == ACTION_PATCH_HANDOFF_STOP:
        if isinstance(patch_handoff, Mapping):
            allowed = patch_handoff.get("allowed_edit_scope")
            if isinstance(allowed, list) and all(isinstance(item, str) for item in allowed):
                return list(allowed)
        return [f"examples/{fixture}/{fixture}.tex"]
    if action == ACTION_POLISH_HANDOFF_STOP:
        return [f"examples/{fixture}/polish/"]
    return ["read-only"]


def _forbidden_scope(action: str, patch_handoff: Mapping[str, Any] | None) -> list[str]:
    if action == ACTION_PATCH_HANDOFF_STOP and isinstance(patch_handoff, Mapping):
        forbidden = patch_handoff.get("forbidden_edit_scope")
        if isinstance(forbidden, list) and all(isinstance(item, str) for item in forbidden):
            return list(forbidden)
    return list(_DEFAULT_FORBIDDEN_SCOPE)


def _summary(
    *,
    fixture: str,
    action: str,
    reason: str,
    blocking_source: str,
    safe_command: str | None,
    requires_human: bool,
    evidence_refs: list[str],
    patch_handoff: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "action": action,
        "reason": reason,
        "blocking_source": blocking_source,
        "safe_command": safe_command,
        "requires_human": requires_human,
        "decision_boundary": _decision_boundary(
            action=action,
            blocking_source=blocking_source,
            requires_human=requires_human,
        ),
        "allowed_scope": _allowed_scope(action, fixture, patch_handoff, blocking_source),
        "forbidden_scope": _forbidden_scope(action, patch_handoff),
        "evidence_refs": evidence_refs,
    }


def status_next_action_summary(status: Mapping[str, Any]) -> dict[str, Any]:
    """Compress a /fig_status result without changing status.next semantics."""
    fixture = _fixture(status)
    explanation = status.get("status_explanation")
    first_blocker = explanation.get("first_blocker") if isinstance(explanation, Mapping) else None
    safe_command = None
    blocking_source = "status.next"
    reason = _string(status.get("next"), "inspect figure status")
    evidence_refs = ["status.next"]
    manual = False
    if isinstance(first_blocker, Mapping):
        code = _string(first_blocker.get("code"), "none")
        blocking_source = code
        reason = _string(first_blocker.get("message"), reason)
        command = first_blocker.get("next_command")
        safe_command = command if isinstance(command, str) and command else None
        manual = first_blocker.get("manual") is True
        evidence_refs = [f"status.first_blocker:{code}"]
    action = _action_from_command(safe_command) or _action_from_status(status)
    return _summary(
        fixture=fixture,
        action=action,
        reason=reason,
        blocking_source=blocking_source,
        safe_command=safe_command,
        requires_human=manual and blocking_source in _HUMAN_BLOCKER_CODES,
        evidence_refs=evidence_refs,
    )


def driver_next_action_summary(driver_summary: Mapping[str, Any]) -> dict[str, Any]:
    """Compress the already-selected /fig_drive dry-run action."""
    fixture = _fixture(driver_summary)
    action = _string(driver_summary.get("action"), ACTION_RUN_FIG_LOOP)
    stop_boundary = driver_summary.get("stop_boundary")
    blocking_source = (
        stop_boundary if isinstance(stop_boundary, str) and stop_boundary else "driver.action"
    )
    safe_command = driver_summary.get("safe_command")
    if not isinstance(safe_command, str):
        safe_command = None
    evidence_refs = []
    if isinstance(stop_boundary, str) and stop_boundary:
        evidence_refs.append(f"driver.stop_boundary:{stop_boundary}")
    status_explanation = driver_summary.get("status_explanation")
    if isinstance(status_explanation, Mapping):
        first = status_explanation.get("first_blocker")
        if isinstance(first, Mapping):
            code = _string(first.get("code"))
            if code and code != "none":
                evidence_refs.append(f"status.first_blocker:{code}")
    loop_checkpoint = driver_summary.get("loop_checkpoint")
    if isinstance(loop_checkpoint, Mapping):
        stop = _string(loop_checkpoint.get("final_stop_reason"))
        if stop:
            evidence_refs.append(f"loop.final_stop_reason:{stop}")
    ready_improvement = driver_summary.get("ready_improvement_summary")
    marginal_return = None
    if isinstance(ready_improvement, Mapping):
        marginal_return = ready_improvement.get("marginal_return_summary")
        if isinstance(marginal_return, Mapping):
            marginal_state = _string(marginal_return.get("state"))
            if marginal_state:
                evidence_refs.append(f"ready_improvement.marginal_return:{marginal_state}")
    closeout = driver_summary.get("closeout")
    if isinstance(closeout, Mapping):
        blocking = closeout.get("blocking_step_ids")
        if isinstance(blocking, list) and blocking:
            joined = ",".join(str(item) for item in blocking)
            evidence_refs.append(f"closeout.blocking_steps:{joined}")
    if not evidence_refs:
        evidence_refs.append("driver.action")
    summary = _summary(
        fixture=fixture,
        action=action,
        reason=_string(driver_summary.get("reason"), "follow selected driver action"),
        blocking_source=blocking_source,
        safe_command=safe_command,
        requires_human=action in _HUMAN_ACTIONS or blocking_source in _HUMAN_STOP_BOUNDARIES,
        evidence_refs=evidence_refs,
    )
    if isinstance(ready_improvement, Mapping):
        summary["ready_improvement_state"] = _string(
            ready_improvement.get("state"),
            "unknown",
        )
        summary["ready_improvement_safe_to_ship"] = ready_improvement.get("safe_to_ship") is True
        if (
            action == ACTION_COMPLETE
            and summary["ready_improvement_state"] == "ready_but_improvable"
            and summary["ready_improvement_safe_to_ship"] is True
        ):
            summary["decision_boundary"] = _advisory_only_boundary()
        candidate_count = ready_improvement.get("candidate_count")
        summary["optional_candidate_count"] = (
            candidate_count if isinstance(candidate_count, int) else 0
        )
        if isinstance(marginal_return, Mapping):
            summary["marginal_return_state"] = _string(
                marginal_return.get("state"),
                "unknown",
            )
            reason = _string(marginal_return.get("reason"))
            if reason:
                summary["marginal_return_reason"] = reason
    return summary


def loop_next_action_summary(
    loop_decision: Mapping[str, Any],
    status: Mapping[str, Any],
    patch_handoff: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Compress one fig_loop decision iteration."""
    fixture = _fixture(status)
    stop_reason = _string(loop_decision.get("stop_reason"), "unknown")
    recommended = _string(loop_decision.get("recommended_next_action"), "inspect figure state")
    action = _action_from_command(recommended)
    if action is None:
        if stop_reason in {"patch_target_recommended", "active_subregion_recommended"}:
            action = ACTION_PATCH_HANDOFF_STOP
        elif stop_reason == "ambiguous_patch_selection":
            action = ACTION_PATCH_HANDOFF_STOP
        elif stop_reason == "human_gate_required":
            action = ACTION_HUMAN_GATE_STOP
        elif stop_reason in {"stale_adjudication", "invalid_adjudication", "missing_adjudication"}:
            action = ACTION_RUN_ADJUDICATE
        elif stop_reason in {"no_actionable_findings", "verify_only_complete"}:
            action = ACTION_COMPLETE
        else:
            action = _action_from_status(status)
    safe_command = recommended if recommended.startswith("/") else None
    return _summary(
        fixture=fixture,
        action=action,
        reason=recommended,
        blocking_source=stop_reason,
        safe_command=safe_command,
        requires_human=action in _HUMAN_ACTIONS
        or loop_decision.get("human_gate_status") == "required",
        evidence_refs=[f"loop.stop_reason:{stop_reason}"],
        patch_handoff=patch_handoff,
    )


def closeout_next_action_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    """Compress a fig_closeout report into the shared next-action shape."""
    fixture = _fixture(report)
    steps = report.get("steps")
    next_step = None
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, Mapping) and step.get("state") == "needs_action":
                next_step = step
                break
        if next_step is None:
            for step in steps:
                if isinstance(step, Mapping) and step.get("state") == "blocked":
                    next_step = step
                    break
    next_action = report.get("next_action")
    safe_command = (
        next_action if isinstance(next_action, str) and next_action.startswith("/") else None
    )
    action = _action_from_command(safe_command)
    blocking_source = "closeout.complete"
    reason = "closeout complete"
    evidence_refs: list[str] = []
    blocking_steps = report.get("blocking_step_ids")
    if isinstance(blocking_steps, list) and blocking_steps:
        joined = ",".join(str(item) for item in blocking_steps)
        evidence_refs.append(f"closeout.blocking_steps:{joined}")
    if isinstance(next_step, Mapping):
        step_id = _string(next_step.get("id"), "unknown")
        blocking_source = f"closeout:{step_id}"
        reason = _string(next_step.get("reason"), _string(next_action, "inspect closeout"))
        command = next_step.get("command")
        safe_command = command if isinstance(command, str) and command else safe_command
        action = _action_from_command(safe_command) or ACTION_HUMAN_GATE_STOP
        evidence_refs.append(f"closeout.next_step:{step_id}")
    if action is None:
        action = ACTION_COMPLETE
    if not evidence_refs:
        evidence_refs.append("closeout.complete")
    return _summary(
        fixture=fixture,
        action=action,
        reason=reason,
        blocking_source=blocking_source,
        safe_command=safe_command,
        requires_human=action in _HUMAN_ACTIONS,
        evidence_refs=evidence_refs,
    )
