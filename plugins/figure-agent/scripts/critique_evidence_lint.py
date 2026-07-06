"""Shared critique evidence-completeness checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PRINT_SCALE_EVIDENCE_TOKENS = (
    "print-scale",
    "print_scale",
    "print_178mm",
    "print_thumbnail",
)
SCHEMAS_WITH_PRINT_SCALE_EVIDENCE = frozenset(
    {
        "figure-agent.critique.v1.10",
        "figure-agent.critique.v1.14",
        "figure-agent.critique.v1.17",
    }
)
# Schemas that legitimately predate the print-scale-evidence requirement (added at
# v1.10). A critique on one of these may declare a journal_polish/publication_readiness
# pass without naming print-scale evidence. This is an explicit closed allowlist: a
# schema in NEITHER this set nor SCHEMAS_WITH_PRINT_SCALE_EVIDENCE that declares a
# gated pass verdict is treated as unlintable and blocks (fail-closed).
SCHEMAS_PREDATING_PRINT_SCALE = frozenset(
    {
        "figure-agent.critique.v1",
        "figure-agent.critique.v1.1",
        "figure-agent.critique.v1.2",
        "figure-agent.critique.v1.3",
        "figure-agent.critique.v1.4",
        "figure-agent.critique.v1.5",
        "figure-agent.critique.v1.6",
        "figure-agent.critique.v1.7",
        "figure-agent.critique.v1.8",
        "figure-agent.critique.v1.9",
    }
)


@dataclass(frozen=True)
class CritiqueEvidenceViolation:
    category: str
    message: str


def _text_mentions_print_scale_evidence(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return any(token in lowered for token in PRINT_SCALE_EVIDENCE_TOKENS)
    if isinstance(value, list):
        return any(_text_mentions_print_scale_evidence(item) for item in value)
    if isinstance(value, dict):
        return any(_text_mentions_print_scale_evidence(item) for item in value.values())
    return False


def critique_evidence_violations(frontmatter: dict[str, Any]) -> list[CritiqueEvidenceViolation]:
    quality_axes = frontmatter.get("quality_axes")
    if not isinstance(quality_axes, dict):
        return []
    gated_pass_axes = [
        axis_name
        for axis_name in ("journal_polish", "publication_readiness")
        if isinstance(quality_axes.get(axis_name), dict)
        and quality_axes[axis_name].get("verdict") == "pass"
    ]
    # Nothing declared -> nothing to check -> pass, regardless of schema.
    if not gated_pass_axes:
        return []
    schema = frontmatter.get("schema")
    if schema in SCHEMAS_PREDATING_PRINT_SCALE:
        return []
    if schema not in SCHEMAS_WITH_PRINT_SCALE_EVIDENCE:
        # Unknown/missing/retired schema that declares a gated pass verdict: the
        # print-scale token lint cannot be applied, so fail closed rather than
        # silently exempt it.
        return [
            CritiqueEvidenceViolation(
                category="audit_evidence",
                message=(
                    "critique schema not lintable for print-scale evidence: "
                    f"{schema!r} declares a passing journal_polish/publication_readiness verdict"
                ),
            )
        ]
    violations: list[CritiqueEvidenceViolation] = []
    for axis_name in gated_pass_axes:
        if _text_mentions_print_scale_evidence(quality_axes[axis_name].get("evidence")):
            continue
        violations.append(
            CritiqueEvidenceViolation(
                category="audit_evidence",
                message=(
                    f"{axis_name} verdict is pass but evidence does not name "
                    "print-scale audit evidence"
                ),
            )
        )
    return violations
