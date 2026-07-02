from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from editorial_redesign_packet import (  # noqa: E402
    SCHEMA,
    EditorialRedesignPacketError,
    build_editorial_redesign_packet,
)


def _style_pack() -> dict[str, object]:
    return {
        "state": "present",
        "target_style_class": "restrained editorial multipanel scientific schematic",
    }


def _comparison() -> dict[str, object]:
    return {
        "state": "present",
        "forbidden_semantic_changes": ["panel roles", "required labels", "semantic colors"],
    }


def test_editorial_redesign_packet_is_handoff_only() -> None:
    packet = build_editorial_redesign_packet(
        "fig1_overview_v2_pair_001_vault",
        style_pack=_style_pack(),
        comparison=_comparison(),
    )

    assert packet == {
        "schema": SCHEMA,
        "fixture": "fig1_overview_v2_pair_001_vault",
        "mutation_boundary": "no_source_mutation",
        "state": "ready_for_human_handoff_choice",
        "candidate_request": {
            "target_style_class": "restrained editorial multipanel scientific schematic",
            "must_preserve": ["panel roles", "required labels", "semantic colors"],
            "must_not_do": [
                "semantic rewrite",
                "SVG polish as repair",
                "accepted/golden mutation",
            ],
        },
        "human_question": (
            "I can prepare editorial redesign candidates under these guardrails. "
            "Should I proceed with candidate preparation?"
        ),
        "next_agent_action": "prepare_editorial_redesign_candidates_only_after_human_approval",
    }


@pytest.mark.parametrize("fixture", ["../escape", "nested/path"])
def test_editorial_redesign_packet_rejects_unsafe_fixture(fixture: str) -> None:
    with pytest.raises(EditorialRedesignPacketError, match="fixture_invalid"):
        build_editorial_redesign_packet(
            fixture,
            style_pack=_style_pack(),
            comparison=_comparison(),
        )


def test_editorial_redesign_packet_requires_style_pack() -> None:
    with pytest.raises(EditorialRedesignPacketError, match="style_benchmark_pack_missing"):
        build_editorial_redesign_packet(
            "fig1_overview_v2_pair_001_vault",
            style_pack=None,
            comparison=_comparison(),
        )


def test_editorial_redesign_packet_requires_comparison() -> None:
    with pytest.raises(EditorialRedesignPacketError, match="style_benchmark_comparison_missing"):
        build_editorial_redesign_packet(
            "fig1_overview_v2_pair_001_vault",
            style_pack=_style_pack(),
            comparison=None,
        )
