from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_assessments import (  # noqa: E402
    JOURNAL_ASSESSMENT_SCHEMA,
    JOURNAL_SCORE_KEYS,
    crop_audit_summary,
    editorial_art_direction_summary,
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


def _editorial_art_direction(
    *,
    trigger_path: str = "ready_for_svg_polish",
    overrides: dict[str, dict[str, object]] | None = None,
) -> dict[str, dict[str, object]]:
    overrides = overrides or {}
    keys = (
        "hero_focus",
        "narrative_choreography",
        "illustration_readiness",
        "abstraction_consistency",
        "reference_class_fit",
        "visual_identity",
        "claim_payload_fit",
        "aesthetic_risk",
        "tikz_vs_svg_polish_trigger",
        "human_art_direction_gate",
    )
    slots = {
        key: {
            "verdict": "pass",
            "evidence": f"{key} evidence",
            "rationale": f"{key} rationale",
            "concrete_fix": "none",
            "blocks_high_impact": False,
        }
        for key in keys
    }
    slots["tikz_vs_svg_polish_trigger"]["recommended_path"] = trigger_path
    for key, value in overrides.items():
        slots[key].update(value)
    return slots


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


def test_journal_grade_assessment_accepts_v1_4_quality_axes_schema(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.4",
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
    assert assessment["evaluation_state"] == "passed"


def test_journal_grade_assessment_accepts_v1_5_editorial_schema(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.5",
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
    assert assessment["evaluation_state"] == "passed"


def test_journal_grade_assessment_accepts_v1_7_visual_clash_schema(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.7",
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
    assert assessment["evaluation_state"] == "passed"


def test_crop_audit_summary_surfaces_uncertain_v1_8_crops(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.8",
            "crop_audit_log": [
                {
                    "crop_id": "full_q1",
                    "verdict": "no_defect",
                    "rationale": "full crop inspected",
                },
                {
                    "crop_id": "VC001_A",
                    "verdict": "uncertain",
                    "rationale": "local geometry remains ambiguous",
                },
            ],
        },
    )

    summary = crop_audit_summary(example_dir, "FRESH")

    assert summary == {
        "source": "critique.crop_audit_log",
        "evidence_path": str(example_dir / "critique.md"),
        "crop_count": 2,
        "verdict_counts": {"defect": 0, "no_defect": 1, "uncertain": 1},
        "defect_crop_ids": [],
        "uncertain_crop_ids": ["VC001_A"],
        "evaluation_state": "needs_action",
    }


def test_crop_audit_summary_ignores_legacy_v1_7(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.7",
            "crop_audit_log": [{"crop_id": "full_q1", "verdict": "uncertain"}],
        },
    )

    assert crop_audit_summary(example_dir, "FRESH") is None


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


def test_top_tier_audit_summary_accepts_v1_4_schema(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.4",
            "top_tier_audit": {
                "reduction_print_readability": {
                    "verdict": "needs_human",
                    "blocks_high_impact": True,
                },
            },
        },
    )

    summary = top_tier_audit_summary(example_dir, "FRESH")

    assert summary is not None
    assert summary["worst_verdict"] == "needs_human"
    assert summary["blocking_high_impact_slots"] == ["reduction_print_readability"]


def test_top_tier_audit_summary_accepts_v1_5_editorial_schema(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.5",
            "top_tier_audit": {
                "aesthetic_coherence": {
                    "verdict": "weak",
                    "blocks_high_impact": True,
                },
            },
        },
    )

    summary = top_tier_audit_summary(example_dir, "FRESH")

    assert summary is not None
    assert summary["worst_verdict"] == "weak"
    assert summary["blocking_high_impact_slots"] == ["aesthetic_coherence"]


def test_top_tier_audit_summary_accepts_v1_7_visual_clash_schema(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.7",
            "top_tier_audit": {
                "reader_misinterpretation_risk": {
                    "verdict": "fail",
                    "blocks_high_impact": True,
                },
            },
        },
    )

    summary = top_tier_audit_summary(example_dir, "FRESH")

    assert summary is not None
    assert summary["worst_verdict"] == "fail"
    assert summary["blocking_high_impact_slots"] == ["reader_misinterpretation_risk"]


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


def test_editorial_art_direction_summary_extracts_polish_trigger(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.5",
            "editorial_art_direction": _editorial_art_direction(
                trigger_path="ready_for_svg_polish",
                overrides={
                    "hero_focus": {
                        "verdict": "weak",
                        "blocks_high_impact": True,
                    },
                    "human_art_direction_gate": {"verdict": "needs_human"},
                },
            ),
        },
    )

    summary = editorial_art_direction_summary(example_dir, "FRESH")

    assert summary == {
        "source": "critique.editorial_art_direction",
        "evidence_path": str(example_dir / "critique.md"),
        "slot_count": 10,
        "verdict_counts": {
            "pass": 8,
            "weak": 1,
            "needs_human": 1,
            "fail": 0,
        },
        "blocking_high_impact_count": 1,
        "blocking_high_impact_slots": ["hero_focus"],
        "weak_or_failed_slots": ["hero_focus", "human_art_direction_gate"],
        "worst_verdict": "needs_human",
        "polish_recommended_path": "ready_for_svg_polish",
        "polish_trigger_verdict": "pass",
        "human_art_direction_gate_verdict": "needs_human",
    }


def test_editorial_art_direction_summary_accepts_v1_7_visual_clash_schema(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.7",
            "editorial_art_direction": _editorial_art_direction(
                trigger_path="ready_for_svg_polish",
                overrides={"human_art_direction_gate": {"verdict": "needs_human"}},
            ),
        },
    )

    summary = editorial_art_direction_summary(example_dir, "FRESH")

    assert summary is not None
    assert summary["worst_verdict"] == "needs_human"
    assert summary["human_art_direction_gate_verdict"] == "needs_human"


def test_editorial_art_direction_summary_ignores_legacy_or_stale(
    tmp_path: Path,
) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.4",
            "editorial_art_direction": _editorial_art_direction(),
        },
    )

    assert editorial_art_direction_summary(example_dir, "FRESH") is None

    _write_critique(
        example_dir / "critique.md",
        {
            "schema": "figure-agent.critique.v1.5",
            "editorial_art_direction": _editorial_art_direction(),
        },
    )
    assert editorial_art_direction_summary(example_dir, "STALE") is None
