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
    assert "memory_prior" not in rendered_score["scores"]


def test_memory_prior_changes_reviewable_candidate_score() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "edit_class": "label_offset",
        "verification": {"hard_gate_state": "pass"},
    }
    memory_index = {
        "schema": "figure-agent.quality-memory-index.v1",
        "families": {
            "label_offset": {
                "attempts": 3,
                "recommended_prior": 0.2,
            }
        },
    }

    score = candidate_rank.score_manifest(manifest, memory_index=memory_index)

    assert score["scores"]["memory_prior"] == 0.2
    assert score["rank_score"] == 0.7
    assert "memory_prior:label_offset:+0.2000" in score["evidence"]["positive"]
    assert score["effective_apply_authority"] == "apply_eligible"


def test_memory_prior_does_not_change_effective_apply_authority() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "review_only",
        "edit_class": "label_offset",
        "verification": {"hard_gate_state": "pass"},
    }
    memory_index = {
        "schema": "figure-agent.quality-memory-index.v1",
        "families": {
            "label_offset": {
                "attempts": 3,
                "recommended_prior": 0.25,
            }
        },
    }

    score = candidate_rank.score_manifest(manifest, memory_index=memory_index)

    assert score["scores"]["memory_prior"] == 0.25
    assert score["rank_score"] == 0.75
    assert score["effective_apply_authority"] == "review_only"
    assert "effective_apply_authority" not in memory_index["families"]["label_offset"]


def test_negative_memory_prior_lowers_score_and_adds_negative_evidence() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "edit_class": "label_offset",
        "verification": {"hard_gate_state": "pass"},
    }
    memory_index = {
        "schema": "figure-agent.quality-memory-index.v1",
        "families": {
            "label_offset": {
                "attempts": 3,
                "recommended_prior": -0.1,
            }
        },
    }

    score = candidate_rank.score_manifest(manifest, memory_index=memory_index)

    assert score["scores"]["memory_prior"] == -0.1
    assert score["rank_score"] == 0.4
    assert "memory_prior:label_offset:-0.1000" in score["evidence"]["negative"]


def test_memory_prior_cannot_promote_rejected_candidate() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "edit_class": "label_offset",
        "verification": {"hard_gate_state": "rejected"},
    }
    memory_index = {
        "schema": "figure-agent.quality-memory-index.v1",
        "families": {
            "label_offset": {
                "attempts": 3,
                "recommended_prior": 0.25,
            }
        },
    }

    score = candidate_rank.score_manifest(manifest, memory_index=memory_index)

    assert score["scores"]["memory_prior"] == 0.0
    assert score["rank_score"] == 0.0
    assert score["verdict"] == "rejected"
    assert score["effective_apply_authority"] == "rejected"


def test_memory_prior_can_use_candidate_set_family_metadata() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "verification": {"hard_gate_state": "pass"},
    }
    candidate = {"edit_class": "label_offset"}
    memory_index = {
        "schema": "figure-agent.quality-memory-index.v1",
        "families": {
            "label_offset": {
                "attempts": 3,
                "recommended_prior": 0.1,
            }
        },
    }

    score = candidate_rank.score_manifest(
        manifest,
        candidate=candidate,
        memory_index=memory_index,
    )

    assert score["scores"]["memory_prior"] == 0.1


def test_detector_improvement_adds_soft_prior_and_evidence() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "verification": {"hard_gate_state": "pass"},
    }
    detector_evaluation = {
        "state": "passed",
        "movements": [
            {
                "metric": "text_boundary.blocker_count",
                "operator": "decrease_or_equal",
                "state": "passed",
                "baseline": 3,
                "candidate": 1,
            }
        ],
    }

    score = candidate_rank.score_manifest(manifest, detector_evaluation=detector_evaluation)

    assert score["scores"]["detector_prior"] == 0.15
    assert score["rank_score"] == 0.65
    assert "detector:text_boundary.blocker_count:decrease_or_equal" in (
        score["evidence"]["positive"]
    )


def test_detector_regression_lowers_soft_score() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "verification": {"hard_gate_state": "pass"},
    }
    detector_evaluation = {
        "state": "failed",
        "movements": [
            {
                "metric": "text_boundary.blocker_count",
                "operator": "decrease_or_equal",
                "state": "failed",
                "baseline": 1,
                "candidate": 3,
            }
        ],
    }

    score = candidate_rank.score_manifest(manifest, detector_evaluation=detector_evaluation)

    assert score["scores"]["detector_prior"] == -0.2
    assert score["rank_score"] == 0.3
    assert "detector:text_boundary.blocker_count:failed" in score["evidence"]["negative"]


def test_detector_improvement_cannot_promote_rejected_candidate() -> None:
    manifest = {
        "schema": "figure-agent.candidate-manifest.v1",
        "candidate_id": "CAND001",
        "apply_authority": "apply_eligible",
        "verification": {"hard_gate_state": "rejected"},
    }
    detector_evaluation = {
        "state": "passed",
        "movements": [
            {
                "metric": "text_boundary.blocker_count",
                "operator": "decrease_or_equal",
                "state": "passed",
                "baseline": 3,
                "candidate": 1,
            }
        ],
    }

    score = candidate_rank.score_manifest(manifest, detector_evaluation=detector_evaluation)

    assert score["scores"]["detector_prior"] == 0.0
    assert score["rank_score"] == 0.0
    assert score["effective_apply_authority"] == "rejected"
