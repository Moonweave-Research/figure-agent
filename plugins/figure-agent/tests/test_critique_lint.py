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


def _top_tier_yaml_with_aesthetic_anchor(anchor: str) -> str:
    lines = ["top_tier_audit:"]
    for key in TOP_TIER_KEYS:
        finding = (
            f"aesthetic_coherence cites aesthetic intent anchor {anchor}"
            if key == "aesthetic_coherence"
            else f"{key} finding"
        )
        lines.extend(
            [
                f"  {key}:",
                "    verdict: pass",
                f"    finding: {_quote_yaml_string(finding)}",
                "    concrete_fix: accept_simplification",
                "    blocks_high_impact: false",
            ]
        )
    return "\n".join(lines) + "\n"


def _editorial_yaml_with_aesthetic_anchors(
    *,
    polish_trigger_path: str = "ready_for_svg_polish",
) -> str:
    anchor_by_key = {
        "visual_identity": "preset_macro_feel",
        "aesthetic_risk": "toy_diagram",
        "tikz_vs_svg_polish_trigger": "svg_micro_polish",
    }
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
        anchor = anchor_by_key.get(key)
        evidence = f"{key} evidence"
        rationale = f"{key} rationale"
        concrete_fix = "accept_simplification"
        if anchor is not None:
            evidence = f"{key} cites aesthetic intent anchor {anchor}"
            rationale = f"{key} remains calibrated to {anchor}"
            concrete_fix = f"preserve {anchor} unless visual evidence contradicts it"
        lines.extend(
            [
                f"  {key}:",
                "    verdict: pass",
                f"    evidence: {_quote_yaml_string(evidence)}",
                f"    rationale: {_quote_yaml_string(rationale)}",
                f"    concrete_fix: {_quote_yaml_string(concrete_fix)}",
                "    blocks_high_impact: false",
            ]
        )
        if key == "tikz_vs_svg_polish_trigger":
            lines.append(f"    recommended_path: {polish_trigger_path}")
    return "\n".join(lines) + "\n"


def _write_aesthetic_intent(fig_dir: Path, *, malformed: bool = False) -> Path:
    path = fig_dir / "aesthetic_intent.yaml"
    if malformed:
        path.write_text("schema: [", encoding="utf-8")
        return path
    path.write_text(
        f"""schema: figure-agent.aesthetic-intent.v1
fixture: {fig_dir.name}
target_journal: Nature Materials
visual_maturity: editorial
density: balanced
reference_style: multipanel_story
design_principles:
  - id: mature_restraint
    instruction: Prefer restrained publication-grade hierarchy.
must_avoid:
  - id: toy_diagram
    pattern: Avoid cartoon-like oversized labels.
    severity: MAJOR
  - id: preset_macro_feel
    pattern: Avoid repeated generic macro styling.
    severity: MINOR
polish_triggers:
  - id: svg_micro_polish
    condition: Semantic TikZ is correct but optical finish is limiting.
    recommended_path: ready_for_svg_polish
""",
        encoding="utf-8",
    )
    return path


def _write_aesthetic_intent_v2(
    fig_dir: Path,
    *,
    hero_default_route: str = "tikz_patch",
) -> Path:
    path = fig_dir / "aesthetic_intent.yaml"
    path.write_text(
        f"""schema: figure-agent.aesthetic-intent.v2
fixture: {fig_dir.name}
target_journal: Nature Materials
visual_maturity: editorial
density: balanced
reference_style: multipanel_story
design_principles:
  - id: mature_restraint
    instruction: Prefer restrained publication-grade hierarchy.
must_avoid:
  - id: toy_diagram
    pattern: Avoid cartoon-like oversized labels.
    severity: MAJOR
  - id: preset_macro_feel
    pattern: Avoid repeated generic macro styling.
    severity: MINOR
polish_triggers:
  - id: svg_micro_polish
    condition: Semantic TikZ is correct but optical finish is limiting.
    recommended_path: ready_for_svg_polish
aesthetic_levers:
  - id: maturity_restraint
    dimension: maturity
    intent: Keep the figure visually mature and restrained.
    priority: required
    positive_signals:
      - restrained label scale
    anti_patterns:
      - poster-like saturation
    allowed_adjustments:
      - reduce non-essential label prominence
    forbidden_adjustments:
      - change scientific meaning
    default_route: tikz_patch
  - id: hero_balance
    dimension: hero_hierarchy
    intent: Keep the intended hero panel dominant without hiding support panels.
    priority: recommended
    positive_signals:
      - primary panel remains the first fixation
    anti_patterns:
      - secondary panel competes with the main claim
    allowed_adjustments:
      - rebalance secondary accent weight
    forbidden_adjustments:
      - remove mechanism support
    default_route: {hero_default_route}
  - id: optional_svg_texture
    dimension: hand_craft
    intent: Add final hand-crafted detail only after semantic gates are stable.
    priority: optional
    positive_signals:
      - lines do not feel mechanically repeated
    anti_patterns:
      - deterministic macro repetition
    allowed_adjustments:
      - polish stroke rhythm in SVG
    forbidden_adjustments:
      - edit scientific geometry
    default_route: svg_polish
""",
        encoding="utf-8",
    )
    return path


