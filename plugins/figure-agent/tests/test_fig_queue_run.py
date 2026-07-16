from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_queue  # noqa: E402
import fig_queue_run  # noqa: E402


def _queue() -> dict[str, Any]:
    return {
        "schema": "figure-agent.fixture-driver-queue.v1",
        "mode": "review",
        "goal": "triage",
        "filters": {"required_actor": "workflow_agent"},
        "unfiltered_total": 3,
        "rows": [],
        "summary": {"total": 3, "errors": 0},
        "bottleneck_report": {
            "schema": "figure-agent.queue-bottleneck-report.v1",
            "total_rows": 3,
        },
        "command_plan": {
            "schema": "figure-agent.fixture-command-plan.v1",
            "executable_count": 2,
            "blocked_count": 1,
            "complete_count": 1,
            "executable": [
                {
                    "fixture": "alpha",
                    "action": "run_fig_loop",
                    "safe_command": "uv run python3 scripts/fig_loop.py alpha --goal triage --json",
                    "required_actor": "workflow_agent",
                },
                {
                    "fixture": "beta",
                    "action": "run_compile",
                    "safe_command": "bash scripts/compile.sh examples/beta/beta.tex",
                    "required_actor": "workflow_agent",
                },
            ],
            "blocked": [
                {
                    "fixture": "gamma",
                    "action": "run_export",
                    "required_actor": "workflow_agent",
                    "blocking_source": "closeout_required",
                    "stop_boundary": "closeout_required",
                    "reason": "stop_boundary:closeout_required",
                }
            ],
            "complete": [
                {
                    "fixture": "delta",
                    "action": "complete",
                    "required_actor": "workflow_agent",
                    "reason": "mode_scoped_complete",
                }
            ],
        },
    }


def test_plan_only_reports_planned_runs_without_executing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())
    calls: list[str] = []

    def fake_run_workflow(*args, **kwargs):
        calls.append("called")
        return {}

    monkeypatch.setattr(fig_queue_run.fig_run, "run_workflow", fake_run_workflow)

    payload = fig_queue_run.run_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        execute=False,
        max_steps=3,
        max_fixtures=10,
        fixtures=None,
        filters={"required_actor": "workflow_agent"},
    )

    assert payload["schema"] == "figure-agent.queue-run.v1"
    assert payload["execute"] is False
    assert payload["queue"]["bottleneck_report"]["schema"] == (
        "figure-agent.queue-bottleneck-report.v1"
    )
    assert payload["summary"] == {
        "planned_executable": 2,
        "planned_blocked": 1,
        "planned_complete": 1,
        "attempted": 2,
        "executed_commands": 0,
        "failed": 0,
        "stale": 0,
        "busy": 0,
        "admission_invalid": 0,
        "admission_pending": 0,
        "blocked": 1,
        "unattempted_executable": 0,
    }
    assert [run["fixture"] for run in payload["runs"]] == ["alpha", "beta"]
    assert all(run["would_execute"] is True for run in payload["runs"])
    assert all(run["executed"] is False for run in payload["runs"])
    assert calls == []


def test_plan_only_run_preserves_command_plan_evidence_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queue = _queue()
    contract = {
        "required_actor": "workflow_agent",
        "evidence_refs": ["review/closed-loop/attempt-a/state-005.json"],
        "allowed_scope": ["bounded repair packet"],
        "forbidden_scope": ["accepted artifact mutation"],
        "publication_acceptance": "not_claimed",
        "decision_boundary": {
            "kind": "deterministic_plugin_gate",
            "authority": "plugin",
        },
    }
    queue["command_plan"]["executable"][0].update(contract)
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: queue)

    payload = fig_queue_run.run_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        execute=False,
        max_steps=3,
        max_fixtures=1,
        fixtures=None,
        filters={},
    )

    planned = payload["runs"][0]
    for key, value in contract.items():
        assert planned[key] == value


