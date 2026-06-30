# ruff: noqa: E402, I001

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import style_benchmark_comparison  # noqa: E402


REAL_COMPARISON = (
    PLUGIN_ROOT
    / "docs"
    / "style-benchmark-comparisons"
    / "2026-07-01-wave-f"
    / "fig1_overview_v2_pair_001_vault.json"
)


def _write_comparison(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _copy_plugin_file(plugin_root: Path, relative: str) -> None:
    source = PLUGIN_ROOT / relative
    target = plugin_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def _real_payload_copy(tmp_path: Path) -> tuple[Path, Path]:
    plugin_root = tmp_path / "plugin"
    for relative in (
        "docs/style-benchmark-packs/2026-06-30-wave-c/fig1_overview_v2_pair_001_vault.json",
        "docs/decision-packets/2026-06-30-wave-c/fig1_overview_v2_pair_001_vault.json",
        "docs/decision-records/2026-06-30-wave-c/fig1_overview_v2_pair_001_vault.json",
        (
            "docs/decision-records/2026-07-01-wave-e/"
            "fig1_overview_v2_pair_001_vault_keep_current_style.json"
        ),
        "examples/fig1_overview_v2_pair_001_vault/benchmark_contract.yaml",
        "examples/fig1_overview_v2_pair_001_vault/aesthetic_intent.yaml",
    ):
        _copy_plugin_file(plugin_root, relative)
    payload = json.loads(REAL_COMPARISON.read_text(encoding="utf-8"))
    path = (
        plugin_root
        / "docs"
        / "style-benchmark-comparisons"
        / "2026-07-01-wave-f"
        / "fig1_overview_v2_pair_001_vault.json"
    )
    _write_comparison(path, payload)
    return plugin_root, Path(
        "docs/style-benchmark-comparisons/2026-07-01-wave-f/"
        "fig1_overview_v2_pair_001_vault.json"
    )


def test_real_wave_f_style_benchmark_comparison_loads() -> None:
    payload = style_benchmark_comparison.load_comparison(
        "fig1_overview_v2_pair_001_vault",
        plugin_root=PLUGIN_ROOT,
    )

    assert payload["schema"] == style_benchmark_comparison.SCHEMA
    assert payload["human_style_decision"] == "keep_current_style"
    assert payload["target_style_class"] == (
        "restrained editorial multipanel scientific schematic"
    )
    assert {
        candidate["id"] for candidate in payload["candidate_family_comparisons"]
    } == style_benchmark_comparison.REQUIRED_CANDIDATE_FAMILIES
    winners = [
        candidate
        for candidate in payload["candidate_family_comparisons"]
        if candidate["result"] == "winner_candidate"
    ]
    assert winners == [
        {
            "id": "current_style",
            "result": "winner_candidate",
            "mutation_boundary": "no_source_mutation",
            "authorizes_mutation": False,
            "semantic_change_allowed": False,
            "comparison_basis": [
                "human decision selected keep_current_style as policy state only",
                (
                    "current style remains the benchmark until a candidate beats it "
                    "on measurable checks and human art direction"
                ),
            ],
            "failure_modes": [
                "can still be displaced by a later candidate with stronger evidence",
                (
                    "does not approve release, accepted-state mutation, export "
                    "mutation, or golden mutation"
                ),
            ],
            "prerequisite_evidence": [
                "Wave E decision record keeps current style with no_source_mutation boundary",
                "Wave C benchmark pack defines target style class and rejection rules",
            ],
        }
    ]
    assert all(
        candidate["authorizes_mutation"] is False
        for candidate in payload["candidate_family_comparisons"]
    )
    assert all(
        candidate["semantic_change_allowed"] is False
        for candidate in payload["candidate_family_comparisons"]
    )


def test_candidate_family_cannot_authorize_mutation(tmp_path: Path) -> None:
    plugin_root, relative_path = _real_payload_copy(tmp_path)
    path = plugin_root / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["candidate_family_comparisons"][1]["authorizes_mutation"] = True
    _write_comparison(path, payload)

    with pytest.raises(
        style_benchmark_comparison.StyleBenchmarkComparisonError,
        match="candidate_authorizes_mutation",
    ):
            style_benchmark_comparison.load_comparison(
                "fig1_overview_v2_pair_001_vault",
                plugin_root=plugin_root,
                comparison_path=relative_path,
            )


def test_prettier_candidate_cannot_allow_semantic_change(tmp_path: Path) -> None:
    plugin_root, relative_path = _real_payload_copy(tmp_path)
    path = plugin_root / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    editorial = payload["candidate_family_comparisons"][2]
    editorial["result"] = "eligible"
    editorial["semantic_change_allowed"] = True
    _write_comparison(path, payload)

    with pytest.raises(
        style_benchmark_comparison.StyleBenchmarkComparisonError,
        match="candidate_semantic_change_allowed",
    ):
            style_benchmark_comparison.load_comparison(
                "fig1_overview_v2_pair_001_vault",
                plugin_root=plugin_root,
                comparison_path=relative_path,
            )


def test_svg_polish_candidate_requires_ready_for_svg_polish_evidence(tmp_path: Path) -> None:
    plugin_root, relative_path = _real_payload_copy(tmp_path)
    path = plugin_root / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    svg_candidate = payload["candidate_family_comparisons"][3]
    svg_candidate["prerequisite_evidence"] = ["separate SVG approval required"]
    _write_comparison(path, payload)

    with pytest.raises(
        style_benchmark_comparison.StyleBenchmarkComparisonError,
        match="svg_polish_prerequisite_missing",
    ):
            style_benchmark_comparison.load_comparison(
                "fig1_overview_v2_pair_001_vault",
                plugin_root=plugin_root,
                comparison_path=relative_path,
            )