def _aesthetic_lever_audit_yaml(
    *,
    first_verdict: str = "pass",
    first_route: str = "none",
    first_linked_evidence: str = "top_tier_audit.aesthetic_coherence",
    first_allowed_next_adjustment: str = "",
    second_lever_id: str = "hero_balance",
    second_dimension: str = "hero_hierarchy",
    second_verdict: str = "weak",
    second_route: str = "tikz_patch",
    second_linked_evidence: str = "C001",
    second_observed_anti_patterns: list[str] | None = None,
    second_rationale: str = "hero_balance needs a bounded TikZ adjustment linked to C001",
    include_optional: bool = True,
    optional_verdict: str = "pass",
    optional_route: str = "none",
    optional_allowed_next_adjustment: str = "",
) -> str:
    if second_observed_anti_patterns is None:
        second_observed_anti_patterns = ["secondary panel competes with the main claim"]
    if second_observed_anti_patterns:
        second_anti_patterns_yaml = "\n".join(
            f"      - {_quote_yaml_string(item)}" for item in second_observed_anti_patterns
        )
    else:
        second_anti_patterns_yaml = "      []"
    optional = ""
    if include_optional:
        optional = (
            "  - lever_id: optional_svg_texture\n"
            "    dimension: hand_craft\n"
            f"    verdict: {optional_verdict}\n"
            "    confidence: medium\n"
            "    observed_positive_signals:\n"
            "      - no mechanical repetition remains at current scope\n"
            "    observed_anti_patterns:\n"
            "      - deterministic macro repetition remains visible\n"
            f"    route: {optional_route}\n"
            "    linked_evidence:\n"
            "      - editorial_art_direction.tikz_vs_svg_polish_trigger\n"
            f"    allowed_next_adjustment: {_quote_yaml_string(optional_allowed_next_adjustment)}\n"
            "    forbidden_adjustment_guard: do not edit scientific geometry\n"
            "    rationale: optional_svg_texture is not active in this loop\n"
        )
    return (
        "aesthetic_lever_audit:\n"
        "  - lever_id: maturity_restraint\n"
        "    dimension: maturity\n"
        f"    verdict: {first_verdict}\n"
        "    confidence: high\n"
        "    observed_positive_signals:\n"
        "      - restrained label scale\n"
        "    observed_anti_patterns:\n"
        "      - poster-like saturation remains possible\n"
        f"    route: {first_route}\n"
        "    linked_evidence:\n"
        f"      - {first_linked_evidence}\n"
        f"    allowed_next_adjustment: {_quote_yaml_string(first_allowed_next_adjustment)}\n"
        "    forbidden_adjustment_guard: do not change scientific meaning\n"
        "    rationale: maturity_restraint passes with restrained labels\n"
        f"  - lever_id: {second_lever_id}\n"
        f"    dimension: {second_dimension}\n"
        f"    verdict: {second_verdict}\n"
        "    confidence: medium\n"
        "    observed_positive_signals:\n"
        "      - primary panel remains visible\n"
        "    observed_anti_patterns:\n"
        f"{second_anti_patterns_yaml}\n"
        f"    route: {second_route}\n"
        "    linked_evidence:\n"
        f"      - {second_linked_evidence}\n"
        "    allowed_next_adjustment: rebalance secondary accent weight\n"
        "    forbidden_adjustment_guard: do not remove mechanism support\n"
        f"    rationale: {_quote_yaml_string(second_rationale)}\n"
        f"{optional}"
    )


