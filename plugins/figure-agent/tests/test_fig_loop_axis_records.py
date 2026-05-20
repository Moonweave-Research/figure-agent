from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_axis_records import (  # noqa: E402
    adjudication_evaluation_state,
    adjudication_verdict,
    axis_record,
    publication_safety_evaluation_state,
    reference_fidelity_evaluation_state,
    status_axis_evaluation,
)


def test_axis_record_serializes_evidence_path_and_metadata(tmp_path: Path) -> None:
    record = axis_record(
        state="FRESH",
        verdict="fresh",
        source="status.render_state",
        evidence_path=tmp_path / "build.png",
        evaluation_state="passed",
        extra_field=["render"],
    )

    assert record == {
        "state": "FRESH",
        "verdict": "fresh",
        "source": "status.render_state",
        "evidence_path": str(tmp_path / "build.png"),
        "evaluation_state": "passed",
        "extra_field": ["render"],
    }


def test_status_axis_evaluation_maps_passed_not_configured_blocked_and_action() -> None:
    assert status_axis_evaluation("FRESH", passed_values={"FRESH"}) == "passed"
    assert (
        status_axis_evaluation(
            "NOT_REQUIRED",
            passed_values={"FRESH"},
            not_configured_values={"NOT_REQUIRED"},
        )
        == "not_configured"
    )
    assert (
        status_axis_evaluation(
            "REFERENCE_MISSING",
            passed_values={"FRESH"},
            blocked_values={"REFERENCE_MISSING"},
        )
        == "blocked"
    )
    assert status_axis_evaluation("STALE", passed_values={"FRESH"}) == "needs_action"


def test_adjudication_evaluation_state_preserves_loop_stop_precedence() -> None:
    fresh = {"state": "fresh", "decisions": []}
    stale = {"state": "stale", "decisions": []}
    missing = {"state": "missing", "decisions": []}

    assert adjudication_evaluation_state(fresh, "patch_target_recommended", "FRESH") == (
        "needs_action"
    )
    assert adjudication_evaluation_state(fresh, "verify_only_complete", "FRESH") == "passed"
    assert adjudication_evaluation_state(stale, "stale_adjudication", "FRESH") == (
        "needs_action"
    )
    assert adjudication_evaluation_state(missing, "status_action_required", "STALE") == (
        "not_configured"
    )


def test_reference_and_publication_evaluation_state_mappings() -> None:
    assert reference_fidelity_evaluation_state(True, "REFERENCE_MISSING") == "blocked"
    assert reference_fidelity_evaluation_state(False, "NOT_REQUIRED") == "not_configured"
    assert reference_fidelity_evaluation_state(False, "FRESH") == "not_evaluated"

    assert publication_safety_evaluation_state("ACCEPTED", "not_requested") == "passed"
    assert publication_safety_evaluation_state("NOT_DECLARED", "not_requested") == (
        "not_configured"
    )
    assert publication_safety_evaluation_state("PENDING", "not_requested") == "needs_action"
    assert publication_safety_evaluation_state("ACCEPTED", "required") == "blocked"


def test_adjudication_verdict_maps_stop_reason_and_state() -> None:
    fresh_empty = {"state": "fresh", "decisions": []}
    fresh_with_decision = {"state": "fresh", "decisions": [{"finding_id": "C001"}]}

    assert adjudication_verdict(fresh_empty, "patch_target_recommended") == "actionable"
    assert adjudication_verdict(fresh_empty, "human_gate_required") == "human_gate"
    assert adjudication_verdict({"state": "invalid"}, "invalid_adjudication") == "invalid"
    assert adjudication_verdict(fresh_empty, "no_actionable_findings") == "complete"
    assert adjudication_verdict(fresh_with_decision, "verify_only_complete") == "complete"
    assert adjudication_verdict(fresh_empty, "verify_only_complete") == "not_actionable"
