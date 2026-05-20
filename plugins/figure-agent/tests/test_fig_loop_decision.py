from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop_decision import (  # noqa: E402
    critique_refresh_action,
    decisions_with_value,
    first_decision,
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
