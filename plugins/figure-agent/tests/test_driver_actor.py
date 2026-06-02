from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import driver_actor  # noqa: E402


def _summary(
    *,
    action: str,
    stop_boundary: str | None = None,
    blocking_source: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "action": action,
        "stop_boundary": stop_boundary,
    }
    if blocking_source is not None:
        payload["next_action_summary"] = {
            "blocking_source": blocking_source,
            "requires_human": action in {"human_gate_stop", "release_blocked"},
        }
    return payload


def test_required_actor_for_host_critique_boundary() -> None:
    assert (
        driver_actor.required_actor_for_driver_summary(
            _summary(
                action="run_critique",
                stop_boundary="host_llm_critique_required",
            )
        )
        == "host_llm"
    )


def test_required_actor_for_human_gate() -> None:
    assert (
        driver_actor.required_actor_for_driver_summary(
            _summary(action="human_gate_stop", stop_boundary="human_gate_required")
        )
        == "human"
    )


def test_required_actor_for_release_boundary() -> None:
    assert (
        driver_actor.required_actor_for_driver_summary(
            _summary(
                action="release_blocked",
                stop_boundary="force_golden_required",
            )
        )
        == "release_operator"
    )


def test_required_actor_for_svg_polish_handoff() -> None:
    assert (
        driver_actor.required_actor_for_driver_summary(
            _summary(action="polish_handoff_stop")
        )
        == "svg_editor"
    )


def test_required_actor_defaults_to_workflow_agent() -> None:
    assert (
        driver_actor.required_actor_for_driver_summary(_summary(action="run_export"))
        == "workflow_agent"
    )


def test_blocking_source_uses_next_action_summary_before_stop_boundary() -> None:
    assert (
        driver_actor.blocking_source_for_driver_summary(
            _summary(
                action="release_blocked",
                stop_boundary="accepted_or_final_ready_required",
                blocking_source="publication_gate_required",
            )
        )
        == "publication_gate_required"
    )


def test_blocking_source_omits_mode_scoped_complete_rows() -> None:
    assert (
        driver_actor.blocking_source_for_driver_summary(
            _summary(action="complete", stop_boundary=None)
        )
        is None
    )


def test_requires_human_follows_next_action_summary_when_available() -> None:
    assert (
        driver_actor.requires_human_for_driver_summary(
            _summary(
                action="run_fig_loop",
                stop_boundary=None,
                blocking_source="driver.action",
            )
        )
        is False
    )
