from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "quality"))

import structural_collision_gate as gate  # noqa: E402


def test_text_text_zero_does_not_pass_when_text_crosses_a_path() -> None:
    summary = gate.summarize_reports(
        collisions={
            "schema": "figure-agent.text-collisions.v1",
            "collisions": [],
            "total": 0,
        },
        visual_clash={
            "candidates": [
                {"id": "VC001", "kind": "text_on_path", "text": "increases"}
            ],
            "total": 1,
        },
        undeclared_geometry={"candidates": [], "downranked": []},
        declared_coverage={"label_path": True, "panel_boundary": True},
    )

    assert summary["state"] == "failed"
    assert summary["structural_pass"] is False
    assert summary["blocking_counts"] == {
        "text_text": 0,
        "text_on_path_or_fill": 1,
        "semantic_path_crossing": 0,
    }


def test_missing_declared_geometry_coverage_requires_review() -> None:
    summary = gate.summarize_reports(
        collisions={"collisions": [], "total": 0},
        visual_clash={
            "candidates": [{"id": "VC001", "kind": "near_miss", "text": "S60"}],
            "total": 1,
        },
        undeclared_geometry={"candidates": [], "downranked": []},
        declared_coverage={"label_path": False, "panel_boundary": False},
    )

    assert summary["state"] == "review_required"
    assert summary["structural_pass"] is False
    assert summary["review_counts"] == {"visual_near_miss": 1}
    assert summary["coverage_gaps"] == ["label_path", "panel_boundary"]


def test_semantic_arrow_crossing_is_blocking_even_when_visual_detector_is_clean() -> None:
    summary = gate.summarize_reports(
        collisions={"collisions": [], "total": 0},
        visual_clash={"candidates": [], "total": 0},
        undeclared_geometry={
            "candidates": [
                {
                    "id": "UG001",
                    "kind": "label_crosses_semantic_path",
                    "nearest_text": "increases",
                }
            ],
            "downranked": [],
        },
        declared_coverage={"label_path": True, "panel_boundary": True},
    )

    assert summary["state"] == "failed"
    assert summary["blocking_counts"]["semantic_path_crossing"] == 1
