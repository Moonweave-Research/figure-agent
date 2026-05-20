from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_escalation import escalation_summary  # noqa: E402


def test_escalation_summary_marks_human_gate_as_domain_review() -> None:
    assert escalation_summary({"stop_reason": "human_gate_required"}) == {
        "escalation_level": "human_review_required",
        "requires_user_input": True,
        "requires_domain_review": True,
    }


def test_escalation_summary_marks_patch_targets_as_patch_allowed() -> None:
    assert escalation_summary({"stop_reason": "patch_target_recommended"}) == {
        "escalation_level": "patch_allowed",
        "requires_user_input": False,
        "requires_domain_review": False,
    }
    assert escalation_summary({"stop_reason": "active_subregion_recommended"})[
        "escalation_level"
    ] == "patch_allowed"


def test_escalation_summary_marks_release_gates_as_manual_approval() -> None:
    assert escalation_summary(
        {
            "stop_reason": "status_action_required",
            "recommended_next_action": "run /fig_export --force-golden",
        }
    ) == {
        "escalation_level": "manual_approval_required",
        "requires_user_input": True,
        "requires_domain_review": False,
    }
    assert escalation_summary(
        {
            "stop_reason": "status_action_required",
            "recommended_next_action": "set accepted: true after review",
        }
    )["escalation_level"] == "manual_approval_required"


def test_escalation_summary_marks_agent_action_boundaries() -> None:
    for stop_reason in (
        "status_action_required",
        "missing_adjudication",
        "stale_adjudication",
        "invalid_adjudication",
        "reference_input_missing",
    ):
        assert escalation_summary({"stop_reason": stop_reason}) == {
            "escalation_level": "agent_action_required",
            "requires_user_input": False,
            "requires_domain_review": False,
        }


def test_escalation_summary_preserves_ambiguous_and_none_states() -> None:
    assert escalation_summary({"stop_reason": "ambiguous_patch_selection"})[
        "escalation_level"
    ] == "ambiguous_patch_selection"
    assert escalation_summary({"stop_reason": "no_actionable_findings"})[
        "escalation_level"
    ] == "none"
    assert escalation_summary({"stop_reason": "verify_only_complete"})[
        "escalation_level"
    ] == "none"
