from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_schema_vocab import (  # noqa: E402
    AESTHETIC_LEVER_DIMENSIONS,
    AESTHETIC_LEVER_ROUTES,
    AESTHETIC_LEVER_VERDICTS,
    CRITIQUE_SCHEMA_V1,
    CRITIQUE_SCHEMA_V1_1,
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
    CROP_AUDIT_VERDICTS,
    EDITORIAL_AUDIT_KEYS,
    EDITORIAL_POLISH_PATHS,
    EDITORIAL_VERDICTS,
    JOURNAL_SCORE_KEYS,
    MICRO_DEFECT_ACCEPT_SIMPLIFICATION_REASONS,
    MICRO_DEFECT_KINDS,
    MICRO_DEFECT_STATUSES,
    QUALITY_AXIS_NAMES,
    TOP_TIER_AUDIT_KEYS,
)


def test_critique_schema_versions_are_canonical() -> None:
    assert CRITIQUE_SCHEMA_V1 == "figure-agent.critique.v1"
    assert CRITIQUE_SCHEMA_V1_1 == "figure-agent.critique.v1.1"
    assert CRITIQUE_SCHEMA_V1_2 == "figure-agent.critique.v1.2"
    assert CRITIQUE_SCHEMA_V1_3 == "figure-agent.critique.v1.3"
    assert CRITIQUE_SCHEMA_V1_4 == "figure-agent.critique.v1.4"
    assert CRITIQUE_SCHEMA_V1_5 == "figure-agent.critique.v1.5"
    assert CRITIQUE_SCHEMA_V1_6 == "figure-agent.critique.v1.6"
    assert CRITIQUE_SCHEMA_V1_7 == "figure-agent.critique.v1.7"
    assert CRITIQUE_SCHEMA_V1_8 == "figure-agent.critique.v1.8"
    assert CRITIQUE_SCHEMA_V1_9 == "figure-agent.critique.v1.9"
    assert CRITIQUE_SCHEMA_V1_10 == "figure-agent.critique.v1.10"
    assert CRITIQUE_SCHEMA_V1_11 == "figure-agent.critique.v1.11"


def test_critique_schema_vocab_keeps_current_audit_dimensions() -> None:
    assert QUALITY_AXIS_NAMES == (
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
    assert JOURNAL_SCORE_KEYS == frozenset(
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
    assert TOP_TIER_AUDIT_KEYS == (
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
    assert MICRO_DEFECT_KINDS == frozenset(
        {
            "line_crosses_label",
            "wire_crosses_label",
            "arrow_tip_fused",
            "label_target_detached",
            "floating_semantic_cue",
            "drawing_order_suspect",
            "print_scale_unreadable",
            "label_backdrop_overflows_outline",
            "label_glyph_overlaps_internal_drawing",
            "label_crosses_panel_boundary",
            "label_crosses_column_rule",
            "label_overflows_row_box",
        }
    )
    assert MICRO_DEFECT_STATUSES == frozenset({"open", "resolved", "accept_simplification"})
    assert MICRO_DEFECT_ACCEPT_SIMPLIFICATION_REASONS == frozenset(
        {
            "false_positive",
            "intentional_schematic",
            "outside_target_region",
            "convention_acceptable",
            "decorative_background",
        }
    )
    assert CROP_AUDIT_VERDICTS == frozenset({"defect", "no_defect", "uncertain"})
    assert AESTHETIC_LEVER_DIMENSIONS == frozenset(
        {
            "maturity",
            "hero_hierarchy",
            "whitespace_breathing",
            "typography_authority",
            "color_harmony",
            "line_weight_rhythm",
            "component_fidelity",
            "hand_craft",
            "cross_panel_grammar",
            "polish_route",
        }
    )
    assert AESTHETIC_LEVER_VERDICTS == frozenset(
        {"pass", "weak", "fail", "needs_human", "not_applicable"}
    )
    assert AESTHETIC_LEVER_ROUTES == frozenset(
        {"none", "tikz_patch", "svg_polish", "semantic_backport", "human_art_direction"}
    )


def test_editorial_art_direction_vocab_is_canonical() -> None:
    assert EDITORIAL_AUDIT_KEYS == (
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
    assert EDITORIAL_VERDICTS == frozenset({"pass", "weak", "fail", "needs_human"})
    assert EDITORIAL_POLISH_PATHS == frozenset(
        {
            "continue_tikz",
            "ready_for_svg_polish",
            "needs_human_art_direction",
            "semantic_backport_required",
        }
    )