def test_execute_delegates_each_planned_fixture_to_fig_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("alpha", "beta"):
        (tmp_path / "examples" / name).mkdir(parents=True)
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())
    calls: list[tuple[str, bool, int, str, str]] = []

    def fake_run_workflow(
        name: str,
        *,
        mode: str,
        goal: str,
        execute: bool,
        max_steps: int,
        repo_root: Path,
        expected_first_action: str,
        expected_first_safe_command: str,
    ) -> dict[str, Any]:
        calls.append(
            (
                name,
                execute,
                max_steps,
                expected_first_action,
                expected_first_safe_command,
            )
        )
        return {
            "schema": "figure-agent.run.v1",
            "fixture": name,
            "execute": execute,
            "executed_count": 1,
            "final_stop_reason": "complete",
        }

    monkeypatch.setattr(fig_queue_run.fig_run, "run_workflow", fake_run_workflow)

    payload = fig_queue_run.run_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        execute=True,
        max_steps=4,
        max_fixtures=10,
        fixtures=None,
        filters={},
    )

    assert calls == [
        (
            "alpha",
            True,
            4,
            "run_fig_loop",
            "uv run python3 scripts/fig_loop.py alpha --goal triage --json",
        ),
        (
            "beta",
            True,
            4,
            "run_compile",
            "bash scripts/compile.sh examples/beta/beta.tex",
        ),
    ]
    assert payload["summary"]["attempted"] == 2
    assert payload["summary"]["executed_commands"] == 2
    assert payload["summary"]["failed"] == 0
    assert payload["summary"]["stale"] == 0
    assert [run["result"]["fixture"] for run in payload["runs"]] == ["alpha", "beta"]


def test_execute_counts_stale_plan_separately_and_continues_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("alpha", "beta"):
        (tmp_path / "examples" / name).mkdir(parents=True)
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())
    calls: list[str] = []

    def fake_run_workflow(name: str, **kwargs: Any) -> dict[str, Any]:
        calls.append(name)
        return {
            "schema": "figure-agent.run.v1",
            "fixture": name,
            "executed_count": 0 if name == "alpha" else 1,
            "final_stop_reason": (
                fig_queue_run.fig_run.STOP_STALE_PLAN
                if name == "alpha"
                else fig_queue_run.fig_run.STOP_COMPLETE
            ),
        }

    monkeypatch.setattr(fig_queue_run.fig_run, "run_workflow", fake_run_workflow)

    payload = fig_queue_run.run_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        execute=True,
        max_steps=4,
        max_fixtures=10,
        fixtures=None,
        filters={},
    )

    assert calls == ["alpha", "beta"]
    assert payload["summary"]["failed"] == 0
    assert payload["summary"]["stale"] == 1
    assert payload["summary"]["executed_commands"] == 1


def test_main_returns_one_for_stale_plan_and_preserves_failure_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in ("alpha", "beta"):
        (tmp_path / "examples" / name).mkdir(parents=True)
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())

    def fake_run_workflow(name: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "schema": "figure-agent.run.v1",
            "fixture": name,
            "executed_count": 0,
            "final_stop_reason": (
                fig_queue_run.fig_run.STOP_STALE_PLAN
                if name == "alpha"
                else fig_queue_run.fig_run.STOP_COMPLETE
            ),
        }

    monkeypatch.setattr(fig_queue_run.fig_run, "run_workflow", fake_run_workflow)

    assert fig_queue_run.main(
        ["--mode", "review", "--goal", "triage", "--execute"], repo_root=tmp_path
    ) == 1

    payload = json.loads(capsys.readouterr().out)
    assert [run["fixture"] for run in payload["runs"]] == ["alpha", "beta"]
    assert payload["summary"]["failed"] == 0
    assert payload["summary"]["stale"] == 1


def test_main_returns_one_for_executed_delegated_command_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in ("alpha", "beta"):
        (tmp_path / "examples" / name).mkdir(parents=True)
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())

    def fake_run_workflow(name: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "schema": "figure-agent.run.v1",
            "fixture": name,
            "executed_count": 1,
            "final_stop_reason": (
                fig_queue_run.fig_run.STOP_COMMAND_FAILED if name == "alpha" else "complete"
            ),
        }

    monkeypatch.setattr(fig_queue_run.fig_run, "run_workflow", fake_run_workflow)

    assert fig_queue_run.main(
        ["--mode", "review", "--goal", "triage", "--execute"], repo_root=tmp_path
    ) == 1

    payload = json.loads(capsys.readouterr().out)
    assert [run["fixture"] for run in payload["runs"]] == ["alpha", "beta"]
    assert payload["summary"]["failed"] == 1


