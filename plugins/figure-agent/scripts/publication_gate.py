"""Structured publication-gate helpers for accepted figure workflows."""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

import fixture_identity


class PublicationGateFailure(NamedTuple):
    code: str
    category: str
    actor: str
    message: str
    required_action: str


PUBLICATION_GATE_NOT_APPLICABLE = "NOT_APPLICABLE"
PUBLICATION_GATE_PASS = "PASS"
PUBLICATION_GATE_HUMAN_ACCEPTANCE_REQUIRED = "HUMAN_ACCEPTANCE_REQUIRED"
PUBLICATION_GATE_PROVENANCE_REQUIRED = "PROVENANCE_REQUIRED"


def _has_field_value(audit_text: str, field: str, values: tuple[str, ...]) -> bool:
    value_pattern = "|".join(re.escape(value) for value in values)
    pattern = (
        rf"^\s*(?:[-*]\s*)?(?:\*\*)?{re.escape(field)}(?:\*\*)?\s*:"
        rf"\s*(?:\*\*)?\s*(?:{value_pattern})(?:\*\*)?\s*$"
    )
    return re.search(pattern, audit_text, re.IGNORECASE | re.MULTILINE) is not None


def publication_gate_failure_dicts(
    records: list[PublicationGateFailure],
) -> list[dict[str, str]]:
    return [record._asdict() for record in records]


def publication_gate_summary(
    audit_path: Path,
    *,
    accepted: bool | None,
    require_disclosure: bool = False,
) -> dict[str, object]:
    if accepted is None:
        return {
            "publication_gate_state": PUBLICATION_GATE_NOT_APPLICABLE,
            "publication_gate_failures": [],
        }

    records = publication_compliance_failure_records(
        audit_path,
        require_disclosure=require_disclosure,
    )
    if accepted is False:
        state = PUBLICATION_GATE_HUMAN_ACCEPTANCE_REQUIRED
    elif records:
        state = PUBLICATION_GATE_PROVENANCE_REQUIRED
    else:
        state = PUBLICATION_GATE_PASS

    return {
        "publication_gate_state": state,
        "publication_gate_failures": publication_gate_failure_dicts(records),
    }


def publication_compliance_failure_records(
    audit_path: Path,
    *,
    require_disclosure: bool = False,
) -> list[PublicationGateFailure]:
    if not audit_path.exists():
        return [
            PublicationGateFailure(
                code="missing_quality_audit",
                category="quality_audit_stale",
                actor="agent",
                message="missing audit: QUALITY_AUDIT.md",
                required_action="create QUALITY_AUDIT.md from the publication audit scaffold",
            )
        ]

    audit_text = audit_path.read_text(encoding="utf-8")
    records: list[PublicationGateFailure] = []
    if "Provenance and Publication Compliance" not in audit_text:
        records.append(
            PublicationGateFailure(
                code="missing_publication_compliance_section",
                category="publication_provenance",
                actor="human",
                message="missing Provenance and Publication Compliance section in QUALITY_AUDIT.md",
                required_action=(
                    "add a Provenance and Publication Compliance section with target "
                    "venue, disclosure, and human review fields"
                ),
            )
        )
    if not _has_field_value(audit_text, "submission-safe", ("true", "yes")):
        records.append(
            PublicationGateFailure(
                code="missing_submission_safe_true",
                category="publication_provenance",
                actor="human",
                message="QUALITY_AUDIT.md does not declare submission-safe: true",
                required_action=(
                    "Human reviewer must decide submission safety and write an explicit value."
                ),
            )
        )
    if require_disclosure and not _has_field_value(
        audit_text,
        "disclosure-needed",
        ("true", "false", "yes", "no", "none", "n/a", "not-applicable"),
    ):
        records.append(
            PublicationGateFailure(
                code="missing_disclosure_needed",
                category="publication_provenance",
                actor="human",
                message="QUALITY_AUDIT.md does not declare disclosure-needed",
                required_action=(
                    "Human reviewer must declare whether publication disclosure is needed."
                ),
            )
        )
    return records


def publication_audit_scaffold_text(fixture: str) -> str:
    fixture_identity.validate_fixture_name(fixture)
    return (
        "# Quality Audit\n\n"
        f"fixture: {fixture}\n\n"
        "## Provenance and Publication Compliance\n\n"
        "target-venue: unresolved\n"
        "final-artifact-scope: unresolved\n"
        "ai-generated-image-in-submitted-artifact: unresolved\n"
        "ai-generated-images-used-as-internal-reference: unresolved\n"
        "ai-tools-used: unresolved\n"
        "disclosure-needed: unresolved\n"
        "disclosure-draft: unresolved\n"
        "human-reviewer: unresolved\n"
        "human-visual-acceptance: false\n"
        "submission-safe: false\n"
    )


def write_publication_audit_scaffold(
    audit_path: Path,
    *,
    fixture: str,
    force: bool = False,
) -> Path:
    if audit_path.exists() and not force:
        raise FileExistsError(f"{audit_path} already exists; pass force=True to overwrite")
    audit_path.write_text(publication_audit_scaffold_text(fixture), encoding="utf-8")
    return audit_path
