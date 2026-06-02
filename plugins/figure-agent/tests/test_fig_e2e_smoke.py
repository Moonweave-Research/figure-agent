from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_e2e_smoke as smoke  # noqa: E402


def _make_fixture(repo: Path, name: str = "loop_demo") -> Path:
    fixture = repo / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        f"name: {name}\npanels: []\nstyle_profile: polymer-default\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("briefing", encoding="utf-8")
    (fixture / f"{name}.tex").write_text("\\documentclass{standalone}\n", encoding="utf-8")
    return fixture


def _loop_stdout(
    runs_root: Path,
    *,
    index: int = 1,
    stop_reason: str = "status_action_required",
    escalation_level: str = "agent_action_required",
    patch_handoff_present: bool = False,
) -> str:
    loop_payload = {
        "run_dir": str(runs_root / f"run-{index}"),
        "manifest_path": str(runs_root / f"run-{index}" / "run_manifest.json"),
        "iteration_path": str(runs_root / f"run-{index}" / "iteration_001.json"),
        "final_stop_reason": stop_reason,
        "escalation_level": escalation_level,
        "patch_handoff_present": patch_handoff_present,
    }
    return json.dumps(loop_payload) + "\n"


def _completed(
    args: list[str],
    returncode: int = 0,
    stdout: str = "ok\n",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr="")


def test_run_smoke_repeats_compile_export_status_loop_in_order(tmp_path: Path) -> None:
    _make_fixture(tmp_path)
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    commands: list[list[str]] = []

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        assert cwd == tmp_path
        commands.append(args)
        if args[:4] == ["uv", "run", "python3", "scripts/fig_loop.py"]:
            run_index = len([command for command in commands if "scripts/fig_loop.py" in command])
            return _completed(args, stdout=_loop_stdout(runs_root, index=run_index))
        return _completed(args)

    summary = smoke.run_smoke(
        "loop_demo",
        goal="dogfood",
        repeat=2,
        repo_root=tmp_path,
        runs_root=runs_root,
        command_runner=runner,
    )

    assert summary["success"] is True
    assert summary["repeat"] == 2
    assert [run["iteration"] for run in summary["runs"]] == [1, 2]
    assert [run["fig_loop"]["final_stop_reason"] for run in summary["runs"]] == [
        "status_action_required",
        "status_action_required",
    ]
    assert commands == [
        ["bash", "scripts/compile.sh", "examples/loop_demo/loop_demo.tex"],
        ["uv", "run", "python3", "scripts/run_export.py", "loop_demo"],
        ["uv", "run", "python3", "scripts/status.py", "examples/loop_demo"],
        [
            "uv",
            "run",
            "python3",
            "scripts/fig_loop.py",
            "loop_demo",
            "--goal",
            "dogfood (smoke run 1/2)",
            "--json",
            "--runs-root",
            str(runs_root),
        ],
        ["bash", "scripts/compile.sh", "examples/loop_demo/loop_demo.tex"],
        ["uv", "run", "python3", "scripts/run_export.py", "loop_demo"],
        ["uv", "run", "python3", "scripts/status.py", "examples/loop_demo"],
        [
            "uv",
            "run",
            "python3",
            "scripts/fig_loop.py",
            "loop_demo",
            "--goal",
            "dogfood (smoke run 2/2)",
            "--json",
            "--runs-root",
            str(runs_root),
        ],
    ]


def test_run_smoke_stops_on_first_failed_step(tmp_path: Path) -> None:
    _make_fixture(tmp_path)
    commands: list[list[str]] = []

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        if args == ["uv", "run", "python3", "scripts/run_export.py", "loop_demo"]:
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="critique_stale\n")
        return _completed(args)

    summary = smoke.run_smoke(
        "loop_demo",
        goal="dogfood",
        repo_root=tmp_path,
        command_runner=runner,
    )

    assert summary["success"] is False
    assert summary["failed_run"] == 1
    assert summary["failed_step"] == "export"
    assert summary["runs"][0]["export"]["returncode"] == 1
    assert summary["runs"][0]["export"]["stderr_tail"] == "critique_stale\n"
    assert commands == [
        ["bash", "scripts/compile.sh", "examples/loop_demo/loop_demo.tex"],
        ["uv", "run", "python3", "scripts/run_export.py", "loop_demo"],
    ]


