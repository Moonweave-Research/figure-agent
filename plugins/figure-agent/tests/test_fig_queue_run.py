from __future__ import annotations

import json
import os
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
        "blocked": 1,
        "unattempted_executable": 0,
    }
    assert [run["fixture"] for run in payload["runs"]] == ["alpha", "beta"]
    assert all(run["would_execute"] is True for run in payload["runs"])
    assert all(run["executed"] is False for run in payload["runs"])
    assert calls == []


def test_execute_delegates_each_planned_fixture_to_fig_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fig_queue_run.fig_queue, "build_queue", lambda **kwargs: _queue())
    calls: list[tuple[str, bool, int]] = []

    def fake_run_workflow(
        name: str,
        *,
        mode: str,
        goal: str,
        execute: bool,
        max_steps: int,
        repo_root: Path,
    ) -> dict[str, Any]:
        calls.append((name, execute, max_steps))
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

    assert calls == [("alpha", True, 4), ("beta", True, 4)]
    assert payload["summary"]["attempted"] == 2
    assert payload["summary"]["executed_commands"] == 2
    assert payload["summary"]["failed"] == 0
    assert [run["result"]["fixture"] for run in payload["runs"]] == ["alpha", "beta"]


def test_execute_respects_max_fixtures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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


def test_queue_run_filter_surface_matches_fig_queue() -> None:
    assert fig_queue_run.QUEUE_FILTER_KEYS == fig_queue._FILTER_KEYS
