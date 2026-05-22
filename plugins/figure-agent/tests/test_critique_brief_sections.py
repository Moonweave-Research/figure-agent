from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_brief_sections import (  # noqa: E402
    journal_grade_assessment,
    journal_grade_assessment_schema,
    mandatory_audit_checklists,
    quality_axes_schema,
    top_tier_journal_audit,
)


def test_critique_brief_sections_render_core_contracts() -> None:
    assert "## Mandatory Audit Checklists" in mandatory_audit_checklists()
    assert "### D. Conceptual Completeness Audit" in mandatory_audit_checklists()
    assert "## Top-Tier Journal Figure Audit" in top_tier_journal_audit()
    assert "top_tier_audit.<slot_key>" in top_tier_journal_audit()
    assert "Scores are advisory fresh re-audit diagnostics" in journal_grade_assessment()


def test_critique_brief_sections_render_schema_blocks() -> None:
    quality_schema = quality_axes_schema()
    assessment_schema = journal_grade_assessment_schema("sha256:abc")
    calibrated_schema = journal_grade_assessment_schema(
        "sha256:abc",
        {
            "reference_pack_hash": "sha256:def",
            "reference_class": "mechanism_schematic",
            "visual_ambition": "high_impact_candidate",
        },
    )

    assert "quality_axes:" in quality_schema
    assert "  message_storyline:" in quality_schema
    assert "  publication_readiness:" in quality_schema
    assert "journal_grade_assessment:" in assessment_schema
    assert "assessed_artifact_hash: sha256:abc" in assessment_schema
    assert "overall_score: 0-100" in assessment_schema
    assert "reference_calibration:" in calibrated_schema
    assert "reference_pack_hash: sha256:def" in calibrated_schema
    assert "score_basis: current_artifact_vs_pack" in calibrated_schema
