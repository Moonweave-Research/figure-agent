"""Patch-assisted handoff contract for fig_loop."""

from __future__ import annotations

from typing import Any


def patch_handoff(name: str, loop_decision: dict[str, Any]) -> dict[str, Any] | None:
    active_patch_target = loop_decision["active_patch_target"]
    if not active_patch_target:
        return None

    finding_id = active_patch_target.get("finding_id")
    patch_target = active_patch_target["patch_target"]
    target_type = "finding" if finding_id else "subregion"
    target_id = finding_id if finding_id else patch_target
    example_prefix = f"examples/{name}"
    return {
        "target_type": target_type,
        "target_id": target_id,
        "patch_target": patch_target,
        "reason": active_patch_target["reason"],
        "allowed_edit_scope": [
            f"{example_prefix}/{name}.tex",
            f"{example_prefix}/authoring_plan.md",
            f"{example_prefix}/subregion_iteration_log.md",
        ],
        "forbidden_edit_scope": [
            "accepted",
            "golden_contract",
            f"{example_prefix}/exports/",
            f"{example_prefix}/build/",
            f"{example_prefix}/critique.md",
            "unrelated examples",
            "broad refactors",
            "multiple findings in one patch",
        ],
        "required_closeout_checks": [
            f"/fig_compile {name}",
            f"/fig_critique {name} when critique freshness requires it",
            f"update or recreate {example_prefix}/critique_adjudication.yaml",
            "preserve unresolved findings",
            f"/fig_loop {name} --goal <same goal or next goal>",
        ],
        "unresolved_findings_requirement": (
            "Do not delete, rewrite, or hide unresolved critique findings; record only the"
            " selected target decision in critique_adjudication.yaml."
        ),
    }
