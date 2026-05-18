from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_closeout as fig_closeout_mod  # noqa: E402
from fig_closeout import compute_closeout, main  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402


def _make_fixture(repo: Path, name: str = "loop_demo") -> Path:
    fixture = repo / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        f"name: {name}\npanels: []\nstyle_profile: polymer-default\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("briefing", encoding="utf-8")
    return fixture


def _status(
    *,
    render_state: str = "FRESH",
    critique_state: str = "NOT_REQUIRED",
    export_state: str = "FRESH",
    workflow_ready: bool = True,
    next_hint: str = "done",
) -> dict:
    return {
        "stage": 4,
        "name": "loop_demo",
        "checks": [],
        "notes": [],
        "next": next_hint,
        "accepted": None,
        "exports_substate": export_state,
        "render_state": render_state,
        "critique_state": critique_state,
        "export_state": export_state,
        "acceptance_state": "NOT_DECLARED",
        "workflow_ready": workflow_ready,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }


def _steps_by_id(report: dict) -> dict[str, dict]:
    return {step["id"]: step for step in report["steps"]}


def _write_adjudication(fixture: Path, critique: Path) -> None:
    (fixture / "critique_adjudication.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.critique-adjudication.v1",
                "fixture": fixture.name,
                "source_critique_hash": file_sha256(critique),
                "decisions": [
                    {
                        "finding_id": "C001",
                        "decision": "dismiss",
                        "reason": "false positive",
                        "patch_target": "",
                        "evidence": "",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_loop_run(repo: Path, name: str = "loop_demo", *, fixture: str | None = None) -> Path:
    run_dir = repo / ".scratch" / "fig-loop-runs" / f"20260518-000000-{name}"
    run_dir.mkdir(parents=True)
    iteration = run_dir / "iteration_001.json"
    iteration.write_text(json.dumps({"iteration": 1}) + "\n", encoding="utf-8")
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.fig-loop-run.v1",
                "fixture": fixture or name,
                "iterations": ["iteration_001.json"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return iteration


def test_closeout_reports_compile_critique_and_loop_actions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_fixture(tmp_path)
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(
            render_state="MISSING",
            critique_state="STALE",
            export_state="STALE",
            workflow_ready=False,
            next_hint="run /fig_compile loop_demo then /fig_critique loop_demo",
        ),
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    steps = _steps_by_id(report)

    assert report["schema"] == "figure-agent.closeout.v1"
    assert report["closeout_complete"] is False
    assert steps["compile"]["state"] == "needs_action"
    assert steps["compile"]["command"] == "/fig_compile loop_demo"
    assert steps["critique"]["state"] == "needs_action"
    assert steps["critique"]["command"] == "/fig_critique loop_demo"
    assert steps["adjudication"]["state"] == "blocked"
    assert steps["export"]["state"] == "blocked"
    assert steps["loop_rerun"]["state"] == "blocked"
    assert steps["loop_rerun"]["command"] is None
    assert steps["loop_rerun"]["evidence"]["blocked_by"] == [
        "compile",
        "critique",
        "adjudication",
        "export",
    ]


def test_closeout_blocks_compile_when_source_is_not_authored(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_fixture(tmp_path)
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(
            render_state="NOT_AUTHORED",
            export_state="MISSING",
            workflow_ready=False,
            next_hint="author examples/<name>/<name>.tex",
        ),
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    compile_step = _steps_by_id(report)["compile"]

    assert compile_step["state"] == "blocked"
    assert compile_step["command"] is None
    assert compile_step["evidence"]["next"] == "author examples/<name>/<name>.tex"


def test_closeout_requires_adjudication_for_fresh_critique(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_fixture(tmp_path)
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(critique_state="FRESH"),
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    steps = _steps_by_id(report)

    assert steps["compile"]["state"] == "passed"
    assert steps["critique"]["state"] == "passed"
    assert steps["adjudication"]["state"] == "needs_action"
    assert steps["adjudication"]["command"] == "/fig_adjudicate loop_demo"
    assert steps["export"]["state"] == "passed"
    assert report["next_action"] == "/fig_adjudicate loop_demo"


def test_closeout_invalid_adjudication_does_not_emit_fake_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    (fixture / "critique_adjudication.yaml").write_text("not: valid\n", encoding="utf-8")
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(critique_state="FRESH"),
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    adjudication_step = _steps_by_id(report)["adjudication"]

    assert adjudication_step["state"] == "needs_action"
    assert adjudication_step["command"] is None
    assert "invalid" in adjudication_step["reason"]
    assert report["next_action"] == adjudication_step["reason"]


def test_closeout_stale_adjudication_does_not_emit_fake_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# old critique\n", encoding="utf-8")
    _write_adjudication(fixture, critique)
    critique.write_text("# new critique\n", encoding="utf-8")
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(critique_state="FRESH"),
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    adjudication_step = _steps_by_id(report)["adjudication"]

    assert adjudication_step["state"] == "needs_action"
    assert adjudication_step["command"] is None
    assert adjudication_step["reason"] == "critique_adjudication.yaml is stale against critique.md"
    assert report["next_action"] == adjudication_step["reason"]


def test_closeout_passes_when_loop_record_is_newer_than_fixture_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    tex = fixture / "loop_demo.tex"
    tex.write_text("% tikz\n", encoding="utf-8")
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(fixture, critique)
    old_time = 1000
    for path in fixture.rglob("*"):
        if path.is_file():
            os.utime(path, (old_time, old_time))
    iteration = _write_loop_run(tmp_path)
    os.utime(iteration, (old_time + 100, old_time + 100))
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(critique_state="FRESH"),
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    steps = _steps_by_id(report)

    assert report["closeout_complete"] is True
    assert steps["adjudication"]["state"] == "passed"
    assert steps["loop_rerun"]["state"] == "passed"
    assert report["next_action"] == "closeout complete"


def test_closeout_loop_rerun_is_stale_when_fixture_changed_after_loop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    tex = fixture / "loop_demo.tex"
    tex.write_text("% tikz\n", encoding="utf-8")
    for path in fixture.rglob("*"):
        if path.is_file():
            os.utime(path, (900, 900))
    iteration = _write_loop_run(tmp_path)
    os.utime(iteration, (1000, 1000))
    os.utime(tex, (1100, 1100))
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(),
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    loop_step = _steps_by_id(report)["loop_rerun"]

    assert loop_step["state"] == "needs_action"
    assert loop_step["command"] == '/fig_loop loop_demo --goal "<goal>"'
    assert loop_step["reason"] == (
        "examples/loop_demo/loop_demo.tex is newer than latest loop record"
    )


def test_closeout_ignores_loop_record_for_the_wrong_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    tex = fixture / "loop_demo.tex"
    tex.write_text("% tikz\n", encoding="utf-8")
    old_time = 1000
    os.utime(tex, (old_time, old_time))
    iteration = _write_loop_run(tmp_path, fixture="different_fixture")
    os.utime(iteration, (old_time + 100, old_time + 100))
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(),
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    loop_step = _steps_by_id(report)["loop_rerun"]

    assert loop_step["state"] == "needs_action"
    assert loop_step["reason"] == "no post-patch fig_loop run was found"


def test_closeout_ignores_loop_record_with_malformed_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    tex = fixture / "loop_demo.tex"
    tex.write_text("% tikz\n", encoding="utf-8")
    for path in fixture.rglob("*"):
        if path.is_file():
            os.utime(path, (900, 900))
    iteration = _write_loop_run(tmp_path)
    (iteration.parent / "run_manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.fig-loop-run.v1",
                "fixture": "loop_demo",
                "iterations": "iteration_001.json",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    os.utime(iteration, (1000, 1000))
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(),
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    loop_step = _steps_by_id(report)["loop_rerun"]

    assert loop_step["state"] == "needs_action"
    assert loop_step["reason"] == "no post-patch fig_loop run was found"


def test_closeout_blocks_loop_rerun_until_adjudication_is_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _make_fixture(tmp_path)
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(critique_state="FRESH"),
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    loop_step = _steps_by_id(report)["loop_rerun"]

    assert loop_step["state"] == "blocked"
    assert loop_step["command"] is None
    assert loop_step["evidence"]["blocked_by"] == ["adjudication"]


def test_closeout_tracks_golden_roll_forward_as_manual_approval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(fixture, critique)
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(critique_state="FRESH", export_state="TRACKED_GOLDEN"),
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    export_step = _steps_by_id(report)["export"]

    assert export_step["state"] == "blocked"
    assert export_step["command"] is None
    assert export_step["evidence"]["approval_command"] == "/fig_export loop_demo --force-golden"
    assert report["next_action"] == "tracked golden export requires deliberate manual approval"


def test_closeout_cli_json_outputs_machine_readable_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _make_fixture(tmp_path)
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(),
    )

    exit_code = main(["loop_demo", "--repo-root", str(tmp_path), "--json"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err == ""
    data = json.loads(captured.out)
    assert data["fixture"] == "loop_demo"
    assert _steps_by_id(data)["loop_rerun"]["state"] == "needs_action"


def test_closeout_cli_reports_status_errors_without_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _make_fixture(tmp_path)

    def _raise_status_error(_example_dir: Path) -> dict:
        raise ValueError("Unknown style_profile 'bad'")

    monkeypatch.setattr(fig_closeout_mod, "infer_stage", _raise_status_error)

    exit_code = main(["loop_demo", "--repo-root", str(tmp_path), "--json"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "fig_closeout.py: cannot compute status for examples/loop_demo" in captured.err
    assert "Traceback" not in captured.err