def test_run_smoke_missing_tex_fails_preflight_without_running_commands(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "examples" / "loop_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        "name: loop_demo\npanels: []\nstyle_profile: polymer-default\n",
        encoding="utf-8",
    )
    calls: list[list[str]] = []

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return _completed(args)

    with pytest.raises(smoke.SmokeError, match="examples/loop_demo/loop_demo.tex not found"):
        smoke.run_smoke("loop_demo", repo_root=tmp_path, command_runner=runner)

    assert calls == []


def test_run_smoke_manual_approval_loop_outcome_is_still_success(tmp_path: Path) -> None:
    _make_fixture(tmp_path)
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        if args[:4] == ["uv", "run", "python3", "scripts/fig_loop.py"]:
            return _completed(
                args,
                stdout=_loop_stdout(
                    runs_root,
                    stop_reason="status_action_required",
                    escalation_level="manual_approval_required",
                ),
            )
        return _completed(args)

    summary = smoke.run_smoke(
        "loop_demo",
        repo_root=tmp_path,
        runs_root=runs_root,
        command_runner=runner,
    )

    assert summary["success"] is True
    assert summary["runs"][0]["fig_loop"]["final_stop_reason"] == "status_action_required"
    assert summary["runs"][0]["fig_loop"]["escalation_level"] == "manual_approval_required"


def test_run_smoke_tracked_golden_export_noop_is_success(tmp_path: Path) -> None:
    _make_fixture(tmp_path)
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        if args == ["uv", "run", "python3", "scripts/run_export.py", "loop_demo"]:
            return subprocess.CompletedProcess(
                args,
                0,
                stdout="",
                stderr="run_export.py: exports/ for loop_demo is TRACKED_GOLDEN\n",
            )
        if args[:4] == ["uv", "run", "python3", "scripts/fig_loop.py"]:
            return _completed(args, stdout=_loop_stdout(runs_root))
        return _completed(args)

    summary = smoke.run_smoke(
        "loop_demo",
        repo_root=tmp_path,
        runs_root=runs_root,
        command_runner=runner,
    )

    assert summary["success"] is True
    assert "TRACKED_GOLDEN" in summary["runs"][0]["export"]["stderr_tail"]
    assert "--force-golden" not in summary["runs"][0]["export"]["args"]


def test_run_smoke_invalid_fig_loop_json_fails_fig_loop_step(tmp_path: Path) -> None:
    _make_fixture(tmp_path)
    commands: list[list[str]] = []

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        if args[:4] == ["uv", "run", "python3", "scripts/fig_loop.py"]:
            return _completed(args, stdout="not json\n")
        return _completed(args)

    summary = smoke.run_smoke(
        "loop_demo",
        repeat=2,
        repo_root=tmp_path,
        command_runner=runner,
    )

    assert summary["success"] is False
    assert summary["failed_run"] == 1
    assert summary["failed_step"] == "fig_loop"
    assert len(summary["runs"]) == 1
    assert len(commands) == 4


def test_run_smoke_missing_fig_loop_json_key_fails_fig_loop_step(tmp_path: Path) -> None:
    _make_fixture(tmp_path)

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        if args[:4] == ["uv", "run", "python3", "scripts/fig_loop.py"]:
            return _completed(
                args,
                stdout=json.dumps({"run_dir": "missing required keys"}) + "\n",
            )
        return _completed(args)

    summary = smoke.run_smoke("loop_demo", repo_root=tmp_path, command_runner=runner)

    assert summary["success"] is False
    assert summary["failed_step"] == "fig_loop"


def test_run_smoke_wrong_fig_loop_json_type_fails_fig_loop_step(tmp_path: Path) -> None:
    _make_fixture(tmp_path)
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        if args[:4] == ["uv", "run", "python3", "scripts/fig_loop.py"]:
            payload = json.loads(_loop_stdout(runs_root))
            payload["patch_handoff_present"] = "false"
            return _completed(args, stdout=json.dumps(payload) + "\n")
        return _completed(args)

    summary = smoke.run_smoke(
        "loop_demo",
        repo_root=tmp_path,
        runs_root=runs_root,
        command_runner=runner,
    )

    assert summary["success"] is False
    assert summary["failed_step"] == "fig_loop"


