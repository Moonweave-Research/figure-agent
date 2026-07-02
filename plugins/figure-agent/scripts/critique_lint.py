"""Lint critique.md without writing adjudication state."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fixture_identity  # noqa: E402
from aesthetic_intent import (  # noqa: E402
    AESTHETIC_INTENT_SCHEMA_V2,
    AestheticIntentError,
    load_optional_aesthetic_intent,
)
from briefing_grounding import (  # noqa: E402
    explicit_briefing_rule_text,
    has_reference_free_grounding_context,
)
from critique_adjudication import (  # noqa: E402
    CritiqueAdjudicationError,
    build_adjudication_scaffold,
)
from critique_contract import (  # noqa: E402
    CritiqueContractError,
    critique_finding_id,
    critique_findings,
    load_critique_frontmatter,
)
from critique_evidence_lint import critique_evidence_violations  # noqa: E402
from critique_schema_vocab import (  # noqa: E402
    MICRO_DEFECT_ACCEPT_SIMPLIFICATION_MIN_RATIONALE_CHARS,
    MICRO_DEFECT_ACCEPT_SIMPLIFICATION_RATIONALE_MARKERS,
    MICRO_DEFECT_ACCEPT_SIMPLIFICATION_REASONS,
)
from external_vision_review import (  # noqa: E402
    ExternalVisionReviewError,
    external_vision_review_freshness,
    load_optional_external_vision_review,
)
from inputs import parse_briefing, parse_spec  # noqa: E402
from inspection_trace import (  # noqa: E402
    InspectionTraceError,
    load_optional_inspection_trace,
)
from journal_art_direction_playbook import (  # noqa: E402
    JournalArtDirectionPlaybookError,
    journal_playbook_anchors,
    load_optional_journal_art_direction_playbook,
)
from paper_aesthetic_context import (  # noqa: E402
    PaperAestheticContextError,
    load_optional_paper_aesthetic_context,
    paper_context_anchors,
)
from quality_manifest import file_sha256  # noqa: E402
from reference_contract import (  # noqa: E402
    declared_figure_reference_path,
    participating_panel_reference_paths,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
VISUAL_CLASH_ACCOUNTING_SCHEMA = "figure-agent.critique.v1.7"
CROP_AUDIT_ACCOUNTING_SCHEMA = "figure-agent.critique.v1.8"
VISUAL_CLASH_ACCOUNTING_SCHEMAS = frozenset(
    {
        "figure-agent.critique.v1.7",
        "figure-agent.critique.v1.8",
        "figure-agent.critique.v1.9",
        "figure-agent.critique.v1.10",
        "figure-agent.critique.v1.11",
        "figure-agent.critique.v1.12",
        "figure-agent.critique.v1.13",
        "figure-agent.critique.v1.14",
        "figure-agent.critique.v1.15",
        "figure-agent.critique.v1.16",
        "figure-agent.critique.v1.17",
    }
)
CROP_AUDIT_ACCOUNTING_SCHEMAS = frozenset(
    {
        "figure-agent.critique.v1.8",
        "figure-agent.critique.v1.9",
        "figure-agent.critique.v1.10",
        "figure-agent.critique.v1.11",
        "figure-agent.critique.v1.12",
        "figure-agent.critique.v1.13",
        "figure-agent.critique.v1.14",
        "figure-agent.critique.v1.15",
        "figure-agent.critique.v1.16",
        "figure-agent.critique.v1.17",
    }
)
STRUCTURED_ACCEPT_SIMPLIFICATION_SCHEMAS = frozenset(
    {
        "figure-agent.critique.v1.10",
        "figure-agent.critique.v1.11",
        "figure-agent.critique.v1.12",
        "figure-agent.critique.v1.13",
        "figure-agent.critique.v1.14",
        "figure-agent.critique.v1.15",
        "figure-agent.critique.v1.16",
        "figure-agent.critique.v1.17",
    }
)
_VISUAL_CLASH_ACCEPT_MIN_OBSERVATION_CHARS = 80
_VISUAL_CLASH_ACCEPT_RATIONALE_MARKERS = MICRO_DEFECT_ACCEPT_SIMPLIFICATION_RATIONALE_MARKERS
_STRUCTURED_ACCEPT_MIN_RATIONALE_CHARS = MICRO_DEFECT_ACCEPT_SIMPLIFICATION_MIN_RATIONALE_CHARS
TEXT_BOUNDARY_ACCOUNTING_SCHEMAS = frozenset(
    {
        "figure-agent.critique.v1.10",
        "figure-agent.critique.v1.11",
        "figure-agent.critique.v1.12",
        "figure-agent.critique.v1.13",
        "figure-agent.critique.v1.14",
        "figure-agent.critique.v1.15",
        "figure-agent.critique.v1.16",
        "figure-agent.critique.v1.17",
    }
)
AESTHETIC_LEVER_ACCOUNTING_SCHEMAS = frozenset(
    {
        "figure-agent.critique.v1.11",
        "figure-agent.critique.v1.12",
        "figure-agent.critique.v1.13",
        "figure-agent.critique.v1.14",
        "figure-agent.critique.v1.15",
        "figure-agent.critique.v1.16",
        "figure-agent.critique.v1.17",
    }
)
LABEL_PATH_ACCOUNTING_SCHEMAS = frozenset(
    {
        "figure-agent.critique.v1.10",
        "figure-agent.critique.v1.11",
        "figure-agent.critique.v1.12",
        "figure-agent.critique.v1.13",
        "figure-agent.critique.v1.14",
        "figure-agent.critique.v1.15",
        "figure-agent.critique.v1.16",
        "figure-agent.critique.v1.17",
    }
)
UNDECLARED_GEOMETRY_ACCOUNTING_SCHEMAS = frozenset(
    {
        "figure-agent.critique.v1.4",
        "figure-agent.critique.v1.5",
        "figure-agent.critique.v1.6",
        "figure-agent.critique.v1.7",
        "figure-agent.critique.v1.8",
        "figure-agent.critique.v1.9",
        "figure-agent.critique.v1.10",
        "figure-agent.critique.v1.11",
        "figure-agent.critique.v1.12",
        "figure-agent.critique.v1.13",
        "figure-agent.critique.v1.14",
        "figure-agent.critique.v1.15",
        "figure-agent.critique.v1.16",
        "figure-agent.critique.v1.17",
    }
)
_HISTORICAL_VISUAL_CLASH_FIXTURE = "fig1_visual_clash_regression"
_HISTORICAL_VISUAL_CLASH_EXPECTED_KINDS = {
    ("VC026", "V"): "label_glyph_overlaps_internal_drawing",
    ("VC027", "s"): "label_glyph_overlaps_internal_drawing",
    ("VC050", "HV+"): "label_backdrop_overflows_outline",
}
_AESTHETIC_INTENT_REQUIRED_SLOTS = (
    ("top_tier_audit", "aesthetic_coherence"),
    ("editorial_art_direction", "visual_identity"),
    ("editorial_art_direction", "aesthetic_risk"),
    ("editorial_art_direction", "tikz_vs_svg_polish_trigger"),
)
_PAPER_CONTEXT_REQUIRED_SLOTS = (
    ("top_tier_audit", "cross_panel_semantic_grammar"),
    ("top_tier_audit", "aesthetic_coherence"),
    ("editorial_art_direction", "visual_identity"),
)
_JOURNAL_PLAYBOOK_REQUIRED_SLOTS = (
    ("top_tier_audit", "first_glance_message"),
    ("top_tier_audit", "target_journal_fit"),
    ("top_tier_audit", "visual_economy"),
    ("top_tier_audit", "reduction_print_readability"),
    ("top_tier_audit", "aesthetic_coherence"),
    ("editorial_art_direction", "visual_identity"),
    ("editorial_art_direction", "aesthetic_risk"),
    ("editorial_art_direction", "tikz_vs_svg_polish_trigger"),
    ("journal_grade_assessment", "rationale"),
)
_CURRENT_ARTIFACT_EVIDENCE_MARKERS = (
    "current artifact",
    "current render",
    "rendered figure",
    "rendered panel",
    "visible",
    "visibly",
    "panel ",
    "crop",
    "print-scale",
    "png",
    "pdf",
    "bbox",
)
_SYMBOLIC_ENTITY_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9+\-]+\b")
_TEX_TEXT_COMMAND_RE = re.compile(r"\\(?:mathrm|operatorname|text)\{([^{}]+)\}")
_UNESCAPED_PERCENT_RE = re.compile(r"(?<!\\)%")


@dataclass(frozen=True)
class CritiqueLintViolation:
    severity: str
    category: str
    message: str


def _duplicate_finding_id_violations(frontmatter: dict[str, Any]) -> list[CritiqueLintViolation]:
    seen: set[str] = set()
    violations: list[CritiqueLintViolation] = []
    for index, finding in enumerate(critique_findings(frontmatter)):
        finding_id = critique_finding_id(finding, f"critique finding {index}")
        if finding_id in seen:
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="duplicate_finding_id",
                    message=f"duplicate finding_id: {finding_id}",
                )
            )
        seen.add(finding_id)
    return violations


def _aesthetic_intent_anchor_strings(pack: dict[str, Any]) -> set[str]:
    anchors = {
        str(pack.get("target_journal", "")).strip(),
        str(pack.get("visual_maturity", "")).strip(),
        str(pack.get("density", "")).strip(),
        str(pack.get("reference_style", "")).strip(),
    }
    for key in ("design_principles", "must_avoid", "polish_triggers"):
        raw_items = pack.get(key)
        if not isinstance(raw_items, list):
            continue
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id.strip():
                anchors.add(item_id.strip())
    return {anchor.lower() for anchor in anchors if anchor}


def _text_blob(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_text_blob(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_text_blob(item) for item in value.values())
    return ""


def _contains_aesthetic_anchor(text: str, anchors: set[str]) -> bool:
    for anchor in anchors:
        if re.search(rf"(^|[^A-Za-z0-9_]){re.escape(anchor)}($|[^A-Za-z0-9_])", text):
            return True
    return False


def _contains_anchor_with_current_artifact_evidence(text: str, anchors: set[str]) -> bool:
    return _contains_aesthetic_anchor(text, anchors) and any(
        marker in text for marker in _CURRENT_ARTIFACT_EVIDENCE_MARKERS
    )


def _aesthetic_lever_items(pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_items = pack.get("aesthetic_levers")
    if not isinstance(raw_items, list):
        return {}
    items: dict[str, dict[str, Any]] = {}
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        lever_id = raw_item.get("id")
        if isinstance(lever_id, str) and lever_id.strip():
            items[lever_id.strip()] = raw_item
    return items


def _aesthetic_audit_items(frontmatter: dict[str, Any]) -> list[dict[str, Any]] | None:
    raw_items = frontmatter.get("aesthetic_lever_audit")
    if not isinstance(raw_items, list):
        return None
    return [item for item in raw_items if isinstance(item, dict)]


def _aesthetic_linked_evidence(item: dict[str, Any]) -> list[str]:
    raw_items = item.get("linked_evidence")
    if not isinstance(raw_items, list):
        return []
    return [item.strip() for item in raw_items if isinstance(item, str) and item.strip()]


def _quality_axis_is_blocking(frontmatter: dict[str, Any], evidence: str) -> bool:
    if not evidence.startswith("quality_axes."):
        return False
    axis_name = evidence.removeprefix("quality_axes.")
    quality_axes = frontmatter.get("quality_axes")
    axis = quality_axes.get(axis_name) if isinstance(quality_axes, dict) else None
    if not isinstance(axis, dict):
        return False
    blocking_items = axis.get("blocking_items")
    return isinstance(blocking_items, list) and bool(blocking_items)


def _links_finding_or_quality_axis(frontmatter: dict[str, Any], evidence: list[str]) -> bool:
    finding_ids = {
        critique_finding_id(finding, f"critique finding {index}")
        for index, finding in enumerate(critique_findings(frontmatter))
    }
    return any(
        item in finding_ids or _quality_axis_is_blocking(frontmatter, item) for item in evidence
    )


def _editorial_polish_trigger_path(frontmatter: dict[str, Any]) -> str:
    editorial = frontmatter.get("editorial_art_direction")
    trigger = editorial.get("tikz_vs_svg_polish_trigger") if isinstance(editorial, dict) else None
    path = trigger.get("recommended_path") if isinstance(trigger, dict) else None
    return path.strip() if isinstance(path, str) else ""


def _aesthetic_lever_accounting_violations(
    pack: dict[str, Any],
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    if pack.get("schema") != AESTHETIC_INTENT_SCHEMA_V2:
        return []
    if frontmatter.get("schema") not in AESTHETIC_LEVER_ACCOUNTING_SCHEMAS:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="aesthetic_lever_accounting",
                message=(
                    "aesthetic_intent.yaml schema v2 requires "
                    "critique schema figure-agent.critique.v1.11 or newer"
                ),
            )
        ]

    declared = _aesthetic_lever_items(pack)
    audit_items = _aesthetic_audit_items(frontmatter)
    if audit_items is None:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="aesthetic_lever_accounting",
                message="missing aesthetic_lever_audit for v2 aesthetic intent",
            )
        ]

    lever_ids = [
        item.get("lever_id").strip()
        for item in audit_items
        if isinstance(item.get("lever_id"), str) and item.get("lever_id").strip()
    ]
    duplicate_ids = sorted({lever_id for lever_id in lever_ids if lever_ids.count(lever_id) > 1})
    if duplicate_ids:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="aesthetic_lever_accounting",
                message=f"duplicate lever ids: {', '.join(duplicate_ids)}",
            )
        ]
    declared_ids = set(declared)
    unknown_ids = sorted(lever_id for lever_id in lever_ids if lever_id not in declared_ids)
    if unknown_ids:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="aesthetic_lever_accounting",
                message=f"unknown lever ids: {', '.join(unknown_ids)}",
            )
        ]
    missing_ids = sorted(declared_ids - set(lever_ids))
    if missing_ids:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="aesthetic_lever_accounting",
                message=f"missing declared lever ids: {', '.join(missing_ids)}",
            )
        ]

    item_by_id = {
        item["lever_id"].strip(): item
        for item in audit_items
        if isinstance(item.get("lever_id"), str) and item["lever_id"].strip()
    }
    for lever_id, declared_item in declared.items():
        item = item_by_id[lever_id]
        expected_dimension = declared_item.get("dimension")
        actual_dimension = item.get("dimension")
        if actual_dimension != expected_dimension:
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category="aesthetic_lever_accounting",
                    message=(
                        f"dimension mismatch for {lever_id}: expected "
                        f"{expected_dimension}, got {actual_dimension}"
                    ),
                )
            ]
        verdict = item.get("verdict")
        route = item.get("route")
        priority = declared_item.get("priority")
        default_route = declared_item.get("default_route")
        linked_evidence = _aesthetic_linked_evidence(item)
        if priority == "required" and verdict == "not_applicable":
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category="aesthetic_lever_accounting",
                    message=f"{lever_id} is required and cannot be not_applicable",
                )
            ]
        if verdict in {"weak", "fail", "needs_human"} and route == "none":
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category="aesthetic_lever_accounting",
                    message=f"{lever_id} route must not be none for verdict {verdict}",
                )
            ]
        if verdict == "pass" and route != "none":
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category="aesthetic_lever_accounting",
                    message=f"{lever_id} route must be none for pass verdict",
                )
            ]
        if route != "none" and route != default_route:
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category="aesthetic_lever_accounting",
                    message=(
                        f"{lever_id} route must match declared default_route "
                        f"{default_route}; got {route}"
                    ),
                )
            ]
        if route == "tikz_patch" and not _links_finding_or_quality_axis(
            frontmatter,
            linked_evidence,
        ):
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category="aesthetic_lever_accounting",
                    message=(
                        f"{lever_id} route tikz_patch must link to a finding id or "
                        "quality axis blocking item"
                    ),
                )
            ]
        if route == "svg_polish" and (
            "editorial_art_direction.tikz_vs_svg_polish_trigger" not in linked_evidence
        ):
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category="aesthetic_lever_accounting",
                    message=(
                        f"{lever_id} route svg_polish must cite "
                        "editorial_art_direction.tikz_vs_svg_polish_trigger"
                    ),
                )
            ]
        if route == "svg_polish" and _editorial_polish_trigger_path(frontmatter) != (
            "ready_for_svg_polish"
        ):
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category="aesthetic_lever_accounting",
                    message=(
                        f"{lever_id} route svg_polish requires recommended_path "
                        "ready_for_svg_polish"
                    ),
                )
            ]
        if route == "semantic_backport":
            has_semantic_trigger = (
                "editorial_art_direction.tikz_vs_svg_polish_trigger" in linked_evidence
                and _editorial_polish_trigger_path(frontmatter) == "semantic_backport_required"
            )
            if not has_semantic_trigger:
                return [
                    CritiqueLintViolation(
                        severity="blocker",
                        category="aesthetic_lever_accounting",
                        message=(
                            f"{lever_id} route semantic_backport must cite "
                            "semantic-backport evidence"
                        ),
                    )
                ]
        if route == "human_art_direction" and (
            "editorial_art_direction.human_art_direction_gate" not in linked_evidence
        ):
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category="aesthetic_lever_accounting",
                    message=(
                        f"{lever_id} route human_art_direction must cite "
                        "editorial_art_direction.human_art_direction_gate"
                    ),
                )
            ]
        if route == "human_art_direction" and "accept_simplification" in _text_blob(item).lower():
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category="aesthetic_lever_accounting",
                    message=(
                        "human_art_direction must not be hidden behind "
                        f"accept_simplification: {lever_id}"
                    ),
                )
            ]

    assessment = frontmatter.get("journal_grade_assessment")
    is_high_impact = (
        isinstance(assessment, dict)
        and assessment.get("benchmark_level") == "high_impact_candidate"
    )
    if is_high_impact:
        unresolved_required = [
            lever_id
            for lever_id, declared_item in declared.items()
            if declared_item.get("priority") == "required"
            and (
                item_by_id[lever_id].get("verdict") in {"fail", "needs_human"}
                or (
                    item_by_id[lever_id].get("verdict") == "weak"
                    and item_by_id[lever_id].get("route") != "none"
                )
            )
        ]
        if unresolved_required:
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category="aesthetic_lever_accounting",
                    message=(
                        "high_impact_candidate requires passing required aesthetic levers; "
                        "unresolved: " + ", ".join(sorted(unresolved_required))
                    ),
                )
            ]
    return []


def _aesthetic_intent_accounting_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    try:
        pack = load_optional_aesthetic_intent(example_dir)
    except AestheticIntentError as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="aesthetic_intent_accounting",
                message=f"aesthetic_intent.yaml invalid: {exc}",
            )
        ]
    if pack is None:
        return []
    lever_violations = _aesthetic_lever_accounting_violations(pack, frontmatter)
    if lever_violations:
        return lever_violations
    anchors = _aesthetic_intent_anchor_strings(pack)
    if not anchors:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="aesthetic_intent_accounting",
                message="aesthetic_intent.yaml produced no usable lint anchors",
            )
        ]

    missing: list[str] = []
    for section_name, slot_name in _AESTHETIC_INTENT_REQUIRED_SLOTS:
        raw_section = frontmatter.get(section_name)
        raw_slot = raw_section.get(slot_name) if isinstance(raw_section, dict) else None
        normalized_text = _text_blob(raw_slot).lower()
        if not _contains_anchor_with_current_artifact_evidence(normalized_text, anchors):
            missing.append(f"{section_name}.{slot_name}")
    if not missing:
        return []
    return [
        CritiqueLintViolation(
            severity="blocker",
            category="aesthetic_intent_accounting",
            message=(
                "aesthetic intent pack exists; critique slots must cite at least "
                "one exact aesthetic-intent anchor from target fields or item ids "
                "with current-artifact evidence: " + ", ".join(missing)
            ),
        )
    ]


# Canonical detector sources a grounded_in_rule may cite (mirrors the prefixes
# _candidate_ref_from_source recognizes). Referencing one anchors the finding to a
# real detector rather than generic best-practice prose.
_DETECTOR_SOURCE_ANCHORS: frozenset[str] = frozenset(
    {"visual_clash", "text_boundary", "label_path", "undeclared_geometry"}
)


def _grounding_anchor_set(example_dir: Path, spec: dict[str, Any]) -> set[str]:
    """Lowercased anchor strings a reference-free grounded_in_rule must cite one of:
    a briefing rule section marker (§N), a panel (panel <id>), or a detector source."""
    anchors: set[str] = set(_DETECTOR_SOURCE_ANCHORS)
    briefing_path = example_dir / "briefing.md"
    if briefing_path.is_file():
        sections = parse_briefing(briefing_path.read_text(encoding="utf-8"))
        rule_text = explicit_briefing_rule_text(sections)
        anchors.update(
            marker.replace(" ", "").lower() for marker in re.findall(r"§\s*\d+", rule_text)
        )
    panels = spec.get("panels")
    if isinstance(panels, list):
        for panel in panels:
            if isinstance(panel, dict):
                panel_id = panel.get("id")
                if isinstance(panel_id, str) and panel_id.strip():
                    label = panel_id.strip().lower()
                    anchors.add(f"panel {label}")
                    anchors.add(f"panel-{label}")
    return anchors


def _grounding_references_anchor(grounded_in_rule: str, anchors: set[str]) -> bool:
    text = grounded_in_rule.lower().replace(" ", "")
    # Compare against space-stripped anchors so "§ 3" and "panel b" match "§3"/"panelb".
    return any(anchor.replace(" ", "") in text for anchor in anchors)


def _reference_free_grounding_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    if not has_reference_free_grounding_context(example_dir):
        return []

    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        spec: dict[str, Any] = {}
    else:
        try:
            spec = parse_spec(spec_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category="reference_free_grounding",
                    message=f"spec.yaml invalid for reference-free grounding check: {exc}",
                )
            ]
    if declared_figure_reference_path(example_dir, spec) is not None:
        return []
    if participating_panel_reference_paths(example_dir, spec):
        return []

    try:
        findings = critique_findings(frontmatter)
    except CritiqueContractError as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="critique_contract",
                message=str(exc),
            )
        ]
    anchors = _grounding_anchor_set(example_dir, spec)
    missing: list[str] = []
    ungrounded: list[str] = []
    try:
        for index, finding in enumerate(findings):
            label = critique_finding_id(finding, f"finding[{index}]")
            grounded_in_rule = finding.get("grounded_in_rule")
            if not isinstance(grounded_in_rule, str) or not grounded_in_rule.strip():
                missing.append(label)
            elif not _grounding_references_anchor(grounded_in_rule, anchors):
                ungrounded.append(label)
    except CritiqueContractError as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="critique_contract",
                message=str(exc),
            )
        ]
    violations: list[CritiqueLintViolation] = []
    if missing:
        violations.append(
            CritiqueLintViolation(
                severity="blocker",
                category="reference_free_grounding",
                message=(
                    "reference-free critique findings must include grounded_in_rule "
                    "anchored to a briefing rule, panel_goal, or detector id: " + ", ".join(missing)
                ),
            )
        )
    if ungrounded:
        violations.append(
            CritiqueLintViolation(
                severity="blocker",
                category="reference_free_grounding",
                message=(
                    "reference-free grounded_in_rule must reference a real briefing rule "
                    "(§N), panel, or detector source (visual_clash / text_boundary / "
                    "label_path / undeclared_geometry), not generic prose: " + ", ".join(ungrounded)
                ),
            )
        )
    return violations


def _paper_context_anchor_strings(pack: dict[str, Any], fixture: str) -> set[str]:
    return {anchor.lower() for anchor in paper_context_anchors(pack, fixture) if anchor}


def _paper_aesthetic_context_accounting_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        return []
    try:
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))
        pack = load_optional_paper_aesthetic_context(example_dir, spec)
    except (PaperAestheticContextError, ValueError) as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="paper_aesthetic_context_accounting",
                message=f"paper_aesthetic_context invalid: {exc}",
            )
        ]
    if pack is None:
        return []
    anchors = _paper_context_anchor_strings(pack, example_dir.name)
    if not anchors:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="paper_aesthetic_context_accounting",
                message="paper_aesthetic_context produced no usable lint anchors",
            )
        ]

    missing: list[str] = []
    for section_name, slot_name in _PAPER_CONTEXT_REQUIRED_SLOTS:
        raw_section = frontmatter.get(section_name)
        raw_slot = raw_section.get(slot_name) if isinstance(raw_section, dict) else None
        normalized_text = _text_blob(raw_slot).lower()
        if not _contains_anchor_with_current_artifact_evidence(normalized_text, anchors):
            missing.append(f"{section_name}.{slot_name}")
    if not missing:
        return []
    return [
        CritiqueLintViolation(
            severity="blocker",
            category="paper_aesthetic_context_accounting",
            message=(
                "paper_aesthetic_context is declared; critique slots must cite at least "
                "one exact paper-wide anchor from paper id, target fields, role, shared "
                "language ids, or must-avoid ids with current-artifact evidence: "
                + ", ".join(missing)
            ),
        )
    ]


def _journal_playbook_anchor_strings(pack: dict[str, Any]) -> set[str]:
    return {anchor.lower() for anchor in journal_playbook_anchors(pack) if anchor}


def _id_set(pack: dict[str, Any], key: str) -> set[str]:
    return {
        item["id"]
        for item in pack.get(key, [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _journal_playbook_audit_violations(
    pack: dict[str, Any],
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    category = "journal_art_direction_playbook_accounting"
    raw_audit = frontmatter.get("journal_art_direction_playbook_audit")
    if not isinstance(raw_audit, dict):
        return [
            CritiqueLintViolation(
                severity="blocker",
                category=category,
                message="missing journal_art_direction_playbook_audit for declared playbook",
            )
        ]
    declared_design_ids = _id_set(pack, "design_center")
    positive_signal_ids = _id_set(pack, "positive_signals")
    anti_pattern_ids = _id_set(pack, "anti_patterns")
    route_rules = {
        item["id"]: item["recommended_path"]
        for item in pack.get("polish_route_rules", [])
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and isinstance(item.get("recommended_path"), str)
    }
    human_trigger_ids = _id_set(pack, "human_review_triggers")
    raw_design_items = raw_audit.get("design_center")
    if not isinstance(raw_design_items, list):
        return [
            CritiqueLintViolation(
                severity="blocker",
                category=category,
                message="journal_art_direction_playbook_audit.design_center must be a list",
            )
        ]
    audit_design_ids = {
        item.get("id")
        for item in raw_design_items
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    missing = sorted(declared_design_ids - audit_design_ids)
    unknown = sorted(audit_design_ids - declared_design_ids)
    if missing or unknown:
        details: list[str] = []
        if missing:
            details.append("missing design_center ids: " + ", ".join(missing))
        if unknown:
            details.append("unknown design_center ids: " + ", ".join(unknown))
        return [
            CritiqueLintViolation(
                severity="blocker",
                category=category,
                message="; ".join(details),
            )
        ]
    unknown_positive_refs: set[str] = set()
    unknown_anti_refs: set[str] = set()
    for item in raw_design_items:
        if not isinstance(item, dict):
            continue
        positive_refs = item.get("positive_signal_refs")
        if isinstance(positive_refs, list):
            unknown_positive_refs.update(
                ref
                for ref in positive_refs
                if isinstance(ref, str) and ref not in positive_signal_ids
            )
        anti_refs = item.get("anti_pattern_refs")
        if isinstance(anti_refs, list):
            unknown_anti_refs.update(
                ref for ref in anti_refs if isinstance(ref, str) and ref not in anti_pattern_ids
            )
    if unknown_positive_refs or unknown_anti_refs:
        details = []
        if unknown_positive_refs:
            details.append(
                "unknown positive_signal_refs: " + ", ".join(sorted(unknown_positive_refs))
            )
        if unknown_anti_refs:
            details.append("unknown anti_pattern_refs: " + ", ".join(sorted(unknown_anti_refs)))
        return [
            CritiqueLintViolation(
                severity="blocker",
                category=category,
                message="; ".join(details),
            )
        ]
    route_rule = raw_audit.get("route_rule_applied")
    if not isinstance(route_rule, dict):
        return [
            CritiqueLintViolation(
                severity="blocker",
                category=category,
                message="journal_art_direction_playbook_audit.route_rule_applied must be a mapping",
            )
        ]
    route_rule_id = route_rule.get("id")
    recommended_path = route_rule.get("recommended_path")
    if route_rule_id not in route_rules:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category=category,
                message=f"unknown route_rule_applied.id: {route_rule_id}",
            )
        ]
    if recommended_path != route_rules[route_rule_id]:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category=category,
                message=(
                    "route_rule_applied.recommended_path must match playbook rule "
                    f"{route_rule_id}: {route_rules[route_rule_id]}"
                ),
            )
        ]
    raw_triggers = raw_audit.get("human_review_triggers")
    if not isinstance(raw_triggers, list):
        return []
    unknown_triggers = sorted(
        item.get("id")
        for item in raw_triggers
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and item.get("id") not in human_trigger_ids
    )
    if unknown_triggers:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category=category,
                message="unknown human_review_triggers ids: " + ", ".join(unknown_triggers),
            )
        ]
    active_triggers = [
        item["id"]
        for item in raw_triggers
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item.get("active") is True
    ]
    if active_triggers:
        editorial = frontmatter.get("editorial_art_direction")
        gate = editorial.get("human_art_direction_gate") if isinstance(editorial, dict) else None
        gate_text = _text_blob(gate).lower()
        findings_text = _text_blob(frontmatter.get("findings")).lower()
        missing_gate_refs = [
            trigger
            for trigger in active_triggers
            if trigger.lower() not in gate_text and trigger.lower() not in findings_text
        ]
        if missing_gate_refs:
            return [
                CritiqueLintViolation(
                    severity="blocker",
                    category=category,
                    message=(
                        "active human_review_triggers must be visible in "
                        "editorial_art_direction.human_art_direction_gate or findings: "
                        + ", ".join(missing_gate_refs)
                    ),
                )
            ]
    return []


def _journal_art_direction_playbook_accounting_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        return []
    try:
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))
        pack = load_optional_journal_art_direction_playbook(example_dir, spec)
    except (JournalArtDirectionPlaybookError, ValueError) as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="journal_art_direction_playbook_accounting",
                message=f"journal_art_direction_playbook invalid: {exc}",
            )
        ]
    if pack is None:
        return []
    audit_violations = _journal_playbook_audit_violations(pack, frontmatter)
    if audit_violations:
        return audit_violations
    anchors = _journal_playbook_anchor_strings(pack)
    if not anchors:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="journal_art_direction_playbook_accounting",
                message="journal_art_direction_playbook produced no usable lint anchors",
            )
        ]
    missing: list[str] = []
    for section_name, slot_name in _JOURNAL_PLAYBOOK_REQUIRED_SLOTS:
        raw_section = frontmatter.get(section_name)
        raw_slot = raw_section.get(slot_name) if isinstance(raw_section, dict) else None
        normalized_text = _text_blob(raw_slot).lower()
        if not _contains_anchor_with_current_artifact_evidence(normalized_text, anchors):
            missing.append(f"{section_name}.{slot_name}")
    if not missing:
        return []
    return [
        CritiqueLintViolation(
            severity="blocker",
            category="journal_art_direction_playbook_accounting",
            message=(
                "journal_art_direction_playbook is declared; critique slots must cite "
                "at least one exact playbook anchor with current-artifact evidence: "
                + ", ".join(missing)
            ),
        )
    ]


def _audit_evidence_violations(frontmatter: dict[str, Any]) -> list[CritiqueLintViolation]:
    return [
        CritiqueLintViolation(
            severity="blocker",
            category=violation.category,
            message=violation.message,
        )
        for violation in critique_evidence_violations(frontmatter)
    ]


def _visual_clash_candidate_ids(report_path: Path) -> tuple[list[str], list[CritiqueLintViolation]]:
    if not report_path.is_file():
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accounting",
                message="missing build/visual_clash.json for visual_clash_ref validation",
            )
        ]
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accounting",
                message=f"malformed build/visual_clash.json: {exc}",
            )
        ]
    if not isinstance(report, dict):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accounting",
                message="malformed build/visual_clash.json: top-level value must be a mapping",
            )
        ]
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accounting",
                message="build/visual_clash.json candidates must be a list",
            )
        ]
    ids: list[str] = []
    violations: list[CritiqueLintViolation] = []
    seen: set[str] = set()
    for index, raw_candidate in enumerate(candidates):
        if not isinstance(raw_candidate, dict):
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="visual_clash_accounting",
                    message=f"build/visual_clash.json candidates[{index}] must be a mapping",
                )
            )
            continue
        candidate_id = raw_candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="visual_clash_accounting",
                    message=f"build/visual_clash.json candidates[{index}].id is required",
                )
            )
            continue
        candidate_id = candidate_id.strip()
        if candidate_id in seen:
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="visual_clash_accounting",
                    message=f"duplicate visual clash candidate id: {candidate_id}",
                )
            )
            continue
        seen.add(candidate_id)
        ids.append(candidate_id)
    return ids, violations


def _micro_defect_visual_clash_refs(frontmatter: dict[str, Any]) -> list[str]:
    raw_items = frontmatter.get("micro_defects")
    if not isinstance(raw_items, list):
        return []
    refs: list[str] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        value = raw_item.get("visual_clash_ref")
        if isinstance(value, str) and value.strip():
            refs.append(value.strip())
    return refs


def _visual_clash_accept_simplification_violations(
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    raw_items = frontmatter.get("micro_defects")
    if not isinstance(raw_items, list):
        return []
    violations: list[CritiqueLintViolation] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        visual_clash_ref = raw_item.get("visual_clash_ref")
        if (
            raw_item.get("status") != "accept_simplification"
            or not isinstance(visual_clash_ref, str)
            or not visual_clash_ref.strip()
        ):
            continue
        defect_id = raw_item.get("id")
        if frontmatter.get("schema") in STRUCTURED_ACCEPT_SIMPLIFICATION_SCHEMAS:
            reason = raw_item.get("accept_simplification_reason")
            rationale = raw_item.get("accept_simplification_rationale")
            if reason not in MICRO_DEFECT_ACCEPT_SIMPLIFICATION_REASONS:
                violations.append(
                    CritiqueLintViolation(
                        severity="blocker",
                        category="visual_clash_accept_simplification",
                        message=(
                            "visual-clash-linked accept_simplification requires "
                            "accept_simplification_reason with a supported enum value: "
                            f"{visual_clash_ref.strip()} ({defect_id})"
                        ),
                    )
                )
                continue
            if not isinstance(rationale, str) or not rationale.strip():
                violations.append(
                    CritiqueLintViolation(
                        severity="blocker",
                        category="visual_clash_accept_simplification",
                        message=(
                            "visual-clash-linked accept_simplification requires "
                            "accept_simplification_rationale: "
                            f"{visual_clash_ref.strip()} ({defect_id})"
                        ),
                    )
                )
                continue
            normalized_rationale = " ".join(rationale.split())
            lowered_rationale = normalized_rationale.lower()
            has_concrete_length = (
                len(normalized_rationale) >= _STRUCTURED_ACCEPT_MIN_RATIONALE_CHARS
            )
            names_candidate = visual_clash_ref.strip() in normalized_rationale
            gives_non_defect_reason = any(
                marker in lowered_rationale for marker in _VISUAL_CLASH_ACCEPT_RATIONALE_MARKERS
            )
            if has_concrete_length and names_candidate and gives_non_defect_reason:
                continue
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="visual_clash_accept_simplification",
                    message=(
                        "visual-clash-linked accept_simplification_rationale must be "
                        "concrete, name the candidate id, and explain the non-defect "
                        f"geometry/context: {visual_clash_ref.strip()} ({defect_id})"
                    ),
                )
            )
            continue
        observation = raw_item.get("observation")
        if not isinstance(observation, str):
            observation = ""
        normalized_observation = " ".join(observation.split())
        rationale = normalized_observation.lower()
        has_concrete_length = (
            len(normalized_observation) >= _VISUAL_CLASH_ACCEPT_MIN_OBSERVATION_CHARS
        )
        names_candidate = visual_clash_ref.strip() in normalized_observation
        gives_non_defect_reason = any(
            marker in rationale for marker in _VISUAL_CLASH_ACCEPT_RATIONALE_MARKERS
        )
        if has_concrete_length and names_candidate and gives_non_defect_reason:
            continue
        violations.append(
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accept_simplification",
                message=(
                    "visual-clash-linked accept_simplification requires a concrete "
                    "observation naming the candidate id and explaining why it is "
                    f"not a defect: {visual_clash_ref.strip()} ({defect_id})"
                ),
            )
        )
    return violations


def _visual_clash_accounting_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    if frontmatter.get("schema") not in VISUAL_CLASH_ACCOUNTING_SCHEMAS:
        return []
    candidate_ids, violations = _visual_clash_candidate_ids(
        example_dir / "build" / "visual_clash.json"
    )
    if violations or not candidate_ids:
        return violations
    refs = _micro_defect_visual_clash_refs(frontmatter)
    accounted = set(refs)
    duplicate_refs = sorted({ref for ref in refs if refs.count(ref) > 1})
    if duplicate_refs:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accounting",
                message=f"duplicate visual_clash_ref entries: {', '.join(duplicate_refs)}",
            )
        ]
    candidate_id_set = set(candidate_ids)
    unknown_refs = sorted(ref for ref in accounted if ref not in candidate_id_set)
    if unknown_refs:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="visual_clash_accounting",
                message=f"unknown visual_clash_ref entries: {', '.join(unknown_refs)}",
            )
        ]
    missing = [candidate_id for candidate_id in candidate_ids if candidate_id not in accounted]
    if not missing:
        return _visual_clash_accept_simplification_violations(frontmatter)
    return [
        CritiqueLintViolation(
            severity="blocker",
            category="visual_clash_accounting",
            message=(
                "visual_clash.json candidates must be referenced by "
                f"micro_defects[].visual_clash_ref; missing: {', '.join(missing)}"
            ),
        )
    ]


def _text_boundary_candidate_ids(
    report_path: Path,
) -> tuple[list[str], list[CritiqueLintViolation]]:
    if not report_path.is_file():
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="text_boundary_accounting",
                message="missing build/text_boundary_clash.json for text_boundary_ref validation",
            )
        ]
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="text_boundary_accounting",
                message=f"malformed build/text_boundary_clash.json: {exc}",
            )
        ]
    if not isinstance(report, dict):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="text_boundary_accounting",
                message=(
                    "malformed build/text_boundary_clash.json: top-level value must be a mapping"
                ),
            )
        ]
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="text_boundary_accounting",
                message="build/text_boundary_clash.json candidates must be a list",
            )
        ]
    ids: list[str] = []
    violations: list[CritiqueLintViolation] = []
    seen: set[str] = set()
    for index, raw_candidate in enumerate(candidates):
        if not isinstance(raw_candidate, dict):
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="text_boundary_accounting",
                    message=f"build/text_boundary_clash.json candidates[{index}] must be a mapping",
                )
            )
            continue
        candidate_id = raw_candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="text_boundary_accounting",
                    message=f"build/text_boundary_clash.json candidates[{index}].id is required",
                )
            )
            continue
        candidate_id = candidate_id.strip()
        if candidate_id in seen:
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="text_boundary_accounting",
                    message=f"duplicate text boundary candidate id: {candidate_id}",
                )
            )
            continue
        seen.add(candidate_id)
        ids.append(candidate_id)
    return ids, violations


def _micro_defect_text_boundary_refs(frontmatter: dict[str, Any]) -> list[str]:
    raw_items = frontmatter.get("micro_defects")
    if not isinstance(raw_items, list):
        return []
    refs: list[str] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        value = raw_item.get("text_boundary_ref")
        if isinstance(value, str) and value.strip():
            refs.append(value.strip())
    return refs


def _text_boundary_accounting_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    if frontmatter.get("schema") not in TEXT_BOUNDARY_ACCOUNTING_SCHEMAS:
        return []
    candidate_ids, violations = _text_boundary_candidate_ids(
        example_dir / "build" / "text_boundary_clash.json"
    )
    if violations or not candidate_ids:
        return violations
    refs = _micro_defect_text_boundary_refs(frontmatter)
    accounted = set(refs)
    duplicate_refs = sorted({ref for ref in refs if refs.count(ref) > 1})
    if duplicate_refs:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="text_boundary_accounting",
                message=f"duplicate text_boundary_ref entries: {', '.join(duplicate_refs)}",
            )
        ]
    candidate_id_set = set(candidate_ids)
    unknown_refs = sorted(ref for ref in accounted if ref not in candidate_id_set)
    if unknown_refs:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="text_boundary_accounting",
                message=f"unknown text_boundary_ref entries: {', '.join(unknown_refs)}",
            )
        ]
    missing = [candidate_id for candidate_id in candidate_ids if candidate_id not in accounted]
    if not missing:
        return []
    return [
        CritiqueLintViolation(
            severity="blocker",
            category="text_boundary_accounting",
            message=(
                "text_boundary_clash.json candidates must be referenced by "
                f"micro_defects[].text_boundary_ref; missing: {', '.join(missing)}"
            ),
        )
    ]


def _label_path_candidate_ids(
    report_path: Path,
) -> tuple[list[str], list[CritiqueLintViolation]]:
    if not report_path.is_file():
        return [], []
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="label_path_accounting",
                message=f"malformed build/label_path_proximity.json: {exc}",
            )
        ]
    if not isinstance(report, dict):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="label_path_accounting",
                message=(
                    "malformed build/label_path_proximity.json: top-level value must be a mapping"
                ),
            )
        ]
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="label_path_accounting",
                message="build/label_path_proximity.json candidates must be a list",
            )
        ]
    ids: list[str] = []
    violations: list[CritiqueLintViolation] = []
    seen: set[str] = set()
    for index, raw_candidate in enumerate(candidates):
        if not isinstance(raw_candidate, dict):
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="label_path_accounting",
                    message=(
                        f"build/label_path_proximity.json candidates[{index}] must be a mapping"
                    ),
                )
            )
            continue
        candidate_id = raw_candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="label_path_accounting",
                    message=(f"build/label_path_proximity.json candidates[{index}].id is required"),
                )
            )
            continue
        candidate_id = candidate_id.strip()
        if candidate_id in seen:
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="label_path_accounting",
                    message=f"duplicate label path candidate id: {candidate_id}",
                )
            )
            continue
        seen.add(candidate_id)
        ids.append(candidate_id)
    return ids, violations


def _micro_defect_label_path_refs(frontmatter: dict[str, Any]) -> list[str]:
    raw_items = frontmatter.get("micro_defects")
    if not isinstance(raw_items, list):
        return []
    refs: list[str] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        value = raw_item.get("label_path_ref")
        if isinstance(value, str) and value.strip():
            refs.append(value.strip())
    return refs


def _label_path_accounting_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    if frontmatter.get("schema") not in LABEL_PATH_ACCOUNTING_SCHEMAS:
        return []
    candidate_ids, violations = _label_path_candidate_ids(
        example_dir / "build" / "label_path_proximity.json"
    )
    if violations or not candidate_ids:
        return violations
    refs = _micro_defect_label_path_refs(frontmatter)
    accounted = set(refs)
    duplicate_refs = sorted({ref for ref in refs if refs.count(ref) > 1})
    if duplicate_refs:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="label_path_accounting",
                message=f"duplicate label_path_ref entries: {', '.join(duplicate_refs)}",
            )
        ]
    candidate_id_set = set(candidate_ids)
    unknown_refs = sorted(ref for ref in accounted if ref not in candidate_id_set)
    if unknown_refs:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="label_path_accounting",
                message=f"unknown label_path_ref entries: {', '.join(unknown_refs)}",
            )
        ]
    missing = [candidate_id for candidate_id in candidate_ids if candidate_id not in accounted]
    if not missing:
        return []
    return [
        CritiqueLintViolation(
            severity="blocker",
            category="label_path_accounting",
            message=(
                "label_path_proximity.json candidates must be referenced by "
                f"micro_defects[].label_path_ref; missing: {', '.join(missing)}"
            ),
        )
    ]


def _undeclared_geometry_candidate_ids(
    report_path: Path,
) -> tuple[list[str], list[CritiqueLintViolation]]:
    if not report_path.is_file():
        return [], []
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="undeclared_geometry_accounting",
                message=f"malformed build/undeclared_geometry.json: {exc}",
            )
        ]
    if not isinstance(report, dict):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="undeclared_geometry_accounting",
                message=(
                    "malformed build/undeclared_geometry.json: top-level value must be a mapping"
                ),
            )
        ]
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="undeclared_geometry_accounting",
                message="build/undeclared_geometry.json candidates must be a list",
            )
        ]
    ids: list[str] = []
    violations: list[CritiqueLintViolation] = []
    seen: set[str] = set()
    for index, raw_candidate in enumerate(candidates):
        if not isinstance(raw_candidate, dict):
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="undeclared_geometry_accounting",
                    message=(
                        f"build/undeclared_geometry.json candidates[{index}] must be a mapping"
                    ),
                )
            )
            continue
        candidate_id = raw_candidate.get("id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="undeclared_geometry_accounting",
                    message=(f"build/undeclared_geometry.json candidates[{index}].id is required"),
                )
            )
            continue
        candidate_id = candidate_id.strip()
        if candidate_id in seen:
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="undeclared_geometry_accounting",
                    message=f"duplicate undeclared geometry candidate id: {candidate_id}",
                )
            )
            continue
        seen.add(candidate_id)
        ids.append(candidate_id)
    return ids, violations


def _micro_defect_undeclared_geometry_refs(frontmatter: dict[str, Any]) -> list[str]:
    raw_items = frontmatter.get("micro_defects")
    if not isinstance(raw_items, list):
        return []
    refs: list[str] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        value = raw_item.get("undeclared_geometry_ref")
        if isinstance(value, str) and value.strip():
            refs.append(value.strip())
    return refs


def _undeclared_geometry_accounting_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    if frontmatter.get("schema") not in UNDECLARED_GEOMETRY_ACCOUNTING_SCHEMAS:
        return []
    candidate_ids, violations = _undeclared_geometry_candidate_ids(
        example_dir / "build" / "undeclared_geometry.json"
    )
    if violations or not candidate_ids:
        return violations
    refs = _micro_defect_undeclared_geometry_refs(frontmatter)
    accounted = set(refs)
    duplicate_refs = sorted({ref for ref in refs if refs.count(ref) > 1})
    if duplicate_refs:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="undeclared_geometry_accounting",
                message=f"duplicate undeclared_geometry_ref entries: {', '.join(duplicate_refs)}",
            )
        ]
    candidate_id_set = set(candidate_ids)
    unknown_refs = sorted(ref for ref in accounted if ref not in candidate_id_set)
    if unknown_refs:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="undeclared_geometry_accounting",
                message=f"unknown undeclared_geometry_ref entries: {', '.join(unknown_refs)}",
            )
        ]
    missing = [candidate_id for candidate_id in candidate_ids if candidate_id not in accounted]
    if not missing:
        return []
    return [
        CritiqueLintViolation(
            severity="blocker",
            category="undeclared_geometry_accounting",
            message=(
                "undeclared_geometry.json candidates must be referenced by "
                f"micro_defects[].undeclared_geometry_ref; missing: {', '.join(missing)}"
            ),
        )
    ]


def _micro_defects_by_visual_clash_ref(frontmatter: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_items = frontmatter.get("micro_defects")
    if not isinstance(raw_items, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        visual_clash_ref = raw_item.get("visual_clash_ref")
        if isinstance(visual_clash_ref, str) and visual_clash_ref.strip():
            result[visual_clash_ref.strip()] = raw_item
    return result


def _historical_visual_clash_regression_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    if frontmatter.get("schema") not in VISUAL_CLASH_ACCOUNTING_SCHEMAS:
        return []
    report_path = example_dir / "build" / "visual_clash.json"
    if not report_path.is_file():
        return []
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(report, dict):
        return []
    fixture = report.get("fixture")
    if (
        example_dir.name != _HISTORICAL_VISUAL_CLASH_FIXTURE
        and fixture != _HISTORICAL_VISUAL_CLASH_FIXTURE
    ):
        return []
    candidates = report.get("candidates")
    if not isinstance(candidates, list):
        return []
    defects_by_ref = _micro_defects_by_visual_clash_ref(frontmatter)
    violations: list[CritiqueLintViolation] = []
    for raw_candidate in candidates:
        if not isinstance(raw_candidate, dict):
            continue
        candidate_id = raw_candidate.get("id")
        text = raw_candidate.get("text")
        if not isinstance(candidate_id, str) or not isinstance(text, str):
            continue
        expected_kind = _HISTORICAL_VISUAL_CLASH_EXPECTED_KINDS.get(
            (candidate_id.strip(), text.strip())
        )
        if expected_kind is None:
            continue
        defect = defects_by_ref.get(candidate_id.strip())
        if defect is None:
            continue
        if defect.get("kind") == expected_kind:
            continue
        violations.append(
            CritiqueLintViolation(
                severity="blocker",
                category="historical_visual_clash_regression",
                message=(
                    f"{_HISTORICAL_VISUAL_CLASH_FIXTURE} candidate {candidate_id.strip()} "
                    f"({text.strip()}) must use micro_defects[].kind={expected_kind}"
                ),
            )
        )
    return violations


def _normalize_tex_symbol_text(value: str) -> str:
    text = _TEX_TEXT_COMMAND_RE.sub(r"\1", value)
    text = text.replace("$", "")
    text = text.replace("{", "").replace("}", "")
    text = text.replace("\\", "")
    return text


def _symbolic_entities(value: str) -> set[str]:
    normalized = _normalize_tex_symbol_text(value)
    return {match.group(0) for match in _SYMBOLIC_ENTITY_RE.finditer(normalized)}


def _active_and_comment_tex_text(tex_path: Path) -> tuple[str, str]:
    active_lines: list[str] = []
    comment_lines: list[str] = []
    try:
        tex_text = tex_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise CritiqueContractError(f"invalid UTF-8 in {tex_path}: {exc}") from exc
    for line in tex_text.splitlines():
        match = _UNESCAPED_PERCENT_RE.search(line)
        if match is None:
            active_lines.append(line)
            continue
        active_lines.append(line[: match.start()])
        comment_lines.append(line[match.end() :])
    return (
        _normalize_tex_symbol_text("\n".join(active_lines)),
        _normalize_tex_symbol_text("\n".join(comment_lines)),
    )


def _critique_entity_consistency_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    tex_path = example_dir / f"{example_dir.name}.tex"
    if not tex_path.is_file():
        return []
    audit = frontmatter.get("audit_enumeration")
    label_matches = audit.get("label_target_matching") if isinstance(audit, dict) else None
    if not isinstance(label_matches, list):
        return []

    active_text, comment_text = _active_and_comment_tex_text(tex_path)
    active_entities = _symbolic_entities(active_text)
    comment_entities = _symbolic_entities(comment_text)
    violations: list[CritiqueLintViolation] = []
    for index, item in enumerate(label_matches):
        if not isinstance(item, dict) or item.get("matches") is not True:
            continue
        label = item.get("label")
        if not isinstance(label, str):
            continue
        for entity in sorted(_symbolic_entities(label)):
            if entity in active_entities:
                continue
            state = "comment-only" if entity in comment_entities else "absent"
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="critique_entity_consistency",
                    message=(
                        "label_target_matching "
                        f"entry {index} entity {entity} is {state} in active TeX source"
                    ),
                )
            )
    return violations


def _crop_manifest_required_ids(
    example_dir: Path,
    manifest_path: Path,
) -> tuple[list[str], list[CritiqueLintViolation]]:
    if not manifest_path.is_file():
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message="missing build/audit_crops/manifest.json for crop_audit_log validation",
            )
        ]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message=f"malformed build/audit_crops/manifest.json: {exc}",
            )
        ]
    if not isinstance(manifest, dict):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message=(
                    "malformed build/audit_crops/manifest.json: top-level value must be a mapping"
                ),
            )
        ]
    required = manifest.get("required_crop_ids")
    if not isinstance(required, list):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message="build/audit_crops/manifest.json required_crop_ids must be a list",
            )
        ]
    ids: list[str] = []
    for index, crop_id in enumerate(required):
        if not isinstance(crop_id, str) or not crop_id.strip():
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=(
                        "build/audit_crops/manifest.json "
                        f"required_crop_ids[{index}] must be a non-empty string"
                    ),
                )
            ]
        ids.append(crop_id.strip())
    crops = manifest.get("crops")
    if not isinstance(crops, list):
        return [], [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message="build/audit_crops/manifest.json crops must be a list",
            )
        ]
    crop_by_id = {
        crop.get("id").strip(): crop
        for crop in crops
        if isinstance(crop, dict) and isinstance(crop.get("id"), str) and crop.get("id").strip()
    }
    for crop_id in ids:
        crop = crop_by_id.get(crop_id)
        if crop is None:
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=f"required crop id missing from manifest crops: {crop_id}",
                )
            ]
        expected_hash = crop.get("sha256")
        if (
            not isinstance(expected_hash, str)
            or not expected_hash.startswith("sha256:")
            or len(expected_hash) != len("sha256:") + 64
        ):
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=f"manifest crop {crop_id} must include sha256:<64 hex chars>",
                )
            ]
        hash_suffix = expected_hash.removeprefix("sha256:")
        if hash_suffix.lower() != hash_suffix or any(
            char not in "0123456789abcdef" for char in hash_suffix
        ):
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=f"manifest crop {crop_id} must use lowercase sha256 hex",
                )
            ]
        crop_path = crop.get("path")
        relative_crop_path = Path(crop_path) if isinstance(crop_path, str) else None
        if (
            relative_crop_path is None
            or relative_crop_path.is_absolute()
            or ".." in relative_crop_path.parts
            or relative_crop_path.parts[:2] != ("build", "audit_crops")
            or relative_crop_path.suffix != ".png"
        ):
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=f"manifest crop {crop_id} path must point to build/audit_crops/*.png",
                )
            ]
        absolute_crop_path = example_dir / relative_crop_path
        if not absolute_crop_path.is_file():
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=f"missing crop file for manifest crop {crop_id}: {crop_path}",
                )
            ]
        actual_hash = file_sha256(absolute_crop_path)
        if actual_hash != expected_hash:
            return [], [
                CritiqueLintViolation(
                    severity="blocker",
                    category="crop_audit_accounting",
                    message=f"hash mismatch for manifest crop {crop_id}: {crop_path}",
                )
            ]
    return ids, []


def _crop_audit_log_items(frontmatter: dict[str, Any]) -> list[dict[str, Any]]:
    raw_items = frontmatter.get("crop_audit_log")
    if not isinstance(raw_items, list):
        return []
    return [item for item in raw_items if isinstance(item, dict)]


def _crop_audit_accounting_violations(
    example_dir: Path,
    frontmatter: dict[str, Any],
) -> list[CritiqueLintViolation]:
    if frontmatter.get("schema") not in CROP_AUDIT_ACCOUNTING_SCHEMAS:
        return []
    required_ids, violations = _crop_manifest_required_ids(
        example_dir, example_dir / "build" / "audit_crops" / "manifest.json"
    )
    if violations or not required_ids:
        return violations

    items = _crop_audit_log_items(frontmatter)
    crop_ids = [
        item["crop_id"].strip()
        for item in items
        if isinstance(item.get("crop_id"), str) and item["crop_id"].strip()
    ]
    duplicate_ids = sorted({crop_id for crop_id in crop_ids if crop_ids.count(crop_id) > 1})
    if duplicate_ids:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message=f"duplicate crop_audit_log crop_id entries: {', '.join(duplicate_ids)}",
            )
        ]
    required_set = set(required_ids)
    unknown_ids = sorted(crop_id for crop_id in crop_ids if crop_id not in required_set)
    if unknown_ids:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message=f"unknown crop_audit_log crop_id entries: {', '.join(unknown_ids)}",
            )
        ]
    missing = [crop_id for crop_id in required_ids if crop_id not in crop_ids]
    if missing:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message=f"missing required crop_audit_log entries: {', '.join(missing)}",
            )
        ]

    micro_defect_ids = {
        item.get("id")
        for item in frontmatter.get("micro_defects", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    unlinked_defect_crops = [
        str(item.get("crop_id"))
        for item in items
        if item.get("verdict") == "defect"
        and item.get("linked_micro_defect_id") not in micro_defect_ids
    ]
    if unlinked_defect_crops:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="crop_audit_accounting",
                message=(
                    "defect crop_audit_log entries must link to micro_defects[].id: "
                    + ", ".join(unlinked_defect_crops)
                ),
            )
        ]
    return []


def _external_vision_review_violations(example_dir: Path) -> list[CritiqueLintViolation]:
    spec_path = example_dir / "spec.yaml"
    if not spec_path.is_file():
        return []
    try:
        spec = parse_spec(spec_path.read_text(encoding="utf-8"))
        review = load_optional_external_vision_review(example_dir, spec)
    except (ExternalVisionReviewError, ValueError) as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="external_vision_review",
                message=f"external_vision_review invalid: {exc}",
            )
        ]
    if review is None:
        return []

    freshness = external_vision_review_freshness(example_dir, review)
    if freshness["state"] == "fresh":
        return []
    return [
        CritiqueLintViolation(
            severity="blocker",
            category="external_vision_review",
            message=(
                f"external_vision_review is {freshness['state']}; "
                f"stale_paths={freshness['stale_paths']} "
                f"missing_paths={freshness['missing_paths']}"
            ),
        )
    ]


def _inspection_trace_violations(example_dir: Path) -> list[CritiqueLintViolation]:
    try:
        load_optional_inspection_trace(example_dir)
    except InspectionTraceError as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="inspection_trace",
                message=f"inspection_trace invalid: {exc}",
            )
        ]
    return []


def lint_critique(example_dir: Path) -> list[CritiqueLintViolation]:
    critique_path = example_dir / "critique.md"
    try:
        frontmatter = load_critique_frontmatter(critique_path)
    except CritiqueContractError as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="critique_frontmatter",
                message=str(exc),
            )
        ]

    try:
        violations = _duplicate_finding_id_violations(frontmatter)
    except CritiqueContractError as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="critique_contract",
                message=str(exc),
            )
        ]
    if violations:
        return violations

    violations.extend(_external_vision_review_violations(example_dir))
    if violations:
        return violations
    violations.extend(_inspection_trace_violations(example_dir))
    if violations:
        return violations

    violations.extend(_aesthetic_intent_accounting_violations(example_dir, frontmatter))
    if violations:
        return violations
    violations.extend(_reference_free_grounding_violations(example_dir, frontmatter))
    if violations:
        return violations
    violations.extend(_paper_aesthetic_context_accounting_violations(example_dir, frontmatter))
    if violations:
        return violations
    violations.extend(
        _journal_art_direction_playbook_accounting_violations(example_dir, frontmatter)
    )
    if violations:
        return violations
    if frontmatter.get("schema") in STRUCTURED_ACCEPT_SIMPLIFICATION_SCHEMAS:
        violations.extend(_visual_clash_accept_simplification_violations(frontmatter))
    if violations:
        return violations
    try:
        violations.extend(_critique_entity_consistency_violations(example_dir, frontmatter))
    except CritiqueContractError as exc:
        return [
            CritiqueLintViolation(
                severity="blocker",
                category="critique_contract",
                message=str(exc),
            )
        ]
    if violations:
        return violations

    try:
        build_adjudication_scaffold(example_dir)
    except CritiqueAdjudicationError as exc:
        evidence_violations = _audit_evidence_violations(frontmatter)
        if evidence_violations and "print-scale audit evidence" in str(exc):
            violations.extend(evidence_violations)
        else:
            violations.append(
                CritiqueLintViolation(
                    severity="blocker",
                    category="critique_contract",
                    message=str(exc),
                )
            )
    if violations:
        return violations
    violations.extend(_audit_evidence_violations(frontmatter))
    violations.extend(_visual_clash_accounting_violations(example_dir, frontmatter))
    if violations:
        return violations
    violations.extend(_text_boundary_accounting_violations(example_dir, frontmatter))
    if violations:
        return violations
    violations.extend(_label_path_accounting_violations(example_dir, frontmatter))
    if violations:
        return violations
    violations.extend(_undeclared_geometry_accounting_violations(example_dir, frontmatter))
    if violations:
        return violations
    violations.extend(_historical_visual_clash_regression_violations(example_dir, frontmatter))
    violations.extend(_crop_audit_accounting_violations(example_dir, frontmatter))
    return violations


def _resolve_example_dir(value: str, repo_root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "examples":
        if len(path.parts) != 2 or ".." in path.parts:
            raise CritiqueContractError("invalid fixture path: expected examples/<fixture-name>")
        _validate_fixture_name(path.parts[1], value)
        return repo_root / "examples" / path.parts[1]
    if len(path.parts) == 1:
        _validate_fixture_name(value, value)
        return repo_root / "examples" / value
    raise CritiqueContractError(
        "invalid fixture path: expected fixture name, examples/<fixture-name>, or an absolute path"
    )


def _validate_fixture_name(name: str, original: str) -> None:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise CritiqueContractError(f"invalid fixture path: {original}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example", help="fixture name, examples/<name>, or path")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    try:
        example_dir = _resolve_example_dir(args.example, args.repo_root)
    except CritiqueContractError as exc:
        print(f"BLOCKER: critique_contract: {exc}")
        return 1
    violations = lint_critique(example_dir)
    if not violations:
        print(f"OK: critique lint passed for {example_dir.name}")
        return 0
    for violation in violations:
        print(f"{violation.severity.upper()}: {violation.category}: {violation.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
