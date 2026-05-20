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


def _quality_axis_yaml(name: str) -> str:
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
        "    verdict: pass\n"
        "    confidence: high\n"
        f"    rationale: {name} passes\n"
        f"    evidence: {name} evidence\n"
        f"{extra}"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
    )


def _quality_axes_yaml() -> str:
    return "quality_axes:\n" + "".join(_quality_axis_yaml(name) for name in QUALITY_AXIS_NAMES)


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


def _write_critique(
    fig_dir: Path,
    *,
    findings_yaml: str,
    top_tier_yaml: str | None = None,
) -> Path:
    critique = fig_dir / "critique.md"
    critique.write_text(
        "---\n"
        "schema: figure-agent.critique.v1.3\n"
        "fixture: demo_fig\n"
        f"{_audit_enumeration_yaml()}"
        f"{_quality_axes_yaml()}"
        f"{top_tier_yaml or _top_tier_yaml()}"
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


def test_lint_critique_uses_public_adjudication_api_only() -> None:
    source = Path(critique_lint.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    private_imports: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != "critique_adjudication":
            continue
        private_imports.extend(alias.name for alias in node.names if alias.name.startswith("_"))

    assert private_imports == []


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
