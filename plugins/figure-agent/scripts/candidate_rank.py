"""Rank candidate manifests and compute effective apply authority."""

from __future__ import annotations

from typing import Any

import candidate_contracts

SCHEMA = "figure-agent.candidate-score.v1"


def _stage_status(render_manifest: dict[str, Any] | None, stage: str) -> str:
    if not isinstance(render_manifest, dict):
        return "not_rendered"
    stages = render_manifest.get("stages")
    if not isinstance(stages, dict):
        return "not_rendered"
    value = stages.get(stage)
    if not isinstance(value, dict):
        return "not_rendered"
    return str(value.get("status") or "not_rendered")


def _render_evidence(
    render_manifest: dict[str, Any] | None,
) -> tuple[str, float, dict[str, list[str]]]:
    if not isinstance(render_manifest, dict):
        return "not_rendered", 0.0, {"positive": [], "negative": ["render:not_rendered"]}
    render_status = _stage_status(render_manifest, "evaluate")
    evidence: dict[str, list[str]] = {"positive": [], "negative": []}
    bonus = 0.0
    for stage in ("compile", "export", "crop"):
        status = _stage_status(render_manifest, stage)
        if status in {"failed", "dependency_missing", "blocked"}:
            evidence["negative"].append(f"{stage}:{status}")
    if render_status == "rendered_needs_human_review":
        evidence["positive"].append("rendered_before_after_available")
        bonus = 0.25
    elif render_status in {"failed", "dependency_missing", "blocked"}:
        evidence["negative"].append(f"evaluate:{render_status}")
        bonus = -0.35
    elif render_status == "not_run":
        evidence["negative"].append("evaluate:not_run")
        bonus = -0.1
    return render_status, bonus, evidence


def _candidate_family(manifest: dict[str, Any], candidate: dict[str, Any] | None) -> str:
    candidate = candidate if isinstance(candidate, dict) else {}
    value = (
        manifest.get("edit_family")
        or manifest.get("edit_class")
        or candidate.get("edit_family")
        or candidate.get("edit_class")
        or manifest.get("family")
        or candidate.get("family")
    )
    return str(value) if value else "unknown"


def _memory_prior(
    *,
    family: str,
    memory_index: dict[str, Any] | None,
    hard_gate_state: str,
) -> float:
    if hard_gate_state == "rejected" or not isinstance(memory_index, dict):
        return 0.0
    families = memory_index.get("families")
    if not isinstance(families, dict):
        return 0.0
    family_bucket = families.get(family)
    if not isinstance(family_bucket, dict):
        return 0.0
    try:
        attempts = int(family_bucket.get("attempts") or 0)
        prior = float(family_bucket.get("recommended_prior") or 0.0)
    except (TypeError, ValueError):
        return 0.0
    if attempts < 3:
        return 0.0
    return max(-0.25, min(0.25, prior))


def score_manifest(
    manifest: dict[str, Any],
    *,
    render_manifest: dict[str, Any] | None = None,
    candidate: dict[str, Any] | None = None,
    memory_index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    hard_gate_state = str(
        (manifest.get("verification") or {}).get("hard_gate_state", "rejected")
    )
    effective = candidate_contracts.effective_apply_authority(
        str(manifest.get("apply_authority", "rejected")),
        hard_gate_state,
    )
    verdict = "rejected" if hard_gate_state == "rejected" else "reviewable"
    render_status, render_bonus, evidence = _render_evidence(render_manifest)
    family = _candidate_family(manifest, candidate)
    memory_prior = _memory_prior(
        family=family,
        memory_index=memory_index,
        hard_gate_state=hard_gate_state,
    )
    rank_score = 0.0 if hard_gate_state == "rejected" else max(
        0.0,
        0.5 + render_bonus + memory_prior,
    )
    if memory_index is not None:
        if memory_prior > 0:
            evidence["positive"].append(f"memory_prior:{family}:{memory_prior:+.4f}")
        elif memory_prior < 0:
            evidence["negative"].append(f"memory_prior:{family}:{memory_prior:+.4f}")
    scores = {
        "legibility": 0.0,
        "reference_faithfulness": 0.0,
        "semantic_preservation": 1.0 if hard_gate_state != "rejected" else 0.0,
        "review_burden": 0.5,
    }
    if memory_index is not None:
        scores["memory_prior"] = memory_prior
    return {
        "schema": SCHEMA,
        "candidate_id": str(manifest.get("candidate_id")),
        "hard_gate_state": hard_gate_state,
        "hard_gate_failures": [] if hard_gate_state == "pass" else [hard_gate_state],
        "render_status": render_status,
        "evidence": evidence,
        "scores": scores,
        "rank_score": rank_score,
        "verdict": verdict,
        "effective_apply_authority": effective,
    }
