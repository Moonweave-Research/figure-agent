from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from next_action_summary import (  # noqa: E402
    closeout_next_action_summary,
    driver_next_action_summary,
    loop_next_action_summary,
    status_next_action_summary,
)


def _assert_summary_shape(summary: dict[str, Any]) -> None:
    assert summary["schema"] == "figure-agent.next-action-summary.v1"
    assert isinstance(summary["action"], str)
    assert summary["action"]
    assert isinstance(summary["reason"], str)
    assert summary["reason"]
    assert isinstance(summary["blocking_source"], str)
    assert summary["blocking_source"]
    assert "safe_command" in summary
    assert isinstance(summary["requires_human"], bool)
    assert isinstance(summary["allowed_scope"], list)
    assert isinstance(summary["forbidden_scope"], list)
    assert isinstance(summary["evidence_refs"], list)
    boundary = summary["decision_boundary"]
    assert boundary["schema"] == "figure-agent.decision-boundary.v1"
    assert isinstance(boundary["kind"], str)
    assert isinstance(boundary["authority"], str)
    assert isinstance(boundary["blocks_progress"], bool)
    assert isinstance(boundary["blocks_release"], bool)
    assert isinstance(boundary["explanation"], str)
    assert boundary["explanation"]


def test_status_summary_maps_render_missing_to_compile_action() -> None:
    summary = status_next_action_summary(
        {
            "name": "demo",
            "next": "run /fig_compile demo to compile the TikZ source.",
            "render_state": "MISSING",
            "critique_state": "NOT_REQUIRED",
            "export_state": "MISSING",
            "status_explanation": {
                "first_blocker": {
                    "code": "render_missing",
                    "message": "build PDF is missing.",
                    "next_command": "/fig_compile demo",
                    "manual": False,
                }
            },
        }
    )

    _assert_summary_shape(summary)
    assert summary["action"] == "run_compile"
    assert summary["safe_command"] == "/fig_compile demo"
    assert summary["blocking_source"] == "render_missing"
    assert summary["requires_human"] is False
    assert summary["evidence_refs"] == ["status.first_blocker:render_missing"]
    assert summary["decision_boundary"]["kind"] == "deterministic_plugin_gate"
    assert summary["decision_boundary"]["authority"] == "plugin"
    assert summary["decision_boundary"]["blocks_progress"] is True


def test_driver_summary_preserves_human_gate_stop() -> None:
    summary = driver_next_action_summary(
        {
            "fixture": "demo",
            "action": "human_gate_stop",
            "safe_command": None,
            "stop_boundary": "human_gate_required",
            "reason": "latest /fig_loop checkpoint requires human review.",
            "loop_checkpoint": {
                "final_stop_reason": "human_gate_required",
                "recommended_next_action": "human review required for C001",
            },
        }
    )

    _assert_summary_shape(summary)
    assert summary["action"] == "human_gate_stop"
    assert summary["safe_command"] is None
    assert summary["blocking_source"] == "human_gate_required"
    assert summary["requires_human"] is True
    assert "loop.final_stop_reason:human_gate_required" in summary["evidence_refs"]
    assert summary["decision_boundary"]["kind"] == "human_decision"
    assert summary["decision_boundary"]["authority"] == "human"
    assert summary["decision_boundary"]["blocks_release"] is True


def test_status_summary_marks_reference_missing_as_human_decision_not_host_vision() -> None:
    summary = status_next_action_summary(
        {
            "name": "demo",
            "render_state": "FRESH",
            "critique_state": "REFERENCE_MISSING",
            "status_explanation": {
                "first_blocker": {
                    "code": "critique_reference_missing",
                    "message": "declared critique reference input is missing.",
                    "manual": True,
                },
            },
        }
    )

    _assert_summary_shape(summary)
    assert summary["action"] == "run_critique"
    assert summary["requires_human"] is True
    assert summary["decision_boundary"]["kind"] == "human_decision"
    assert summary["decision_boundary"]["authority"] == "human"


def test_driver_summary_marks_reference_missing_as_workflow_blocker_not_host_vision() -> None:
    summary = driver_next_action_summary(
        {
            "fixture": "demo",
            "action": "run_critique",
            "safe_command": None,
            "stop_boundary": "reference_missing",
            "reason": "declared reference input is missing.",
        }
    )

    _assert_summary_shape(summary)
    assert summary["decision_boundary"]["kind"] == "deterministic_plugin_gate"
    assert summary["decision_boundary"]["authority"] == "plugin"


def test_driver_summary_marks_ready_improvement_as_advisory_only() -> None:
    summary = driver_next_action_summary(
        {
            "fixture": "demo",
            "action": "complete",
            "safe_command": None,
            "stop_boundary": None,
            "reason": "review mode is complete.",
            "ready_improvement_summary": {
                "state": "ready_but_improvable",
                "safe_to_ship": True,
                "candidate_count": 1,
                "marginal_return_summary": {"state": "stop_recommended"},
            },
        }
    )

    _assert_summary_shape(summary)
    assert summary["decision_boundary"] == {
        "schema": "figure-agent.decision-boundary.v1",
        "kind": "advisory_only",
        "authority": "plugin",
        "blocks_progress": False,
        "blocks_release": False,
        "explanation": (
            "The required workflow is complete; optional improvement candidates "
            "are advisory and do not block release."
        ),
    }


def test_loop_summary_maps_patch_target_to_handoff_stop() -> None:
    summary = loop_next_action_summary(
        {
            "stop_reason": "patch_target_recommended",
            "recommended_next_action": "patch C001: Panel A label offset",
            "active_patch_target": {
                "finding_id": "C001",
                "patch_target": "Panel A label offset",
            },
            "human_gate_status": "not_requested",
        },
        {"name": "demo", "next": "inspect figure state"},
        {
            "target_type": "finding",
            "target_id": "C001",
            "allowed_edit_scope": ["examples/demo/demo.tex"],
            "forbidden_edit_scope": ["examples/demo/exports/"],
        },
    )

    _assert_summary_shape(summary)
    assert summary["action"] == "patch_handoff_stop"
    assert summary["safe_command"] is None
    assert summary["blocking_source"] == "patch_target_recommended"
    assert summary["requires_human"] is False
    assert summary["allowed_scope"] == ["examples/demo/demo.tex"]
    assert "loop.stop_reason:patch_target_recommended" in summary["evidence_refs"]


def test_closeout_summary_maps_first_needed_step_to_action() -> None:
    summary = closeout_next_action_summary(
        {
            "fixture": "demo",
            "closeout_complete": False,
            "next_action": "/fig_compile demo",
            "blocking_step_ids": ["compile", "critique"],
            "steps": [
                {
                    "id": "compile",
                    "state": "needs_action",
                    "reason": "render_state is MISSING",
                    "command": "/fig_compile demo",
                },
                {
                    "id": "critique",
                    "state": "blocked",
                    "reason": "fresh render required before critique",
                    "command": None,
                },
            ],
        }
    )

    _assert_summary_shape(summary)
    assert summary["action"] == "run_compile"
    assert summary["safe_command"] == "/fig_compile demo"
    assert summary["blocking_source"] == "closeout:compile"
    assert summary["requires_human"] is False
    assert summary["evidence_refs"] == [
        "closeout.blocking_steps:compile,critique",
        "closeout.next_step:compile",
    ]
