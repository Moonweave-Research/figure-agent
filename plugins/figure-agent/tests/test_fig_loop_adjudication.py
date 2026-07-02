from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from critique_adjudication import write_adjudication  # noqa: E402
from fig_loop_adjudication import adjudication_state  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402

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


def _write_valid_adjudication(example_dir: Path, critique_hash: str) -> None:
    write_adjudication(
        example_dir / "critique_adjudication.yaml",
        {
            "schema": "figure-agent.critique-adjudication.v1",
            "fixture": example_dir.name,
            "source_critique_hash": critique_hash,
            "decisions": [
                {
                    "finding_id": "C001",
                    "decision": "defer",
                    "reason": "requires visual confirmation",
                }
            ],
        },
    )


def _quality_axis_yaml(name: str) -> str:
    panel_roles = ""
    if name == "panel_role_coherence":
        panel_roles = (
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
        f"{panel_roles}"
        "    blocking_items: []\n"
        "    recommended_action: none\n"
    )


def _write_v1_4_critique_without_print_scale_evidence(example_dir: Path) -> Path:
    quality_axes = "quality_axes:\n" + "".join(
        _quality_axis_yaml(name) for name in QUALITY_AXIS_NAMES
    )
    top_tier_audit = ["top_tier_audit:"]
    for key in TOP_TIER_KEYS:
        top_tier_audit.extend(
            [
                f"  {key}:",
                "    verdict: pass",
                f"    finding: {key} finding",
                "    concrete_fix: accept_simplification",
                "    blocks_high_impact: false",
            ]
        )
    critique = example_dir / "critique.md"
    critique.write_text(
        "---\n"
        "schema: figure-agent.critique.v1.10\n"
        f"fixture: {example_dir.name}\n"
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
        f"{quality_axes}"
        f"{'\n'.join(top_tier_audit)}\n"
        "micro_defects: []\n"
        "findings: []\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )
    return critique


def test_adjudication_state_reports_missing_file(tmp_path: Path) -> None:
    state = adjudication_state(tmp_path)

    assert state == {
        "state": "missing",
        "path": str(tmp_path / "critique_adjudication.yaml"),
        "decision_count": 0,
    }


def test_adjudication_state_reports_fresh_adjudication(tmp_path: Path) -> None:
    critique = tmp_path / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_valid_adjudication(tmp_path, file_sha256(critique))

    state = adjudication_state(tmp_path)

    assert state["state"] == "fresh"
    assert state["decision_count"] == 1
    assert state["decisions"][0]["finding_id"] == "C001"
    assert state["source_critique_hash"] == file_sha256(critique)


def test_adjudication_state_reports_stale_hash(tmp_path: Path) -> None:
    critique = tmp_path / "critique.md"
    critique.write_text("# critique v1\n", encoding="utf-8")
    _write_valid_adjudication(tmp_path, file_sha256(critique))
    critique.write_text("# critique v2\n", encoding="utf-8")

    state = adjudication_state(tmp_path)

    assert state["state"] == "stale"
    assert state["decision_count"] == 1


def test_adjudication_state_reports_invalid_without_traceback(tmp_path: Path) -> None:
    (tmp_path / "critique_adjudication.yaml").write_text(
        "schema: [unterminated\n",
        encoding="utf-8",
    )

    state = adjudication_state(tmp_path)

    assert state["state"] == "invalid"
    assert state["decision_count"] == 0
    assert "invalid YAML" in state["error"]


def test_adjudication_state_reports_invalid_when_critique_fails_evidence_lint(
    tmp_path: Path,
) -> None:
    critique = _write_v1_4_critique_without_print_scale_evidence(tmp_path)
    _write_valid_adjudication(tmp_path, file_sha256(critique))

    state = adjudication_state(tmp_path)

    assert state["state"] == "invalid"
    assert state["decision_count"] == 0
    assert "print-scale audit evidence" in state["error"]
