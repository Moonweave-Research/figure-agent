"""Validate critique.md schema-specific frontmatter contracts."""

from __future__ import annotations

import re
import warnings
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
        (
            "critique frontmatter.audit_enumeration."
            "structural_completeness.missing_from_reference"
        ),
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


def _validate_journal_grade_assessment(
    frontmatter: dict[str, Any],
    quality_verdicts: dict[str, str],
    top_tier_verdicts: dict[str, str] | None = None,
    editorial_verdicts: dict[str, str] | None = None,
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
        raise CritiqueContractError(
            f"{label}.scoring_mode must be {vocab.JOURNAL_SCORING_MODE}"
        )
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


def validate_critique_schema(frontmatter: dict[str, Any]) -> None:
    """Validate schema-specific critique.md frontmatter fields."""
    critique_schema = frontmatter.get("schema")
    if critique_schema == vocab.CRITIQUE_SCHEMA_V1:
        warnings.warn(
            (
                f"{vocab.CRITIQUE_SCHEMA_V1} is legacy; v1.1 critiques should include "
                "audit_enumeration"
            ),
            DeprecationWarning,
            stacklevel=2,
        )
    elif critique_schema == vocab.CRITIQUE_SCHEMA_V1_1:
        _validate_v1_1_audit(frontmatter)
    elif critique_schema == vocab.CRITIQUE_SCHEMA_V1_2:
        _validate_v1_1_audit(frontmatter)
        quality_verdicts = _validate_v1_2_quality_axes(frontmatter)
        _validate_journal_grade_assessment(frontmatter, quality_verdicts)
        _validate_v1_2_audit_to_finding(frontmatter)
    elif critique_schema == vocab.CRITIQUE_SCHEMA_V1_3:
        _validate_v1_1_audit(frontmatter)
        quality_verdicts = _validate_v1_2_quality_axes(frontmatter)
        top_tier_verdicts = _validate_v1_3_top_tier_audit(frontmatter)
        _validate_journal_grade_assessment(frontmatter, quality_verdicts, top_tier_verdicts)
        _validate_v1_2_audit_to_finding(frontmatter)
    elif critique_schema == vocab.CRITIQUE_SCHEMA_V1_4:
        _validate_v1_1_audit(frontmatter)
        quality_verdicts = _validate_v1_2_quality_axes(frontmatter)
        top_tier_verdicts = _validate_v1_3_top_tier_audit(frontmatter)
        _validate_v1_4_micro_defects(frontmatter)
        _validate_journal_grade_assessment(frontmatter, quality_verdicts, top_tier_verdicts)
        _validate_v1_2_audit_to_finding(frontmatter)
    elif critique_schema == vocab.CRITIQUE_SCHEMA_V1_5:
        _validate_v1_1_audit(frontmatter)
        quality_verdicts = _validate_v1_2_quality_axes(frontmatter)
        top_tier_verdicts = _validate_v1_3_top_tier_audit(frontmatter)
        _validate_v1_4_micro_defects(frontmatter)
        editorial_verdicts = _validate_v1_5_editorial_art_direction(frontmatter)
        _validate_journal_grade_assessment(
            frontmatter,
            quality_verdicts,
            top_tier_verdicts,
            editorial_verdicts,
        )
        _validate_v1_2_audit_to_finding(frontmatter)
    elif isinstance(critique_schema, str) and critique_schema.startswith("figure-agent.critique."):
        raise CritiqueContractError(f"unsupported critique schema: {critique_schema}")
