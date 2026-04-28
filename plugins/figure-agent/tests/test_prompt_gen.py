"""Smoke tests for prompt_gen — parsers and full prompt composition on
the fig3_trapping_concept scaffold."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from prompt_gen import compose_prompt, generate_for, main, parse_briefing, parse_spec  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_parse_spec_minimal():
    text = """name: fig3_trapping_concept
panels:
  - id: a
    caption: PDMS
  - id: b
    caption: Sulfur Polymer
style_profile: polymer-default
selected_preview: null
"""
    spec = parse_spec(text)
    assert spec["name"] == "fig3_trapping_concept"
    assert spec["style_profile"] == "polymer-default"
    assert len(spec["panels"]) == 2
    assert spec["panels"][0] == {"id": "a", "caption": "PDMS"}
    assert spec["panels"][1] == {"id": "b", "caption": "Sulfur Polymer"}


def test_parse_briefing_strips_html_comments():
    text = """# Title

> dogfooding note line.

## 1. What does this figure show?

This is real content.
<!-- TODO: ignored -->

## 2. Vocabulary

<!-- TODO: also ignored -->
"""
    sections = parse_briefing(text)
    assert sections[1][1] == "This is real content."
    assert sections[2][1] == ""


def test_compose_prompt_uses_topic_and_panels():
    spec = {"name": "demo", "panels": [{"id": "a", "caption": "left"}]}
    briefing = {
        1: ("Topic", "Two-panel band diagram comparing materials."),
        3: ("Composition", "- panel a shows clean bandgap\n- panel b shows trap states"),
    }
    out = compose_prompt(spec, briefing)
    assert "Two-panel band diagram" in out
    assert "(a) left" in out
    assert "panel a shows clean bandgap" in out
    assert "Do NOT include:" in out


def test_compose_prompt_surfaces_physics_invariants_before_include():
    spec = {"name": "demo", "panels": []}
    briefing = {
        1: ("Topic", "Trap-assisted retention schematic."),
        3: ("Composition", "- show CB, trap level, and VB"),
        6: (
            "Physics invariants",
            "- E_t stays inside the bandgap\n"
            "- capture arrow direction is CB to trap, not the reverse",
        ),
    }

    out = compose_prompt(spec, briefing)

    invariants_idx = out.index("Preserve these scientific constraints.")
    include_idx = out.index("Include:")
    assert invariants_idx < include_idx
    assert "Physics invariants" not in out
    assert "- E_t stays inside the bandgap" in out
    assert "- capture arrow direction is CB to trap, not the reverse" in out


def test_compose_prompt_strips_markdown_bold_from_topic():
    spec = {"name": "demo", "panels": []}
    briefing = {
        1: ("Topic", "Show **trap-based retention** mechanism."),
        3: ("Composition", "- demo bullet"),
    }
    out = compose_prompt(spec, briefing)
    assert "**trap-based retention**" not in out
    assert "trap-based retention" in out


def test_generate_for_fig3_scaffold_runs():
    example_dir = REPO_ROOT / "examples" / "fig3_trapping_concept"
    if not (example_dir / "spec.yaml").exists():
        return  # scaffold not present in this checkout
    prompt, audit = generate_for(example_dir)
    assert "fig3_trapping_concept" in prompt
    assert "CB" in prompt and "VB" in prompt
    assert "deep trap" in prompt.lower()
    assert "polarization" in prompt.lower()
    assert isinstance(audit, list)


def test_generate_for_tmp_path_normalizes_prompt_text(tmp_path):
    example_dir = tmp_path / "example"
    example_dir.mkdir()
    (example_dir / "spec.yaml").write_text(
        """name: prompt_normalization_demo
panels:
  - id: a
    caption: S60-S85 comparison
style_profile: polymer-default
selected_preview: null
"""
    )
    (example_dir / "briefing.md").write_text(
        """## 1. Topic

Use 4 dots for trapped electrons.

## 2. Vocabulary

CB, VB, HOMO, LUMO, E_t, kT

## 3. Composition

- Show three layers with arrows.
- Compare S60-S85 panels.
- Gate width 200 by 50 pixels.
- Use a 200 nm film.
- Use 2 dots for shallow traps.
- Sketch a 70/30 copolymer blend.
- Plot n vs composition with error bars.

## 4. Forbidden

skip
"""
    )

    prompt, audit = generate_for(example_dir)
    categories = [ev.category for ev in audit]

    assert "a few dots" in prompt
    assert "a small cluster of dots" in prompt
    assert "4 dots" not in prompt
    assert "stacked layers" in prompt
    assert "three layers" not in prompt
    assert "different material compositions" in prompt
    assert "S60-S85" not in prompt
    assert "general geometry" in prompt
    assert "200 by 50" not in prompt
    assert "thin film" in prompt
    assert "200 nm" not in prompt
    assert "copolymer material" in prompt
    assert "70/30" not in prompt
    assert "CB" in prompt and "VB" in prompt
    assert "HOMO" in prompt and "LUMO" in prompt
    assert "count" in categories
    assert "sample_label" in categories
    assert "geometry" in categories
    assert "composition_ratio" in categories
    assert "domain_term" in categories
    assert any("plot" in category for category in categories)


def test_generate_for_preserves_physics_invariants_verbatim(tmp_path):
    example_dir = tmp_path / "example"
    example_dir.mkdir()
    (example_dir / "spec.yaml").write_text(
        """name: invariant_preservation_demo
panels: []
style_profile: polymer-default
selected_preview: null
""",
        encoding="utf-8",
    )
    (example_dir / "briefing.md").write_text(
        """## 1. Topic

Use 4 dots in the composition.

## 3. Composition

- Show three layers with 1 arrow.

## 6. Physics invariants

