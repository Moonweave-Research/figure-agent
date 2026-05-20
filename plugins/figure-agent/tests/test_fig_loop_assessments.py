from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_assessments import (  # noqa: E402
    JOURNAL_ASSESSMENT_SCHEMA,
    JOURNAL_SCORE_KEYS,
    journal_grade_assessment,
    top_tier_audit_summary,
)


def _write_critique(path: Path, frontmatter: dict[str, object]) -> None:
    path.write_text(
        "---\n" + yaml.safe_dump(frontmatter, sort_keys=False) + "---\n\n# Critique\n",
        encoding="utf-8",
    )


def _valid_scores() -> dict[str, int]:
    return {key: 80 for key in JOURNAL_SCORE_KEYS}


def test_journal_grade_assessment_returns_none_without_fresh_critique(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()

    assert journal_grade_assessment(example_dir, "STALE") is None


def test_journal_grade_assessment_marks_hash_mismatch_stale(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.2",
            "critique_input_hash": "sha256:" + "a" * 64,
            "journal_grade_assessment": {
                "schema": JOURNAL_ASSESSMENT_SCHEMA,
                "scoring_mode": "fresh_reaudit",
                "assessed_artifact_hash": "sha256:" + "b" * 64,
                "score_is_gateable": True,
                "benchmark_level": "solid_manuscript",
            },
        },
    )

    assessment = journal_grade_assessment(example_dir, "FRESH")

    assert assessment is not None
    assert assessment["score_is_gateable"] is False
    assert assessment["evaluation_state"] == "stale"
    assert assessment["source"] == "critique.journal_grade_assessment"
    assert assessment["evidence_path"] == str(example_dir / "critique.md")


def test_journal_grade_assessment_adds_score_policy_for_complete_gateable_score(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.3",
            "critique_input_hash": critique_hash,
            "journal_grade_assessment": {
                "schema": JOURNAL_ASSESSMENT_SCHEMA,
                "scoring_mode": "fresh_reaudit",
                "assessed_artifact_hash": critique_hash,
                "score_is_gateable": True,
                "benchmark_level": "solid_manuscript",
                "overall_score": 82,
                "sub_scores": _valid_scores(),
                "score_rationale": "solid but not high impact",
            },
        },
    )

    assessment = journal_grade_assessment(example_dir, "FRESH")

    assert assessment is not None
    assert assessment["score_is_gateable"] is True
    assert assessment["evaluation_state"] == "passed"
    assert assessment["score_policy"] == "advisory_fresh_reaudit_not_gate"


def test_top_tier_audit_summary_counts_valid_slots_and_worst_verdict(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.3",
            "top_tier_audit": {
                "target_journal_fit": {
                    "verdict": "weak",
                    "blocks_high_impact": True,
                },
                "visual_originality": {
                    "verdict": "fail",
                    "blocks_high_impact": True,
                },
                "reduction_print_readability": {
                    "verdict": "needs_human",
                    "blocks_high_impact": False,
                },
                "ignored_slot": {"verdict": "unknown"},
            },
        },
    )

    summary = top_tier_audit_summary(example_dir, "FRESH")

    assert summary == {
        "source": "critique.top_tier_audit",
        "evidence_path": str(example_dir / "critique.md"),
        "slot_count": 3,
        "verdict_counts": {
            "pass": 0,
            "weak": 1,
            "needs_human": 1,
            "fail": 1,
        },
        "blocking_high_impact_count": 2,
        "blocking_high_impact_slots": ["target_journal_fit", "visual_originality"],
        "weak_or_failed_slots": [
            "target_journal_fit",
            "visual_originality",
            "reduction_print_readability",
        ],
        "worst_verdict": "fail",
    }


def test_top_tier_audit_summary_ignores_legacy_or_empty_audit(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.2",
            "top_tier_audit": {"target_journal_fit": {"verdict": "fail"}},
        },
    )

    assert top_tier_audit_summary(example_dir, "FRESH") is None
