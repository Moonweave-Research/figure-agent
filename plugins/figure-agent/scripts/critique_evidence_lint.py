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
        "figure-agent.critique.v1.4",
        "figure-agent.critique.v1.5",
        "figure-agent.critique.v1.6",
        "figure-agent.critique.v1.7",
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
    if frontmatter.get("schema") not in SCHEMAS_WITH_PRINT_SCALE_EVIDENCE:
        return []
    quality_axes = frontmatter.get("quality_axes")
    if not isinstance(quality_axes, dict):
        return []
    violations: list[CritiqueEvidenceViolation] = []
    for axis_name in ("journal_polish", "publication_readiness"):
        axis = quality_axes.get(axis_name)
        if not isinstance(axis, dict) or axis.get("verdict") != "pass":
            continue
        if _text_mentions_print_scale_evidence(axis.get("evidence")):
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
