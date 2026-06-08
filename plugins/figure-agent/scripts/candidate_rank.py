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


def score_manifest(
    manifest: dict[str, Any],
    *,
    render_manifest: dict[str, Any] | None = None,
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
    rank_score = 0.0 if hard_gate_state == "rejected" else max(0.0, 0.5 + render_bonus)
    return {
        "schema": SCHEMA,
        "candidate_id": str(manifest.get("candidate_id")),
        "hard_gate_state": hard_gate_state,
        "hard_gate_failures": [] if hard_gate_state == "pass" else [hard_gate_state],
        "render_status": render_status,
        "evidence": evidence,
        "scores": {
            "legibility": 0.0,
            "reference_faithfulness": 0.0,
            "semantic_preservation": 1.0 if hard_gate_state != "rejected" else 0.0,
            "review_burden": 0.5,
        },
        "rank_score": rank_score,
        "verdict": verdict,
        "effective_apply_authority": effective,
    }
