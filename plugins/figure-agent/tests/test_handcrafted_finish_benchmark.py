# ruff: noqa: E402, I001

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import handcrafted_finish_benchmark  # noqa: E402


REAL_BENCHMARK = (
    PLUGIN_ROOT
    / "examples"
    / "handcrafted_finish_benchmark_v1"
    / "benchmark_manifest.yaml"
)
REAL_REVIEW = REAL_BENCHMARK.parent / "review" / "host_masked_review.yaml"


def test_real_handcrafted_finish_benchmark_covers_three_figure_families() -> None:
    payload = handcrafted_finish_benchmark.load_manifest(REAL_BENCHMARK)

    assert payload["schema"] == handcrafted_finish_benchmark.MANIFEST_SCHEMA
    assert {motif["id"] for motif in payload["motifs"]} == {
        "amorphous_trap_host",
        "progressive_mim_transport",
        "cantilever_force_sequence",
    }
    assert {
        candidate["role"]
        for motif in payload["motifs"]
        for candidate in motif["candidates"]
    } == handcrafted_finish_benchmark.CANDIDATE_ROLES
    assert len(
        {
            candidate["option_id"]
            for motif in payload["motifs"]
            for candidate in motif["candidates"]
        }
    ) == 9


def test_host_review_is_advisory_and_cannot_create_reward_or_promotion() -> None:
    manifest = handcrafted_finish_benchmark.load_manifest(REAL_BENCHMARK)
    review = handcrafted_finish_benchmark.load_review(REAL_REVIEW, manifest=manifest)

    assert review["review_authority"] == "host_advisory_only"
    assert review["blinding_strength"] == "masked_but_authorship_confounded"
    assert review["creates_quality_reward"] is False
    assert review["authorizes_rule_promotion"] is False
    assert all(result["human_verdict"] == "not_recorded" for result in review["results"])
    cantilever = next(
        result
        for result in review["results"]
        if result["motif_id"] == "cantilever_force_sequence"
    )
    assert cantilever["host_verdict"] == "repair_candidate_pending_human"
    assert cantilever["host_preference"] is None
    assert cantilever["repair_candidate"] == "V9"


def test_review_rejects_false_human_or_reward_claim(tmp_path: Path) -> None:
    manifest = handcrafted_finish_benchmark.load_manifest(REAL_BENCHMARK)
    text = REAL_REVIEW.read_text(encoding="utf-8")
    review_path = tmp_path / "review.yaml"
    review_path.write_text(
        text.replace("creates_quality_reward: false", "creates_quality_reward: true"),
        encoding="utf-8",
    )

    with pytest.raises(
        handcrafted_finish_benchmark.HandcraftedFinishBenchmarkError,
        match="host_review_cannot_create_reward",
    ):
        handcrafted_finish_benchmark.load_review(review_path, manifest=manifest)


def test_review_rejects_pending_repair_outside_masked_candidate_set(
    tmp_path: Path,
) -> None:
    manifest = handcrafted_finish_benchmark.load_manifest(REAL_BENCHMARK)
    text = REAL_REVIEW.read_text(encoding="utf-8")
    review_path = tmp_path / "review.yaml"
    review_path.write_text(
        text.replace("repair_candidate: V9", "repair_candidate: Z0"),
        encoding="utf-8",
    )

    with pytest.raises(
        handcrafted_finish_benchmark.HandcraftedFinishBenchmarkError,
        match="repair_candidate_invalid",
    ):
        handcrafted_finish_benchmark.load_review(review_path, manifest=manifest)


def test_manifest_rejects_candidate_that_changes_meaning(tmp_path: Path) -> None:
    text = REAL_BENCHMARK.read_text(encoding="utf-8")
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        text.replace("meaning_preserved: true", "meaning_preserved: false", 1),
        encoding="utf-8",
    )

    with pytest.raises(
        handcrafted_finish_benchmark.HandcraftedFinishBenchmarkError,
        match="candidate_meaning_not_preserved",
    ):
        handcrafted_finish_benchmark.load_manifest(manifest_path)
