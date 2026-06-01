from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_run_journal import latest_journal_summary, main  # noqa: E402


def _write_fixture(repo_root: Path, name: str = "runner_demo") -> Path:
    example_dir = repo_root / "examples" / name
    example_dir.mkdir(parents=True)
    (example_dir / f"{name}.tex").write_text("% source\n", encoding="utf-8")
    (example_dir / "briefing.md").write_text("brief\n", encoding="utf-8")
    return example_dir


def _touch_fixture_evidence(example_dir: Path, timestamp: float) -> None:
    for path in example_dir.iterdir():
        if path.is_file():
            os.utime(path, (timestamp, timestamp))


def _write_run_journal(
    repo_root: Path,
    *,
    run_id: str,
    fixture: str = "runner_demo",
    final_stop_reason: str = "host_boundary",
    mtime: float | None = None,
) -> Path:
    run_dir = repo_root / ".scratch" / "fig-run-runs" / run_id
    run_dir.mkdir(parents=True)
    manifest = {
        "schema": "figure-agent.fig-run-journal.v1",
        "fixture": fixture,
        "mode": "review",
        "goal": "close loop",
        "execute": True,
        "max_steps": 5,
        "executed_count": 1,
        "final_action": "run_critique",
        "final_safe_command": "/fig_critique runner_demo",
        "final_stop_boundary": "host_llm_critique_required",
        "final_stop_reason": final_stop_reason,
        "run_dir": str(run_dir),
        "started_at": "2026-06-01T01:00:00Z",
        "completed_at": "2026-06-01T01:01:00Z",
        "run_json": "run.json",
        "steps": ["steps/step_001.json"],
        "stop_markdown": "stop.md",
        "authoritative": False,
        "replay_allowed": False,
        "commands_are_evidence_only": True,
        "rerun_live_status_first": True,
        "rerun_live_driver_first": True,
    }
    payload = {
        "schema": "figure-agent.run.v1",
        "fixture": fixture,
        "mode": "review",
        "goal": "close loop",
        "final_action": "run_critique",
        "final_safe_command": "/fig_critique runner_demo",
        "final_stop_boundary": "host_llm_critique_required",
        "final_stop_reason": final_stop_reason,
        "executed_count": 1,
        "boundary_handoff": {
            "schema": "figure-agent.boundary-handoff.v1",
            "required_actor": "host_llm",
            "blocking_reason": "critique is required",
            "closeout_checks": [
                "write or refresh critique.md",
                "rerun live /fig_status",
                "rerun live /fig_drive",
            ],
        },
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (run_dir / "run.json").write_text(json.dumps(payload), encoding="utf-8")
    if mtime is not None:
        os.utime(run_dir / "run_manifest.json", (mtime, mtime))
        os.utime(run_dir / "run.json", (mtime, mtime))
    return run_dir


def test_latest_journal_summary_reports_missing_without_runs_root(tmp_path: Path) -> None:
    _write_fixture(tmp_path)

    summary = latest_journal_summary(tmp_path, "runner_demo")

    assert summary["schema"] == "figure-agent.fig-run-journal-summary.v1"
    assert summary["state"] == "missing"
    assert summary["authoritative"] is False
    assert summary["replay_allowed"] is False
    assert summary["next_live_commands"] == [
        "/fig_status runner_demo",
        "/fig_drive runner_demo --mode review --goal 'close loop' --dry-run",
    ]


def test_latest_journal_summary_selects_newest_valid_fixture_journal(
    tmp_path: Path,
) -> None:
    example_dir = _write_fixture(tmp_path)
    old_time = time.time() - 20
    new_time = time.time() - 10
    _touch_fixture_evidence(example_dir, old_time - 10)
    _write_run_journal(
        tmp_path,
        run_id="20260601-010000-old",
        final_stop_reason="plan_only",
        mtime=old_time,
    )
    (tmp_path / ".scratch" / "fig-run-runs" / "malformed").mkdir(parents=True)
    (
        tmp_path / ".scratch" / "fig-run-runs" / "malformed" / "run_manifest.json"
    ).write_text("{not json", encoding="utf-8")
    _write_run_journal(
        tmp_path,
        run_id="20260601-010500-other",
        fixture="other_fixture",
        mtime=new_time + 5,
    )
    newest = _write_run_journal(
        tmp_path,
        run_id="20260601-011000-new",
        final_stop_reason="host_boundary",
        mtime=new_time,
    )

    summary = latest_journal_summary(tmp_path, "runner_demo")

    assert summary["state"] == "available"
    assert summary["run_dir"] == str(newest)
    assert summary["final_stop_reason"] == "host_boundary"
    assert summary["required_actor"] == "host_llm"
    assert summary["closeout_checks"] == [
        "write or refresh critique.md",
        "rerun live /fig_status",
        "rerun live /fig_drive",
    ]
    assert "final_safe_command" not in summary
    assert summary["resume_command"] is None


def test_latest_journal_summary_marks_journal_stale_when_fixture_evidence_is_newer(
    tmp_path: Path,
) -> None:
    example_dir = _write_fixture(tmp_path)
    old_time = time.time() - 20
    new_time = time.time()
    _touch_fixture_evidence(example_dir, old_time - 10)
    _write_run_journal(tmp_path, run_id="20260601-010000-old", mtime=old_time)
    os.utime(example_dir / "briefing.md", (new_time, new_time))

    summary = latest_journal_summary(tmp_path, "runner_demo")

    assert summary["state"] == "stale"
    assert summary["authoritative"] is False
    assert summary["stale_against"] == ["examples/runner_demo/briefing.md"]
    assert summary["next_live_commands"][0] == "/fig_status runner_demo"


def test_latest_journal_summary_marks_external_review_evidence_newer_as_stale(
    tmp_path: Path,
) -> None:
    example_dir = _write_fixture(tmp_path)
    old_time = time.time() - 20
    new_time = time.time()
    _touch_fixture_evidence(example_dir, old_time - 10)
    _write_run_journal(tmp_path, run_id="20260601-010000-old", mtime=old_time)
    external_review = example_dir / "external_vision_review.yaml"
    external_review.write_text("schema: figure-agent.external-vision-review.v1\n")
    os.utime(external_review, (new_time, new_time))

    summary = latest_journal_summary(tmp_path, "runner_demo")

    assert summary["state"] == "stale"
    assert summary["stale_against"] == [
        "examples/runner_demo/external_vision_review.yaml"
    ]


def test_latest_journal_summary_marks_inspection_trace_newer_as_stale(
    tmp_path: Path,
) -> None:
    example_dir = _write_fixture(tmp_path)
    old_time = time.time() - 20
    new_time = time.time()
    _touch_fixture_evidence(example_dir, old_time - 10)
    _write_run_journal(tmp_path, run_id="20260601-010000-old", mtime=old_time)
    inspection_trace = example_dir / "inspection_trace.yaml"
    inspection_trace.write_text("inspection_trace:\n  schema: figure-agent.inspection-trace.v1\n")
    os.utime(inspection_trace, (new_time, new_time))

    summary = latest_journal_summary(tmp_path, "runner_demo")

    assert summary["state"] == "stale"
    assert summary["stale_against"] == [
        "examples/runner_demo/inspection_trace.yaml"
    ]


def test_latest_journal_summary_marks_svg_polish_sidecar_newer_as_stale(
    tmp_path: Path,
) -> None:
    example_dir = _write_fixture(tmp_path)
    old_time = time.time() - 20
    new_time = time.time()
    _touch_fixture_evidence(example_dir, old_time - 10)
    _write_run_journal(tmp_path, run_id="20260601-010000-old", mtime=old_time)
    polish_dir = example_dir / "polish"
    polish_dir.mkdir()
    manifest = polish_dir / "svg_polish_manifest.yaml"
    manifest.write_text("schema: figure-agent.svg-polish-manifest.v1\n")
    os.utime(manifest, (new_time, new_time))

    summary = latest_journal_summary(tmp_path, "runner_demo")

    assert summary["state"] == "stale"
    assert summary["stale_against"] == [
        "examples/runner_demo/polish/svg_polish_manifest.yaml"
    ]

    delta_manifest = polish_dir / "aesthetic_delta" / "delta_manifest.json"
    delta_manifest.parent.mkdir()
    delta_manifest.write_text('{"schema": "figure-agent.svg-polish-delta.v1"}\n')
    os.utime(delta_manifest, (new_time, new_time))

    summary = latest_journal_summary(tmp_path, "runner_demo")

    assert summary["stale_against"] == [
        "examples/runner_demo/polish/aesthetic_delta/delta_manifest.json",
        "examples/runner_demo/polish/svg_polish_manifest.yaml",
    ]


def test_latest_journal_summary_uses_custom_runs_root(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    runs_root = tmp_path / "custom-runs"
    run_dir = _write_run_journal(
        tmp_path,
        run_id="20260601-010000-runner_demo",
        mtime=time.time(),
    )
    runs_root.mkdir()
    moved = runs_root / run_dir.name
    run_dir.rename(moved)

    summary = latest_journal_summary(tmp_path, "runner_demo", runs_root=runs_root)

    assert summary["state"] == "available"
    assert summary["run_dir"] == str(moved)


def test_latest_journal_summary_does_not_follow_unsafe_run_json_path(
    tmp_path: Path,
) -> None:
    example_dir = _write_fixture(tmp_path)
    _touch_fixture_evidence(example_dir, time.time() - 30)
    run_dir = _write_run_journal(
        tmp_path,
        run_id="20260601-010000-runner_demo",
        mtime=time.time() - 10,
    )
    manifest_path = run_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["run_json"] = "../outside.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    summary = latest_journal_summary(tmp_path, "runner_demo")

    assert summary["state"] == "available"
    assert summary["run_path"] is None
    assert summary["required_actor"] is None
    assert summary["closeout_checks"] == []


def test_cli_prints_latest_journal_summary_json(
    tmp_path: Path,
    capsys,
) -> None:
    _write_fixture(tmp_path)
    runs_root = tmp_path / "custom-runs"
    run_dir = _write_run_journal(
        tmp_path,
        run_id="20260601-010000-runner_demo",
        mtime=time.time(),
    )
    runs_root.mkdir()
    moved = runs_root / run_dir.name
    run_dir.rename(moved)

    result = main(
        [
            "runner_demo",
            "--repo-root",
            str(tmp_path),
            "--runs-root",
            str(runs_root),
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.fig-run-journal-summary.v1"
    assert payload["run_dir"] == str(moved)
