"""Critique assessment summaries surfaced by fig_loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from external_vision_review import (
    ExternalVisionReviewError,
    external_vision_review_freshness,
    load_optional_external_vision_review,
)
from inputs import parse_spec
from quality_manifest import yaml_frontmatter

CRITIQUE_SCHEMA_V1_2 = "figure-agent.critique.v1.2"
CRITIQUE_SCHEMA_V1_3 = "figure-agent.critique.v1.3"
CRITIQUE_SCHEMA_V1_4 = "figure-agent.critique.v1.4"
CRITIQUE_SCHEMA_V1_5 = "figure-agent.critique.v1.5"
CRITIQUE_SCHEMA_V1_6 = "figure-agent.critique.v1.6"
CRITIQUE_SCHEMA_V1_7 = "figure-agent.critique.v1.7"
CRITIQUE_SCHEMA_V1_8 = "figure-agent.critique.v1.8"
CRITIQUE_SCHEMA_V1_9 = "figure-agent.critique.v1.9"
CRITIQUE_SCHEMA_V1_10 = "figure-agent.critique.v1.10"
CRITIQUE_SCHEMA_V1_11 = "figure-agent.critique.v1.11"
CRITIQUE_SCHEMA_V1_12 = "figure-agent.critique.v1.12"
CRITIQUE_SCHEMA_V1_13 = "figure-agent.critique.v1.13"
CRITIQUE_SCHEMA_V1_14 = "figure-agent.critique.v1.14"
CRITIQUE_SCHEMA_V1_15 = "figure-agent.critique.v1.15"
CRITIQUE_SCHEMA_V1_16 = "figure-agent.critique.v1.16"
CRITIQUE_SCHEMAS_WITH_QUALITY_AXES = frozenset(
    {
        CRITIQUE_SCHEMA_V1_2,
        CRITIQUE_SCHEMA_V1_3,
        CRITIQUE_SCHEMA_V1_4,
        CRITIQUE_SCHEMA_V1_5,
        CRITIQUE_SCHEMA_V1_6,
        CRITIQUE_SCHEMA_V1_7,
        CRITIQUE_SCHEMA_V1_8,
        CRITIQUE_SCHEMA_V1_9,
        CRITIQUE_SCHEMA_V1_10,
        CRITIQUE_SCHEMA_V1_11,
        CRITIQUE_SCHEMA_V1_12,
        CRITIQUE_SCHEMA_V1_13,
        CRITIQUE_SCHEMA_V1_14,
        CRITIQUE_SCHEMA_V1_15,
        CRITIQUE_SCHEMA_V1_16,
    }
)
CRITIQUE_SCHEMAS_WITH_TOP_TIER_AUDIT = frozenset(
    {
        CRITIQUE_SCHEMA_V1_3,
        CRITIQUE_SCHEMA_V1_4,
        CRITIQUE_SCHEMA_V1_5,
        CRITIQUE_SCHEMA_V1_6,
        CRITIQUE_SCHEMA_V1_7,
        CRITIQUE_SCHEMA_V1_8,
        CRITIQUE_SCHEMA_V1_9,
        CRITIQUE_SCHEMA_V1_10,
        CRITIQUE_SCHEMA_V1_11,
        CRITIQUE_SCHEMA_V1_12,
        CRITIQUE_SCHEMA_V1_13,
        CRITIQUE_SCHEMA_V1_14,
        CRITIQUE_SCHEMA_V1_15,
        CRITIQUE_SCHEMA_V1_16,
    }
)
CRITIQUE_SCHEMAS_WITH_EDITORIAL_ART_DIRECTION = frozenset(
    {
        CRITIQUE_SCHEMA_V1_5,
        CRITIQUE_SCHEMA_V1_6,
        CRITIQUE_SCHEMA_V1_7,
        CRITIQUE_SCHEMA_V1_8,
        CRITIQUE_SCHEMA_V1_9,
        CRITIQUE_SCHEMA_V1_10,
        CRITIQUE_SCHEMA_V1_11,
        CRITIQUE_SCHEMA_V1_12,
        CRITIQUE_SCHEMA_V1_13,
        CRITIQUE_SCHEMA_V1_14,
        CRITIQUE_SCHEMA_V1_15,
        CRITIQUE_SCHEMA_V1_16,
    }
)
CRITIQUE_SCHEMAS_WITH_CROP_AUDIT = frozenset(
    {
        CRITIQUE_SCHEMA_V1_8,
        CRITIQUE_SCHEMA_V1_9,
        CRITIQUE_SCHEMA_V1_10,
        CRITIQUE_SCHEMA_V1_11,
        CRITIQUE_SCHEMA_V1_12,
        CRITIQUE_SCHEMA_V1_13,
        CRITIQUE_SCHEMA_V1_14,
        CRITIQUE_SCHEMA_V1_15,
        CRITIQUE_SCHEMA_V1_16,
    }
)
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
EDITORIAL_POLISH_DETAIL_FIELD_BY_PATH = {
    "continue_tikz": "remaining_tikz_lever",
    "ready_for_svg_polish": "svg_polish_candidate_reason",
    "semantic_backport_required": "semantic_backport_reason",
    "needs_human_art_direction": "human_art_direction_reason",
}
AESTHETIC_LEVER_VERDICTS = ("pass", "not_applicable", "weak", "fail", "needs_human")
AESTHETIC_LEVER_VERDICT_RANK = {
    verdict: index for index, verdict in enumerate(AESTHETIC_LEVER_VERDICTS)
}
JOURNAL_PLAYBOOK_VERDICTS = ("pass", "not_applicable", "weak", "fail", "needs_human")


def external_vision_review_summary(example_dir: Path) -> dict[str, Any] | None:
    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        return None
    try:
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))
        review = load_optional_external_vision_review(example_dir, spec)
    except (ExternalVisionReviewError, ValueError) as exc:
        return {
            "source": "external_vision_review.yaml",
            "evidence_path": str(example_dir / "external_vision_review.yaml"),
            "evaluation_state": "invalid",
            "error": str(exc),
        }
    if review is None:
        return None

    freshness = external_vision_review_freshness(example_dir, review)
    conflicts = [
        item
        for item in review.get("conflicts", [])
        if isinstance(item, dict)
        and isinstance(item.get("external_finding_id"), str)
        and isinstance(item.get("host_finding_id"), str)
    ]
    active_conflicts = [
        f"{item['external_finding_id']} vs {item['host_finding_id']}"
        for item in conflicts
    ]
    if freshness["state"] != "fresh":
        evaluation_state = freshness["state"]
    elif active_conflicts:
        evaluation_state = "needs_human"
    else:
        evaluation_state = "passed"
    findings = review.get("findings")
    finding_count = len(findings) if isinstance(findings, list) else 0
    return {
        "source": "external_vision_review.yaml",
        "evidence_path": str(example_dir / "external_vision_review.yaml"),
        "reviewer": review.get("reviewer"),
        "confidence": review.get("confidence"),
        "finding_count": finding_count,
        "conflict_count": len(active_conflicts),
        "active_conflicts": active_conflicts,
        "freshness": freshness,
        "evaluation_state": evaluation_state,
    }
JOURNAL_PLAYBOOK_VERDICT_RANK = {
    verdict: index for index, verdict in enumerate(JOURNAL_PLAYBOOK_VERDICTS)
}


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


def reference_calibration_summary(record: dict[str, Any]) -> dict[str, Any] | None:
    calibration = record.get("reference_calibration")
    if not isinstance(calibration, dict):
        return None
    traits = calibration.get("limiting_reference_traits")
    trait_count = len(traits) if isinstance(traits, list) else 0
    return {
        "reference_pack_hash": calibration.get("reference_pack_hash"),
        "reference_class": calibration.get("reference_class"),
        "visual_ambition": calibration.get("visual_ambition"),
        "score_basis": calibration.get("score_basis"),
        "limiting_reference_trait_count": trait_count,
    }


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
    calibration_summary = (
        reference_calibration_summary(record)
        if frontmatter.get("schema")
        in {
            CRITIQUE_SCHEMA_V1_9,
            CRITIQUE_SCHEMA_V1_10,
            CRITIQUE_SCHEMA_V1_11,
            CRITIQUE_SCHEMA_V1_12,
            CRITIQUE_SCHEMA_V1_13,
            CRITIQUE_SCHEMA_V1_14,
        }
        else None
    )
    if calibration_summary is not None:
        record["reference_calibration_summary"] = calibration_summary
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
    polish_route_detail: str | None = None
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
                detail_field = EDITORIAL_POLISH_DETAIL_FIELD_BY_PATH[recommended_path]
                route_detail = slot.get(detail_field)
                if isinstance(route_detail, str) and route_detail.strip():
                    polish_route_detail = route_detail.strip()
            polish_trigger_verdict = verdict
        elif slot_name == "human_art_direction_gate":
            human_gate_verdict = verdict

    if not valid_verdicts or polish_recommended_path is None:
        return None
    worst_verdict = max(valid_verdicts, key=lambda verdict: TOP_TIER_VERDICT_RANK[verdict])
    summary = {
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
    if polish_route_detail is not None:
        summary["polish_route_detail"] = polish_route_detail
    return summary


def crop_audit_summary(
    example_dir: Path,
    critique_state: Any,
) -> dict[str, Any] | None:
    if critique_state != "FRESH":
        return None
    critique_path = example_dir / "critique.md"
    if not critique_path.is_file():
        return None
    frontmatter = yaml_frontmatter(critique_path)
    if frontmatter.get("schema") not in CRITIQUE_SCHEMAS_WITH_CROP_AUDIT:
        return None
    raw_items = frontmatter.get("crop_audit_log")
    if not isinstance(raw_items, list):
        return None

    verdict_counts = {"defect": 0, "no_defect": 0, "uncertain": 0}
    defect_crop_ids: list[str] = []
    uncertain_crop_ids: list[str] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        verdict = raw_item.get("verdict")
        crop_id = raw_item.get("crop_id")
        if not isinstance(verdict, str) or verdict not in verdict_counts:
            continue
        if not isinstance(crop_id, str) or not crop_id.strip():
            continue
        verdict_counts[verdict] += 1
        if verdict == "defect":
            defect_crop_ids.append(crop_id)
        elif verdict == "uncertain":
            uncertain_crop_ids.append(crop_id)

    crop_count = sum(verdict_counts.values())
    if crop_count == 0:
        return None
    return {
        "source": "critique.crop_audit_log",
        "evidence_path": str(critique_path),
        "crop_count": crop_count,
        "verdict_counts": verdict_counts,
        "defect_crop_ids": defect_crop_ids,
        "uncertain_crop_ids": uncertain_crop_ids,
        "evaluation_state": "needs_action" if uncertain_crop_ids else "passed",
    }


def _aesthetic_bottleneck(item: dict[str, Any]) -> dict[str, Any]:
    linked_evidence = item.get("linked_evidence")
    return {
        "lever_id": item.get("lever_id"),
        "dimension": item.get("dimension"),
        "route": item.get("route"),
        "linked_evidence": linked_evidence if isinstance(linked_evidence, list) else [],
    }


def aesthetic_lever_summary(
    example_dir: Path,
    critique_state: Any,
) -> dict[str, Any] | None:
    critique_path = example_dir / "critique.md"
    if not critique_path.is_file():
        return None
    frontmatter = yaml_frontmatter(critique_path)
    if frontmatter.get("schema") not in {
        CRITIQUE_SCHEMA_V1_11,
        CRITIQUE_SCHEMA_V1_12,
        CRITIQUE_SCHEMA_V1_13,
        CRITIQUE_SCHEMA_V1_14,
        CRITIQUE_SCHEMA_V1_15,
        CRITIQUE_SCHEMA_V1_16,
    }:
        return None
    if critique_state != "FRESH":
        return {
            "source": "critique.aesthetic_lever_audit",
            "evidence_path": str(critique_path),
            "evaluation_state": "stale",
        }

    raw_items = frontmatter.get("aesthetic_lever_audit")
    if not isinstance(raw_items, list):
        return None

    verdict_counts = dict.fromkeys(AESTHETIC_LEVER_VERDICTS, 0)
    valid_items: list[dict[str, Any]] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        verdict = raw_item.get("verdict")
        lever_id = raw_item.get("lever_id")
        if not isinstance(verdict, str) or verdict not in AESTHETIC_LEVER_VERDICT_RANK:
            continue
        if not isinstance(lever_id, str) or not lever_id.strip():
            continue
        verdict_counts[verdict] += 1
        valid_items.append(raw_item)

    if not valid_items:
        return None
    worst_item = max(
        valid_items,
        key=lambda item: AESTHETIC_LEVER_VERDICT_RANK[str(item["verdict"])],
    )
    worst_verdict = str(worst_item["verdict"])
    if verdict_counts["needs_human"]:
        evaluation_state = "needs_human"
    elif verdict_counts["fail"]:
        evaluation_state = "blocked"
    elif verdict_counts["weak"]:
        evaluation_state = "needs_patch"
    else:
        evaluation_state = "passed"
    return {
        "source": "critique.aesthetic_lever_audit",
        "evidence_path": str(critique_path),
        "lever_count": len(valid_items),
        "verdict_counts": verdict_counts,
        "worst_verdict": worst_verdict,
        "evaluation_state": evaluation_state,
        "next_aesthetic_bottleneck": (
            None if evaluation_state == "passed" else _aesthetic_bottleneck(worst_item)
        ),
    }


def _journal_playbook_bottleneck(item: dict[str, Any]) -> dict[str, Any]:
    linked_evidence = item.get("linked_evidence")
    return {
        "id": item.get("id"),
        "verdict": item.get("verdict"),
        "route": item.get("route"),
        "linked_evidence": linked_evidence if isinstance(linked_evidence, list) else [],
    }


def journal_art_direction_playbook_summary(
    example_dir: Path,
    critique_state: Any,
) -> dict[str, Any] | None:
    critique_path = example_dir / "critique.md"
    if not critique_path.is_file():
        return None
    frontmatter = yaml_frontmatter(critique_path)
    if frontmatter.get("schema") not in {
        CRITIQUE_SCHEMA_V1_12,
        CRITIQUE_SCHEMA_V1_13,
        CRITIQUE_SCHEMA_V1_14,
        CRITIQUE_SCHEMA_V1_15,
        CRITIQUE_SCHEMA_V1_16,
    }:
        return None
    if critique_state != "FRESH":
        return {
            "source": "critique.journal_art_direction_playbook_audit",
            "evidence_path": str(critique_path),
            "evaluation_state": "stale",
        }

    audit = frontmatter.get("journal_art_direction_playbook_audit")
    if not isinstance(audit, dict):
        return None
    raw_items = audit.get("design_center")
    if not isinstance(raw_items, list):
        return None

    verdict_counts = dict.fromkeys(JOURNAL_PLAYBOOK_VERDICTS, 0)
    weak_or_failed_ids: list[str] = []
    valid_items: list[dict[str, Any]] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        item_id = raw_item.get("id")
        verdict = raw_item.get("verdict")
        if not isinstance(item_id, str) or not item_id.strip():
            continue
        if not isinstance(verdict, str) or verdict not in JOURNAL_PLAYBOOK_VERDICT_RANK:
            continue
        verdict_counts[verdict] += 1
        valid_items.append(raw_item)
        if verdict in {"weak", "fail", "needs_human"}:
            weak_or_failed_ids.append(item_id)

    if not valid_items:
        return None
    route_rule = audit.get("route_rule_applied")
    route_rule_summary = None
    recommended_path = None
    if isinstance(route_rule, dict):
        route_id = route_rule.get("id")
        route_path = route_rule.get("recommended_path")
        if isinstance(route_id, str) and isinstance(route_path, str):
            recommended_path = route_path
            route_rule_summary = {
                "id": route_id,
                "recommended_path": route_path,
            }
    raw_triggers = audit.get("human_review_triggers")
    active_triggers = []
    if isinstance(raw_triggers, list):
        active_triggers = [
            item["id"]
            for item in raw_triggers
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and item.get("active") is True
        ]
    worst_item = max(
        valid_items,
        key=lambda item: JOURNAL_PLAYBOOK_VERDICT_RANK[str(item["verdict"])],
    )
    worst_verdict = str(worst_item["verdict"])
    if active_triggers or verdict_counts["needs_human"]:
        evaluation_state = "needs_human"
    elif verdict_counts["fail"]:
        evaluation_state = "blocked"
    elif verdict_counts["weak"]:
        evaluation_state = "needs_patch"
    else:
        evaluation_state = "passed"
    return {
        "source": "critique.journal_art_direction_playbook_audit",
        "evidence_path": str(critique_path),
        "playbook_id": audit.get("playbook_id"),
        "venue_context": audit.get("venue_context"),
        "design_center_count": len(valid_items),
        "verdict_counts": verdict_counts,
        "worst_verdict": worst_verdict,
        "evaluation_state": evaluation_state,
        "weak_or_failed_design_center_ids": weak_or_failed_ids,
        "recommended_path": recommended_path,
        "route_rule_applied": route_rule_summary,
        "active_human_review_triggers": active_triggers,
        "next_journal_art_direction_bottleneck": (
            None if evaluation_state == "passed" else _journal_playbook_bottleneck(worst_item)
        ),
    }
