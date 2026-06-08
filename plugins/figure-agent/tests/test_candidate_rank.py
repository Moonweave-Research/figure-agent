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


def test_rendered_candidate_scores_above_dependency_missing_without_apply_promotion() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "verification": {"hard_gate_state": "human_required"},
    }
    rendered = {
        "stages": {
            "compile": {"status": "success"},
            "export": {"status": "success"},
            "crop": {"status": "success"},
            "evaluate": {"status": "rendered_needs_human_review"},
        },
        "visual_deltas": {"pixel_diff_mean": 0.1},
    }
    missing_dep = {
        "stages": {
            "compile": {"status": "dependency_missing"},
            "export": {"status": "not_run"},
            "crop": {"status": "not_run"},
            "evaluate": {"status": "dependency_missing"},
        },
        "diagnostics": [{"category": "dependency_missing", "dependency": "lualatex"}],
    }

    rendered_score = candidate_rank.score_manifest(manifest, render_manifest=rendered)
    missing_score = candidate_rank.score_manifest(manifest, render_manifest=missing_dep)

    assert rendered_score["render_status"] == "rendered_needs_human_review"
    assert missing_score["render_status"] == "dependency_missing"
    assert rendered_score["rank_score"] > missing_score["rank_score"]
    assert rendered_score["effective_apply_authority"] == "review_only"
    assert rendered_score["evidence"]["positive"] == ["rendered_before_after_available"]
    assert missing_score["evidence"]["negative"] == [
        "compile:dependency_missing",
        "evaluate:dependency_missing",
    ]
