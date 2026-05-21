from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import critique_lint  # noqa: E402

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

TOP_TIER_KEYS = (
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


def _quote_yaml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _quality_axis_yaml(
    name: str,
    *,
    evidence: str | None = None,
    verdict: str = "pass",
) -> str:
    extra = ""
    if name == "panel_role_coherence":
        extra = (
            "    panel_roles:\n"
            "      - panel_id: A\n"
            "        role: setup\n"
            "        role_quality: clear\n"
            "        rationale: panel A establishes context\n"
        )
    return (
        f"  {name}:\n"
        f"    verdict: {verdict}\n"
        "    confidence: high\n"
        f"    rationale: {name} passes\n"
        f"    evidence: {_quote_yaml_string(evidence or f'{name} evidence')}\n"
        f"{extra}"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
    )


def _quality_axes_yaml(
    *,
    journal_polish_evidence: str | None = None,
    publication_readiness_evidence: str | None = None,
) -> str:
    evidence_by_axis = {
        "journal_polish": journal_polish_evidence,
        "publication_readiness": publication_readiness_evidence,
    }
    return "quality_axes:\n" + "".join(
        _quality_axis_yaml(name, evidence=evidence_by_axis.get(name))
        for name in QUALITY_AXIS_NAMES
    )


def _audit_enumeration_yaml() -> str:
    return (
        "audit_enumeration:\n"
        "  structural_completeness:\n"
        "    components:\n"
        "      - component: apparatus\n"
        "        mount_support: yes\n"
        "        rationale: support is visible\n"
        "    missing_from_reference:\n"
        "      - element: stage\n"
        "        status: intentional_omission\n"
        "        rationale: simplified schematic\n"
        "  label_target_matching:\n"
        "    - label: Apparatus\n"
        "      nearest_object: apparatus\n"
        "      intended_target: apparatus\n"
        "      matches: true\n"
        "  physical_plausibility:\n"
        "    - check: floating_components\n"
        "      finding: no floating components\n"
        "      verdict: convention_acceptable\n"
        "  conceptual_completeness:\n"
        "    - element: apparatus\n"
        "      reference: briefing\n"
        "      severity: MINOR\n"
        "      proposed_action: accept_simplification\n"
    )


def _top_tier_yaml(*, first_verdict: str = "pass", first_fix: str = "accept_simplification") -> str:
    lines = ["top_tier_audit:"]
    for key in TOP_TIER_KEYS:
        verdict = first_verdict if key == "first_glance_message" else "pass"
        fix = first_fix if key == "first_glance_message" else "accept_simplification"
        lines.extend(
            [
                f"  {key}:",
                f"    verdict: {verdict}",
                f"    finding: {key} finding",
                f"    concrete_fix: {fix}",
                "    blocks_high_impact: false",
            ]
        )
    return "\n".join(lines) + "\n"


def _editorial_yaml(*, hero_verdict: str = "pass", hero_fix: str = "accept_simplification") -> str:
    keys = (
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
    lines = ["editorial_art_direction:"]
    for key in keys:
        verdict = hero_verdict if key == "hero_focus" else "pass"
        fix = hero_fix if key == "hero_focus" else "accept_simplification"
        lines.extend(
            [
                f"  {key}:",
                f"    verdict: {verdict}",
                f"    evidence: {key} evidence",
                f"    rationale: {key} rationale",
                f"    concrete_fix: {_quote_yaml_string(fix)}",
                "    blocks_high_impact: false",
            ]
        )
        if key == "tikz_vs_svg_polish_trigger":
            lines.append("    recommended_path: continue_tikz")
    return "\n".join(lines) + "\n"


def _write_critique(
    fig_dir: Path,
    *,
    findings_yaml: str,
    schema: str = "figure-agent.critique.v1.3",
    micro_defects_yaml: str = "",
    top_tier_yaml: str | None = None,
    editorial_yaml: str = "",
    journal_polish_evidence: str | None = None,
    publication_readiness_evidence: str | None = None,
) -> Path:
    critique = fig_dir / "critique.md"
    quality_axes = _quality_axes_yaml(
        journal_polish_evidence=journal_polish_evidence,
        publication_readiness_evidence=publication_readiness_evidence,
    )
    critique.write_text(
        "---\n"
        f"schema: {schema}\n"
        "fixture: demo_fig\n"
        f"{_audit_enumeration_yaml()}"
        f"{quality_axes}"
        f"{top_tier_yaml or _top_tier_yaml()}"
        f"{micro_defects_yaml}"
        f"{editorial_yaml}"
        f"{findings_yaml}"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )
    return critique


def test_lint_critique_accepts_valid_v1_3_critique(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        findings_yaml=(
            "findings:\n"
            "  - id: C001\n"
            "    status: open\n"
            "    tex_lines: [10, 20]\n"
            "    observation: ordinary finding\n"
        ),
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_accepts_valid_v1_4_micro_defect_critique(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.4",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/full_q1.png\n"
            "    kind: line_crosses_label\n"
            "    severity: MAJOR\n"
            "    observation: line_crosses_label is visible in the crop\n"
            "    linked_finding_id: C001\n"
            "    status: open\n"
        ),
        findings_yaml=(
            "findings:\n"
            "  - id: C001\n"
            "    status: open\n"
            "    tex_lines: [10, 20]\n"
            "    observation: line_crosses_label in high-zoom crop\n"
        ),
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_accepts_valid_v1_5_editorial_art_direction(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.5",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml="micro_defects: []\n",
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_rejects_unlinked_v1_6_instrument_label_micro_defect(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.6",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/panel_E_s01.png\n"
            "    kind: label_backdrop_overflows_outline\n"
            "    severity: MAJOR\n"
            "    observation: HV+ backdrop extends below the instrument outline\n"
            "    linked_finding_id: \"\"\n"
            "    status: open\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["critique_contract"]
    assert "linked_finding_id" in violations[0].message


def test_lint_critique_reports_v1_5_passed_polish_without_print_scale_evidence(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.5",
        micro_defects_yaml="micro_defects: []\n",
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == [
        "audit_evidence",
        "audit_evidence",
    ]
    assert "journal_polish" in violations[0].message
    assert "publication_readiness" in violations[1].message


def test_lint_critique_reports_v1_5_needs_human_editorial_without_link(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.5",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml="micro_defects: []\n",
        editorial_yaml=_editorial_yaml(
            hero_verdict="needs_human",
            hero_fix="accept_simplification: leave hero focus unresolved",
        ),
        findings_yaml="findings: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["critique_contract"]
    assert "hero_focus" in violations[0].message


def test_lint_critique_reports_missing_v1_4_micro_defects(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.4",
        findings_yaml=(
            "findings:\n"
            "  - id: C001\n"
            "    status: open\n"
            "    tex_lines: [10, 20]\n"
            "    observation: ordinary finding\n"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["critique_contract"]
    assert "micro_defects" in violations[0].message


def test_lint_critique_reports_passed_polish_without_print_scale_evidence(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.4",
        micro_defects_yaml="micro_defects: []\n",
        findings_yaml="findings: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == [
        "audit_evidence",
        "audit_evidence",
    ]
    assert "journal_polish" in violations[0].message
    assert "print-scale" in violations[0].message
    assert "publication_readiness" in violations[1].message


def test_lint_critique_accepts_passed_polish_with_print_scale_evidence(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.4",
        micro_defects_yaml="micro_defects: []\n",
        findings_yaml="findings: []\n",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_uses_public_adjudication_api_only() -> None:
    source = Path(critique_lint.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    private_imports: list[str] = []
    adjudication_reader_imports: list[str] = []
    contract_imports: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module == "critique_adjudication":
            private_imports.extend(alias.name for alias in node.names if alias.name.startswith("_"))
            adjudication_reader_imports.extend(
                alias.name
                for alias in node.names
                if alias.name
                in {"critique_finding_id", "critique_findings", "load_critique_frontmatter"}
            )
        if node.module == "critique_contract":
            contract_imports.update(alias.name for alias in node.names)

    assert private_imports == []
    assert adjudication_reader_imports == []
    assert {
        "CritiqueContractError",
        "critique_finding_id",
        "critique_findings",
        "load_critique_frontmatter",
    } <= contract_imports


def test_lint_critique_reports_duplicate_finding_ids(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        findings_yaml=(
            "panels:\n"
            "  - id: A\n"
            "    findings:\n"
            "      - id: P001\n"
            "        status: open\n"
            "        observation: panel finding\n"
            "findings:\n"
            "  - id: P001\n"
            "    status: open\n"
            "    observation: duplicate top-level finding\n"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["duplicate_finding_id"]
    assert "P001" in violations[0].message


def test_lint_critique_reports_malformed_finding_ids_without_traceback(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        findings_yaml=(
            "findings:\n"
            "  - status: open\n"
            "    observation: missing id\n"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["critique_contract"]
    assert "id must be a non-empty string" in violations[0].message


def test_lint_critique_reports_contract_validation_errors(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        top_tier_yaml=_top_tier_yaml(
            first_verdict="needs_human",
            first_fix="ask human for first-glance art direction",
        ),
        findings_yaml="findings: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["critique_contract"]
    assert "first_glance_message" in violations[0].message


def test_lint_critique_cli_returns_nonzero_for_violations(
    tmp_path: Path, capsys
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        findings_yaml=(
            "findings:\n"
            "  - id: C001\n"
            "    status: open\n"
            "    observation: first\n"
            "  - id: C001\n"
            "    status: open\n"
            "    observation: duplicate\n"
        ),
    )

    result = critique_lint.main([str(fig_dir)])

    captured = capsys.readouterr()
    assert result == 1
    assert "duplicate_finding_id" in captured.out


def test_lint_critique_cli_reports_malformed_findings_without_traceback(
    tmp_path: Path, capsys
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        findings_yaml=(
            "findings:\n"
            "  - status: open\n"
            "    observation: missing id\n"
        ),
    )

    result = critique_lint.main([str(fig_dir)])

    captured = capsys.readouterr()
    assert result == 1
    assert "critique_contract" in captured.out
    assert "Traceback" not in captured.err