def test_run_smoke_parses_full_fig_loop_stdout_not_tail(tmp_path: Path) -> None:
    _make_fixture(tmp_path)
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        if args[:4] == ["uv", "run", "python3", "scripts/fig_loop.py"]:
            payload = json.loads(_loop_stdout(runs_root))
            payload["padding"] = "x" * 5000
            return _completed(args, stdout=json.dumps(payload) + "\n")
        return _completed(args)

    summary = smoke.run_smoke(
        "loop_demo",
        repo_root=tmp_path,
        runs_root=runs_root,
        command_runner=runner,
    )

    assert summary["success"] is True
    assert "padding" not in summary["runs"][0]["fig_loop"]


def test_run_smoke_status_summary_exception_becomes_status_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_fixture(tmp_path)

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        return _completed(args)

    def broken_status(_example_dir: Path) -> dict:
        raise RuntimeError("status exploded")

    monkeypatch.setattr(smoke, "infer_stage", broken_status)

    summary = smoke.run_smoke("loop_demo", repo_root=tmp_path, command_runner=runner)

    assert summary["success"] is False
    assert summary["failed_step"] == "status"
    assert summary["runs"][0]["status_error"] == "status exploded"


def test_run_smoke_fails_when_repeat_outcome_drifts(tmp_path: Path) -> None:
    _make_fixture(tmp_path)
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    loop_calls = 0

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        nonlocal loop_calls
        if args[:4] == ["uv", "run", "python3", "scripts/fig_loop.py"]:
            loop_calls += 1
            stop_reason = "status_action_required" if loop_calls == 1 else "verify_only_complete"
            return _completed(
                args,
                stdout=_loop_stdout(runs_root, index=loop_calls, stop_reason=stop_reason),
            )
        return _completed(args)

    summary = smoke.run_smoke(
        "loop_demo",
        repeat=2,
        repo_root=tmp_path,
        runs_root=runs_root,
        command_runner=runner,
    )

    assert summary["success"] is False
    assert summary["failed_run"] == 2
    assert summary["failed_step"] == "repeat_stability"
    assert summary["stability_mismatch"]["baseline"]["fig_loop"]["final_stop_reason"] == (
        "status_action_required"
    )
    assert summary["stability_mismatch"]["current"]["fig_loop"]["final_stop_reason"] == (
        "verify_only_complete"
    )


