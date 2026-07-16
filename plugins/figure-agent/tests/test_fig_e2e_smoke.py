from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from hashlib import sha256
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import closed_loop_attempt_state  # noqa: E402
import closed_loop_current_state  # noqa: E402
import fig_e2e_smoke as smoke  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


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


def _root_attempt_manifest(fixture: Path) -> Path:
    source = fixture / f"{fixture.name}.tex"
    render = fixture / "build" / f"{fixture.name}.png"
    render.parent.mkdir()
    render.write_bytes(b"render")

    def digest(path: Path) -> str:
        return "sha256:" + sha256(path.read_bytes()).hexdigest()

    payload: dict[str, object] = {
        "schema": "figure-agent.root-attempt-manifest.v1",
        "fixture": fixture.name,
        "author": {"identity": "smoke-author", "role": "authoring_agent"},
        "source": {
            "path": f"examples/{fixture.name}/{fixture.name}.tex",
            "sha256": digest(source),
        },
        "render": {
            "path": f"examples/{fixture.name}/build/{fixture.name}.png",
            "sha256": digest(render),
        },
        "task": {"id": "smoke-task"},
        "model": {"identity": "smoke-model"},
        "budget": {"id": "smoke-budget"},
        "publication_acceptance": "not_claimed",
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["manifest_sha256"] = "sha256:" + sha256(encoded).hexdigest()
    manifest = fixture / "root-attempt-manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    return manifest


def test_default_command_runner_uses_bundled_fig_agent_for_internal_steps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], Path]] = []

    def fake_run(
        args: list[str],
        *,
        cwd: Path,
        capture_output: bool,
        text: bool,
        errors: str,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        calls.append((args, cwd))
        return _completed(args)

    monkeypatch.setenv("FIGURE_AGENT_PLUGIN_ROOT", str(PLUGIN_ROOT))
    monkeypatch.setattr(smoke.subprocess, "run", fake_run)

    result = smoke._default_command_runner(["fig-agent", "status", "loop_demo"], cwd=tmp_path)

    assert result.returncode == 0
    assert calls == [([str(PLUGIN_ROOT / "bin" / "fig-agent"), "status", "loop_demo"], tmp_path)]


def test_run_smoke_repeats_compile_export_status_loop_in_order(tmp_path: Path) -> None:
    _make_fixture(tmp_path)
    runs_root = tmp_path / ".scratch" / "fig-loop-runs"
    commands: list[list[str]] = []

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        assert cwd == tmp_path
        commands.append(args)
        if args[:2] == ["fig-agent", "loop"]:
            run_index = len([command for command in commands if "loop" in command])
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
        ["fig-agent", "compile", "loop_demo"],
        ["fig-agent", "export", "loop_demo"],
        ["fig-agent", "status", "loop_demo"],
        [
            "fig-agent",
            "loop",
            "loop_demo",
            "--goal",
            "dogfood (smoke run 1/2)",
            "--json",
            "--runs-root",
            str(runs_root),
        ],
        ["fig-agent", "compile", "loop_demo"],
        ["fig-agent", "export", "loop_demo"],
        ["fig-agent", "status", "loop_demo"],
        [
            "fig-agent",
            "loop",
            "loop_demo",
            "--goal",
            "dogfood (smoke run 2/2)",
            "--json",
            "--runs-root",
            str(runs_root),
        ],
    ]


