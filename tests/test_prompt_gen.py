"""Smoke tests for prompt_gen — parsers and full prompt composition on
the fig3_trapping_concept scaffold."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from prompt_gen import compose_prompt, generate_for, parse_briefing, parse_spec  # noqa: E402

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
