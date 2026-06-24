"""Closeout-to-driver recommendation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CloseoutRecommendation:
    kind: str
    reason: str


def closeout_report(name: str, *, repo_root: Path) -> dict[str, Any]:
    from fig_closeout import FigCloseoutError, compute_closeout  # noqa: PLC0415

    try:
        return compute_closeout(name, repo_root=repo_root)
    except FigCloseoutError:
        return {"closeout_complete": True, "next_action": "closeout not applicable"}


def compact_closeout(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "closeout_complete": report.get("closeout_complete"),
        "next_action": report.get("next_action"),
        "blocking_step_ids": list(report.get("blocking_step_ids") or ()),
        "steps": list(report.get("steps") or ()),
    }


def closeout_recommendation(report: dict[str, Any] | None) -> CloseoutRecommendation | None:
    if not isinstance(report, dict) or report.get("closeout_complete") is True:
        return None
    compact = compact_closeout(report)
    blocking_step_ids = compact["blocking_step_ids"]
    if blocking_step_ids == ["loop_rerun"]:
        reason = None
        for step in compact["steps"]:
            if isinstance(step, dict) and step.get("id") == "loop_rerun":
                reason = step.get("reason")
                break
        if reason == "no post-patch fig_loop run was found":
            return None
    next_action = str(report.get("next_action") or "")
    if next_action.startswith("/fig_export ") and "--force-golden" not in next_action:
        return CloseoutRecommendation(
            kind="export",
            reason=f"closeout is incomplete; export step requires {next_action}.",
        )
    if next_action.startswith("/fig_loop "):
        return CloseoutRecommendation(
            kind="loop",
            reason="closeout is incomplete; rerun /fig_loop after post-patch evidence is current.",
        )
    for step in compact["steps"]:
        if not isinstance(step, dict):
            continue
        if step.get("id") == "export":
            evidence = step.get("evidence")
            if isinstance(evidence, dict) and "--force-golden" in str(
                evidence.get("approval_command")
            ):
                return CloseoutRecommendation(
                    kind="force_golden",
                    reason=(
                        "closeout is incomplete; tracked golden export requires "
                        "manual approval."
                    ),
                )
    return CloseoutRecommendation(
        kind="blocked",
        reason=f"closeout is incomplete: {next_action or 'inspect /fig_closeout report'}.",
    )
