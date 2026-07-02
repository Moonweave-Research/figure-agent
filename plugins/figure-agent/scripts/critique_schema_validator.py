"""Validate critique.md schema-specific frontmatter contracts."""

from __future__ import annotations

import re
from typing import Any

import critique_schema_vocab as vocab
from critique_contract import (
    CritiqueContractError,
    critique_finding_id,
    critique_findings,
    require_mapping,
)


def _require_score_value(value: Any, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CritiqueContractError(f"{label} must be a number from 0 to 100")
    if value < 0 or value > 100:
        raise CritiqueContractError(f"{label} must be a number from 0 to 100")


def _require_non_empty_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise CritiqueContractError(f"{label} must be a non-empty list")
    return value


def _require_mapping_items(value: Any, label: str) -> list[dict[str, Any]]:
    items = _require_non_empty_list(value, label)
    mappings: list[dict[str, Any]] = []
    for index, raw_item in enumerate(items):
        mappings.append(require_mapping(raw_item, f"{label}[{index}]"))
    return mappings


def _require_non_empty_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CritiqueContractError(f"{label}.{key} must be a non-empty string")
    return value


def _require_string_value(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise CritiqueContractError(f"{label}.{key} must be a string")
    return value.strip()


def _require_enum(
    data: dict[str, Any],
    key: str,
    allowed: frozenset[str],
    *,
    label: str,
) -> str:
    value = _require_string_value(data, key, label=label)
    if value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise CritiqueContractError(f"{label}.{key} must be one of: {allowed_values}")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise CritiqueContractError(f"{label} must be a list")
    return value


def _validate_string_list(value: Any, label: str, *, require_non_empty: bool) -> list[str]:
    items = _require_list(value, label)
    if require_non_empty and not items:
        raise CritiqueContractError(f"{label} must be a non-empty list")
    strings: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            raise CritiqueContractError(f"{label}[{index}] must be a non-empty string")
        strings.append(item.strip())
    return strings


def _validate_sha256_string(value: str, label: str) -> None:
    if not value.startswith("sha256:") or len(value) <= len("sha256:"):
        raise CritiqueContractError(f"{label} must be a sha256-prefixed string")


def _validate_v1_1_audit(frontmatter: dict[str, Any]) -> None:
    audit = require_mapping(
        frontmatter.get("audit_enumeration"),
        "critique frontmatter.audit_enumeration",
    )
    structural = require_mapping(
        audit.get("structural_completeness"),
        "critique frontmatter.audit_enumeration.structural_completeness",
    )
    _require_mapping_items(
        structural.get("components"),
        "critique frontmatter.audit_enumeration.structural_completeness.components",
    )
    _require_mapping_items(
        structural.get("missing_from_reference"),
        ("critique frontmatter.audit_enumeration.structural_completeness.missing_from_reference"),
    )
    _require_mapping_items(
        audit.get("label_target_matching"),
        "critique frontmatter.audit_enumeration.label_target_matching",
    )
    _require_mapping_items(
        audit.get("physical_plausibility"),
        "critique frontmatter.audit_enumeration.physical_plausibility",
    )
    conceptual_items = _require_mapping_items(
        audit.get("conceptual_completeness"),
        "critique frontmatter.audit_enumeration.conceptual_completeness",
    )
    for index, item in enumerate(conceptual_items):
        reference = item.get("reference")
        if reference not in vocab.ALLOWED_CONCEPTUAL_REFERENCES:
            allowed = ", ".join(sorted(vocab.ALLOWED_CONCEPTUAL_REFERENCES))
            raise CritiqueContractError(
                "critique frontmatter.audit_enumeration.conceptual_completeness"
                f"[{index}].reference must be one of: {allowed}"
            )


def _validate_quality_axis(
    axis: dict[str, Any],
    axis_name: str,
    *,
    require_panel_roles: bool = False,
) -> str:
    label = f"critique frontmatter.quality_axes.{axis_name}"
    verdict = _require_enum(axis, "verdict", vocab.QUALITY_VERDICTS, label=label)
    _require_enum(axis, "confidence", vocab.QUALITY_CONFIDENCES, label=label)
    action = _require_enum(axis, "recommended_action", vocab.QUALITY_ACTIONS, label=label)

    allowed_actions = vocab.QUALITY_ACTIONS_BY_VERDICT[verdict]
    if action not in allowed_actions:
        allowed = ", ".join(sorted(allowed_actions))
        raise CritiqueContractError(
            f"{label}.recommended_action must be one of {allowed} for verdict {verdict}"
        )

    if verdict != "not_applicable":
        _require_non_empty_string(axis, "rationale", label=label)
        _require_non_empty_string(axis, "evidence", label=label)
    else:
        _require_string_value(axis, "rationale", label=label)
        _require_string_value(axis, "evidence", label=label)

    blocking_items = _require_list(axis.get("blocking_items"), f"{label}.blocking_items")
    for index, item in enumerate(blocking_items):
        if not isinstance(item, str) or not item.strip():
            raise CritiqueContractError(
                f"{label}.blocking_items[{index}] must be a non-empty string"
            )
    if verdict in {"needs_patch", "block"} and not blocking_items:
        raise CritiqueContractError(
            f"{label}.blocking_items must be a non-empty list for verdict {verdict}"
        )

    if require_panel_roles and verdict != "not_applicable":
        _validate_panel_roles(axis, label)

    return verdict


def _validate_panel_roles(axis: dict[str, Any], axis_label: str) -> None:
    panel_roles = _require_non_empty_list(axis.get("panel_roles"), f"{axis_label}.panel_roles")
    for index, raw_role in enumerate(panel_roles):
        role_label = f"{axis_label}.panel_roles[{index}]"
        role_item = require_mapping(raw_role, role_label)
        _require_non_empty_string(role_item, "panel_id", label=role_label)
        _require_enum(role_item, "role", vocab.PANEL_ROLES, label=role_label)
        _require_enum(role_item, "role_quality", vocab.PANEL_ROLE_QUALITIES, label=role_label)
        _require_non_empty_string(role_item, "rationale", label=role_label)


def _validate_v1_2_quality_axes(frontmatter: dict[str, Any]) -> dict[str, str]:
    quality_axes = require_mapping(
        frontmatter.get("quality_axes"),
        "critique frontmatter.quality_axes",
    )
    verdicts: dict[str, str] = {}
    for axis_name in vocab.QUALITY_AXIS_NAMES:
        axis = require_mapping(
            quality_axes.get(axis_name),
            f"critique frontmatter.quality_axes.{axis_name}",
        )
        verdicts[axis_name] = _validate_quality_axis(
            axis,
            axis_name,
            require_panel_roles=axis_name == "panel_role_coherence",
        )

    readiness_verdict = verdicts["publication_readiness"]
    upstream_verdicts = [
        verdict
        for axis_name, verdict in verdicts.items()
        if axis_name != "publication_readiness" and verdict != "not_applicable"
    ]
    if readiness_verdict == "not_applicable" and upstream_verdicts:
        raise CritiqueContractError(
            "critique frontmatter.quality_axes.publication_readiness.verdict "
            "cannot be not_applicable while upstream axes are applicable"
        )
    if readiness_verdict != "not_applicable" and upstream_verdicts:
        required_rank = max(vocab.QUALITY_SEVERITY_RANK[verdict] for verdict in upstream_verdicts)
        readiness_rank = vocab.QUALITY_SEVERITY_RANK[readiness_verdict]
        if readiness_rank < required_rank:
            raise CritiqueContractError(
                "critique frontmatter.quality_axes.publication_readiness.verdict "
                "is less severe than an applicable upstream quality axis"
            )
    return verdicts


def _validate_journal_score_block(assessment: dict[str, Any], label: str) -> None:
    present = vocab.JOURNAL_SCORE_BLOCK_KEYS & assessment.keys()
    if not present:
        return
    if present != vocab.JOURNAL_SCORE_BLOCK_KEYS:
        missing = ", ".join(sorted(vocab.JOURNAL_SCORE_BLOCK_KEYS - present))
        raise CritiqueContractError(f"{label} score block is incomplete; missing: {missing}")

    _require_score_value(assessment.get("overall_score"), f"{label}.overall_score")
    sub_scores = require_mapping(assessment.get("sub_scores"), f"{label}.sub_scores")
    keys = set(sub_scores)
    if keys != vocab.JOURNAL_SCORE_KEYS:
        missing = ", ".join(sorted(vocab.JOURNAL_SCORE_KEYS - keys))
        extra = ", ".join(sorted(keys - vocab.JOURNAL_SCORE_KEYS))
        details = []
        if missing:
            details.append(f"missing: {missing}")
        if extra:
            details.append(f"extra: {extra}")
        suffix = f" ({'; '.join(details)})" if details else ""
        raise CritiqueContractError(
            f"{label}.sub_scores must contain exactly the required score keys{suffix}"
        )
    for key, value in sub_scores.items():
        _require_score_value(value, f"{label}.sub_scores.{key}")
    _require_non_empty_string(assessment, "score_rationale", label=label)


def _validate_reference_calibration(assessment: dict[str, Any], label: str) -> None:
    raw_calibration = assessment.get("reference_calibration")
    if raw_calibration is None:
        return
    calibration = require_mapping(raw_calibration, f"{label}.reference_calibration")
    calibration_label = f"{label}.reference_calibration"
    pack_hash = _require_non_empty_string(
        calibration,
        "reference_pack_hash",
        label=calibration_label,
    )
    _validate_sha256_string(pack_hash, f"{calibration_label}.reference_pack_hash")
    _require_non_empty_string(calibration, "reference_class", label=calibration_label)
    _require_non_empty_string(calibration, "visual_ambition", label=calibration_label)
    _require_enum(
        calibration,
        "score_basis",
        vocab.JOURNAL_REFERENCE_SCORE_BASIS,
        label=calibration_label,
    )
    traits = _require_list(
        calibration.get("limiting_reference_traits"),
        f"{calibration_label}.limiting_reference_traits",
    )
    for index, trait in enumerate(traits):
        if not isinstance(trait, str) or not trait.strip():
            raise CritiqueContractError(
                f"{calibration_label}.limiting_reference_traits[{index}] must be a non-empty string"
            )
    _require_non_empty_string(calibration, "rationale", label=calibration_label)


def _validate_journal_grade_assessment(
    frontmatter: dict[str, Any],
    quality_verdicts: dict[str, str],
    top_tier_verdicts: dict[str, str] | None = None,
    editorial_verdicts: dict[str, str] | None = None,
    *,
    allow_reference_calibration: bool = False,
) -> None:
    raw_assessment = frontmatter.get("journal_grade_assessment")
    if raw_assessment is None:
        return
    assessment = require_mapping(
        raw_assessment,
        "critique frontmatter.journal_grade_assessment",
    )
    label = "critique frontmatter.journal_grade_assessment"
    schema = assessment.get("schema")
    if schema != vocab.JOURNAL_ASSESSMENT_SCHEMA:
        raise CritiqueContractError(f"{label}.schema must be {vocab.JOURNAL_ASSESSMENT_SCHEMA}")
    scoring_mode = _require_string_value(assessment, "scoring_mode", label=label)
    if scoring_mode != vocab.JOURNAL_SCORING_MODE:
        raise CritiqueContractError(f"{label}.scoring_mode must be {vocab.JOURNAL_SCORING_MODE}")
    assessed_hash = _require_non_empty_string(
        assessment,
        "assessed_artifact_hash",
        label=label,
    )
    _validate_sha256_string(assessed_hash, f"{label}.assessed_artifact_hash")
    benchmark_level = _require_enum(
        assessment,
        "benchmark_level",
        vocab.JOURNAL_BENCHMARK_LEVELS,
        label=label,
    )
    _require_enum(assessment, "confidence", vocab.QUALITY_CONFIDENCES, label=label)
    blockers = _require_list(assessment.get("blockers"), f"{label}.blockers")
    for index, blocker in enumerate(blockers):
        if not isinstance(blocker, str) or not blocker.strip():
            raise CritiqueContractError(f"{label}.blockers[{index}] must be a string")
    regression_detected = assessment.get("regression_detected")
    if not isinstance(regression_detected, bool):
        raise CritiqueContractError(f"{label}.regression_detected must be a boolean")
    regressions = _require_list(assessment.get("regressions"), f"{label}.regressions")
    for index, raw_regression in enumerate(regressions):
        regression_label = f"{label}.regressions[{index}]"
        regression = require_mapping(raw_regression, regression_label)
        _require_non_empty_string(regression, "axis", label=regression_label)
        _require_non_empty_string(regression, "previous_state", label=regression_label)
        _require_non_empty_string(regression, "current_state", label=regression_label)
        _require_non_empty_string(regression, "reason", label=regression_label)
    score_is_gateable = assessment.get("score_is_gateable")
    if not isinstance(score_is_gateable, bool):
        raise CritiqueContractError(f"{label}.score_is_gateable must be a boolean")
    _require_enum(assessment, "next_quality_bottleneck", vocab.JOURNAL_BOTTLENECKS, label=label)
    _require_non_empty_string(assessment, "rationale", label=label)
    _validate_journal_score_block(assessment, label)
    if allow_reference_calibration:
        _validate_reference_calibration(assessment, label)

    if benchmark_level == "high_impact_candidate":
        non_passing = {
            axis_name: verdict
            for axis_name, verdict in quality_verdicts.items()
            if verdict not in {"pass", "not_applicable"}
        }
        if non_passing:
            axes = ", ".join(sorted(non_passing))
            raise CritiqueContractError(
                f"{label}.benchmark_level high_impact_candidate requires passing "
                f"upstream quality axes; non-passing axes: {axes}"
            )
        non_passing_top_tier = {
            audit_name: verdict
            for audit_name, verdict in (top_tier_verdicts or {}).items()
            if verdict != "pass"
        }
        if non_passing_top_tier:
            audits = ", ".join(sorted(non_passing_top_tier))
            raise CritiqueContractError(
                f"{label}.benchmark_level high_impact_candidate requires passing "
                f"top_tier_audit slots; non-passing slots: {audits}"
            )
        non_passing_editorial = {
            audit_name: verdict
            for audit_name, verdict in (editorial_verdicts or {}).items()
            if verdict != "pass"
        }
        if non_passing_editorial:
            audits = ", ".join(sorted(non_passing_editorial))
            raise CritiqueContractError(
                f"{label}.benchmark_level high_impact_candidate requires passing "
                f"editorial_art_direction slots; non-passing slots: {audits}"
            )

    critique_input_hash = frontmatter.get("critique_input_hash")
    if score_is_gateable and assessed_hash != critique_input_hash:
        raise CritiqueContractError(
            f"{label}.assessed_artifact_hash must match critique_input_hash "
            "when score_is_gateable is true"
        )


def _validate_v1_2_audit_to_finding(frontmatter: dict[str, Any]) -> None:
    quality_axes = require_mapping(
        frontmatter.get("quality_axes"),
        "critique frontmatter.quality_axes",
    )
    findings = critique_findings(frontmatter)
    finding_ids = {
        critique_finding_id(finding, f"critique finding {index}")
        for index, finding in enumerate(findings)
    }
    finding_required_axes: list[str] = []
    for axis_name in vocab.QUALITY_AXIS_NAMES:
        axis = require_mapping(
            quality_axes.get(axis_name),
            f"critique frontmatter.quality_axes.{axis_name}",
        )
        verdict = str(axis.get("verdict", "")).strip()
        action = str(axis.get("recommended_action", "")).strip()
        if verdict in {"needs_patch", "block"} and action not in {
            "human_review",
            "revise_briefing",
        }:
            finding_required_axes.append(axis_name)
            blocking_items = _require_list(
                axis.get("blocking_items"),
                f"critique frontmatter.quality_axes.{axis_name}.blocking_items",
            )
            if not finding_ids:
                continue
            if any(
                isinstance(item, str)
                and re.search(
                    rf"(^|[^A-Za-z0-9_.-]){re.escape(finding_id)}($|[^A-Za-z0-9_.-])",
                    item,
                )
                for item in blocking_items
                for finding_id in finding_ids
            ):
                continue
            raise CritiqueContractError(
                "critique frontmatter.quality_axes."
                f"{axis_name}.blocking_items must reference a panel/top-level "
                "finding id for patch or block_release action"
            )
    if finding_required_axes and not finding_ids:
        axes = ", ".join(finding_required_axes)
        raise CritiqueContractError(
            "critique frontmatter.quality_axes must include at least one "
            f"panel/top-level findings item for patch or block_release axis: {axes}"
        )


def _text_mentions_top_tier_slot(value: Any, key: str) -> bool:
    needle = f"top_tier_audit.{key}"
    if isinstance(value, str):
        return needle in value or key in value
    if isinstance(value, list):
        return any(_text_mentions_top_tier_slot(item, key) for item in value)
    if isinstance(value, dict):
        return any(_text_mentions_top_tier_slot(item, key) for item in value.values())
    return False


def _text_mentions_editorial_slot(value: Any, key: str) -> bool:
    needle = f"editorial_art_direction.{key}"
    if isinstance(value, str):
        return needle in value or key in value
    if isinstance(value, list):
        return any(_text_mentions_editorial_slot(item, key) for item in value)
    if isinstance(value, dict):
        return any(_text_mentions_editorial_slot(item, key) for item in value.values())
    return False


def _quality_axes_link_top_tier_slot(frontmatter: dict[str, Any], key: str) -> bool:
    quality_axes = require_mapping(
        frontmatter.get("quality_axes"),
        "critique frontmatter.quality_axes",
    )
    for axis_name in vocab.QUALITY_AXIS_NAMES:
        axis = require_mapping(
            quality_axes.get(axis_name),
            f"critique frontmatter.quality_axes.{axis_name}",
        )
        verdict = str(axis.get("verdict", "")).strip()
        action = str(axis.get("recommended_action", "")).strip()
        if verdict != "needs_human" and action not in {"revise_briefing", "block_release"}:
            continue
        if _text_mentions_top_tier_slot(axis.get("blocking_items"), key):
            return True
    return False


def _quality_axes_link_editorial_slot(frontmatter: dict[str, Any], key: str) -> bool:
    quality_axes = require_mapping(
        frontmatter.get("quality_axes"),
        "critique frontmatter.quality_axes",
    )
    for axis_name in vocab.QUALITY_AXIS_NAMES:
        axis = require_mapping(
            quality_axes.get(axis_name),
            f"critique frontmatter.quality_axes.{axis_name}",
        )
        verdict = str(axis.get("verdict", "")).strip()
        action = str(axis.get("recommended_action", "")).strip()
        if verdict != "needs_human" and action not in {"revise_briefing", "block_release"}:
            continue
        if _text_mentions_editorial_slot(axis.get("blocking_items"), key):
            return True
    return False


def _findings_link_top_tier_slot(findings: list[dict[str, Any]], key: str) -> bool:
    return any(_text_mentions_top_tier_slot(finding, key) for finding in findings)


def _findings_link_editorial_slot(findings: list[dict[str, Any]], key: str) -> bool:
    return any(_text_mentions_editorial_slot(finding, key) for finding in findings)


def _validate_v1_3_top_tier_audit(frontmatter: dict[str, Any]) -> dict[str, str]:
    top_tier_audit = require_mapping(
        frontmatter.get("top_tier_audit"),
        "critique frontmatter.top_tier_audit",
    )
    findings = critique_findings(frontmatter)
    unlinked_items: list[str] = []
    verdicts: dict[str, str] = {}
    for key in vocab.TOP_TIER_AUDIT_KEYS:
        label = f"critique frontmatter.top_tier_audit.{key}"
        item = require_mapping(top_tier_audit.get(key), label)
        verdict = _require_enum(item, "verdict", vocab.TOP_TIER_AUDIT_VERDICTS, label=label)
        verdicts[key] = verdict
        _require_non_empty_string(item, "finding", label=label)
        concrete_fix = _require_non_empty_string(item, "concrete_fix", label=label)
        if not isinstance(item.get("blocks_high_impact"), bool):
            raise CritiqueContractError(f"{label}.blocks_high_impact must be a boolean")
        requires_link = (
            verdict == "fail"
            or verdict == "needs_human"
            or (verdict == "weak" and item["blocks_high_impact"])
        )
        if (
            requires_link
            and "accept_simplification" not in concrete_fix
            and not _findings_link_top_tier_slot(findings, key)
            and not _quality_axes_link_top_tier_slot(frontmatter, key)
        ):
            unlinked_items.append(key)
    if unlinked_items:
        slots = ", ".join(unlinked_items)
        raise CritiqueContractError(
            "critique frontmatter.top_tier_audit requires linked "
            "panel/top-level findings, quality_axes blocking_items, or "
            f"accept_simplification for slots: {slots}"
        )
    return verdicts


def _validate_v1_5_editorial_art_direction(frontmatter: dict[str, Any]) -> dict[str, str]:
    editorial = require_mapping(
        frontmatter.get("editorial_art_direction"),
        "critique frontmatter.editorial_art_direction",
    )
    findings = critique_findings(frontmatter)
    unlinked_items: list[str] = []
    verdicts: dict[str, str] = {}
    for key in vocab.EDITORIAL_AUDIT_KEYS:
        label = f"critique frontmatter.editorial_art_direction.{key}"
        item = require_mapping(editorial.get(key), label)
        verdict = _require_enum(item, "verdict", vocab.EDITORIAL_VERDICTS, label=label)
        verdicts[key] = verdict
        _require_non_empty_string(item, "evidence", label=label)
        _require_non_empty_string(item, "rationale", label=label)
        concrete_fix = _require_non_empty_string(item, "concrete_fix", label=label)
        if not isinstance(item.get("blocks_high_impact"), bool):
            raise CritiqueContractError(f"{label}.blocks_high_impact must be a boolean")
        if key == "tikz_vs_svg_polish_trigger":
            _require_enum(
                item,
                "recommended_path",
                vocab.EDITORIAL_POLISH_PATHS,
                label=label,
            )

        requires_link = (
            verdict == "fail"
            or verdict == "needs_human"
            or (verdict == "weak" and item["blocks_high_impact"])
        )
        allow_simplification = verdict != "needs_human" and "accept_simplification" in concrete_fix
        if (
            requires_link
            and not allow_simplification
            and not _findings_link_editorial_slot(findings, key)
            and not _quality_axes_link_editorial_slot(frontmatter, key)
        ):
            unlinked_items.append(key)
    if unlinked_items:
        slots = ", ".join(unlinked_items)
        raise CritiqueContractError(
            "critique frontmatter.editorial_art_direction requires linked "
            "panel/top-level findings, quality_axes blocking_items, or allowed "
            f"accept_simplification for slots: {slots}"
        )
    return verdicts


def _validate_v1_14_editorial_route_detail(frontmatter: dict[str, Any]) -> None:
    editorial = require_mapping(
        frontmatter.get("editorial_art_direction"),
        "critique frontmatter.editorial_art_direction",
    )
    label = "critique frontmatter.editorial_art_direction.tikz_vs_svg_polish_trigger"
    trigger = require_mapping(editorial.get("tikz_vs_svg_polish_trigger"), label)
    required_field_by_path = {
        "continue_tikz": "remaining_tikz_lever",
        "ready_for_svg_polish": "svg_polish_candidate_reason",
        "semantic_backport_required": "semantic_backport_reason",
        "needs_human_art_direction": "human_art_direction_reason",
    }
    recommended_path = _require_enum(
        trigger,
        "recommended_path",
        vocab.EDITORIAL_POLISH_PATHS,
        label=label,
    )
    _require_non_empty_string(
        trigger,
        required_field_by_path[recommended_path],
        label=label,
    )


def _editorial_trigger_recommended_path(frontmatter: dict[str, Any]) -> str:
    editorial = frontmatter.get("editorial_art_direction")
    trigger = editorial.get("tikz_vs_svg_polish_trigger") if isinstance(editorial, dict) else None
    path = trigger.get("recommended_path") if isinstance(trigger, dict) else None
    return path.strip() if isinstance(path, str) else ""


def _validate_v1_4_micro_defects(frontmatter: dict[str, Any]) -> None:
    raw_items = _require_list(
        frontmatter.get("micro_defects"),
        "critique frontmatter.micro_defects",
    )
    findings = critique_findings(frontmatter)
    finding_ids = {
        critique_finding_id(finding, f"critique finding {index}")
        for index, finding in enumerate(findings)
    }
    unlinked_items: list[str] = []
    for index, raw_item in enumerate(raw_items):
        label = f"critique frontmatter.micro_defects[{index}]"
        item = require_mapping(raw_item, label)
        micro_defect_id = _require_non_empty_string(item, "id", label=label)
        crop_path = _require_non_empty_string(item, "crop", label=label)
        if not crop_path.startswith("examples/") or "/build/audit_crops/" not in crop_path:
            raise CritiqueContractError(
                f"{label}.crop must point to examples/<name>/build/audit_crops/*.png"
            )
        _require_enum(item, "kind", vocab.MICRO_DEFECT_KINDS, label=label)
        severity = _require_enum(item, "severity", vocab.FINDING_SEVERITIES, label=label)
        _require_non_empty_string(item, "observation", label=label)
        linked_finding_id = _require_string_value(item, "linked_finding_id", label=label)
        status = _require_enum(item, "status", vocab.MICRO_DEFECT_STATUSES, label=label)
        if (
            severity in {"BLOCKER", "MAJOR"}
            and status != "accept_simplification"
            and linked_finding_id not in finding_ids
        ):
            unlinked_items.append(micro_defect_id)
    if unlinked_items:
        items = ", ".join(unlinked_items)
        raise CritiqueContractError(
            "critique frontmatter.micro_defects BLOCKER/MAJOR items must "
            f"reference linked_finding_id or use accept_simplification: {items}"
        )


def _validate_v1_10_accept_simplification(frontmatter: dict[str, Any]) -> None:
    raw_items = _require_list(
        frontmatter.get("micro_defects"),
        "critique frontmatter.micro_defects",
    )
    for index, raw_item in enumerate(raw_items):
        label = f"critique frontmatter.micro_defects[{index}]"
        item = require_mapping(raw_item, label)
        if item.get("status") != "accept_simplification":
            continue
        _require_enum(
            item,
            "accept_simplification_reason",
            vocab.MICRO_DEFECT_ACCEPT_SIMPLIFICATION_REASONS,
            label=label,
        )
        rationale = _require_non_empty_string(
            item,
            "accept_simplification_rationale",
            label=label,
        )
        visual_clash_ref = item.get("visual_clash_ref")
        if not isinstance(visual_clash_ref, str) or not visual_clash_ref.strip():
            continue
        normalized_rationale = " ".join(rationale.split())
        lowered_rationale = normalized_rationale.lower()
        if (
            len(normalized_rationale)
            >= vocab.MICRO_DEFECT_ACCEPT_SIMPLIFICATION_MIN_RATIONALE_CHARS
            and visual_clash_ref.strip() in normalized_rationale
            and any(
                marker in lowered_rationale
                for marker in vocab.MICRO_DEFECT_ACCEPT_SIMPLIFICATION_RATIONALE_MARKERS
            )
        ):
            continue
        raise CritiqueContractError(
            f"{label}.accept_simplification_rationale must be concrete, name "
            "the visual_clash_ref candidate id, and explain the non-defect "
            "geometry/context"
        )


def _validate_v1_11_aesthetic_lever_audit(
    frontmatter: dict[str, Any],
) -> dict[str, tuple[str, str]]:
    raw_items = _require_non_empty_list(
        frontmatter.get("aesthetic_lever_audit"),
        "critique frontmatter.aesthetic_lever_audit",
    )
    seen: set[str] = set()
    verdicts: dict[str, tuple[str, str]] = {}
    for index, raw_item in enumerate(raw_items):
        label = f"critique frontmatter.aesthetic_lever_audit[{index}]"
        item = require_mapping(raw_item, label)
        lever_id = _require_non_empty_string(item, "lever_id", label=label)
        if lever_id in seen:
            raise CritiqueContractError(
                f"critique frontmatter.aesthetic_lever_audit has duplicate lever_id: {lever_id}"
            )
        seen.add(lever_id)
        _require_enum(item, "dimension", vocab.AESTHETIC_LEVER_DIMENSIONS, label=label)
        verdict = _require_enum(item, "verdict", vocab.AESTHETIC_LEVER_VERDICTS, label=label)
        _require_enum(item, "confidence", vocab.QUALITY_CONFIDENCES, label=label)
        positive_signals = _validate_string_list(
            item.get("observed_positive_signals"),
            f"{label}.observed_positive_signals",
            require_non_empty=verdict == "pass",
        )
        _validate_string_list(
            item.get("observed_anti_patterns"),
            f"{label}.observed_anti_patterns",
            require_non_empty=verdict in {"weak", "fail", "needs_human"},
        )
        route = _require_enum(item, "route", vocab.AESTHETIC_LEVER_ROUTES, label=label)
        linked_evidence = _validate_string_list(
            item.get("linked_evidence"),
            f"{label}.linked_evidence",
            require_non_empty=verdict in {"weak", "fail", "needs_human"},
        )
        allowed_next_adjustment = _require_string_value(
            item,
            "allowed_next_adjustment",
            label=label,
        )
        _require_non_empty_string(item, "forbidden_adjustment_guard", label=label)
        _require_non_empty_string(item, "rationale", label=label)

        if verdict == "pass" and not positive_signals:
            raise CritiqueContractError(
                f"{label}.observed_positive_signals must be non-empty for pass verdict"
            )
        if verdict in {"pass", "not_applicable"} and route != "none":
            raise CritiqueContractError(f"{label}.route must be none for verdict {verdict}")
        if verdict in {"weak", "fail", "needs_human"} and route == "none":
            raise CritiqueContractError(f"{label}.route must not be none for verdict {verdict}")
        if route != "none" and not allowed_next_adjustment:
            raise CritiqueContractError(
                f"{label}.allowed_next_adjustment must be non-empty for route {route}"
            )
        if route != "none" and not linked_evidence:
            raise CritiqueContractError(
                f"{label}.linked_evidence must be non-empty for route {route}"
            )

        verdicts[lever_id] = (verdict, route)
    return verdicts


def _validate_v1_12_journal_art_direction_playbook_audit(
    frontmatter: dict[str, Any],
) -> None:
    audit = require_mapping(
        frontmatter.get("journal_art_direction_playbook_audit"),
        "critique frontmatter.journal_art_direction_playbook_audit",
    )
    label = "critique frontmatter.journal_art_direction_playbook_audit"
    schema = _require_non_empty_string(audit, "schema", label=label)
    if schema != vocab.JOURNAL_PLAYBOOK_AUDIT_SCHEMA:
        raise CritiqueContractError(f"{label}.schema must be {vocab.JOURNAL_PLAYBOOK_AUDIT_SCHEMA}")
    _require_non_empty_string(audit, "playbook_id", label=label)
    _require_non_empty_string(audit, "venue_context", label=label)
    raw_design_center = _require_non_empty_list(
        audit.get("design_center"),
        f"{label}.design_center",
    )
    seen_ids: set[str] = set()
    for index, raw_item in enumerate(raw_design_center):
        item_label = f"{label}.design_center[{index}]"
        item = require_mapping(raw_item, item_label)
        item_id = _require_non_empty_string(item, "id", label=item_label)
        if item_id in seen_ids:
            raise CritiqueContractError(f"{label}.design_center has duplicate id: {item_id}")
        seen_ids.add(item_id)
        verdict = _require_enum(
            item,
            "verdict",
            vocab.JOURNAL_PLAYBOOK_VERDICTS,
            label=item_label,
        )
        _require_non_empty_string(item, "evidence", label=item_label)
        positive_signal_refs = _validate_string_list(
            item.get("positive_signal_refs"),
            f"{item_label}.positive_signal_refs",
            require_non_empty=verdict == "pass",
        )
        anti_pattern_refs = _validate_string_list(
            item.get("anti_pattern_refs"),
            f"{item_label}.anti_pattern_refs",
            require_non_empty=verdict in {"weak", "fail", "needs_human"},
        )
        route = _require_enum(
            item,
            "route",
            vocab.JOURNAL_PLAYBOOK_ROUTES,
            label=item_label,
        )
        linked_evidence = _validate_string_list(
            item.get("linked_evidence"),
            f"{item_label}.linked_evidence",
            require_non_empty=verdict in {"weak", "fail", "needs_human"},
        )
        _require_non_empty_string(item, "rationale", label=item_label)
        if verdict == "pass" and not positive_signal_refs:
            raise CritiqueContractError(
                f"{item_label}.positive_signal_refs must be non-empty for pass verdict"
            )
        if verdict in {"weak", "fail", "needs_human"} and not anti_pattern_refs:
            raise CritiqueContractError(
                f"{item_label}.anti_pattern_refs must be non-empty for verdict {verdict}"
            )
        if verdict in {"pass", "not_applicable"} and route != "none":
            raise CritiqueContractError(f"{item_label}.route must be none for verdict {verdict}")
        if verdict in {"weak", "fail", "needs_human"} and route == "none":
            raise CritiqueContractError(
                f"{item_label}.route must not be none for verdict {verdict}"
            )
        if route != "none" and not linked_evidence:
            raise CritiqueContractError(
                f"{item_label}.linked_evidence must be non-empty for route {route}"
            )

    route_rule = require_mapping(
        audit.get("route_rule_applied"),
        f"{label}.route_rule_applied",
    )
    _require_non_empty_string(route_rule, "id", label=f"{label}.route_rule_applied")
    _require_enum(
        route_rule,
        "recommended_path",
        vocab.JOURNAL_PLAYBOOK_ROUTES - {"none"},
        label=f"{label}.route_rule_applied",
    )
    _require_non_empty_string(route_rule, "rationale", label=f"{label}.route_rule_applied")

    raw_triggers = _require_list(
        audit.get("human_review_triggers"),
        f"{label}.human_review_triggers",
    )
    for index, raw_trigger in enumerate(raw_triggers):
        trigger_label = f"{label}.human_review_triggers[{index}]"
        trigger = require_mapping(raw_trigger, trigger_label)
        _require_non_empty_string(trigger, "id", label=trigger_label)
        if not isinstance(trigger.get("active"), bool):
            raise CritiqueContractError(f"{trigger_label}.active must be a boolean")
        _require_non_empty_string(trigger, "rationale", label=trigger_label)


def _validate_v1_8_crop_audit_log(frontmatter: dict[str, Any]) -> None:
    raw_items = _require_non_empty_list(
        frontmatter.get("crop_audit_log"),
        "critique frontmatter.crop_audit_log",
    )
    micro_defect_ids = {
        str(item.get("id")).strip()
        for item in frontmatter.get("micro_defects", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item.get("id").strip()
    }
    for index, raw_item in enumerate(raw_items):
        label = f"critique frontmatter.crop_audit_log[{index}]"
        item = require_mapping(raw_item, label)
        _require_non_empty_string(item, "crop_id", label=label)
        path = _require_non_empty_string(item, "path", label=label)
        if not path.startswith("build/audit_crops/"):
            raise CritiqueContractError(f"{label}.path must point to build/audit_crops/*.png")
        _require_non_empty_string(item, "source", label=label)
        if item.get("inspected") is not True:
            raise CritiqueContractError(f"{label}.inspected must be true")
        verdict = _require_enum(item, "verdict", vocab.CROP_AUDIT_VERDICTS, label=label)
        linked_micro_defect_id = _require_string_value(
            item,
            "linked_micro_defect_id",
            label=label,
        )
        _require_non_empty_string(item, "rationale", label=label)
        if verdict != "defect":
            continue
        if not linked_micro_defect_id:
            raise CritiqueContractError(
                f"{label}.linked_micro_defect_id must be set when verdict is defect"
            )
        if linked_micro_defect_id not in micro_defect_ids:
            raise CritiqueContractError(
                f"{label}.linked_micro_defect_id must reference micro_defects[].id"
            )


def _finding_ids(frontmatter: dict[str, Any]) -> set[str]:
    finding_ids: set[str] = set()
    for item in frontmatter.get("findings", []):
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            finding_ids.add(item["id"].strip())
    for panel in frontmatter.get("panels", []):
        if not isinstance(panel, dict):
            continue
        for item in panel.get("findings", []):
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                finding_ids.add(item["id"].strip())
    return {item for item in finding_ids if item}


def _micro_defect_ids(frontmatter: dict[str, Any]) -> set[str]:
    return {
        item["id"].strip()
        for item in frontmatter.get("micro_defects", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"].strip()
    }


def _validate_v1_13_crop_anomaly_accounting(frontmatter: dict[str, Any]) -> None:
    raw_items = _require_non_empty_list(
        frontmatter.get("crop_audit_log"),
        "critique frontmatter.crop_audit_log",
    )
    micro_defect_ids = {
        str(item.get("id")).strip()
        for item in frontmatter.get("micro_defects", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item.get("id").strip()
    }
    finding_ids = _finding_ids(frontmatter)
    for index, raw_item in enumerate(raw_items):
        label = f"critique frontmatter.crop_audit_log[{index}]"
        item = require_mapping(raw_item, label)
        anomaly = _require_enum(
            item,
            "unintended_visible_anomaly",
            vocab.CROP_ANOMALY_VERDICTS,
            label=label,
        )
        _require_non_empty_string(item, "anomaly_rationale", label=label)
        anomaly_link = _require_string_value(item, "anomaly_link", label=label)
        if anomaly != "present":
            continue
        if not anomaly_link:
            raise CritiqueContractError(
                f"{label}.anomaly_link must be set when unintended_visible_anomaly is present"
            )
        if anomaly_link.startswith("accept_simplification:"):
            if not anomaly_link.split(":", 1)[1].strip():
                raise CritiqueContractError(
                    f"{label}.anomaly_link accept_simplification reason must be non-empty"
                )
            continue
        if anomaly_link not in micro_defect_ids and anomaly_link not in finding_ids:
            raise CritiqueContractError(
                f"{label}.anomaly_link must reference a finding id, micro_defect id, "
                "or accept_simplification:<reason>"
            )


def _require_non_empty_string_list(value: Any, label: str) -> list[str]:
    items = _require_non_empty_list(value, label)
    result: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            raise CritiqueContractError(f"{label}[{index}] must be a non-empty string")
        result.append(item.strip())
    return result


def _generic_observation(value: str) -> bool:
    normalized = " ".join(value.lower().split())
    generic_values = {
        "all good",
        "clear",
        "looks fine",
        "no defect",
        "no issue",
        "ok",
        "pass",
    }
    return normalized in generic_values or len(normalized) < 24


def _candidate_ref_from_source(source: str) -> str | None:
    if ":" not in source:
        return None
    prefix, value = source.split(":", 1)
    if prefix in {"visual_clash", "text_boundary", "label_path", "undeclared_geometry"}:
        value = value.strip()
        return value or None
    return None


def _validate_v1_16_grounded_crop_observations(frontmatter: dict[str, Any]) -> None:
    raw_items = _require_non_empty_list(
        frontmatter.get("crop_audit_log"),
        "critique frontmatter.crop_audit_log",
    )
    for index, raw_item in enumerate(raw_items):
        label = f"critique frontmatter.crop_audit_log[{index}]"
        item = require_mapping(raw_item, label)
        _require_non_empty_string_list(item.get("observed_objects"), f"{label}.observed_objects")
        relationship = _require_non_empty_string(item, "local_relationship", label=label)
        if _generic_observation(relationship):
            raise CritiqueContractError(f"{label}.local_relationship must be crop-local")
        candidate_refs = item.get("candidate_refs")
        if not isinstance(candidate_refs, list) or not all(
            isinstance(ref, str) and ref.strip() for ref in candidate_refs
        ):
            raise CritiqueContractError(f"{label}.candidate_refs must be a string list")
        source = _require_non_empty_string(item, "source", label=label)
        expected_ref = _candidate_ref_from_source(source)
        if expected_ref and expected_ref not in {ref.strip() for ref in candidate_refs}:
            raise CritiqueContractError(
                f"{label}.candidate_refs must include deterministic candidate {expected_ref}"
            )


def _validate_v1_15_aesthetic_gate_audit(frontmatter: dict[str, Any]) -> None:
    raw_items = _require_mapping_items(
        frontmatter.get("aesthetic_gate_audit"),
        "critique frontmatter.aesthetic_gate_audit",
    )
    slots: list[str] = []
    for index, item in enumerate(raw_items):
        label = f"critique frontmatter.aesthetic_gate_audit[{index}]"
        slot = _require_enum(item, "slot", frozenset(vocab.AESTHETIC_GATE_SLOTS), label=label)
        slots.append(slot)
        verdict = _require_enum(
            item,
            "verdict",
            vocab.AESTHETIC_GATE_VERDICTS,
            label=label,
        )
        route = _require_enum(item, "route", vocab.AESTHETIC_GATE_ROUTES, label=label)
        _require_non_empty_string(item, "evidence", label=label)
        _require_non_empty_string(item, "rationale", label=label)
        _validate_string_list(
            item.get("linked_evidence"),
            f"{label}.linked_evidence",
            require_non_empty=verdict in {"weak", "fail", "needs_human"} or route != "pass",
        )
        if verdict == "pass" and route != "pass":
            raise CritiqueContractError(f"{label}.route must be pass for pass verdict")
        if verdict in {"weak", "fail", "needs_human"} and route == "pass":
            raise CritiqueContractError(f"{label}.route must not be pass for verdict {verdict}")
        trigger_path = _editorial_trigger_recommended_path(frontmatter)
        if route == "svg_polish" and trigger_path != "ready_for_svg_polish":
            raise CritiqueContractError(
                f"{label}.route svg_polish requires "
                "editorial_art_direction.tikz_vs_svg_polish_trigger recommended_path "
                "ready_for_svg_polish"
            )
        if route == "semantic_backport" and trigger_path != "semantic_backport_required":
            raise CritiqueContractError(
                f"{label}.route semantic_backport requires recommended_path "
                "semantic_backport_required"
            )
    duplicate_slots = sorted({slot for slot in slots if slots.count(slot) > 1})
    if duplicate_slots:
        raise CritiqueContractError(
            "critique frontmatter.aesthetic_gate_audit has duplicate slots: "
            + ", ".join(duplicate_slots)
        )
    missing_slots = [slot for slot in vocab.AESTHETIC_GATE_SLOTS if slot not in slots]
    if missing_slots:
        raise CritiqueContractError(
            "critique frontmatter.aesthetic_gate_audit missing slots: " + ", ".join(missing_slots)
        )


def _validate_v1_17_aesthetic_antipattern_audit(frontmatter: dict[str, Any]) -> None:
    raw_items = _require_mapping_items(
        frontmatter.get("aesthetic_antipattern_audit"),
        "critique frontmatter.aesthetic_antipattern_audit",
    )
    ids: list[str] = []
    for index, item in enumerate(raw_items):
        label = f"critique frontmatter.aesthetic_antipattern_audit[{index}]"
        anti_pattern_id = _require_enum(
            item,
            "id",
            frozenset(vocab.AESTHETIC_ANTIPATTERN_IDS),
            label=label,
        )
        ids.append(anti_pattern_id)
        verdict = _require_enum(
            item,
            "verdict",
            vocab.AESTHETIC_ANTIPATTERN_VERDICTS,
            label=label,
        )
        _require_enum(item, "severity", vocab.FINDING_SEVERITIES, label=label)
        route = _require_enum(
            item,
            "route",
            vocab.AESTHETIC_ANTIPATTERN_ROUTES,
            label=label,
        )
        evidence = _require_non_empty_string(item, "evidence", label=label)
        if _generic_observation(evidence):
            raise CritiqueContractError(f"{label}.evidence must be current-artifact specific")
        rationale = _require_non_empty_string(item, "rationale", label=label)
        if _generic_observation(rationale):
            raise CritiqueContractError(f"{label}.rationale must explain the route")
        linked_evidence = _validate_string_list(
            item.get("linked_evidence"),
            f"{label}.linked_evidence",
            require_non_empty=verdict in {"present", "needs_human"} or route != "none",
        )
        if verdict in {"absent", "not_applicable"} and route != "none":
            raise CritiqueContractError(f"{label}.route must be none for verdict {verdict}")
        if verdict in {"present", "needs_human"} and route == "none":
            raise CritiqueContractError(f"{label}.route must not be none for verdict {verdict}")
        if route == "accept_simplification" and "accept" not in rationale.lower():
            raise CritiqueContractError(
                f"{label}.rationale must explicitly justify accept_simplification"
            )
        _validate_v1_17_route_contract(
            label=label,
            route=route,
            linked_evidence=linked_evidence,
            frontmatter=frontmatter,
        )

    duplicate_ids = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
    if duplicate_ids:
        raise CritiqueContractError(
            "critique frontmatter.aesthetic_antipattern_audit has duplicate ids: "
            + ", ".join(duplicate_ids)
        )
    missing_ids = [item_id for item_id in vocab.AESTHETIC_ANTIPATTERN_IDS if item_id not in ids]
    if missing_ids:
        raise CritiqueContractError(
            "critique frontmatter.aesthetic_antipattern_audit missing ids: "
            + ", ".join(missing_ids)
        )


def _validate_v1_17_route_contract(
    *,
    label: str,
    route: str,
    linked_evidence: list[str],
    frontmatter: dict[str, Any],
) -> None:
    trigger_path = _editorial_trigger_recommended_path(frontmatter)
    finding_ids = _finding_ids(frontmatter)
    micro_defect_ids = _micro_defect_ids(frontmatter)
    if route == "svg_polish" and trigger_path != "ready_for_svg_polish":
        raise CritiqueContractError(
            f"{label}.route svg_polish requires "
            "editorial_art_direction.tikz_vs_svg_polish_trigger recommended_path "
            "ready_for_svg_polish"
        )
    if route == "semantic_backport" and trigger_path != "semantic_backport_required":
        raise CritiqueContractError(
            f"{label}.route semantic_backport requires recommended_path semantic_backport_required"
        )
    if route == "human_art_direction" and (
        "editorial_art_direction.human_art_direction_gate" not in linked_evidence
    ):
        raise CritiqueContractError(
            f"{label}.route human_art_direction requires "
            "editorial_art_direction.human_art_direction_gate linked_evidence"
        )
    if route == "tikz_patch" and not any(
        ref in finding_ids or ref in micro_defect_ids or ref.startswith("quality_axes.")
        for ref in linked_evidence
    ):
        raise CritiqueContractError(
            f"{label}.route tikz_patch must link to a finding, micro_defect, or quality axis"
        )


def _validate_v1_17_weakest_panel_coherence(frontmatter: dict[str, Any]) -> None:
    label = "critique frontmatter.weakest_panel_coherence"
    item = require_mapping(frontmatter.get("weakest_panel_coherence"), label)
    _require_non_empty_string(item, "panel_id", label=label)
    _require_non_empty_string(item, "subregion_id", label=label)
    weakness_type = _require_enum(
        item,
        "weakness_type",
        vocab.WEAKEST_PANEL_WEAKNESS_TYPES,
        label=label,
    )
    route = _require_enum(item, "route", vocab.AESTHETIC_ANTIPATTERN_ROUTES, label=label)
    evidence = _require_non_empty_string(item, "evidence", label=label)
    if _generic_observation(evidence):
        raise CritiqueContractError(f"{label}.evidence must be current-artifact specific")
    rationale = _require_non_empty_string(item, "rationale", label=label)
    if _generic_observation(rationale):
        raise CritiqueContractError(f"{label}.rationale must explain the route")
    if weakness_type == "none" and route != "none":
        raise CritiqueContractError(f"{label}.route must be none for weakness_type none")
    if weakness_type != "none" and route == "none":
        raise CritiqueContractError(f"{label}.route must not be none for weakest panel")
    linked_evidence = _validate_string_list(
        item.get("linked_evidence"),
        f"{label}.linked_evidence",
        require_non_empty=weakness_type != "none" or route != "none",
    )
    _validate_v1_17_route_contract(
        label=label,
        route=route,
        linked_evidence=linked_evidence,
        frontmatter=frontmatter,
    )


def _validate_v1_17_reference_learning_accountability(
    frontmatter: dict[str, Any],
) -> None:
    label = "critique frontmatter.reference_learning_accountability"
    item = require_mapping(frontmatter.get("reference_learning_accountability"), label)
    _require_non_empty_string(item, "learned_principle", label=label)
    _require_non_empty_string(item, "rejected_copy_target", label=label)
    overcopying = _require_enum(
        item,
        "overcopying",
        vocab.REFERENCE_LEARNING_ACCOUNTING_VERDICTS,
        label=label,
    )
    underlearning = _require_enum(
        item,
        "underlearning",
        vocab.REFERENCE_LEARNING_ACCOUNTING_VERDICTS,
        label=label,
    )
    route = _require_enum(item, "route", vocab.AESTHETIC_ANTIPATTERN_ROUTES, label=label)
    evidence = _require_non_empty_string(item, "evidence", label=label)
    if _generic_observation(evidence):
        raise CritiqueContractError(f"{label}.evidence must be current-artifact specific")
    rationale = _require_non_empty_string(item, "rationale", label=label)
    if _generic_observation(rationale):
        raise CritiqueContractError(f"{label}.rationale must explain reference learning")
    active = overcopying in {"present", "needs_human"} or underlearning in {
        "present",
        "needs_human",
    }
    if not active and route != "none":
        raise CritiqueContractError(f"{label}.route must be none when reference misuse is absent")
    if active and route == "none":
        raise CritiqueContractError(f"{label}.route must not be none for reference misuse")
    linked_evidence = _validate_string_list(
        item.get("linked_evidence"),
        f"{label}.linked_evidence",
        require_non_empty=active or route != "none",
    )
    _validate_v1_17_route_contract(
        label=label,
        route=route,
        linked_evidence=linked_evidence,
        frontmatter=frontmatter,
    )


def validate_critique_schema(frontmatter: dict[str, Any]) -> None:
    """Validate schema-specific critique.md frontmatter fields."""
    critique_schema = frontmatter.get("schema")
    if critique_schema == vocab.CRITIQUE_SCHEMA_V1:
        raise CritiqueContractError(
            f"{vocab.CRITIQUE_SCHEMA_V1} is retired: it predates audit_enumeration "
            "and ran zero validators (warn-only), so an empty critique passed. "
            "Re-run /fig_critique to emit a v1.x critique with audit_enumeration."
        )
    elif critique_schema in vocab.RETIRED_CRITIQUE_SCHEMAS:
        raise CritiqueContractError(
            f"{critique_schema} is retired: it is no longer emitted by /fig_critique. "
            "Re-run /fig_critique to emit a supported critique schema."
        )
    elif critique_schema == vocab.CRITIQUE_SCHEMA_V1_10:
        _validate_v1_1_audit(frontmatter)
        quality_verdicts = _validate_v1_2_quality_axes(frontmatter)
        top_tier_verdicts = _validate_v1_3_top_tier_audit(frontmatter)
        _validate_v1_4_micro_defects(frontmatter)
        _validate_v1_10_accept_simplification(frontmatter)
        editorial_verdicts = _validate_v1_5_editorial_art_direction(frontmatter)
        _validate_v1_8_crop_audit_log(frontmatter)
        _validate_journal_grade_assessment(
            frontmatter,
            quality_verdicts,
            top_tier_verdicts,
            editorial_verdicts,
            allow_reference_calibration=True,
        )
        _validate_v1_2_audit_to_finding(frontmatter)
    elif critique_schema == vocab.CRITIQUE_SCHEMA_V1_14:
        _validate_v1_1_audit(frontmatter)
        quality_verdicts = _validate_v1_2_quality_axes(frontmatter)
        top_tier_verdicts = _validate_v1_3_top_tier_audit(frontmatter)
        _validate_v1_4_micro_defects(frontmatter)
        _validate_v1_10_accept_simplification(frontmatter)
        editorial_verdicts = _validate_v1_5_editorial_art_direction(frontmatter)
        _validate_v1_14_editorial_route_detail(frontmatter)
        _validate_v1_8_crop_audit_log(frontmatter)
        _validate_v1_13_crop_anomaly_accounting(frontmatter)
        if "aesthetic_lever_audit" in frontmatter:
            _validate_v1_11_aesthetic_lever_audit(frontmatter)
        if "journal_art_direction_playbook_audit" in frontmatter:
            _validate_v1_12_journal_art_direction_playbook_audit(frontmatter)
        _validate_journal_grade_assessment(
            frontmatter,
            quality_verdicts,
            top_tier_verdicts,
            editorial_verdicts,
            allow_reference_calibration=True,
        )
        _validate_v1_2_audit_to_finding(frontmatter)
    elif critique_schema == vocab.CRITIQUE_SCHEMA_V1_17:
        _validate_v1_1_audit(frontmatter)
        quality_verdicts = _validate_v1_2_quality_axes(frontmatter)
        top_tier_verdicts = _validate_v1_3_top_tier_audit(frontmatter)
        _validate_v1_4_micro_defects(frontmatter)
        _validate_v1_10_accept_simplification(frontmatter)
        editorial_verdicts = _validate_v1_5_editorial_art_direction(frontmatter)
        _validate_v1_14_editorial_route_detail(frontmatter)
        _validate_v1_8_crop_audit_log(frontmatter)
        _validate_v1_13_crop_anomaly_accounting(frontmatter)
        _validate_v1_16_grounded_crop_observations(frontmatter)
        _validate_v1_17_aesthetic_antipattern_audit(frontmatter)
        _validate_v1_17_weakest_panel_coherence(frontmatter)
        _validate_v1_17_reference_learning_accountability(frontmatter)
        if "aesthetic_lever_audit" in frontmatter:
            _validate_v1_11_aesthetic_lever_audit(frontmatter)
        if "journal_art_direction_playbook_audit" in frontmatter:
            _validate_v1_12_journal_art_direction_playbook_audit(frontmatter)
        _validate_journal_grade_assessment(
            frontmatter,
            quality_verdicts,
            top_tier_verdicts,
            editorial_verdicts,
            allow_reference_calibration=True,
        )
        _validate_v1_2_audit_to_finding(frontmatter)
    else:
        raise CritiqueContractError(f"unsupported or missing critique schema: {critique_schema!r}")
