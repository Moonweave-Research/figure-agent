"""Prompt-normalization tests for redact.redact() in figure-agent v0.1."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from redact import redact  # noqa: E402


def _categories(audit) -> list[str]:
    return [ev.category for ev in audit]


def test_numeric_count_normalized_to_intent_phrase():
    out, audit = redact("Use 4 dots for trapped electrons.")
    assert "a few dots" in out
    assert "4 dots" not in out
    assert "count" in _categories(audit)


def test_english_count_word_normalized_to_stacked_layers():
    out, audit = redact("Show three layers with arrows.")
    assert "stacked layers" in out
    assert "three layers" not in out
    assert "count_word" in _categories(audit)


def test_sample_label_range_normalized_to_material_compositions():
    out, audit = redact("Compare S60-S85 panels.")
    assert "different material compositions" in out
    assert "S60-S85" not in out
    assert "sample_label" in _categories(audit)


def test_sample_labels_do_not_swallow_surrounding_spaces():
    out, audit = redact("S60 and S70 comparison")
    assert out == "different material compositions and different material compositions comparison"
    assert _categories(audit).count("sample_label") == 2

    out, audit = redact("Compare S60 to S85.")
    assert out == "Compare different material compositions to different material compositions."
    assert _categories(audit).count("sample_label") == 2


def test_sample_like_domain_tokens_are_preserved():
    out, audit = redact("Compare C60, E11, and T90 transport states.")
    assert "C60" in out
    assert "E11" in out
    assert "T90" in out
    assert "sample_label" not in _categories(audit)


def test_unitless_geometry_normalized():
    out, audit = redact("Gate width 200 by 50 pixels.")
    assert "general geometry" in out
    assert "200 by 50" not in out
    assert "geometry" in _categories(audit)


def test_thin_film_length_normalized():
    out, audit = redact("Use a 200 nm film for the dielectric.")
    assert "thin film" in out
    assert "200 nm" not in out
    assert "length" in _categories(audit)


def test_composition_ratio_normalized():
    out, audit = redact("Illustrate a 70/30 copolymer interface.")
    assert "copolymer material" in out
    assert "70/30" not in out
    assert "composition_ratio" in _categories(audit)


def test_voltage_and_time_normalization_preserve_sentence_grammar():
    out, audit = redact("Apply 5 V to the gate.")
    assert out == "Apply a representative voltage to the gate."
    assert "Apply applied" not in out
    assert "voltage" in _categories(audit)

    out, audit = redact("Pulse for 120 ms.")
    assert out == "Pulse for a representative duration."
    assert "time" in _categories(audit)


def test_korean_count_normalized_but_domain_phrase_preserved():
    out, audit = redact("트랩 전자를 4개 점으로 표시하고 두 종 dielectric를 비교하라.")
    assert "a few dots" in out
    assert "4개 점" not in out
    assert "두 종 dielectric" in out
    assert "count" in _categories(audit)


def test_dot_count_normalization_preserves_relative_density():
    out, audit = redact("Deep trap has 4 dots, shallow trap has 2 dots.")
    assert "a few dots" in out
    assert "a small cluster of dots" in out
    assert "4 dots" not in out
    assert "2 dots" not in out
    assert _categories(audit).count("count") == 2


def test_panel_count_normalization_preserves_layout_intent():
    out, audit = redact("Two panels side by side.")
    assert out == "two-panel comparison layout side by side."
    assert "count_word" in _categories(audit)

    out, audit = redact("One panel.")
    assert out == "single-panel layout."
    assert "count_word" in _categories(audit)

    out, audit = redact("Six panels in a grid.")
    assert out == "multi-panel layout in a grid."
    assert "count_word" in _categories(audit)


def test_domain_terms_preserved_and_audited_as_kept():
    text = "Align CB, VB, HOMO, LUMO, E_t, and kT in the band diagram."
    out, audit = redact(text)
    for token in ("CB", "VB", "HOMO", "LUMO", "E_t", "kT"):
        assert token in out
    assert "[REDACTED:" not in out
    assert "domain_term" in _categories(audit)


def test_data_plot_signal_warned_without_silent_redaction():
    text = "Plot n vs composition with error bars."
    out, audit = redact(text)
    assert "composition" in out
    assert "error bars" in out
    assert any("plot" in category for category in _categories(audit))
