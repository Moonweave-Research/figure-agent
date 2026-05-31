from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import critique_brief  # noqa: E402
from critique_brief import generate_for, main  # noqa: E402
from reference_aesthetic_metrics import build_reference_aesthetic_metrics  # noqa: E402
from svg_polish_delta import build_svg_polish_delta_pack  # noqa: E402
from svg_polish_recipe import (  # noqa: E402
    SVG_POLISH_RECIPE_RELATIVE_PATH,
    svg_polish_recipe_input_hash,
    write_svg_polish_recipe,
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


def _quality_axes_schema_block(brief: str) -> str:
    start = brief.index("quality_axes:")
    end = brief.index("panels:", start)
    return brief[start:end]


def _write_example(tmp_path: Path, *, section6: str | None = None, png: bool = True) -> Path:
    example_dir = tmp_path / "review_demo"
    build_dir = example_dir / "build"
    build_dir.mkdir(parents=True)
    (example_dir / "spec.yaml").write_text(
        """name: review_demo
panels:
  - id: a
    caption: demo panel
style_profile: polymer-default
""",
        encoding="utf-8",
    )
    briefing = """## 1. Topic

Trap-assisted retention schematic.

## 2. Vocabulary

CB, VB, E_t

## 3. Composition

- CB line above trap level.
- Capture arrow points from CB to trap.
"""
    if section6 is not None:
        briefing += f"""

## 6. Physics invariants

{section6}
"""
    (example_dir / "briefing.md").write_text(briefing, encoding="utf-8")
    (example_dir / "review_demo.tex").write_text(
        "\\documentclass{standalone}\n"
        "\\begin{document}\n"
        "\\begin{tikzpicture}\n"
        "\\draw (0,1) -- (2,1) node[right]{CB};\n"
        "\\draw[->] (1,1) -- (1,0) node[right]{$E_t$};\n"
        "\\end{tikzpicture}\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    if png:
        Image.new("RGB", (120, 80), "white").save(build_dir / "review_demo.png")
    return example_dir


def _write_real_render_pair(example_dir: Path, *, size: tuple[int, int] = (200, 100)) -> None:
    build_dir = example_dir / "build"
    image = Image.new("RGB", size, "white")
    image.save(build_dir / "review_demo.png")
    image.save(build_dir / "review_demo.pdf", "PDF", resolution=72)


def _fake_svg_delta_renderer(source_svg: Path, output_png: Path) -> None:
    color = "red" if "exports" in source_svg.parts else "blue"
    Image.new("RGB", (4, 4), color).save(output_png)


def _write_svg_polish_delta_fixture(example_dir: Path) -> None:
    (example_dir / "exports").mkdir(exist_ok=True)
    (example_dir / "polish").mkdir(exist_ok=True)
    (example_dir / "exports" / "review_demo.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text id="label-a">A</text></svg>\n',
        encoding="utf-8",
    )
    (example_dir / "polish" / "review_demo.polished.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><text id="label-a">A</text></svg>\n',
        encoding="utf-8",
    )
    recipe_path = example_dir / SVG_POLISH_RECIPE_RELATIVE_PATH
    write_svg_polish_recipe(
        recipe_path,
        {
            "schema": "figure-agent.svg-polish-recipe.v1",
            "fixture": "review_demo",
            "source_svg": "exports/review_demo.svg",
            "target_svg": "polish/review_demo.polished.svg",
            "recipe_input_hash": svg_polish_recipe_input_hash(
                example_dir,
                "review_demo",
                source_svg="exports/review_demo.svg",
                base_dir=example_dir.parent,
            ),
            "operations": [
                {
                    "id": "R001",
                    "class": "label_micro_position",
                    "selector": {"kind": "element_id", "value": "label-a"},
                    "action": {"type": "translate", "dx": 1.0, "dy": -1.5, "unit": "px"},
                    "rationale": "visual-only polish",
                    "semantic_guard": {
                        "allowed": True,
                        "reason": "same label and target",
                    },
                }
            ],
        },
    )
    build_svg_polish_delta_pack(
        example_dir,
        recipe_path=recipe_path,
        renderer=_fake_svg_delta_renderer,
        base_dir=example_dir.parent,
    )


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _enable_external_vision_review(example_dir: Path) -> None:
    spec_path = example_dir / "spec.yaml"
    spec_path.write_text(
        spec_path.read_text(encoding="utf-8") + "external_vision_review: true\n",
        encoding="utf-8",
    )
    artifact = example_dir / "build" / "review_demo.png"
    (example_dir / "external_vision_review.yaml").write_text(
        f"""
schema: figure-agent.external-vision-review.v1
fixture: review_demo
reviewer: Gemini manual second pass
reviewed_at: "2026-05-28T12:00:00Z"
confidence: medium
reviewed_artifact:
  path: build/review_demo.png
  hash: {_sha256(artifact)}
reviewed_crops: []
findings:
  - id: EV001
    severity: MAJOR
    observation: external reviewer sees a possible near-miss label conflict
    evidence_ref: build/review_demo.png
    suggested_action: human_review
conflicts:
  - external_finding_id: EV001
    host_finding_id: C001
    summary: host critique treated the area as clean but external review disagrees
""".lstrip(),
        encoding="utf-8",
    )


def _enable_paper_aesthetic_context(example_dir: Path) -> Path:
    spec_path = example_dir / "spec.yaml"
    spec_path.write_text(
        spec_path.read_text(encoding="utf-8") + "paper_aesthetic_context: paper-demo\n",
        encoding="utf-8",
    )
    pack_dir = example_dir.parent / "_paper_aesthetic_contexts"
    pack_dir.mkdir(exist_ok=True)
    pack_path = pack_dir / "paper-demo.yaml"
    pack_path.write_text(
        """
schema: figure-agent.paper-aesthetic-context.v1
paper_id: paper-demo
target_journal: Nature Communications
visual_maturity: editorial
density: balanced
shared_visual_language:
  - id: restrained_palette
    dimension: palette
    instruction: keep palette restrained across the manuscript series
    priority: required
    positive_signals:
      - repeated muted accent colors
    anti_patterns:
      - poster-like saturation
  - id: typography_authority
    dimension: typography
    instruction: keep compact journal-style label hierarchy
    priority: required
    positive_signals:
      - consistent label scale across figures
    anti_patterns:
      - slide-like explanatory labels
figure_roles:
  - fixture: review_demo
    role: overview_mechanism
    must_align_with:
      - restrained_palette
      - typography_authority
    allowed_variations:
      - may use one stronger hero panel than downstream data figures
must_avoid:
  - id: series_drift
    pattern: one figure looks like a different design system from the rest
    severity: MAJOR
""".lstrip(),
        encoding="utf-8",
    )
    return pack_path


def _enable_journal_art_direction_playbook(example_dir: Path) -> Path:
    spec_path = example_dir / "spec.yaml"
    spec_path.write_text(
        spec_path.read_text(encoding="utf-8")
        + "journal_art_direction_playbook: nc-main-text\n",
        encoding="utf-8",
    )
    pack_dir = example_dir.parent / "_journal_art_direction_playbooks"
    pack_dir.mkdir(exist_ok=True)
    pack_path = pack_dir / "nc-main-text.yaml"
    pack_path.write_text(
        """
schema: figure-agent.journal-art-direction-playbook.v1
playbook_id: nc-main-text
target_journal: Nature Communications
venue_context: main_text
visual_maturity: restrained
design_center:
  - id: editorial_restraint
    dimension: maturity
    instruction: prefer controlled scientific illustration over decoration
    priority: required
    positive_signals:
      - compact labels are subordinate to visual evidence
    anti_patterns:
      - poster-like saturation without semantic role
    evidence_prompts:
      - check print-scale restraint
  - id: typography_authority
    dimension: typography
    instruction: keep labels typeset and quiet
    priority: required
    positive_signals:
      - math subscripts align cleanly
    anti_patterns:
      - slide-like explanatory labels
    evidence_prompts:
      - inspect reduced-scale labels
  - id: whitespace_breathing
    dimension: whitespace
    instruction: keep dense regions readable
    priority: recommended
    positive_signals:
      - visible resting space around labels
    anti_patterns:
      - near-miss spacing that feels stacked
    evidence_prompts:
      - identify the densest region
anti_patterns:
  - id: toy_schematic
    dimension: maturity
    severity: MAJOR
    pattern: oversized arrows or generic rounded blocks
    preferred_route: continue_tikz
  - id: preset_macro_feel
    dimension: hand_craft
    severity: MINOR
    pattern: repeated elements look mechanically identical
    preferred_route: ready_for_svg_polish
positive_signals:
  - id: restrained_hero
    dimension: hierarchy
    signal: one first-fixation element without poster emphasis
    evidence_prompt: name the first visual object noticed
  - id: print_scale_calm
    dimension: typography
    signal: labels remain readable and quiet at target print scale
    evidence_prompt: check the print-scale crop
polish_route_rules:
  - id: tikz_until_semantics_close
    condition: semantic structure or relative placement still needs edits
    recommended_path: continue_tikz
    forbidden_actions:
      - hide semantic ambiguity behind SVG polish
  - id: svg_for_optical_finish
    condition: semantics are stable but optical spacing limits finish
    recommended_path: ready_for_svg_polish
    forbidden_actions:
      - move scientific components semantically
human_review_triggers:
  - id: taste_direction_conflict
    condition: playbook and fixture intent conflict
    severity: MAJOR
""".lstrip(),
        encoding="utf-8",
    )
    return pack_path


def test_critique_brief_includes_invariants_when_section6_present(tmp_path):
    example_dir = _write_example(
        tmp_path,
        section6="- E_t must stay inside the bandgap.\n- Capture arrow must point CB to trap.",
    )

    brief = generate_for(example_dir)

    assert "## Physics invariants the figure MUST honor" in brief
    assert "- E_t must stay inside the bandgap." in brief
    assert "- Capture arrow must point CB to trap." in brief


def test_critique_brief_handles_missing_section6_gracefully(tmp_path):
    example_dir = _write_example(tmp_path, section6=None)

    brief = generate_for(example_dir)

    assert "(none provided" in brief
    assert "critic should infer plausible physics constraints from §1+§2" in brief


def test_critique_brief_errors_when_png_missing(tmp_path, capsys, monkeypatch):
    example_dir = _write_example(tmp_path, section6="- invariant", png=False)

    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])

    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "run /fig_compile first" in captured.err


