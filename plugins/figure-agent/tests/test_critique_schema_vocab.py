from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_schema_vocab import (  # noqa: E402
    CRITIQUE_SCHEMA_V1,
    CRITIQUE_SCHEMA_V1_1,
    CRITIQUE_SCHEMA_V1_2,
    CRITIQUE_SCHEMA_V1_3,
    JOURNAL_SCORE_KEYS,
    QUALITY_AXIS_NAMES,
    TOP_TIER_AUDIT_KEYS,
)


def test_critique_schema_versions_are_canonical() -> None:
    assert CRITIQUE_SCHEMA_V1 == "figure-agent.critique.v1"
    assert CRITIQUE_SCHEMA_V1_1 == "figure-agent.critique.v1.1"
    assert CRITIQUE_SCHEMA_V1_2 == "figure-agent.critique.v1.2"
    assert CRITIQUE_SCHEMA_V1_3 == "figure-agent.critique.v1.3"


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
