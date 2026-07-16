from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_driver  # noqa: E402
import fig_run  # noqa: E402
import fig_run_records  # noqa: E402
from next_action_summary import driver_next_action_summary  # noqa: E402


def _driver_summary(
    *,
    action: str,
    safe_command: str | None,
    stop_boundary: str | None = None,
    reason: str = "driver reason",
    status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": fig_driver.SCHEMA,
        "fixture": "runner_demo",
        "mode": "review",
        "goal": "close loop",
        "status": status or {"render_state": "STALE"},
        "action": action,
        "safe_command": safe_command,
        "stop_boundary": stop_boundary,
        "reason": reason,
        "forbidden_actions": [],
        "workspace_warnings": [],
        "may_execute": False,
        "next_action_summary": {
            "action": action,
            "safe_command": safe_command,
        },
    }


def _install_driver_sequence(
    monkeypatch: pytest.MonkeyPatch, sequence: list[dict[str, Any]]
) -> list[str]:
    calls: list[str] = []

    def _fake_driver(
        name: str,
        *,
        mode: str,
        goal: str,
        repo_root: Path,
    ) -> dict[str, Any]:
        calls.append(f"{name}:{mode}:{goal}:{repo_root}")
        index = min(len(calls) - 1, len(sequence) - 1)
        return dict(sequence[index])

    monkeypatch.setattr(fig_run, "_driver_summary", _fake_driver)
    return calls


def test_plan_only_reports_compile_without_executing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            )
        ],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=False,
        repo_root=tmp_path,
    )

    assert payload["schema"] == "figure-agent.run.v1"
    assert payload["execute"] is False
    assert payload["executed_count"] == 0
    assert payload["final_action"] == fig_driver.ACTION_RUN_COMPILE
    assert payload["final_stop_reason"] == "plan_only"
    assert payload["steps"][0]["would_execute"] is True
    assert payload["steps"][0]["executed"] is False
    assert commands == []


def test_execute_runs_compile_then_stops_at_host_critique(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            ),
            _driver_summary(
                action=fig_driver.ACTION_RUN_CRITIQUE,
                safe_command="/fig_critique runner_demo",
                stop_boundary=fig_driver.STOP_HOST_LLM_CRITIQUE,
            ),
        ],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(returncode=0, stdout="ok\n", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert len(calls) == 2
    assert commands == ["bash scripts/compile.sh examples/runner_demo/runner_demo.tex"]
    assert payload["executed_count"] == 1
    assert payload["final_action"] == fig_driver.ACTION_RUN_CRITIQUE
    assert payload["final_stop_boundary"] == fig_driver.STOP_HOST_LLM_CRITIQUE
    assert payload["final_stop_reason"] == "host_boundary"
    assert payload["steps"][0]["executed"] is True
    assert payload["steps"][0]["returncode"] == 0
    assert payload["steps"][1]["executed"] is False


def test_runner_accepts_quoted_fixture_name_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    name = "runner demo"
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh 'examples/runner demo/runner demo.tex'",
            ),
            _driver_summary(action=fig_driver.ACTION_COMPLETE, safe_command=None),
        ],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        name,
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert commands == ["bash scripts/compile.sh 'examples/runner demo/runner demo.tex'"]
    assert payload["executed_count"] == 1
    assert payload["final_stop_reason"] == "complete"


def test_first_step_expectation_requires_action_and_command_together(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="first-step action and command"):
        fig_run.run_workflow(
            "runner_demo",
            mode="review",
            goal="close loop",
            execute=True,
            expected_first_action=fig_driver.ACTION_RUN_COMPILE,
            repo_root=tmp_path,
        )


def test_first_step_expectation_rejects_closed_loop_lifecycle_inputs(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="first-step expectation.*closed-loop"):
        fig_run.run_workflow(
            "runner_demo",
            mode="review",
            goal="close loop",
            execute=True,
            expected_first_action=fig_driver.ACTION_RUN_COMPILE,
            expected_first_safe_command=(
                "bash scripts/compile.sh examples/runner_demo/runner_demo.tex"
            ),
            closed_loop_state=tmp_path / "state.json",
            repo_root=tmp_path,
        )


@pytest.mark.parametrize(
    ("live_action", "live_command", "live_boundary"),
    (
        (
            fig_driver.ACTION_RUN_EXPORT,
            "fig-agent export runner_demo",
            None,
        ),
        (
            fig_driver.ACTION_RUN_COMPILE,
            "bash scripts/compile.sh examples/runner_demo/other.tex",
            None,
        ),
        (
            fig_driver.ACTION_RUN_COMPILE,
            "bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            fig_driver.STOP_CLOSEOUT,
        ),
        (
            fig_driver.ACTION_COMPLETE,
            None,
            None,
        ),
    ),
)
def test_first_step_expectation_stops_stale_plan_before_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    live_action: str,
    live_command: str | None,
    live_boundary: str | None,
) -> None:
    planned_action = fig_driver.ACTION_RUN_COMPILE
    planned_command = (
        "bash scripts/compile.sh examples/runner_demo/runner_demo.tex"
    )
    live_summary = _driver_summary(
        action=live_action,
        safe_command=live_command,
        stop_boundary=live_boundary,
    )
    _install_driver_sequence(monkeypatch, [live_summary])
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        expected_first_action=planned_action,
        expected_first_safe_command=planned_command,
        repo_root=tmp_path,
    )

    assert commands == []
    assert payload["executed_count"] == 0
    assert payload["final_stop_reason"] == fig_run.STOP_STALE_PLAN
    assert payload["steps"] == [
        {
            "index": 1,
            "action": live_action,
            "safe_command": live_command,
            "stop_boundary": live_boundary,
            "reason": "driver reason",
            "would_execute": False,
            "executed": False,
            "returncode": None,
            "stdout_tail": "",
            "stderr_tail": "",
            "stop_reason": fig_run.STOP_STALE_PLAN,
            "driver": live_summary,
        }
    ]
    assert payload["plan_binding"] == {
        "scope": "first_step_only",
        "state": "stale",
        "planned": {
            "action": planned_action,
            "safe_command": planned_command,
        },
        "live": {
            "action": live_action,
            "safe_command": live_command,
            "stop_boundary": live_boundary,
        },
        "mutation_prevented": True,
    }
    assert payload["boundary_handoff"]["required_actor"] == "workflow_agent"
    assert payload["boundary_handoff"]["allowed_scope"] == ["read-only"]
    assert payload["boundary_handoff"]["publication_acceptance"] == "not_claimed"


