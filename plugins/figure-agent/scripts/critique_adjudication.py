"""Parse and validate critique adjudication decisions."""

from __future__ import annotations

import argparse
import re
import sys
import warnings
from pathlib import Path
from typing import Any

import yaml
from quality_manifest import file_sha256

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.critique-adjudication.v1"
CRITIQUE_SCHEMA_V1 = "figure-agent.critique.v1"
CRITIQUE_SCHEMA_V1_1 = "figure-agent.critique.v1.1"
CRITIQUE_SCHEMA_V1_2 = "figure-agent.critique.v1.2"
CRITIQUE_SCHEMA_V1_3 = "figure-agent.critique.v1.3"
ALLOWED_DECISIONS = frozenset({"apply", "dismiss", "defer", "needs_human", "resolved"})
_PATCH_EVIDENCE_REQUIRED = frozenset({"apply", "resolved"})
_ALLOWED_CONCEPTUAL_REFERENCES = frozenset(
    {"provided_reference", "briefing", "reference_pack", "not_provided"}
)
_QUALITY_AXIS_NAMES = (
    "message_storyline",
    "panel_role_coherence",
    "subregion_integration",
    "component_fidelity",
    "scientific_plausibility",
    "composition_layout",
    "label_annotation_semantics",
    "journal_polish",
    "reference_fidelity",
    "publication_readiness",
)
_QUALITY_VERDICTS = frozenset(
    {"pass", "needs_patch", "needs_human", "block", "not_applicable"}
)
_QUALITY_CONFIDENCES = frozenset({"low", "medium", "high"})
_QUALITY_ACTIONS = frozenset(
    {"none", "patch", "human_review", "revise_briefing", "block_release"}
)
_PANEL_ROLES = frozenset(
    {
        "setup",
        "mechanism",
        "result",
        "comparison",
        "control",
        "zoom",
        "model",
        "workflow",
        "context",
    }
)
_PANEL_ROLE_QUALITIES = frozenset({"clear", "weak", "missing", "redundant"})
_QUALITY_SEVERITY_RANK = {
    "pass": 0,
    "needs_patch": 1,
    "needs_human": 2,
    "block": 3,
}
_QUALITY_ACTIONS_BY_VERDICT = {
    "pass": frozenset({"none"}),
    "not_applicable": frozenset({"none"}),
    "needs_patch": frozenset({"patch", "revise_briefing"}),
    "needs_human": frozenset({"human_review", "revise_briefing"}),
    "block": frozenset({"block_release", "human_review"}),
}
_JOURNAL_ASSESSMENT_SCHEMA = "figure-agent.journal-grade-assessment.v1"
_JOURNAL_SCORING_MODE = "fresh_reaudit"
_JOURNAL_BENCHMARK_LEVELS = frozenset(
    {"draft", "solid_manuscript", "high_impact_candidate", "needs_human_art_direction", "blocked"}
)
_JOURNAL_BOTTLENECKS = frozenset(
    {
        "storyline",
        "composition",
        "component_fidelity",
        "scientific_plausibility",
        "label_semantics",
        "polish",
        "reference_fidelity",
        "export_scale_readability",
        "human_policy",
    }
)
_JOURNAL_SCORE_KEYS = frozenset(
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
_JOURNAL_SCORE_BLOCK_KEYS = frozenset({"overall_score", "sub_scores", "score_rationale"})
_TOP_TIER_AUDIT_KEYS = (
    "first_glance_message",
    "target_journal_fit",
    "novelty_claim_support",
    "figure_caption_coupling",
    "visual_economy",
    "cross_panel_semantic_grammar",
    "reader_misinterpretation_risk",
    "reduction_print_readability",
    "accessibility_color_robustness",
    "aesthetic_coherence",
)
_TOP_TIER_AUDIT_VERDICTS = frozenset({"pass", "weak", "fail", "needs_human"})


class CritiqueAdjudicationError(ValueError):
    """Expected user-facing error for malformed critique adjudication files."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CritiqueAdjudicationError(f"{label} must be a mapping")
    return value


def _require_score_value(value: Any, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CritiqueAdjudicationError(f"{label} must be a number from 0 to 100")
    if value < 0 or value > 100:
        raise CritiqueAdjudicationError(f"{label} must be a number from 0 to 100")


def _require_non_empty_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise CritiqueAdjudicationError(f"{label} must be a non-empty list")
    return value


def _require_mapping_items(value: Any, label: str) -> list[dict[str, Any]]:
    items = _require_non_empty_list(value, label)
    mappings: list[dict[str, Any]] = []
    for index, raw_item in enumerate(items):
        mappings.append(_require_mapping(raw_item, f"{label}[{index}]"))
    return mappings


def _require_non_empty_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CritiqueAdjudicationError(f"{label}.{key} must be a non-empty string")
    return value


def _require_string_value(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise CritiqueAdjudicationError(f"{label}.{key} must be a string")
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
        raise CritiqueAdjudicationError(f"{label}.{key} must be one of: {allowed_values}")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise CritiqueAdjudicationError(f"{label} must be a list")
    return value


def _validate_hash(value: str) -> None:
    if not value.startswith("sha256:") or len(value) <= len("sha256:"):
        raise CritiqueAdjudicationError(
            "adjudication.source_critique_hash must be a sha256-prefixed string"
        )


def _validate_sha256_string(value: str, label: str) -> None:
    if not value.startswith("sha256:") or len(value) <= len("sha256:"):
        raise CritiqueAdjudicationError(f"{label} must be a sha256-prefixed string")


def validate_adjudication(data: dict[str, Any]) -> dict[str, Any]:
    """Validate a critique adjudication mapping and return it unchanged."""
    data = _require_mapping(data, "adjudication")
    schema = data.get("schema")
    if schema != SCHEMA:
        raise CritiqueAdjudicationError(f"adjudication.schema must be {SCHEMA}")

    _require_non_empty_string(data, "fixture", label="adjudication")
    source_hash = _require_non_empty_string(data, "source_critique_hash", label="adjudication")
    _validate_hash(source_hash)

    decisions = data.get("decisions")
    if not isinstance(decisions, list):
        raise CritiqueAdjudicationError("adjudication.decisions must be a list")

    seen_finding_ids: set[str] = set()
    for index, raw_decision in enumerate(decisions):
        decision_label = f"adjudication.decisions[{index}]"
        decision_item = _require_mapping(raw_decision, decision_label)
        finding_id = _require_non_empty_string(decision_item, "finding_id", label=decision_label)
        if finding_id in seen_finding_ids:
            raise CritiqueAdjudicationError(
                f"{decision_label}.duplicate finding_id: {finding_id}"
            )
        seen_finding_ids.add(finding_id)
        decision_value = _require_non_empty_string(decision_item, "decision", label=decision_label)
        if decision_value not in ALLOWED_DECISIONS:
            allowed = ", ".join(sorted(ALLOWED_DECISIONS))
            raise CritiqueAdjudicationError(
                f"{decision_label}.decision must be one of: {allowed}"
            )
        _require_non_empty_string(decision_item, "reason", label=decision_label)
        if decision_value in _PATCH_EVIDENCE_REQUIRED:
            _require_non_empty_string(decision_item, "patch_target", label=decision_label)
            _require_non_empty_string(decision_item, "evidence", label=decision_label)

    return data


def load_adjudication(path: Path) -> dict[str, Any]:
    """Load and validate a critique adjudication YAML file."""
    if not path.is_file():
        raise CritiqueAdjudicationError(f"missing adjudication: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise CritiqueAdjudicationError(f"invalid UTF-8 in {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise CritiqueAdjudicationError(f"invalid YAML in {path}: {exc}") from exc
    return validate_adjudication(data)


def write_adjudication(path: Path, data: dict[str, Any]) -> None:
    """Validate and write a critique adjudication YAML file."""
    validated = validate_adjudication(data)
    path.write_text(
        yaml.safe_dump(validated, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def _critique_frontmatter(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CritiqueAdjudicationError(f"missing critique: {path}")

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise CritiqueAdjudicationError(f"invalid UTF-8 in {path}: {exc}") from exc
    if not lines or lines[0].strip() != "---":
        raise CritiqueAdjudicationError(f"missing critique frontmatter: {path}")

    end_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if end_index is None:
        raise CritiqueAdjudicationError(f"unterminated critique frontmatter: {path}")

    try:
        data = yaml.safe_load("\n".join(lines[1:end_index])) or {}
    except yaml.YAMLError as exc:
        raise CritiqueAdjudicationError(f"invalid YAML in {path}: {exc}") from exc
    return _require_mapping(data, "critique frontmatter")


def _finding_id(finding: dict[str, Any], label: str) -> str:
    value = finding.get("id")
    if not isinstance(value, str) or not value.strip():
        raise CritiqueAdjudicationError(f"{label}.id must be a non-empty string")
    return value.strip()


def _validate_v1_1_audit(frontmatter: dict[str, Any]) -> None:
    audit = _require_mapping(
        frontmatter.get("audit_enumeration"),
        "critique frontmatter.audit_enumeration",
    )
    structural = _require_mapping(
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
        if reference not in _ALLOWED_CONCEPTUAL_REFERENCES:
            allowed = ", ".join(sorted(_ALLOWED_CONCEPTUAL_REFERENCES))
            raise CritiqueAdjudicationError(
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
    verdict = _require_enum(axis, "verdict", _QUALITY_VERDICTS, label=label)
    _require_enum(axis, "confidence", _QUALITY_CONFIDENCES, label=label)
    action = _require_enum(axis, "recommended_action", _QUALITY_ACTIONS, label=label)

    allowed_actions = _QUALITY_ACTIONS_BY_VERDICT[verdict]
    if action not in allowed_actions:
        allowed = ", ".join(sorted(allowed_actions))
        raise CritiqueAdjudicationError(
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
            raise CritiqueAdjudicationError(
                f"{label}.blocking_items[{index}] must be a non-empty string"
            )
    if verdict in {"needs_patch", "block"} and not blocking_items:
        raise CritiqueAdjudicationError(
            f"{label}.blocking_items must be a non-empty list for verdict {verdict}"
        )

    if require_panel_roles and verdict != "not_applicable":
        _validate_panel_roles(axis, label)

    return verdict


def _validate_panel_roles(axis: dict[str, Any], axis_label: str) -> None:
    panel_roles = _require_non_empty_list(axis.get("panel_roles"), f"{axis_label}.panel_roles")
    for index, raw_role in enumerate(panel_roles):
        role_label = f"{axis_label}.panel_roles[{index}]"
        role_item = _require_mapping(raw_role, role_label)
        _require_non_empty_string(role_item, "panel_id", label=role_label)
        _require_enum(role_item, "role", _PANEL_ROLES, label=role_label)
        _require_enum(role_item, "role_quality", _PANEL_ROLE_QUALITIES, label=role_label)
        _require_non_empty_string(role_item, "rationale", label=role_label)


def _validate_v1_2_quality_axes(frontmatter: dict[str, Any]) -> dict[str, str]:
    quality_axes = _require_mapping(
        frontmatter.get("quality_axes"),
        "critique frontmatter.quality_axes",
    )
    verdicts: dict[str, str] = {}
    for axis_name in _QUALITY_AXIS_NAMES:
        axis = _require_mapping(
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
        raise CritiqueAdjudicationError(
            "critique frontmatter.quality_axes.publication_readiness.verdict "
            "cannot be not_applicable while upstream axes are applicable"
        )
    if readiness_verdict != "not_applicable" and upstream_verdicts:
        required_rank = max(_QUALITY_SEVERITY_RANK[verdict] for verdict in upstream_verdicts)
        readiness_rank = _QUALITY_SEVERITY_RANK[readiness_verdict]
        if readiness_rank < required_rank:
            raise CritiqueAdjudicationError(
                "critique frontmatter.quality_axes.publication_readiness.verdict "
                "is less severe than an applicable upstream quality axis"
            )
    return verdicts


def _validate_journal_score_block(assessment: dict[str, Any], label: str) -> None:
    present = _JOURNAL_SCORE_BLOCK_KEYS & assessment.keys()
    if not present:
        return
    if present != _JOURNAL_SCORE_BLOCK_KEYS:
        missing = ", ".join(sorted(_JOURNAL_SCORE_BLOCK_KEYS - present))
        raise CritiqueAdjudicationError(
            f"{label} score block is incomplete; missing: {missing}"
        )

    _require_score_value(assessment.get("overall_score"), f"{label}.overall_score")
    sub_scores = _require_mapping(assessment.get("sub_scores"), f"{label}.sub_scores")
    keys = set(sub_scores)
    if keys != _JOURNAL_SCORE_KEYS:
        missing = ", ".join(sorted(_JOURNAL_SCORE_KEYS - keys))
        extra = ", ".join(sorted(keys - _JOURNAL_SCORE_KEYS))
        details = []
        if missing:
            details.append(f"missing: {missing}")
        if extra:
            details.append(f"extra: {extra}")
        suffix = f" ({'; '.join(details)})" if details else ""
        raise CritiqueAdjudicationError(
            f"{label}.sub_scores must contain exactly the required score keys{suffix}"
        )
    for key, value in sub_scores.items():
        _require_score_value(value, f"{label}.sub_scores.{key}")
    _require_non_empty_string(assessment, "score_rationale", label=label)


def _validate_journal_grade_assessment(
    frontmatter: dict[str, Any],
    quality_verdicts: dict[str, str],
    top_tier_verdicts: dict[str, str] | None = None,
) -> None:
    raw_assessment = frontmatter.get("journal_grade_assessment")
    if raw_assessment is None:
        return
    assessment = _require_mapping(
        raw_assessment,
        "critique frontmatter.journal_grade_assessment",
    )
    label = "critique frontmatter.journal_grade_assessment"
    schema = assessment.get("schema")
    if schema != _JOURNAL_ASSESSMENT_SCHEMA:
        raise CritiqueAdjudicationError(f"{label}.schema must be {_JOURNAL_ASSESSMENT_SCHEMA}")
    scoring_mode = _require_string_value(assessment, "scoring_mode", label=label)
    if scoring_mode != _JOURNAL_SCORING_MODE:
        raise CritiqueAdjudicationError(
            f"{label}.scoring_mode must be {_JOURNAL_SCORING_MODE}"
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
        _JOURNAL_BENCHMARK_LEVELS,
        label=label,
    )
    _require_enum(assessment, "confidence", _QUALITY_CONFIDENCES, label=label)
    blockers = _require_list(assessment.get("blockers"), f"{label}.blockers")
    for index, blocker in enumerate(blockers):
        if not isinstance(blocker, str) or not blocker.strip():
            raise CritiqueAdjudicationError(f"{label}.blockers[{index}] must be a string")
    regression_detected = assessment.get("regression_detected")
    if not isinstance(regression_detected, bool):
        raise CritiqueAdjudicationError(f"{label}.regression_detected must be a boolean")
    regressions = _require_list(assessment.get("regressions"), f"{label}.regressions")
    for index, raw_regression in enumerate(regressions):
        regression_label = f"{label}.regressions[{index}]"
        regression = _require_mapping(raw_regression, regression_label)
        _require_non_empty_string(regression, "axis", label=regression_label)
        _require_non_empty_string(regression, "previous_state", label=regression_label)
        _require_non_empty_string(regression, "current_state", label=regression_label)
        _require_non_empty_string(regression, "reason", label=regression_label)
    score_is_gateable = assessment.get("score_is_gateable")
    if not isinstance(score_is_gateable, bool):
        raise CritiqueAdjudicationError(f"{label}.score_is_gateable must be a boolean")
    _require_enum(assessment, "next_quality_bottleneck", _JOURNAL_BOTTLENECKS, label=label)
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
            raise CritiqueAdjudicationError(
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
            raise CritiqueAdjudicationError(
                f"{label}.benchmark_level high_impact_candidate requires passing "
                f"top_tier_audit slots; non-passing slots: {audits}"
            )

    critique_input_hash = frontmatter.get("critique_input_hash")
    if score_is_gateable and assessed_hash != critique_input_hash:
        raise CritiqueAdjudicationError(
            f"{label}.assessed_artifact_hash must match critique_input_hash "
            "when score_is_gateable is true"
        )


def _validate_v1_2_audit_to_finding(frontmatter: dict[str, Any]) -> None:
    quality_axes = _require_mapping(
        frontmatter.get("quality_axes"),
        "critique frontmatter.quality_axes",
    )
    findings = _findings_from_critique(frontmatter)
    finding_ids = {
        _finding_id(finding, f"critique finding {index}")
        for index, finding in enumerate(findings)
    }
    finding_required_axes: list[str] = []
    for axis_name in _QUALITY_AXIS_NAMES:
        axis = _require_mapping(
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
            raise CritiqueAdjudicationError(
                "critique frontmatter.quality_axes."
                f"{axis_name}.blocking_items must reference a panel/top-level "
                "finding id for patch or block_release action"
            )
    if finding_required_axes and not finding_ids:
        axes = ", ".join(finding_required_axes)
        raise CritiqueAdjudicationError(
            "critique frontmatter.quality_axes must include at least one "
            f"panel/top-level findings item for patch or block_release axis: {axes}"
        )


def _validate_v1_3_top_tier_audit(frontmatter: dict[str, Any]) -> dict[str, str]:
    top_tier_audit = _require_mapping(
        frontmatter.get("top_tier_audit"),
        "critique frontmatter.top_tier_audit",
    )
    findings = _findings_from_critique(frontmatter)
    blocking_without_finding: list[str] = []
    verdicts: dict[str, str] = {}
    for key in _TOP_TIER_AUDIT_KEYS:
        label = f"critique frontmatter.top_tier_audit.{key}"
        item = _require_mapping(top_tier_audit.get(key), label)
        verdict = _require_enum(item, "verdict", _TOP_TIER_AUDIT_VERDICTS, label=label)
        verdicts[key] = verdict
        _require_non_empty_string(item, "finding", label=label)
        _require_non_empty_string(item, "concrete_fix", label=label)
        if not isinstance(item.get("blocks_high_impact"), bool):
            raise CritiqueAdjudicationError(f"{label}.blocks_high_impact must be a boolean")
        if verdict == "fail" or item["blocks_high_impact"]:
            blocking_without_finding.append(key)
    if blocking_without_finding and not findings:
        slots = ", ".join(blocking_without_finding)
        raise CritiqueAdjudicationError(
            "critique frontmatter.top_tier_audit requires at least one "
            f"panel/top-level finding for blocking slots: {slots}"
        )
    return verdicts


def _patch_target_from_tex_lines(fixture: str, finding: dict[str, Any]) -> str:
    tex_lines = finding.get("tex_lines")
    if (
        not isinstance(tex_lines, list)
        or len(tex_lines) != 2
        or not all(isinstance(value, int) for value in tex_lines)
    ):
        return ""
    start, end = tex_lines
    return f"examples/{fixture}/{fixture}.tex lines {start}-{end}"


def _findings_from_critique(frontmatter: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    panels = frontmatter.get("panels", [])
    if panels is None:
        panels = []
    if not isinstance(panels, list):
        raise CritiqueAdjudicationError("critique frontmatter.panels must be a list")
    for panel_index, raw_panel in enumerate(panels):
        panel_label = f"critique frontmatter.panels[{panel_index}]"
        panel = _require_mapping(raw_panel, panel_label)
        panel_findings = panel.get("findings", [])
        if panel_findings is None:
            panel_findings = []
        if not isinstance(panel_findings, list):
            raise CritiqueAdjudicationError(f"{panel_label}.findings must be a list")
        for finding_index, raw_finding in enumerate(panel_findings):
            finding_label = f"{panel_label}.findings[{finding_index}]"
            findings.append(_require_mapping(raw_finding, finding_label))

    top_level_findings = frontmatter.get("findings", [])
    if top_level_findings is None:
        top_level_findings = []
    if not isinstance(top_level_findings, list):
        raise CritiqueAdjudicationError("critique frontmatter.findings must be a list")
    for finding_index, raw_finding in enumerate(top_level_findings):
        finding_label = f"critique frontmatter.findings[{finding_index}]"
        findings.append(_require_mapping(raw_finding, finding_label))

    return findings


def build_adjudication_scaffold(example_dir: Path) -> dict[str, Any]:
    """Build a conservative adjudication scaffold from critique.md frontmatter."""
    critique_path = example_dir / "critique.md"
    frontmatter = _critique_frontmatter(critique_path)
    critique_schema = frontmatter.get("schema")
    if critique_schema == CRITIQUE_SCHEMA_V1:
        warnings.warn(
            (
                f"{CRITIQUE_SCHEMA_V1} is legacy; v1.1 critiques should include "
                "audit_enumeration"
            ),
            DeprecationWarning,
            stacklevel=2,
        )
    elif critique_schema == CRITIQUE_SCHEMA_V1_1:
        _validate_v1_1_audit(frontmatter)
    elif critique_schema == CRITIQUE_SCHEMA_V1_2:
        _validate_v1_1_audit(frontmatter)
        quality_verdicts = _validate_v1_2_quality_axes(frontmatter)
        _validate_journal_grade_assessment(frontmatter, quality_verdicts)
        _validate_v1_2_audit_to_finding(frontmatter)
    elif critique_schema == CRITIQUE_SCHEMA_V1_3:
        _validate_v1_1_audit(frontmatter)
        quality_verdicts = _validate_v1_2_quality_axes(frontmatter)
        top_tier_verdicts = _validate_v1_3_top_tier_audit(frontmatter)
        _validate_journal_grade_assessment(frontmatter, quality_verdicts, top_tier_verdicts)
        _validate_v1_2_audit_to_finding(frontmatter)
    elif isinstance(critique_schema, str) and critique_schema.startswith("figure-agent.critique."):
        raise CritiqueAdjudicationError(f"unsupported critique schema: {critique_schema}")
    fixture_value = frontmatter.get("fixture")
    fixture = (
        fixture_value.strip()
        if isinstance(fixture_value, str) and fixture_value.strip()
        else example_dir.name
    )

    decisions: list[dict[str, str]] = []
    for index, finding in enumerate(_findings_from_critique(frontmatter)):
        label = f"critique finding {index}"
        finding_id = _finding_id(finding, label)
        patch_target = _patch_target_from_tex_lines(fixture, finding)
        status = str(finding.get("status", "")).strip().lower()
        if status == "resolved":
            decisions.append(
                {
                    "finding_id": finding_id,
                    "decision": "resolved",
                    "reason": f"Critique marks {finding_id} as resolved.",
                    "patch_target": patch_target or f"examples/{fixture}/{fixture}.tex",
                    "evidence": f"critique.md marks {finding_id} status resolved.",
                }
            )
        else:
            decisions.append(
                {
                    "finding_id": finding_id,
                    "decision": "needs_human",
                    "reason": (
                        f"Review {finding_id} before selecting apply, dismiss, defer, or resolved."
                    ),
                    "patch_target": patch_target,
                    "evidence": f"critique.md finding {finding_id}.",
                }
            )

    return validate_adjudication(
        {
            "schema": SCHEMA,
            "fixture": fixture,
            "source_critique_hash": file_sha256(critique_path),
            "decisions": decisions,
        }
    )


def scaffold_adjudication(example_dir: Path, *, force: bool = False) -> Path:
    """Write critique_adjudication.yaml from critique.md unless it already exists."""
    path = example_dir / "critique_adjudication.yaml"
    if path.exists() and not force:
        raise CritiqueAdjudicationError(f"{path} already exists; pass --force to overwrite")
    write_adjudication(path, build_adjudication_scaffold(example_dir))
    return path


def adjudication_is_stale(adjudication_path: Path, critique_path: Path) -> bool:
    """Return true when adjudication was made against different critique content."""
    adjudication = load_adjudication(adjudication_path)
    if not critique_path.is_file():
        raise CritiqueAdjudicationError(f"missing critique: {critique_path}")
    return adjudication["source_critique_hash"] != file_sha256(critique_path)


def _resolve_example_dir(value: str, repo_root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "examples":
        return repo_root / path
    if len(path.parts) == 1:
        return repo_root / "examples" / value
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold_parser = subparsers.add_parser(
        "scaffold",
        help="create critique_adjudication.yaml from critique.md frontmatter",
    )
    scaffold_parser.add_argument("example", help="fixture name, examples/<name>, or path")
    scaffold_parser.add_argument("--force", action="store_true", help="overwrite an existing file")
    scaffold_parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)

    args = parser.parse_args(argv)
    if args.command == "scaffold":
        example_dir = _resolve_example_dir(args.example, args.repo_root)
        try:
            path = scaffold_adjudication(example_dir, force=args.force)
        except CritiqueAdjudicationError as exc:
            print(f"critique_adjudication.py: {exc}", file=sys.stderr)
            return 1
        print(f"critique_adjudication.py: wrote {path}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