def test_run_smoke_does_not_mutate_non_output_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "critique.md").write_text("# critique\n", encoding="utf-8")
    (fixture / "critique_adjudication.yaml").write_text(
        "schema: figure-agent.critique-adjudication.v1\n",
        encoding="utf-8",
    )
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"

    def snapshot() -> dict[str, bytes]:
        ignored = {"build", "exports", ".scratch"}
        files: dict[str, bytes] = {}
        for path in sorted(tmp_path.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(tmp_path)
            if any(part in ignored for part in rel.parts):
                continue
            files[str(rel)] = path.read_bytes()
        return files

    before = snapshot()
    monkeypatch.setattr(
        smoke,
        "infer_stage",
        lambda _example_dir: {
            "stage": 4,
            "render_state": "FRESH",
            "critique_state": "NOT_REQUIRED",
            "export_state": "FRESH",
            "acceptance_state": "NOT_DECLARED",
            "workflow_ready": True,
            "golden_ready": False,
            "release_ready": False,
            "final_ready": False,
            "notes": [],
            "next": "done",
        },
    )

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        if args[0:2] == ["bash", "scripts/compile.sh"]:
            build = fixture / "build"
            build.mkdir()
            (build / "loop_demo.pdf").write_bytes(b"%PDF")
            (build / "loop_demo.png").write_bytes(b"\x89PNG")
        elif args == ["uv", "run", "python3", "scripts/run_export.py", "loop_demo"]:
            exports = fixture / "exports"
            exports.mkdir()
            (exports / "loop_demo.pdf").write_bytes(b"%PDF")
            (exports / "loop_demo.svg").write_text("<svg/>", encoding="utf-8")
            (exports / "loop_demo.tif").write_bytes(b"TIFF")
            (exports / "loop_demo.png").write_bytes(b"\x89PNG")
        elif args[:4] == ["uv", "run", "python3", "scripts/fig_loop.py"]:
            (runs_root / "run-1").mkdir(parents=True)
            return _completed(args, stdout=_loop_stdout(runs_root))
        return _completed(args)

    summary = smoke.run_smoke(
        "loop_demo",
        repo_root=tmp_path,
        runs_root=runs_root,
        command_runner=runner,
    )

    assert summary["success"] is True
    assert snapshot() == before


def test_default_command_runner_replaces_non_utf8_output(tmp_path: Path) -> None:
    child = [sys.executable, "-c", 'import os; os.write(1, b"\\xff\\xfe font name\\n")']

    result = smoke._default_command_runner(child, cwd=tmp_path)

    assert result.returncode == 0
    assert "�" in result.stdout


def test_repeat_must_be_positive(tmp_path: Path) -> None:
    _make_fixture(tmp_path)

    with pytest.raises(smoke.SmokeError, match="repeat"):
        smoke.run_smoke("loop_demo", goal="dogfood", repeat=0, repo_root=tmp_path)


def test_main_emits_json_summary_and_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_smoke(
        name: str,
        *,
        goal: str,
        repeat: int,
        repo_root: Path,
        runs_root: Path | None,
    ) -> dict:
        assert name == "loop_demo"
        assert goal == "dogfood"
        assert repeat == 3
        assert repo_root == tmp_path
        assert runs_root == tmp_path / "runs"
        return {
            "schema": "figure-agent.e2e-smoke.v1",
            "fixture": name,
            "goal": goal,
            "repeat": repeat,
            "success": True,
            "runs": [],
        }

    monkeypatch.setattr(smoke, "run_smoke", fake_run_smoke)

    exit_code = smoke.main(
        [
            "loop_demo",
            "--goal",
            "dogfood",
            "--repeat",
            "3",
            "--repo-root",
            str(tmp_path),
            "--runs-root",
            str(tmp_path / "runs"),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["success"] is True
    assert captured.err == ""


def test_main_accepts_json_noop_flag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_smoke(
        name: str,
        *,
        goal: str,
        repeat: int,
        repo_root: Path,
        runs_root: Path | None,
    ) -> dict:
        return {
            "schema": "figure-agent.e2e-smoke.v1",
            "fixture": name,
            "goal": goal,
            "repeat": repeat,
            "success": True,
            "runs": [],
        }

    monkeypatch.setattr(smoke, "run_smoke", fake_run_smoke)

    exit_code = smoke.main(["loop_demo", "--repo-root", str(tmp_path), "--json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["schema"] == "figure-agent.e2e-smoke.v1"
    assert payload["success"] is True


def test_main_accepts_format_json_alias(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_smoke(
        name: str,
        *,
        goal: str,
        repeat: int,
        repo_root: Path,
        runs_root: Path | None,
    ) -> dict:
        return {
            "schema": "figure-agent.e2e-smoke.v1",
            "fixture": name,
            "goal": goal,
            "repeat": repeat,
            "success": True,
            "runs": [],
        }

    monkeypatch.setattr(smoke, "run_smoke", fake_run_smoke)

    exit_code = smoke.main(["loop_demo", "--repo-root", str(tmp_path), "--format", "json"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["schema"] == "figure-agent.e2e-smoke.v1"
    assert payload["success"] is True


def test_main_missing_fixture_returns_json_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = smoke.main(["missing", "--repo-root", str(tmp_path)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 1
    assert payload["success"] is False
    assert payload["fixture"] == "missing"
    assert "examples/missing/ not found" in payload["error"]
    assert captured.err == ""


def test_run_smoke_rejects_unsafe_fixture_name_before_commands(tmp_path: Path) -> None:
    repo = tmp_path
    (repo / "examples").mkdir()
    outside = repo / "outside"
    outside.mkdir()
    (outside / "spec.yaml").write_text("name: outside\npanels: []\n", encoding="utf-8")
    commands: list[list[str]] = []

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        return _completed(args)

    with pytest.raises(
        smoke.SmokeError,
        match="fixture name must be a single examples/<name> directory name",
    ):
        smoke.run_smoke("../outside", repo_root=repo, command_runner=runner)

    assert commands == []


def test_main_returns_exit_code_1_when_run_smoke_reports_unsuccessful_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run_smoke(
        name: str,
        *,
        goal: str,
        repeat: int,
        repo_root: Path,
        runs_root: Path | None,
    ) -> dict:
        return {
            "schema": "figure-agent.e2e-smoke.v1",
            "fixture": name,
            "goal": goal,
            "repeat": repeat,
            "success": False,
            "failed_run": 1,
            "failed_step": "export",
            "runs": [],
        }

    monkeypatch.setattr(smoke, "run_smoke", fake_run_smoke)

    exit_code = smoke.main(["loop_demo", "--repo-root", str(tmp_path)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 1
    assert payload["success"] is False
    assert payload["failed_step"] == "export"
