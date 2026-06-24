"""Escalation-level policy for fig_loop stop reasons."""

from __future__ import annotations

from typing import Any


def escalation_summary(loop_decision: dict[str, Any]) -> dict[str, Any]:
    stop_reason = loop_decision["stop_reason"]
    recommended = loop_decision.get("recommended_next_action", "")
    if stop_reason in {"human_gate_required", "basin_detected"}:
        level = "human_review_required"
    elif stop_reason in {"patch_target_recommended", "active_subregion_recommended"}:
        level = "patch_allowed"
    elif stop_reason == "ambiguous_patch_selection":
        level = "ambiguous_patch_selection"
    elif stop_reason == "status_action_required" and "--force-golden" in recommended:
        level = "manual_approval_required"
    elif stop_reason == "status_action_required" and "accepted: true" in recommended:
        level = "manual_approval_required"
    elif stop_reason in {
        "status_action_required",
        "missing_adjudication",
        "stale_adjudication",
        "invalid_adjudication",
        "reference_input_missing",
    }:
        level = "agent_action_required"
    elif stop_reason == "no_actionable_findings":
        level = "none"
    else:
        level = "none"

    return {
        "escalation_level": level,
        "requires_user_input": level in {"manual_approval_required", "human_review_required"},
        "requires_domain_review": level == "human_review_required",
    }
