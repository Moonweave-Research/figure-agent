"""Typed JSON contracts for figure convergence attempts."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

FIGURE_SPEC_SCHEMA = "figure-agent.figure-spec.v1"
JOURNAL_GUIDE_SCHEMA = "figure-agent.journal-guide.v1"
AESTHETIC_OBJECTIVE_SCHEMA = "figure-agent.aesthetic-objective.v1"
FIGURE_ATTEMPT_SCHEMA = "figure-agent.figure-attempt.v1"
CONVERGENCE_DECISION_SCHEMA = "figure-agent.convergence-decision.v1"

ATTEMPT_DECISIONS = {"accept", "retry", "rollback", "human_review", "reject", "stop"}
TARGET_MEDIA = {"journal_paper"}


class ConvergenceModelError(ValueError):
    """Raised when convergence contract data is unsafe or incomplete."""


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_hash(payload: dict[str, Any]) -> str:
    return "sha256:" + sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _require_mapping(payload: Any, label: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ConvergenceModelError(f"{label}_invalid")
    return payload


def _require_nonempty_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ConvergenceModelError(f"{field}_missing")
    return value


def _require_hash(payload: dict[str, Any], field: str) -> str:
    value = _require_nonempty_string(payload, field)
    if not value.startswith("sha256:") or len(value) != 71:
        raise ConvergenceModelError(f"{field}_invalid")
    return value


def _require_schema(payload: dict[str, Any], expected: str) -> None:
    if payload.get("schema") != expected:
        raise ConvergenceModelError("schema_invalid")


def _validate_score(value: Any, field: str) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ConvergenceModelError(f"{field}_invalid") from exc
    if score < 0.0 or score > 1.0:
        raise ConvergenceModelError(f"{field}_out_of_range")
    return score


def validate_figure_spec(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(_require_mapping(payload, "figure_spec"))
    _require_schema(payload, FIGURE_SPEC_SCHEMA)
    _require_nonempty_string(payload, "figure_id")
    _require_nonempty_string(payload, "user_goal")
    medium = _require_nonempty_string(payload, "target_medium")
    if medium not in TARGET_MEDIA:
        raise ConvergenceModelError("target_medium_invalid")
    source = _require_mapping(payload.get("source"), "source")
    _require_nonempty_string(source, "editable_path")
    _require_hash(source, "source_hash")
    return payload


def validate_journal_guide(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(_require_mapping(payload, "journal_guide"))
    _require_schema(payload, JOURNAL_GUIDE_SCHEMA)
    _require_nonempty_string(payload, "target_journal")
    _require_hash(payload, "guide_hash")
    _require_mapping(payload.get("hard_constraints"), "hard_constraints")
    return payload


def validate_aesthetic_objective(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(_require_mapping(payload, "aesthetic_objective"))
    _require_schema(payload, AESTHETIC_OBJECTIVE_SCHEMA)
    scores = _require_mapping(payload.get("scores"), "scores")
    _validate_score(scores.get("overall"), "overall")
    return payload


def validate_figure_attempt(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(_require_mapping(payload, "figure_attempt"))
    _require_schema(payload, FIGURE_ATTEMPT_SCHEMA)
    _require_nonempty_string(payload, "attempt_id")
    _require_nonempty_string(payload, "figure_id")
    _require_nonempty_string(payload, "user_goal")
    medium = _require_nonempty_string(payload, "target_medium")
    if medium not in TARGET_MEDIA:
        raise ConvergenceModelError("target_medium_invalid")
    _require_hash(payload, "spec_hash")
    _require_hash(payload, "journal_guide_hash")
    _require_mapping(payload.get("outputs"), "outputs")
    journal_constraints = _require_mapping(
        payload.get("journal_constraints"),
        "journal_constraints",
    )
    if not isinstance(journal_constraints.get("passed"), bool):
        raise ConvergenceModelError("journal_constraints_passed_invalid")
    semantic_score = _require_mapping(payload.get("semantic_score"), "semantic_score")
    if not isinstance(semantic_score.get("complete"), bool):
        raise ConvergenceModelError("semantic_score_complete_invalid")
    aesthetic_score = _require_mapping(payload.get("aesthetic_score"), "aesthetic_score")
    _validate_score(aesthetic_score.get("overall"), "overall")
    decision = payload.get("decision")
    if decision is not None and decision not in ATTEMPT_DECISIONS:
        raise ConvergenceModelError("decision_invalid")
    return payload


def validate_convergence_decision(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(_require_mapping(payload, "convergence_decision"))
    _require_schema(payload, CONVERGENCE_DECISION_SCHEMA)
    decision = _require_nonempty_string(payload, "decision")
    if decision not in ATTEMPT_DECISIONS:
        raise ConvergenceModelError("decision_invalid")
    _require_nonempty_string(payload, "attempt_id")
    _require_nonempty_string(payload, "selected_attempt_id")
    reasons = payload.get("reasons")
    if not isinstance(reasons, list) or not all(isinstance(item, str) for item in reasons):
        raise ConvergenceModelError("reasons_invalid")
    return payload
