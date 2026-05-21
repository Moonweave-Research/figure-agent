"""Critique assessment summaries surfaced by fig_loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quality_manifest import yaml_frontmatter

CRITIQUE_SCHEMA_V1_2 = "figure-agent.critique.v1.2"
CRITIQUE_SCHEMA_V1_3 = "figure-agent.critique.v1.3"
CRITIQUE_SCHEMA_V1_4 = "figure-agent.critique.v1.4"
CRITIQUE_SCHEMA_V1_5 = "figure-agent.critique.v1.5"
CRITIQUE_SCHEMAS_WITH_QUALITY_AXES = frozenset(
    {CRITIQUE_SCHEMA_V1_2, CRITIQUE_SCHEMA_V1_3, CRITIQUE_SCHEMA_V1_4, CRITIQUE_SCHEMA_V1_5}
)
CRITIQUE_SCHEMAS_WITH_TOP_TIER_AUDIT = frozenset(
    {CRITIQUE_SCHEMA_V1_3, CRITIQUE_SCHEMA_V1_4, CRITIQUE_SCHEMA_V1_5}
)
CRITIQUE_SCHEMAS_WITH_EDITORIAL_ART_DIRECTION = frozenset({CRITIQUE_SCHEMA_V1_5})
JOURNAL_ASSESSMENT_SCHEMA = "figure-agent.journal-grade-assessment.v1"
JOURNAL_SCORE_KEYS = frozenset(
    {
        "storyline",
        "composition",
        "component_fidelity",
        "scientific_plausibility",
        "label_semantics",
        "polish",
        "reference_fidelity",
        "export_scale_readability",
    }
)
TOP_TIER_VERDICTS = ("pass", "weak", "needs_human", "fail")
TOP_TIER_VERDICT_RANK = {verdict: index for index, verdict in enumerate(TOP_TIER_VERDICTS)}
EDITORIAL_POLISH_PATHS = frozenset(
    {
        "continue_tikz",
        "ready_for_svg_polish",
        "needs_human_art_direction",
        "semantic_backport_required",
    }
)


def is_score_value(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and 0 <= value <= 100
    )


def has_complete_score_block(record: dict[str, Any]) -> bool:
    if not {"overall_score", "sub_scores", "score_rationale"} <= record.keys():
        return False
    if not is_score_value(record.get("overall_score")):
        return False
    if (
        not isinstance(record.get("score_rationale"), str)
        or not record["score_rationale"].strip()
    ):
        return False
    sub_scores = record.get("sub_scores")
    return (
        isinstance(sub_scores, dict)
        and set(sub_scores) == JOURNAL_SCORE_KEYS
        and all(is_score_value(value) for value in sub_scores.values())
    )


def journal_grade_assessment(
    example_dir: Path,
    critique_state: Any,
) -> dict[str, Any] | None:
    if critique_state != "FRESH":
        return None
    critique_path = example_dir / "critique.md"
    if not critique_path.is_file():
        return None
    frontmatter = yaml_frontmatter(critique_path)
    if frontmatter.get("schema") not in CRITIQUE_SCHEMAS_WITH_QUALITY_AXES:
        return None
    assessment = frontmatter.get("journal_grade_assessment")
    if not isinstance(assessment, dict):
        return None
    record = dict(assessment)
    gateable = (
        record.get("schema") == JOURNAL_ASSESSMENT_SCHEMA
        and record.get("scoring_mode") == "fresh_reaudit"
        and isinstance(record.get("assessed_artifact_hash"), str)
        and record.get("assessed_artifact_hash") == frontmatter.get("critique_input_hash")
        and record.get("score_is_gateable") is True
    )
    record["score_is_gateable"] = gateable
    if not gateable:
        record["evaluation_state"] = "stale"
    elif record.get("benchmark_level") in {"blocked", "needs_human_art_direction"}:
        record["evaluation_state"] = "blocked"
    else:
        record["evaluation_state"] = "passed"
    record["source"] = "critique.journal_grade_assessment"
    record["evidence_path"] = str(critique_path)
    if gateable and has_complete_score_block(record):
        record["score_policy"] = "advisory_fresh_reaudit_not_gate"
    return record


def top_tier_audit_summary(
    example_dir: Path,
    critique_state: Any,
) -> dict[str, Any] | None:
    if critique_state != "FRESH":
        return None
    critique_path = example_dir / "critique.md"
    if not critique_path.is_file():
        return None
    frontmatter = yaml_frontmatter(critique_path)
    if frontmatter.get("schema") not in CRITIQUE_SCHEMAS_WITH_TOP_TIER_AUDIT:
        return None
    top_tier_audit = frontmatter.get("top_tier_audit")
    if not isinstance(top_tier_audit, dict):
        return None

    verdict_counts = dict.fromkeys(TOP_TIER_VERDICTS, 0)
    weak_or_failed_slots: list[str] = []
    blocking_high_impact_slots: list[str] = []
    valid_verdicts: list[str] = []
    for slot_name, slot in top_tier_audit.items():
        if not isinstance(slot_name, str) or not isinstance(slot, dict):
            continue
        verdict = slot.get("verdict")
        if not isinstance(verdict, str) or verdict not in TOP_TIER_VERDICT_RANK:
            continue
        verdict_counts[verdict] += 1
        valid_verdicts.append(verdict)
        if verdict != "pass":
            weak_or_failed_slots.append(slot_name)
        if slot.get("blocks_high_impact") is True:
            blocking_high_impact_slots.append(slot_name)

    if not valid_verdicts:
        return None
    worst_verdict = max(valid_verdicts, key=lambda verdict: TOP_TIER_VERDICT_RANK[verdict])
    return {
        "source": "critique.top_tier_audit",
        "evidence_path": str(critique_path),
        "slot_count": len(valid_verdicts),
        "verdict_counts": verdict_counts,
        "blocking_high_impact_count": len(blocking_high_impact_slots),
        "blocking_high_impact_slots": blocking_high_impact_slots,
        "weak_or_failed_slots": weak_or_failed_slots,
        "worst_verdict": worst_verdict,
    }


def editorial_art_direction_summary(
    example_dir: Path,
    critique_state: Any,
) -> dict[str, Any] | None:
    if critique_state != "FRESH":
        return None
    critique_path = example_dir / "critique.md"
    if not critique_path.is_file():
        return None
    frontmatter = yaml_frontmatter(critique_path)
    if frontmatter.get("schema") not in CRITIQUE_SCHEMAS_WITH_EDITORIAL_ART_DIRECTION:
        return None
    editorial = frontmatter.get("editorial_art_direction")
    if not isinstance(editorial, dict):
        return None

    verdict_counts = dict.fromkeys(TOP_TIER_VERDICTS, 0)
    weak_or_failed_slots: list[str] = []
    blocking_high_impact_slots: list[str] = []
    valid_verdicts: list[str] = []
    polish_recommended_path: str | None = None
    polish_trigger_verdict: str | None = None
    human_gate_verdict: str | None = None
    for slot_name, slot in editorial.items():
        if not isinstance(slot_name, str) or not isinstance(slot, dict):
            continue
        verdict = slot.get("verdict")
        if not isinstance(verdict, str) or verdict not in TOP_TIER_VERDICT_RANK:
            continue
        verdict_counts[verdict] += 1
        valid_verdicts.append(verdict)
        if verdict != "pass":
            weak_or_failed_slots.append(slot_name)
        if slot.get("blocks_high_impact") is True:
            blocking_high_impact_slots.append(slot_name)
        if slot_name == "tikz_vs_svg_polish_trigger":
            recommended_path = slot.get("recommended_path")
            if isinstance(recommended_path, str) and recommended_path in EDITORIAL_POLISH_PATHS:
                polish_recommended_path = recommended_path
            polish_trigger_verdict = verdict
        elif slot_name == "human_art_direction_gate":
            human_gate_verdict = verdict

    if not valid_verdicts or polish_recommended_path is None:
        return None
    worst_verdict = max(valid_verdicts, key=lambda verdict: TOP_TIER_VERDICT_RANK[verdict])
    return {
        "source": "critique.editorial_art_direction",
        "evidence_path": str(critique_path),
        "slot_count": len(valid_verdicts),
        "verdict_counts": verdict_counts,
        "blocking_high_impact_count": len(blocking_high_impact_slots),
        "blocking_high_impact_slots": blocking_high_impact_slots,
        "weak_or_failed_slots": weak_or_failed_slots,
        "worst_verdict": worst_verdict,
        "polish_recommended_path": polish_recommended_path,
        "polish_trigger_verdict": polish_trigger_verdict,
        "human_art_direction_gate_verdict": human_gate_verdict,
    }