def test_first_step_expectation_matches_once_then_allows_live_replanning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    compile_command = (
        "bash scripts/compile.sh examples/runner_demo/runner_demo.tex"
    )
    loop_command = (
        "uv run python3 scripts/fig_loop.py runner_demo --goal 'close loop' --json"
    )
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command=compile_command,
            ),
            _driver_summary(
                action=fig_driver.ACTION_RUN_FIG_LOOP,
                safe_command=loop_command,
            ),
            _driver_summary(action=fig_driver.ACTION_COMPLETE, safe_command=None),
        ],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        expected_first_action=fig_driver.ACTION_RUN_COMPILE,
        expected_first_safe_command=compile_command,
        repo_root=tmp_path,
    )

    assert commands == [compile_command, loop_command]
    assert payload["executed_count"] == 2
    assert payload["final_stop_reason"] == fig_run.STOP_COMPLETE
    assert payload["plan_binding"] == {
        "scope": "first_step_only",
        "state": "matched",
        "planned": {
            "action": fig_driver.ACTION_RUN_COMPILE,
            "safe_command": compile_command,
        },
        "live": {
            "action": fig_driver.ACTION_RUN_COMPILE,
            "safe_command": compile_command,
            "stop_boundary": None,
        },
        "mutation_prevented": False,
    }


@pytest.mark.parametrize(
    ("action", "safe_command"),
    [
        (
            fig_driver.ACTION_RUN_COMPILE,
            "bash scripts/compile.sh examples/other_demo/other_demo.tex",
        ),
        (
            fig_driver.ACTION_RUN_ADJUDICATE,
            "uv run python3 scripts/critique_adjudication.py scaffold other_demo",
        ),
        (
            fig_driver.ACTION_RUN_FIG_LOOP,
            "uv run python3 scripts/fig_loop.py other_demo --goal 'close loop' --json",
        ),
    ],
)
def test_runner_refuses_mismatched_fixture_commands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    safe_command: str,
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [_driver_summary(action=action, safe_command=safe_command)],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert commands == []
    assert payload["executed_count"] == 0
    assert payload["final_action"] == action
    assert payload["final_stop_reason"] == "not_executable_action"
    assert payload["steps"][0]["would_execute"] is False


def test_execute_stops_immediately_at_host_critique(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_CRITIQUE,
                safe_command="/fig_critique runner_demo",
                stop_boundary=fig_driver.STOP_HOST_LLM_CRITIQUE,
            )
            | {
                "next_action_summary": {
                    "action": fig_driver.ACTION_RUN_CRITIQUE,
                    "safe_command": "/fig_critique runner_demo",
                    "allowed_scope": [
                        "examples/runner_demo/critique.md",
                        "examples/runner_demo/build/audit_crops/",
                    ],
                    "forbidden_scope": ["hidden source edits"],
                    "evidence_refs": [f"driver.stop_boundary:{fig_driver.STOP_HOST_LLM_CRITIQUE}"],
                }
            }
        ],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert commands == []
    assert payload["executed_count"] == 0
    assert payload["final_stop_reason"] == "host_boundary"
    assert payload["steps"][0]["would_execute"] is False
    handoff = payload["boundary_handoff"]
    assert handoff["schema"] == "figure-agent.boundary-handoff.v1"
    assert handoff["action"] == fig_driver.ACTION_RUN_CRITIQUE
    assert handoff["stop_boundary"] == fig_driver.STOP_HOST_LLM_CRITIQUE
    assert handoff["required_actor"] == "host_llm"
    assert handoff["allowed_scope"] == [
        "examples/runner_demo/critique.md",
        "examples/runner_demo/build/audit_crops/",
    ]
    assert handoff["continuation_guidance"]["rerun_live_status_first"] is True
    assert handoff["continuation_guidance"]["rerun_live_driver_first"] is True
    assert "command" not in handoff["continuation_guidance"]


def test_execute_stops_at_export_without_safe_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_EXPORT,
                safe_command="uv run python3 scripts/run_export.py runner_demo",
            )
        ],
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert payload["executed_count"] == 0
    assert payload["final_action"] == fig_driver.ACTION_RUN_EXPORT
    assert payload["final_stop_reason"] == "not_executable_action"
    assert payload["steps"][0]["would_execute"] is False


def test_execute_runs_draft_export_then_requeries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_EXPORT,
                safe_command="uv run python3 scripts/run_export.py runner_demo",
                status={
                    "render_state": "FRESH",
                    "critique_state": "NOT_REQUIRED",
                    "export_state": "MISSING",
                    "acceptance_state": "NOT_DECLARED",
                },
            ),
            _driver_summary(action=fig_driver.ACTION_COMPLETE, safe_command=None),
        ],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(returncode=0, stdout="exported\n", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="release",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert len(calls) == 2
    assert commands == ["uv run python3 scripts/run_export.py runner_demo"]
    assert payload["executable_actions"] == [
        "run_adjudicate",
        "run_compile",
        "run_export",
        "run_fig_loop",
    ]
    assert payload["executed_count"] == 1
    assert payload["final_action"] == fig_driver.ACTION_COMPLETE
    assert payload["final_stop_reason"] == "complete"
    assert payload["steps"][0]["executed"] is True
    assert payload["steps"][0]["returncode"] == 0
    assert "boundary_handoff" not in payload


def test_export_with_stop_boundary_is_not_executed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_EXPORT,
                safe_command="uv run python3 scripts/run_export.py runner_demo",
                stop_boundary=fig_driver.STOP_CLOSEOUT,
                status={
                    "render_state": "FRESH",
                    "critique_state": "NOT_REQUIRED",
                    "export_state": "MISSING",
                    "acceptance_state": "NOT_DECLARED",
                },
            )
        ],
    )
    commands: list[str] = []
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda command, *, repo_root: commands.append(command),
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert commands == []
    assert payload["executed_count"] == 0
    assert payload["final_action"] == fig_driver.ACTION_RUN_EXPORT
    assert payload["final_stop_boundary"] == fig_driver.STOP_CLOSEOUT
    assert payload["final_stop_reason"] == "not_executable_action"
    assert payload["steps"][0]["would_execute"] is False
    assert payload["boundary_handoff"]["closeout_checks"][0] == (
            "run fig-agent closeout runner_demo --json"
    )


