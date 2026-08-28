"""Contract tests for the path_reroute composition operator."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "candidates"))

import path_reroute  # noqa: E402
import vector_clearance  # noqa: E402


def test_parse_refuses_everything_but_one_straight_segment() -> None:
    refusals = (
        r"\draw (0,0) .. controls (1,1) and (2,1) .. (3,0);",
        r"\draw (0,0) -- (1,1) -- (2,0);",
        r"\draw (0,0) circle (0.5);",
        r"\draw (0,0) rectangle (1,1);",
        r"\draw (0,0) to[bend left=15] (1,1);",
        r"\node at (0,0) {label};",
    )
    for line in refusals:
        assert path_reroute.parse_two_point_draw(line) is None

    parsed = path_reroute.parse_two_point_draw(r"\draw[flow] (0,1.0) -- (4,1.0);")
    assert parsed is not None
    assert parsed["start"] == (0.0, 1.0)
    assert parsed["end"] == (4.0, 1.0)


def test_reroute_prefers_the_smaller_detour_and_preserves_endpoints() -> None:
    line = r"\draw[flow] (0,1.0) -- (4,1.0);"

    detour = path_reroute.reroute_detour(
        line,
        obstacle_bbox_cm=[1.5, 0.9, 2.0, 1.2],
        clearance_cm=0.3,
    )

    assert detour is not None
    assert detour["template_id"] == "reroute_under_neighbor"
    assert detour["waypoint_y_cm"] == pytest.approx(0.55)
    assert detour["replacement"] == (r"\draw[flow] (0,1.0) -- (0,0.55) -- (4,0.55) -- (4,1.0);")


def test_reroute_refuses_when_an_endpoint_sits_over_the_obstacle() -> None:
    line = r"\draw[flow] (0,1.30) -- (1,1.30);"

    detour = path_reroute.reroute_detour(
        line,
        obstacle_bbox_cm=[0.0, 0.0, 1.0, 1.23],
        clearance_cm=0.1,
    )

    assert detour is None


def test_reroute_refuses_when_both_detours_exceed_the_cap() -> None:
    line = r"\draw[flow] (0,0) -- (6,0);"

    detour = path_reroute.reroute_detour(
        line,
        obstacle_bbox_cm=[2.0, -1.4, 4.0, 1.4],
        clearance_cm=0.3,
    )

    assert detour is None


def test_rerouted_chain_resolves_the_declared_clearance_check() -> None:
    """End to end against the detector: the violated check must pass on the
    rewritten source, measured on the full chain including the detour."""
    obstacle = r"\draw (2.0,1.05) circle (0.1);"
    line = r"\draw[flow] (0,1.0) -- (4,1.0);"
    checks = [
        {
            "id": "VC-flow",
            "relation": "min_clearance_cm",
            "min_clearance_cm": 0.3,
            "element_a": {"source_line": 1, "kind": "circle"},
            "element_b": {"source_line": 2, "kind": "line"},
        }
    ]
    before = vector_clearance.check_vector_clearance(obstacle + "\n" + line, checks)
    assert [issue["id"] for issue in before if issue.get("status") == "violated"] == ["VC-flow"]

    detour = path_reroute.reroute_detour(
        line,
        obstacle_bbox_cm=[1.9, 0.95, 2.1, 1.15],
        clearance_cm=0.3,
    )
    assert detour is not None
    after = vector_clearance.check_vector_clearance(obstacle + "\n" + detour["replacement"], checks)

    assert [issue for issue in after if issue.get("status") == "violated"] == []
