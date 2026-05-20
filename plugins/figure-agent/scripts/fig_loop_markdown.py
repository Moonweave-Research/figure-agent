"""Markdown rendering for verify-only fig loop decisions."""

from __future__ import annotations

from typing import Any

MODE = "verify-only"


def decision_markdown(
    *,
    name: str,
    goal: str,
    status_result: dict[str, Any],
    adjudication: dict[str, Any],
    loop_decision: dict[str, Any],
    escalation: dict[str, Any],
    patch_handoff: dict[str, Any] | None,
) -> str:
    notes = status_result.get("notes", [])
    notes_text = ", ".join(notes) if notes else "(none)"
    active_patch_target = loop_decision["active_patch_target"]
    if active_patch_target:
        finding_id = active_patch_target["finding_id"]
        patch_target = active_patch_target["patch_target"]
        active_patch_text = f"{finding_id} -> {patch_target}" if finding_id else str(patch_target)
    else:
        active_patch_text = "(none)"
    if patch_handoff:
        handoff_text = f"{patch_handoff['target_type']} {patch_handoff['target_id']}"
    else:
        handoff_text = "(none)"
    return "\n".join(
        [
            f"# Fig Loop Decision: {name}",
            "",
            f"- mode: {MODE}",
            f"- goal: {goal}",
            f"- stop_reason: {loop_decision['stop_reason']}",
            f"- escalation_level: {escalation['escalation_level']}",
            f"- stage: {status_result.get('stage')}/4",
            f"- render_state: {status_result.get('render_state')}",
            f"- critique_state: {status_result.get('critique_state')}",
            f"- export_state: {status_result.get('export_state')}",
            (
                "- final_artifact_state: "
                f"{status_result.get('final_artifact_kind', 'generated_export')} "
                f"{status_result.get('final_artifact_state', 'NONE')} "
                f"{status_result.get('final_artifact_path', '')}"
            ),
            f"- adjudication_state: {adjudication['state']}",
            f"- active_patch_target: {active_patch_text}",
            f"- patch_handoff_target: {handoff_text}",
            f"- notes: {notes_text}",
            f"- recommended_next_action: {loop_decision['recommended_next_action']}",
            "",
            "Verify-only mode records loop evidence only. It does not patch source, "
            "compile outputs, export artifacts, or acceptance state.",
            "",
        ]
    )
