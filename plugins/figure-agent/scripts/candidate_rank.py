"""Rank candidate manifests and compute effective apply authority."""

from __future__ import annotations

from typing import Any

import candidate_contracts

SCHEMA = "figure-agent.candidate-score.v1"


def score_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    hard_gate_state = str(
        (manifest.get("verification") or {}).get("hard_gate_state", "rejected")
    )
    effective = candidate_contracts.effective_apply_authority(
        str(manifest.get("apply_authority", "rejected")),
        hard_gate_state,
    )
    verdict = "rejected" if hard_gate_state == "rejected" else "reviewable"
    rank_score = 0.0 if hard_gate_state == "rejected" else 0.5
    return {
        "schema": SCHEMA,
        "candidate_id": str(manifest.get("candidate_id")),
        "hard_gate_state": hard_gate_state,
        "hard_gate_failures": [] if hard_gate_state == "pass" else [hard_gate_state],
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
