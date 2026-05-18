from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_adjudication import (  # noqa: E402
    CritiqueAdjudicationError,
    adjudication_is_stale,
    build_adjudication_scaffold,
    load_adjudication,
    main,
    scaffold_adjudication,
    validate_adjudication,
    write_adjudication,
)
from quality_manifest import file_sha256  # noqa: E402


def _valid_payload(critique_hash: str = "sha256:" + "a" * 64) -> dict:
    return {
        "schema": "figure-agent.critique-adjudication.v1",
        "fixture": "demo_fig",
        "source_critique_hash": critique_hash,
        "decisions": [
            {
                "finding_id": "C001",
                "decision": "apply",
                "reason": "label overlaps the trap lobe",
                "patch_target": "panel A label cluster",
                "evidence": "critique C001 and build/demo_fig.png",
            }
        ],
    }


def test_valid_adjudication_loads_successfully(tmp_path: Path) -> None:
    path = tmp_path / "critique_adjudication.yaml"
    write_adjudication(path, _valid_payload())

    data = load_adjudication(path)

    assert data["fixture"] == "demo_fig"
    assert data["decisions"][0]["finding_id"] == "C001"


def test_invalid_schema_fails() -> None:
    payload = _valid_payload()
    payload["schema"] = "figure-agent.critique-adjudication.v0"

    with pytest.raises(CritiqueAdjudicationError, match="schema"):
        validate_adjudication(payload)


def test_invalid_decision_value_fails() -> None:
    payload = _valid_payload()
    payload["decisions"][0]["decision"] = "maybe"

    with pytest.raises(CritiqueAdjudicationError, match="decision"):
        validate_adjudication(payload)


def test_missing_required_fields_fail() -> None:
    payload = _valid_payload()
    del payload["source_critique_hash"]

    with pytest.raises(CritiqueAdjudicationError, match="source_critique_hash"):
        validate_adjudication(payload)


@pytest.mark.parametrize("field", ("fixture", "decisions"))
def test_missing_top_level_required_fields_fail(field: str) -> None:
    payload = _valid_payload()
    del payload[field]

    with pytest.raises(CritiqueAdjudicationError, match=field):
        validate_adjudication(payload)


@pytest.mark.parametrize("field", ("finding_id", "reason"))
def test_missing_decision_required_fields_fail(field: str) -> None:
    payload = _valid_payload()
    del payload["decisions"][0][field]

    with pytest.raises(CritiqueAdjudicationError, match=field):
        validate_adjudication(payload)


def test_duplicate_finding_ids_fail() -> None:
    payload = _valid_payload()
    payload["decisions"].append(
        {
            "finding_id": "C001",
            "decision": "defer",
            "reason": "same finding repeated",
        }
    )

    with pytest.raises(CritiqueAdjudicationError, match="duplicate finding_id"):
        validate_adjudication(payload)


def test_invalid_source_critique_hash_prefix_fails() -> None:
    payload = _valid_payload("md5:" + "a" * 32)

    with pytest.raises(CritiqueAdjudicationError, match="sha256"):
        validate_adjudication(payload)


def test_malformed_yaml_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path / "critique_adjudication.yaml"
    path.write_text("schema: [unterminated\n", encoding="utf-8")

    with pytest.raises(CritiqueAdjudicationError, match="invalid YAML"):
        load_adjudication(path)


def test_load_adjudication_fails_cleanly_when_file_is_missing(tmp_path: Path) -> None:
    path = tmp_path / "critique_adjudication.yaml"

    with pytest.raises(CritiqueAdjudicationError, match="missing adjudication"):
        load_adjudication(path)


def test_matching_critique_hash_is_fresh(tmp_path: Path) -> None:
    critique = tmp_path / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    adjudication = tmp_path / "critique_adjudication.yaml"
    write_adjudication(adjudication, _valid_payload(file_sha256(critique)))

    assert adjudication_is_stale(adjudication, critique) is False


def test_stale_adjudication_is_detected_when_critique_changes(tmp_path: Path) -> None:
    critique = tmp_path / "critique.md"
    critique.write_text("# critique v1\n", encoding="utf-8")
    adjudication = tmp_path / "critique_adjudication.yaml"
    write_adjudication(adjudication, _valid_payload(file_sha256(critique)))

    critique.write_text("# critique v2\n", encoding="utf-8")

    assert adjudication_is_stale(adjudication, critique) is True


