"""Contract tests for release routing driven by human decision records."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from export_freshness import EXPORT_FRESH  # noqa: E402
from human_decision_record import (  # noqa: E402
    RELEASE_DECISION_PACKET_SCHEMA,
    STYLE_DIRECTION_PACKET_SCHEMA,
)
from human_decision_record import (
    SCHEMA as DECISION_RECORD_SCHEMA,
)
from status_explanation import build_status_explanation  # noqa: E402
from status_next_policy import select_next_hint  # noqa: E402


def _decision_record(
    decision_kind: str,
    *,
    packet_schema: str = RELEASE_DECISION_PACKET_SCHEMA,
) -> dict:
    return {
        "schema": DECISION_RECORD_SCHEMA,
        "fixture": "demo",
        "packet_schema": packet_schema,
        "packet_path": "docs/decision-packets/2026-07-01-acceptance/demo.json",
        "packet_recommendation": "accept_current_generated_export",
        "packet_timestamp": "2026-07-01T00:00:00Z",
        "queue_run_id": None,
        "decision_kind": decision_kind,
        "agent_recommendation": "Record an explicit release decision only.",
        "human_decision": decision_kind,
        "human_note": "Decision record authorizes routing, not automatic mutation.",
        "follow_up": {"implementation_slice": "route status to the explicit release surface"},
        "mutation_boundary": "no_source_mutation",
    }


def _stage4_hint(**overrides: object) -> str:
    kwargs = {
        "stage": 4,
        "name": "demo",
        "notes": [],
        "critique_state": "FRESH",
        "exports_substate": EXPORT_FRESH,
        "source_stale": False,
        "export_content_stale": False,
        "render_state": "FRESH",
        "partial": False,
        "final_artifact": {"state": "NONE", "kind": "generated_export", "path": None},
        "accepted": None,
    }
    kwargs.update(overrides)
    return select_next_hint(**kwargs)


def test_stage_4_without_decision_record_stays_at_acceptance_gate() -> None:
    hint = _stage4_hint()

    assert "fixture has no accepted or final-ready declaration" in hint
    assert "explicit human acceptance/final-artifact decision" in hint
    assert "closeout-accept" not in hint
    assert "accepted: true" not in hint


@pytest.mark.xfail(strict=True, reason="Wave 2 implementation should add decision-record routing")
def test_accept_current_record_routes_to_explicit_closeout_accept_surface() -> None:
    hint = _stage4_hint(human_decision_record=_decision_record("accept_current_generated_export"))

    assert "fig-agent closeout-accept demo" in hint
    assert "--decision accept" in hint
    assert "--reviewer" in hint
    assert "--rationale" in hint
    assert "accepted: true" not in hint


@pytest.mark.xfail(strict=True, reason="Wave 2 implementation should add decision-record routing")
def test_defer_record_keeps_release_blocked_and_routes_to_dogfood() -> None:
    hint = _stage4_hint(human_decision_record=_decision_record("defer_for_dogfood"))

    assert "release" in hint.lower()
    assert "blocked" in hint.lower()
    assert "/fig_loop demo" in hint or "dogfood" in hint.lower()
    assert "closeout-accept" not in hint
    assert "accepted: true" not in hint


@pytest.mark.xfail(strict=True, reason="Wave 2 implementation should add decision-record routing")
def test_style_record_keeps_release_blocked_and_routes_to_style_work() -> None:
    hint = _stage4_hint(
        human_decision_record=_decision_record(
            "request_full_style_redesign",
            packet_schema=STYLE_DIRECTION_PACKET_SCHEMA,
        )
    )

    assert "release" in hint.lower()
    assert "blocked" in hint.lower()
    assert "redesign" in hint.lower() or "style" in hint.lower()
    assert "closeout-accept" not in hint
    assert "accepted: true" not in hint


@pytest.mark.xfail(
    strict=True,
    reason="Wave 2 implementation should surface valid decision records",
)
def test_status_explanation_names_valid_record_without_claiming_release_ready() -> None:
    explanation = build_status_explanation(
        {
            "name": "demo",
            "stage": 4,
            "render_state": "FRESH",
            "critique_state": "FRESH",
            "export_state": "FRESH",
            "acceptance_state": "NOT_DECLARED",
            "final_artifact_state": "NONE",
            "release_ready": False,
            "final_ready": False,
            "human_decision_record": _decision_record("accept_current_generated_export"),
            "notes": [],
        }
    )

    first = explanation["first_blocker"]
    assert first["code"] == "release_decision_record_ready"
    assert "valid human decision record" in first["message"]
    assert first["next_command"].startswith("fig-agent closeout-accept demo")
    assert first["manual"] is True