def test_critique_brief_embeds_full_tex_source(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    tex = (example_dir / "review_demo.tex").read_text(encoding="utf-8")
    assert "```tex\n" in brief
    for line_number, line in enumerate(tex.splitlines(), start=1):
        assert f"{line_number:4d}: {line}" in brief
    assert "\n```\n\n## Mandatory Audit Checklists" in brief
    assert "### D. Conceptual Completeness Audit\n" in brief
    assert "\n## Critique rubric" in brief


def test_critique_brief_uses_example_relative_png_path(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    absolute_png_path = str((example_dir / "build" / "review_demo.png").resolve())
    assert absolute_png_path not in brief
    assert "`examples/review_demo/build/review_demo.png`" in brief
    assert "host main loop via the Read tool" in brief


def test_critique_brief_errors_when_png_is_older_than_tex(tmp_path, capsys, monkeypatch):
    example_dir = _write_example(tmp_path, section6="- invariant")
    tex_path = example_dir / "review_demo.tex"
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (100, 100))
    os.utime(tex_path, (200, 200))

    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])

    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "run /fig_compile first" in captured.err


def test_critique_brief_errors_when_png_is_older_than_briefing(tmp_path, capsys, monkeypatch):
    example_dir = _write_example(tmp_path, section6="- invariant")
    briefing_path = example_dir / "briefing.md"
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (100, 100))
    os.utime(briefing_path, (200, 200))

    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])

    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "run /fig_compile first" in captured.err


def test_critique_brief_errors_when_png_is_older_than_style_lock(tmp_path, capsys, monkeypatch):
    example_dir = _write_example(tmp_path, section6="- invariant")
    style_path = tmp_path / "polymer-paper-preamble.sty"
    style_path.write_text("% style", encoding="utf-8")
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (100, 100))
    os.utime(style_path, (200, 200))
    monkeypatch.setattr(critique_brief, "STYLE_LOCK_PATH", style_path)
    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])

    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "run /fig_compile first" in captured.err
    assert "polymer-paper-preamble.sty" in captured.err


