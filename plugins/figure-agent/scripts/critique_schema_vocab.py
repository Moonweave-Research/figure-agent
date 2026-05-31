"""Shared vocabulary for critique.md schema validation."""

from __future__ import annotations

CRITIQUE_SCHEMA_V1 = "figure-agent.critique.v1"
CRITIQUE_SCHEMA_V1_1 = "figure-agent.critique.v1.1"
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

FINDING_SEVERITIES = frozenset({"BLOCKER", "MAJOR", "MINOR", "NIT"})
ALLOWED_CONCEPTUAL_REFERENCES = frozenset(
    {"provided_reference", "briefing", "reference_pack", "not_provided"}
)
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
QUALITY_VERDICTS = frozenset(
    {"pass", "needs_patch", "needs_human", "block", "not_applicable"}
)
QUALITY_CONFIDENCES = frozenset({"low", "medium", "high"})
QUALITY_ACTIONS = frozenset(
    {"none", "patch", "human_review", "revise_briefing", "block_release"}
)
PANEL_ROLES = frozenset(
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
PANEL_ROLE_QUALITIES = frozenset({"clear", "weak", "missing", "redundant"})
QUALITY_SEVERITY_RANK = {
    "pass": 0,
    "needs_patch": 1,
    "needs_human": 2,
    "block": 3,
}
QUALITY_ACTIONS_BY_VERDICT = {
    "pass": frozenset({"none"}),
    "not_applicable": frozenset({"none"}),
    "needs_patch": frozenset({"patch", "revise_briefing"}),
    "needs_human": frozenset({"human_review", "revise_briefing"}),
    "block": frozenset({"block_release", "human_review"}),
}

JOURNAL_ASSESSMENT_SCHEMA = "figure-agent.journal-grade-assessment.v1"
JOURNAL_SCORING_MODE = "fresh_reaudit"
JOURNAL_BENCHMARK_LEVELS = frozenset(
    {"draft", "solid_manuscript", "high_impact_candidate", "needs_human_art_direction", "blocked"}
)
JOURNAL_BOTTLENECKS = frozenset(
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
JOURNAL_SCORE_BLOCK_KEYS = frozenset({"overall_score", "sub_scores", "score_rationale"})
JOURNAL_REFERENCE_SCORE_BASIS = frozenset({"current_artifact_vs_pack"})

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
TOP_TIER_AUDIT_VERDICTS = frozenset({"pass", "weak", "fail", "needs_human"})

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
EDITORIAL_VERDICTS = frozenset({"pass", "weak", "fail", "needs_human"})
EDITORIAL_POLISH_PATHS = frozenset(
    {
        "continue_tikz",
        "ready_for_svg_polish",
        "needs_human_art_direction",
        "semantic_backport_required",
    }
)

MICRO_DEFECT_KINDS = frozenset(
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
        "label_stacked_on_reference_line",
        "label_curve_near_label",
        "label_path_near_miss",
    }
)
MICRO_DEFECT_STATUSES = frozenset({"open", "resolved", "accept_simplification"})
MICRO_DEFECT_ACCEPT_SIMPLIFICATION_REASONS = frozenset(
    {
        "false_positive",
        "intentional_schematic",
        "outside_target_region",
        "convention_acceptable",
        "decorative_background",
    }
)
MICRO_DEFECT_ACCEPT_SIMPLIFICATION_MIN_RATIONALE_CHARS = 40
MICRO_DEFECT_ACCEPT_SIMPLIFICATION_RATIONALE_MARKERS = (
    "false positive",
    "not ",
    "intentional",
    "acceptable because",
    "separate",
    "distinct",
    "outside",
    "axis",
    "legend",
    "background",
    "decorative",
    "convention",
)
CROP_AUDIT_VERDICTS = frozenset({"defect", "no_defect", "uncertain"})
CROP_ANOMALY_VERDICTS = frozenset({"none", "present", "uncertain"})

SVG_DELTA_EVALUATION_STATES = frozenset(
    {
        "improved",
        "no_meaningful_change",
        "regressed",
        "needs_human_art_direction",
        "invalid",
    }
)
SVG_DELTA_IMAGE_IDS = frozenset({"before", "after", "diff"})
SVG_DELTA_IMAGE_VERDICTS = frozenset({"inspected"})
SVG_DELTA_REGRESSION_CATEGORIES = frozenset(
    {
        "semantic_drift",
        "label_readability",
        "crop_regression",
        "print_scale_regression",
        "overdecorated",
        "journal_mismatch",
    }
)
SVG_DELTA_ROUTES = frozenset(
    {
        "continue_svg_polish",
        "accept_svg_polish",
        "semantic_backport_required",
        "needs_human_art_direction",
    }
)
AESTHETIC_GATE_SLOTS = (
    "maturity_restraint",
    "visual_hierarchy",
    "template_genericness",
    "overdecorated_or_cartoonish",
    "journal_fit",
    "handcrafted_finish",
    "semantic_preservation",
    "print_scale_finish",
    "paper_wide_coherence",
)
AESTHETIC_ANTIPATTERN_IDS = (
    "childish_shape_language",
    "poster_gradient_decoration",
    "generic_template_look",
    "dead_flat_vector_finish",
    "uniform_line_weight_monotony",
    "weak_hero_anchor",
    "cramped_or_dead_whitespace",
    "low_authority_typography",
    "annotation_noise_competes_with_science",
    "panel_style_mismatch",
    "reference_overcopying",
    "reference_underlearning",
    "decorative_detail_without_explanatory_value",
)
AESTHETIC_GATE_VERDICTS = frozenset({"pass", "weak", "fail", "needs_human"})
AESTHETIC_GATE_ROUTES = frozenset(
    {
        "pass",
        "tikz_patch",
        "svg_polish",
        "semantic_backport",
        "needs_human_art_direction",
        "accept_simplification",
    }
)
AESTHETIC_LEVER_DIMENSIONS = frozenset(
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
AESTHETIC_LEVER_VERDICTS = frozenset(
    {"pass", "weak", "fail", "needs_human", "not_applicable"}
)
AESTHETIC_LEVER_ROUTES = frozenset(
    {"none", "tikz_patch", "svg_polish", "semantic_backport", "human_art_direction"}
)

JOURNAL_PLAYBOOK_AUDIT_SCHEMA = "figure-agent.journal-art-direction-playbook-audit.v1"
JOURNAL_PLAYBOOK_VERDICTS = frozenset(
    {"pass", "weak", "fail", "needs_human", "not_applicable"}
)
JOURNAL_PLAYBOOK_ROUTES = frozenset(
    {
        "none",
        "continue_tikz",
        "ready_for_svg_polish",
        "semantic_backport_required",
        "needs_human_art_direction",
    }
)
