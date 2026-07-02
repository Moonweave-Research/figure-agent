"""Regression checks for the Wave 5 reference-briefing handoff doc."""

from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HANDOFF = PLUGIN_ROOT / "docs/milestones/2026-06-30-wave5-reference-briefing-handoff.md"


def test_wave5_reference_briefing_handoff_names_all_target_fixtures() -> None:
    doc = HANDOFF.read_text(encoding="utf-8")

    for fixture in (
        "fig3_floating_clip_protocol",
        "fig3_trapping_concept",
        "fig4_trap_energy_diagram",
    ):
        assert fixture in doc
        assert f"/fig_compile {fixture}" in doc
        assert f"/fig_critique {fixture}" in doc


def test_wave5_reference_briefing_handoff_preserves_boundaries() -> None:
    doc = HANDOFF.read_text(encoding="utf-8")

    for required in (
        "did not write `critique.md`",
        "did not mutate fixture source",
        "accepted state",
        "golden exports",
        "publication state",
        "did not invent reference images",
        "did not run compile/export/acceptance/golden/publication commands",
    ):
        assert required in doc


def test_wave5_reference_briefing_handoff_records_probe_and_coordination_evidence() -> None:
    doc = HANDOFF.read_text(encoding="utf-8")

    for required in (
        "fig-agent helper critique_brief.py examples/<fixture>",
        "fig-agent context-pack <fixture> --json",
        "fig-agent status <fixture> --json",
        "figure-agent.authoring-context-pack.v1",
        "read_only=true",
        "Coordination mode: coordinated.",
        "Subagent spawn skipped. Reason:",
        "Verification performed",
    ):
        assert required in doc
