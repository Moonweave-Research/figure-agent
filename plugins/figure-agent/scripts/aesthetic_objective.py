"""Deterministic scientific-figure aesthetic objective envelope."""

from __future__ import annotations

from typing import Any

import convergence_models

SCHEMA = convergence_models.AESTHETIC_OBJECTIVE_SCHEMA
SCORE_FIELDS = (
    "clarity",
    "visual_hierarchy",
    "balance",
    "readability",
    "density_control",
    "restraint",
    "journal_elegance",
)
REQUIRED_EVIDENCE = (
    "rank_score",
    "label_readability",
    "hierarchy_score",
    "density_control",
)


def _clamp(value: float) -> float:
    return round(min(max(value, 0.0), 1.0), 4)


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _visual_clash_penalty(value: Any) -> float:
    try:
        count = max(int(value), 0)
    except (TypeError, ValueError):
        return 0.0
    return min(count * 0.04, 0.24)


def _penalties(raw: Any) -> tuple[list[dict[str, Any]], float]:
    if not isinstance(raw, list):
        return [], 0.0
    penalties: list[dict[str, Any]] = []
    total = 0.0
    for item in raw:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            continue
        weight = _float_or_none(item.get("weight"))
        weight = 0.05 if weight is None else max(weight, 0.0)
        total += weight
        penalties.append({"id": item_id, "weight": round(weight, 4)})
    return penalties, min(total, 0.5)


def score_aesthetic_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    measured = [key for key in REQUIRED_EVIDENCE if _float_or_none(evidence.get(key)) is not None]
    not_measured = [key for key in REQUIRED_EVIDENCE if key not in measured]
    if not measured:
        scores = {field: 0.0 for field in SCORE_FIELDS}
        scores["overall"] = 0.0
        payload = {
            "schema": SCHEMA,
            "objective": "scientific_figure_quality",
            "evidence_state": "unknown",
            "confidence": 0.0,
            "scores": scores,
            "penalties": [],
            "not_measured": list(REQUIRED_EVIDENCE),
        }
        return convergence_models.validate_aesthetic_objective(payload)

    rank_score = _clamp(_float_or_none(evidence.get("rank_score")) or 0.5)
    readability = _clamp(_float_or_none(evidence.get("label_readability")) or rank_score)
    hierarchy = _clamp(_float_or_none(evidence.get("hierarchy_score")) or rank_score)
    density = _clamp(_float_or_none(evidence.get("density_control")) or rank_score)
    clash_penalty = _visual_clash_penalty(evidence.get("visual_clash_count"))
    explicit_penalties, explicit_penalty = _penalties(evidence.get("penalties"))
    clarity = _clamp((readability + hierarchy + rank_score) / 3.0 - clash_penalty)
    restraint = _clamp(1.0 - explicit_penalty - clash_penalty / 2.0)
    balance = _clamp((hierarchy + density + restraint) / 3.0)
    journal_elegance = _clamp((restraint + readability + density) / 3.0)
    overall = _clamp(
        (
            clarity * 0.22
            + hierarchy * 0.18
            + balance * 0.14
            + readability * 0.18
            + density * 0.12
            + restraint * 0.08
            + journal_elegance * 0.08
        )
        - explicit_penalty
    )
    scores = {
        "overall": overall,
        "clarity": clarity,
        "visual_hierarchy": hierarchy,
        "balance": balance,
        "readability": readability,
        "density_control": density,
        "restraint": restraint,
        "journal_elegance": journal_elegance,
    }
    payload = {
        "schema": SCHEMA,
        "objective": "scientific_figure_quality",
        "evidence_state": "measured" if not not_measured else "partial",
        "confidence": _clamp(len(measured) / len(REQUIRED_EVIDENCE)),
        "scores": scores,
        "penalties": explicit_penalties,
        "not_measured": not_measured,
        "evidence": {
            "rank_score": evidence.get("rank_score"),
            "visual_clash_count": evidence.get("visual_clash_count"),
            "label_readability": evidence.get("label_readability"),
            "hierarchy_score": evidence.get("hierarchy_score"),
            "density_control": evidence.get("density_control"),
        },
    }
    return convergence_models.validate_aesthetic_objective(payload)
