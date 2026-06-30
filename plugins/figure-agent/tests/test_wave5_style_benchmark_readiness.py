"""Regression checks for the Wave 5 style benchmark readiness packet."""

from __future__ import annotations

from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PACKET = PLUGIN_ROOT / "docs/milestones/2026-06-30-wave5-style-benchmark-readiness.md"


def test_wave5_style_benchmark_names_fixture_artifact_and_style_class() -> None:
    doc = PACKET.read_text(encoding="utf-8")

    for required in (
        "fig1_overview_v2_pair_001_vault",
        "fig1_overview_v2_pair_001_vault.tex",
        "restrained editorial multipanel scientific schematic",
        "benchmark_contract.yaml",
        "aesthetic_intent.yaml",
        "QUALITY_AUDIT.md",
    ):
        assert required in doc


def test_wave5_style_benchmark_preserves_non_mutation_boundaries() -> None:
    doc = PACKET.read_text(encoding="utf-8")

    for required in (
        "Did not edit `examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex`",
        "Did not edit any fixture `.tex`",
        "Did not run compile/export/acceptance/golden/publication commands",
        "This fixture is a benchmark for comparison criteria, not an instruction to rewrite its source",
        "without source mutation",
    ):
        assert required in doc


def test_wave5_style_benchmark_records_forbidden_semantics_and_comparison_criteria() -> None:
    doc = PACKET.read_text(encoding="utf-8")

    for required in (
        "Forbidden semantic changes",
        "Change A/B/C/D/E/F panel roles",
        "Swap shallow/deep trap color semantics",
        "Style Lock lint output",
        "Text-boundary and visual-clash detector deltas",
        "Human review only for non-measurable art direction",
    ):
        assert required in doc
