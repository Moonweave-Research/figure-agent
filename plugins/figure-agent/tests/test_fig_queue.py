from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_queue  # noqa: E402


def _summary(
    name: str,
    *,
    action: str,
    stop_boundary: str | None,
    first_blocker: str,
    safe_command: str | None = None,
    blocking_source: str | None = None,
) -> dict[str, Any]:
    return {
        "fixture": name,
        "action": action,
        "stop_boundary": stop_boundary,
        "safe_command": safe_command,
        "status": {
            "render_state": "FRESH",
            "critique_state": "FRESH",
            "export_state": "FRESH",
            "acceptance_state": "NOT_DECLARED",
            "publication_gate_state": "NOT_APPLICABLE",
            "release_ready": False,
        },
        "status_explanation": {
            "first_blocker": {
                "code": first_blocker,
                "category": "fixture_freshness",
                "manual": False,
            }
        },
        "next_action_summary": {
            "blocking_source": blocking_source or stop_boundary or "driver.action",
            "requires_human": action in {"human_gate_stop", "release_blocked"},
        },
    }


def _write_fixture(root: Path, name: str) -> None:
    fixture = root / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(f"name: {name}\npanels: []\n", encoding="utf-8")


def test_build_queue_json_rows_and_summaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        assert mode == "release"
        assert goal == "triage"
        assert repo_root == tmp_path
        if name == "alpha":
            return _summary(
                name,
                action="run_critique",
                stop_boundary="host_llm_critique_required",
                first_blocker="critique_stale",
                safe_command="/fig_critique alpha",
            )
        return _summary(
            name,
            action="release_blocked",
            stop_boundary="accepted_or_final_ready_required",
            first_blocker="acceptance_not_declared",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=None,
    )

    assert queue["schema"] == "figure-agent.fixture-driver-queue.v1"
    assert [row["fixture"] for row in queue["rows"]] == ["alpha", "beta"]
    assert queue["rows"][0]["safe_command"] == "/fig_critique alpha"
    assert queue["rows"][0]["required_actor"] == "host_llm"
    assert queue["rows"][0]["blocking_source"] == "host_llm_critique_required"
    assert queue["rows"][0]["requires_human"] is False
    assert queue["summary"]["total"] == 2
    assert queue["summary"]["by_action"] == {"release_blocked": 1, "run_critique": 1}
    assert queue["summary"]["by_required_actor"] == {
        "host_llm": 1,
        "release_operator": 1,
    }
    assert queue["summary"]["by_blocking_source"] == {
        "accepted_or_final_ready_required": 1,
        "host_llm_critique_required": 1,
    }
    assert queue["summary"]["by_stop_boundary"] == {
        "accepted_or_final_ready_required": 1,
        "host_llm_critique_required": 1,
    }
    assert queue["summary"]["by_first_blocker"] == {
        "acceptance_not_declared": 1,
        "critique_stale": 1,
    }


def test_build_queue_filters_requested_fixtures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")
    seen: list[str] = []

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        seen.append(name)
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        fixtures=["beta"],
    )

    assert seen == ["beta"]
    assert [row["fixture"] for row in queue["rows"]] == ["beta"]


def test_build_queue_records_missing_fixture_as_error(tmp_path: Path) -> None:
    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=["missing"],
    )

    assert queue["summary"]["total"] == 1
    assert queue["summary"]["errors"] == 1
    assert queue["rows"] == [
        {
            "fixture": "missing",
            "mode": "release",
            "action": "error",
            "stop_boundary": "fixture_not_found",
            "first_blocker": "fixture_not_found",
            "safe_command": None,
            "render_state": None,
            "critique_state": None,
            "export_state": None,
            "acceptance_state": None,
            "publication_gate_state": None,
            "release_ready": None,
            "required_actor": "workflow_agent",
            "blocking_source": "fixture_not_found",
            "requires_human": False,
            "error": "examples/missing/ not found",
        }
    ]


def test_print_table_outputs_rows_and_summary(capsys: pytest.CaptureFixture[str]) -> None:
    queue = {
        "schema": "figure-agent.fixture-driver-queue.v1",
        "mode": "release",
        "goal": "triage",
        "rows": [
            {
                "fixture": "alpha",
                "mode": "release",
                "action": "run_critique",
                "stop_boundary": "host_llm_critique_required",
                "first_blocker": "critique_stale",
                "safe_command": "/fig_critique alpha",
                "render_state": "FRESH",
                "critique_state": "STALE",
                "export_state": "FRESH",
                "acceptance_state": "NOT_DECLARED",
                "publication_gate_state": "NOT_APPLICABLE",
                "release_ready": False,
                "required_actor": "host_llm",
                "blocking_source": "host_llm_critique_required",
                "requires_human": False,
            }
        ],
        "summary": {
            "total": 1,
            "errors": 0,
            "by_action": {"run_critique": 1},
            "by_stop_boundary": {"host_llm_critique_required": 1},
            "by_first_blocker": {"critique_stale": 1},
            "by_required_actor": {"host_llm": 1},
            "by_blocking_source": {"host_llm_critique_required": 1},
        },
    }

    fig_queue.print_table(queue)

    out = capsys.readouterr().out
    assert "fixture actor action stop_boundary first_blocker safe_command" in out
    assert (
        "alpha host_llm run_critique host_llm_critique_required "
        "critique_stale /fig_critique alpha"
    ) in out
    assert "summary total=1 errors=0" in out


