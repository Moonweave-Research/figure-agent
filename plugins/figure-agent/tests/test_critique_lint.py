from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import critique_lint  # noqa: E402
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
    crop_audit_log_yaml: str = "",
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
        f"{crop_audit_log_yaml}"
        f"{editorial_yaml}"
        f"{findings_yaml}"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )
    return critique


def _write_visual_clash_report(fig_dir: Path, *, candidate_ids: tuple[str, ...]) -> Path:
    report = fig_dir / "build" / "visual_clash.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "fixture": fig_dir.name,
                "render_pdf": f"build/{fig_dir.name}.pdf",
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "text_on_path",
                        "text": f"label {candidate_id}",
                        "bbox_px": [index, index + 1, index + 2, index + 3],
                        "metric": {"dark": 0.04},
                        "tex_lines": None,
                    }
                    for index, candidate_id in enumerate(candidate_ids, start=1)
                ],
                "total": len(candidate_ids),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return report


def _write_historical_visual_clash_report(fig_dir: Path) -> Path:
    report = fig_dir / "build" / "visual_clash.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "fixture": fig_dir.name,
                "render_pdf": f"build/{fig_dir.name}.pdf",
                "candidates": [
                    {
                        "id": "VC026",
                        "kind": "text_on_path",
                        "text": "V",
                        "bbox_px": [100, 100, 120, 130],
                        "metric": {"dark": 0.041},
                        "tex_lines": None,
                    },
                    {
                        "id": "VC027",
                        "kind": "text_on_path",
                        "text": "s",
                        "bbox_px": [121, 100, 130, 130],
                        "metric": {"dark": 0.041},
                        "tex_lines": None,
                    },
                    {
                        "id": "VC050",
                        "kind": "text_on_path",
                        "text": "HV+",
                        "bbox_px": [200, 200, 250, 225],
                        "metric": {"dark": 0.041},
                        "tex_lines": None,
                    },
                ],
                "total": 3,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return report