@pytest.mark.parametrize(
    ("stop_reason", "summary_key"),
    (
        (fig_queue_run.fig_run.STOP_ADMISSION_BUSY, "busy"),
        (fig_queue_run.fig_run.STOP_ADMISSION_INVALID, "admission_invalid"),
    ),
)
def test_execute_counts_admission_stops_and_continues_batch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stop_reason: str,
    summary_key: str,
) -> None:
    for name in ("alpha", "beta"):
        (tmp_path / "examples" / name).mkdir(parents=True)
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())
    calls: list[str] = []

    def fake_run_workflow(name: str, **kwargs: Any) -> dict[str, Any]:
        calls.append(name)
        return {
            "schema": "figure-agent.run.v1",
            "fixture": name,
            "executed_count": 0 if name == "alpha" else 1,
            "final_stop_reason": (
                stop_reason
                if name == "alpha"
                else fig_queue_run.fig_run.STOP_COMPLETE
            ),
        }

    monkeypatch.setattr(fig_queue_run.fig_run, "run_workflow", fake_run_workflow)

    payload = fig_queue_run.run_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        execute=True,
        max_steps=4,
        max_fixtures=10,
        fixtures=None,
        filters={},
    )

    assert calls == ["alpha", "beta"]
    assert payload["summary"][summary_key] == 1
    assert payload["summary"]["executed_commands"] == 1


@pytest.mark.parametrize(
    "stop_reason",
    (
        fig_queue_run.fig_run.STOP_ADMISSION_BUSY,
        fig_queue_run.fig_run.STOP_ADMISSION_INVALID,
    ),
)
def test_main_returns_one_for_admission_stop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stop_reason: str,
) -> None:
    for name in ("alpha", "beta"):
        (tmp_path / "examples" / name).mkdir(parents=True)
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())
    monkeypatch.setattr(
        fig_queue_run.fig_run,
        "run_workflow",
        lambda name, **kwargs: {
            "schema": "figure-agent.run.v1",
            "fixture": name,
            "executed_count": 0,
            "final_stop_reason": stop_reason,
        },
    )

    assert fig_queue_run.main(
        ["--mode", "review", "--goal", "triage", "--execute"], repo_root=tmp_path
    ) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["failed"] == 0


def test_deprecated_admission_pending_summary_stays_zero_and_does_not_fail_batch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for name in ("alpha", "beta"):
        (tmp_path / "examples" / name).mkdir(parents=True)
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())
    monkeypatch.setattr(
        fig_queue_run.fig_run,
        "run_workflow",
        lambda name, **kwargs: {
            "schema": "figure-agent.run.v1",
            "fixture": name,
            "executed_count": 0,
            "final_stop_reason": (
                fig_queue_run.fig_run.STOP_RUN_FIG_LOOP_ADMISSION_PENDING
            ),
        },
    )

    assert fig_queue_run.main(
        ["--mode", "review", "--goal", "triage", "--execute"], repo_root=tmp_path
    ) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["admission_pending"] == 0
    assert payload["summary"]["failed"] == 0


def test_workspace_diagnostic_exit_two_precedes_nested_admission_busy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = {
        "schema": fig_queue_run.SCHEMA,
        "queue": {
            "workspace_diagnostic": {
                "schema": fig_queue.WORKSPACE_DIAGNOSTIC_SCHEMA,
                "state": "fixture_symlink",
                "workspace_root": str(tmp_path),
                "missing": [],
                "message": "unsafe workspace",
            }
        },
        "runs": [
            {
                "fixture": "alpha",
                "result": {
                    "final_stop_reason": fig_queue_run.fig_run.STOP_ADMISSION_BUSY
                },
            }
        ],
    }
    monkeypatch.setattr(fig_queue_run, "run_queue", lambda **kwargs: payload)
    monkeypatch.setattr(fig_queue_run.fig_queue, "_print_workspace_diagnostic", lambda queue: None)
    monkeypatch.setattr(
        fig_queue_run.fig_queue,
        "workspace_diagnostic_exit_code",
        lambda queue: 2,
    )

    assert fig_queue_run.main(
        ["--mode", "review", "--goal", "triage", "--execute"], repo_root=tmp_path
    ) == 2
    assert json.loads(capsys.readouterr().out)["runs"][0]["fixture"] == "alpha"


