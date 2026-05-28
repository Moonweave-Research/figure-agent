from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_driver  # noqa: E402
import fig_run  # noqa: E402


def _driver_summary(
    *,
    action: str,
    safe_command: str | None,
    stop_boundary: str | None = None,
    reason: str = "driver reason",
) -> dict[str, Any]:
    return {
        "schema": fig_driver.SCHEMA,
        "fixture": "runner_demo",
        "mode": "review",
        "goal": "close loop",
        "status": {"render_state": "STALE"},
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
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda command, *, repo_root: commands.append(command),
    )

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
    assert payload["final_stop_reason"] == "host_boundary"
    assert payload["steps"][0]["would_execute"] is False


def test_execute_stops_at_non_allowlisted_shell_action(
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
                    "uv run python3 scripts/fig_loop.py runner_demo "
                    "--goal 'close loop' --json"
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
                    "uv run python3 scripts/fig_loop.py runner_demo "
                    "--goal 'close loop' --json"
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
        "run_fig_loop",
    ]
    assert payload["executed_count"] == 2
    assert payload["final_action"] == fig_driver.ACTION_HUMAN_GATE_STOP
    assert payload["final_stop_reason"] == "not_executable_action"
    assert payload["steps"][1]["action"] == fig_driver.ACTION_RUN_FIG_LOOP
    assert payload["steps"][1]["executed"] is True


def test_fig_loop_failure_stops_without_requery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = _install_driver_sequence(
        monkeypatch,
        [
            _driver_summary(
                action=fig_driver.ACTION_RUN_FIG_LOOP,
                safe_command=(
                    "uv run python3 scripts/fig_loop.py runner_demo "
                    "--goal 'close loop' --json"
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
                    "uv run python3 scripts/fig_loop.py runner_demo "
                    "--goal 'close loop' --json"
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


def test_max_steps_exceeded_for_repeated_executable_action(
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
    monkeypatch.setattr(
        fig_run,
        "_run_command",
        lambda command, *, repo_root: fig_run.CommandResult(0, "", ""),
    )

    payload = fig_run.run_workflow(
        "runner_demo",
        mode="review",
        goal="close loop",
        execute=True,
        max_steps=2,
        repo_root=tmp_path,
    )

    assert payload["executed_count"] == 2
    assert payload["final_stop_reason"] == "max_steps_exceeded"
    assert len(payload["steps"]) == 2


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


def test_main_rejects_invalid_max_steps(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = fig_run.main(
        ["runner_demo", "--mode", "review", "--goal", "close loop", "--max-steps", "0"],
        repo_root=tmp_path,
    )

    captured = capsys.readouterr()
    assert result == 2
    assert "max_steps must be >= 1" in captured.err
