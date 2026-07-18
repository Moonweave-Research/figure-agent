"""Candidate render-policy and review-threshold scoring helpers.

Pure scoring utilities lifted out of ``quality_search`` so the ranking-evidence
signal ``rendered_change_below_review_threshold`` (emitted by ``candidate_rank``
into ``evidence['negative']``) is consumed in one place. No dependency on
``quality_search`` internals; imported back into that module by name.
"""

from __future__ import annotations

from typing import Any

_BELOW_REVIEW_THRESHOLD_NEGATIVES = frozenset(
    {"rendered_change_below_review_threshold", "rendered_no_pixel_change"}
)


def _bounded_float(
    value: Any,
    *,
    default: float = 0.0,
    lower: float = -1.0,
    upper: float = 1.0,
) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, lower), upper)


def _bounded_int(value: Any, *, default: int = 0, lower: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, lower)


def _ranking_evidence(ranking: dict[str, Any] | None, polarity: str) -> list[str]:
    if not isinstance(ranking, dict):
        return []
    evidence = ranking.get("evidence")
    values = evidence.get(polarity) if isinstance(evidence, dict) else None
    if not isinstance(values, list):
        return []
    return [str(item) for item in values]


def _ranking_negative_set(ranking: dict[str, Any] | None) -> set[str]:
    return set(_ranking_evidence(ranking, "negative"))


def _ranking_evidence_payload(ranking: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(ranking, dict) and isinstance(ranking.get("evidence"), dict):
        return ranking["evidence"]
    return {"positive": [], "negative": []}


def _ranking_below_review_threshold(ranking: dict[str, Any] | None) -> bool:
    return bool(_BELOW_REVIEW_THRESHOLD_NEGATIVES & _ranking_negative_set(ranking))


def _score_negative_set(score: dict[str, Any]) -> set[str]:
    evidence = score.get("ranking_evidence")
    values = evidence.get("negative") if isinstance(evidence, dict) else None
    if not isinstance(values, list):
        return set()
    return {str(item) for item in values}


def _has_below_review_threshold_evidence(score: dict[str, Any]) -> bool:
    return bool(_BELOW_REVIEW_THRESHOLD_NEGATIVES & _score_negative_set(score))


def _render_policy_adjustment(ranking: dict[str, Any] | None) -> tuple[float, float]:
    if not isinstance(ranking, dict):
        return (0.0, 0.0)
    rank_score = ranking.get("rank_score")
    if rank_score is None:
        return (0.0, 0.0)
    adjustment = (_bounded_float(rank_score, default=0.5) - 0.5) * 0.16
    negative = _ranking_negative_set(ranking)
    render_status = str(ranking.get("render_status") or "")
    penalty = 0.0
    if "rendered_no_pixel_change" in negative:
        penalty -= 0.08
    elif "rendered_change_below_review_threshold" in negative:
        penalty -= 0.06
    elif render_status and render_status not in {
        "not_rendered",
        "rendered_needs_human_review",
    }:
        penalty -= 0.04
    return (round(adjustment, 4), round(penalty, 4))
