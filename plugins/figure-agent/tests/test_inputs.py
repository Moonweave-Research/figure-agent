"""Tests for scripts/inputs.py — parse_spec and parse_briefing contract."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from inputs import parse_briefing, parse_spec  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_parse_spec_minimal():
    text = """name: fig3_trapping_concept
panels:
  - id: a
    caption: PDMS
  - id: b
    caption: Sulfur Polymer
style_profile: polymer-default
"""
    spec = parse_spec(text)
    assert spec["name"] == "fig3_trapping_concept"
    assert spec["style_profile"] == "polymer-default"
    assert len(spec["panels"]) == 2
    assert spec["panels"][0] == {"id": "a", "caption": "PDMS"}
    assert spec["panels"][1] == {"id": "b", "caption": "Sulfur Polymer"}


def test_parse_spec_empty_text_returns_default():
    assert parse_spec("") == {"panels": []}


def test_parse_spec_comments_only_returns_default():
    assert parse_spec("# comment\n") == {"panels": []}


def test_parse_spec_non_dict_root_returns_default():
    assert parse_spec("- a\n- b\n") == {"panels": []}


def test_parse_spec_panels_list_preserved():
    text = """name: multi
panels:
  - id: a
    caption: First
  - id: b
    caption: Second
  - id: c
    caption: Third
"""
    spec = parse_spec(text)
    assert len(spec["panels"]) == 3
    assert spec["panels"][2] == {"id": "c", "caption": "Third"}


def test_parse_briefing_basic_split():
    text = """## 1. Topic

This is the topic body.

## 6. Physics invariants

These are the invariants.
"""
    sections = parse_briefing(text)
    assert 1 in sections
    assert 6 in sections
    assert sections[1][1] == "This is the topic body."
    assert sections[6][1] == "These are the invariants."


def test_parse_briefing_accepts_section_symbol_headings():
    text = """# Briefing

> metadata blockquote should not become section content

---

## §1. Figure identity

This is the author intent body.

## §3. Plot-vs-schematic balance

This is the composition body.
"""
    sections = parse_briefing(text)

    assert sections[1] == ("Figure identity", "This is the author intent body.")
    assert sections[3] == (
        "Plot-vs-schematic balance",
        "This is the composition body.",
    )


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


def test_parse_spec_block_scalar_preserved():
    text = """name: test
selection_notes: |
  Line 1
  Line 2
  Line 3
"""
    spec = parse_spec(text)
    expected = "Line 1\nLine 2\nLine 3\n"
    assert spec["selection_notes"] == expected


def test_parse_spec_malformed_panels_coerced():
    text = """name: test
panels: "not a list"
"""
    spec = parse_spec(text)
    assert spec["panels"] == []


def test_parse_spec_panels_with_non_dict_elements_filtered():
    text = """name: test
panels:
  - id: a
    caption: Good
  - "bad string element"
  - id: b
    caption: Also good
"""
    spec = parse_spec(text)
    assert len(spec["panels"]) == 2
    assert spec["panels"][0]["id"] == "a"
    assert spec["panels"][1]["id"] == "b"


def test_parse_spec_accepts_panel_reference_image_and_normalizes_bbox_pdf_cm():
    text = """name: panel_refs
panels:
  - id: row1
    caption: First row
    reference_image: reference/row1.png
    bbox_pdf_cm: [0, 1.25, "3.5", 4]
"""
    spec = parse_spec(text)

    assert spec["panels"] == [
        {
            "id": "row1",
            "caption": "First row",
            "reference_image": "reference/row1.png",
            "bbox_pdf_cm": [0.0, 1.25, 3.5, 4.0],
        }
    ]


def test_parse_spec_rejects_invalid_panel_bbox_pdf_cm():
    import pytest

    text = """name: panel_refs
panels:
  - id: row1
    caption: First row
    reference_image: reference/row1.png
    bbox_pdf_cm: [0, 1, 2]
"""
    with pytest.raises(ValueError, match="bbox_pdf_cm"):
        parse_spec(text)


def test_parse_spec_real_fig3_fixture_pinned():
    fixture = REPO_ROOT / "examples" / "fig3_trapping_concept" / "spec.yaml"
    if not fixture.exists():
        return
    spec = parse_spec(fixture.read_text(encoding="utf-8"))
    expected_selection_notes = (
        "Round 2 (schematic intent, post-reset). Compared chatgpt_b01 vs nanobanana_b01.\n"
        "ChatGPT preferred for: clean Nature-style band diagram, accurate label placement\n"
        "(CB/LUMO + VB/HOMO unified — Nano Banana split LUMO and CB into separate\n"
        'redundant lines), correct trapped-electron positions (Nano Banana drew "trapped\n'
        'electrons" on CB level — physically wrong), elegant polarization-response glyph\n'
        "(dipole + ⊖→⊕ in dashed oval), distinct shallow-vs-deep trap visualization with\n"
        'precise capture/escape arrows. Nano Banana also had label noise ("cond band\n'
        '(CB)" duplication, "low-based dielectric" typo for "low-trap dielectric").\n'
        "Previous attempt (data figure) archived under previews/_previous_attempt_data_figure/.\n"
    )
    assert spec == {
        "name": "fig3_trapping_concept",
        "panels": [
            {"id": "a", "caption": "PDMS — clean bandgap (no trap states)"},
            {"id": "b", "caption": "Sulfur Polymer — deep trap states in bandgap"},
        ],
        "style_profile": "polymer-default",
        # Cleared to None after the v0.1.7.2 dogfood cleanup; the original
        # preview file was moved out of previews/ but selection_notes still
        # preserves the historical decision record.
        "selected_preview": None,
        "selection_notes": expected_selection_notes,
    }


def test_parse_spec_raises_for_unknown_style_profile() -> None:
    import pytest

    with pytest.raises(ValueError, match="Unknown style_profile"):
        parse_spec("name: test\npanels: []\nstyle_profile: unknown-profile\n")


def test_parse_spec_accepts_known_style_profiles() -> None:
    for profile in ("polymer-default", "polymer-paper"):
        result = parse_spec(f"name: test\npanels: []\nstyle_profile: {profile}\n")
        assert result["style_profile"] == profile
