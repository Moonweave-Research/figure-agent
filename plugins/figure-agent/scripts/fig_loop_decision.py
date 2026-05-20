"""Small decision helpers for fig_loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any


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
