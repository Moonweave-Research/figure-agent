from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import convergence_controller  # noqa: E402


def _attempt(
    attempt_id: str,
    score: float,
    *,
    journal_passed: bool = True,
    semantic_complete: bool = True,
    editable: str | None = "examples/demo/demo.tex",
) -> dict[str, object]:
    return {
        "schema": "figure-agent.figure-attempt.v1",
        "attempt_id": attempt_id,
        "parent_attempt_id": None,
        "figure_id": "demo",
        "user_goal": "improve figure",
        "target_medium": "journal_paper",
        "target_journal": "Nature Communications",
        "figure_type": "mechanism_schematic",
        "spec_hash": "sha256:" + "1" * 64,
        "journal_guide_hash": "sha256:" + "2" * 64,
        "render_backend": "tikz_lualatex",
        "outputs": {
            "editable": editable,
            "preview_png": "examples/demo/build/demo.png",
            "pdf": "examples/demo/build/demo.pdf",
        },
        "journal_constraints": {
            "passed": journal_passed,
            "violations": [] if journal_passed else [{"id": "font_too_small"}],
        },
        "semantic_score": {
            "complete": semantic_complete,
            "missing_elements": [] if semantic_complete else ["electrode"],
            "incorrect_relations": [],
        },
        "aesthetic_score": {
            "overall": score,
            "clarity": score,
            "visual_hierarchy": score,
            "balance": score,
            "readability": score,
            "density_control": score,
            "restraint": score,
            "journal_elegance": score,
        },
        "issues": [],
        "edit_plan": [],
        "decision": "retry",
    }


def test_journal_violation_rejects_even_when_aesthetic_score_improves() -> None:
    decision = convergence_controller.decide_attempt(
        _attempt("a2", 0.95, journal_passed=False),
        history=[_attempt("a1", 0.60)],
    )

    assert decision["decision"] == "reject"
    assert "journal_constraints_failed" in decision["reasons"]


def test_semantic_failure_cannot_be_accepted() -> None:
    decision = convergence_controller.decide_attempt(
        _attempt("a2", 0.90, semantic_complete=False),
        history=[_attempt("a1", 0.60)],
    )

    assert decision["decision"] == "reject"
    assert "semantic_correctness_failed" in decision["reasons"]


def test_missing_editable_output_rejects_by_default() -> None:
    decision = convergence_controller.decide_attempt(
        _attempt("a2", 0.90, editable=None),
        history=[],
    )

    assert decision["decision"] == "reject"
    assert "editable_output_missing" in decision["reasons"]


def test_higher_aesthetic_score_preferred_among_valid_attempts() -> None:
    decision = convergence_controller.decide_attempt(
        _attempt("a2", 0.82),
        history=[_attempt("a1", 0.70)],
        policy={"min_marginal_improvement": 0.05},
    )

    assert decision["decision"] == "accept"
    assert decision["selected_attempt_id"] == "a2"
    assert decision["best_previous_attempt_id"] == "a1"


def test_rollback_when_new_attempt_is_worse_than_best_valid_previous() -> None:
    decision = convergence_controller.decide_attempt(
        _attempt("a2", 0.62),
        history=[_attempt("a1", 0.80)],
        policy={"rollback_tolerance": 0.05},
    )

    assert decision["decision"] == "rollback"
    assert decision["selected_attempt_id"] == "a1"
    assert "current_attempt_worse_than_best_valid_previous" in decision["reasons"]


def test_convergence_stops_when_improvement_is_below_threshold() -> None:
    decision = convergence_controller.decide_attempt(
        _attempt("a2", 0.815),
        history=[_attempt("a1", 0.80)],
        policy={"min_marginal_improvement": 0.03},
    )

    assert decision["decision"] == "stop"
    assert decision["selected_attempt_id"] == "a2"
    assert "marginal_improvement_below_threshold" in decision["reasons"]


def test_lifetime_history_does_not_trigger_max_attempts_stop() -> None:
    history = [_attempt(f"a{index}", 0.60 + index * 0.01) for index in range(8)]

    decision = convergence_controller.decide_attempt(
        _attempt("fresh", 0.92),
        history=history,
        policy={"max_attempts": 8, "min_marginal_improvement": 0.02},
    )

    assert decision["decision"] == "accept"
    assert decision["selected_attempt_id"] == "fresh"
    assert "max_attempts_reached" not in decision["reasons"]


def test_current_session_attempt_count_can_trigger_max_attempts_stop() -> None:
    decision = convergence_controller.decide_attempt(
        _attempt("a8", 0.92),
        history=[_attempt("a1", 0.70)],
        policy={"max_attempts": 8, "min_marginal_improvement": 0.02},
        current_attempt_count=8,
    )

    assert decision["decision"] == "stop"
    assert decision["selected_attempt_id"] == "a8"
    assert "max_attempts_reached" in decision["reasons"]
