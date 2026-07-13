from __future__ import annotations

import json
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


def test_same_blocker_count_is_rejected_when_collision_moves_to_new_objects() -> None:
    regression = gate.compare_reports(
        before_collisions={
            "collisions": [
                {"texts": ["capture", "release"], "iou": 0.12},
            ]
        },
        before_visual_clash={"candidates": []},
        before_undeclared_geometry={"candidates": []},
        after_collisions={
            "collisions": [
                {"texts": ["broad", "magnitude"], "iou": 0.08},
            ]
        },
        after_visual_clash={"candidates": []},
        after_undeclared_geometry={"candidates": []},
    )

    assert regression["state"] == "regressed"
    assert regression["new_blockers"] == [
        {
            "count_delta": 1,
            "signature": "text_text:broad|magnitude",
        }
    ]
    assert regression["resolved_blockers"] == [
        {
            "count_delta": 1,
            "signature": "text_text:capture|release",
        }
    ]
    assert regression["publication_acceptance"] == "not_claimed"


def test_path_blocker_is_rejected_when_repair_moves_it_to_another_label() -> None:
    regression = gate.compare_reports(
        before_collisions={"collisions": []},
        before_visual_clash={
            "candidates": [
                {"kind": "text_on_path", "text": "capture"},
            ]
        },
        before_undeclared_geometry={"candidates": []},
        after_collisions={"collisions": []},
        after_visual_clash={
            "candidates": [
                {"kind": "text_on_path", "text": "retained"},
            ]
        },
        after_undeclared_geometry={"candidates": []},
    )

    assert regression["state"] == "regressed"
    assert regression["new_blockers"] == [
        {
            "count_delta": 1,
            "signature": "visual:text_on_path:retained",
        }
    ]


def test_semantic_path_crossing_regression_preserves_label_identity() -> None:
    regression = gate.compare_reports(
        before_collisions={"collisions": []},
        before_visual_clash={"candidates": []},
        before_undeclared_geometry={"candidates": []},
        after_collisions={"collisions": []},
        after_visual_clash={"candidates": []},
        after_undeclared_geometry={
            "candidates": [
                {
                    "kind": "label_crosses_semantic_path",
                    "nearest_text": "retained",
                }
            ]
        },
    )

    assert regression["new_blockers"] == [
        {
            "count_delta": 1,
            "signature": "geometry:label_crosses_semantic_path:retained",
        }
    ]


def test_cli_marks_candidate_regressed_against_bound_baseline(
    tmp_path: Path, monkeypatch
) -> None:
    reports = {
        "before-collisions.json": {
            "collisions": [{"texts": ["capture", "release"]}]
        },
        "after-collisions.json": {
            "collisions": [{"texts": ["broad", "magnitude"]}]
        },
        "before-visual.json": {"candidates": []},
        "after-visual.json": {"candidates": []},
        "before-geometry.json": {"candidates": []},
        "after-geometry.json": {"candidates": []},
    }
    for name, payload in reports.items():
        (tmp_path / name).write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "gate.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "structural_collision_gate.py",
            "--collisions",
            str(tmp_path / "after-collisions.json"),
            "--visual-clash",
            str(tmp_path / "after-visual.json"),
            "--undeclared-geometry",
            str(tmp_path / "after-geometry.json"),
            "--baseline-collisions",
            str(tmp_path / "before-collisions.json"),
            "--baseline-visual-clash",
            str(tmp_path / "before-visual.json"),
            "--baseline-undeclared-geometry",
            str(tmp_path / "before-geometry.json"),
            "--json-output",
            str(output),
        ],
    )

    assert gate.main() == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["state"] == "regressed"
    assert payload["regression"]["new_blockers"][0]["signature"] == (
        "text_text:broad|magnitude"
    )