def test_closeout_boundary_executes_verify_only_fig_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commands: list[str] = []
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_FIG_LOOP,
                safe_command=(
                    "uv run python3 scripts/fig_loop.py runner_demo --goal 'close loop' --json"
                ),
                stop_boundary=fig_driver.STOP_CLOSEOUT,
            )
        ],
    )
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda command, *, repo_root: commands.append(command)
        or fig_run.CommandResult(returncode=0, stdout="", stderr=""),
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert commands == ["uv run python3 scripts/fig_loop.py runner_demo --goal 'close loop' --json"]
    assert payload["executed_count"] == 1
    assert payload["final_action"] == fig_driver.ACTION_RUN_FIG_LOOP
    assert payload["final_stop_boundary"] == fig_driver.STOP_CLOSEOUT
    assert payload["final_stop_reason"] == "repeated_executable_action"


@pytest.mark.parametrize(
    ("acceptance_state", "export_state"),
    [
        ("ACCEPTED", "STALE"),
        ("NOT_DECLARED", "TRACKED_GOLDEN"),
    ],
)
def test_export_for_accepted_or_tracked_fixture_is_not_executed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    acceptance_state: str,
    export_state: str,
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_EXPORT,
                safe_command="uv run python3 scripts/run_export.py runner_demo",
                status={
                    "render_state": "FRESH",
                    "critique_state": "FRESH",
                    "export_state": export_state,
                    "acceptance_state": acceptance_state,
                },
            )
        ],
    )
    commands: list[str] = []
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda command, *, repo_root: commands.append(command),
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="release",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert commands == []
    assert payload["executed_count"] == 0
    assert payload["final_action"] == fig_driver.ACTION_RUN_EXPORT
    assert payload["final_stop_reason"] == "not_executable_action"
    assert payload["steps"][0]["would_execute"] is False


def test_export_with_unclosed_critique_is_not_executed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_EXPORT,
                safe_command="uv run python3 scripts/run_export.py runner_demo",
                status={
                    "render_state": "FRESH",
                    "critique_state": "STALE",
                    "export_state": "MISSING",
                    "acceptance_state": "NOT_DECLARED",
                },
            )
        ],
    )
    commands: list[str] = []
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda command, *, repo_root: commands.append(command),
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="release",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert commands == []
    assert payload["executed_count"] == 0
    assert payload["final_stop_reason"] == "not_executable_action"
    assert payload["steps"][0]["would_execute"] is False


@pytest.mark.parametrize("flag", ["--force-golden", "--skip-critique"])
def test_export_forbidden_flags_are_not_executed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, flag: str
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_EXPORT,
                safe_command=f"uv run python3 scripts/run_export.py runner_demo {flag}",
                status={
                    "render_state": "FRESH",
                    "critique_state": "NOT_REQUIRED",
                    "export_state": "MISSING",
                    "acceptance_state": "NOT_DECLARED",
                },
            )
        ],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="release",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert commands == []
    assert payload["executed_count"] == 0
    assert payload["final_stop_reason"] == "not_executable_action"
    assert payload["steps"][0]["would_execute"] is False


def test_export_for_other_fixture_command_is_not_executed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_EXPORT,
                safe_command="uv run python3 scripts/run_export.py other_demo",
                status={
                    "render_state": "FRESH",
                    "critique_state": "NOT_REQUIRED",
                    "export_state": "MISSING",
                    "acceptance_state": "NOT_DECLARED",
                },
            )
        ],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="release",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert commands == []
    assert payload["executed_count"] == 0
    assert payload["final_stop_reason"] == "not_executable_action"
    assert payload["steps"][0]["would_execute"] is False


def test_export_failure_stops_without_requery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_EXPORT,
                safe_command="uv run python3 scripts/run_export.py runner_demo",
                status={
                    "render_state": "FRESH",
                    "critique_state": "NOT_REQUIRED",
                    "export_state": "STALE",
                    "acceptance_state": "NOT_DECLARED",
                },
            ),
            _driver_summary(action=fig_driver.ACTION_COMPLETE, safe_command=None),
        ],
    )

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        return fig_run.CommandResult(returncode=8, stdout="", stderr="export failed")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="release",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert len(calls) == 1
    assert payload["executed_count"] == 1
    assert payload["final_action"] == fig_driver.ACTION_RUN_EXPORT
    assert payload["final_stop_reason"] == "command_failed"
    assert payload["steps"][0]["stderr_tail"] == "export failed"


