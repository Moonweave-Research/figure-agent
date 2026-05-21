"""Shared vocabulary for critique.md schema validation."""

from __future__ import annotations

CRITIQUE_SCHEMA_V1 = "figure-agent.critique.v1"
CRITIQUE_SCHEMA_V1_1 = "figure-agent.critique.v1.1"
CRITIQUE_SCHEMA_V1_2 = "figure-agent.critique.v1.2"
CRITIQUE_SCHEMA_V1_3 = "figure-agent.critique.v1.3"
CRITIQUE_SCHEMA_V1_4 = "figure-agent.critique.v1.4"
CRITIQUE_SCHEMA_V1_5 = "figure-agent.critique.v1.5"

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
    }
)
MICRO_DEFECT_STATUSES = frozenset({"open", "resolved", "accept_simplification"})
