from __future__ import annotations

import sys
import warnings
from copy import deepcopy
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import critique_schema_vocab as vocab  # noqa: E402
from critique_contract import CritiqueContractError  # noqa: E402
from critique_schema_validator import validate_critique_schema  # noqa: E402


def test_validate_critique_schema_warns_for_v1_legacy() -> None:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        validate_critique_schema({"schema": vocab.CRITIQUE_SCHEMA_V1})

    assert len(captured) == 1
    assert captured[0].category is DeprecationWarning
    assert vocab.CRITIQUE_SCHEMA_V1 in str(captured[0].message)


def test_validate_critique_schema_rejects_future_unsupported_schema() -> None:
    with pytest.raises(CritiqueContractError, match="unsupported critique schema"):
        validate_critique_schema({"schema": "figure-agent.critique.v99"})


QUALITY_AXIS_NAMES = (
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

TOP_TIER_AUDIT_KEYS = (
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

EDITORIAL_AUDIT_KEYS = (
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


def _quality_axis(axis_name: str) -> dict:
    axis = {
        "verdict": "pass",
        "confidence": "high",
        "rationale": f"{axis_name} passes",
        "evidence": f"{axis_name} evidence",
        "blocking_items": [],
        "recommended_action": "none",
    }
    if axis_name == "panel_role_coherence":
        axis["panel_roles"] = [
            {
                "panel_id": "A",
                "role": "setup",
                "role_quality": "clear",
                "rationale": "panel A introduces the figure",
            }
        ]
    return axis


def _editorial_audit_slot(slot_name: str) -> dict:
    slot = {
        "verdict": "pass",
        "evidence": f"{slot_name} visual evidence",
        "rationale": f"{slot_name} supports the editorial target",
        "concrete_fix": "accept_simplification: current artifact is intentional",
        "blocks_high_impact": False,
    }
    if slot_name == "tikz_vs_svg_polish_trigger":
        slot["recommended_path"] = "continue_tikz"
    return slot


def _valid_frontmatter(schema: str = vocab.CRITIQUE_SCHEMA_V1_4) -> dict:
    frontmatter = {
        "schema": schema,
        "audit_enumeration": {
            "structural_completeness": {
                "components": [{"component": "apparatus"}],
                "missing_from_reference": [{"element": "stage"}],
            },
            "label_target_matching": [{"label": "trap"}],
            "physical_plausibility": [{"check": "floating_components"}],
            "conceptual_completeness": [
                {"element": "stage", "reference": "briefing"},
            ],
        },
        "quality_axes": {axis_name: _quality_axis(axis_name) for axis_name in QUALITY_AXIS_NAMES},
        "top_tier_audit": {
            key: {
                "verdict": "pass",
                "finding": f"{key} passes",
                "concrete_fix": "accept_simplification",
                "blocks_high_impact": False,
            }
            for key in TOP_TIER_AUDIT_KEYS
        },
        "findings": [
            {
                "id": "C001",
                "status": "open",
                "observation": "wire_crosses_label from high-zoom crop",
            }
        ],
    }
    if schema in {vocab.CRITIQUE_SCHEMA_V1_4, "figure-agent.critique.v1.5"}:
        frontmatter["micro_defects"] = [
            {
                "id": "M001",
                "crop": "examples/demo_fig/build/audit_crops/full_q1.png",
                "kind": "wire_crosses_label",
                "severity": "MAJOR",
                "observation": "wire crosses the label in the crop",
                "linked_finding_id": "C001",
                "status": "open",
            }
        ]
    if schema == "figure-agent.critique.v1.5":
        frontmatter["editorial_art_direction"] = {
            key: _editorial_audit_slot(key) for key in EDITORIAL_AUDIT_KEYS
        }
    return frontmatter


def test_validate_critique_schema_accepts_v1_3_without_micro_defects() -> None:
    validate_critique_schema(_valid_frontmatter(vocab.CRITIQUE_SCHEMA_V1_3))


def test_validate_critique_schema_accepts_v1_4_micro_defects() -> None:
    validate_critique_schema(_valid_frontmatter())


def test_validate_critique_schema_rejects_v1_4_missing_micro_defects() -> None:
    frontmatter = _valid_frontmatter()
    frontmatter.pop("micro_defects")

    with pytest.raises(CritiqueContractError, match="micro_defects"):
        validate_critique_schema(frontmatter)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("kind", "vague", "kind"),
        ("severity", "CRITICAL", "severity"),
        ("status", "ignored", "status"),
        ("id", "", "id"),
        ("crop", "", "crop"),
        ("observation", "", "observation"),
    ),
)
def test_validate_critique_schema_rejects_malformed_v1_4_micro_defect_fields(
    field: str,
    value: str,
    message: str,
) -> None:
    frontmatter = _valid_frontmatter()
    frontmatter["micro_defects"][0][field] = value

    with pytest.raises(CritiqueContractError, match=message):
        validate_critique_schema(frontmatter)


def test_validate_critique_schema_rejects_v1_4_bad_micro_defect_crop_path() -> None:
    frontmatter = _valid_frontmatter()
    frontmatter["micro_defects"][0]["crop"] = "screenshots/full_q1.png"

    with pytest.raises(CritiqueContractError, match="audit_crops"):
        validate_critique_schema(frontmatter)


def test_validate_critique_schema_rejects_v1_4_major_micro_defect_bad_link() -> None:
    frontmatter = _valid_frontmatter()
    frontmatter["micro_defects"][0]["linked_finding_id"] = "C999"

    with pytest.raises(CritiqueContractError, match="linked_finding_id"):
        validate_critique_schema(frontmatter)


def test_validate_critique_schema_accepts_v1_4_major_micro_defect_simplification() -> None:
    frontmatter = _valid_frontmatter()
    frontmatter["micro_defects"][0]["linked_finding_id"] = ""
    frontmatter["micro_defects"][0]["status"] = "accept_simplification"
    frontmatter["findings"] = []

    validate_critique_schema(frontmatter)


@pytest.mark.parametrize("severity", ["MINOR", "NIT"])
def test_validate_critique_schema_accepts_v1_4_low_severity_micro_defect_without_link(
    severity: str,
) -> None:
    frontmatter = _valid_frontmatter()
    frontmatter["micro_defects"][0]["severity"] = severity
    frontmatter["micro_defects"][0]["linked_finding_id"] = ""
    frontmatter["findings"] = []

    validate_critique_schema(frontmatter)


def test_validate_critique_schema_accepts_v1_4_empty_micro_defect_list() -> None:
    frontmatter = deepcopy(_valid_frontmatter())
    frontmatter["micro_defects"] = []
    frontmatter["findings"] = []

    validate_critique_schema(frontmatter)


def test_validate_critique_schema_accepts_v1_5_editorial_art_direction() -> None:
    validate_critique_schema(_valid_frontmatter("figure-agent.critique.v1.5"))


def test_validate_critique_schema_rejects_v1_5_missing_editorial_art_direction() -> None:
    frontmatter = _valid_frontmatter("figure-agent.critique.v1.5")
    frontmatter.pop("editorial_art_direction")

    with pytest.raises(CritiqueContractError, match="editorial_art_direction"):
        validate_critique_schema(frontmatter)


def test_validate_critique_schema_rejects_v1_5_invalid_editorial_verdict() -> None:
    frontmatter = _valid_frontmatter("figure-agent.critique.v1.5")
    frontmatter["editorial_art_direction"]["hero_focus"]["verdict"] = "excellent"

    with pytest.raises(CritiqueContractError, match="hero_focus.verdict"):
        validate_critique_schema(frontmatter)


def test_validate_critique_schema_rejects_v1_5_empty_editorial_evidence() -> None:
    frontmatter = _valid_frontmatter("figure-agent.critique.v1.5")
    frontmatter["editorial_art_direction"]["hero_focus"]["evidence"] = ""

    with pytest.raises(CritiqueContractError, match="hero_focus.evidence"):
        validate_critique_schema(frontmatter)


def test_validate_critique_schema_rejects_v1_5_non_boolean_blocks_high_impact() -> None:
    frontmatter = _valid_frontmatter("figure-agent.critique.v1.5")
    frontmatter["editorial_art_direction"]["hero_focus"]["blocks_high_impact"] = "false"

    with pytest.raises(CritiqueContractError, match="hero_focus.blocks_high_impact"):
        validate_critique_schema(frontmatter)


def test_validate_critique_schema_rejects_v1_5_invalid_polish_recommended_path() -> None:
    frontmatter = _valid_frontmatter("figure-agent.critique.v1.5")
    frontmatter["editorial_art_direction"]["tikz_vs_svg_polish_trigger"][
        "recommended_path"
    ] = "guess_from_prose"

    with pytest.raises(CritiqueContractError, match="recommended_path"):
        validate_critique_schema(frontmatter)


def test_validate_critique_schema_rejects_v1_5_needs_human_accept_simplification_bypass() -> None:
    frontmatter = _valid_frontmatter("figure-agent.critique.v1.5")
    frontmatter["editorial_art_direction"]["hero_focus"] = {
        "verdict": "needs_human",
        "evidence": "target journal is unspecified",
        "rationale": "human art direction must choose the hero panel",
        "concrete_fix": "accept_simplification: leave hero focus as-is",
        "blocks_high_impact": False,
    }
    frontmatter["findings"] = []
    frontmatter["micro_defects"] = []

    with pytest.raises(CritiqueContractError, match="hero_focus"):
        validate_critique_schema(frontmatter)


def test_validate_critique_schema_accepts_v1_5_fail_with_intentional_simplification() -> None:
    frontmatter = _valid_frontmatter("figure-agent.critique.v1.5")
    frontmatter["editorial_art_direction"]["visual_identity"] = {
        "verdict": "fail",
        "evidence": "visual identity is intentionally plain for this methods figure",
        "rationale": "the visual register cannot support high-impact promotion",
        "concrete_fix": "accept_simplification: methods-only schematic, not a hero illustration",
        "blocks_high_impact": True,
    }
    frontmatter["findings"] = []
    frontmatter["micro_defects"] = []

    validate_critique_schema(frontmatter)


def test_validate_critique_schema_rejects_v1_5_high_impact_with_weak_editorial_slot() -> None:
    critique_hash = "sha256:" + "a" * 64
    frontmatter = _valid_frontmatter("figure-agent.critique.v1.5")
    frontmatter["critique_input_hash"] = critique_hash
    frontmatter["editorial_art_direction"]["aesthetic_risk"]["verdict"] = "weak"
    frontmatter["journal_grade_assessment"] = {
        "schema": "figure-agent.journal-grade-assessment.v1",
        "scoring_mode": "fresh_reaudit",
        "assessed_artifact_hash": critique_hash,
        "benchmark_level": "high_impact_candidate",
        "confidence": "high",
        "blockers": [],
        "regression_detected": False,
        "regressions": [],
        "score_is_gateable": True,
        "next_quality_bottleneck": "polish",
        "rationale": "claims high-impact quality",
    }

    with pytest.raises(CritiqueContractError, match="high_impact_candidate"):
        validate_critique_schema(frontmatter)