@pytest.mark.parametrize(
    "stop_reason",
    (
        "complete",
        "host_boundary",
        "repeated_executable_action",
        "max_steps_exceeded",
        "not_executable_action",
    ),
)
def test_main_keeps_nonfailure_execute_stop_reasons_at_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stop_reason: str,
) -> None:
    for name in ("alpha", "beta"):
        (tmp_path / "examples" / name).mkdir(parents=True)
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())
    monkeypatch.setattr(
        fig_queue_run.fig_run,
        "run_workflow",
        lambda name, **kwargs: {
            "schema": "figure-agent.run.v1",
            "fixture": name,
            "executed_count": 0,
            "final_stop_reason": stop_reason,
        },
    )

    assert fig_queue_run.main(
        ["--mode", "review", "--goal", "triage", "--execute"], repo_root=tmp_path
    ) == 0
    assert json.loads(capsys.readouterr().out)["summary"]["failed"] == 0


def test_execute_respects_max_fixtures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "examples" / "alpha").mkdir(parents=True)
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())
    calls: list[str] = []

    def fake_run_workflow(name: str, **kwargs) -> dict[str, Any]:
        calls.append(name)
        return {
            "schema": "figure-agent.run.v1",
            "fixture": name,
            "executed_count": 1,
            "final_stop_reason": "complete",
        }

    monkeypatch.setattr(fig_queue_run.fig_run, "run_workflow", fake_run_workflow)

    payload = fig_queue_run.run_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        execute=True,
        max_steps=2,
        max_fixtures=1,
        fixtures=None,
        filters={},
    )

    assert calls == ["alpha"]
    assert [run["fixture"] for run in payload["runs"]] == ["alpha"]
    assert payload["summary"]["attempted"] == 1
    assert payload["summary"]["planned_executable"] == 2
    assert payload["summary"]["unattempted_executable"] == 1


def test_execute_rejects_symlink_fixture_before_delegating_to_fig_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    examples = tmp_path / "examples"
    examples.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    (external / "spec.yaml").write_text("name: demo\n", encoding="utf-8")
    (examples / "demo").symlink_to(external, target_is_directory=True)
    queue = _queue()
    queue["command_plan"]["executable"] = [
        {
            "fixture": "demo",
            "action": "run_compile",
            "safe_command": "fig-agent compile demo",
            "required_actor": "workflow_agent",
        }
    ]
    queue["command_plan"]["executable_count"] = 1
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **_kwargs: queue)
    monkeypatch.setattr(
        fig_queue_run.fig_run,
        "run_workflow",
        lambda *_args, **_kwargs: pytest.fail("symlink fixture reached fig_run"),
    )

    payload = fig_queue_run.run_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        execute=True,
        max_steps=2,
        max_fixtures=1,
        fixtures=None,
        filters={},
    )

    assert payload["runs"] == [
        {
            "fixture": "demo",
            "action": "run_compile",
            "safe_command": "fig-agent compile demo",
            "would_execute": False,
            "executed": False,
            "result": None,
            "required_actor": "workflow_agent",
            "stop_reason": "fixture_symlink",
        }
    ]


def test_execute_rejects_symlinked_examples_workspace_before_fig_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    external_examples = tmp_path / "external-examples"
    fixture = external_examples / "demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: demo\n", encoding="utf-8")
    (tmp_path / "examples").symlink_to(external_examples, target_is_directory=True)
    monkeypatch.setattr(
        fig_queue_run.fig_run,
        "run_workflow",
        lambda *_args, **_kwargs: pytest.fail("symlinked examples reached fig_run"),
    )

    payload = fig_queue_run.run_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        execute=True,
        max_fixtures=1,
        fixtures=None,
        filters={},
    )

    assert payload["runs"] == []
    assert payload["queue"]["workspace_diagnostic"]["state"] == "fixture_symlink"