def test_main_prints_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(name, action="complete", stop_boundary=None, first_blocker="none")

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    assert fig_queue.main(
        ["--mode", "review", "--goal", "triage", "--json"],
        repo_root=tmp_path,
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.fixture-driver-queue.v1"
    assert payload["rows"][0]["fixture"] == "alpha"


def test_build_queue_filters_by_actor_and_preserves_unfiltered_total(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        if name == "alpha":
            return _summary(
                name,
                action="run_critique",
                stop_boundary="host_llm_critique_required",
                first_blocker="critique_stale",
            )
        return _summary(
            name,
            action="run_fig_loop",
            stop_boundary=None,
            first_blocker="acceptance_not_declared",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        fixtures=None,
        filters={"required_actor": "host_llm"},
    )

    assert queue["filters"] == {"required_actor": "host_llm"}
    assert queue["unfiltered_total"] == 2
    assert [row["fixture"] for row in queue["rows"]] == ["alpha"]
    assert queue["summary"]["total"] == 1
    assert queue["summary"]["by_required_actor"] == {"host_llm": 1}


def test_build_queue_filters_compose_with_fixture_args(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")
    seen: list[str] = []

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        seen.append(name)
        return _summary(
            name,
            action="release_blocked",
            stop_boundary="force_golden_required",
            first_blocker="export_tracked_golden",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="release",
        goal="triage",
        fixtures=["beta"],
        filters={"stop_boundary": "force_golden_required"},
    )

    assert seen == ["beta"]
    assert queue["unfiltered_total"] == 1
    assert [row["fixture"] for row in queue["rows"]] == ["beta"]


def test_main_json_accepts_filter_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    _write_fixture(tmp_path, "alpha")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action="run_critique",
            stop_boundary="host_llm_critique_required",
            first_blocker="critique_stale",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    assert fig_queue.main(
        [
            "--mode",
            "review",
            "--goal",
            "triage",
            "--actor",
            "host_llm",
            "--action",
            "run_critique",
            "--json",
        ],
        repo_root=tmp_path,
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["filters"] == {
        "action": "run_critique",
        "required_actor": "host_llm",
    }
    assert payload["unfiltered_total"] == 1
    assert payload["rows"][0]["fixture"] == "alpha"


def test_build_queue_can_include_command_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")
    _write_fixture(tmp_path, "gamma")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        if name == "alpha":
            return _summary(
                name,
                action="run_fig_loop",
                stop_boundary=None,
                first_blocker="acceptance_not_declared",
                safe_command="uv run python3 scripts/fig_loop.py alpha --goal triage --json",
            )
        if name == "beta":
            return _summary(
                name,
                action="run_export",
                stop_boundary="closeout_required",
                first_blocker="export_missing",
                safe_command="uv run python3 scripts/run_export.py beta",
            )
        return _summary(
            name,
            action="run_critique",
            stop_boundary="host_llm_critique_required",
            first_blocker="critique_stale",
            safe_command="/fig_critique gamma",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        fixtures=None,
        include_command_plan=True,
    )

    assert queue["command_plan"]["schema"] == "figure-agent.fixture-command-plan.v1"
    assert queue["command_plan"]["executable_count"] == 1
    assert queue["command_plan"]["blocked_count"] == 2
    assert queue["command_plan"]["executable"] == [
        {
            "fixture": "alpha",
            "action": "run_fig_loop",
            "safe_command": "uv run python3 scripts/fig_loop.py alpha --goal triage --json",
            "required_actor": "workflow_agent",
        }
    ]
    assert [row["fixture"] for row in queue["command_plan"]["blocked"]] == [
        "beta",
        "gamma",
    ]
    assert queue["command_plan"]["blocked"][0]["reason"] == "stop_boundary:closeout_required"
    assert queue["command_plan"]["blocked"][1]["reason"] == "required_actor:host_llm"


def test_command_plan_uses_filtered_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        return _summary(
            name,
            action="run_fig_loop",
            stop_boundary=None,
            first_blocker="acceptance_not_declared",
            safe_command=f"uv run python3 scripts/fig_loop.py {name} --goal triage --json",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    queue = fig_queue.build_queue(
        repo_root=tmp_path,
        mode="review",
        goal="triage",
        fixtures=None,
        filters={"action": "run_critique"},
        include_command_plan=True,
    )

    assert queue["unfiltered_total"] == 2
    assert queue["rows"] == []
    assert queue["command_plan"]["executable"] == []
    assert queue["command_plan"]["blocked"] == []


def test_main_commands_prints_executable_commands_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    _write_fixture(tmp_path, "alpha")
    _write_fixture(tmp_path, "beta")

    def fake_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
        if name == "alpha":
            return _summary(
                name,
                action="run_fig_loop",
                stop_boundary=None,
                first_blocker="acceptance_not_declared",
                safe_command="uv run python3 scripts/fig_loop.py alpha --goal triage --json",
            )
        return _summary(
            name,
            action="human_gate_stop",
            stop_boundary="human_gate_required",
            first_blocker="not_accepted",
        )

    monkeypatch.setattr(fig_queue.fig_driver, "build_driver_summary", fake_driver)

    assert fig_queue.main(
        ["--mode", "review", "--goal", "triage", "--commands"],
        repo_root=tmp_path,
    ) == 0

    assert capsys.readouterr().out.splitlines() == [
        "uv run python3 scripts/fig_loop.py alpha --goal triage --json"
    ]