def _journal_grade_yaml(*, benchmark_level: str = "solid_manuscript") -> str:
    return (
        "journal_grade_assessment:\n"
        "  schema: figure-agent.journal-grade-assessment.v1\n"
        "  scoring_mode: fresh_reaudit\n"
        f"  assessed_artifact_hash: sha256:{'a' * 64}\n"
        f"  benchmark_level: {benchmark_level}\n"
        "  confidence: high\n"
        "  blockers: []\n"
        "  regression_detected: false\n"
        "  regressions: []\n"
        "  score_is_gateable: false\n"
        "  next_quality_bottleneck: polish\n"
        "  rationale: calibrated journal assessment\n"
    )


def _single_crop_audit_log_yaml() -> str:
    return (
        "crop_audit_log:\n"
        "  - crop_id: full_q1\n"
        "    path: build/audit_crops/full_q1.png\n"
        "    source: full_render\n"
        "    inspected: true\n"
        "    verdict: no_defect\n"
        "    linked_micro_defect_id: ''\n"
        "    rationale: full crop inspected with no defect\n"
    )


def _write_critique(
    fig_dir: Path,
    *,
    findings_yaml: str,
    schema: str = "figure-agent.critique.v1.3",
    micro_defects_yaml: str = "",
    crop_audit_log_yaml: str = "",
    top_tier_yaml: str | None = None,
    editorial_yaml: str = "",
    aesthetic_lever_audit_yaml: str = "",
    journal_grade_yaml: str = "",
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
        f"{aesthetic_lever_audit_yaml}"
        f"{journal_grade_yaml}"
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
    if not (fig_dir / "build" / "text_boundary_clash.json").exists():
        _write_text_boundary_clash_report(fig_dir, candidate_ids=())
    return report


def _write_text_boundary_clash_report(fig_dir: Path, *, candidate_ids: tuple[str, ...]) -> Path:
    report = fig_dir / "build" / "text_boundary_clash.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-boundary-clash.v1",
                "fixture": fig_dir.name,
                "render_pdf": f"build/{fig_dir.name}.pdf",
                "source": "spec.yaml:text_boundary_checks",
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "text_crosses_vertical_boundary",
                        "text": f"label {candidate_id}",
                        "boundary_id": "de_column_rule",
                        "boundary_role": "column_rule",
                        "bbox_pt": [70.0, 20.0, 75.0, 30.0],
                        "boundary_pt": {"x": 72.0, "y_range": [0.0, 144.0]},
                        "clearance_pt": 0.5,
                    }
                    for candidate_id in candidate_ids
                ],
                "total": len(candidate_ids),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return report


