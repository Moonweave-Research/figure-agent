from __future__ import annotations

import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HANDOFF = PLUGIN_ROOT / "docs/current-sulfur-paper-figure-state.md"


def test_current_handoff_binds_fig1_candidate_and_machine_evidence() -> None:
    text = HANDOFF.read_text(encoding="utf-8")

    for required in (
        "fig1-redraw-to-final",
        "comparable-v3-repair-c5/repaired.tex",
        "source_sha256: sha256:6f0a40a221da752f0fdefe34238c74f9bfe8513e5f1e026bbac774f7d3670741",
        "promotion_state: candidate_only",
        "human_gate: pending",
        "strict compile",
        "physics grounding",
        "checked=11",
        "checked=9",
        "publication acceptance | not claimed",
    ):
        assert required in text


def test_current_handoff_preserves_experiment_specific_protocol() -> None:
    text = HANDOFF.read_text(encoding="utf-8")

    for required in (
        "gridless two-terminal high-voltage",
        "manually moved",
        "grounded conductive substrate",
        "induction-type electrostatic surface voltmeter",
        "not a Kelvin probe/KPFM schematic",
        "motion stage",
        "grid electrode",
        "protective-ground symbol",
    ):
        assert required in text


def test_legacy_cantilever_fixtures_are_explicitly_non_authoritative() -> None:
    fig5 = (PLUGIN_ROOT / "examples/fig5_actuation_mechanism/briefing.md").read_text(
        encoding="utf-8"
    )
    fig3 = (PLUGIN_ROOT / "examples/fig3_floating_clip_protocol/briefing.md").read_text(
        encoding="utf-8"
    )

    fig5_flat = re.sub(r"\s+", " ", fig5)
    fig3_flat = re.sub(r"\s+", " ", fig3)
    assert "legacy validation sandbox" in fig5_flat
    assert "current experiment" in fig5_flat
    assert "authority" in fig5_flat
    assert "legacy SI/methods validation fixture" in fig3_flat
    assert "current" in fig3_flat
    assert "docs/current-sulfur-paper-figure-state.md" in fig5
    assert "docs/current-sulfur-paper-figure-state.md" in fig3
