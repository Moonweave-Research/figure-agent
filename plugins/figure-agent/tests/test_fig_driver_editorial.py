from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_driver_editorial import (  # noqa: E402
    ROUTE_HUMAN_GATE,
    ROUTE_READY_FOR_SVG_POLISH,
    ROUTE_RUN_LOOP,
    ROUTE_SEMANTIC_BACKPORT,
    editorial_polish_route,
    editorial_review_requires_human_gate,
)


def test_editorial_review_requires_human_gate_for_blocking_summary() -> None:
    assert editorial_review_requires_human_gate(
        {
            "worst_verdict": "pass",
            "verdict_counts": {"pass": 9, "weak": 0, "fail": 0, "needs_human": 0},
            "blocking_high_impact_count": 1,
            "polish_recommended_path": "ready_for_svg_polish",
        }
    )


def test_editorial_review_ignores_nonblocking_weak_summary() -> None:
    assert not editorial_review_requires_human_gate(
        {
            "worst_verdict": "weak",
            "verdict_counts": {"pass": 9, "weak": 1, "fail": 0, "needs_human": 0},
            "blocking_high_impact_count": 0,
            "polish_recommended_path": "ready_for_svg_polish",
        }
    )


def test_editorial_polish_route_maps_all_recommended_paths() -> None:
    assert (
        editorial_polish_route({"polish_recommended_path": "semantic_backport_required"})
        == ROUTE_SEMANTIC_BACKPORT
    )
    assert (
        editorial_polish_route({"polish_recommended_path": "needs_human_art_direction"})
        == ROUTE_HUMAN_GATE
    )
    assert editorial_polish_route({"polish_recommended_path": "continue_tikz"}) == ROUTE_RUN_LOOP
    assert (
        editorial_polish_route({"polish_recommended_path": "ready_for_svg_polish"})
        == ROUTE_READY_FOR_SVG_POLISH
    )


def test_editorial_polish_route_human_gate_wins_over_ready_path() -> None:
    assert (
        editorial_polish_route(
            {
                "worst_verdict": "needs_human",
                "verdict_counts": {"pass": 9, "weak": 0, "fail": 0, "needs_human": 1},
                "blocking_high_impact_count": 0,
                "polish_recommended_path": "ready_for_svg_polish",
            }
        )
        == ROUTE_HUMAN_GATE
    )


def test_editorial_polish_route_ignores_missing_or_malformed_summary() -> None:
    assert editorial_polish_route(None) is None
    assert editorial_polish_route({"polish_recommended_path": "unknown"}) is None
