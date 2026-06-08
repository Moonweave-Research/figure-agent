from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_contracts  # noqa: E402
import candidate_rank  # noqa: E402


def test_human_required_gate_downgrades_effective_authority() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "verification": {"hard_gate_state": "human_required"},
    }

    score = candidate_rank.score_manifest(manifest)

    assert score["schema"] == "figure-agent.candidate-score.v1"
    assert score["hard_gate_state"] == "human_required"
    assert score["effective_apply_authority"] == "review_only"
    assert score["verdict"] == "reviewable"


def test_rejected_gate_blocks_ranking_above_reviewable() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "verification": {"hard_gate_state": "rejected"},
    }

    score = candidate_rank.score_manifest(manifest)

    assert score["effective_apply_authority"] == "rejected"
    assert score["rank_score"] == 0.0
    assert score["verdict"] == "rejected"


def test_invalid_hard_gate_state_is_not_promoted() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "verification": {"hard_gate_state": "needs_review"},
    }

    with pytest.raises(candidate_contracts.CandidateContractError, match="invalid hard_gate_state"):
        candidate_rank.score_manifest(manifest)


def test_invalid_apply_authority_is_not_promoted() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "auto_apply",
        "verification": {"hard_gate_state": "pass"},
    }

    with pytest.raises(candidate_contracts.CandidateContractError, match="invalid apply_authority"):
        candidate_rank.score_manifest(manifest)
