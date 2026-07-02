"""Readiness policy for /fig_status state vectors."""

from __future__ import annotations

from collections.abc import Mapping

from export_freshness import EXPORT_FRESH, EXPORT_TRACKED_GOLDEN
from status_next_policy import critique_needs_action

_NON_BLOCKING_WORKFLOW_NOTE_PREFIXES = ("coordinate_hints_", "final_artifact_")


def workflow_ready(
    *,
    stage: int,
    notes: list[str],
    exports_substate: str,
    render_state: str,
    critique_requires_action: bool,
) -> bool:
    blocking_notes = [
        note
        for note in notes
        if not note.startswith(_NON_BLOCKING_WORKFLOW_NOTE_PREFIXES)
    ]
    return (
        stage == 4
        and not blocking_notes
        and render_state == "FRESH"
        and exports_substate in {EXPORT_FRESH, EXPORT_TRACKED_GOLDEN}
        and not critique_requires_action
    )


def golden_ready(*, workflow_ready: bool, accepted: bool | None) -> bool:
    return workflow_ready and accepted is True


def release_ready(
    *,
    golden_ready: bool,
    exports_substate: str,
    final_artifact: Mapping[str, object],
) -> bool:
    if not golden_ready or exports_substate != EXPORT_FRESH:
        return False
    return True


def acceptance_state(accepted: bool | None) -> str:
    if accepted is True:
        return "ACCEPTED"
    if accepted is False:
        return "NOT_ACCEPTED"
    return "NOT_DECLARED"


def acceptance_freshness_state(*, accepted: bool | None, workflow_ready: bool) -> str:
    if accepted is True and not workflow_ready:
        return "accepted_but_stale"
    if accepted is True:
        return "accepted_current"
    return "not_accepted"


def build_status_vector(
    *,
    stage: int,
    notes: list[str],
    accepted: bool | None,
    exports_substate: str,
    render_state: str,
    critique_state: str,
    final_artifact: Mapping[str, object],
    publication_gate: Mapping[str, object] | None = None,
) -> dict:
    publication_gate = publication_gate or {
        "publication_gate_state": "NOT_APPLICABLE",
        "publication_gate_failures": [],
    }
    is_workflow_ready = workflow_ready(
        stage=stage,
        notes=notes,
        exports_substate=exports_substate,
        render_state=render_state,
        critique_requires_action=critique_needs_action(critique_state),
    )
    is_golden_ready = golden_ready(workflow_ready=is_workflow_ready, accepted=accepted)
    is_release_ready = release_ready(
        golden_ready=is_golden_ready,
        exports_substate=exports_substate,
        final_artifact=final_artifact,
    )
    return {
        "render_state": render_state,
        "critique_state": critique_state,
        "export_state": exports_substate,
        "acceptance_state": acceptance_state(accepted),
        "acceptance_freshness_state": acceptance_freshness_state(
            accepted=accepted,
            workflow_ready=is_workflow_ready,
        ),
        "final_artifact_state": final_artifact["state"],
        "final_artifact_kind": final_artifact["kind"],
        "final_artifact_path": final_artifact["path"],
        "workflow_ready": is_workflow_ready,
        "golden_ready": is_golden_ready,
        "release_ready": is_release_ready,
        "final_ready": is_release_ready,
        **publication_gate,
    }
