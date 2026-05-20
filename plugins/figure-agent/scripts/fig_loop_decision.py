"""Small decision helpers for fig_loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fig_loop_subregion import active_subregion_target


def reference_input_missing(status_result: dict[str, Any]) -> bool:
    reference_notes = {
        "critique_reference_missing",
        "reference_image_missing",
        "panel_reference_image_missing",
    }
    return bool(reference_notes.intersection(status_result.get("notes", [])))


def critique_refresh_action(example_dir: Path, critique_state: Any) -> str:
    state_text = str(critique_state).lower()
    return f"run /fig_critique {example_dir.name} because critique is {state_text}."


def first_decision(adjudication: dict[str, Any], decision: str) -> dict[str, Any] | None:
    if adjudication["state"] != "fresh":
        return None
    for item in adjudication.get("decisions", []):
        if item.get("decision") == decision:
            return item
    return None


def decisions_with_value(adjudication: dict[str, Any], decision: str) -> list[dict[str, Any]]:
    if adjudication["state"] != "fresh":
        return []
    return [item for item in adjudication.get("decisions", []) if item.get("decision") == decision]


def loop_decision(
    status_result: dict[str, Any],
    adjudication: dict[str, Any],
    example_dir: Path,
) -> dict[str, Any]:
    if reference_input_missing(status_result):
        return {
            "stop_reason": "reference_input_missing",
            "recommended_next_action": "fix declared reference inputs before continuing",
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }
    if status_result.get("critique_state") in {"MISSING", "STALE"}:
        return {
            "stop_reason": "status_action_required",
            "recommended_next_action": critique_refresh_action(
                example_dir,
                status_result.get("critique_state"),
            ),
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }
    if adjudication["state"] == "stale":
        return {
            "stop_reason": "stale_adjudication",
            "recommended_next_action": "review or refresh critique_adjudication.yaml",
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }
    if adjudication["state"] == "invalid":
        return {
            "stop_reason": "invalid_adjudication",
            "recommended_next_action": "fix critique_adjudication.yaml",
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }

    human_decision = first_decision(adjudication, "needs_human")
    if human_decision:
        finding_id = human_decision["finding_id"]
        return {
            "stop_reason": "human_gate_required",
            "recommended_next_action": f"human review required for {finding_id}",
            "active_patch_target": None,
            "human_gate_status": "required",
        }

    apply_decisions = decisions_with_value(adjudication, "apply")
    if len(apply_decisions) > 1:
        return {
            "stop_reason": "ambiguous_patch_selection",
            "recommended_next_action": (
                "select exactly one apply decision in critique_adjudication.yaml"
            ),
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }
    if len(apply_decisions) == 1:
        apply_decision = apply_decisions[0]
        finding_id = apply_decision["finding_id"]
        patch_target = apply_decision["patch_target"]
        return {
            "stop_reason": "patch_target_recommended",
            "recommended_next_action": f"patch {finding_id}: {patch_target}",
            "active_patch_target": {
                "finding_id": finding_id,
                "patch_target": patch_target,
                "reason": apply_decision["reason"],
            },
            "human_gate_status": "not_requested",
        }

    if adjudication["state"] == "missing" and (status_result.get("critique_state") == "FRESH"):
        return {
            "stop_reason": "missing_adjudication",
            "recommended_next_action": "create critique_adjudication.yaml",
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }

    active_subregion = active_subregion_target(example_dir)
    if active_subregion:
        return {
            "stop_reason": "active_subregion_recommended",
            "recommended_next_action": (
                f"patch active sub-region: {active_subregion['patch_target']}"
            ),
            "active_patch_target": active_subregion,
            "human_gate_status": "not_requested",
        }

    if (
        status_result.get("workflow_ready")
        and status_result.get("acceptance_state") == "NOT_ACCEPTED"
    ):
        return {
            "stop_reason": "status_action_required",
            "recommended_next_action": status_result.get("next", "inspect figure state"),
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }

    # status.py owns canonical final-artifact next-action prose; the loop only
    # forwards status.next when a polished/final artifact is not ready.
    if status_result.get("workflow_ready") and not status_result.get("final_ready", True):
        return {
            "stop_reason": "status_action_required",
            "recommended_next_action": status_result.get("next", "inspect figure state"),
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }

    if not status_result.get("workflow_ready"):
        return {
            "stop_reason": "status_action_required",
            "recommended_next_action": status_result.get("next", "inspect figure state"),
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }

    if adjudication["state"] == "fresh" and adjudication.get("decisions"):
        return {
            "stop_reason": "no_actionable_findings",
            "recommended_next_action": "no actionable adjudicated findings remain",
            "active_patch_target": None,
            "human_gate_status": "not_requested",
        }

    return {
        "stop_reason": "verify_only_complete",
        "recommended_next_action": status_result.get("next", "inspect figure state"),
        "active_patch_target": None,
        "human_gate_status": "not_requested",
    }
