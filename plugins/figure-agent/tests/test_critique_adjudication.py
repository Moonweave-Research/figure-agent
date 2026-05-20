from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_adjudication import (  # noqa: E402
    CritiqueAdjudicationError,
    adjudication_is_stale,
    build_adjudication_scaffold,
    critique_finding_id,
    critique_findings,
    load_adjudication,
    load_critique_frontmatter,
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


def test_public_critique_reader_loads_frontmatter_and_findings(tmp_path: Path) -> None:
    critique_path = tmp_path / "critique.md"
    critique_path.write_text(
        "---\n"
        "schema: figure-agent.critique.v1\n"
        "fixture: demo_fig\n"
        "panels:\n"
        "  - id: A\n"
        "    findings:\n"
        "      - id: P001\n"
        "        status: open\n"
        "findings:\n"
        "  - id: C001\n"
        "    status: resolved\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )

    frontmatter = load_critique_frontmatter(critique_path)
    findings = critique_findings(frontmatter)
    finding_ids = [
        critique_finding_id(finding, f"critique finding {index}")
        for index, finding in enumerate(findings)
    ]

    assert frontmatter["fixture"] == "demo_fig"
    assert finding_ids == ["P001", "C001"]


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


def _quality_axis_yaml(
    name: str,
    *,
    verdict: str = "pass",
    confidence: str = "high",
    recommended_action: str = "none",
    blocking_items: tuple[str, ...] = (),
) -> str:
    blocking_yaml = (
        "[]"
        if not blocking_items
        else "\n" + "".join(f"      - {item}\n" for item in blocking_items).rstrip()
    )
    return (
        f"  {name}:\n"
        f"    verdict: {verdict}\n"
        f"    confidence: {confidence}\n"
        f"    rationale: {name} rationale\n"
        f"    evidence: {name} evidence\n"
        f"    blocking_items: {blocking_yaml}\n"
        f"    recommended_action: {recommended_action}\n"
    )


def _complete_v1_2_quality_axes_yaml(
    *,
    axis_overrides: dict[str, str] | None = None,
) -> str:
    axis_overrides = axis_overrides or {}
    parts = ["quality_axes:\n"]
    for axis_name in QUALITY_AXIS_NAMES:
        if axis_name in axis_overrides:
            parts.append(axis_overrides[axis_name])
            continue
        if axis_name == "panel_role_coherence":
            parts.append(
                "  panel_role_coherence:\n"
                "    verdict: pass\n"
                "    confidence: high\n"
                "    rationale: panel roles are coherent\n"
                "    evidence: panel A is setup\n"
                "    panel_roles:\n"
                "      - panel_id: A\n"
                "        role: setup\n"
                "        role_quality: clear\n"
                "        rationale: panel A introduces the apparatus\n"
                "    blocking_items: []\n"
                "    recommended_action: none\n"
            )
        elif axis_name == "publication_readiness":
            parts.append(
                _quality_axis_yaml(
                    "publication_readiness",
                    verdict="pass",
                    confidence="high",
                    recommended_action="none",
                )
            )
        else:
            parts.append(_quality_axis_yaml(axis_name))
    return "".join(parts)


def _journal_assessment_yaml(
    *,
    assessed_hash: str = "sha256:" + "a" * 64,
    level: str = "solid_manuscript",
    scoring_mode: str = "fresh_reaudit",
    gateable: str = "true",
) -> str:
    return (
        "journal_grade_assessment:\n"
        "  schema: figure-agent.journal-grade-assessment.v1\n"
        f"  scoring_mode: {scoring_mode}\n"
        f"  assessed_artifact_hash: {assessed_hash}\n"
        f"  benchmark_level: {level}\n"
        "  confidence: high\n"
        "  blockers: []\n"
        "  regression_detected: false\n"
        "  regressions: []\n"
        f"  score_is_gateable: {gateable}\n"
        "  next_quality_bottleneck: polish\n"
        "  rationale: current artifact is manuscript-ready but not high-impact\n"
    )


def _score_block_yaml(*, overall_score: float = 72) -> str:
    return (
        f"  overall_score: {overall_score}\n"
        "  sub_scores:\n"
        "    storyline: 78\n"
        "    composition: 70\n"
        "    component_fidelity: 55\n"
        "    scientific_plausibility: 82\n"
        "    label_semantics: 76\n"
        "    polish: 64\n"
        "    reference_fidelity: 80\n"
        "    export_scale_readability: 68\n"
        '  score_rationale: "current artifact only; not a progress score"\n'
    )


def _complete_v1_3_top_tier_audit_yaml() -> str:
    keys = (
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
    lines = ["top_tier_audit:"]
    for key in keys:
        lines.extend(
            [
                f"  {key}:",
                "    verdict: pass",
                f"    finding: {key} is acceptable for the current artifact",
                "    concrete_fix: accept_simplification",
                "    blocks_high_impact: false",
            ]
        )
    return "\n".join(lines) + "\n"


def _micro_defects_yaml(*, linked_finding_id: str = "C001", status: str = "open") -> str:
    return (
        "micro_defects:\n"
        "  - id: M001\n"
        "    crop: examples/demo_fig/build/audit_crops/full_q1.png\n"
        "    kind: wire_crosses_label\n"
        "    severity: MAJOR\n"
        "    observation: wire_crosses_label visible across the trap label\n"
        f"    linked_finding_id: \"{linked_finding_id}\"\n"
        f"    status: {status}\n"
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


def _write_v1_2_critique_with_quality_axes(
    fig_dir: Path,
    *,
    critique_schema: str = "figure-agent.critique.v1.2",
    audit_yaml: str | None = None,
    quality_axes_yaml: str | None = None,
    critique_input_hash: str | None = None,
    journal_assessment_yaml: str | None = None,
    extra_frontmatter_yaml: str = "",
    findings_yaml: str | None = None,
) -> Path:
    critique = fig_dir / "critique.md"
    findings_yaml = findings_yaml or (
        "findings:\n"
        "  - id: C001\n"
        "    status: open\n"
        "    tex_lines: [10, 20]\n"
        "    observation: needs review\n"
    )
    critique_hash_yaml = (
        f"critique_input_hash: {critique_input_hash}\n" if critique_input_hash else ""
    )
    critique.write_text(
        "---\n"
        f"schema: {critique_schema}\n"
        "fixture: demo_fig\n"
        f"{critique_hash_yaml}"
        f"{audit_yaml or _complete_v1_1_audit_yaml()}"
        f"{quality_axes_yaml or _complete_v1_2_quality_axes_yaml()}"
        f"{extra_frontmatter_yaml}"
        f"{journal_assessment_yaml or ''}"
        f"{findings_yaml}"
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


def test_build_adjudication_scaffold_accepts_v1_2_quality_axes(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique = _write_v1_2_critique_with_quality_axes(fig_dir)

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)
    assert [decision["finding_id"] for decision in scaffold["decisions"]] == ["C001"]


def test_build_adjudication_scaffold_accepts_v1_2_fresh_reaudit_assessment(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        journal_assessment_yaml=_journal_assessment_yaml(assessed_hash=critique_hash),
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)


def test_build_adjudication_scaffold_accepts_v1_2_journal_score_block(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        journal_assessment_yaml=(
            _journal_assessment_yaml(assessed_hash=critique_hash) + _score_block_yaml()
        ),
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)


def test_build_adjudication_scaffold_accepts_v1_3_top_tier_audit(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        extra_frontmatter_yaml=_complete_v1_3_top_tier_audit_yaml(),
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)


def test_build_adjudication_scaffold_accepts_v1_4_micro_defects(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        extra_frontmatter_yaml=_complete_v1_3_top_tier_audit_yaml() + _micro_defects_yaml(),
        findings_yaml=(
            "findings:\n"
            "  - id: C001\n"
            "    status: open\n"
            "    tex_lines: [10, 20]\n"
            "    observation: wire_crosses_label caused by lead crossing the label\n"
        ),
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)


def test_build_adjudication_scaffold_accepts_v1_4_empty_micro_defects(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        extra_frontmatter_yaml=_complete_v1_3_top_tier_audit_yaml() + "micro_defects: []\n",
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)


def test_build_adjudication_scaffold_rejects_v1_4_missing_micro_defects(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        extra_frontmatter_yaml=_complete_v1_3_top_tier_audit_yaml(),
    )

    with pytest.raises(CritiqueAdjudicationError, match="micro_defects"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_4_invalid_micro_defect_kind(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        extra_frontmatter_yaml=(
            _complete_v1_3_top_tier_audit_yaml()
            + _micro_defects_yaml().replace("kind: wire_crosses_label", "kind: vague")
        ),
    )

    with pytest.raises(CritiqueAdjudicationError, match="kind"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_4_major_micro_defect_without_link(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        extra_frontmatter_yaml=(
            _complete_v1_3_top_tier_audit_yaml()
            + _micro_defects_yaml(linked_finding_id="")
        ),
    )

    with pytest.raises(CritiqueAdjudicationError, match="linked_finding_id"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_accepts_v1_4_major_micro_defect_simplification(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.4",
        extra_frontmatter_yaml=(
            _complete_v1_3_top_tier_audit_yaml()
            + _micro_defects_yaml(linked_finding_id="", status="accept_simplification")
        ),
        findings_yaml="findings: []\n",
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)


def test_build_adjudication_scaffold_rejects_v1_3_missing_top_tier_audit(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
    )

    with pytest.raises(CritiqueAdjudicationError, match="top_tier_audit"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_3_invalid_top_tier_verdict(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    top_tier_yaml = _complete_v1_3_top_tier_audit_yaml().replace(
        "    verdict: pass\n",
        "    verdict: perfect\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        extra_frontmatter_yaml=top_tier_yaml,
    )

    with pytest.raises(CritiqueAdjudicationError, match="verdict"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_3_empty_top_tier_finding(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    top_tier_yaml = _complete_v1_3_top_tier_audit_yaml().replace(
        "    finding: first_glance_message is acceptable for the current artifact\n",
        "    finding: \"\"\n",
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        extra_frontmatter_yaml=top_tier_yaml,
    )

    with pytest.raises(CritiqueAdjudicationError, match="finding"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_3_blocking_top_tier_without_finding(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    top_tier_yaml = (
        _complete_v1_3_top_tier_audit_yaml()
        .replace(
            "    verdict: pass\n"
            "    finding: first_glance_message is acceptable for the current artifact\n"
            "    concrete_fix: accept_simplification\n",
            "    verdict: fail\n"
            "    finding: first-glance message is absent\n"
            "    concrete_fix: add a dominant first-glance claim cue\n",
            1,
        )
        .replace("    blocks_high_impact: false\n", "    blocks_high_impact: true\n", 1)
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        extra_frontmatter_yaml=top_tier_yaml,
        findings_yaml="findings: []\n",
    )

    with pytest.raises(CritiqueAdjudicationError, match="top_tier_audit"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_3_needs_human_top_tier_without_link(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    top_tier_yaml = _complete_v1_3_top_tier_audit_yaml().replace(
        "    verdict: pass\n"
        "    finding: first_glance_message is acceptable for the current artifact\n"
        "    concrete_fix: accept_simplification\n",
        "    verdict: needs_human\n"
        "    finding: first-glance message needs target-journal art direction\n"
        "    concrete_fix: ask human to choose the intended first-glance message\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        extra_frontmatter_yaml=top_tier_yaml,
        findings_yaml="findings: []\n",
    )

    with pytest.raises(CritiqueAdjudicationError, match="first_glance_message"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_3_weak_blocker_without_link(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    top_tier_yaml = (
        _complete_v1_3_top_tier_audit_yaml()
        .replace(
            "    verdict: pass\n"
            "    finding: first_glance_message is acceptable for the current artifact\n"
            "    concrete_fix: accept_simplification\n",
            "    verdict: weak\n"
            "    finding: first-glance message is visible but not high-impact\n"
            "    concrete_fix: strengthen the first-glance visual hierarchy\n",
            1,
        )
        .replace("    blocks_high_impact: false\n", "    blocks_high_impact: true\n", 1)
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        extra_frontmatter_yaml=top_tier_yaml,
        findings_yaml="findings: []\n",
    )

    with pytest.raises(CritiqueAdjudicationError, match="first_glance_message"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_3_blocking_top_tier_with_unrelated_finding(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    top_tier_yaml = (
        _complete_v1_3_top_tier_audit_yaml()
        .replace(
            "    verdict: pass\n"
            "    finding: first_glance_message is acceptable for the current artifact\n"
            "    concrete_fix: accept_simplification\n",
            "    verdict: fail\n"
            "    finding: first-glance message is absent\n"
            "    concrete_fix: add a dominant first-glance claim cue\n",
            1,
        )
        .replace("    blocks_high_impact: false\n", "    blocks_high_impact: true\n", 1)
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        extra_frontmatter_yaml=top_tier_yaml,
        findings_yaml=(
            "findings:\n"
            "  - id: C999\n"
            "    status: open\n"
            "    tex_lines: [10, 20]\n"
            "    observation: unrelated label offset needs review\n"
        ),
    )

    with pytest.raises(CritiqueAdjudicationError, match="first_glance_message"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_accepts_v1_3_top_tier_linked_finding(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    top_tier_yaml = (
        _complete_v1_3_top_tier_audit_yaml()
        .replace("    verdict: pass\n", "    verdict: fail\n", 1)
        .replace("    blocks_high_impact: false\n", "    blocks_high_impact: true\n", 1)
    )
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        extra_frontmatter_yaml=top_tier_yaml,
        findings_yaml=(
            "findings:\n"
            "  - id: C001\n"
            "    status: open\n"
            "    tex_lines: [10, 20]\n"
            "    observation: top_tier_audit.first_glance_message fails because the "
            "main claim is invisible\n"
        ),
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)


def test_build_adjudication_scaffold_accepts_v1_3_top_tier_quality_axis_link(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    top_tier_yaml = _complete_v1_3_top_tier_audit_yaml().replace(
        "    verdict: pass\n",
        "    verdict: needs_human\n",
        1,
    )
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="needs_human",
                recommended_action="human_review",
                blocking_items=(
                    "top_tier_audit.first_glance_message needs target-journal decision",
                ),
            )
        }
    )
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        quality_axes_yaml=quality_axes_yaml,
        extra_frontmatter_yaml=top_tier_yaml,
        findings_yaml="findings: []\n",
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)


def test_build_adjudication_scaffold_accepts_v1_3_accept_simplification_link_exception(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    top_tier_yaml = _complete_v1_3_top_tier_audit_yaml().replace(
        "    verdict: pass\n"
        "    finding: first_glance_message is acceptable for the current artifact\n"
        "    concrete_fix: accept_simplification\n"
        "    blocks_high_impact: false\n",
        "    verdict: needs_human\n"
        "    finding: first-glance story depends on target-journal art direction\n"
        "    concrete_fix: \"accept_simplification: keep current schematic until target "
        "journal is known\"\n"
        "    blocks_high_impact: false\n",
        1,
    )
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        extra_frontmatter_yaml=top_tier_yaml,
        findings_yaml="findings: []\n",
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)


def test_build_adjudication_scaffold_rejects_v1_3_high_impact_with_weak_top_tier(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    top_tier_yaml = (
        _complete_v1_3_top_tier_audit_yaml()
        .replace("    verdict: pass\n", "    verdict: weak\n", 1)
        .replace("    blocks_high_impact: false\n", "    blocks_high_impact: true\n", 1)
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_schema="figure-agent.critique.v1.3",
        critique_input_hash=critique_hash,
        extra_frontmatter_yaml=top_tier_yaml,
        journal_assessment_yaml=_journal_assessment_yaml(
            assessed_hash=critique_hash,
            level="high_impact_candidate",
        ),
    )

    with pytest.raises(CritiqueAdjudicationError, match="high_impact_candidate"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_out_of_range_overall_score(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        journal_assessment_yaml=(
            _journal_assessment_yaml(assessed_hash=critique_hash)
            + _score_block_yaml(overall_score=101)
        ),
    )

    with pytest.raises(CritiqueAdjudicationError, match="overall_score"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_out_of_range_sub_score(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    score_yaml = _score_block_yaml().replace("    polish: 64\n", "    polish: -1\n")
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        journal_assessment_yaml=_journal_assessment_yaml(assessed_hash=critique_hash)
        + score_yaml,
    )

    with pytest.raises(CritiqueAdjudicationError, match="sub_scores.polish"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_boolean_score(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    score_yaml = _score_block_yaml().replace("  overall_score: 72\n", "  overall_score: true\n")
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        journal_assessment_yaml=_journal_assessment_yaml(assessed_hash=critique_hash)
        + score_yaml,
    )

    with pytest.raises(CritiqueAdjudicationError, match="overall_score"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_empty_score_rationale(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    score_yaml = _score_block_yaml().replace(
        '  score_rationale: "current artifact only; not a progress score"\n',
        '  score_rationale: ""\n',
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        journal_assessment_yaml=_journal_assessment_yaml(assessed_hash=critique_hash)
        + score_yaml,
    )

    with pytest.raises(CritiqueAdjudicationError, match="score_rationale"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_partial_score_block(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        journal_assessment_yaml=(
            _journal_assessment_yaml(assessed_hash=critique_hash) + "  overall_score: 72\n"
        ),
    )

    with pytest.raises(CritiqueAdjudicationError, match="score block"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_missing_sub_score_key(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    score_yaml = _score_block_yaml().replace("    polish: 64\n", "")
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        journal_assessment_yaml=_journal_assessment_yaml(assessed_hash=critique_hash)
        + score_yaml,
    )

    with pytest.raises(CritiqueAdjudicationError, match="sub_scores"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_extra_sub_score_key(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    score_yaml = _score_block_yaml().replace(
        "    export_scale_readability: 68\n",
        "    export_scale_readability: 68\n    typography: 90\n",
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        journal_assessment_yaml=_journal_assessment_yaml(assessed_hash=critique_hash)
        + score_yaml,
    )

    with pytest.raises(CritiqueAdjudicationError, match="sub_scores"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_allows_high_score_without_level_promotion(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        journal_assessment_yaml=(
            _journal_assessment_yaml(assessed_hash=critique_hash, level="draft")
            + _score_block_yaml(overall_score=95)
        ),
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)


def test_build_adjudication_scaffold_allows_lower_score_after_regression(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    assessment_yaml = _journal_assessment_yaml(
        assessed_hash=critique_hash,
        level="draft",
    ).replace(
        "  regression_detected: false\n"
        "  regressions: []\n",
        "  regression_detected: true\n"
        "  regressions:\n"
        "    - axis: polish\n"
        '      previous_state: "72"\n'
        '      current_state: "58"\n'
        '      reason: "patch made label balance worse"\n',
    )
    critique = _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        journal_assessment_yaml=assessment_yaml + _score_block_yaml(overall_score=58),
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["source_critique_hash"] == file_sha256(critique)


def test_build_adjudication_scaffold_rejects_invalid_assessment_scoring_mode(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        journal_assessment_yaml=_journal_assessment_yaml(
            assessed_hash=critique_hash,
            scoring_mode="cumulative_progress",
        ),
    )

    with pytest.raises(CritiqueAdjudicationError, match="scoring_mode"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_gateable_assessment_hash_mismatch(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash="sha256:" + "a" * 64,
        journal_assessment_yaml=_journal_assessment_yaml(
            assessed_hash="sha256:" + "b" * 64,
        ),
    )

    with pytest.raises(CritiqueAdjudicationError, match="assessed_artifact_hash"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_high_impact_with_upstream_patch(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    critique_hash = "sha256:" + "a" * 64
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "journal_polish": _quality_axis_yaml(
                "journal_polish",
                verdict="needs_patch",
                recommended_action="patch",
                blocking_items=("C001 - export-scale polish still weak",),
            ),
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="needs_patch",
                recommended_action="patch",
                blocking_items=("C001 - export-scale polish still weak",),
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        critique_input_hash=critique_hash,
        quality_axes_yaml=quality_axes_yaml,
        journal_assessment_yaml=_journal_assessment_yaml(
            assessed_hash=critique_hash,
            level="high_impact_candidate",
        ),
    )

    with pytest.raises(CritiqueAdjudicationError, match="high_impact_candidate"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_missing_quality_axis(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        _quality_axis_yaml("journal_polish"),
        "",
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="journal_polish"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_invalid_verdict(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "    verdict: pass\n",
        "    verdict: excellent\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="verdict"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_invalid_confidence(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "    confidence: high\n",
        "    confidence: certain\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="confidence"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_invalid_recommended_action(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "    recommended_action: none\n",
        "    recommended_action: auto_fix\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="recommended_action"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_non_list_blocking_items(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "    blocking_items: []\n",
        "    blocking_items: hidden issue\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="blocking_items"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_empty_evidence_for_pass(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "    evidence: message_storyline evidence\n",
        "    evidence: \"\"\n",
        1,
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="evidence"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_patch_without_blocking_item(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "composition_layout": _quality_axis_yaml(
                "composition_layout",
                verdict="needs_patch",
                recommended_action="patch",
                blocking_items=(),
            )
        }
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="blocking_items"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_action_conflict(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "scientific_plausibility": _quality_axis_yaml(
                "scientific_plausibility",
                verdict="needs_human",
                recommended_action="patch",
                blocking_items=("Mechanism requires domain review.",),
            )
        }
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="recommended_action"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_readiness_less_severe_than_axis(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "journal_polish": _quality_axis_yaml(
                "journal_polish",
                verdict="block",
                recommended_action="block_release",
                blocking_items=("Export-scale text is unreadable.",),
            ),
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="pass",
                recommended_action="none",
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="publication_readiness"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_readiness_not_applicable_with_axes(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="not_applicable",
                recommended_action="none",
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="publication_readiness"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_invalid_panel_role(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "        role: setup\n",
        "        role: decoration\n",
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="panel_roles"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_empty_panel_roles(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "    panel_roles:\n"
        "      - panel_id: A\n"
        "        role: setup\n"
        "        role_quality: clear\n"
        "        rationale: panel A introduces the apparatus\n",
        "    panel_roles: []\n",
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="panel_roles"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_panel_role_without_panel_id(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "      - panel_id: A\n",
        "      -\n",
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="panel_id"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_panel_role_without_rationale(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml().replace(
        "        rationale: panel A introduces the apparatus\n",
        "",
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="rationale"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_patch_axis_without_finding(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "message_storyline": _quality_axis_yaml(
                "message_storyline",
                verdict="needs_patch",
                recommended_action="patch",
                blocking_items=("Story bridge is missing.",),
            ),
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="needs_patch",
                recommended_action="revise_briefing",
                blocking_items=("Story bridge is missing.",),
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        quality_axes_yaml=quality_axes_yaml,
        findings_yaml="findings: []\n",
    )

    with pytest.raises(CritiqueAdjudicationError, match="findings"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_allows_v1_2_non_patch_axis_without_finding(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "message_storyline": _quality_axis_yaml(
                "message_storyline",
                verdict="needs_patch",
                recommended_action="revise_briefing",
                blocking_items=("Story bridge needs clearer briefing.",),
            ),
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="needs_patch",
                recommended_action="revise_briefing",
                blocking_items=("Story bridge needs clearer briefing.",),
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        quality_axes_yaml=quality_axes_yaml,
        findings_yaml="findings: []\n",
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["decisions"] == []


def test_build_adjudication_scaffold_rejects_v1_2_patch_axis_unlinked_to_finding(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "message_storyline": _quality_axis_yaml(
                "message_storyline",
                verdict="needs_patch",
                recommended_action="patch",
                blocking_items=("Story bridge is missing.",),
            ),
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="needs_patch",
                recommended_action="revise_briefing",
                blocking_items=("Story bridge is missing.",),
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="message_storyline"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_accepts_v1_2_patch_axis_linked_to_finding(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "message_storyline": _quality_axis_yaml(
                "message_storyline",
                verdict="needs_patch",
                recommended_action="patch",
                blocking_items=("C001 - Story bridge is missing.",),
            ),
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="needs_patch",
                recommended_action="revise_briefing",
                blocking_items=("Story bridge is missing.",),
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    scaffold = build_adjudication_scaffold(fig_dir)

    assert [decision["finding_id"] for decision in scaffold["decisions"]] == ["C001"]


def test_build_adjudication_scaffold_rejects_v1_2_near_miss_finding_id_link(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "message_storyline": _quality_axis_yaml(
                "message_storyline",
                verdict="needs_patch",
                recommended_action="patch",
                blocking_items=("C0010 - Story bridge is missing.",),
            ),
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="needs_patch",
                recommended_action="revise_briefing",
                blocking_items=("Story bridge is missing.",),
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="message_storyline"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_block_release_without_finding(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "journal_polish": _quality_axis_yaml(
                "journal_polish",
                verdict="block",
                recommended_action="block_release",
                blocking_items=("Export-scale text is unreadable.",),
            ),
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="block",
                recommended_action="block_release",
                blocking_items=("Export-scale text is unreadable.",),
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        quality_axes_yaml=quality_axes_yaml,
        findings_yaml="findings: []\n",
    )

    with pytest.raises(CritiqueAdjudicationError, match="findings"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_rejects_v1_2_block_release_unlinked_to_finding(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "journal_polish": _quality_axis_yaml(
                "journal_polish",
                verdict="block",
                recommended_action="block_release",
                blocking_items=("Export-scale text is unreadable.",),
            ),
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="block",
                recommended_action="block_release",
                blocking_items=("C001 - Export-scale text is unreadable.",),
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(fig_dir, quality_axes_yaml=quality_axes_yaml)

    with pytest.raises(CritiqueAdjudicationError, match="journal_polish"):
        build_adjudication_scaffold(fig_dir)


def test_build_adjudication_scaffold_allows_v1_2_human_review_block_without_finding(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    quality_axes_yaml = _complete_v1_2_quality_axes_yaml(
        axis_overrides={
            "journal_polish": _quality_axis_yaml(
                "journal_polish",
                verdict="block",
                recommended_action="human_review",
                blocking_items=("Domain reviewer must approve the simplification.",),
            ),
            "publication_readiness": _quality_axis_yaml(
                "publication_readiness",
                verdict="block",
                recommended_action="human_review",
                blocking_items=("Domain reviewer must approve the simplification.",),
            ),
        }
    )
    _write_v1_2_critique_with_quality_axes(
        fig_dir,
        quality_axes_yaml=quality_axes_yaml,
        findings_yaml="findings: []\n",
    )

    scaffold = build_adjudication_scaffold(fig_dir)

    assert scaffold["decisions"] == []


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
