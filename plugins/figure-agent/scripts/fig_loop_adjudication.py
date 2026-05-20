"""Adjudication state adapter for verify-only fig loop runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from critique_adjudication import (
    CritiqueAdjudicationError,
    adjudication_is_stale,
    load_adjudication,
)


def adjudication_state(example_dir: Path) -> dict[str, Any]:
    critique_path = example_dir / "critique.md"
    adjudication_path = example_dir / "critique_adjudication.yaml"
    if not adjudication_path.is_file():
        return {"state": "missing", "path": str(adjudication_path), "decision_count": 0}
    try:
        adjudication = load_adjudication(adjudication_path)
        stale = adjudication_is_stale(adjudication_path, critique_path)
    except CritiqueAdjudicationError as exc:
        return {
            "state": "invalid",
            "path": str(adjudication_path),
            "decision_count": 0,
            "error": str(exc),
        }
    return {
        "state": "stale" if stale else "fresh",
        "path": str(adjudication_path),
        "decision_count": len(adjudication.get("decisions", [])),
        "decisions": adjudication.get("decisions", []),
        "source_critique_hash": adjudication["source_critique_hash"],
    }
