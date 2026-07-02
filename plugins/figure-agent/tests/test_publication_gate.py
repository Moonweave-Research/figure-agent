from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import human_attestation  # noqa: E402
from publication_gate import (  # noqa: E402
    PUBLICATION_GATE_PASS,
    PUBLICATION_GATE_PROVENANCE_REQUIRED,
    publication_audit_scaffold_text,
    publication_compliance_failure_records,
    publication_gate_summary,
    write_publication_audit_scaffold,
)


def test_publication_compliance_records_missing_audit(tmp_path: Path) -> None:
    records = publication_compliance_failure_records(tmp_path / "QUALITY_AUDIT.md")

    assert [record.code for record in records] == ["missing_quality_audit"]
    assert records[0].category == "quality_audit_stale"
    assert records[0].actor == "agent"
    assert records[0].message == "missing audit: QUALITY_AUDIT.md"
    assert "create QUALITY_AUDIT.md" in records[0].required_action


def test_publication_compliance_records_missing_required_fields(tmp_path: Path) -> None:
    audit = tmp_path / "QUALITY_AUDIT.md"
    audit.write_text("# Quality Audit\n\nsubmission-safe: false\n", encoding="utf-8")

    records = publication_compliance_failure_records(audit, require_disclosure=True)

    assert [record.code for record in records] == [
        "missing_publication_compliance_section",
        "missing_submission_safe_true",
        "missing_disclosure_needed",
    ]
    assert all(record.category == "publication_provenance" for record in records)
    assert all(record.actor == "human" for record in records)
    assert [record.message for record in records] == [
        "missing Provenance and Publication Compliance section in QUALITY_AUDIT.md",
        "QUALITY_AUDIT.md does not declare submission-safe: true",
        "QUALITY_AUDIT.md does not declare disclosure-needed",
    ]


def test_publication_compliance_records_accept_complete_audit(tmp_path: Path) -> None:
    audit = tmp_path / "QUALITY_AUDIT.md"
    audit.write_text(
        "# Quality Audit\n\n"
        "## Provenance and Publication Compliance\n\n"
        "submission-safe: true\n"
        "disclosure-needed: no\n",
        encoding="utf-8",
    )

    assert publication_compliance_failure_records(audit, require_disclosure=True) == []


def test_publication_compliance_records_accept_markdown_bold_fields(tmp_path: Path) -> None:
    audit = tmp_path / "QUALITY_AUDIT.md"
    audit.write_text(
        "# Quality Audit\n\n"
        "## Provenance and Publication Compliance\n\n"
        "**submission-safe:** true\n"
        "**disclosure-needed:** no\n",
        encoding="utf-8",
    )

    assert publication_compliance_failure_records(audit, require_disclosure=True) == []


def test_publication_gate_summary_requires_valid_human_attestation_when_accepted(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "examples" / "demo_fig"
    fixture.mkdir(parents=True)
    (fixture / "demo_fig.tex").write_text("source\n", encoding="utf-8")
    audit = fixture / "QUALITY_AUDIT.md"
    audit.write_text(
        "# Quality Audit\n\n"
        "## Provenance and Publication Compliance\n\n"
        "submission-safe: true\n"
        "disclosure-needed: no\n",
        encoding="utf-8",
    )

    summary = publication_gate_summary(audit, accepted=True, example_dir=fixture)

    assert summary["publication_gate_state"] == PUBLICATION_GATE_PROVENANCE_REQUIRED
    assert summary["publication_gate_failures"][0]["code"] == "invalid_human_attestation"
    assert "fig-agent attest demo_fig" in summary["publication_gate_failures"][0]["required_action"]


def test_publication_gate_summary_accepts_valid_human_attestation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    fixture = tmp_path / "examples" / "demo_fig"
    fixture.mkdir(parents=True)
    (fixture / "demo_fig.tex").write_text("source\n", encoding="utf-8")
    human_attestation.write_attestation(fixture)
    audit = fixture / "QUALITY_AUDIT.md"
    audit.write_text(
        "# Quality Audit\n\n"
        "## Provenance and Publication Compliance\n\n"
        "submission-safe: true\n"
        "disclosure-needed: no\n",
        encoding="utf-8",
    )

    summary = publication_gate_summary(audit, accepted=True, example_dir=fixture)

    assert summary["publication_gate_state"] == PUBLICATION_GATE_PASS
    assert summary["publication_gate_failures"] == []


def test_publication_compliance_records_reject_partial_truthy_values(tmp_path: Path) -> None:
    audit = tmp_path / "QUALITY_AUDIT.md"
    audit.write_text(
        "# Quality Audit\n\n"
        "## Provenance and Publication Compliance\n\n"
        "submission-safe: true-ish\n"
        "disclosure-needed: not-applicable-ish\n",
        encoding="utf-8",
    )

    records = publication_compliance_failure_records(audit, require_disclosure=True)

    assert [record.code for record in records] == [
        "missing_submission_safe_true",
        "missing_disclosure_needed",
    ]


def test_publication_audit_scaffold_uses_conservative_defaults() -> None:
    text = publication_audit_scaffold_text("demo_fig")

    assert "## Provenance and Publication Compliance" in text
    assert "target-venue: unresolved" in text
    assert "final-artifact-scope: unresolved" in text
    assert "ai-generated-image-in-submitted-artifact: unresolved" in text
    assert "ai-tools-used: unresolved" in text
    assert "disclosure-needed: unresolved" in text
    assert "human-reviewer: unresolved" in text
    assert "human-visual-acceptance: false" in text
    assert "submission-safe: false" in text
    assert "accepted: true" not in text


def test_publication_audit_scaffold_rejects_unsafe_fixture_name() -> None:
    with pytest.raises(ValueError, match="fixture name"):
        publication_audit_scaffold_text("../outside")


def test_write_publication_audit_scaffold_refuses_overwrite_without_force(
    tmp_path: Path,
) -> None:
    audit = tmp_path / "QUALITY_AUDIT.md"
    audit.write_text("existing\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_publication_audit_scaffold(audit, fixture="demo_fig")

    assert audit.read_text(encoding="utf-8") == "existing\n"


def test_write_publication_audit_scaffold_rejects_unsafe_fixture_before_write(
    tmp_path: Path,
) -> None:
    audit = tmp_path / "QUALITY_AUDIT.md"

    with pytest.raises(ValueError, match="fixture name"):
        write_publication_audit_scaffold(audit, fixture="../outside")

    assert not audit.exists()


def test_write_publication_audit_scaffold_can_force_overwrite(tmp_path: Path) -> None:
    audit = tmp_path / "QUALITY_AUDIT.md"
    audit.write_text("existing\n", encoding="utf-8")

    write_publication_audit_scaffold(audit, fixture="demo_fig", force=True)

    assert "submission-safe: false" in audit.read_text(encoding="utf-8")