def test_execute_runs_missing_adjudication_scaffold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_ADJUDICATE,
                safe_command="uv run python3 scripts/critique_adjudication.py scaffold runner_demo",
            ),
            _driver_summary(
                action=fig_driver.ACTION_RUN_FIG_LOOP,
                safe_command=(
                    "uv run python3 scripts/fig_loop.py runner_demo --goal 'close loop' --json"
                ),
            ),
            _driver_summary(action=fig_driver.ACTION_COMPLETE, safe_command=None),
        ],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        if "critique_adjudication.py scaffold" in command:
            adjudication = repo_root / "examples" / "runner_demo" / "critique_adjudication.yaml"
            adjudication.parent.mkdir(parents=True, exist_ok=True)
            adjudication.write_text(
                "schema: figure-agent.critique-adjudication.v1\n",
                encoding="utf-8",
            )
        return fig_run.CommandResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert len(calls) == 3
    assert commands == [
        "uv run python3 scripts/critique_adjudication.py scaffold runner_demo",
        "uv run python3 scripts/fig_loop.py runner_demo --goal 'close loop' --json",
    ]
    assert payload["executable_actions"] == [
        "run_adjudicate",
        "run_compile",
        "run_export",
        "run_fig_loop",
    ]
    assert payload["executed_count"] == 2
    assert payload["final_action"] == fig_driver.ACTION_COMPLETE
    assert payload["final_stop_reason"] == "complete"


def test_existing_adjudication_file_blocks_auto_scaffold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adjudication = tmp_path / "examples" / "runner_demo" / "critique_adjudication.yaml"
    adjudication.parent.mkdir(parents=True)
    adjudication.write_text("existing: human decision\n", encoding="utf-8")
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_ADJUDICATE,
                safe_command="uv run python3 scripts/critique_adjudication.py scaffold runner_demo",
            )
        ],
    )
    commands: list[str] = []
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda command, *, repo_root: commands.append(command),
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert commands == []
    assert payload["executed_count"] == 0
    assert payload["final_action"] == fig_driver.ACTION_RUN_ADJUDICATE
    assert payload["final_stop_reason"] == "not_executable_action"
    assert payload["steps"][0]["would_execute"] is False
    handoff = payload["boundary_handoff"]
    assert handoff["required_actor"] == "workflow_agent"
    assert handoff["action"] == fig_driver.ACTION_RUN_ADJUDICATE
    assert handoff["closeout_checks"] == [
        "inspect critique_adjudication.yaml",
        "rerun live /fig_status",
        "rerun live /fig_drive",
    ]
    assert "command" not in handoff["continuation_guidance"]


def test_adjudication_scaffold_failure_stops_without_requery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_ADJUDICATE,
                safe_command="uv run python3 scripts/critique_adjudication.py scaffold runner_demo",
            ),
            _driver_summary(action=fig_driver.ACTION_COMPLETE, safe_command=None),
        ],
    )

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        return fig_run.CommandResult(returncode=4, stdout="", stderr="scaffold failed")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert len(calls) == 1
    assert payload["executed_count"] == 1
    assert payload["final_action"] == fig_driver.ACTION_RUN_ADJUDICATE
    assert payload["final_stop_reason"] == "command_failed"
    assert payload["steps"][0]["stderr_tail"] == "scaffold failed"


def test_execute_runs_compile_and_fig_loop_then_stops_at_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            ),
            _driver_summary(
                action=fig_driver.ACTION_RUN_FIG_LOOP,
                safe_command=(
                    "uv run python3 scripts/fig_loop.py runner_demo --goal 'close loop' --json"
                ),
            ),
            _driver_summary(
                action=fig_driver.ACTION_HUMAN_GATE_STOP,
                safe_command=None,
                stop_boundary=fig_driver.STOP_HUMAN_GATE,
            ),
        ],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert len(calls) == 3
    assert commands == [
        "bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
        "uv run python3 scripts/fig_loop.py runner_demo --goal 'close loop' --json",
    ]
    assert payload["executable_actions"] == [
        "run_adjudicate",
        "run_compile",
        "run_export",
        "run_fig_loop",
    ]
    assert payload["executed_count"] == 2
    assert payload["final_action"] == fig_driver.ACTION_HUMAN_GATE_STOP
    assert payload["final_stop_reason"] == "not_executable_action"
    assert payload["steps"][1]["action"] == fig_driver.ACTION_RUN_FIG_LOOP
    assert payload["steps"][1]["executed"] is True
    handoff = payload["boundary_handoff"]
    assert handoff["required_actor"] == "human"
    assert handoff["action"] == fig_driver.ACTION_HUMAN_GATE_STOP
    assert handoff["stop_boundary"] == fig_driver.STOP_HUMAN_GATE
    assert "command" not in handoff["continuation_guidance"]


def test_fig_loop_failure_stops_without_requery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_FIG_LOOP,
                safe_command=(
                    "uv run python3 scripts/fig_loop.py runner_demo --goal 'close loop' --json"
                ),
            ),
            _driver_summary(action=fig_driver.ACTION_COMPLETE, safe_command=None),
        ],
    )

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        return fig_run.CommandResult(returncode=9, stdout="", stderr="loop failed")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert len(calls) == 1
    assert payload["executed_count"] == 1
    assert payload["final_action"] == fig_driver.ACTION_RUN_FIG_LOOP
    assert payload["final_stop_reason"] == "command_failed"
    assert payload["steps"][0]["stderr_tail"] == "loop failed"


def test_fig_loop_with_stop_boundary_is_not_executed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_FIG_LOOP,
                safe_command=(
                    "uv run python3 scripts/fig_loop.py runner_demo --goal 'close loop' --json"
                ),
                stop_boundary=fig_driver.STOP_MODE_FORBIDDEN,
            )
        ],
    )
    commands: list[str] = []
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda command, *, repo_root: commands.append(command),
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="polish",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert commands == []
    assert payload["executed_count"] == 0
    assert payload["final_action"] == fig_driver.ACTION_RUN_FIG_LOOP
    assert payload["final_stop_boundary"] == fig_driver.STOP_MODE_FORBIDDEN
    assert payload["final_stop_reason"] == "not_executable_action"