def _write_crop_manifest(fig_dir: Path, *, crop_ids: tuple[str, ...]) -> Path:
    manifest = fig_dir / "build" / "audit_crops" / "manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    crop_entries = []
    for crop_id in crop_ids:
        crop_path = fig_dir / "build" / "audit_crops" / f"{crop_id}.png"
        crop_path.parent.mkdir(parents=True, exist_ok=True)
        crop_path.write_bytes(f"crop:{crop_id}\n".encode())
        crop_entries.append(
            {
                "id": crop_id,
                "kind": "zoom_crop",
                "source": "full_render",
                "path": f"build/audit_crops/{crop_id}.png",
                "source_path": f"build/{fig_dir.name}.png",
                "bbox_px": [0, 0, 10, 10],
                "sha256": file_sha256(crop_path),
            }
        )
    manifest.write_text(
        json.dumps(
            {
                "schema": "figure-agent.audit-crop-manifest.v1",
                "fixture": fig_dir.name,
                "render_path": f"build/{fig_dir.name}.png",
                "required_crop_ids": list(crop_ids),
                "crops": crop_entries,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def _crop_audit_log_yaml(
    *,
    first_crop_id: str = "full_q1",
    second_crop_id: str = "VC001_A",
    second_verdict: str = "defect",
    second_link: str = "M001",
) -> str:
    return (
        "crop_audit_log:\n"
        f"  - crop_id: {first_crop_id}\n"
        f"    path: build/audit_crops/{first_crop_id}.png\n"
        "    source: full_render\n"
        "    inspected: true\n"
        "    verdict: no_defect\n"
        "    linked_micro_defect_id: ''\n"
        "    rationale: full crop inspected with no defect\n"
        f"  - crop_id: {second_crop_id}\n"
        f"    path: build/audit_crops/visual_clash/{second_crop_id}.png\n"
        "    source: visual_clash:VC001\n"
        "    inspected: true\n"
        f"    verdict: {second_verdict}\n"
        f"    linked_micro_defect_id: {second_link!r}\n"
        "    rationale: visual clash crop inspected\n"
    )


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


def test_lint_critique_accepts_complete_v1_8_crop_accounting(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_crop_manifest(fig_dir, crop_ids=("full_q1", "VC001_A"))
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.8",
        findings_yaml=(
            "findings:\n"
            "  - id: C001\n"
            "    severity: MAJOR\n"
            "    category: label_placement\n"
            "    tex_lines: [10]\n"
            "    observation: linked visual clash defect\n"
            "    suggested_fix: fix the label\n"
            "    status: open\n"
            "panels: []\n"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/visual_clash/VC001_A.png\n"
            "    kind: label_backdrop_overflows_outline\n"
            "    severity: MAJOR\n"
            "    observation: label backdrop overflows in VC001_A crop\n"
            "    linked_finding_id: C001\n"
            "    visual_clash_ref: VC001\n"
            "    status: open\n"
        ),
        crop_audit_log_yaml=_crop_audit_log_yaml(),
        editorial_yaml=_editorial_yaml(),
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_rejects_v1_8_missing_crop_audit_log_with_manifest(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.8",
        findings_yaml="findings: []\npanels: []\n",
        micro_defects_yaml="micro_defects: []\n",
        editorial_yaml=_editorial_yaml(),
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["critique_contract"]
    assert "crop_audit_log" in violations[0].message


def test_lint_critique_rejects_v1_9_missing_crop_audit_log_with_manifest(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.9",
        findings_yaml="findings: []\npanels: []\n",
        micro_defects_yaml="micro_defects: []\n",
        editorial_yaml=_editorial_yaml(),
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["critique_contract"]
    assert "crop_audit_log" in violations[0].message


def test_lint_critique_rejects_v1_9_crop_audit_log_without_manifest(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.9",
        findings_yaml="findings: []\npanels: []\n",
        micro_defects_yaml="micro_defects: []\n",
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: fake\n"
            "    path: build/audit_crops/fake.png\n"
            "    source: visual_clash\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: fake crop must not pass without manifest provenance\n"
        ),
        editorial_yaml=_editorial_yaml(),
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["crop_audit_accounting"]
    assert "manifest" in violations[0].message


def test_lint_critique_rejects_v1_8_unknown_crop_id(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_crop_manifest(fig_dir, crop_ids=("full_q1", "VC001_A"))
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.8",
        findings_yaml="findings: []\npanels: []\n",
        micro_defects_yaml="micro_defects: []\n",
        crop_audit_log_yaml=_crop_audit_log_yaml(
            first_crop_id="unknown_q9",
            second_verdict="no_defect",
            second_link="",
        ),
        editorial_yaml=_editorial_yaml(),
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["crop_audit_accounting"]
    assert "unknown crop_audit_log crop_id entries: unknown_q9" in violations[0].message


def test_lint_critique_rejects_v1_8_manifest_crop_missing_sha256(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    manifest = _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    del payload["crops"][0]["sha256"]
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.8",
        findings_yaml="findings: []\npanels: []\n",
        micro_defects_yaml="micro_defects: []\n",
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: full_q1\n"
            "    path: build/audit_crops/full_q1.png\n"
            "    source: full_render\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: full crop inspected with no defect\n"
        ),
        editorial_yaml=_editorial_yaml(),
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["crop_audit_accounting"]
    assert "sha256" in violations[0].message
    assert "full_q1" in violations[0].message


def test_lint_critique_rejects_v1_8_manifest_crop_invalid_sha256(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    manifest = _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["crops"][0]["sha256"] = "sha256:" + ("A" * 64)
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.8",
        findings_yaml="findings: []\npanels: []\n",
        micro_defects_yaml="micro_defects: []\n",
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: full_q1\n"
            "    path: build/audit_crops/full_q1.png\n"
            "    source: full_render\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: full crop inspected with no defect\n"
        ),
        editorial_yaml=_editorial_yaml(),
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["crop_audit_accounting"]
    assert "lowercase sha256 hex" in violations[0].message
    assert "full_q1" in violations[0].message


def test_lint_critique_rejects_v1_8_manifest_crop_path_traversal(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    manifest = _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    outside_crop = fig_dir / "build" / "outside.png"
    outside_crop.parent.mkdir(parents=True, exist_ok=True)
    outside_crop.write_bytes(b"outside\n")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["crops"][0]["path"] = "build/audit_crops/../outside.png"
    payload["crops"][0]["sha256"] = file_sha256(outside_crop)
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.8",
        findings_yaml="findings: []\npanels: []\n",
        micro_defects_yaml="micro_defects: []\n",
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: full_q1\n"
            "    path: build/audit_crops/full_q1.png\n"
            "    source: full_render\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: full crop inspected with no defect\n"
        ),
        editorial_yaml=_editorial_yaml(),
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["crop_audit_accounting"]
    assert "path must point to build/audit_crops/*.png" in violations[0].message
    assert "full_q1" in violations[0].message


def test_lint_critique_rejects_v1_8_manifest_crop_missing_file(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    (fig_dir / "build" / "audit_crops" / "full_q1.png").unlink()
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.8",
        findings_yaml="findings: []\npanels: []\n",
        micro_defects_yaml="micro_defects: []\n",
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: full_q1\n"
            "    path: build/audit_crops/full_q1.png\n"
            "    source: full_render\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: full crop inspected with no defect\n"
        ),
        editorial_yaml=_editorial_yaml(),
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["crop_audit_accounting"]
    assert "missing crop file" in violations[0].message
    assert "full_q1" in violations[0].message


def test_lint_critique_rejects_v1_8_manifest_crop_hash_mismatch(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    (fig_dir / "build" / "audit_crops" / "full_q1.png").write_bytes(b"changed\n")
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.8",
        findings_yaml="findings: []\npanels: []\n",
        micro_defects_yaml="micro_defects: []\n",
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: full_q1\n"
            "    path: build/audit_crops/full_q1.png\n"
            "    source: full_render\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: full crop inspected with no defect\n"
        ),
        editorial_yaml=_editorial_yaml(),
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["crop_audit_accounting"]
    assert "hash mismatch" in violations[0].message
    assert "full_q1" in violations[0].message


def test_lint_critique_rejects_v1_8_missing_required_crop_id(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_crop_manifest(fig_dir, crop_ids=("full_q1", "VC001_A"))
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.8",
        findings_yaml="findings: []\npanels: []\n",
        micro_defects_yaml="micro_defects: []\n",
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: full_q1\n"
            "    path: build/audit_crops/full_q1.png\n"
            "    source: full_render\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: full crop inspected with no defect\n"
        ),
        editorial_yaml=_editorial_yaml(),
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["crop_audit_accounting"]
    assert "missing required crop_audit_log entries: VC001_A" in violations[0].message


def test_lint_critique_keeps_v1_7_legacy_parseable_without_crop_audit_log(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        findings_yaml="findings: []\npanels: []\n",
        micro_defects_yaml="micro_defects: []\n",
        editorial_yaml=_editorial_yaml(),
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
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


def test_lint_critique_rejects_unaccounted_v1_7_visual_clash_candidate(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001", "VC002"))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/panel_E_s01.png\n"
            "    kind: label_backdrop_overflows_outline\n"
            "    severity: MINOR\n"
            "    observation: VC001 label backdrop candidate remains visible\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC001\n"
            "    status: open\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["visual_clash_accounting"]
    assert "VC002" in violations[0].message


def test_lint_critique_accepts_v1_7_when_all_visual_clash_candidates_are_accounted(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001", "VC002"))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/panel_E_s01.png\n"
            "    kind: label_backdrop_overflows_outline\n"
            "    severity: MINOR\n"
            "    observation: VC001 label backdrop candidate remains visible\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC001\n"
            "    status: open\n"
            "  - id: M002\n"
            "    crop: examples/demo_fig/build/audit_crops/panel_E_s02.png\n"
            "    kind: label_glyph_overlaps_internal_drawing\n"
            "    severity: NIT\n"
            "    observation: >-\n"
            "      VC002 is a false positive: the glyph is a separate axis label,\n"
            "      not an internal instrument-box drawing, and the contact is outside\n"
            "      the apparatus.\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC002\n"
            "    status: accept_simplification\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_rejects_v1_7_when_visual_clash_report_is_missing(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml="micro_defects: []\n",
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["visual_clash_accounting"]
    assert "missing build/visual_clash.json" in violations[0].message


@pytest.mark.parametrize(
    "schema",
    ["figure-agent.critique.v1.8", "figure-agent.critique.v1.9", "figure-agent.critique.v1.10"],
)
def test_lint_critique_rejects_current_schema_when_visual_clash_report_is_missing(
    tmp_path: Path,
    schema: str,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema=schema,
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml="micro_defects: []\n",
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: full_q1\n"
            "    path: build/audit_crops/full_q1.png\n"
            "    source: full_render\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: full crop inspected with no defect\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\npanels: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["visual_clash_accounting"]
    assert "missing build/visual_clash.json" in violations[0].message


def test_lint_critique_accepts_v1_7_when_visual_clash_report_has_no_candidates(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml="micro_defects: []\n",
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_rejects_weak_visual_clash_accept_simplification_rationale(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/panel_E_s01.png\n"
            "    kind: label_backdrop_overflows_outline\n"
            "    severity: NIT\n"
            "    observation: acceptable after review\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC001\n"
            "    status: accept_simplification\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == [
        "visual_clash_accept_simplification"
    ]
    assert "VC001" in violations[0].message


def test_lint_critique_accepts_concrete_visual_clash_accept_simplification_rationale(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/panel_E_s01.png\n"
            "    kind: label_backdrop_overflows_outline\n"
            "    severity: NIT\n"
            "    observation: >-\n"
            "      VC001 is a false positive: the label belongs to a separate axis annotation,\n"
            "      not the instrument box, and the apparent contact is outside the apparatus.\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC001\n"
            "    status: accept_simplification\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_rejects_duplicate_v1_7_visual_clash_candidate_refs(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/panel_E_s01.png\n"
            "    kind: label_backdrop_overflows_outline\n"
            "    severity: MINOR\n"
            "    observation: VC001 first accounting\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC001\n"
            "    status: open\n"
            "  - id: M002\n"
            "    crop: examples/demo_fig/build/audit_crops/panel_E_s02.png\n"
            "    kind: label_glyph_overlaps_internal_drawing\n"
            "    severity: NIT\n"
            "    observation: VC001 duplicate accounting\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC001\n"
            "    status: accept_simplification\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["visual_clash_accounting"]
    assert "duplicate visual_clash_ref" in violations[0].message
    assert "VC001" in violations[0].message


def test_lint_critique_rejects_unknown_v1_7_visual_clash_candidate_ref(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/panel_E_s01.png\n"
            "    kind: label_backdrop_overflows_outline\n"
            "    severity: MINOR\n"
            "    observation: VC001 candidate remains visible\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC001\n"
            "    status: open\n"
            "  - id: M002\n"
            "    crop: examples/demo_fig/build/audit_crops/panel_E_s02.png\n"
            "    kind: label_glyph_overlaps_internal_drawing\n"
            "    severity: NIT\n"
            "    observation: typo candidate id should not pass\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC999\n"
            "    status: accept_simplification\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["visual_clash_accounting"]
    assert "unknown visual_clash_ref" in violations[0].message
    assert "VC999" in violations[0].message


def test_lint_critique_rejects_v1_10_accept_simplification_without_structured_reason(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001",))
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.10",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/visual_clash/VC001_A.png\n"
            "    kind: line_crosses_label\n"
            "    severity: NIT\n"
            "    observation: VC001 is accepted because it is a false positive on a "
            "background texture\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC001\n"
            "    status: accept_simplification\n"
        ),
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: full_q1\n"
            "    path: build/audit_crops/full_q1.png\n"
            "    source: full_render\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: full crop inspected with no defect\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\npanels: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == [
        "visual_clash_accept_simplification"
    ]
    assert "accept_simplification_reason" in violations[0].message
    assert "VC001" in violations[0].message


def test_lint_critique_rejects_v1_10_accept_simplification_without_rationale(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001",))
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.10",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/visual_clash/VC001_A.png\n"
            "    kind: line_crosses_label\n"
            "    severity: NIT\n"
            "    observation: VC001 is accepted because it is a false positive on a "
            "background texture\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC001\n"
            "    status: accept_simplification\n"
            "    accept_simplification_reason: false_positive\n"
            "    accept_simplification_rationale: \"\"\n"
        ),
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: full_q1\n"
            "    path: build/audit_crops/full_q1.png\n"
            "    source: full_render\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: full crop inspected with no defect\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\npanels: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == [
        "visual_clash_accept_simplification"
    ]
    assert "accept_simplification_rationale" in violations[0].message
    assert "VC001" in violations[0].message


def test_lint_critique_rejects_v1_10_vague_accept_simplification_rationale(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001",))
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.10",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/visual_clash/VC001_A.png\n"
            "    kind: line_crosses_label\n"
            "    severity: NIT\n"
            "    observation: VC001 is a detector false positive on a decorative texture\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC001\n"
            "    status: accept_simplification\n"
            "    accept_simplification_reason: false_positive\n"
            "    accept_simplification_rationale: acceptable after review\n"
        ),
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: full_q1\n"
            "    path: build/audit_crops/full_q1.png\n"
            "    source: full_render\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: full crop inspected with no defect\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\npanels: []\n",
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == [
        "visual_clash_accept_simplification"
    ]
    assert "concrete" in violations[0].message
    assert "VC001" in violations[0].message


def test_lint_critique_accepts_v1_10_structured_accept_simplification(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001",))
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.10",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/visual_clash/VC001_A.png\n"
            "    kind: line_crosses_label\n"
            "    severity: NIT\n"
            "    observation: VC001 is a detector false positive on a decorative texture\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC001\n"
            "    status: accept_simplification\n"
            "    accept_simplification_reason: false_positive\n"
            "    accept_simplification_rationale: VC001 marks background texture, "
            "not a label collision.\n"
        ),
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: full_q1\n"
            "    path: build/audit_crops/full_q1.png\n"
            "    source: full_render\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: full crop inspected with no defect\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\npanels: []\n",
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_keeps_v1_9_accept_simplification_legacy_heuristic(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001",))
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.9",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M001\n"
            "    crop: examples/demo_fig/build/audit_crops/visual_clash/VC001_A.png\n"
            "    kind: line_crosses_label\n"
            "    severity: NIT\n"
            "    observation: VC001 is an intentional schematic label on a decorative "
            "background and not a collision defect.\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC001\n"
            "    status: accept_simplification\n"
        ),
        crop_audit_log_yaml=(
            "crop_audit_log:\n"
            "  - crop_id: full_q1\n"
            "    path: build/audit_crops/full_q1.png\n"
            "    source: full_render\n"
            "    inspected: true\n"
            "    verdict: no_defect\n"
            "    linked_micro_defect_id: ''\n"
            "    rationale: full crop inspected with no defect\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\npanels: []\n",
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_rejects_historical_hv_candidate_with_wrong_kind(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "fig1_visual_clash_regression"
    fig_dir.mkdir()
    _write_historical_visual_clash_report(fig_dir)
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M026\n"
            "    crop: examples/fig1_visual_clash_regression/build/audit_crops/VC026.png\n"
            "    kind: label_glyph_overlaps_internal_drawing\n"
            "    severity: MAJOR\n"
            "    observation: VC026 V glyph overlaps same-box meter display\n"
            "    linked_finding_id: C302\n"
            "    visual_clash_ref: VC026\n"
            "    status: open\n"
            "  - id: M027\n"
            "    crop: examples/fig1_visual_clash_regression/build/audit_crops/VC027.png\n"
            "    kind: label_glyph_overlaps_internal_drawing\n"
            "    severity: MAJOR\n"
            "    observation: VC027 s glyph overlaps same-box meter display\n"
            "    linked_finding_id: C302\n"
            "    visual_clash_ref: VC027\n"
            "    status: open\n"
            "  - id: M050\n"
            "    crop: examples/fig1_visual_clash_regression/build/audit_crops/VC050.png\n"
            "    kind: wire_crosses_label\n"
            "    severity: BLOCKER\n"
            "    observation: VC050 HV+ backdrop protrudes below the instrument outline\n"
            "    linked_finding_id: C301\n"
            "    visual_clash_ref: VC050\n"
            "    status: open\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml=(
            "findings:\n"
            "  - id: C301\n"
            "    severity: BLOCKER\n"
            "    category: label_placement\n"
            "    tex_lines: [10]\n"
            "    observation: HV+ historical regression\n"
            "    suggested_fix: repair HV+ box geometry\n"
            "    status: open\n"
            "  - id: C302\n"
            "    severity: MAJOR\n"
            "    category: label_placement\n"
            "    tex_lines: [20]\n"
            "    observation: V_s historical regression\n"
            "    suggested_fix: repair V_s meter label geometry\n"
            "    status: open\n"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == [
        "historical_visual_clash_regression"
    ]
    assert "VC050" in violations[0].message
    assert "label_backdrop_overflows_outline" in violations[0].message


def test_lint_critique_rejects_historical_vs_candidate_with_wrong_kind(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "fig1_visual_clash_regression"
    fig_dir.mkdir()
    _write_historical_visual_clash_report(fig_dir)
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M026\n"
            "    crop: examples/fig1_visual_clash_regression/build/audit_crops/VC026.png\n"
            "    kind: line_crosses_label\n"
            "    severity: MAJOR\n"
            "    observation: VC026 V glyph overlaps same-box meter display\n"
            "    linked_finding_id: C302\n"
            "    visual_clash_ref: VC026\n"
            "    status: open\n"
            "  - id: M027\n"
            "    crop: examples/fig1_visual_clash_regression/build/audit_crops/VC027.png\n"
            "    kind: label_glyph_overlaps_internal_drawing\n"
            "    severity: MAJOR\n"
            "    observation: VC027 s glyph overlaps same-box meter display\n"
            "    linked_finding_id: C302\n"
            "    visual_clash_ref: VC027\n"
            "    status: open\n"
            "  - id: M050\n"
            "    crop: examples/fig1_visual_clash_regression/build/audit_crops/VC050.png\n"
            "    kind: label_backdrop_overflows_outline\n"
            "    severity: BLOCKER\n"
            "    observation: VC050 HV+ backdrop protrudes below the instrument outline\n"
            "    linked_finding_id: C301\n"
            "    visual_clash_ref: VC050\n"
            "    status: open\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml=(
            "findings:\n"
            "  - id: C301\n"
            "    severity: BLOCKER\n"
            "    category: label_placement\n"
            "    tex_lines: [10]\n"
            "    observation: HV+ historical regression\n"
            "    suggested_fix: repair HV+ box geometry\n"
            "    status: open\n"
            "  - id: C302\n"
            "    severity: MAJOR\n"
            "    category: label_placement\n"
            "    tex_lines: [20]\n"
            "    observation: V_s historical regression\n"
            "    suggested_fix: repair V_s meter label geometry\n"
            "    status: open\n"
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == [
        "historical_visual_clash_regression"
    ]
    assert "VC026" in violations[0].message
    assert "label_glyph_overlaps_internal_drawing" in violations[0].message


def test_lint_critique_accepts_historical_visual_clash_expected_kinds(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "fig1_visual_clash_regression"
    fig_dir.mkdir()
    _write_historical_visual_clash_report(fig_dir)
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M026\n"
            "    crop: examples/fig1_visual_clash_regression/build/audit_crops/VC026.png\n"
            "    kind: label_glyph_overlaps_internal_drawing\n"
            "    severity: MAJOR\n"
            "    observation: VC026 V glyph overlaps same-box meter display\n"
            "    linked_finding_id: C302\n"
            "    visual_clash_ref: VC026\n"
            "    status: open\n"
            "  - id: M027\n"
            "    crop: examples/fig1_visual_clash_regression/build/audit_crops/VC027.png\n"
            "    kind: label_glyph_overlaps_internal_drawing\n"
            "    severity: MAJOR\n"
            "    observation: VC027 s glyph overlaps same-box meter display\n"
            "    linked_finding_id: C302\n"
            "    visual_clash_ref: VC027\n"
            "    status: open\n"
            "  - id: M050\n"
            "    crop: examples/fig1_visual_clash_regression/build/audit_crops/VC050.png\n"
            "    kind: label_backdrop_overflows_outline\n"
            "    severity: BLOCKER\n"
            "    observation: VC050 HV+ backdrop protrudes below the instrument outline\n"
            "    linked_finding_id: C301\n"
            "    visual_clash_ref: VC050\n"
            "    status: open\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml=(
            "findings:\n"
            "  - id: C301\n"
            "    severity: BLOCKER\n"
            "    category: label_placement\n"
            "    tex_lines: [10]\n"
            "    observation: HV+ historical regression\n"
            "    suggested_fix: repair HV+ box geometry\n"
            "    status: open\n"
            "  - id: C302\n"
            "    severity: MAJOR\n"
            "    category: label_placement\n"
            "    tex_lines: [20]\n"
            "    observation: V_s historical regression\n"
            "    suggested_fix: repair V_s meter label geometry\n"
            "    status: open\n"
        ),
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_does_not_apply_historical_candidate_rule_to_other_fixtures(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_historical_visual_clash_report(fig_dir)
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml=(
            "micro_defects:\n"
            "  - id: M026\n"
            "    crop: examples/demo_fig/build/audit_crops/VC026.png\n"
            "    kind: line_crosses_label\n"
            "    severity: NIT\n"
            "    observation: VC026 is accounted for in a non-regression fixture\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC026\n"
            "    status: open\n"
            "  - id: M027\n"
            "    crop: examples/demo_fig/build/audit_crops/VC027.png\n"
            "    kind: line_crosses_label\n"
            "    severity: NIT\n"
            "    observation: VC027 is accounted for in a non-regression fixture\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC027\n"
            "    status: open\n"
            "  - id: M050\n"
            "    crop: examples/demo_fig/build/audit_crops/VC050.png\n"
            "    kind: wire_crosses_label\n"
            "    severity: NIT\n"
            "    observation: VC050 is accounted for in a non-regression fixture\n"
            "    linked_finding_id: \"\"\n"
            "    visual_clash_ref: VC050\n"
            "    status: open\n"
        ),
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_keeps_v1_6_visual_clash_accounting_legacy_compatible(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=("VC001",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.6",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        micro_defects_yaml="micro_defects: []\n",
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_keeps_v1_6_missing_visual_clash_report_legacy_compatible(
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
        micro_defects_yaml="micro_defects: []\n",
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    assert critique_lint.lint_critique(fig_dir) == []


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


def test_lint_critique_reports_v1_7_passed_polish_without_print_scale_evidence(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.7",
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


def test_lint_critique_reports_v1_9_passed_polish_without_print_scale_evidence(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_crop_manifest(fig_dir, crop_ids=("full_q1", "VC001_A"))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.9",
        findings_yaml="findings: []\npanels: []\n",
        micro_defects_yaml="micro_defects: []\n",
        crop_audit_log_yaml=_crop_audit_log_yaml(
            second_verdict="no_defect",
            second_link="",
        ),
        editorial_yaml=_editorial_yaml(),
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
