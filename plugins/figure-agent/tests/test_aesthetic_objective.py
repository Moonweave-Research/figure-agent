from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import aesthetic_objective  # noqa: E402


def test_higher_clarity_and_readability_raise_overall_score() -> None:
    low = aesthetic_objective.score_aesthetic_evidence(
        {
            "rank_score": 0.45,
            "visual_clash_count": 4,
            "label_readability": 0.4,
            "hierarchy_score": 0.45,
            "density_control": 0.4,
        }
    )
    high = aesthetic_objective.score_aesthetic_evidence(
        {
            "rank_score": 0.75,
            "visual_clash_count": 0,
            "label_readability": 0.9,
            "hierarchy_score": 0.85,
            "density_control": 0.8,
        }
    )

    assert high["scores"]["overall"] > low["scores"]["overall"]
    assert high["scores"]["readability"] > low["scores"]["readability"]
    assert high["evidence_state"] == "measured"


def test_excess_decoration_penalty_lowers_overall_score() -> None:
    clean = aesthetic_objective.score_aesthetic_evidence(
        {
            "rank_score": 0.75,
            "label_readability": 0.8,
            "hierarchy_score": 0.8,
            "density_control": 0.8,
        }
    )
    decorated = aesthetic_objective.score_aesthetic_evidence(
        {
            "rank_score": 0.75,
            "label_readability": 0.8,
            "hierarchy_score": 0.8,
            "density_control": 0.8,
            "penalties": [{"id": "excessive_decoration", "weight": 0.2}],
        }
    )

    assert decorated["scores"]["overall"] < clean["scores"]["overall"]
    assert decorated["penalties"][0]["id"] == "excessive_decoration"


def test_missing_evidence_is_explicit_unknown_not_confident_score() -> None:
    objective = aesthetic_objective.score_aesthetic_evidence({})

    assert objective["evidence_state"] == "unknown"
    assert objective["confidence"] == 0.0
    assert objective["scores"]["overall"] == 0.0
    assert objective["not_measured"] == [
        "rank_score",
        "label_readability",
        "hierarchy_score",
        "density_control",
    ]