def test_command_failure_stops_without_requery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            ),
            _driver_summary(
                action=fig_driver.ACTION_RUN_CRITIQUE,
                safe_command="/fig_critique runner_demo",
                stop_boundary=fig_driver.STOP_HOST_LLM_CRITIQUE,
            ),
        ],
    )

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        return fig_run.CommandResult(returncode=7, stdout="", stderr="compile failed")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert len(calls) == 1
    assert payload["executed_count"] == 1
    assert payload["final_stop_reason"] == "command_failed"
    assert payload["steps"][0]["returncode"] == 7
    assert payload["steps"][0]["stderr_tail"] == "compile failed"
    handoff = payload["boundary_handoff"]
    assert handoff["required_actor"] == "workflow_agent"
    assert handoff["action"] == fig_driver.ACTION_RUN_COMPILE
    assert handoff["closeout_checks"] == ["inspect command stderr_tail", "rerun live /fig_status"]
    assert "compile failed" in handoff["blocking_reason"]


def test_stops_after_repeated_executable_command_without_progress(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_FIG_LOOP,
                safe_command=(
                    "uv run python3 scripts/fig_loop.py runner_demo --goal 'close loop' --json"
                ),
            )
        ],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(0, "", "")

    monkeypatch.setattr(
        fig_run,
        "_run_command",
        _fake_run,
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        max_steps=2,
        repo_root=tmp_path,
    )

    assert commands == ["uv run python3 scripts/fig_loop.py runner_demo --goal 'close loop' --json"]
    assert payload["executed_count"] == 1
    assert payload["final_stop_reason"] == "repeated_executable_action"
    assert len(payload["steps"]) == 2
    assert payload["steps"][0]["executed"] is True
    assert payload["steps"][1]["executed"] is False
    assert payload["steps"][1]["would_execute"] is False
    handoff = payload["boundary_handoff"]
    assert handoff["required_actor"] == "workflow_agent"
    assert handoff["action"] == fig_driver.ACTION_RUN_FIG_LOOP
    assert "same executable action and command" in handoff["blocking_reason"]
    assert handoff["closeout_checks"] == [
        "inspect repeated action",
        "rerun live /fig_status",
        "rerun live /fig_drive",
    ]
    assert "runner.stop_reason:repeated_executable_action" in handoff["evidence_refs"]
    assert "command" not in handoff["continuation_guidance"]


def test_basin_detected_handoff_preserves_step_out_actions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    summary = _driver_summary(
        action=fig_driver.ACTION_HUMAN_GATE_STOP,
        safe_command=None,
        stop_boundary=fig_driver.STOP_HUMAN_GATE,
        reason="latest /fig_loop checkpoint reports repeated loop basin.",
    )
    summary["loop_checkpoint"] = {
        "final_stop_reason": "basin_detected",
        "basin_summary": {
            "schema": "figure-agent.loop-basin.v1",
            "evaluation_state": "basin_detected",
            "history_count": 3,
            "signal": {
                "signal_class": "reference_aesthetic_metric",
                "signal_value": "palette_histogram_distance",
                "signal_key": "reference_aesthetic_metric:palette_histogram_distance",
                "source": "reference_aesthetic_metrics_summary",
            },
            "recommended_step_out_actions": [
                "run external second-opinion review on the repeated issue",
                "revise reference-learning contract if reference style conflicts with intent",
            ],
        },
    }
    summary["next_action_summary"] = {
        "action": fig_driver.ACTION_HUMAN_GATE_STOP,
        "safe_command": None,
        "evidence_refs": ["loop.final_stop_reason:basin_detected"],
    }
    _install_driver_sequence(monkeypatch, [summary])

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    assert payload["final_stop_reason"] == fig_run.STOP_NOT_EXECUTABLE
    handoff = payload["boundary_handoff"]
    assert handoff["required_actor"] == "human"
    assert handoff["basin_summary"] == summary["loop_checkpoint"]["basin_summary"]
    assert handoff["closeout_checks"][:2] == [
        "run external second-opinion review on the repeated issue",
        "revise reference-learning contract if reference style conflicts with intent",
    ]
    assert any(check.startswith("rerun live /fig_loop") for check in handoff["closeout_checks"])
    assert "loop.final_stop_reason:basin_detected" in handoff["evidence_refs"]


def test_release_blocked_handoff_requires_release_operator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RELEASE_BLOCKED,
                safe_command=None,
                stop_boundary=fig_driver.STOP_FORCE_GOLDEN,
                reason="tracked golden export requires explicit force-golden",
            )
        ],
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="release",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    handoff = payload["boundary_handoff"]
    assert payload["final_stop_reason"] == "not_executable_action"
    assert handoff["required_actor"] == "release_operator"
    assert handoff["action"] == fig_driver.ACTION_RELEASE_BLOCKED
    assert handoff["stop_boundary"] == fig_driver.STOP_FORCE_GOLDEN
    assert handoff["allowed_scope"] == ["read-only"]
    assert "command" not in handoff["continuation_guidance"]


def test_reference_missing_handoff_requires_workflow_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_CRITIQUE,
                safe_command=None,
                stop_boundary=fig_driver.STOP_REFERENCE_MISSING,
                reason="reference image missing; fix spec path first",
            )
        ],
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    handoff = payload["boundary_handoff"]
    assert handoff["required_actor"] == "workflow_agent"
    assert handoff["stop_boundary"] == fig_driver.STOP_REFERENCE_MISSING
    assert handoff["closeout_checks"] == [
        "fix reference path or provide reference image",
        "rerun live /fig_status",
        "rerun live /fig_drive",
    ]


def test_semantic_backport_handoff_requires_workflow_agent_not_svg_editor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    driver_summary = _driver_summary(
        action=fig_driver.ACTION_POLISH_HANDOFF_STOP,
        safe_command=None,
        stop_boundary=fig_driver.STOP_SEMANTIC_BACKPORT,
        reason="polished SVG requires semantic backport to TikZ first",
    )
    # Mirror fig_driver.py attaching the real next_action_summary so the
    # boundary_handoff copies the source-repair allowed_scope, not the stub.
    driver_summary["next_action_summary"] = driver_next_action_summary(driver_summary)
    _install_driver_sequence(monkeypatch, [driver_summary])

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="polish",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    handoff = payload["boundary_handoff"]
    assert handoff["required_actor"] == "workflow_agent"
    assert handoff["action"] == fig_driver.ACTION_POLISH_HANDOFF_STOP
    assert handoff["stop_boundary"] == fig_driver.STOP_SEMANTIC_BACKPORT
    assert handoff["allowed_scope"] == [
        "examples/runner_demo/spec.yaml",
        "examples/runner_demo/briefing.md",
        "examples/runner_demo/runner_demo.tex",
    ]
    assert handoff["closeout_checks"] == [
        "backport semantic changes to source/spec",
        "rerun live /fig_status",
        "rerun live /fig_drive",
    ]


