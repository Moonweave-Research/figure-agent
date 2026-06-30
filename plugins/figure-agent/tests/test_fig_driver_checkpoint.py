from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_driver_checkpoint import latest_loop_checkpoint  # noqa: E402


def _write_basic_fixture(root: Path, name: str = "driver_demo") -> Path:
    fixture = root / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(f"name: {name}\npanels: []\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text("% tikz\n", encoding="utf-8")
    build = fixture / "build"
    build.mkdir()
    (build / f"{name}.pdf").write_bytes(b"%PDF-1.4 checkpoint")
    return fixture


def _write_loop_run(
    repo_root: Path,
    *,
    name: str = "driver_demo",
    run_id: str,
    stop_reason: str,
    fixture_name: str | None = None,
    recommended_next_action: str = "inspect figure state",
    top_tier_audit_summary: dict[str, Any] | None = None,
    editorial_art_direction_summary: dict[str, Any] | None = None,
    aesthetic_lever_summary: dict[str, Any] | None = None,
    journal_art_direction_playbook_summary: dict[str, Any] | None = None,
    next_action_summary: dict[str, Any] | None = None,
    mtime: float | None = None,
) -> Path:
    run_dir = repo_root / ".scratch" / "fig-loop-runs" / run_id
    run_dir.mkdir(parents=True)
    manifest = {
        "schema": "figure-agent.fig-loop-run.v1",
        "fixture": fixture_name or name,
        "mode": "verify-only",
        "goal": "loop",
        "run_dir": str(run_dir),
        "final_stop_reason": stop_reason,
        "iterations": ["iteration_001.json"],
    }
    iteration = {
        "iteration": 1,
        "stop_reason": stop_reason,
        "escalation_level": "agent_action_required",
        "patch_handoff": None,
        "recommended_next_action": recommended_next_action,
    }
    if top_tier_audit_summary is not None:
        iteration["top_tier_audit_summary"] = top_tier_audit_summary
    if editorial_art_direction_summary is not None:
        iteration["editorial_art_direction_summary"] = editorial_art_direction_summary
    if aesthetic_lever_summary is not None:
        iteration["aesthetic_lever_summary"] = aesthetic_lever_summary
    if journal_art_direction_playbook_summary is not None:
        iteration["journal_art_direction_playbook_summary"] = (
            journal_art_direction_playbook_summary
        )
    if next_action_summary is not None:
        iteration["next_action_summary"] = next_action_summary
    manifest_path = run_dir / "run_manifest.json"
    iteration_path = run_dir / "iteration_001.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    iteration_path.write_text(json.dumps(iteration), encoding="utf-8")
    if mtime is not None:
        os.utime(manifest_path, (mtime, mtime))
        os.utime(iteration_path, (mtime, mtime))
    return run_dir


def test_latest_loop_checkpoint_ignores_malformed_or_wrong_fixture_runs(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    malformed = tmp_path / ".scratch" / "fig-loop-runs" / "20260521-malformed"
    malformed.mkdir(parents=True)
    (malformed / "run_manifest.json").write_text("{not json", encoding="utf-8")
    _write_loop_run(
        tmp_path,
        run_id="20260521-120000-000000-other_fixture",
        stop_reason="human_gate_required",
        fixture_name="other_fixture",
        mtime=time.time() + 10,
    )

    checkpoint = latest_loop_checkpoint(tmp_path, "driver_demo", fixture)

    assert checkpoint is None


def test_latest_loop_checkpoint_ignores_runs_without_stop_reason(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    run_dir = _write_loop_run(
        tmp_path,
        run_id="20260521-120000-000000-driver_demo",
        stop_reason="status_action_required",
        mtime=time.time() + 10,
    )
    manifest_path = run_dir / "run_manifest.json"
    iteration_path = run_dir / "iteration_001.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    iteration = json.loads(iteration_path.read_text(encoding="utf-8"))
    manifest["final_stop_reason"] = ""
    iteration["stop_reason"] = ""
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    iteration_path.write_text(json.dumps(iteration), encoding="utf-8")

    checkpoint = latest_loop_checkpoint(tmp_path, "driver_demo", fixture)

    assert checkpoint is None


def test_latest_loop_checkpoint_ignores_checkpoint_older_than_fixture_evidence(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    old_time = time.time() - 100
    new_time = time.time()
    _write_loop_run(
        tmp_path,
        run_id="20260521-120000-000000-driver_demo",
        stop_reason="patch_target_recommended",
        mtime=old_time,
    )
    adjudication = fixture / "critique_adjudication.yaml"
    adjudication.write_text("schema: figure-agent.critique-adjudication.v1\n", encoding="utf-8")
    os.utime(adjudication, (new_time, new_time))

    checkpoint = latest_loop_checkpoint(tmp_path, "driver_demo", fixture)

    assert checkpoint is None


def test_latest_loop_checkpoint_selects_newest_current_run_and_preserves_summaries(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    old_time = time.time() + 10
    new_time = time.time() + 20
    _write_loop_run(
        tmp_path,
        run_id="20260521-120000-000000-driver_demo",
        stop_reason="status_action_required",
        recommended_next_action="old action",
        mtime=old_time,
    )
    top_tier_summary = {"worst_verdict": "needs_human"}
    editorial_summary = {"polish_recommended_path": "ready_for_svg_polish"}
    aesthetic_summary = {"evaluation_state": "needs_patch"}
    journal_summary = {"evaluation_state": "needs_patch"}
    next_action_summary = {
        "schema": "figure-agent.next-action-summary.v1",
        "action": "complete",
        "decision_boundary": {"blocks_progress": False},
    }
    newest = _write_loop_run(
        tmp_path,
        run_id="20260521-130000-000000-driver_demo",
        stop_reason="verify_only_complete",
        recommended_next_action="new action",
        top_tier_audit_summary=top_tier_summary,
        editorial_art_direction_summary=editorial_summary,
        aesthetic_lever_summary=aesthetic_summary,
        journal_art_direction_playbook_summary=journal_summary,
        next_action_summary=next_action_summary,
        mtime=new_time,
    )

    checkpoint = latest_loop_checkpoint(tmp_path, "driver_demo", fixture)

    assert checkpoint == {
        "run_dir": str(newest),
        "manifest_path": str(newest / "run_manifest.json"),
        "iteration_path": str(newest / "iteration_001.json"),
        "final_stop_reason": "verify_only_complete",
        "escalation_level": "agent_action_required",
        "patch_handoff": None,
        "recommended_next_action": "new action",
        "top_tier_audit_summary": top_tier_summary,
        "editorial_art_direction_summary": editorial_summary,
        "aesthetic_lever_summary": aesthetic_summary,
        "journal_art_direction_playbook_summary": journal_summary,
        "next_action_summary": next_action_summary,
    }
