"""Axis record and evaluation-state helpers for fig_loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def axis_record(
    *,
    state: Any,
    verdict: str,
    source: str,
    evaluation_state: str,
    evidence_path: Path | None = None,
    **metadata: Any,
) -> dict[str, Any]:
    record = {
        "state": state,
        "verdict": verdict,
        "source": source,
        "evidence_path": str(evidence_path) if evidence_path else None,
        "evaluation_state": evaluation_state,
    }
    record.update(metadata)
    return record


def status_axis_evaluation(
    state: Any,
    *,
    passed_values: set[str],
    not_configured_values: set[str] | None = None,
    blocked_values: set[str] | None = None,
) -> str:
    if state in passed_values:
        return "passed"
    if not_configured_values and state in not_configured_values:
        return "not_configured"
    if blocked_values and state in blocked_values:
        return "blocked"
    return "needs_action"


def adjudication_evaluation_state(
    adjudication: dict[str, Any],
    stop_reason: str,
    critique_state: Any,
) -> str:
    if stop_reason in {"patch_target_recommended", "human_gate_required"}:
        return "needs_action"
    if adjudication["state"] == "missing" and critique_state != "FRESH":
        return "not_configured"
    if adjudication["state"] == "fresh":
        return "passed"
    if adjudication["state"] in {"stale", "invalid", "missing"}:
        return "needs_action"
    return "not_evaluated"


def reference_fidelity_evaluation_state(reference_blocked: bool, critique_state: Any) -> str:
    if reference_blocked:
        return "blocked"
    if critique_state == "NOT_REQUIRED":
        return "not_configured"
    return "not_evaluated"


def publication_safety_evaluation_state(
    acceptance_state: Any,
    human_gate_status: str,
) -> str:
    if human_gate_status == "required":
        return "blocked"
    if acceptance_state == "ACCEPTED":
        return "passed"
    if acceptance_state == "NOT_DECLARED":
        return "not_configured"
    return "needs_action"


def adjudication_verdict(adjudication: dict[str, Any], stop_reason: str) -> str:
    if stop_reason == "patch_target_recommended":
        return "actionable"
    if stop_reason == "human_gate_required":
        return "human_gate"
    if adjudication["state"] in {"stale", "invalid", "missing"}:
        return adjudication["state"]
    if stop_reason == "no_actionable_findings" or (
        adjudication["state"] == "fresh" and adjudication.get("decisions")
    ):
        return "complete"
    return "not_actionable"