def _write_label_path_proximity_report(fig_dir: Path, *, candidate_ids: tuple[str, ...]) -> Path:
    report = fig_dir / "build" / "label_path_proximity.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps(
            {
                "schema": "figure-agent.label-path-proximity.v1",
                "fixture": fig_dir.name,
                "render_pdf": f"build/{fig_dir.name}.pdf",
                "source": "spec.yaml:label_path_proximity_checks",
                "candidates": [
                    {
                        "id": candidate_id,
                        "kind": "label_path_near_miss",
                        "text": f"label {candidate_id}",
                        "path_id": "reference_line",
                        "path_role": "reference_line",
                        "bbox_pt": [index, index + 1, index + 2, index + 3],
                        "path_pt": {
                            "kind": "horizontal_line",
                            "y": 10.0,
                            "x_range": [0.0, 20.0],
                        },
                        "clearance_pt": 2.0,
                        "distance_pt": 1.0,
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


def test_lint_critique_rejects_generic_aesthetic_slots_when_intent_exists(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_aesthetic_intent(fig_dir)
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

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == [
        "aesthetic_intent_accounting"
    ]
    assert "top_tier_audit.aesthetic_coherence" in violations[0].message
    assert "editorial_art_direction.visual_identity" in violations[0].message
    assert "editorial_art_direction.aesthetic_risk" in violations[0].message
    assert "editorial_art_direction.tikz_vs_svg_polish_trigger" in violations[0].message


def test_lint_critique_accepts_aesthetic_slots_with_exact_intent_anchors(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_aesthetic_intent(fig_dir)
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.5",
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        top_tier_yaml=_top_tier_yaml_with_aesthetic_anchor("mature_restraint"),
        micro_defects_yaml="micro_defects: []\n",
        editorial_yaml=_editorial_yaml_with_aesthetic_anchors(),
        findings_yaml="findings: []\n",
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_keeps_missing_aesthetic_intent_legacy_behavior(
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
        editorial_yaml=_editorial_yaml(),
        findings_yaml="findings: []\n",
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_reports_malformed_aesthetic_intent_as_controlled_blocker(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_aesthetic_intent(fig_dir, malformed=True)
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

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == [
        "aesthetic_intent_accounting"
    ]
    assert "aesthetic_intent.yaml invalid" in violations[0].message


def _write_complete_v1_11_aesthetic_fixture(
    fig_dir: Path,
    *,
    aesthetic_lever_audit_yaml: str | None = None,
    journal_grade_yaml: str = "",
    editorial_trigger_path: str = "ready_for_svg_polish",
    hero_default_route: str = "tikz_patch",
) -> None:
    _write_aesthetic_intent_v2(fig_dir, hero_default_route=hero_default_route)
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_text_boundary_clash_report(fig_dir, candidate_ids=())
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.11",
        top_tier_yaml=_top_tier_yaml_with_aesthetic_anchor("mature_restraint"),
        micro_defects_yaml="micro_defects: []\n",
        crop_audit_log_yaml=_single_crop_audit_log_yaml(),
        editorial_yaml=_editorial_yaml_with_aesthetic_anchors(
            polish_trigger_path=editorial_trigger_path
        ),
        aesthetic_lever_audit_yaml=aesthetic_lever_audit_yaml
        if aesthetic_lever_audit_yaml is not None
        else _aesthetic_lever_audit_yaml(),
        journal_grade_yaml=journal_grade_yaml,
        journal_polish_evidence="print-scale audit: print_178mm.png and print_thumbnail.png pass",
        publication_readiness_evidence=(
            "publication readiness includes print-scale evidence from print_178mm.png"
        ),
        findings_yaml=(
            "findings:\n"
            "  - id: C001\n"
            "    severity: MINOR\n"
            "    category: composition_layout\n"
            "    tex_lines: [10]\n"
            "    observation: bounded hero balance adjustment\n"
            "    suggested_fix: rebalance the secondary accent only\n"
            "    status: open\n"
            "panels: []\n"
        ),
    )


def test_lint_critique_accepts_complete_v1_11_aesthetic_lever_accounting(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(fig_dir)

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_rejects_missing_v1_11_aesthetic_lever(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(include_optional=False),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "missing declared lever ids: optional_svg_texture" in violations[0].message


def test_lint_critique_rejects_unknown_v1_11_aesthetic_lever(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_lever_id="unplanned_lever",
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "unknown lever ids: unplanned_lever" in violations[0].message


def test_lint_critique_rejects_duplicate_v1_11_aesthetic_lever(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_lever_id="maturity_restraint",
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "duplicate lever ids: maturity_restraint" in violations[0].message


def test_lint_critique_rejects_v1_11_aesthetic_dimension_mismatch(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(second_dimension="maturity"),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "dimension mismatch for hero_balance" in violations[0].message


def test_lint_critique_rejects_v1_11_route_none_for_unresolved_lever(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(second_route="none"),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "hero_balance route must not be none" in violations[0].message


def test_lint_critique_rejects_v1_11_unresolved_lever_without_anti_pattern(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_observed_anti_patterns=[],
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["critique_contract"]
    assert "observed_anti_patterns" in violations[0].message


def test_lint_critique_rejects_v1_11_required_not_applicable_lever(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            first_verdict="not_applicable",
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "maturity_restraint is required and cannot be not_applicable" in (
        violations[0].message
    )


def test_lint_critique_rejects_v1_11_tikz_patch_without_finding_or_axis_link(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_linked_evidence="top_tier_audit.aesthetic_coherence",
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "hero_balance route tikz_patch must link to a finding id or quality axis" in (
        violations[0].message
    )


def test_lint_critique_rejects_v1_11_svg_polish_without_editorial_trigger(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        hero_default_route="svg_polish",
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_route="svg_polish",
            second_linked_evidence="C001",
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "hero_balance route svg_polish must cite editorial_art_direction" in (
        violations[0].message
    )


def test_lint_critique_rejects_v1_11_svg_polish_when_trigger_path_is_not_svg(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        editorial_trigger_path="continue_tikz",
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_verdict="pass",
            second_route="none",
            second_linked_evidence="top_tier_audit.aesthetic_coherence",
            optional_verdict="weak",
            optional_route="svg_polish",
            optional_allowed_next_adjustment="polish stroke rhythm in SVG",
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert (
        "optional_svg_texture route svg_polish requires recommended_path ready_for_svg_polish"
        in violations[0].message
    )


def test_lint_critique_rejects_v1_11_semantic_backport_without_semantic_evidence(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        hero_default_route="semantic_backport",
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_route="semantic_backport",
            second_linked_evidence="C001",
            second_rationale="hero_balance needs an ordinary visual adjustment",
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "hero_balance route semantic_backport must cite semantic-backport evidence" in (
        violations[0].message
    )


def test_lint_critique_rejects_v1_11_semantic_backport_with_non_semantic_trigger(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        hero_default_route="semantic_backport",
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_route="semantic_backport",
            second_linked_evidence="editorial_art_direction.tikz_vs_svg_polish_trigger",
            second_rationale="hero_balance needs an ordinary visual adjustment",
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "hero_balance route semantic_backport must cite semantic-backport evidence" in (
        violations[0].message
    )


def test_lint_critique_accepts_v1_11_semantic_backport_with_semantic_trigger(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        hero_default_route="semantic_backport",
        editorial_trigger_path="semantic_backport_required",
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_route="semantic_backport",
            second_linked_evidence="editorial_art_direction.tikz_vs_svg_polish_trigger",
            second_rationale="semantic source must be updated before polish",
        ),
    )

    assert critique_lint.lint_critique(fig_dir) == []


def test_lint_critique_rejects_v1_11_route_drift_from_declared_default(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_route="human_art_direction",
            second_linked_evidence="editorial_art_direction.human_art_direction_gate",
            second_rationale="human judgment is useful here",
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "hero_balance route must match declared default_route tikz_patch" in (
        violations[0].message
    )


def test_lint_critique_rejects_v1_11_human_route_without_human_gate(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        hero_default_route="human_art_direction",
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_route="human_art_direction",
            second_linked_evidence="C001",
            second_rationale="human target-journal art direction is needed",
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "hero_balance route human_art_direction must cite editorial_art_direction" in (
        violations[0].message
    )


def test_lint_critique_rejects_v1_11_human_route_hidden_by_simplification(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        hero_default_route="human_art_direction",
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_route="human_art_direction",
            second_linked_evidence="editorial_art_direction.human_art_direction_gate",
            second_rationale="accept_simplification: leave target-journal taste unchanged",
        ),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "human_art_direction must not be hidden behind accept_simplification" in (
        violations[0].message
    )


def test_lint_critique_rejects_high_impact_with_unresolved_required_lever(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            first_verdict="weak",
            first_route="tikz_patch",
            first_linked_evidence="C001",
            first_allowed_next_adjustment="reduce non-essential label prominence",
        ),
        journal_grade_yaml=_journal_grade_yaml(benchmark_level="high_impact_candidate"),
    )

    violations = critique_lint.lint_critique(fig_dir)

    assert [violation.category for violation in violations] == ["aesthetic_lever_accounting"]
    assert "high_impact_candidate requires passing required aesthetic levers" in (
        violations[0].message
    )


def test_lint_critique_allows_high_impact_with_unresolved_optional_lever(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_complete_v1_11_aesthetic_fixture(
        fig_dir,
        aesthetic_lever_audit_yaml=_aesthetic_lever_audit_yaml(
            second_verdict="pass",
            second_route="none",
            second_linked_evidence="top_tier_audit.aesthetic_coherence",
            optional_verdict="weak",
            optional_route="svg_polish",
            optional_allowed_next_adjustment="polish stroke rhythm in SVG",
        ),
        journal_grade_yaml=_journal_grade_yaml(benchmark_level="high_impact_candidate"),
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


def test_lint_critique_rejects_missing_text_boundary_ref_when_report_has_candidates(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_text_boundary_clash_report(fig_dir, candidate_ids=("TB001",))
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.10",
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

    assert [violation.category for violation in violations] == ["text_boundary_accounting"]
    assert "missing: TB001" in violations[0].message


def test_lint_critique_rejects_current_schema_when_text_boundary_report_is_missing(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=())
    (fig_dir / "build" / "text_boundary_clash.json").unlink()
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.10",
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

    assert [violation.category for violation in violations] == ["text_boundary_accounting"]
    assert "missing build/text_boundary_clash.json" in violations[0].message


def test_lint_critique_accepts_text_boundary_ref_accounting(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_text_boundary_clash_report(fig_dir, candidate_ids=("TB001",))
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
            "    crop: examples/demo_fig/build/audit_crops/full_q1.png\n"
            "    kind: label_crosses_column_rule\n"
            "    severity: MINOR\n"
            "    observation: TB001 shows label crossing the declared column rule\n"
            "    linked_finding_id: ''\n"
            "    visual_clash_ref: ''\n"
            "    text_boundary_ref: TB001\n"
            "    status: open\n"
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


def test_lint_critique_rejects_missing_label_path_ref_when_report_has_candidates(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_text_boundary_clash_report(fig_dir, candidate_ids=())
    _write_label_path_proximity_report(fig_dir, candidate_ids=("LP001",))
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.10",
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

    assert [violation.category for violation in violations] == ["label_path_accounting"]
    assert "missing: LP001" in violations[0].message


def test_lint_critique_rejects_malformed_label_path_report_without_traceback(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_text_boundary_clash_report(fig_dir, candidate_ids=())
    malformed_report = fig_dir / "build" / "label_path_proximity.json"
    malformed_report.parent.mkdir(parents=True, exist_ok=True)
    malformed_report.write_text("{not json", encoding="utf-8")
    _write_crop_manifest(fig_dir, crop_ids=("full_q1",))
    _write_critique(
        fig_dir,
        schema="figure-agent.critique.v1.10",
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

    assert [violation.category for violation in violations] == ["label_path_accounting"]
    assert "malformed build/label_path_proximity.json" in violations[0].message


def test_lint_critique_accepts_label_path_ref_accounting(tmp_path: Path) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_text_boundary_clash_report(fig_dir, candidate_ids=())
    _write_label_path_proximity_report(fig_dir, candidate_ids=("LP001",))
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
            "    crop: examples/demo_fig/build/audit_crops/full_q1.png\n"
            "    kind: label_path_near_miss\n"
            "    severity: MINOR\n"
            "    observation: LP001 shows a label too close to a declared semantic path\n"
            "    linked_finding_id: ''\n"
            "    visual_clash_ref: ''\n"
            "    text_boundary_ref: ''\n"
            "    label_path_ref: LP001\n"
            "    status: open\n"
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


def test_lint_critique_rejects_duplicate_label_path_ref_accounting(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_text_boundary_clash_report(fig_dir, candidate_ids=())
    _write_label_path_proximity_report(fig_dir, candidate_ids=("LP001",))
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
            "    crop: examples/demo_fig/build/audit_crops/full_q1.png\n"
            "    kind: label_path_near_miss\n"
            "    severity: MINOR\n"
            "    observation: first LP001 account\n"
            "    linked_finding_id: ''\n"
            "    visual_clash_ref: ''\n"
            "    text_boundary_ref: ''\n"
            "    label_path_ref: LP001\n"
            "    status: open\n"
            "  - id: M002\n"
            "    crop: examples/demo_fig/build/audit_crops/full_q1.png\n"
            "    kind: label_path_near_miss\n"
            "    severity: MINOR\n"
            "    observation: duplicate LP001 account\n"
            "    linked_finding_id: ''\n"
            "    visual_clash_ref: ''\n"
            "    text_boundary_ref: ''\n"
            "    label_path_ref: LP001\n"
            "    status: open\n"
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

    assert [violation.category for violation in violations] == ["label_path_accounting"]
    assert "duplicate label_path_ref" in violations[0].message


def test_lint_critique_rejects_unknown_label_path_ref_accounting(
    tmp_path: Path,
) -> None:
    fig_dir = tmp_path / "demo_fig"
    fig_dir.mkdir()
    _write_visual_clash_report(fig_dir, candidate_ids=())
    _write_text_boundary_clash_report(fig_dir, candidate_ids=())
    _write_label_path_proximity_report(fig_dir, candidate_ids=("LP001",))
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
            "    crop: examples/demo_fig/build/audit_crops/full_q1.png\n"
            "    kind: label_path_near_miss\n"
            "    severity: MINOR\n"
            "    observation: LP999 is a typo and must be rejected\n"
            "    linked_finding_id: ''\n"
            "    visual_clash_ref: ''\n"
            "    text_boundary_ref: ''\n"
            "    label_path_ref: LP999\n"
            "    status: open\n"
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

    assert [violation.category for violation in violations] == ["label_path_accounting"]
    assert "unknown label_path_ref" in violations[0].message


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