def test_repeat_rechecks_canonical_resolution_before_each_mutation_cycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _make_fixture(tmp_path)
    resolutions: list[str] = []
    original = smoke.closed_loop_current_state.resolve_current_attempt

    def resolve(*args: object, **kwargs: object) -> dict[str, object]:
        if args:
            resolutions.append(str(args[1]))
        return original(*args, **kwargs)

    def runner(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        stdout = (
            _loop_stdout(tmp_path / "runs", index=len(resolutions))
            if args[:2] == ["fig-agent", "loop"]
            else "ok\n"
        )
        return _completed(args, stdout=stdout)

    monkeypatch.setattr(smoke.closed_loop_current_state, "resolve_current_attempt", resolve)

    smoke.run_smoke(
        fixture.name,
        repeat=2,
        repo_root=tmp_path,
        command_runner=runner,
    )

    assert resolutions == [fixture.name, fixture.name]


@pytest.mark.parametrize("resolution", ["current", "invalid", "ambiguous"])
def test_canonical_resolution_blocks_smoke_before_commands_or_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, resolution: str
) -> None:
    fixture = _make_fixture(tmp_path)
    calls: list[list[str]] = []
    monkeypatch.setattr(
        smoke.closed_loop_current_state,
        "resolve_current_attempt",
        lambda *_args, **_kwargs: {"resolution": resolution, "reason": "test"},
    )

    with pytest.raises(smoke.SmokeError, match=f"canonical_attempt_resolution:{resolution}"):
        smoke.run_smoke(
            fixture.name,
            repo_root=tmp_path,
            runs_root=tmp_path / ".scratch" / "fig-loop-runs",
            command_runner=lambda args, **_kwargs: calls.append(args) or _completed(args),
        )

    assert calls == []
    assert not (fixture / "build").exists()
    assert not (fixture / "exports").exists()
    assert not (tmp_path / ".scratch").exists()


@pytest.mark.parametrize("symlink_kind", ["fixture", "examples"])
def test_symlinked_fixture_or_examples_blocks_smoke_before_commands(
    tmp_path: Path, symlink_kind: str
) -> None:
    target = tmp_path / "target"
    _make_fixture(target)
    examples = tmp_path / "examples"
    if symlink_kind == "fixture":
        examples.mkdir()
        (examples / "loop_demo").symlink_to(target / "examples" / "loop_demo")
    else:
        examples.symlink_to(target / "examples")
    calls: list[list[str]] = []

    with pytest.raises(smoke.SmokeError, match="canonical_preflight:fixture_symlink"):
        smoke.run_smoke(
            "loop_demo",
            repo_root=tmp_path,
            command_runner=lambda args, **_kwargs: calls.append(args) or _completed(args),
        )

    assert calls == []
    assert not (tmp_path / ".scratch").exists()