def test_main_prints_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())

    assert fig_queue_run.main(
        [
            "--mode",
            "review",
            "--goal",
            "triage",
            "--actor",
            "workflow_agent",
            "--max-fixtures",
            "1",
        ],
        repo_root=tmp_path,
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.queue-run.v1"
    assert payload["execute"] is False
    assert payload["filters"] == {"required_actor": "workflow_agent"}
    assert [run["fixture"] for run in payload["runs"]] == ["alpha"]




def test_main_warns_when_queue_workspace_has_no_examples(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert fig_queue_run.main(
        ["--mode", "review", "--goal", "triage", "--dry-run"],
        repo_root=tmp_path,
    ) == 2

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["summary"]["attempted"] == 0
    assert payload["queue"]["summary"]["total"] == 0
    assert payload["queue"]["workspace_diagnostic"]["state"] == "missing_examples"
    assert payload["queue"]["workspace_diagnostic"]["workspace_root"] == str(tmp_path)
    assert "implicit queue discovery found no examples/ directory" in captured.err


def test_main_keeps_empty_examples_workspace_as_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "examples").mkdir()

    assert fig_queue_run.main(
        ["--mode", "review", "--goal", "triage", "--dry-run"], repo_root=tmp_path
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["attempted"] == 0
    assert "workspace_diagnostic" not in payload["queue"]


def test_main_accepts_json_and_dry_run_flags_as_plan_only_noops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())

    assert fig_queue_run.main(
        [
            "--mode",
            "review",
            "--goal",
            "triage",
            "--actor",
            "workflow_agent",
            "--json",
            "--dry-run",
        ],
        repo_root=tmp_path,
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.queue-run.v1"
    assert payload["execute"] is False
    assert [run["fixture"] for run in payload["runs"]] == ["alpha", "beta"]


def test_main_returns_nonzero_for_implicit_missing_examples_workspace(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    queue = _queue()
    queue["workspace_diagnostic"] = {
        "schema": "figure-agent.queue-workspace-diagnostic.v1",
        "state": "missing_examples",
        "workspace_root": "/repo-root",
        "missing": ["examples"],
        "message": "implicit queue discovery found no examples/ directory",
    }

    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: queue)

    assert fig_queue_run.main(["--mode", "review", "--goal", "triage"]) == 2

    captured = capsys.readouterr()
    assert "implicit queue discovery found no examples/ directory" in captured.err
    payload = json.loads(captured.out)
    assert payload["queue"]["workspace_diagnostic"]["state"] == "missing_examples"


def test_main_prioritizes_workspace_diagnostic_over_delegated_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in ("alpha", "beta"):
        (tmp_path / "examples" / name).mkdir(parents=True)
    queue = _queue()
    queue["workspace_diagnostic"] = {
        "schema": fig_queue.WORKSPACE_DIAGNOSTIC_SCHEMA,
        "state": "missing_examples",
        "workspace_root": str(tmp_path),
        "missing": ["examples"],
        "message": "synthetic missing examples diagnostic",
    }
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: queue)
    monkeypatch.setattr(
        fig_queue_run.fig_run,
        "run_workflow",
        lambda name, **kwargs: {
            "fixture": name,
            "executed_count": 1,
            "final_stop_reason": fig_queue_run.fig_run.STOP_COMMAND_FAILED,
        },
    )

    assert fig_queue_run.main(
        ["--mode", "review", "--goal", "triage", "--execute"], repo_root=tmp_path
    ) == 2
    assert json.loads(capsys.readouterr().out)["summary"]["failed"] == 2


def test_main_rejects_execute_with_dry_run_without_running(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())
    calls: list[str] = []

    def fake_run_workflow(*args, **kwargs):
        calls.append("called")
        return {}

    monkeypatch.setattr(fig_queue_run.fig_run, "run_workflow", fake_run_workflow)

    assert fig_queue_run.main(
        [
            "--mode",
            "review",
            "--goal",
            "triage",
            "--actor",
            "workflow_agent",
            "--execute",
            "--dry-run",
        ],
        repo_root=tmp_path,
    ) == 2

    captured = capsys.readouterr()
    assert "choose either --execute or --dry-run" in captured.err
    assert calls == []


def test_main_accepts_format_json_as_output_compatibility_noop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())

    assert fig_queue_run.main(
        [
            "--mode",
            "review",
            "--goal",
            "triage",
            "--actor",
            "workflow_agent",
            "--format",
            "json",
        ],
        repo_root=tmp_path,
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.queue-run.v1"
    assert payload["execute"] is False
    assert [run["fixture"] for run in payload["runs"]] == ["alpha", "beta"]


def test_main_passes_svg_polish_filters_to_queue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    seen_filters: dict[str, str | None] = {}

    def fake_build_queue(**kwargs):
        nonlocal seen_filters
        seen_filters = dict(kwargs["filters"])
        queue = _queue()
        queue["filters"] = {
            key: value for key, value in seen_filters.items() if value is not None
        }
        return queue

    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", fake_build_queue)

    assert fig_queue_run.main(
        [
            "--mode",
            "polish",
            "--goal",
            "svg readiness",
            "--can-start-svg-polish",
            "true",
            "--svg-polish-blocking-source",
            "driver_prerequisite",
            "--svg-polish-gate-state",
            "blocked",
            "--svg-polish-next-action",
            "run_fig_critique",
            "--svg-polish-recommended-path",
            "continue_tikz",
        ],
        repo_root=tmp_path,
    ) == 0

    assert seen_filters == {
        "required_actor": None,
        "action": None,
        "stop_boundary": None,
        "first_blocker": None,
        "blocking_source": None,
        "svg_polish_gate_state": "blocked",
        "can_start_svg_polish": "true",
        "svg_polish_recommended_path": "continue_tikz",
        "svg_polish_next_action": "run_fig_critique",
        "svg_polish_blocking_sources": "driver_prerequisite",
        "polish_blocker_reason": None,
        "svg_polish_evidence_state": None,
        "style_benchmark_pack_state": None,
        "style_benchmark_comparison_state": None,
        "spine_evidence_state": None,
        "tex_assertions_state": None,
        "convention_receipt_state": None,
        "physics_grounding_status": None,
    }
    payload = json.loads(capsys.readouterr().out)
    assert payload["filters"] == {
        "svg_polish_gate_state": "blocked",
        "can_start_svg_polish": "true",
        "svg_polish_recommended_path": "continue_tikz",
        "svg_polish_next_action": "run_fig_critique",
        "svg_polish_blocking_sources": "driver_prerequisite",
    }


def test_main_passes_spine_evidence_filters_to_queue(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    seen_filters: dict[str, str | None] = {}

    def fake_build_queue(**kwargs):
        nonlocal seen_filters
        seen_filters = dict(kwargs["filters"])
        queue = _queue()
        queue["filters"] = {
            key: value for key, value in seen_filters.items() if value is not None
        }
        return queue

    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", fake_build_queue)

    assert fig_queue_run.main(
        [
            "--mode",
            "review",
            "--goal",
            "spine evidence readiness",
            "--spine-evidence-state",
            "present",
            "--tex-assertions-state",
            "passed",
            "--convention-receipt-state",
            "present",
            "--physics-grounding-status",
            "grounded",
        ],
        repo_root=tmp_path,
    ) == 0

    assert seen_filters["spine_evidence_state"] == "present"
    assert seen_filters["tex_assertions_state"] == "passed"
    assert seen_filters["convention_receipt_state"] == "present"
    assert seen_filters["physics_grounding_status"] == "grounded"
    payload = json.loads(capsys.readouterr().out)
    assert payload["filters"] == {
        "spine_evidence_state": "present",
        "tex_assertions_state": "passed",
        "convention_receipt_state": "present",
        "physics_grounding_status": "grounded",
    }


def test_wrapper_queue_run_from_parent_uses_plugin_examples() -> None:
    env = os.environ.copy()
    env.pop("FIGURE_AGENT_WORKSPACE", None)
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("FIGURE_AGENT_PLUGIN_ROOT", None)
    env.pop("CLAUDE_PLUGIN_ROOT", None)

    result = subprocess.run(
        [
            str(Path("figure-agent") / "bin" / "fig-agent"),
            "queue-run",
            "--mode",
            "review",
            "--goal",
            "cwd trap regression",
            "--dry-run",
            "--json",
            "--max-fixtures",
            "1",
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["queue"]["unfiltered_total"] > 0
    assert payload["queue"]["summary"]["total"] > 0


def test_public_wrapper_queue_run_returns_one_after_synthetic_delegated_failure(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / "broken_compile"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        "name: broken_compile\npanels: []\n", encoding="utf-8"
    )
    (fixture / "briefing.md").write_text("brief\n", encoding="utf-8")
    (fixture / "broken_compile.tex").write_text(
        "% intentionally incomplete\n", encoding="utf-8"
    )
    tool_dir = tmp_path / "tools"
    tool_dir.mkdir()
    compiler_marker = tmp_path / "compiler-invoked.txt"
    compiler = tool_dir / "deterministic-compiler-failure"
    compiler.write_text(
        "#!/bin/sh\n"
        f"printf 'invoked:%s\\n' \"$*\" > {shlex.quote(str(compiler_marker))}\n"
        "exit 73\n",
        encoding="utf-8",
    )
    compiler.chmod(0o755)
    pdf_helper_markers = {
        helper: tmp_path / f"{helper}-invoked.txt" for helper in ("pdftocairo", "magick")
    }
    for helper, marker in pdf_helper_markers.items():
        shim = tool_dir / helper
        shim.write_text(
            "#!/bin/sh\n"
            f"printf 'forbidden helper invoked\\n' > {shlex.quote(str(marker))}\n"
            "exit 91\n",
            encoding="utf-8",
        )
        shim.chmod(0o755)
    env = os.environ.copy()
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(Path(__file__).resolve().parents[1])
    env["LATEX_ENGINE"] = str(compiler)
    env["UV_PROJECT_ENVIRONMENT"] = str(tmp_path / "uv-project-environment")
    env["PATH"] = os.pathsep.join((str(tool_dir), env["PATH"]))
    repo_root = Path(__file__).resolve().parents[3]
    source_status_before = subprocess.run(
        ["git", "status", "--short", "--", "plugins/figure-agent"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    result = subprocess.run(
        [
            str(Path(__file__).resolve().parents[1] / "bin" / "fig-agent"),
            "queue-run",
            "broken_compile",
            "--mode",
            "review",
            "--goal",
            "synthetic delegated failure",
            "--execute",
            "--json",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.queue-run.v1"
    assert [run["fixture"] for run in payload["runs"]] == ["broken_compile"]
    assert payload["runs"][0]["result"]["final_stop_reason"] == "command_failed"
    assert payload["runs"][0]["result"]["steps"][0]["returncode"] == 73
    assert payload["summary"]["failed"] == 1
    assert compiler_marker.read_text(encoding="utf-8").startswith("invoked:")
    assert all(not marker.exists() for marker in pdf_helper_markers.values())
    assert Path(env["UV_PROJECT_ENVIRONMENT"]).is_relative_to(tmp_path)
    source_status_after = subprocess.run(
        ["git", "status", "--short", "--", "plugins/figure-agent"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert source_status_after == source_status_before


@pytest.mark.parametrize(
    ("command", "expected_returncode"),
    (
        (("drive", "demo", "--mode", "review", "--goal", "triage", "--dry-run", "--json"), 2),
        (("queue", "demo", "--mode", "review", "--goal", "triage", "--json"), 0),
        (("queue-run", "demo", "--mode", "review", "--goal", "triage", "--execute", "--json"), 0),
    ),
)
def test_public_wrapper_rejects_workspace_symlink_fixture_without_external_mutation(
    tmp_path: Path, command: tuple[str, ...], expected_returncode: int
) -> None:
    workspace = tmp_path / "workspace"
    examples = workspace / "examples"
    examples.mkdir(parents=True)
    external = tmp_path / "external"
    external.mkdir()
    spec = external / "spec.yaml"
    spec.write_text("name: demo\n", encoding="utf-8")
    (examples / "demo").symlink_to(external, target_is_directory=True)
    before = {path.relative_to(external): path.read_bytes() for path in external.iterdir()}
    env = os.environ.copy()
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(Path(__file__).resolve().parents[1])

    result = subprocess.run(
        [str(Path(__file__).resolve().parents[1] / "bin" / "fig-agent"), *command],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == expected_returncode, result.stderr + result.stdout
    assert {path.relative_to(external): path.read_bytes() for path in external.iterdir()} == before
    if command[0] == "drive":
        assert "fixture_symlink" in result.stderr
        assert result.stdout == ""
    else:
        payload = json.loads(result.stdout)
        queue_payload = payload["queue"] if command[0] == "queue-run" else payload
        assert queue_payload["summary"]["errors"] == 1


@pytest.mark.parametrize(
    "target",
    ("external", "../external", "missing-target"),
)
def test_queue_run_fixture_symlink_rows_do_not_delegate_or_mutate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    examples = tmp_path / "examples"
    examples.mkdir()
    external = tmp_path / "external"
    external.mkdir()
    marker = external / "marker.txt"
    marker.write_text("unchanged\n", encoding="utf-8")
    (examples / "demo").symlink_to(target, target_is_directory=True)
    queue = _queue()
    queue["command_plan"]["executable"] = [
        {
            "fixture": "demo",
            "action": "run_compile",
            "safe_command": "fig-agent compile demo",
            "required_actor": "workflow_agent",
        }
    ]
    queue["command_plan"]["executable_count"] = 1
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **_kwargs: queue)
    monkeypatch.setattr(
        fig_queue_run.fig_run,
        "run_workflow",
        lambda *_args, **_kwargs: pytest.fail("symlink fixture reached fig_run"),
    )

    payload = fig_queue_run.run_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        execute=True,
        max_fixtures=1,
        fixtures=None,
        filters={},
    )

    assert payload["runs"][0]["stop_reason"] == "fixture_symlink"
    assert marker.read_text(encoding="utf-8") == "unchanged\n"


@pytest.mark.parametrize(
    "command",
    (
        ("queue", "--mode", "review", "--goal", "triage", "--json"),
        ("queue-run", "--mode", "review", "--goal", "triage", "--execute", "--json"),
    ),
)
def test_public_wrapper_rejects_symlinked_examples_workspace_without_external_mutation(
    tmp_path: Path, command: tuple[str, ...]
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    external_examples = tmp_path / "external-examples"
    fixture = external_examples / "demo"
    fixture.mkdir(parents=True)
    spec = fixture / "spec.yaml"
    spec.write_text("name: demo\n", encoding="utf-8")
    (workspace / "examples").symlink_to(external_examples, target_is_directory=True)
    before = {path.relative_to(external_examples): path.read_bytes() for path in fixture.iterdir()}
    env = os.environ.copy()
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(Path(__file__).resolve().parents[1])

    result = subprocess.run(
        [str(Path(__file__).resolve().parents[1] / "bin" / "fig-agent"), *command],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2, result.stderr + result.stdout
    after = {path.relative_to(external_examples): path.read_bytes() for path in fixture.iterdir()}
    assert after == before
    payload = json.loads(result.stdout)
    queue_payload = payload["queue"] if command[0] == "queue-run" else payload
    assert queue_payload["summary"]["total"] == 0
    assert queue_payload["summary"]["errors"] == 0
    assert queue_payload["workspace_diagnostic"] == {
        "schema": fig_queue.WORKSPACE_DIAGNOSTIC_SCHEMA,
        "state": "fixture_symlink",
        "workspace_root": str(workspace),
        "missing": [],
        "message": "implicit queue discovery refused symlinked examples/ directory",
    }
    assert "symlinked examples/ directory" in result.stderr


def test_queue_run_filter_surface_matches_fig_queue() -> None:
    assert fig_queue_run.QUEUE_FILTER_KEYS == fig_queue._FILTER_KEYS