def test_patch_handoff_boundary_is_deferred_without_patch_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_PATCH_HANDOFF_STOP,
                safe_command=None,
                stop_boundary=fig_driver.STOP_PATCH_HANDOFF,
                reason="single patch target exists",
                status={"render_state": "FRESH"},
            )
            | {
                "next_action_summary": {
                    "action": fig_driver.ACTION_PATCH_HANDOFF_STOP,
                    "allowed_scope": ["examples/runner_demo/runner_demo.tex"],
                    "forbidden_scope": ["accepted", "golden_contract"],
                    "evidence_refs": ["loop.final_stop_reason:patch_target_recommended"],
                }
            }
        ],
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        repo_root=tmp_path,
    )

    handoff = payload["boundary_handoff"]
    assert handoff["action"] == fig_driver.ACTION_PATCH_HANDOFF_STOP
    assert handoff["stop_boundary"] == fig_driver.STOP_PATCH_HANDOFF
    assert handoff["required_actor"] == "workflow_agent"
    assert handoff["deferred_boundary"] == "patch_source_mutation_deferred_until_70c"
    assert handoff["allowed_scope"] == ["read-only"]
    assert handoff["forbidden_scope"] == [
        "source mutation before patch executor currentness is verified"
    ]


def test_main_accepts_format_json_as_output_compatibility_noop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    example_dir = tmp_path / "examples" / "runner_demo"
    example_dir.mkdir(parents=True)
    (example_dir / "runner_demo.tex").write_text("% source\n", encoding="utf-8")
    (example_dir / "briefing.md").write_text("brief\n", encoding="utf-8")
    (example_dir / "spec.yaml").write_text("name: runner_demo\n", encoding="utf-8")
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_CRITIQUE,
                safe_command="/fig_critique runner_demo",
                stop_boundary=fig_driver.STOP_HOST_LLM_CRITIQUE,
            )
        ],
    )

    result = fig_run.main(
        [
            "runner_demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--format",
            "json",
        ],
        repo_root=tmp_path,
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["schema"] == "figure-agent.run.v1"
    assert payload["fixture"] == "runner_demo"
    assert payload["execute"] is False


def test_main_accepts_json_as_output_compatibility_noop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    example_dir = tmp_path / "examples" / "runner_demo"
    example_dir.mkdir(parents=True)
    (example_dir / "runner_demo.tex").write_text("% source\n", encoding="utf-8")
    (example_dir / "briefing.md").write_text("brief\n", encoding="utf-8")
    (example_dir / "spec.yaml").write_text("name: runner_demo\n", encoding="utf-8")
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_CRITIQUE,
                safe_command="/fig_critique runner_demo",
                stop_boundary=fig_driver.STOP_HOST_LLM_CRITIQUE,
            )
        ],
    )

    result = fig_run.main(
        [
            "runner_demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--json",
        ],
        repo_root=tmp_path,
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["schema"] == "figure-agent.run.v1"
    assert payload["fixture"] == "runner_demo"
    assert payload["execute"] is False


def test_main_records_non_authoritative_run_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    example_dir = tmp_path / "examples" / "runner_demo"
    example_dir.mkdir(parents=True)
    (example_dir / "runner_demo.tex").write_text("% source\n", encoding="utf-8")
    (example_dir / "briefing.md").write_text("brief\n", encoding="utf-8")
    (example_dir / "spec.yaml").write_text("name: runner_demo\n", encoding="utf-8")
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_CRITIQUE,
                safe_command="/fig_critique runner_demo",
                stop_boundary=fig_driver.STOP_HOST_LLM_CRITIQUE,
            )
        ],
    )
    runs_root = tmp_path / "fig-run-runs"

    result = fig_run.main(
        [
            "runner_demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--record",
            "--runs-root",
            str(runs_root),
        ],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    journal = payload["journal"]
    assert journal["schema"] == "figure-agent.fig-run-journal-ref.v1"
    assert journal["authoritative"] is False
    assert journal["replay_allowed"] is False
    assert journal["commands_are_evidence_only"] is True
    assert journal["rerun_live_status_first"] is True
    assert journal["rerun_live_driver_first"] is True
    assert "command" not in journal

    run_dir = Path(journal["run_dir"])
    assert run_dir.parent == runs_root
    assert run_dir.name.endswith("-runner_demo")
    manifest_path = run_dir / "run_manifest.json"
    run_path = run_dir / "run.json"
    step_path = run_dir / "steps" / "step_001.json"
    stop_path = run_dir / "stop.md"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == "figure-agent.fig-run-journal.v1"
    assert manifest["fixture"] == "runner_demo"
    assert manifest["mode"] == "review"
    assert manifest["goal"] == "close loop"
    assert manifest["final_action"] == fig_driver.ACTION_RUN_CRITIQUE
    assert manifest["final_stop_boundary"] == fig_driver.STOP_HOST_LLM_CRITIQUE
    assert manifest["final_stop_reason"] == "host_boundary"
    assert manifest["started_at"].endswith("Z")
    assert manifest["completed_at"].endswith("Z")
    assert "branch" in manifest
    assert "commit" in manifest
    assert manifest["authoritative"] is False
    assert manifest["replay_allowed"] is False
    assert manifest["commands_are_evidence_only"] is True
    assert manifest["rerun_live_status_first"] is True
    assert manifest["rerun_live_driver_first"] is True
    assert manifest["run_json"] == "run.json"
    assert manifest["steps"] == ["steps/step_001.json"]
    assert manifest["stop_markdown"] == "stop.md"
    snapshot = manifest["evidence_snapshot"]
    assert snapshot["schema"] == "figure-agent.fig-run-evidence-snapshot.v1"
    assert {item["path"] for item in snapshot["items"]} >= {
        "examples/runner_demo/runner_demo.tex",
        "examples/runner_demo/briefing.md",
        "examples/runner_demo/spec.yaml",
    }

    assert json.loads(run_path.read_text(encoding="utf-8")) == payload
    assert json.loads(step_path.read_text(encoding="utf-8")) == payload["steps"][0]
    stop_text = stop_path.read_text(encoding="utf-8")
    assert "non-authoritative evidence" in stop_text
    assert "Recorded safe_command fields are evidence only" in stop_text
    assert "Do not replay commands from this journal" in stop_text
    assert "Required actor: host_llm" in stop_text


def test_main_records_run_journal_when_spec_shape_is_malformed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    example_dir = tmp_path / "examples" / "runner_demo"
    example_dir.mkdir(parents=True)
    (example_dir / "runner_demo.tex").write_text("% source\n", encoding="utf-8")
    (example_dir / "briefing.md").write_text("brief\n", encoding="utf-8")
    (example_dir / "spec.yaml").write_text(
        "name: runner_demo\npanels:\n  - malformed panel entry\n",
        encoding="utf-8",
    )
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_CRITIQUE,
                safe_command="/fig_critique runner_demo",
                stop_boundary=fig_driver.STOP_HOST_LLM_CRITIQUE,
            )
        ],
    )
    runs_root = tmp_path / "fig-run-runs"

    result = fig_run.main(
        [
            "runner_demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--record",
            "--runs-root",
            str(runs_root),
        ],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    manifest_path = Path(payload["journal"]["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["evidence_snapshot"]["schema"] == ("figure-agent.fig-run-evidence-snapshot.v1")
    assert {item["path"] for item in manifest["evidence_snapshot"]["items"]} >= {
        "examples/runner_demo/runner_demo.tex",
        "examples/runner_demo/briefing.md",
        "examples/runner_demo/spec.yaml",
    }


def test_main_plan_only_does_not_record_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            )
        ],
    )
    runs_root = tmp_path / "fig-run-runs"

    result = fig_run.main(
        [
            "runner_demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--runs-root",
            str(runs_root),
        ],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["final_stop_reason"] == "plan_only"
    assert "journal" not in payload
    assert not runs_root.exists()


def test_execute_records_run_journal_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            ),
            _driver_summary(action=fig_driver.ACTION_COMPLETE, safe_command=None),
        ],
    )
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda command, *, repo_root: fig_run.CommandResult(0, "compiled\n", ""),
    )
    runs_root = tmp_path / "fig-run-runs"

    result = fig_run.main(
        [
            "runner_demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--execute",
            "--runs-root",
            str(runs_root),
        ],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["executed_count"] == 1
    run_dir = Path(payload["journal"]["run_dir"])
    assert run_dir.parent == runs_root
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["steps"] == ["steps/step_001.json", "steps/step_002.json"]
    assert (run_dir / "steps" / "step_001.json").is_file()
    assert (run_dir / "steps" / "step_002.json").is_file()
    assert json.loads((run_dir / "run.json").read_text(encoding="utf-8")) == payload


def test_journal_manifest_timestamps_cover_run_not_write_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            ),
            _driver_summary(action=fig_driver.ACTION_COMPLETE, safe_command=None),
        ],
    )
    clock = iter(["run-start", "run-end"])
    monkeypatch.setattr(fig_run, "_utc_now", lambda: next(clock), raising=False)
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda command, *, repo_root: fig_run.CommandResult(0, "compiled\n", ""),
    )
    runs_root = tmp_path / "fig-run-runs"

    result = fig_run.main(
        [
            "runner_demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--execute",
            "--runs-root",
            str(runs_root),
        ],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    run_dir = Path(payload["journal"]["run_dir"])
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["started_at"] == "run-start"
    assert manifest["completed_at"] == "run-end"


def test_execute_without_runs_root_uses_repo_scratch_fig_run_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(action=fig_driver.ACTION_COMPLETE, safe_command=None),
        ],
    )

    result = fig_run.main(
        ["runner_demo", "--mode", "review", "--goal", "close loop", "--execute"],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    run_dir = Path(payload["journal"]["run_dir"])
    assert run_dir.parent == tmp_path / ".scratch" / "fig-run-runs"
    assert (run_dir / "run_manifest.json").is_file()


def test_main_no_record_disables_run_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            )
        ],
    )
    runs_root = tmp_path / "fig-run-runs"

    result = fig_run.main(
        [
            "runner_demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--runs-root",
            str(runs_root),
            "--no-record",
        ],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert "journal" not in payload
    assert not runs_root.exists()


def test_execute_no_record_disables_run_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            ),
            _driver_summary(action=fig_driver.ACTION_COMPLETE, safe_command=None),
        ],
    )
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda command, *, repo_root: fig_run.CommandResult(0, "compiled\n", ""),
    )
    runs_root = tmp_path / "fig-run-runs"

    result = fig_run.main(
        [
            "runner_demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--execute",
            "--runs-root",
            str(runs_root),
            "--no-record",
        ],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["executed_count"] == 1
    assert "journal" not in payload
    assert "journal_error" not in payload
    assert not runs_root.exists()


def test_journal_write_failure_does_not_hide_run_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(action=fig_driver.ACTION_COMPLETE, safe_command=None),
        ],
    )

    def _fail_journal(*args: object, **kwargs: object) -> dict[str, Any]:
        raise OSError("disk full")

    monkeypatch.setattr(fig_run, "write_run_journal", _fail_journal)

    result = fig_run.main(
        ["runner_demo", "--mode", "review", "--goal", "close loop", "--execute"],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["final_stop_reason"] == "complete"
    assert "journal" not in payload
    error = payload["journal_error"]
    assert error["schema"] == "figure-agent.fig-run-journal-error.v1"
    assert error["authoritative"] is False
    assert error["replay_allowed"] is False
    assert error["commands_are_evidence_only"] is True
    assert "disk full" in error["message"]


def test_command_failed_journal_is_non_authoritative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            )
        ],
    )
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda command, *, repo_root: fig_run.CommandResult(7, "", "compile failed"),
    )
    runs_root = tmp_path / "fig-run-runs"

    result = fig_run.main(
        [
            "runner_demo",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--execute",
            "--runs-root",
            str(runs_root),
        ],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["final_stop_reason"] == "command_failed"
    journal = payload["journal"]
    assert journal["authoritative"] is False
    assert journal["replay_allowed"] is False
    assert "command" not in journal
    run_dir = Path(journal["run_dir"])
    stop_text = (run_dir / "stop.md").read_text(encoding="utf-8")
    assert "Do not replay commands from this journal" in stop_text


def test_main_refuses_to_record_journal_for_unsafe_fixture_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_CRITIQUE,
                safe_command="/fig_critique runner_demo",
                stop_boundary=fig_driver.STOP_HOST_LLM_CRITIQUE,
            )
        ],
    )
    runs_root = tmp_path / "fig-run-runs"

    result = fig_run.main(
        [
            "../bad/name with spaces",
            "--mode",
            "review",
            "--goal",
            "close loop",
            "--record",
            "--runs-root",
            str(runs_root),
        ],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert "journal" not in payload
    assert not runs_root.exists()
    error = payload["journal_error"]
    assert error["schema"] == "figure-agent.fig-run-journal-error.v1"
    assert "fixture name must be a single examples/<name> directory name" in error["message"]


def test_write_run_journal_rejects_unsafe_fixture_name_before_writing(
    tmp_path: Path,
) -> None:
    runs_root = tmp_path / "fig-run-runs"

    with pytest.raises(
        ValueError, match="fixture name must be a single examples/<name> directory name"
    ):
        fig_run_records.write_run_journal(
            {
                "schema": "figure-agent.run.v1",
                "fixture": "../bad/name with spaces",
                "mode": "review",
                "goal": "close loop",
                "execute": False,
                "max_steps": 5,
                "executed_count": 0,
                "final_action": fig_driver.ACTION_RUN_CRITIQUE,
                "final_safe_command": "/fig_critique runner_demo",
                "final_stop_boundary": fig_driver.STOP_HOST_LLM_CRITIQUE,
                "final_stop_reason": "host_boundary",
                "steps": [],
            },
            runs_root=runs_root,
            repo_root=tmp_path,
            started_at="run-start",
            completed_at="run-end",
        )

    assert not runs_root.exists()


def test_run_workflow_does_not_write_journal_directly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            )
        ],
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        repo_root=tmp_path,
    )

    assert payload["final_stop_reason"] == "plan_only"
    assert "journal" not in payload
    assert not (tmp_path / ".scratch").exists()


