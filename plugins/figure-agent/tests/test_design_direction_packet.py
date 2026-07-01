from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from design_direction_packet import (  # noqa: E402
    SCHEMA,
    DesignDirectionPacketError,
    build_design_direction_packet,
)

FIXTURE = "fig1_overview_v2_pair_001_vault"


def _queue_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {"action": "status_action_required"}
    row.update(overrides)
    return row


def _style_pack(**overrides: object) -> dict[str, object]:
    pack: dict[str, object] = {
        "state": "present",
        "path": "docs/style-benchmark-packs/wave/fixture.json",
        "linked_files": {
            "benchmark_contract": "examples/fixture/benchmark_contract.yaml",
            "aesthetic_intent": "examples/fixture/aesthetic_intent.yaml",
            "source_decision_packet": "docs/decision-packets/wave/fixture.json",
        },
    }
    pack.update(overrides)
    return pack


def _comparison(**overrides: object) -> dict[str, object]:
    comparison: dict[str, object] = {
        "state": "present",
        "path": "docs/style-benchmark-comparisons/wave/fixture.json",
        "default_recommendation": "keep_current_style_until_candidate_beats_benchmark",
    }
    comparison.update(overrides)
    return comparison


def test_ready_packet_summarizes_recommendation_and_human_choice_boundary() -> None:
    packet = build_design_direction_packet(
        FIXTURE,
        queue_row=_queue_row(action="run_review"),
        style_pack=_style_pack(),
        comparison=_comparison(),
        svg_polish_state={"state": "ready_for_svg_polish"},
    )

    assert packet == {
        "schema": SCHEMA,
        "fixture": FIXTURE,
        "state": "ready_for_human_choice",
        "default_recommendation": "keep_current_style_until_candidate_beats_benchmark",
        "alternatives": [
            "current_style",
            "bounded_tikz_refinement",
            "editorial_redesign",
            "svg_polish_handoff",
        ],
        "mutation_boundary": "no_source_mutation",
        "human_question": (
            "I recommend keeping the current style unless a candidate beats the "
            "benchmark. Which direction should I prepare next?"
        ),
        "evidence_refs": [
            "style_benchmark_pack:docs/style-benchmark-packs/pack.json",
            "benchmark_contract:docs/benchmarks/contract.yaml",
            "aesthetic_intent:docs/aesthetic-intents/intent.yaml",
            "style_benchmark_comparison:docs/style-benchmark-comparisons/comparison.json",
        ],
        "next_agent_action": "prepare_bounded_candidate_or_stop_for_human_choice",
        "source_queue_action": "run_review",
        "svg_polish_state": "ready_for_svg_polish",
        "evidence_refs": [
            "style_benchmark_pack:docs/style-benchmark-packs/wave/fixture.json",
            "style_benchmark_comparison:docs/style-benchmark-comparisons/wave/fixture.json",
            "benchmark_contract:examples/fixture/benchmark_contract.yaml",
            "aesthetic_intent:examples/fixture/aesthetic_intent.yaml",
        ],
    }


@pytest.mark.parametrize("style_pack", [None, {"state": "missing"}])
def test_packet_blocks_when_style_pack_is_missing(style_pack: dict[str, object] | None) -> None:
    packet = build_design_direction_packet(
        FIXTURE,
        queue_row=_queue_row(),
        style_pack=style_pack,
        comparison=_comparison(),
    )

    assert packet == {
        "schema": SCHEMA,
        "fixture": FIXTURE,
        "state": "blocked_missing_style_pack",
        "mutation_boundary": "no_source_mutation",
        "alternatives": [],
        "blocking_reasons": ["style_benchmark_pack_missing"],
        "evidence_refs": [
            "style_benchmark_comparison:docs/style-benchmark-comparisons/comparison.json",
        ],
        "next_agent_action": "create_style_benchmark_pack",
    }
    assert "human_question" not in packet


@pytest.mark.parametrize("comparison", [None, {"state": "missing"}])
def test_packet_blocks_when_comparison_is_missing(comparison: dict[str, object] | None) -> None:
    packet = build_design_direction_packet(
        FIXTURE,
        queue_row=_queue_row(),
        style_pack=_style_pack(),
        comparison=comparison,
    )

    assert packet == {
        "schema": SCHEMA,
        "fixture": FIXTURE,
        "state": "blocked_missing_comparison",
        "mutation_boundary": "no_source_mutation",
        "alternatives": [],
        "blocking_reasons": ["style_benchmark_comparison_missing"],
        "evidence_refs": [
            "style_benchmark_pack:docs/style-benchmark-packs/pack.json",
            "benchmark_contract:docs/benchmarks/contract.yaml",
            "aesthetic_intent:docs/aesthetic-intents/intent.yaml",
        ],
        "next_agent_action": "create_style_benchmark_comparison",
    }
    assert "human_question" not in packet


def test_packet_validates_fixture_name() -> None:
    with pytest.raises(DesignDirectionPacketError, match="fixture_invalid"):
        build_design_direction_packet(
            "../escape",
            queue_row=_queue_row(),
            style_pack=_style_pack(),
            comparison=_comparison(),
        )
