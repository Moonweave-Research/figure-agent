from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import convergence_models  # noqa: E402


def _attempt(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "figure-agent.figure-attempt.v1",
        "attempt_id": "attempt-001",
        "parent_attempt_id": None,
        "figure_id": "fig-demo",
        "user_goal": "make the figure journal-ready",
        "target_medium": "journal_paper",
        "target_journal": "Nature Communications",
        "figure_type": "mechanism_schematic",
        "spec_hash": "sha256:" + "1" * 64,
        "journal_guide_hash": "sha256:" + "2" * 64,
        "render_backend": "tikz_lualatex",
        "outputs": {
            "editable": "examples/fig-demo/fig-demo.tex",
            "preview_png": "examples/fig-demo/build/fig-demo.png",
            "pdf": "examples/fig-demo/build/fig-demo.pdf",
        },
        "journal_constraints": {"passed": True, "violations": []},
        "semantic_score": {
            "complete": True,
            "missing_elements": [],
            "incorrect_relations": [],
        },
        "aesthetic_score": {
            "overall": 0.74,
            "clarity": 0.8,
            "visual_hierarchy": 0.7,
            "balance": 0.72,
            "readability": 0.81,
            "density_control": 0.7,
            "restraint": 0.78,
            "journal_elegance": 0.72,
        },
        "issues": [],
        "edit_plan": [],
        "decision": "accept",
    }
    payload.update(overrides)
    return payload


def test_figure_attempt_round_trips_with_stable_hash() -> None:
    attempt = convergence_models.validate_figure_attempt(_attempt())
    encoded = convergence_models.canonical_json(attempt)
    decoded = json.loads(encoded)

    assert decoded["schema"] == "figure-agent.figure-attempt.v1"
    assert convergence_models.canonical_hash(decoded) == convergence_models.canonical_hash(
        dict(reversed(list(decoded.items())))
    )


def test_figure_attempt_invalid_decision_fails_closed() -> None:
    with pytest.raises(convergence_models.ConvergenceModelError, match="decision_invalid"):
        convergence_models.validate_figure_attempt(_attempt(decision="maybe"))


def test_figure_attempt_missing_hash_fails_closed() -> None:
    with pytest.raises(convergence_models.ConvergenceModelError, match="spec_hash_missing"):
        convergence_models.validate_figure_attempt(_attempt(spec_hash=""))


def test_convergence_decision_validation_requires_known_decision() -> None:
    decision = convergence_models.validate_convergence_decision(
        {
            "schema": "figure-agent.convergence-decision.v1",
            "decision": "rollback",
            "attempt_id": "attempt-002",
            "selected_attempt_id": "attempt-001",
            "reasons": ["current_attempt_worse_than_best_valid_previous"],
        }
    )

    assert decision["decision"] == "rollback"

    with pytest.raises(convergence_models.ConvergenceModelError, match="decision_invalid"):
        convergence_models.validate_convergence_decision(
            {
                "schema": "figure-agent.convergence-decision.v1",
                "decision": "ship_it",
                "attempt_id": "attempt-002",
                "selected_attempt_id": "attempt-002",
                "reasons": [],
            }
        )
