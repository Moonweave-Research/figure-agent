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
    assert "PDMS" in prompt
    assert "Sulfur Polymer" in prompt
    assert isinstance(audit, list)
