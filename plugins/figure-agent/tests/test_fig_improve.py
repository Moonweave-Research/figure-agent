from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_driver  # noqa: E402
import fig_improve  # noqa: E402
import fig_run  # noqa: E402


def _driver(
    *,
    action: str,
    safe_command: str | None = None,
    stop_boundary: str | None = None,
    ready_improvement_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema": fig_driver.SCHEMA,
        "fixture": "demo",
        "mode": "review",
        "goal": "improve",
        "status": {"render_state": "FRESH", "critique_state": "FRESH"},
        "action": action,
        "safe_command": safe_command,
        "stop_boundary": stop_boundary,
        "reason": "driver reason",
        "forbidden_actions": [],
        "workspace_warnings": [],
        "may_execute": False,
        "next_action_summary": {
            "action": action,
            "safe_command": safe_command,
            "required_actor": "workflow_agent",
        },
    }
    if ready_improvement_summary is not None:
        payload["ready_improvement_summary"] = ready_improvement_summary
    return payload


def _run_payload(
    *,
    final_action: str,
    final_stop_reason: str,
    final_stop_boundary: str | None = None,
    ready_improvement_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    driver = _driver(
        action=final_action,
        stop_boundary=final_stop_boundary,
        ready_improvement_summary=ready_improvement_summary,
    )
    return {
        "schema": fig_run.SCHEMA,
        "fixture": "demo",
        "mode": "review",
        "goal": "improve",
        "execute": False,
        "max_steps": 5,
        "executable_actions": sorted(fig_run.EXECUTABLE_ACTIONS),
        "steps": [
            {
                "index": 1,
                "action": final_action,
                "safe_command": driver["safe_command"],
                "stop_boundary": final_stop_boundary,
                "would_execute": False,
                "executed": False,
                "stop_reason": final_stop_reason,
                "driver": driver,
            }
        ],
        "final_action": final_action,
        "final_safe_command": driver["safe_command"],
        "final_stop_boundary": final_stop_boundary,
        "final_stop_reason": final_stop_reason,
        "executed_count": 0,
    }


def _install_runs(
    monkeypatch: Any,
    runs: list[dict[str, Any]],
) -> list[tuple[str, bool, int]]:
    calls: list[tuple[str, bool, int]] = []

    def _fake_run_workflow(
        name: str,
        *,
        mode: str,
        goal: str,
        execute: bool = False,
        max_steps: int = fig_run.DEFAULT_MAX_STEPS,
        repo_root: Path = fig_run.REPO_ROOT,
    ) -> dict[str, Any]:
        calls.append((name, execute, max_steps))
        index = min(len(calls) - 1, len(runs) - 1)
        return dict(runs[index])

    monkeypatch.setattr(fig_improve, "_run_workflow", _fake_run_workflow)
    return calls


def test_improve_stops_at_host_critique_boundary(
    tmp_path: Path, monkeypatch: Any
) -> None:
    calls = _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_RUN_CRITIQUE,
                final_stop_reason=fig_run.STOP_HOST_BOUNDARY,
                final_stop_boundary=fig_driver.STOP_HOST_LLM_CRITIQUE,
            )
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        max_loops=10,
        repo_root=tmp_path,
    )

    assert calls == [("demo", True, fig_run.DEFAULT_MAX_STEPS)]
    assert payload["schema"] == "figure-agent.improve.v1"
    assert payload["final_stop_reason"] == "host_boundary"
    assert payload["final_required_actor"] == "host_llm"
    assert payload["next_operator_instruction"] == (
        "Run /fig_critique demo, then rerun /fig_improve."
    )
    assert payload["cycles"][0]["stop_reason"] == "host_boundary"


def test_improve_continues_after_safe_step_cap(
    tmp_path: Path, monkeypatch: Any
) -> None:
    calls = _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_RUN_COMPILE,
                final_stop_reason=fig_run.STOP_MAX_STEPS,
            ),
            _run_payload(
                final_action=fig_driver.ACTION_COMPLETE,
                final_stop_reason=fig_run.STOP_COMPLETE,
            ),
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        max_loops=3,
        max_steps_per_loop=1,
        repo_root=tmp_path,
    )

    assert calls == [("demo", True, 1), ("demo", True, 1)]
    assert payload["final_stop_reason"] == "complete"
    assert len(payload["cycles"]) == 2


def test_improve_reports_complete_without_optional_candidates(
    tmp_path: Path, monkeypatch: Any
) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_COMPLETE,
                final_stop_reason=fig_run.STOP_COMPLETE,
            )
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        repo_root=tmp_path,
    )

    assert payload["final_stop_reason"] == "complete"
    assert payload["final_required_actor"] == "none"
    assert payload["next_operator_instruction"] == "No required plugin action remains."


def test_improve_surfaces_optional_improvement_candidates(
    tmp_path: Path, monkeypatch: Any
) -> None:
    ready_improvement = {
        "schema": "figure-agent.ready-improvement-summary.v1",
        "state": "ready_but_improvable",
        "safe_to_ship": True,
        "blocks_release": False,
        "auto_patch_allowed": False,
        "candidate_count": 1,
        "candidates": [{"id": "I001", "source": "editorial_art_direction_summary"}],
    }
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_COMPLETE,
                final_stop_reason=fig_run.STOP_COMPLETE,
                ready_improvement_summary=ready_improvement,
            )
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        repo_root=tmp_path,
    )

    assert payload["final_stop_reason"] == "optional_improvement_available"
    assert payload["final_required_actor"] == "workflow_agent"
    assert payload["ready_improvement_summary"] == ready_improvement
    assert "Review ready_improvement_summary.candidates" in payload["next_operator_instruction"]


def test_improve_plan_only_runs_one_cycle_without_execution(
    tmp_path: Path, monkeypatch: Any
) -> None:
    calls = _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_RUN_COMPILE,
                final_stop_reason=fig_run.STOP_PLAN_ONLY,
            )
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=False,
        max_loops=5,
        repo_root=tmp_path,
    )

    assert calls == [("demo", False, fig_run.DEFAULT_MAX_STEPS)]
    assert payload["final_stop_reason"] == "plan_only"
    assert payload["final_required_actor"] == "workflow_agent"
    assert len(payload["cycles"]) == 1


def test_improve_stops_on_repeated_boundary(
    tmp_path: Path, monkeypatch: Any
) -> None:
    run = _run_payload(
        final_action=fig_driver.ACTION_RUN_COMPILE,
        final_stop_reason=fig_run.STOP_MAX_STEPS,
    )
    _install_runs(monkeypatch, [run, run])

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        max_loops=3,
        repo_root=tmp_path,
    )

    assert payload["final_stop_reason"] == "repeated_boundary"
    assert payload["final_required_actor"] == "workflow_agent"
    assert len(payload["cycles"]) == 2


def test_main_rejects_invalid_max_loops(
    tmp_path: Path, capsys: Any
) -> None:
    result = fig_improve.main(
        ["demo", "--goal", "improve", "--max-loops", "0"],
        repo_root=tmp_path,
    )

    captured = capsys.readouterr()
    assert result == 2
    assert "max_loops must be >= 1" in captured.err


def test_main_emits_json(tmp_path: Path, monkeypatch: Any, capsys: Any) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_COMPLETE,
                final_stop_reason=fig_run.STOP_COMPLETE,
            )
        ],
    )

    result = fig_improve.main(["demo", "--goal", "improve"], repo_root=tmp_path)

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.improve.v1"
    assert payload["fixture"] == "demo"
