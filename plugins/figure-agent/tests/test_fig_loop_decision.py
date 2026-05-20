from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_decision import (  # noqa: E402
    critique_refresh_action,
    decisions_with_value,
    first_decision,
    loop_decision,
    reference_input_missing,
)


def test_reference_input_missing_detects_fixture_and_panel_reference_notes() -> None:
    for note in (
        "critique_reference_missing",
        "reference_image_missing",
        "panel_reference_image_missing",
    ):
        assert reference_input_missing({"notes": [note]}) is True

    assert reference_input_missing({"notes": ["unrelated"]}) is False
    assert reference_input_missing({}) is False


def test_critique_refresh_action_uses_fixture_name_and_lowercase_state(tmp_path: Path) -> None:
    example_dir = tmp_path / "examples" / "loop_demo"

    assert critique_refresh_action(example_dir, "STALE") == (
        "run /fig_critique loop_demo because critique is stale."
    )


def test_first_decision_requires_fresh_adjudication() -> None:
    adjudication = {
        "state": "fresh",
        "decisions": [
            {"finding_id": "C001", "decision": "dismiss"},
            {"finding_id": "C002", "decision": "needs_human"},
        ],
    }

    assert first_decision(adjudication, "needs_human") == {
        "finding_id": "C002",
        "decision": "needs_human",
    }
    assert (
        first_decision({"state": "stale", "decisions": adjudication["decisions"]}, "dismiss")
        is None
    )


def test_decisions_with_value_requires_fresh_adjudication() -> None:
    adjudication = {
        "state": "fresh",
        "decisions": [
            {"finding_id": "C001", "decision": "apply"},
            {"finding_id": "C002", "decision": "defer"},
            {"finding_id": "C003", "decision": "apply"},
        ],
    }

    assert decisions_with_value(adjudication, "apply") == [
        {"finding_id": "C001", "decision": "apply"},
        {"finding_id": "C003", "decision": "apply"},
    ]
    assert (
        decisions_with_value(
            {"state": "missing", "decisions": adjudication["decisions"]},
            "apply",
        )
        == []
    )


def test_loop_decision_reference_missing_precedes_stale_critique(tmp_path: Path) -> None:
    decision = loop_decision(
        {
            "notes": ["reference_image_missing"],
            "critique_state": "STALE",
            "workflow_ready": False,
            "next": "run /fig_compile loop_demo",
        },
        {"state": "fresh", "decisions": [{"finding_id": "C001", "decision": "needs_human"}]},
        tmp_path / "loop_demo",
    )

    assert decision == {
        "stop_reason": "reference_input_missing",
        "recommended_next_action": "fix declared reference inputs before continuing",
        "active_patch_target": None,
        "human_gate_status": "not_requested",
    }


def test_loop_decision_stale_critique_precedes_human_gate(tmp_path: Path) -> None:
    decision = loop_decision(
        {"notes": [], "critique_state": "STALE", "workflow_ready": True},
        {"state": "fresh", "decisions": [{"finding_id": "C001", "decision": "needs_human"}]},
        tmp_path / "loop_demo",
    )

    assert decision["stop_reason"] == "status_action_required"
    assert decision["recommended_next_action"] == (
        "run /fig_critique loop_demo because critique is stale."
    )
    assert decision["human_gate_status"] == "not_requested"


def test_loop_decision_human_gate_precedes_apply_decision(tmp_path: Path) -> None:
    decision = loop_decision(
        {"notes": [], "critique_state": "FRESH", "workflow_ready": True},
        {
            "state": "fresh",
            "decisions": [
                {
                    "finding_id": "C001",
                    "decision": "apply",
                    "patch_target": "panel A",
                    "reason": "fix",
                },
                {"finding_id": "C002", "decision": "needs_human"},
            ],
        },
        tmp_path / "loop_demo",
    )

    assert decision == {
        "stop_reason": "human_gate_required",
        "recommended_next_action": "human review required for C002",
        "active_patch_target": None,
        "human_gate_status": "required",
    }


def test_loop_decision_missing_adjudication_precedes_active_subregion(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    example_dir.mkdir()
    (example_dir / "subregion_iteration_log.md").write_text(
        "## Active Target Set\n\n"
        "| State | Sub-region ID | Evidence | Notes |\n"
        "|---|---|---|---|\n"
        "| active target | D-2 | current loop | label spacing |\n",
        encoding="utf-8",
    )

    decision = loop_decision(
        {"notes": [], "critique_state": "FRESH", "workflow_ready": True},
        {"state": "missing", "decisions": []},
        example_dir,
    )

    assert decision["stop_reason"] == "missing_adjudication"
    assert decision["active_patch_target"] is None


def test_loop_decision_workflow_and_final_ready_status_branches(tmp_path: Path) -> None:
    example_dir = tmp_path / "loop_demo"
    adjudication = {"state": "fresh", "decisions": []}

    not_ready = loop_decision(
        {
            "notes": [],
            "critique_state": "NOT_REQUIRED",
            "workflow_ready": False,
            "next": "run /fig_compile loop_demo",
        },
        adjudication,
        example_dir,
    )
    final_not_ready = loop_decision(
        {
            "notes": [],
            "critique_state": "NOT_REQUIRED",
            "workflow_ready": True,
            "final_ready": False,
            "next": "refresh final artifact",
        },
        adjudication,
        example_dir,
    )

    assert not_ready["stop_reason"] == "status_action_required"
    assert not_ready["recommended_next_action"] == "run /fig_compile loop_demo"
    assert final_not_ready["stop_reason"] == "status_action_required"
    assert final_not_ready["recommended_next_action"] == "refresh final artifact"


def test_loop_decision_verify_only_complete_fallthrough(tmp_path: Path) -> None:
    decision = loop_decision(
        {
            "notes": [],
            "critique_state": "NOT_REQUIRED",
            "workflow_ready": True,
            "final_ready": True,
            "next": "inspect figure state",
        },
        {"state": "missing", "decisions": []},
        tmp_path / "loop_demo",
    )

    assert decision == {
        "stop_reason": "verify_only_complete",
        "recommended_next_action": "inspect figure state",
        "active_patch_target": None,
        "human_gate_status": "not_requested",
    }