def test_stale_check_fails_cleanly_when_critique_is_missing(tmp_path: Path) -> None:
    critique = tmp_path / "critique.md"
    adjudication = tmp_path / "critique_adjudication.yaml"
    write_adjudication(adjudication, _valid_payload())

    with pytest.raises(CritiqueAdjudicationError, match="missing critique"):
        adjudication_is_stale(adjudication, critique)


def test_unknown_future_fields_survive_load_write(tmp_path: Path) -> None:
    payload = _valid_payload()
    payload["reviewer"] = "host-llm"
    payload["decisions"][0]["confidence"] = "medium"
    path = tmp_path / "critique_adjudication.yaml"

    write_adjudication(path, payload)
    loaded = load_adjudication(path)
    rewrite_path = tmp_path / "rewritten.yaml"
    write_adjudication(rewrite_path, loaded)

    rewritten = load_adjudication(rewrite_path)
    assert rewritten["reviewer"] == "host-llm"
    assert rewritten["decisions"][0]["confidence"] == "medium"


def test_writer_emits_reloadable_yaml(tmp_path: Path) -> None:
    path = tmp_path / "critique_adjudication.yaml"
    write_adjudication(path, _valid_payload())

    reloaded = load_adjudication(path)

    assert validate_adjudication(reloaded) == reloaded


@pytest.mark.parametrize("decision", ("apply", "resolved"))
def test_apply_and_resolved_require_patch_target_and_evidence(decision: str) -> None:
    payload = _valid_payload()
    payload["decisions"][0]["decision"] = decision
    payload["decisions"][0]["patch_target"] = ""
    payload["decisions"][0]["evidence"] = ""

    with pytest.raises(CritiqueAdjudicationError, match="patch_target"):
        validate_adjudication(payload)


def test_apply_requires_evidence_when_patch_target_is_present() -> None:
    payload = _valid_payload()
    payload["decisions"][0]["evidence"] = ""

    with pytest.raises(CritiqueAdjudicationError, match="evidence"):
        validate_adjudication(payload)


@pytest.mark.parametrize("decision", ("dismiss", "defer", "needs_human"))
def test_non_patch_decisions_allow_empty_patch_target_and_evidence(decision: str) -> None:
    payload = _valid_payload()
    payload["decisions"][0]["decision"] = decision
    payload["decisions"][0]["patch_target"] = ""
    payload["decisions"][0]["evidence"] = ""

    assert validate_adjudication(payload) == payload