def test_main_emits_json_plan_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            )
        ],
    )

    result = fig_run.main(
        ["runner_demo", "--mode", "review", "--goal", "close loop"],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.run.v1"
    assert payload["execute"] is False
    assert payload["final_stop_reason"] == "plan_only"


def test_main_execute_runs_allowlisted_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_COMPILE,
                safe_command="bash scripts/compile.sh examples/runner_demo/runner_demo.tex",
            ),
            _driver_summary(
                action=fig_driver.ACTION_COMPLETE,
                safe_command=None,
            ),
        ],
    )
    commands: list[str] = []

    def _fake_run(command: str, *, repo_root: Path) -> fig_run.CommandResult:
        commands.append(command)
        return fig_run.CommandResult(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(fig_run, "_run_command", _fake_run)

    result = fig_run.main(
        ["runner_demo", "--mode", "review", "--goal", "close loop", "--execute"],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert commands == ["bash scripts/compile.sh examples/runner_demo/runner_demo.tex"]
    assert payload["execute"] is True
    assert payload["executed_count"] == 1
    assert payload["final_action"] == fig_driver.ACTION_COMPLETE
    assert payload["final_stop_reason"] == "complete"


def test_main_rejects_invalid_max_steps(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    result = fig_run.main(
        ["runner_demo", "--mode", "review", "--goal", "close loop", "--max-steps", "0"],
        repo_root=tmp_path,
    )

    captured = capsys.readouterr()
    assert result == 2
    assert "max_steps must be >= 1" in captured.err


def test_main_rejects_unsafe_fixture_name_cleanly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "examples").mkdir()

    result = fig_run.main(
        ["../outside", "--mode", "review", "--goal", "close loop"],
        repo_root=tmp_path,
    )

    captured = capsys.readouterr()
    assert result == 2
    assert "fixture name must be a single examples/<name> directory name" in captured.err
    assert captured.out == ""


def test_run_workflow_rejects_final_mode_as_driver_only(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="final mode is driver-only"):
        fig_run.run_workflow(
            "runner_demo",
            mode="final",
            goal="final readiness",
            execute=True,
            repo_root=tmp_path,
        )


def test_run_command_tolerates_nonutf8_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # The bounded runner executes the allowlisted compile action (lualatex via
    # compile.sh), whose stdout/stderr routinely carries non-UTF8 bytes (font
    # internals, file paths). text=True without errors= would raise
    # UnicodeDecodeError on .stdout access before _run_command returns.
    real_run = subprocess.run
    child = [
        sys.executable,
        "-c",
        "import os,sys; os.write(1, b'\\xff\\xfe font'); sys.exit(0)",
    ]

    def _run(_args, *_pos, **kwargs):
        return real_run(child, **kwargs)

    monkeypatch.setattr(subprocess, "run", _run)

    result = fig_run._run_command("bash whatever.sh", repo_root=tmp_path)

    assert result.returncode == 0
    assert "�" in result.stdout
