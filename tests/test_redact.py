"""Smoke tests for redact.redact() — covers the units/categories actually expected
in v0.1 briefings plus a few negative cases that must NOT be touched."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from redact import redact  # noqa: E402


def _categories(audit) -> list[str]:
    return [ev.category for ev in audit]


def test_composition_wt_percent_redacted():
    text = "85 wt% sulfur, 15 wt% PVDF"
    out, audit = redact(text)
    assert "[REDACTED:composition]" in out
    assert _categories(audit).count("composition") == 2
    assert "85" not in out
    assert "15" not in out


def test_voltage_redacted():
    out, audit = redact("Apply 3000 V for 30 s.")
    assert "[REDACTED:voltage]" in out
    assert "[REDACTED:time]" in out
    cats = _categories(audit)
    assert "voltage" in cats
    assert "time" in cats


def test_temperature_redacted():
    out, _ = redact("Heat to 180 °C for 2 h.")
    assert "[REDACTED:temperature]" in out
    assert "[REDACTED:time]" in out


def test_length_redacted():
    out, _ = redact("Film thickness 200 nm; sample width 5 mm.")
    assert "[REDACTED:length]" in out
    assert "200" not in out
    assert "5 mm" not in out


def test_ratio_warning_kept_but_flagged():
    text = "PVDF-TrFE 70/30 copolymer"
    out, audit = redact(text)
    assert "70/30" in out  # not removed
    assert "ratio_warning" in _categories(audit)


def test_pure_text_unchanged():
    text = "charge trapping mechanism in polymer dielectric"
    out, audit = redact(text)
    assert out == text
    assert audit == []


def test_dpi_redacted():
    out, _ = redact("Export at 600 dpi.")
    assert "[REDACTED:resolution]" in out


def test_audit_records_original():
    _, audit = redact("Charging at 3000 V over 24 h.")
    originals = {ev.original.strip().lower() for ev in audit if ev.category != "ratio_warning"}
    assert any("v" in o for o in originals)
    assert any("h" in o for o in originals)