def _write_critique_with_findings(fig_dir: Path, fixture: str = "demo_fig") -> Path:
    critique = fig_dir / "critique.md"
    critique.write_text(
        "---\n"
        "schema: figure-agent.critique.v1\n"
        f"fixture: {fixture}\n"
        "findings:\n"
        "  - id: C001\n"
        "    status: resolved\n"
        "    tex_lines: [10, 20]\n"
        "    observation: already repaired\n"
        "  - id: C002\n"
        "    status: open\n"
        "    tex_lines: [30, 35]\n"
        "    observation: needs review\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )
    return critique


def _complete_v1_1_audit_yaml() -> str:
    return (
        "audit_enumeration:\n"
        "  structural_completeness:\n"
        "    components:\n"
        "      - component: probe\n"
        "        mount_support: yes\n"
        "        rationale: visible shaft mount\n"
        "        connections: cable endpoint attaches to meter\n"
        "    missing_from_reference:\n"
        "      - element: sample stage\n"
        "        status: incomplete\n"
        "        rationale: standard support is absent\n"
        "  label_target_matching:\n"
        "    - label: polymer film\n"
        "      nearest_object: polymer band\n"
        "      intended_target: polymer film\n"
        "      matches: true\n"
        "      proposed_fix: \"\"\n"
        "  physical_plausibility:\n"
        "    - check: cable_gravity\n"
        "      finding: cable is schematic-straight consistently\n"
        "      verdict: convention_acceptable\n"
        "  conceptual_completeness:\n"
        "    - element: sample stage\n"
        "      reference: provided_reference\n"
        "      severity: MAJOR\n"
        "      proposed_action: add\n"
    )


def _write_v1_1_critique_with_audit(fig_dir: Path, audit_yaml: str) -> Path:
    critique = fig_dir / "critique.md"
    critique.write_text(
        "---\n"
        "schema: figure-agent.critique.v1.1\n"
        "fixture: demo_fig\n"
        f"{audit_yaml}"
        "findings:\n"
        "  - id: C001\n"
        "    status: open\n"
        "    tex_lines: [10, 20]\n"
        "    observation: needs review\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )
    return critique


def test_build_adjudication_scaffold_from_critique_frontmatter(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique = _write_critique_with_findings(fig_dir)

    with pytest.warns(DeprecationWarning, match="legacy"):
        scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["schema"] == "figure-agent.critique-adjudication.v1"
    assert scaffold["fixture"] == "demo_fig"
    assert scaffold["source_critique_hash"] == file_sha256(critique)
    assert scaffold["decisions"] == [
        {
            "finding_id": "C001",
            "decision": "resolved",
            "reason": "Critique marks C001 as resolved.",
            "patch_target": "examples/demo_fig/demo_fig.tex lines 10-20",
            "evidence": "critique.md marks C001 status resolved.",
        },
        {
            "finding_id": "C002",
            "decision": "needs_human",
            "reason": "Review C002 before selecting apply, dismiss, defer, or resolved.",
            "patch_target": "examples/demo_fig/demo_fig.tex lines 30-35",
            "evidence": "critique.md finding C002.",
        },
    ]
    assert validate_adjudication(scaffold) == scaffold


def test_build_adjudication_scaffold_accepts_v1_1_complete_audit(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique = _write_v1_1_critique_with_audit(fig_dir, _complete_v1_1_audit_yaml())

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)
    assert [decision["finding_id"] for decision in scaffold["decisions"]] == ["C001"]


def test_build_adjudication_scaffold_rejects_v1_1_missing_audit_block(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    audit_yaml = _complete_v1_1_audit_yaml().replace(
        "  physical_plausibility:\n"
        "    - check: cable_gravity\n"
        "      finding: cable is schematic-straight consistently\n"
        "      verdict: convention_acceptable\n",
        "",
    )
    _write_v1_1_critique_with_audit(fig_dir, audit_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="physical_plausibility"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_1_empty_audit_block(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    audit_yaml = _complete_v1_1_audit_yaml().replace(
        "  label_target_matching:\n"
        "    - label: polymer film\n"
        "      nearest_object: polymer band\n"
        "      intended_target: polymer film\n"
        "      matches: true\n"
        "      proposed_fix: \"\"\n",
        "  label_target_matching: []\n",
    )
    _write_v1_1_critique_with_audit(fig_dir, audit_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="label_target_matching"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_1_malformed_audit_item(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    audit_yaml = _complete_v1_1_audit_yaml().replace(
        "  physical_plausibility:\n"
        "    - check: cable_gravity\n"
        "      finding: cable is schematic-straight consistently\n"
        "      verdict: convention_acceptable\n",
        "  physical_plausibility:\n"
        "    - null\n",
    )
    _write_v1_1_critique_with_audit(fig_dir, audit_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="physical_plausibility"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_1_unbounded_reference(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    audit_yaml = _complete_v1_1_audit_yaml().replace(
        "      reference: provided_reference\n",
        "      reference: Smith et al. 2025\n",
    )
    _write_v1_1_critique_with_audit(fig_dir, audit_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="reference must be one of"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_unsupported_critique_schema(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique = _write_v1_1_critique_with_audit(fig_dir, _complete_v1_1_audit_yaml())
    critique.write_text(
        critique.read_text(encoding="utf-8").replace(
            "schema: figure-agent.critique.v1.1",
            "schema: figure-agent.critique.v9",
        ),
        encoding="utf-8",
    )

    with pytest.raises(CritiqueAdjudicationError, match="unsupported critique schema"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_includes_panel_findings(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    (fig_dir / "critique.md").write_text(
        "---\n"
        "schema: figure-agent.critique.v1\n"
        "fixture: demo_fig\n"
        "panels:\n"
        "  - id: A\n"
        "    findings:\n"
        "      - id: P001\n"
        "        status: open\n"
        "        tex_lines: [7, 9]\n"
        "findings:\n"
        "  - id: C001\n"
        "    status: open\n"
        "    tex_lines: [20, 25]\n"
        "---\n",
        encoding="utf-8",
    )

    with pytest.warns(DeprecationWarning, match="legacy"):
        scaffold = build_adjudication_scaffold(fig_dir)

    assert [decision["finding_id"] for decision in scaffold["decisions"]] == ["P001", "C001"]
    assert scaffold["decisions"][0]["patch_target"] == "examples/demo_fig/demo_fig.tex lines 7-9"


def test_scaffold_adjudication_writes_reloadable_yaml(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique_with_findings(fig_dir)

    with pytest.warns(DeprecationWarning, match="legacy"):
        path = scaffold_adjudication(fig_dir)

    assert path == fig_dir / "critique_adjudication.yaml"
    loaded = load_adjudication(path)
    assert loaded["fixture"] == "demo_fig"
    assert [decision["finding_id"] for decision in loaded["decisions"]] == ["C001", "C002"]


def test_scaffold_adjudication_refuses_to_overwrite_without_force(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique_with_findings(fig_dir)
    existing = fig_dir / "critique_adjudication.yaml"
    existing.write_text("keep me\n", encoding="utf-8")

    with pytest.raises(CritiqueAdjudicationError, match="already exists"):
        scaffold_adjudication(fig_dir)

    assert existing.read_text(encoding="utf-8") == "keep me\n"


def test_scaffold_adjudication_force_overwrites_existing_file(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique_with_findings(fig_dir)
    existing = fig_dir / "critique_adjudication.yaml"
    existing.write_text("replace me\n", encoding="utf-8")

    with pytest.warns(DeprecationWarning, match="legacy"):
        scaffold_adjudication(fig_dir, force=True)

    assert load_adjudication(existing)["fixture"] == "demo_fig"


def test_build_adjudication_scaffold_fails_cleanly_for_malformed_critique_yaml(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    (fig_dir / "critique.md").write_text(
        "---\n"
        "schema: [unterminated\n"
        "---\n",
        encoding="utf-8",
    )

    with pytest.raises(CritiqueAdjudicationError, match="invalid YAML"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_fails_when_critique_is_missing(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()

    with pytest.raises(CritiqueAdjudicationError, match="missing critique"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_non_list_findings(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    (fig_dir / "critique.md").write_text(
        "---\n"
        "schema: figure-agent.critique.v1\n"
        "fixture: demo_fig\n"
        "findings: C001\n"
        "---\n",
        encoding="utf-8",
    )

    with pytest.warns(DeprecationWarning, match="legacy"):
        with pytest.raises(CritiqueAdjudicationError, match="findings must be a list"):
            build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_finding_without_id(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    (fig_dir / "critique.md").write_text(
        "---\n"
        "schema: figure-agent.critique.v1\n"
        "fixture: demo_fig\n"
        "findings:\n"
        "  - status: open\n"
        "    tex_lines: [1, 2]\n"
        "---\n",
        encoding="utf-8",
    )

    with pytest.warns(DeprecationWarning, match="legacy"):
        with pytest.raises(CritiqueAdjudicationError, match="id must be a non-empty string"):
            build_adjudication_scaffold(fig_dir)


def test_cli_scaffold_writes_fixture_by_name(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fig_dir = tmp_path / "examples" / "demo_fig"
    fig_dir.mkdir(parents=True)
    _write_critique_with_findings(fig_dir)

    with pytest.warns(DeprecationWarning, match="legacy"):
        exit_code = main(["scaffold", "demo_fig", "--repo-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "wrote" in captured.out
    assert captured.err == ""
    assert load_adjudication(fig_dir / "critique_adjudication.yaml")["fixture"] == "demo_fig"


def test_cli_scaffold_reports_controlled_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "examples" / "demo_fig").mkdir(parents=True)

    exit_code = main(["scaffold", "demo_fig", "--repo-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "critique_adjudication.py: missing critique" in captured.err
