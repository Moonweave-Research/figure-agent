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
    assert len(winners) == 1
    winner = winners[0]
    assert winner["id"] == "current_style"
    assert winner["mutation_boundary"] == "no_source_mutation"
    assert winner["authorizes_mutation"] is False
    assert winner["semantic_change_allowed"] is False
    assert winner["can_improve"]
    assert winner["forbidden_semantic_changes"]
    assert winner["proof_evidence"]
    assert winner["human_only_question"]
    assert all(
        candidate["authorizes_mutation"] is False
        for candidate in payload["candidate_family_comparisons"]
    )
    assert all(
        candidate["semantic_change_allowed"] is False
        for candidate in payload["candidate_family_comparisons"]
    )


def test_real_fig3_style_benchmark_comparison_loads() -> None:
    payload = style_benchmark_comparison.load_comparison(
        "fig3_trapping_concept",
        plugin_root=PLUGIN_ROOT,
    )

    assert payload["schema"] == style_benchmark_comparison.SCHEMA
    assert payload["human_style_decision"] == "keep_current_style"
    assert payload["target_style_class"] == (
        "restrained two-panel scientific mechanism schematic"
    )
    assert payload["default_recommendation"] == (
        "keep_current_style_until_candidate_beats_benchmark"
    )
    assert {
        candidate["id"] for candidate in payload["candidate_family_comparisons"]
    } == style_benchmark_comparison.REQUIRED_CANDIDATE_FAMILIES
    assert all(
        candidate["authorizes_mutation"] is False
        for candidate in payload["candidate_family_comparisons"]
    )
    assert all(
        candidate["semantic_change_allowed"] is False
        for candidate in payload["candidate_family_comparisons"]
    )


def test_candidate_family_requires_human_only_question(tmp_path: Path) -> None:
    plugin_root, relative_path = _real_payload_copy(tmp_path)
    path = plugin_root / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    del payload["candidate_family_comparisons"][1]["human_only_question"]
    _write_comparison(path, payload)

    with pytest.raises(
        style_benchmark_comparison.StyleBenchmarkComparisonError,
        match="human_only_question_invalid",
    ):
        style_benchmark_comparison.load_comparison(
            "fig1_overview_v2_pair_001_vault",
            plugin_root=plugin_root,
            comparison_path=relative_path,
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


def test_comparison_requires_local_font_hierarchy_lint(tmp_path: Path) -> None:
    plugin_root, relative_path = _real_payload_copy(tmp_path)
    path = plugin_root / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["benchmark_measurable_checks"] = [
        check
        for check in payload["benchmark_measurable_checks"]
        if "style_lock_typography" not in check
    ]
    _write_comparison(path, payload)

    with pytest.raises(
        style_benchmark_comparison.StyleBenchmarkComparisonError,
        match="style_lock_typography_check_missing",
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


def test_editorial_redesign_cannot_be_winner_without_rendered_candidate_and_approval(
    tmp_path: Path,
) -> None:
    plugin_root, relative_path = _real_payload_copy(tmp_path)
    path = plugin_root / relative_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    editorial = payload["candidate_family_comparisons"][2]
    editorial["result"] = "winner_candidate"
    _write_comparison(path, payload)

    with pytest.raises(
        style_benchmark_comparison.StyleBenchmarkComparisonError,
        match="non_current_winner_requires_real_candidate",
    ):
        style_benchmark_comparison.load_comparison(
            "fig1_overview_v2_pair_001_vault",
            plugin_root=plugin_root,
            comparison_path=relative_path,
        )
