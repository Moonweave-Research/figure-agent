"""Constraint-first convergence decisions for scientific figure attempts."""

from __future__ import annotations

from typing import Any

import convergence_models

SCHEMA = convergence_models.CONVERGENCE_DECISION_SCHEMA

DEFAULT_POLICY = {
    "max_attempts": 8,
    "min_marginal_improvement": 0.02,
    "rollback_tolerance": 0.02,
    "allow_missing_editable": False,
}


def _policy(raw: dict[str, Any] | None) -> dict[str, Any]:
    policy = dict(DEFAULT_POLICY)
    if raw:
        policy.update(raw)
    return policy


def _score(attempt: dict[str, Any]) -> float:
    aesthetic_score = attempt.get("aesthetic_score")
    if not isinstance(aesthetic_score, dict):
        return 0.0
    try:
        return float(aesthetic_score.get("overall") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _invalid_reasons(attempt: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    try:
        convergence_models.validate_figure_attempt(attempt)
    except convergence_models.ConvergenceModelError as exc:
        return [str(exc)]
    journal = attempt.get("journal_constraints")
    if not isinstance(journal, dict) or journal.get("passed") is not True:
        reasons.append("journal_constraints_failed")
    semantic = attempt.get("semantic_score")
    if not isinstance(semantic, dict) or semantic.get("complete") is not True:
        reasons.append("semantic_correctness_failed")
    elif semantic.get("missing_elements") or semantic.get("incorrect_relations"):
        reasons.append("semantic_correctness_failed")
    outputs = attempt.get("outputs")
    editable = outputs.get("editable") if isinstance(outputs, dict) else None
    if not policy["allow_missing_editable"] and not editable:
        reasons.append("editable_output_missing")
    if isinstance(outputs, dict) and not (outputs.get("preview_png") or outputs.get("pdf")):
        reasons.append("export_output_missing")
    return reasons


def _valid_attempt(attempt: dict[str, Any], policy: dict[str, Any]) -> bool:
    return not _invalid_reasons(attempt, policy)


def _best_valid(history: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any] | None:
    valid = [attempt for attempt in history if _valid_attempt(attempt, policy)]
    if not valid:
        return None
    return max(valid, key=_score)


def _decision(
    *,
    decision: str,
    attempt_id: str,
    selected_attempt_id: str,
    reasons: list[str],
    current_score: float,
    selected_score: float,
    best_previous_attempt_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "schema": SCHEMA,
        "decision": decision,
        "attempt_id": attempt_id,
        "selected_attempt_id": selected_attempt_id,
        "best_previous_attempt_id": best_previous_attempt_id,
        "reasons": reasons,
        "current_aesthetic_score": current_score,
        "selected_aesthetic_score": selected_score,
    }
    return convergence_models.validate_convergence_decision(payload)


def decide_attempt(
    current_attempt: dict[str, Any],
    *,
    history: list[dict[str, Any]] | None = None,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy_data = _policy(policy)
    history = history or []
    attempt_id = str(current_attempt.get("attempt_id") or "")
    current_score = _score(current_attempt)
    invalid_reasons = _invalid_reasons(current_attempt, policy_data)
    best_previous = _best_valid(history, policy_data)
    best_previous_id = (
        str(best_previous.get("attempt_id"))
        if isinstance(best_previous, dict) and best_previous.get("attempt_id")
        else None
    )
    if invalid_reasons:
        return _decision(
            decision="reject",
            attempt_id=attempt_id,
            selected_attempt_id=best_previous_id or attempt_id,
            reasons=invalid_reasons,
            current_score=current_score,
            selected_score=_score(best_previous) if best_previous else current_score,
            best_previous_attempt_id=best_previous_id,
        )
    if best_previous is None:
        return _decision(
            decision="accept",
            attempt_id=attempt_id,
            selected_attempt_id=attempt_id,
            reasons=["first_valid_attempt"],
            current_score=current_score,
            selected_score=current_score,
        )
    previous_score = _score(best_previous)
    improvement = current_score - previous_score
    if improvement < -float(policy_data["rollback_tolerance"]):
        return _decision(
            decision="rollback",
            attempt_id=attempt_id,
            selected_attempt_id=best_previous_id or attempt_id,
            reasons=["current_attempt_worse_than_best_valid_previous"],
            current_score=current_score,
            selected_score=previous_score,
            best_previous_attempt_id=best_previous_id,
        )
    selected_id = attempt_id if current_score >= previous_score else best_previous_id or attempt_id
    selected_score = max(current_score, previous_score)
    if len(history) + 1 >= int(policy_data["max_attempts"]):
        return _decision(
            decision="stop",
            attempt_id=attempt_id,
            selected_attempt_id=selected_id,
            reasons=["max_attempts_reached"],
            current_score=current_score,
            selected_score=selected_score,
            best_previous_attempt_id=best_previous_id,
        )
    if improvement < float(policy_data["min_marginal_improvement"]):
        return _decision(
            decision="stop",
            attempt_id=attempt_id,
            selected_attempt_id=selected_id,
            reasons=["marginal_improvement_below_threshold"],
            current_score=current_score,
            selected_score=selected_score,
            best_previous_attempt_id=best_previous_id,
        )
    return _decision(
        decision="accept",
        attempt_id=attempt_id,
        selected_attempt_id=attempt_id,
        reasons=["current_attempt_improves_best_valid_previous"],
        current_score=current_score,
        selected_score=current_score,
        best_previous_attempt_id=best_previous_id,
    )