def test_resolver_error_and_busy_lease_block_smoke_before_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _make_fixture(tmp_path)
    calls: list[list[str]] = []
    monkeypatch.setattr(
        smoke.closed_loop_current_state,
        "resolve_current_attempt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("unavailable")),
    )
    def runner(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        return _completed(args)
    with pytest.raises(smoke.SmokeError, match="canonical_state_resolution_error"):
        smoke.run_smoke(fixture.name, repo_root=tmp_path, command_runner=runner)
    assert calls == []

    monkeypatch.setattr(
        smoke.closed_loop_current_state,
        "resolve_current_attempt",
        lambda *_args, **_kwargs: {"resolution": "absent", "reason": None},
    )
    with closed_loop_attempt_state.fixture_admission_lock(tmp_path, fixture.name):
        with pytest.raises(smoke.SmokeError, match="canonical_admission_legacy_coordination_busy"):
            smoke.run_smoke(fixture.name, repo_root=tmp_path, command_runner=runner)
    assert calls == []


def test_smoke_holds_admission_lease_through_status_then_releases_before_loop(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    manifest = _root_attempt_manifest(fixture)
    entered_compile = threading.Event()
    release_compile = threading.Event()
    commands: list[list[str]] = []
    marker = tmp_path / "root-admission-marker.txt"

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        if args[:2] == ["fig-agent", "compile"]:
            entered_compile.set()
            assert release_compile.wait(timeout=2)
        if args[:2] == ["fig-agent", "loop"]:
            return _completed(args, stdout=_loop_stdout(tmp_path / "runs"))
        return _completed(args)

    thread = threading.Thread(
        target=lambda: smoke.run_smoke(fixture.name, repo_root=tmp_path, command_runner=runner),
    )
    thread.start()
    assert entered_compile.wait(timeout=2)

    root_admission = """
from pathlib import Path
from closed_loop_attempt_admission import ClosedLoopAttemptAdmissionError, admit_root_attempt

workspace = Path(__import__("sys").argv[1])
fixture = __import__("sys").argv[2]
manifest = Path(__import__("sys").argv[3])
marker = Path(__import__("sys").argv[4])
try:
    admitted = admit_root_attempt(
        fixture, manifest_path=manifest, execute=True, workspace_root=workspace
    )
    marker.write_text("published:" + str(admitted["created"]), encoding="utf-8")
except ClosedLoopAttemptAdmissionError as exc:
    marker.write_text("error:" + str(exc), encoding="utf-8")
"""
    environment = {
        **os.environ,
        "PYTHONPATH": str(PLUGIN_ROOT / "scripts"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }

    command = [
        sys.executable,
        "-c",
        root_admission,
        str(tmp_path),
        fixture.name,
        str(manifest),
        str(marker),
    ]
    blocked = subprocess.run(
        command,
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=2,
        check=False,
    )
    assert blocked.returncode == 0
    assert marker.read_text(encoding="utf-8") == (
        "error:canonical_admission_legacy_coordination_busy"
    )
    assert not (fixture / "review" / "closed-loop").exists()

    release_compile.set()
    thread.join(timeout=2)
    assert not thread.is_alive()

    marker.unlink()
    admitted = subprocess.run(
        command,
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=2,
        check=False,
    )
    assert admitted.returncode == 0
    assert marker.read_text(encoding="utf-8") == "published:True"
    current = closed_loop_current_state.resolve_current_attempt(tmp_path, fixture.name)
    assert current["resolution"] == "current"
    assert current["state"] == "authored_rendered"
    assert commands[:3] == [
        ["fig-agent", "compile", fixture.name],
        ["fig-agent", "export", fixture.name],
        ["fig-agent", "status", fixture.name],
    ]


def test_smoke_release_precedes_legacy_loop_preflight(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    commands: list[list[str]] = []

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        if args[:2] == ["fig-agent", "loop"]:
            with closed_loop_attempt_state.fixture_admission_lock(tmp_path, fixture.name):
                pass
            return _completed(args, stdout=_loop_stdout(tmp_path / "runs"))
        return _completed(args)

    summary = smoke.run_smoke(fixture.name, repo_root=tmp_path, command_runner=runner)

    assert summary["success"] is True
    assert commands[-1][:2] == ["fig-agent", "loop"]


def test_run_smoke_stops_on_first_failed_step(tmp_path: Path) -> None:
    _make_fixture(tmp_path)
    commands: list[list[str]] = []

    def runner(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        commands.append(args)
        if args == ["fig-agent", "export", "loop_demo"]:
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
        ["fig-agent", "compile", "loop_demo"],
        ["fig-agent", "export", "loop_demo"],
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
        if args[:2] == ["fig-agent", "loop"]:
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
        if args == ["fig-agent", "export", "loop_demo"]:
            return subprocess.CompletedProcess(
                args,
                0,
                stdout="",
                stderr="run_export.py: exports/ for loop_demo is TRACKED_GOLDEN\n",
            )
        if args[:2] == ["fig-agent", "loop"]:
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
        if args[:2] == ["fig-agent", "loop"]:
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
        if args[:2] == ["fig-agent", "loop"]:
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
        if args[:2] == ["fig-agent", "loop"]:
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
        if args[:2] == ["fig-agent", "loop"]:
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
        if args[:2] == ["fig-agent", "loop"]:
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
        if args[0:2] == ["fig-agent", "compile"]:
            build = fixture / "build"
            build.mkdir()
            (build / "loop_demo.pdf").write_bytes(b"%PDF")
            (build / "loop_demo.png").write_bytes(b"\x89PNG")
        elif args == ["fig-agent", "export", "loop_demo"]:
            exports = fixture / "exports"
            exports.mkdir()
            (exports / "loop_demo.pdf").write_bytes(b"%PDF")
            (exports / "loop_demo.svg").write_text("<svg/>", encoding="utf-8")
            (exports / "loop_demo.tif").write_bytes(b"TIFF")
            (exports / "loop_demo.png").write_bytes(b"\x89PNG")
        elif args[:2] == ["fig-agent", "loop"]:
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