def test_critique_brief_includes_rubric_sections_A_and_B(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "### A. Physics correctness" in brief
    assert "### B. Aesthetic placement" in brief
    assert "schema: figure-agent.critique.v1.16" in brief
    assert "rubric_version: figure-agent.critique-rubric.v1.16" in brief
    assert "panels:" in brief


def test_critique_brief_includes_journal_grade_quality_axes(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Journal-Grade Quality Axes (host LLM MUST evaluate)" in brief
    assert "### 1. Message and Storyline" in brief
    assert "### 2. Panel Role Coherence" in brief
    assert "### 3. Sub-region Integration" in brief
    assert "### 4. Component Fidelity" in brief
    assert "### 5. Scientific Plausibility" in brief
    assert "### 6. Composition and Layout" in brief
    assert "### 7. Label and Annotation Semantics" in brief
    assert "### 8. Journal Polish" in brief
    assert "### 9. Reference Fidelity" in brief
    assert "### 10. Publication Readiness" in brief


def test_critique_brief_includes_top_tier_journal_audit(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Top-Tier Journal Figure Audit (host LLM MUST enumerate)" in brief
    assert "### 1. First-Glance Message" in brief
    assert "### 2. Target-Journal Fit" in brief
    assert "### 3. Novelty and Claim Support" in brief
    assert "### 4. Figure-Caption Coupling" in brief
    assert "### 5. Visual Economy" in brief
    assert "### 6. Cross-Panel Semantic Grammar" in brief
    assert "### 7. Reader Misinterpretation Risk" in brief
    assert "### 8. Reduction / Print Readability" in brief
    assert "### 9. Accessibility and Color Robustness" in brief
    assert "### 10. Aesthetic Coherence" in brief


def test_critique_brief_includes_aesthetic_antipattern_checklist(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Aesthetic Anti-Pattern Checklist (host LLM MUST inspect)" in brief
    assert "childish_shape_language" in brief
    assert "poster_gradient_decoration" in brief
    assert "generic_template_look" in brief
    assert "dead_flat_vector_finish" in brief
    assert "uniform_line_weight_monotony" in brief
    assert "weak_hero_anchor" in brief
    assert "cramped_or_dead_whitespace" in brief
    assert "low_authority_typography" in brief
    assert "annotation_noise_competes_with_science" in brief
    assert "panel_style_mismatch" in brief
    assert "reference_overcopying" in brief
    assert "reference_underlearning" in brief
    assert "decorative_detail_without_explanatory_value" in brief


def test_critique_brief_includes_weakest_panel_coherence_check(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Weakest-Panel Coherence Check (host LLM MUST name one)" in brief
    assert "weakest panel/subregion" in brief
    assert "single-panel figures" in brief
    assert "composition | typography | color | density" in brief
    assert "tikz_patch | svg_polish | semantic_backport" in brief


def test_critique_brief_includes_editorial_art_direction_audit(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Editorial Art-Direction Audit (host LLM MUST evaluate)" in brief
    assert "### 1. Hero Focus" in brief
    assert "### 2. Narrative Choreography" in brief
    assert "### 3. Illustration Readiness" in brief
    assert "### 4. Abstraction Consistency" in brief
    assert "### 5. Reference-Class Fit" in brief
    assert "### 6. Visual Identity" in brief
    assert "### 7. Claim Payload Fit" in brief
    assert "### 8. Aesthetic Risk" in brief
    assert "### 9. TikZ-vs-SVG Polish Trigger" in brief
    assert "### 10. Human Art-Direction Gate" in brief
    assert "editorial_art_direction:" in brief
    assert "recommended_path: continue_tikz | ready_for_svg_polish" in brief
    assert "needs_human editorial slots cannot" in brief
    assert "use accept_simplification to bypass human visibility" in brief


def test_critique_brief_includes_fresh_reaudit_benchmark_level_schema(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Journal-Grade Fresh Re-Audit Assessment" in brief
    assert "journal_grade_assessment:" in brief
    assert "schema: figure-agent.journal-grade-assessment.v1" in brief
    assert "scoring_mode: fresh_reaudit" in brief
    assert "assessed_artifact_hash: " in brief
    assert (
        "benchmark_level: draft | solid_manuscript | high_impact_candidate | "
        "needs_human_art_direction | blocked"
    ) in brief
    assert "### 10. Publication Readiness" in brief


def test_critique_brief_includes_advisory_numeric_score_schema(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "overall_score: 0-100" in brief
    assert "sub_scores:" in brief
    assert "storyline: 0-100" in brief
    assert "composition: 0-100" in brief
    assert "component_fidelity: 0-100" in brief
    assert "scientific_plausibility: 0-100" in brief
    assert "label_semantics: 0-100" in brief
    assert "polish: 0-100" in brief
    assert "reference_fidelity: 0-100" in brief
    assert "export_scale_readability: 0-100" in brief
    assert 'score_rationale: "<why these numbers describe only the current artifact>"' in brief


def test_critique_brief_states_numeric_scores_are_advisory_not_gates(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "Scores are advisory fresh re-audit diagnostics" in brief
    assert "not cumulative progress" in brief
    assert "cannot override blockers" in brief
    assert "human" in brief
    assert "gates" in brief
    assert "stale exports" in brief
    assert "Do not invent journal acceptance" in brief


def test_critique_brief_includes_mandatory_audit_checklists(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Mandatory Audit Checklists (host LLM MUST enumerate)" in brief
    assert "### A. Structural Completeness Audit" in brief
    assert "### B. Label-Target Matching Audit" in brief
    assert "### C. Physical Plausibility Audit" in brief
    assert "### D. Conceptual Completeness Audit" in brief


def test_critique_brief_includes_high_zoom_audit_crops(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _write_real_render_pair(example_dir)

    brief = generate_for(example_dir)

    assert "schema: figure-agent.critique.v1.16" in brief
    assert "rubric_version: figure-agent.critique-rubric.v1.16" in brief
    assert "## High-Zoom Visual Audit Crops" in brief
    assert "`examples/review_demo/build/audit_crops/full_q1.png`" in brief
    assert "`examples/review_demo/build/audit_crops/full_q4.png`" in brief
    assert "original-pixel attention crops" in brief
    assert "line_crosses_label" in brief
    assert "arrow_tip_fused" in brief
    assert "## Print-Scale Audit Images" in brief
    assert "`examples/review_demo/build/audit_crops/print_178mm.png`" in brief
    assert "`examples/review_demo/build/audit_crops/print_thumbnail.png`" in brief
    assert "basis=fixed_width_proxy" in brief
    assert "target_width_px=1000" in brief
    assert "target_width_px=360" in brief
    assert "proxy evidence" in brief
    assert "journal_polish" in brief
    assert "publication_readiness" in brief
    assert "print_scale_unreadable" in brief
    assert (example_dir / "build" / "audit_crops" / "full_q1.png").is_file()
    assert (example_dir / "build" / "audit_crops" / "print_178mm.png").is_file()


def test_critique_brief_keeps_print_scale_images_out_of_high_zoom_section(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _write_real_render_pair(example_dir)

    brief = generate_for(example_dir)

    high_zoom_section = brief.split("## High-Zoom Visual Audit Crops", 1)[1].split(
        "## Print-Scale Audit Images", 1
    )[0]
    assert "print_178mm.png" not in high_zoom_section
    assert "print_thumbnail.png" not in high_zoom_section
    assert "print_scale_unreadable" not in high_zoom_section

    print_scale_section = brief.split("## Print-Scale Audit Images", 1)[1].split(
        "## Author intent", 1
    )[0]
    assert "print_scale_unreadable" in print_scale_section


def test_critique_brief_includes_visual_clash_candidates(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _write_real_render_pair(example_dir, size=(2000, 1600))
    (example_dir / "build" / "visual_clash.json").write_text(
        json.dumps(
            {
                "fixture": "review_demo",
                "render_pdf": "build/review_demo.pdf",
                "candidates": [
                    {
                        "id": "VC002",
                        "kind": "text_on_path",
                        "text": "HV+",
                        "bbox_px": [1750, 1409, 1871, 1466],
                        "metric": {"dark": 0.041, "edge": 0.006},
                        "tex_lines": None,
                    },
                    {
                        "id": "VC001",
                        "kind": "near_miss",
                        "text": "A",
                        "bbox_px": [1, 2, 3, 4],
                        "metric": {"dark": 0.02, "edge": 0.005},
                        "tex_lines": [10],
                    }
                ],
                "total": 2,
            }
        ),
        encoding="utf-8",
    )

    brief = generate_for(example_dir)

    assert "## Visual Clash Candidates (from check_visual_clash.py)" in brief
    assert "Host LLM MUST review each candidate" in brief
    assert "`VC001`" in brief
    assert "`VC002`" in brief
    assert "`text_on_path`" in brief
    assert "`HV+`" in brief
    assert "bbox_px=[1750, 1409, 1871, 1466]" in brief
    assert "metric=dark=0.041, edge=0.006" in brief
    assert brief.index("id=`VC001`") < brief.index("id=`VC002`")
    assert "label_backdrop_overflows_outline" in brief
    assert "label_glyph_overlaps_internal_drawing" in brief
    assert "`examples/review_demo/build/audit_crops/visual_clash/VC001_A.png`" in brief
    assert "`examples/review_demo/build/audit_crops/visual_clash/VC002_HV.png`" in brief
    assert "crop=`build/audit_crops/visual_clash/VC001_A.png`" in brief


def test_critique_brief_includes_text_boundary_clash_candidates(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _write_real_render_pair(example_dir, size=(2000, 1600))
    (example_dir / "build" / "text_boundary_clash.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.text-boundary-clash.v1",
                "fixture": "review_demo",
                "render_pdf": "build/review_demo.pdf",
                "source": "spec.yaml:text_boundary_checks",
                "candidates": [
                    {
                        "id": "TB002",
                        "kind": "text_outside_rect",
                        "text": "film",
                        "boundary_id": "row2_box",
                        "boundary_role": "row_box",
                        "bbox_pt": [20.0, 68.0, 50.0, 75.0],
                        "boundary_pt": {"bbox": [0.0, 0.0, 144.0, 72.0]},
                        "clearance_pt": 0.0,
                    },
                    {
                        "id": "TB001",
                        "kind": "text_crosses_vertical_boundary",
                        "text": "polymer",
                        "boundary_id": "de_column_rule",
                        "boundary_role": "column_rule",
                        "bbox_pt": [70.0, 20.0, 75.0, 30.0],
                        "boundary_pt": {"x": 72.0, "y_range": [0.0, 144.0]},
                        "clearance_pt": 0.5,
                    },
                ],
                "total": 2,
            }
        ),
        encoding="utf-8",
    )

    brief = generate_for(example_dir)

    assert "## Text Boundary Clash Candidates (from check_text_boundary_clash.py)" in brief
    assert "Host LLM MUST review each text-boundary candidate" in brief
    assert "`text_boundary_ref`" in brief
    assert "`TB001`" in brief
    assert "`TB002`" in brief
    assert "boundary_id=`de_column_rule`" in brief
    assert "boundary_role=`column_rule`" in brief
    assert "label_crosses_column_rule" in brief
    assert "label_overflows_row_box" in brief
    assert brief.index("id=`TB001`") < brief.index("id=`TB002`")


def test_critique_brief_includes_label_path_proximity_candidates(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _write_real_render_pair(example_dir, size=(2000, 1600))
    (example_dir / "build" / "label_path_proximity.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.label-path-proximity.v1",
                "fixture": "review_demo",
                "render_pdf": "build/review_demo.pdf",
                "source": "spec.yaml:label_path_proximity_checks",
                "candidates": [
                    {
                        "id": "LP002",
                        "kind": "label_curve_near_label",
                        "text": "shallow",
                        "path_id": "deep_escape_curve",
                        "path_role": "semantic_curve",
                        "bbox_pt": [430.0, 71.0, 460.0, 79.0],
                        "path_pt": {
                            "kind": "polyline",
                            "points": [[448.0, 70.0], [456.0, 75.0]],
                        },
                        "clearance_pt": 5.0,
                        "distance_pt": 2.25,
                    },
                    {
                        "id": "LP001",
                        "kind": "label_stacked_on_reference_line",
                        "text": "mobility edge",
                        "path_id": "mobility_edge_reference",
                        "path_role": "reference_line",
                        "bbox_pt": [443.0, 53.5, 492.0, 61.0],
                        "path_pt": {
                            "kind": "horizontal_line",
                            "y": 56.69,
                            "x_range": [430.0, 500.0],
                        },
                        "clearance_pt": 3.0,
                        "distance_pt": 0.0,
                    },
                ],
                "total": 2,
            }
        ),
        encoding="utf-8",
    )

    brief = generate_for(example_dir)

    assert "## Label-Path Proximity Candidates (from check_label_path_proximity.py)" in brief
    assert "Host LLM MUST review each label-path proximity candidate" in brief
    assert "`label_path_ref`" in brief
    assert "`LP001`" in brief
    assert "`LP002`" in brief
    assert "label_stacked_on_reference_line" in brief
    assert "label_curve_near_label" in brief
    assert "path_id=`mobility_edge_reference`" in brief
    assert "distance_pt=0" in brief
    assert "crop=`build/audit_crops/label_path/LP001_mobility_edge.png`" in brief
    assert "label_path_ref=`LP001`" in brief
    assert brief.index("id=`LP001`") < brief.index("id=`LP002`")


def test_critique_brief_includes_undeclared_geometry_candidates(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _write_real_render_pair(example_dir, size=(2000, 1600))
    (example_dir / "build" / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.undeclared-geometry.v1",
                "fixture": "review_demo",
                "render_pdf": "build/review_demo.pdf",
                "source": "tikz-source:auto-discovery",
                "candidates": [
                    {
                        "id": "UG002",
                        "kind": "label_endpoint_near_miss",
                        "evidence": "line close to mobility label",
                        "bbox_pt": [10.0, 20.0, 40.0, 20.0],
                        "source_line": 42,
                        "nearest_text": "mobility",
                        "distance_pt": 2.0,
                        "recommended_action": "add_micro_defect",
                    },
                    {
                        "id": "UG001",
                        "kind": "undeclared_column_rule",
                        "evidence": "column rule missing spec check",
                        "bbox_pt": [72.0, 0.0, 72.0, 144.0],
                        "source_line": 20,
                        "nearest_text": "",
                        "distance_pt": None,
                        "recommended_action": "add_spec_check",
                    },
                ],
                "total": 2,
            }
        ),
        encoding="utf-8",
    )

    brief = generate_for(example_dir)

    assert "## Undeclared Geometry Candidates (from check_undeclared_geometry.py)" in brief
    assert "`undeclared_geometry_ref`" in brief
    assert "`UG001`" in brief
    assert "`UG002`" in brief
    assert "kind=`undeclared_column_rule`" in brief
    assert "nearest_text=`mobility`" in brief
    assert "distance_pt=2.0" in brief
    assert brief.index("id=`UG001`") < brief.index("id=`UG002`")


def test_critique_brief_includes_panel_high_zoom_crops(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    Image.new("RGB", (80, 40), "white").save(ref_dir / "panel_a.png")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: A\n"
        "    caption: demo panel\n"
        "    reference_image: reference/panel_a.png\n"
        "    bbox_pdf_cm: [0, 0, 3.5, 1.75]\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    _write_real_render_pair(example_dir)

    brief = generate_for(example_dir)

    assert "`examples/review_demo/build/panel_crops/A.png`" in brief
    assert "`examples/review_demo/build/audit_crops/panel_A_q1.png`" in brief
    assert "`examples/review_demo/build/audit_crops/panel_A_q4.png`" in brief


def test_critique_brief_output_format_includes_hash_manifest_metadata(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "generator: critique_brief.py" in brief
    assert "generator_version: sha256:" in brief
    assert "rubric_version: figure-agent.critique-rubric.v1.16" in brief
    assert "critique_input_hash: sha256:" in brief
    assert "audit_enumeration:" in brief
    assert "quality_axes:" in brief
    quality_axes = _quality_axes_schema_block(brief)
    for axis_name in QUALITY_AXIS_NAMES:
        axis_start = quality_axes.index(f"  {axis_name}:")
        next_axis_starts = [
            quality_axes.find(f"  {candidate}:", axis_start + 1)
            for candidate in QUALITY_AXIS_NAMES
        ]
        next_axis_starts = [index for index in next_axis_starts if index != -1]
        axis_end = min(next_axis_starts) if next_axis_starts else len(quality_axes)
        axis_block = quality_axes[axis_start:axis_end]
        assert "verdict: pass | needs_patch | needs_human | block | not_applicable" in axis_block
        assert "confidence: low | medium | high" in axis_block
        assert (
            "recommended_action: none | patch | human_review | revise_briefing | "
            "block_release"
        ) in axis_block
    assert brief.count("category: structural | physics | label_placement") == 2


def test_critique_brief_output_format_uses_v1_16_default_schema_with_crops(
    tmp_path,
):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "schema: figure-agent.critique.v1.16" in brief
    assert "rubric_version: figure-agent.critique-rubric.v1.16" in brief
    assert "top_tier_audit:" in brief
    assert "editorial_art_direction:" in brief
    assert "recommended_path: continue_tikz | ready_for_svg_polish" in brief
    assert "remaining_tikz_lever:" in brief
    assert "svg_polish_candidate_reason:" in brief
    assert "micro_defects:" in brief
    for kind in (
        "line_crosses_label",
        "wire_crosses_label",
        "arrow_tip_fused",
        "label_target_detached",
        "floating_semantic_cue",
        "drawing_order_suspect",
        "print_scale_unreadable",
        "label_backdrop_overflows_outline",
        "label_glyph_overlaps_internal_drawing",
    ):
        assert kind in brief
    assert "linked_finding_id: \"<P001/C001 or empty when accept_simplification>\"" in brief
    assert 'visual_clash_ref: "<VC001 or empty when not from visual_clash.json>"' in brief
    assert (
        'observation: "<visible micro-defect from a crop, print-scale image, or audit candidate>"'
    ) in brief
    assert "visual-clash-linked `accept_simplification`" in brief
    assert "status: open | resolved | accept_simplification" in brief
    assert "accept_simplification_reason:" in brief
    assert "accept_simplification_rationale:" in brief
    assert "crop_audit_log:" in brief
    assert "crop_id: <crop id from build/audit_crops/manifest.json>" in brief
    assert "verdict: defect | no_defect | uncertain" in brief
    assert "linked_micro_defect_id: \"<M001 when verdict=defect or empty>\"" in brief
    assert "unintended_visible_anomaly:" in brief
    assert "anomaly_link:" in brief


def test_critique_brief_explains_top_tier_link_rule(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "top_tier_audit.<slot_key>" in brief
    assert "accept_simplification" in brief


def test_critique_brief_uses_spec_reference_image_over_directory_scan(tmp_path):
    """spec.yaml reference_image declaration must take precedence over directory scan."""
    example_dir = _write_example(tmp_path, section6="- invariant")

    # Create a spec-declared reference image at a non-default path
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    spec_ref = ref_dir / "foo.png"
    spec_ref.write_bytes(b"PNG")
    # Also place a different image that the directory scan would find first
    other_ref = ref_dir / "golden_target_001.png"
    other_ref.write_bytes(b"OTHER")

    # Rewrite spec.yaml to declare reference_image
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "style_profile: polymer-default\n"
        "reference_image: reference/foo.png\n",
        encoding="utf-8",
    )

    # All new source files must be older than the build PNG to pass freshness check
    old_time = 1_000_000.0
    for path in (spec_ref, other_ref, example_dir / "spec.yaml"):
        os.utime(path, (old_time, old_time))

    brief = generate_for(example_dir)

    assert "examples/review_demo/reference/foo.png" in brief
    # golden_target_001.png must NOT appear — spec takes precedence
    assert "golden_target_001.png" not in brief


def test_critique_brief_does_not_scan_reference_directory_without_spec_reference(
    tmp_path,
):
    """Reference grounding must be explicit in spec.yaml, not inferred from files."""
    example_dir = _write_example(tmp_path, section6="- invariant")
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    implicit_ref = ref_dir / "golden_target_001.png"
    implicit_ref.write_bytes(b"PNG")

    old_time = 1_000_000.0
    os.utime(implicit_ref, (old_time, old_time))

    brief = generate_for(example_dir)

    assert "Reference image (for drift detection)" not in brief
    assert "golden_target_001.png" not in brief


def test_critique_brief_allows_coordinate_hints_newer_than_png(tmp_path, capsys, monkeypatch):
    """coordinate_hints.yaml is critique context, not a render source."""
    example_dir = _write_example(tmp_path, section6="- invariant")
    hints = example_dir / "coordinate_hints.yaml"
    hints.write_text("metadata:\n  extraction_version: '0.3'\n", encoding="utf-8")
    # PNG is fresh against render sources but older than coordinate_hints.yaml.
    png_path = example_dir / "build" / "review_demo.png"
    old_time = 1_000_000.0
    png_time = 4_000_000_000.0
    for path in (
        example_dir / "review_demo.tex",
        example_dir / "briefing.md",
        example_dir / "spec.yaml",
    ):
        os.utime(path, (old_time, old_time))
    os.utime(png_path, (png_time, png_time))
    os.utime(hints, (png_time + 100, png_time + 100))

    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])
    assert main() == 0
    captured = capsys.readouterr()
    assert "run /fig_compile first" not in captured.err
    assert "# Critique brief — review_demo" in captured.out


def test_critique_brief_allows_reference_image_newer_than_png(
    tmp_path, capsys, monkeypatch
):
    """Reference image changes make critique stale, but do not make the render stale."""
    example_dir = _write_example(tmp_path, section6="- invariant")
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    reference = ref_dir / "foo.png"
    reference.write_bytes(b"PNG")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "style_profile: polymer-default\n"
        "reference_image: reference/foo.png\n",
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    old_time = 1_000_000.0
    png_time = 4_000_000_000.0
    newer_time = png_time + 100
    for path in (
        example_dir / "review_demo.tex",
        example_dir / "briefing.md",
        example_dir / "spec.yaml",
    ):
        os.utime(path, (old_time, old_time))
    os.utime(png_path, (png_time, png_time))
    os.utime(reference, (newer_time, newer_time))

    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])
    assert main() == 0
    captured = capsys.readouterr()
    assert "run /fig_compile first" not in captured.err
    assert "examples/review_demo/reference/foo.png" in captured.out


def test_critique_brief_blocks_missing_declared_reference_without_fallback(
    tmp_path, capsys, monkeypatch
):
    example_dir = _write_example(tmp_path, section6="- invariant")
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    (ref_dir / "golden_target_001.png").write_bytes(b"OTHER")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels: []\n"
        "style_profile: polymer-default\n"
        "reference_image: reference/missing.png\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sys, "argv", ["critique_brief.py", str(example_dir)])
    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "reference_image_missing: reference/missing.png" in captured.err
    assert "golden_target_001.png" not in captured.err


def test_critique_brief_adds_panel_reference_context_when_ref_and_bbox_present(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant", png=False)
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    Image.new("RGB", (40, 40), "white").save(ref_dir / "panel_a.png")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "    reference_image: reference/panel_a.png\n"
        "    bbox_pdf_cm: [0, 0, 3.5, 1.75]\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    _write_real_render_pair(example_dir)
    png_path = example_dir / "build" / "review_demo.png"
    newer_time = 4_000_000_000.0
    os.utime(png_path, (newer_time, newer_time))

    brief = generate_for(example_dir)

    assert "## Per-panel reference contexts" in brief
    assert "Panel `a`" in brief
    assert "`examples/review_demo/reference/panel_a.png`" in brief
    assert "`examples/review_demo/build/panel_crops/a.png`" in brief
    assert (example_dir / "build" / "panel_crops" / "a.png").is_file()


def test_critique_brief_strips_panel_reference_path_whitespace(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant", png=False)
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    Image.new("RGB", (40, 40), "white").save(ref_dir / "panel_a.png")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "    reference_image: ' reference/panel_a.png '\n"
        "    bbox_pdf_cm: [0, 0, 3.5, 1.75]\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    _write_real_render_pair(example_dir)
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "Panel `a`" in brief
    assert "`examples/review_demo/reference/panel_a.png`" in brief
    assert "Per-panel reference warnings" not in brief


def test_critique_brief_warns_and_skips_panel_reference_without_bbox(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    (ref_dir / "panel_a.png").write_bytes(b"PNG")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "    reference_image: reference/panel_a.png\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    newer_time = 4_000_000_000.0
    os.utime(png_path, (newer_time, newer_time))

    brief = generate_for(example_dir)

    assert "WARN" in brief
    assert "Panel `a` declares reference_image but no bbox_pdf_cm" in brief
    assert "Per-panel reference contexts" not in brief


def test_critique_brief_warns_and_skips_missing_panel_reference_without_bbox(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "    reference_image: reference/missing_panel.png\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "WARN" in brief
    assert "Panel `a` declares reference_image `reference/missing_panel.png`" in brief
    assert "Per-panel reference contexts" not in brief


def test_critique_brief_warns_and_skips_panel_bbox_without_reference_image(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "    bbox_pdf_cm: [0, 0, 3.5, 1.75]\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    newer_time = 4_000_000_000.0
    os.utime(png_path, (newer_time, newer_time))

    brief = generate_for(example_dir)

    assert "WARN" in brief
    assert "Panel `a` declares bbox_pdf_cm but no reference_image" in brief
    assert "Per-panel reference contexts" not in brief


def test_critique_brief_warns_when_skipped_panel_reference_is_newer_than_png(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    ref_path = ref_dir / "panel_a.png"
    ref_path.write_bytes(b"PNG")
    (example_dir / "spec.yaml").write_text(
        "name: review_demo\n"
        "panels:\n"
        "  - id: a\n"
        "    caption: demo panel\n"
        "    reference_image: reference/panel_a.png\n"
        "style_profile: polymer-default\n",
        encoding="utf-8",
    )
    old_time = 1_000_000.0
    for path in (
        example_dir / "review_demo.tex",
        example_dir / "briefing.md",
        example_dir / "spec.yaml",
    ):
        os.utime(path, (old_time, old_time))
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))
    os.utime(ref_path, (4_000_000_001.0, 4_000_000_001.0))

    brief = generate_for(example_dir)

    assert "Panel `a` declares reference_image but no bbox_pdf_cm" in brief


def test_critique_brief_includes_reference_conditioned_authoring_docs(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "authoring_contract.md").write_text(
        "# Authoring Contract\n\n"
        "## Theory Invariants\n\n"
        "- BLOCKER: keep topology linear.\n\n"
        "## Forbidden Transfers\n\n"
        "- Do not transfer network topology.\n\n"
        "## Source Limitations\n\n"
        "- coordinate_hints.yaml is absent.\n\n"
        "## Acceptance Rubric\n\n"
        "- BLOCKER rejects acceptance.\n",
        encoding="utf-8",
    )
    ref_dir = example_dir / "reference"
    ref_dir.mkdir()
    (ref_dir / "reference_pack.md").write_text(
        "# Reference Pack\n\n"
        "| File | Role | Use | Do Not Transfer |\n"
        "|---|---|---|---|\n"
        "| `reference/a.png` | anti_reference | motif only | Do Not Transfer topology |\n",
        encoding="utf-8",
    )
    (example_dir / "authoring_plan.md").write_text(
        "# Authoring Plan\n\n"
        "## Patch Order\n\n"
        "1. Fix Row2-BR2.\n\n"
        "## Human Checkpoints\n\n"
        "- Confirm manuscript chemistry.\n",
        encoding="utf-8",
    )
    (example_dir / "theory_guard.md").write_text(
        "# Theory Guard\n\n"
        "| ID | Severity | Claim | Check Method | Pass/Fail Evidence |\n"
        "|---|---|---|---|---|\n"
        "| TG-A-001 | BLOCKER | topology is linear | source review | pass |\n",
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "## Reference-conditioned authoring context" in brief
    assert "### Authoring Contract" in brief
    assert "- BLOCKER: keep topology linear." in brief
    assert "- Do not transfer network topology." in brief
    assert "### Reference Pack" in brief
    assert "| `reference/a.png` | anti_reference | motif only | Do Not Transfer topology |" in brief
    assert "### Authoring Plan" in brief
    assert "1. Fix Row2-BR2." in brief
    assert "- Confirm manuscript chemistry." in brief
    assert "### Theory Guard" in brief
    assert "| TG-A-001 | BLOCKER | topology is linear | source review | pass |" in brief


def test_critique_brief_includes_subregion_active_set(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "subregion_iteration_log.md").write_text(
        "# Sub-Region Iteration Log\n\n"
        "## Active Target Set\n\n"
        "| State | Sub-region ID | Evidence | Notes |\n"
        "|---|---|---|---|\n"
        "| active target | G-2, G-7 | review | patch electrode and gap |\n"
        "| named but stable | D-1..D-3 | log | stable |\n\n"
        "## Iteration Log\n\n"
        "| Iteration | Sub-region ID | Problem | Patch Summary | Result | Follow-up |\n"
        "|---|---|---|---|---|---|\n"
        "| v7 | G-2, G-7 | setup weak | widened gap | improved | recheck |\n",
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "### Sub-region Active Set" in brief
    assert "- Active targets: G-2, G-7" in brief
    assert "- Observed patch units: G-2, G-7" in brief


def test_critique_brief_includes_reference_calibrated_pack(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "critique_reference_pack.yaml").write_text(
        """
schema: figure-agent.critique-reference-pack.v1
fixture: review_demo
target_journal: Nature Materials
reference_class: mechanism_schematic
visual_ambition: high_impact_candidate
comparison_references:
  - id: R001
    source: human_note
    path_or_citation: target journal exemplar set
    role: journal_register
must_match_traits:
  - id: T001
    trait: each panel reads as one connected mechanism story
    reference_id: R001
must_avoid_traits:
  - id: A001
    trait: dense apparatus boxes without visual hierarchy
    severity: MAJOR
calibration_questions:
  - id: Q001
    question: Would this pass a first-glance Nature Materials mechanism read?
""".lstrip(),
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "## Reference-Calibrated Top-Tier Comparison" in brief
    assert "Target journal: Nature Materials" in brief
    assert "Visual ambition: high_impact_candidate" in brief
    assert "T001" in brief
    assert "each panel reads as one connected mechanism story" in brief
    assert "A001" in brief
    assert "dense apparatus boxes without visual hierarchy" in brief
    assert "Q001" in brief
    assert "Would this pass a first-glance Nature Materials mechanism read?" in brief
    assert "reference_calibration:" in brief
    assert "reference_pack_hash: sha256:" in brief
    assert "reference_class: mechanism_schematic" in brief
    assert "visual_ambition: high_impact_candidate" in brief
    assert "score_basis: current_artifact_vs_pack" in brief
    assert "limiting_reference_traits:" in brief
    assert "scores cite the reference pack" in brief


def test_critique_brief_includes_reference_learning_contract(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "critique_reference_pack.yaml").write_text(
        """
schema: figure-agent.critique-reference-pack.v1
fixture: review_demo
target_journal: Nature Materials
reference_class: mechanism_schematic
visual_ambition: high_impact_candidate
comparison_references:
  - id: R001
    source: human_note
    path_or_citation: target journal exemplar set
    role: journal_register
must_match_traits:
  - id: T001
    trait: compact journal-grade hierarchy
    reference_id: R001
must_avoid_traits:
  - id: A001
    trait: generic clip-art apparatus boxes
    severity: MAJOR
calibration_questions:
  - id: Q001
    question: Does this read as a journal mechanism figure?
reference_learning:
  schema: figure-agent.reference-learning.v1
  references:
    - path: reference/example.png
      roles:
        - style_anchor
        - typography_reference
      allowed_transfer:
        - restrained palette
        - compact label hierarchy
      forbidden_transfer:
        - copy component topology
        - introduce unbriefed hardware
        - override physics story
      rationale: Use as a journal-tone anchor, not a content authority.
""".lstrip(),
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "## Reference Learning Contract" in brief
    assert "schema: figure-agent.critique.v1.16" in brief
    assert "rubric_version: figure-agent.critique-rubric.v1.16" in brief
    assert "References are learning sources, not copy targets." in brief
    assert "reference/example.png" in brief
    assert "roles=style_anchor, typography_reference" in brief
    assert "Allowed transfer: restrained palette; compact label hierarchy" in brief
    assert (
        "Forbidden transfer: copy component topology; introduce unbriefed hardware; "
        "override physics story"
    ) in brief
    assert "Use as a journal-tone anchor, not a content authority." in brief
    assert "Reference-learning accountability required:" in brief
    assert (
        "state what was learned, what was rejected, and whether the current figure "
        "over-copies or under-learns"
    ) in brief


def test_critique_brief_includes_unintended_visible_anomaly_contract(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "critique_reference_pack.yaml").write_text(
        """
schema: figure-agent.critique-reference-pack.v1
fixture: review_demo
target_journal: Nature Materials
reference_class: mechanism_schematic
visual_ambition: high_impact_candidate
comparison_references:
  - id: R001
    source: human_note
    path_or_citation: target journal exemplar set
    role: journal_register
must_match_traits:
  - id: T001
    trait: compact journal-grade hierarchy
    reference_id: R001
must_avoid_traits:
  - id: A001
    trait: generic clip-art apparatus boxes
    severity: MAJOR
calibration_questions:
  - id: Q001
    question: Does this read as a journal mechanism figure?
reference_learning:
  schema: figure-agent.reference-learning.v1
  references:
    - path: reference/example.png
      roles:
        - style_anchor
      allowed_transfer:
        - restrained palette
      forbidden_transfer:
        - copy component topology
      rationale: Use as a journal-tone anchor only.
""".lstrip(),
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "unintended_visible_anomaly: none | present | uncertain" in brief
    assert "anomaly_rationale:" in brief
    assert "anomaly_link:" in brief
    for example in (
        "stray bond",
        "unintended line continuation",
        "accidental component grouping",
        "misleading reference transfer",
        "phantom boundary or texture",
    ):
        assert example in brief


def test_critique_brief_includes_reference_aesthetic_metrics_summary(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    reference_dir = example_dir / "reference"
    reference_dir.mkdir()
    Image.new("RGB", (120, 80), "black").save(reference_dir / "example.png")
    (example_dir / "critique_reference_pack.yaml").write_text(
        """
schema: figure-agent.critique-reference-pack.v1
fixture: review_demo
target_journal: Nature Materials
reference_class: mechanism_schematic
visual_ambition: high_impact_candidate
comparison_references:
  - id: R001
    source: human_note
    path_or_citation: reference/example.png
    role: journal_register
must_match_traits:
  - id: T001
    trait: compact journal-grade hierarchy
    reference_id: R001
must_avoid_traits:
  - id: A001
    trait: generic clip-art apparatus boxes
    severity: MAJOR
calibration_questions:
  - id: Q001
    question: Does this read as a journal mechanism figure?
reference_learning:
  schema: figure-agent.reference-learning.v1
  references:
    - path: reference/example.png
      roles:
        - style_anchor
      allowed_transfer:
        - restrained palette
      forbidden_transfer:
        - copy component topology
      rationale: Use as a journal-tone anchor only.
""".lstrip(),
        encoding="utf-8",
    )
    build_reference_aesthetic_metrics(example_dir)
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "## Reference Aesthetic Metrics" in brief
    assert "Evaluation state:" in brief
    assert "Evidence path: `build/reference_aesthetic_metrics.json`" in brief
    assert "Comparison count: 1" in brief


def test_critique_brief_includes_external_second_opinion_review(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _enable_external_vision_review(example_dir)
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "## External Second-Opinion Vision Review" in brief
    assert "Reviewer: Gemini manual second pass" in brief
    assert "Confidence: medium" in brief
    assert "EV001" in brief
    assert "external reviewer sees a possible near-miss label conflict" in brief
    assert "Conflicts must route to human review" in brief


def test_critique_brief_rejects_malformed_external_vision_review(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    spec_path = example_dir / "spec.yaml"
    spec_path.write_text(
        spec_path.read_text(encoding="utf-8") + "external_vision_review: true\n",
        encoding="utf-8",
    )
    (example_dir / "external_vision_review.yaml").write_text("schema: [", encoding="utf-8")
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    try:
        generate_for(example_dir)
    except critique_brief.CritiqueBriefError as exc:
        assert "external_vision_review.yaml invalid" in str(exc)
    else:
        raise AssertionError("expected CritiqueBriefError")


def test_critique_brief_includes_svg_polish_aesthetic_delta(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _write_svg_polish_delta_fixture(example_dir)
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "## SVG Polish Aesthetic Delta" in brief
    assert "Host LLM MUST compare the before/after polish images" in brief
    assert "`polish/aesthetic_delta/before.png`" in brief
    assert "`polish/aesthetic_delta/after.png`" in brief
    assert "`polish/aesthetic_delta/diff.png`" in brief
    assert "operation_ids: R001" in brief
    assert "Did journal polish improve?" in brief
    assert "Did any scientific semantics change?" in brief
    assert "schema: figure-agent.critique.v1.16" in brief
    assert "rubric_version: figure-agent.critique-rubric.v1.16" in brief
    assert "svg_polish_delta_audit:" in brief
    assert "delta_image_audit_log:" in brief
    assert "aesthetic_gate_audit:" in brief
    assert "maturity_restraint | visual_hierarchy" in brief


def test_critique_brief_includes_paper_wide_aesthetic_context(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _enable_paper_aesthetic_context(example_dir)
    (example_dir / "aesthetic_intent.yaml").write_text(
        """
schema: figure-agent.aesthetic-intent.v1
fixture: review_demo
target_journal: Nature Materials
visual_maturity: editorial
density: balanced
reference_style: multipanel_story
design_principles:
  - id: mature_restraint
    instruction: avoid cartoon-like oversized labels and decorative gradients
must_avoid:
  - id: toy_diagram
    pattern: rounded generic blocks and unmodulated flat color
    severity: MAJOR
polish_triggers:
  - id: svg_micro_polish
    condition: semantically correct TikZ lacks print-scale optical refinement
    recommended_path: ready_for_svg_polish
""".lstrip(),
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "## Paper-Wide Aesthetic Context" in brief
    assert "Paper id: paper-demo" in brief
    assert "Target journal: Nature Communications" in brief
    assert "Visual maturity: editorial" in brief
    assert "Density: balanced" in brief
    assert "Figure role: overview_mechanism" in brief
    assert "restrained_palette priority=required" in brief
    assert "typography_authority priority=required" in brief
    assert "series_drift severity=MAJOR" in brief
    assert "top_tier_audit.cross_panel_semantic_grammar" in brief
    assert "top_tier_audit.aesthetic_coherence" in brief
    assert "editorial_art_direction.visual_identity" in brief
    assert "must cite at least one exact paper-wide anchor" in brief
    assert "restrained_palette, typography_authority" in brief
    assert brief.index("## Paper-Wide Aesthetic Context") < brief.index(
        "## Aesthetic Intent Calibration"
    )


def test_critique_brief_omits_paper_wide_context_without_opt_in(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Paper-Wide Aesthetic Context" not in brief


def test_critique_brief_reports_invalid_paper_wide_context(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    pack_path = _enable_paper_aesthetic_context(example_dir)
    pack_path.write_text("schema: [", encoding="utf-8")
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    try:
        generate_for(example_dir)
    except critique_brief.CritiqueBriefError as exc:
        assert "paper_aesthetic_context" in str(exc)
    else:
        raise AssertionError("expected CritiqueBriefError")


def test_critique_brief_includes_journal_art_direction_playbook(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _enable_journal_art_direction_playbook(example_dir)
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "## Journal Art-Direction Playbook" in brief
    assert "Playbook id: nc-main-text" in brief
    assert "Target journal: Nature Communications" in brief
    assert "Venue context: main_text" in brief
    assert "Visual maturity: restrained" in brief
    assert "editorial_restraint priority=required dimension=maturity" in brief
    assert "typography_authority priority=required dimension=typography" in brief
    assert "toy_schematic severity=MAJOR route=continue_tikz" in brief
    assert "svg_for_optical_finish path=ready_for_svg_polish" in brief
    assert "must cite exact playbook anchors" in brief
    assert "schema: figure-agent.critique.v1.16" in brief
    assert "rubric_version: figure-agent.critique-rubric.v1.16" in brief
    assert "journal_art_direction_playbook_audit:" in brief


def test_critique_brief_uses_v1_16_when_playbook_and_aesthetic_intent_v2_with_crops(
    tmp_path,
):
    example_dir = _write_example(tmp_path, section6="- invariant")
    _enable_journal_art_direction_playbook(example_dir)
    (example_dir / "aesthetic_intent.yaml").write_text(
        """
schema: figure-agent.aesthetic-intent.v2
fixture: review_demo
target_journal: Nature Materials
visual_maturity: editorial
density: balanced
reference_style: multipanel_story
design_principles:
  - id: mature_restraint
    instruction: avoid cartoon-like oversized labels and decorative gradients
must_avoid:
  - id: toy_diagram
    pattern: rounded generic blocks and unmodulated flat color
    severity: MAJOR
polish_triggers:
  - id: svg_micro_polish
    condition: semantically correct TikZ lacks print-scale optical refinement
    recommended_path: ready_for_svg_polish
aesthetic_levers:
  - id: maturity_restraint
    dimension: maturity
    intent: Make the figure read as controlled editorial science illustration.
    priority: required
    positive_signals:
      - restrained label scale
    anti_patterns:
      - poster-like saturation
    allowed_adjustments:
      - reduce non-essential label prominence
    forbidden_adjustments:
      - change mechanism meaning
    default_route: tikz_patch
""".lstrip(),
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "schema: figure-agent.critique.v1.16" in brief
    assert "rubric_version: figure-agent.critique-rubric.v1.16" in brief
    assert "journal_art_direction_playbook_audit:" in brief
    assert "aesthetic_lever_audit:" in brief


def test_critique_brief_omits_journal_playbook_without_opt_in(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Journal Art-Direction Playbook" not in brief


def test_critique_brief_reports_invalid_journal_playbook(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    pack_path = _enable_journal_art_direction_playbook(example_dir)
    pack_path.write_text("schema: [", encoding="utf-8")
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    try:
        generate_for(example_dir)
    except critique_brief.CritiqueBriefError as exc:
        assert "journal_art_direction_playbook" in str(exc)
    else:
        raise AssertionError("expected CritiqueBriefError")


def test_critique_brief_includes_aesthetic_intent_calibration(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "aesthetic_intent.yaml").write_text(
        """
schema: figure-agent.aesthetic-intent.v1
fixture: review_demo
target_journal: Nature Materials
visual_maturity: editorial
density: balanced
reference_style: multipanel_story
design_principles:
  - id: mature_restraint
    instruction: avoid cartoon-like oversized labels and decorative gradients
must_avoid:
  - id: toy_diagram
    pattern: rounded generic blocks and unmodulated flat color
    severity: MAJOR
polish_triggers:
  - id: svg_micro_polish
    condition: semantically correct TikZ lacks print-scale optical refinement
    recommended_path: ready_for_svg_polish
""".lstrip(),
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "## Aesthetic Intent Calibration" in brief
    assert "Target journal: Nature Materials" in brief
    assert "Visual maturity: editorial" in brief
    assert "Density: balanced" in brief
    assert "Reference style: multipanel_story" in brief
    assert "mature_restraint: avoid cartoon-like oversized labels" in brief
    assert "toy_diagram severity=MAJOR" in brief
    assert "svg_micro_polish path=ready_for_svg_polish" in brief
    assert "top_tier_audit.aesthetic_coherence" in brief
    assert "editorial_art_direction.visual_identity" in brief
    assert "editorial_art_direction.aesthetic_risk" in brief
    assert "must cite at least one exact aesthetic intent anchor" in brief


def test_critique_brief_includes_v2_aesthetic_lever_grammar(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "aesthetic_intent.yaml").write_text(
        """
schema: figure-agent.aesthetic-intent.v2
fixture: review_demo
target_journal: Nature Materials
visual_maturity: editorial
density: balanced
reference_style: multipanel_story
design_principles:
  - id: mature_restraint
    instruction: avoid cartoon-like oversized labels and decorative gradients
must_avoid:
  - id: toy_diagram
    pattern: rounded generic blocks and unmodulated flat color
    severity: MAJOR
polish_triggers:
  - id: svg_micro_polish
    condition: semantically correct TikZ lacks print-scale optical refinement
    recommended_path: ready_for_svg_polish
aesthetic_levers:
  - id: maturity_restraint
    dimension: maturity
    intent: Make the figure read as controlled editorial science illustration.
    priority: required
    positive_signals:
      - restrained label scale
    anti_patterns:
      - poster-like saturation
    allowed_adjustments:
      - reduce non-essential label prominence
    forbidden_adjustments:
      - change mechanism meaning
    default_route: tikz_patch
""".lstrip(),
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "## Aesthetic Lever Grammar" in brief
    assert "## Aesthetic Intent Calibration" not in brief
    assert "schema: figure-agent.critique.v1.16" in brief
    assert "rubric_version: figure-agent.critique-rubric.v1.16" in brief
    assert "aesthetic_lever_audit:" in brief
    assert "remaining_tikz_lever:" in brief
    assert "svg_polish_candidate_reason:" in brief
    assert "maturity_restraint" in brief
    assert "dimension=maturity priority=required route=tikz_patch" in brief
    assert "Generic prose such as \"improve polish\" is invalid" in brief


def test_critique_brief_uses_v1_16_for_v1_aesthetic_intent_with_crops(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "aesthetic_intent.yaml").write_text(
        """
schema: figure-agent.aesthetic-intent.v1
fixture: review_demo
target_journal: Nature Materials
visual_maturity: editorial
density: balanced
reference_style: multipanel_story
design_principles:
  - id: mature_restraint
    instruction: avoid cartoon-like oversized labels and decorative gradients
must_avoid:
  - id: toy_diagram
    pattern: rounded generic blocks and unmodulated flat color
    severity: MAJOR
polish_triggers:
  - id: svg_micro_polish
    condition: semantically correct TikZ lacks print-scale optical refinement
    recommended_path: ready_for_svg_polish
""".lstrip(),
        encoding="utf-8",
    )
    png_path = example_dir / "build" / "review_demo.png"
    os.utime(png_path, (4_000_000_000.0, 4_000_000_000.0))

    brief = generate_for(example_dir)

    assert "## Aesthetic Intent Calibration" in brief
    assert "## Aesthetic Lever Grammar" not in brief
    assert "schema: figure-agent.critique.v1.16" in brief
    assert "rubric_version: figure-agent.critique-rubric.v1.16" in brief
    assert "aesthetic_lever_audit:" not in brief


def test_critique_brief_omits_aesthetic_intent_calibration_when_missing(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Aesthetic Intent Calibration" not in brief


def test_critique_brief_reports_malformed_aesthetic_intent(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "aesthetic_intent.yaml").write_text("schema: [", encoding="utf-8")

    try:
        generate_for(example_dir)
    except critique_brief.CritiqueBriefError as exc:
        assert "aesthetic_intent.yaml" in str(exc)
    else:
        raise AssertionError("expected CritiqueBriefError")


def test_critique_brief_omits_reference_calibrated_pack_when_missing(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")

    brief = generate_for(example_dir)

    assert "## Reference-Calibrated Top-Tier Comparison" not in brief


def test_critique_brief_reports_malformed_reference_calibration_pack(tmp_path):
    example_dir = _write_example(tmp_path, section6="- invariant")
    (example_dir / "critique_reference_pack.yaml").write_text("schema: [", encoding="utf-8")

    try:
        generate_for(example_dir)
    except critique_brief.CritiqueBriefError as exc:
        assert "critique_reference_pack.yaml" in str(exc)
    else:
        raise AssertionError("expected CritiqueBriefError")