**Physics invariants:**
- 3 layers must remain in order.
- 1 arrow must point from CB to trap.
""",
        encoding="utf-8",
    )

    prompt, audit = generate_for(example_dir)
    invariant_kept = [ev for ev in audit if ev.category == "physics_invariant"]

    invariant_idx = prompt.index("Preserve these scientific constraints.")
    include_idx = prompt.index("Include:")
    invariant_block = prompt[invariant_idx:include_idx]
    include_block = prompt[include_idx:]

    assert "Physics invariants:" not in invariant_block
    assert "- 3 layers must remain in order." in invariant_block
    assert "- 1 arrow must point from CB to trap." in invariant_block
    assert "stacked layers must remain in order" not in invariant_block
    assert "one directional arrow must point" not in invariant_block
    assert invariant_idx < include_idx
    assert "stacked layers" in include_block
    assert "one directional arrow" in include_block
    assert {ev.original for ev in invariant_kept} == {"3 layers", "1 arrow"}


def test_skip_keyword_in_style_section_omits_body():
    """§5 'skip' should NOT leak into the prompt's Style block."""
    spec = {"name": "demo", "panels": [{"id": "a", "caption": "x"}]}
    briefing = {
        1: ("Topic", "demo topic"),
        3: ("Composition", "- demo bullet"),
        5: ("Style", "skip — Nature default applied"),
    }
    out = compose_prompt(spec, briefing)
    assert "skip" not in out.lower().split("style:")[1].split("do not include:")[0]


def test_negative_section_with_explicit_OK_bullet_excluded():
    """Lines marked 'OK' / '노출 OK' / '허용' must not appear in negative prompt."""
    spec = {"name": "demo", "panels": [{"id": "a", "caption": "x"}]}
    briefing = {
        1: ("Topic", "demo topic"),
        3: ("Composition", "- demo bullet"),
        4: (
            "Forbidden",
            "- exact numeric values\n- setup detail: 노출 OK\n"
            "- domain abbreviations: OK\n- key claim points: 허용",
        ),
    }
    out = compose_prompt(spec, briefing)
    negative = out.split("Do NOT include:")[1]
    assert "exact numeric values" in negative
    assert "노출 OK" not in negative
    assert "허용" not in negative


def test_footer_after_horizontal_rule_excluded():
    """Content below a `---` rule (footer instructions) must not contaminate §5."""
    text = """## 5. Style

skip

---

When this briefing is filled, run /fig_prompt to generate the prompt.
"""
    sections = parse_briefing(text)
    body = sections[5][1]
    assert "skip" in body
    assert "When this briefing is filled" not in body
    assert "/fig_prompt" not in body


def test_markdown_bold_stripped_in_bullets():
    """Markdown `**bold**` must be flattened to plain text."""
    spec = {"name": "demo", "panels": [{"id": "a", "caption": "x"}]}
    briefing = {
        1: ("Topic", "demo"),
        3: ("Composition", "- panel **(a)** shows decay\n- panel **(b)** shows peak"),
    }
    out = compose_prompt(spec, briefing)
    assert "**(a)**" not in out
    assert "**(b)**" not in out
    assert "panel (a) shows decay" in out
    assert "panel (b) shows peak" in out


def test_bare_label_headers_are_not_emitted_as_prompt_bullets():
    spec = {"name": "demo", "panels": []}
    briefing = {
        1: ("Topic", "demo"),
        3: (
            "Composition",
            "**Element 배치 (energy-ordered, top→bottom):**\n"
            "- CB (conduction band): 수평 청색 선, 상단\n"
            "**Arrows:**\n"
            "- Injection arrow: 좌측 외곽 → CB level로 진입\n"
            "**Physics constraints (보존):**\n"
            "- E_t는 반드시 bandgap 내부",
        ),
        4: (
            "Normalize",
            "**Image-gen이 과하게 literal하게 따라가면 안 되는 항목 (정규화 audit에 포함):**\n"
            "- Exact trap depth value: generalize as mid-gap",
        ),
    }

    out = compose_prompt(spec, briefing)

    assert "- Element 배치 (energy-ordered, top→bottom):" not in out
    assert "- Arrows:" not in out
    assert "- Physics constraints (보존):" not in out
    assert (
        "- Image-gen이 과하게 literal하게 따라가면 안 되는 항목 (정규화 audit에 포함):"
        not in out
    )
    assert "- CB (conduction band): 수평 청색 선, 상단" in out
    assert "- Injection arrow: 좌측 외곽 → CB level로 진입" in out
    assert "- E_t는 반드시 bandgap 내부" in out
    assert "- Exact trap depth value: generalize as mid-gap" in out


def test_main_prints_prompt_audit_and_next_steps_to_stdout_in_spec_order(
    tmp_path, capsys, monkeypatch
):
    example_dir = tmp_path / "example"
    example_dir.mkdir()
    (example_dir / "spec.yaml").write_text(
        """name: stdout_order_demo
panels:
  - id: a
    caption: demo panel
style_profile: polymer-default
selected_preview: null
""",
        encoding="utf-8",
    )
    (example_dir / "briefing.md").write_text(
        """## 1. Topic

Use 4 dots for trapped electrons.

## 3. Composition

- demo composition
""",
        encoding="utf-8",
    )

    monkeypatch.setattr(sys, "argv", ["prompt_gen.py", str(example_dir)])
    assert main() == 0

    captured = capsys.readouterr()
    stdout = captured.out
    assert captured.err == ""
    prompt_idx = stdout.index("=== NORMALIZED PROMPT (copy below for external tool) ===")
    end_idx = stdout.index("=== END PROMPT ===")
    audit_idx = stdout.index("Normalization audit:")
    next_idx = stdout.index("Next steps:")
    assert prompt_idx < end_idx < audit_idx < next_idx
