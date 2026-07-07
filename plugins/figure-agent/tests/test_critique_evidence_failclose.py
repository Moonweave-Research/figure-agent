"""Fail-closed behavior for the print-scale critique evidence lint (Task 0.6a)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_evidence_lint import (  # noqa: E402
    SCHEMAS_PREDATING_PRINT_SCALE,
    SCHEMAS_WITH_PRINT_SCALE_EVIDENCE,
    critique_evidence_violations,
)


def _gated_axes(*, evidence: str | None = None) -> dict:
    axis = {"verdict": "pass", "evidence": evidence} if evidence else {"verdict": "pass"}
    return {"journal_polish": dict(axis), "publication_readiness": dict(axis)}


def test_predating_and_lintable_lists_are_disjoint() -> None:
    assert not (SCHEMAS_PREDATING_PRINT_SCALE & SCHEMAS_WITH_PRINT_SCALE_EVIDENCE)


def test_unknown_schema_with_gated_pass_verdict_blocks() -> None:
    frontmatter = {
        "schema": "figure-agent.critique.v99",
        "quality_axes": _gated_axes(),
    }
    violations = critique_evidence_violations(frontmatter)
    assert violations
    assert "not lintable" in violations[0].message


def test_missing_schema_with_gated_pass_verdict_blocks() -> None:
    frontmatter = {"quality_axes": _gated_axes()}
    violations = critique_evidence_violations(frontmatter)
    assert violations
    assert "not lintable" in violations[0].message


def test_retired_intermediate_schema_with_gated_pass_verdict_blocks() -> None:
    # v1.16 postdates print-scale (v1.10) and is retired; it does not legitimately
    # predate the requirement, so a pass verdict without print-scale evidence blocks.
    frontmatter = {
        "schema": "figure-agent.critique.v1.16",
        "quality_axes": _gated_axes(),
    }
    assert critique_evidence_violations(frontmatter)


def test_predating_schema_stays_exempt() -> None:
    for schema in SCHEMAS_PREDATING_PRINT_SCALE:
        frontmatter = {"schema": schema, "quality_axes": _gated_axes()}
        assert critique_evidence_violations(frontmatter) == []


def test_unknown_schema_without_gated_pass_verdict_passes() -> None:
    # Nothing declared -> nothing to check -> pass, regardless of schema.
    frontmatter = {
        "schema": "figure-agent.critique.v99",
        "quality_axes": {"journal_polish": {"verdict": "needs_patch"}},
    }
    assert critique_evidence_violations(frontmatter) == []


def test_unknown_schema_without_quality_axes_passes() -> None:
    assert critique_evidence_violations({"schema": "figure-agent.critique.v99"}) == []


def test_lintable_schema_with_print_scale_evidence_passes() -> None:
    frontmatter = {
        "schema": "figure-agent.critique.v1.17",
        "quality_axes": _gated_axes(evidence="print-scale audit: print_178mm.png passes"),
    }
    assert critique_evidence_violations(frontmatter) == []


def test_lintable_schema_without_print_scale_evidence_blocks() -> None:
    frontmatter = {
        "schema": "figure-agent.critique.v1.17",
        "quality_axes": _gated_axes(evidence="looks good"),
    }
    violations = critique_evidence_violations(frontmatter)
    assert violations
    assert "print-scale audit evidence" in violations[0].message
