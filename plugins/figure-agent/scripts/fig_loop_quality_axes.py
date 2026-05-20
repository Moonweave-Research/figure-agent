"""Quality-axis parsing and summary helpers for fig_loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fig_loop_axis_records import axis_record

QUALITY_VERDICT_RANK = {
    "not_applicable": -1,
    "pass": 0,
    "needs_patch": 1,
    "needs_human": 2,
    "block": 3,
}
QUALITY_EVALUATION_STATE = {
    "not_applicable": "not_configured",
    "pass": "passed",
    "needs_patch": "needs_action",
    "needs_human": "blocked",
    "block": "blocked",
}
STORY_QUALITY_AXES = (
    "message_storyline",
    "panel_role_coherence",
    "composition_layout",
)


def quality_axis(quality_axes: dict[str, Any], axis_name: str) -> dict[str, Any] | None:
    axis = quality_axes.get(axis_name)
    if not isinstance(axis, dict):
        return None
    verdict = axis.get("verdict")
    if not isinstance(verdict, str) or verdict not in QUALITY_VERDICT_RANK:
        return None
    recommended_action = axis.get("recommended_action")
    blocking_items = axis.get("blocking_items")
    return {
        "name": axis_name,
        "verdict": verdict,
        "recommended_action": recommended_action if isinstance(recommended_action, str) else None,
        "blocking_items": blocking_items if isinstance(blocking_items, list) else [],
    }


def quality_axis_summary(
    quality_axes: dict[str, Any] | None,
    axis_names: tuple[str, ...],
) -> dict[str, Any] | None:
    if not quality_axes:
        return None
    axes = [
        axis
        for axis_name in axis_names
        if (axis := quality_axis(quality_axes, axis_name)) is not None
    ]
    if not axes:
        return None
    applicable_axes = [axis for axis in axes if axis["verdict"] != "not_applicable"]
    ranked_axes = applicable_axes or axes
    selected = max(ranked_axes, key=lambda axis: QUALITY_VERDICT_RANK[axis["verdict"]])
    blocking_items: dict[str, list[str]] = {}
    for axis in axes:
        items = [item for item in axis["blocking_items"] if isinstance(item, str) and item.strip()]
        if items:
            blocking_items[axis["name"]] = items
    return {
        "verdict": selected["verdict"],
        "axis_names": [axis["name"] for axis in axes],
        "axis_verdicts": {axis["name"]: axis["verdict"] for axis in axes},
        "recommended_actions": {
            axis["name"]: axis["recommended_action"]
            for axis in axes
            if axis["recommended_action"] is not None
        },
        "blocking_items": blocking_items,
    }


def quality_axis_record(summary: dict[str, Any], critique_path: Path) -> dict[str, Any]:
    verdict = summary["verdict"]
    return axis_record(
        state=verdict,
        verdict=verdict,
        source="critique.quality_axes",
        evidence_path=critique_path,
        evaluation_state=QUALITY_EVALUATION_STATE[verdict],
        quality_axes=summary["axis_names"],
        quality_axis_verdicts=summary["axis_verdicts"],
        quality_axis_recommended_actions=summary["recommended_actions"],
        quality_axis_blocking_items=summary["blocking_items"],
    )
