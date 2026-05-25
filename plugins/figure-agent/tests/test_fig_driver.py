from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_driver  # noqa: E402
import status as status_mod  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402


@pytest.fixture(autouse=True)
def _stub_export_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace qpdf-dependent compute_export_state with a filesystem-only stub.

    Same pattern as tests/test_status.py: stub PDFs cannot be hashed via qpdf,
    so freshness is inferred from artifact presence alone.
    """

    def _stub(example_dir: Path, name: str) -> str:
        exports_dir = example_dir / "exports"
        pdf = exports_dir / f"{name}.pdf"
        if not pdf.is_file():
            return "MISSING"
        svg = exports_dir / f"{name}.svg"
        png = exports_dir / f"{name}.png"
        tif = (exports_dir / f"{name}.tif").is_file() or (exports_dir / f"{name}.tiff").is_file()
        if not (svg.is_file() and png.is_file() and tif):
            return "STALE"
        return "FRESH"

    monkeypatch.setattr(status_mod, "compute_export_state", _stub)


def _write_basic_fixture(root: Path, name: str = "driver_demo") -> Path:
    fixture = root / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(f"name: {name}\npanels: []\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text("% tikz\n", encoding="utf-8")
    return fixture


def _write_fresh_build_and_exports(fixture: Path, name: str = "driver_demo") -> None:
    pdf_bytes = b"%PDF-1.4 driver"
    build = fixture / "build"
    build.mkdir(exist_ok=True)
    (build / f"{name}.pdf").write_bytes(pdf_bytes)
    exports = fixture / "exports"
    exports.mkdir(exist_ok=True)
    (exports / f"{name}.pdf").write_bytes(pdf_bytes)
    (exports / f"{name}.svg").write_text("<svg/>\n", encoding="utf-8")
    (exports / f"{name}.png").write_bytes(b"\x89PNG")
    (exports / f"{name}.tif").write_bytes(b"TIFF")
    old_time = time.time() - 100
    fresh_time = time.time() + 10
    for path in (fixture / "spec.yaml", fixture / "briefing.md", fixture / f"{name}.tex"):
        os.utime(path, (old_time, old_time))
    for path in [build / f"{name}.pdf", *exports.iterdir()]:
        os.utime(path, (fresh_time, fresh_time))


def _run_driver(name: str, *, mode: str, goal: str, repo_root: Path) -> dict[str, Any]:
    return fig_driver.build_driver_summary(name, mode=mode, goal=goal, repo_root=repo_root)


def _write_loop_run(
    repo_root: Path,
    *,
    name: str = "driver_demo",
    run_id: str = "20260519-120000-000000-driver_demo",
    stop_reason: str,
    escalation_level: str = "none",
    patch_handoff: dict[str, Any] | None = None,
    recommended_next_action: str = "inspect figure state",
    top_tier_audit_summary: dict[str, Any] | None = None,
    editorial_art_direction_summary: dict[str, Any] | None = None,
    crop_audit_summary: dict[str, Any] | None = None,
    aesthetic_lever_summary: dict[str, Any] | None = None,
    fixture_name: str | None = None,
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
        "escalation_level": escalation_level,
        "patch_handoff": patch_handoff,
        "recommended_next_action": recommended_next_action,
    }
    if top_tier_audit_summary is not None:
        iteration["top_tier_audit_summary"] = top_tier_audit_summary
    if editorial_art_direction_summary is not None:
        iteration["editorial_art_direction_summary"] = editorial_art_direction_summary
    if crop_audit_summary is not None:
        iteration["crop_audit_summary"] = crop_audit_summary
    if aesthetic_lever_summary is not None:
        iteration["aesthetic_lever_summary"] = aesthetic_lever_summary
    manifest_path = run_dir / "run_manifest.json"
    iteration_path = run_dir / "iteration_001.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    iteration_path.write_text(json.dumps(iteration), encoding="utf-8")
    checkpoint_time = time.time() + 20
    os.utime(manifest_path, (checkpoint_time, checkpoint_time))
    os.utime(iteration_path, (checkpoint_time, checkpoint_time))
    return run_dir


def _patch_handoff() -> dict[str, Any]:
    return {
        "target_type": "finding",
        "target_id": "C001",
        "patch_target": "Panel A label offset",
        "reason": "label overlaps the device frame",
        "allowed_edit_scope": ["examples/driver_demo/driver_demo.tex"],
        "forbidden_edit_scope": ["examples/driver_demo/exports/"],
        "required_closeout_checks": ["/fig_compile driver_demo"],
        "unresolved_findings_requirement": "preserve unresolved findings",
    }


def _release_ready_status(name: str = "driver_demo") -> dict[str, Any]:
    return {
        "stage": 4,
        "name": name,
        "notes": [],
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "FRESH",
        "acceptance_state": "ACCEPTED",
        "final_artifact_state": "NONE",
        "final_artifact_kind": "generated_export",
        "final_artifact_path": None,
        "workflow_ready": True,
        "golden_ready": True,
        "release_ready": True,
        "final_ready": True,
        "publication_gate_state": "OK",
        "publication_gate_failures": [],
    }


# --- CLI + JSON contract -----------------------------------------------------


def test_main_requires_dry_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_basic_fixture(tmp_path)

    result = fig_driver.main(
        ["driver_demo", "--mode", "review", "--goal", "review"], repo_root=tmp_path
    )

    captured = capsys.readouterr()
    assert result == 2
    assert "--dry-run is required" in captured.err
    assert captured.out == ""


def test_main_emits_json_summary_in_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_basic_fixture(tmp_path)

    result = fig_driver.main(
        [
            "driver_demo",
            "--mode",
            "authoring",
            "--goal",
            "tighten layout",
            "--dry-run",
        ],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.driver.v1"
    assert payload["fixture"] == "driver_demo"
    assert payload["mode"] == "authoring"
    assert payload["goal"] == "tighten layout"
    assert payload["may_execute"] is False
    assert isinstance(payload["status"], dict)
    assert isinstance(payload["forbidden_actions"], list)
    assert isinstance(payload["workspace_warnings"], list)
    for key in ("action", "safe_command", "stop_boundary", "reason"):
        assert key in payload


def test_driver_summary_includes_status_explanation_and_first_blocker_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    synthetic_status = _release_ready_status()
    synthetic_status.update(
        {
            "export_state": "MISSING",
            "release_ready": False,
            "status_explanation": {
                "summary": "exports are missing.",
                "first_blocker": {
                    "code": "export_missing",
                    "category": "fixture_freshness",
                    "message": "exports are missing.",
                    "next_command": "/fig_export driver_demo",
                    "manual": False,
                },
                "buckets": {
                    "plugin_state": [],
                    "fixture_freshness": [
                        {
                            "code": "export_missing",
                            "category": "fixture_freshness",
                            "message": "exports are missing.",
                            "next_command": "/fig_export driver_demo",
                            "manual": False,
                        }
                    ],
                    "human_blockers": [],
                },
            },
        }
    )
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["status_explanation"]["first_blocker"]["code"] == "export_missing"
    assert "first blocker export_missing" in summary["reason"]
    assert summary["safe_command"] == "uv run python3 scripts/run_export.py driver_demo"


def test_driver_compact_status_includes_critique_lint_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    synthetic_status = _release_ready_status()
    synthetic_status.update(
        {
            "critique_state": "FRESH",
            "critique_lint_summary": {
                "state": "blocked",
                "violation_count": 1,
                "first_category": "aesthetic_intent_accounting",
                "first_message": "missing aesthetic anchor",
            },
        }
    )
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["status"]["critique_lint_summary"] == {
        "state": "blocked",
        "violation_count": 1,
        "first_category": "aesthetic_intent_accounting",
        "first_message": "missing aesthetic anchor",
    }


def test_driver_summary_includes_actionable_audit_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    synthetic_status = _release_ready_status()
    synthetic_status.update(
        {
            "release_ready": False,
            "critique_state": "FRESH",
            "audit_evidence": {
                "schema": "figure-agent.audit-evidence-summary.v1",
                "fixture": "driver_demo",
                "critique_schema": "figure-agent.critique.v1.10",
                "evaluation_state": "needs_action",
                "blocking_items": ["VC050"],
                "next_action": "/fig_critique driver_demo",
                "reason": "visual-clash candidates are not fully accounted",
            },
        }
    )
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["audit_evidence"]["evaluation_state"] == "needs_action"
    assert summary["audit_evidence"]["blocking_items"] == ["VC050"]
    assert "audit evidence needs_action" in summary["reason"]
    assert summary["action"] == "run_fig_loop"


def test_authoring_mode_explains_source_before_export_for_un_authored_fixture(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "examples" / "driver_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: driver_demo\npanels: []\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("brief\n", encoding="utf-8")

    summary = _run_driver("driver_demo", mode="authoring", goal="author", repo_root=tmp_path)

    assert summary["action"] == "create_or_fix_source"
    assert summary["status_explanation"]["first_blocker"]["code"] == "source_not_authored"
    assert "first blocker export_missing" not in summary["reason"]


def test_driver_summary_surfaces_workspace_warnings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_basic_fixture(tmp_path)
    monkeypatch.setattr(
        fig_driver,
        "_workspace_warnings",
        lambda _repo_root: ["tracked_worktree_dirty: plugins/figure-agent/scripts/foo.py"],
        raising=False,
    )

    summary = _run_driver("driver_demo", mode="authoring", goal="author", repo_root=tmp_path)

    assert summary["workspace_warnings"] == [
        "tracked_worktree_dirty: plugins/figure-agent/scripts/foo.py"
    ]


def test_workspace_warnings_report_tracked_dirty_paths(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    tracked = tmp_path / "plugins" / "figure-agent" / "scripts" / "foo.py"
    tracked.parent.mkdir(parents=True)
    tracked.write_text("before\n", encoding="utf-8")
    subprocess.run(["git", "add", str(tracked.relative_to(tmp_path))], cwd=tmp_path, check=True)
    tracked.write_text("after\n", encoding="utf-8")

    warnings = fig_driver._workspace_warnings(tmp_path)

    assert warnings == [
        "tracked_worktree_dirty: plugins/figure-agent/scripts/foo.py"
    ]


def test_unsupported_mode_fails_cleanly(tmp_path: Path) -> None:
    _write_basic_fixture(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        fig_driver.main(
            [
                "driver_demo",
                "--mode",
                "executive",
                "--goal",
                "x",
                "--dry-run",
            ],
            repo_root=tmp_path,
        )

    assert exc_info.value.code == 2


# --- authoring mode ----------------------------------------------------------


def test_authoring_mode_recommends_compile_when_render_missing(tmp_path: Path) -> None:
    _write_basic_fixture(tmp_path)

    summary = _run_driver("driver_demo", mode="authoring", goal="author", repo_root=tmp_path)

    assert summary["action"] == "run_compile"
    assert summary["safe_command"] == "bash scripts/compile.sh examples/driver_demo/driver_demo.tex"
    assert summary["stop_boundary"] is None


def test_authoring_mode_completes_when_render_fresh(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="authoring", goal="author", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] is None


# --- review mode -------------------------------------------------------------


def test_review_mode_stops_for_reference_missing(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    (fixture / "spec.yaml").write_text(
        "name: driver_demo\nreference_image: reference/missing.png\npanels: []\n",
        encoding="utf-8",
    )
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_critique"
    assert summary["stop_boundary"] == "reference_missing"
    assert summary["safe_command"] is None


def test_review_mode_stops_for_host_critique_when_critique_missing(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    reference = fixture / "reference" / "ref.png"
    reference.parent.mkdir()
    reference.write_bytes(b"\x89PNG")
    (fixture / "spec.yaml").write_text(
        "name: driver_demo\nreference_image: reference/ref.png\npanels: []\n",
        encoding="utf-8",
    )
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_critique"
    assert summary["stop_boundary"] == "host_llm_critique_required"
    assert summary["safe_command"] == "/fig_critique driver_demo"


def test_review_mode_recommends_adjudicate_when_critique_fresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    synthetic_status = {
        "stage": 4,
        "name": "driver_demo",
        "notes": [],
        "render_state": "FRESH",
        "critique_state": "FRESH",
        "export_state": "FRESH",
        "acceptance_state": "NOT_DECLARED",
        "final_artifact_state": "NONE",
        "final_artifact_kind": "generated_export",
        "final_artifact_path": None,
        "workflow_ready": True,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: True)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_adjudicate"
    assert summary["stop_boundary"] is None
    assert (
        summary["safe_command"]
        == "uv run python3 scripts/critique_adjudication.py scaffold driver_demo"
    )


def test_review_mode_runs_fig_loop_when_prerequisites_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_fig_loop"
    assert (
        summary["safe_command"]
        == "uv run python3 scripts/fig_loop.py driver_demo --goal review --json"
    )
    assert summary["stop_boundary"] is None


def test_review_mode_uses_closeout_next_action_before_rerunning_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    monkeypatch.setattr(
        fig_driver.closeout_mod,
        "closeout_report",
        lambda _name, repo_root: {
            "closeout_complete": False,
            "next_action": '/fig_loop driver_demo --goal "<goal>"',
            "blocking_step_ids": ["loop_rerun"],
            "steps": [
                {
                    "id": "loop_rerun",
                    "state": "needs_action",
                    "command": '/fig_loop driver_demo --goal "<goal>"',
                }
            ],
        },
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_fig_loop"
    assert (
        summary["safe_command"]
        == "uv run python3 scripts/fig_loop.py driver_demo --goal review --json"
    )
    assert summary["stop_boundary"] == "closeout_required"
    assert summary["closeout"]["blocking_step_ids"] == ["loop_rerun"]
    assert "closeout is incomplete" in summary["reason"]


def test_review_mode_uses_closeout_export_action_before_rerunning_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    monkeypatch.setattr(
        fig_driver.closeout_mod,
        "closeout_report",
        lambda _name, repo_root: {
            "closeout_complete": False,
            "next_action": "/fig_export driver_demo",
            "blocking_step_ids": ["export"],
            "steps": [
                {"id": "export", "state": "needs_action", "command": "/fig_export driver_demo"}
            ],
        },
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_export"
    assert summary["safe_command"] == "uv run python3 scripts/run_export.py driver_demo"
    assert summary["stop_boundary"] == "closeout_required"
    assert summary["closeout"]["next_action"] == "/fig_export driver_demo"


def test_review_mode_detects_real_closeout_export_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    (fixture / "exports" / "driver_demo.png").unlink()
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_export"
    assert summary["safe_command"] == "uv run python3 scripts/run_export.py driver_demo"
    assert summary["stop_boundary"] == "closeout_required"
    assert summary["closeout"]["blocking_step_ids"] == ["export", "loop_rerun"]


def test_review_mode_closeout_keeps_tracked_golden_manual(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    monkeypatch.setattr(
        fig_driver.closeout_mod,
        "closeout_report",
        lambda _name, repo_root: {
            "closeout_complete": False,
            "next_action": "tracked golden export requires deliberate manual approval",
            "blocking_step_ids": ["export"],
            "steps": [
                {
                    "id": "export",
                    "state": "blocked",
                    "command": None,
                    "evidence": {"approval_command": "/fig_export driver_demo --force-golden"},
                }
            ],
        },
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "release_blocked"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "force_golden_required"
    assert "--force-golden" not in json.dumps(summary["safe_command"])
    assert summary["closeout"]["blocking_step_ids"] == ["export"]


def test_review_mode_closeout_unknown_next_action_stops_without_guessing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    monkeypatch.setattr(
        fig_driver.closeout_mod,
        "closeout_report",
        lambda _name, repo_root: {
            "closeout_complete": False,
            "next_action": "critique_adjudication.yaml is invalid: bad yaml",
            "blocking_step_ids": ["adjudication"],
            "steps": [
                {
                    "id": "adjudication",
                    "state": "needs_action",
                    "command": None,
                    "reason": "critique_adjudication.yaml is invalid: bad yaml",
                }
            ],
        },
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "closeout_required"
    assert "bad yaml" in summary["reason"]


def test_review_mode_ignores_complete_closeout_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    monkeypatch.setattr(
        fig_driver.closeout_mod,
        "closeout_report",
        lambda _name, repo_root: {
            "closeout_complete": True,
            "next_action": "closeout complete",
            "blocking_step_ids": [],
            "steps": [],
        },
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_fig_loop"
    assert "closeout" not in summary


def test_review_mode_fig_loop_goal_is_shell_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)

    summary = _run_driver("driver_demo", mode="review", goal="it's a goal", repo_root=tmp_path)

    assert summary["action"] == "run_fig_loop"
    assert (
        summary["safe_command"]
        == "uv run python3 scripts/fig_loop.py driver_demo --goal 'it'\"'\"'s a goal' --json"
    )


def test_review_mode_surfaces_latest_loop_patch_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    run_dir = _write_loop_run(
        tmp_path,
        stop_reason="patch_target_recommended",
        escalation_level="patch_allowed",
        patch_handoff=_patch_handoff(),
        recommended_next_action="patch C001: Panel A label offset",
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "patch_handoff_stop"
    assert summary["stop_boundary"] == "patch_handoff_required"
    assert summary["safe_command"] is None
    assert summary["loop_checkpoint"]["run_dir"] == str(run_dir)
    assert summary["loop_checkpoint"]["patch_handoff"]["target_id"] == "C001"


def test_review_mode_patch_handoff_takes_priority_over_closeout_export_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    monkeypatch.setattr(
        fig_driver.closeout_mod,
        "closeout_report",
        lambda _name, repo_root: {
            "closeout_complete": False,
            "next_action": "/fig_export driver_demo",
            "blocking_step_ids": ["export"],
            "steps": [
                {"id": "export", "state": "needs_action", "command": "/fig_export driver_demo"}
            ],
        },
    )
    _write_loop_run(
        tmp_path,
        stop_reason="patch_target_recommended",
        escalation_level="patch_allowed",
        patch_handoff=_patch_handoff(),
        recommended_next_action="patch C001 before export closeout",
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "patch_handoff_stop"
    assert summary["stop_boundary"] == "patch_handoff_required"
    assert summary["safe_command"] is None
    assert "closeout" not in summary


def test_review_mode_surfaces_latest_loop_ambiguous_patch_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    _write_loop_run(
        tmp_path,
        stop_reason="ambiguous_patch_selection",
        escalation_level="ambiguous_patch_selection",
        recommended_next_action="select exactly one apply decision",
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "patch_handoff_stop"
    assert summary["stop_boundary"] == "ambiguous_patch_selection"
    assert "select exactly one" in summary["reason"]


def test_review_mode_surfaces_latest_loop_human_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    _write_loop_run(
        tmp_path,
        stop_reason="human_gate_required",
        escalation_level="human_review_required",
        recommended_next_action="human review required for C002",
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["stop_boundary"] == "human_gate_required"
    assert summary["safe_command"] is None


def test_review_mode_completes_after_latest_clean_loop_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        recommended_next_action="inspect figure state",
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] is None
    assert summary["loop_checkpoint"]["final_stop_reason"] == "verify_only_complete"


def test_review_mode_surfaces_uncertain_crop_audit_from_latest_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    crop_audit_summary = {
        "source": "critique.crop_audit_log",
        "crop_count": 2,
        "verdict_counts": {"defect": 0, "no_defect": 1, "uncertain": 1},
        "defect_crop_ids": [],
        "uncertain_crop_ids": ["VC001_A"],
        "evaluation_state": "needs_action",
    }
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        recommended_next_action="inspect figure state",
        crop_audit_summary=crop_audit_summary,
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["stop_boundary"] == "human_gate_required"
    assert summary["safe_command"] is None
    assert "uncertain crop audit" in summary["reason"]
    assert "VC001_A" in summary["reason"]
    assert summary["loop_checkpoint"]["crop_audit_summary"] == crop_audit_summary


def test_review_mode_does_not_block_on_passed_crop_audit_from_latest_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        recommended_next_action="inspect figure state",
        crop_audit_summary={
            "source": "critique.crop_audit_log",
            "crop_count": 2,
            "verdict_counts": {"defect": 0, "no_defect": 2, "uncertain": 0},
            "defect_crop_ids": [],
            "uncertain_crop_ids": [],
            "evaluation_state": "passed",
        },
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] is None


def test_review_mode_surfaces_top_tier_audit_blockers_from_latest_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    audit_summary = {
        "schema": "figure-agent.top-tier-audit-summary.v1",
        "worst_verdict": "needs_human",
        "verdict_counts": {"pass": 7, "weak": 2, "fail": 1, "needs_human": 1},
        "blocking_high_impact_count": 1,
    }
    _write_loop_run(
        tmp_path,
        stop_reason="status_action_required",
        escalation_level="agent_action_required",
        recommended_next_action="run /fig_export driver_demo",
        top_tier_audit_summary=audit_summary,
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["stop_boundary"] == "human_gate_required"
    assert summary["safe_command"] is None
    assert "top-tier audit" in summary["reason"]
    assert summary["loop_checkpoint"]["top_tier_audit_summary"] == audit_summary


def test_review_mode_top_tier_blocker_takes_priority_over_force_golden(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    _write_loop_run(
        tmp_path,
        stop_reason="status_action_required",
        escalation_level="manual_approval_required",
        recommended_next_action="run /fig_export driver_demo --force-golden",
        top_tier_audit_summary={
            "schema": "figure-agent.top-tier-audit-summary.v1",
            "worst_verdict": "fail",
            "verdict_counts": {"pass": 8, "weak": 1, "fail": 1, "needs_human": 0},
            "blocking_high_impact_count": 0,
        },
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["stop_boundary"] == "human_gate_required"
    assert summary["safe_command"] is None


def test_review_mode_does_not_block_on_nonblocking_top_tier_audit_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        recommended_next_action="inspect figure state",
        top_tier_audit_summary={
            "schema": "figure-agent.top-tier-audit-summary.v1",
            "worst_verdict": "weak",
            "verdict_counts": {"pass": 8, "weak": 2, "fail": 0, "needs_human": 0},
            "blocking_high_impact_count": 0,
        },
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] is None


def test_review_mode_surfaces_editorial_human_gate_from_latest_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    editorial_summary = {
        "source": "critique.editorial_art_direction",
        "worst_verdict": "needs_human",
        "verdict_counts": {"pass": 9, "weak": 0, "fail": 0, "needs_human": 1},
        "blocking_high_impact_count": 0,
        "polish_recommended_path": "needs_human_art_direction",
    }
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary=editorial_summary,
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["stop_boundary"] == "human_gate_required"
    assert summary["safe_command"] is None
    assert "editorial art-direction" in summary["reason"]
    assert summary["loop_checkpoint"]["editorial_art_direction_summary"] == editorial_summary


def test_review_mode_ignores_malformed_or_wrong_fixture_loop_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    malformed = tmp_path / ".scratch" / "fig-loop-runs" / "20260519-malformed-driver_demo"
    malformed.mkdir(parents=True)
    (malformed / "run_manifest.json").write_text("{not json", encoding="utf-8")
    _write_loop_run(
        tmp_path,
        run_id="20260519-130000-000000-other_fixture",
        stop_reason="human_gate_required",
        escalation_level="human_review_required",
        fixture_name="other_fixture",
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_fig_loop"
    assert "loop_checkpoint" not in summary


def test_review_mode_ignores_loop_checkpoint_older_than_adjudication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    run_dir = _write_loop_run(
        tmp_path,
        stop_reason="patch_target_recommended",
        escalation_level="patch_allowed",
        patch_handoff=_patch_handoff(),
    )
    old_time = time.time() - 100
    new_time = time.time()
    os.utime(run_dir / "run_manifest.json", (old_time, old_time))
    os.utime(run_dir / "iteration_001.json", (old_time, old_time))
    adjudication = fixture / "critique_adjudication.yaml"
    adjudication.write_text("schema: figure-agent.critique-adjudication.v1\n", encoding="utf-8")
    os.utime(adjudication, (new_time, new_time))

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_fig_loop"
    assert "loop_checkpoint" not in summary


# --- release mode ------------------------------------------------------------


def test_release_mode_reports_release_blocked_without_mutation(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "release_blocked"
    assert summary["stop_boundary"] == "accepted_or_final_ready_required"
    assert summary["may_execute"] is False
    assert summary["safe_command"] is None


def test_release_mode_ignores_reference_calibrated_score_for_gate_selection(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    status = _release_ready_status()
    status.update(
        {
            "acceptance_state": "NOT_ACCEPTED",
            "golden_ready": False,
            "release_ready": False,
            "final_ready": False,
        }
    )
    loop_checkpoint = {
        "final_stop_reason": "verify_only_complete",
        "journal_grade_assessment": {
            "overall_score": 99,
            "score_is_gateable": True,
            "score_policy": "advisory_fresh_reaudit_not_gate",
            "reference_calibration_summary": {
                "reference_pack_hash": "sha256:" + "b" * 64,
                "reference_class": "mechanism_schematic",
                "visual_ambition": "high_impact_candidate",
                "score_basis": "current_artifact_vs_pack",
                "limiting_reference_trait_count": 1,
            },
        },
    }

    summary = fig_driver._select_action(
        "driver_demo",
        mode="release",
        goal="release",
        status=status,
        example_dir=fixture,
        loop_checkpoint=loop_checkpoint,
    )

    assert summary["action"] == "release_blocked"
    assert summary["stop_boundary"] == "accepted_or_final_ready_required"
    assert "release_ready is false" in summary["reason"]


def test_release_mode_surfaces_publication_gate_blocker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    synthetic_status = {
        "stage": 4,
        "name": "driver_demo",
        "notes": [],
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "FRESH",
        "acceptance_state": "NOT_ACCEPTED",
        "final_artifact_state": "NONE",
        "final_artifact_kind": "generated_export",
        "final_artifact_path": None,
        "workflow_ready": True,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
        "publication_gate_state": "HUMAN_ACCEPTANCE_REQUIRED",
        "publication_gate_failures": [
            {
                "code": "missing_quality_audit",
                "category": "quality_audit_stale",
                "actor": "agent",
                "message": "missing audit: QUALITY_AUDIT.md",
                "required_action": "create QUALITY_AUDIT.md from the publication audit scaffold",
            }
        ],
    }
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "release_blocked"
    assert summary["stop_boundary"] == "accepted_or_final_ready_required"
    assert "publication gate" in summary["reason"]
    assert "missing_quality_audit" in summary["reason"]
    assert ".. Driver" not in summary["reason"]
    assert summary["status"]["publication_gate_state"] == "HUMAN_ACCEPTANCE_REQUIRED"
    assert summary["status"]["publication_gate_failures"][0]["actor"] == "agent"


def test_release_mode_publication_gate_blocks_even_when_release_ready_is_true(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    synthetic_status = {
        "stage": 4,
        "name": "driver_demo",
        "notes": [],
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "FRESH",
        "acceptance_state": "ACCEPTED",
        "final_artifact_state": "NONE",
        "final_artifact_kind": "generated_export",
        "final_artifact_path": None,
        "workflow_ready": True,
        "golden_ready": True,
        "release_ready": True,
        "final_ready": True,
        "publication_gate_state": "PROVENANCE_REQUIRED",
        "publication_gate_failures": [
            {
                "code": "missing_submission_safe_true",
                "category": "publication_provenance",
                "actor": "human",
                "message": "QUALITY_AUDIT.md does not declare submission-safe: true",
                "required_action": "Human reviewer must decide submission safety.",
            }
        ],
    }
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "release_blocked"
    assert summary["stop_boundary"] == "accepted_or_final_ready_required"
    assert "missing_submission_safe_true" in summary["reason"]
    assert ".. Driver" not in summary["reason"]


def test_release_mode_requires_adjudication_before_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    release_ready_status = _release_ready_status()
    release_ready_status["critique_state"] = "FRESH"
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: release_ready_status)

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "run_adjudicate"
    assert summary["safe_command"] == (
        "uv run python3 scripts/critique_adjudication.py scaffold driver_demo"
    )
    assert summary["stop_boundary"] is None
    assert "critique_adjudication.yaml is missing or stale" in summary["reason"]
    assert summary["action"] not in summary["forbidden_actions"]


def test_release_mode_surfaces_latest_loop_human_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: _release_ready_status())
    _write_loop_run(
        tmp_path,
        stop_reason="human_gate_required",
        escalation_level="human_review_required",
        recommended_next_action="human review required for C002",
    )

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "human_gate_required"
    assert "human review required for C002" in summary["reason"]
    assert summary["loop_checkpoint"]["final_stop_reason"] == "human_gate_required"


def test_release_mode_surfaces_uncertain_crop_audit_from_latest_loop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: _release_ready_status())
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        escalation_level="none",
        crop_audit_summary={
            "source": "critique.crop_audit_log",
            "crop_count": 1,
            "verdict_counts": {"defect": 0, "no_defect": 0, "uncertain": 1},
            "defect_crop_ids": [],
            "uncertain_crop_ids": ["VC009_B"],
            "evaluation_state": "needs_action",
        },
    )

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "human_gate_required"
    assert "VC009_B" in summary["reason"]


def test_release_mode_surfaces_latest_loop_patch_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: _release_ready_status())
    _write_loop_run(
        tmp_path,
        stop_reason="patch_target_recommended",
        escalation_level="patch_allowed",
        patch_handoff=_patch_handoff(),
        recommended_next_action="patch C001",
    )

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "patch_handoff_stop"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "patch_handoff_required"
    assert "C001" in summary["reason"]
    assert summary["loop_checkpoint"]["patch_handoff"]["target_id"] == "C001"


def test_release_mode_completes_after_latest_clean_loop_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: _release_ready_status())
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        escalation_level="none",
        recommended_next_action="release is ready",
    )

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] is None
    assert summary["loop_checkpoint"]["final_stop_reason"] == "verify_only_complete"


def test_release_mode_preserves_aesthetic_lever_summary_from_latest_loop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: _release_ready_status())
    aesthetic_summary = {
        "source": "critique.aesthetic_lever_audit",
        "evaluation_state": "passed",
        "lever_count": 2,
        "worst_verdict": "pass",
    }
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        escalation_level="none",
        recommended_next_action="release is ready",
        aesthetic_lever_summary=aesthetic_summary,
    )

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["loop_checkpoint"]["aesthetic_lever_summary"] == aesthetic_summary


# --- polish mode -------------------------------------------------------------


def test_polish_mode_requires_current_export_before_polish(tmp_path: Path) -> None:
    _write_basic_fixture(tmp_path)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "run_compile"


def test_polish_mode_stops_for_polish_handoff_when_export_current(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "polish_handoff_stop"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] is None
    assert "polish/svg_polish_recipe.yaml" in summary["reason"]


def test_polish_mode_uses_editorial_ready_for_svg_polish_checkpoint(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    editorial_summary = {
        "source": "critique.editorial_art_direction",
        "worst_verdict": "pass",
        "polish_recommended_path": "ready_for_svg_polish",
    }
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary=editorial_summary,
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "polish_handoff_stop"
    assert summary["stop_boundary"] is None
    assert "ready_for_svg_polish" in summary["reason"]
    assert "polish/svg_polish_recipe.yaml" in summary["reason"]
    assert summary["safe_command"] is None
    assert summary["loop_checkpoint"]["editorial_art_direction_summary"] == editorial_summary


def test_polish_mode_with_recipe_returns_executor_dry_run_command(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    (fixture / "polish").mkdir()
    (fixture / "polish" / "svg_polish_recipe.yaml").write_text(
        "schema: figure-agent.svg-polish-recipe.v1\n",
        encoding="utf-8",
    )
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "pass",
            "polish_recommended_path": "ready_for_svg_polish",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "polish_handoff_stop"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] == (
        "uv run python3 scripts/svg_polish_executor.py examples/driver_demo --dry-run"
    )
    assert "svg_polish_executor.py" in summary["reason"]


def test_polish_mode_with_polished_svg_returns_delta_pack_command(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    polish = fixture / "polish"
    polish.mkdir()
    (polish / "svg_polish_recipe.yaml").write_text(
        "schema: figure-agent.svg-polish-recipe.v1\n",
        encoding="utf-8",
    )
    (polish / "driver_demo.polished.svg").write_text("<svg/>\n", encoding="utf-8")
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "pass",
            "polish_recommended_path": "ready_for_svg_polish",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "polish_handoff_stop"
    assert summary["stop_boundary"] is None
    assert "build_svg_polish_delta_pack" in summary["safe_command"]
    assert "aesthetic delta" in summary["reason"]


def test_polish_mode_with_delta_pack_returns_handoff_guidance(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    polish = fixture / "polish"
    delta = polish / "aesthetic_delta"
    delta.mkdir(parents=True)
    (polish / "svg_polish_recipe.yaml").write_text(
        "schema: figure-agent.svg-polish-recipe.v1\n",
        encoding="utf-8",
    )
    (polish / "driver_demo.polished.svg").write_text("<svg/>\n", encoding="utf-8")
    (delta / "before.png").write_bytes(b"before")
    (delta / "after.png").write_bytes(b"after")
    (delta / "diff.png").write_bytes(b"diff")
    (delta / "delta_manifest.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.svg-polish-delta.v1",
                "fixture": "driver_demo",
                "source_svg": "exports/driver_demo.svg",
                "polished_svg": "polish/driver_demo.polished.svg",
                "recipe": "polish/svg_polish_recipe.yaml",
                "source_svg_hash": file_sha256(fixture / "exports" / "driver_demo.svg"),
                "polished_svg_hash": file_sha256(polish / "driver_demo.polished.svg"),
                "recipe_hash": file_sha256(polish / "svg_polish_recipe.yaml"),
                "operation_ids": ["R001"],
                "artifacts": {
                    "before_png": "polish/aesthetic_delta/before.png",
                    "after_png": "polish/aesthetic_delta/after.png",
                    "diff_png": "polish/aesthetic_delta/diff.png",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "pass",
            "polish_recommended_path": "ready_for_svg_polish",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "polish_handoff_stop"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] is None
    assert "scripts/svg_polish_handoff.py" in summary["reason"]


def test_polish_mode_with_invalid_delta_pack_returns_delta_pack_command(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    polish = fixture / "polish"
    delta = polish / "aesthetic_delta"
    delta.mkdir(parents=True)
    (polish / "svg_polish_recipe.yaml").write_text(
        "schema: figure-agent.svg-polish-recipe.v1\n",
        encoding="utf-8",
    )
    (polish / "driver_demo.polished.svg").write_text("<svg/>\n", encoding="utf-8")
    (delta / "delta_manifest.json").write_text(
        '{"schema":"figure-agent.svg-polish-delta.v1"}\n',
        encoding="utf-8",
    )
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "pass",
            "polish_recommended_path": "ready_for_svg_polish",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "polish_handoff_stop"
    assert summary["stop_boundary"] is None
    assert "build_svg_polish_delta_pack" in summary["safe_command"]
    assert "delta pack is invalid" in summary["reason"]


def test_polish_mode_preserves_aesthetic_lever_summary_from_latest_loop(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    aesthetic_summary = {
        "source": "critique.aesthetic_lever_audit",
        "evaluation_state": "passed",
        "lever_count": 2,
        "worst_verdict": "pass",
    }
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        aesthetic_lever_summary=aesthetic_summary,
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "pass",
            "polish_recommended_path": "ready_for_svg_polish",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["loop_checkpoint"]["aesthetic_lever_summary"] == aesthetic_summary


def test_polish_mode_honors_latest_loop_human_gate_before_svg_handoff(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    _write_loop_run(
        tmp_path,
        stop_reason="human_gate_required",
        escalation_level="human_review_required",
        recommended_next_action="human art-direction review required for target_journal_taste",
        aesthetic_lever_summary={
            "source": "critique.aesthetic_lever_audit",
            "evaluation_state": "needs_human",
            "next_aesthetic_bottleneck": {
                "lever_id": "target_journal_taste",
                "route": "human_art_direction",
            },
        },
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "pass",
            "polish_recommended_path": "ready_for_svg_polish",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "human_gate_required"
    assert "target_journal_taste" in summary["reason"]


def test_polish_mode_honors_top_tier_blocker_before_svg_handoff(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        top_tier_audit_summary={
            "source": "critique.top_tier_audit",
            "worst_verdict": "weak",
            "blocking_high_impact_count": 1,
            "blocking_high_impact_slots": ["aesthetic_coherence"],
        },
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "pass",
            "polish_recommended_path": "ready_for_svg_polish",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "human_gate_required"
    assert "top-tier audit" in summary["reason"]


def test_polish_mode_routes_editorial_continue_tikz_back_to_loop(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "weak",
            "polish_recommended_path": "continue_tikz",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "run_fig_loop"
    assert summary["safe_command"] == (
        "uv run python3 scripts/fig_loop.py driver_demo --goal polish --json"
    )
    assert summary["stop_boundary"] == "mode_forbidden_action"
    assert "continue_tikz" in summary["reason"]


def test_polish_mode_routes_editorial_human_gate_to_human_stop(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "needs_human",
            "polish_recommended_path": "needs_human_art_direction",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "human_gate_required"
    assert "needs_human_art_direction" in summary["reason"]


def test_polish_mode_surfaces_uncertain_crop_audit_from_latest_loop(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        crop_audit_summary={
            "source": "critique.crop_audit_log",
            "crop_count": 1,
            "verdict_counts": {"defect": 0, "no_defect": 0, "uncertain": 1},
            "defect_crop_ids": [],
            "uncertain_crop_ids": ["print_178mm"],
            "evaluation_state": "needs_action",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "human_gate_required"
    assert "print_178mm" in summary["reason"]


def test_polish_mode_blocks_ready_path_when_editorial_slots_need_human(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "needs_human",
            "verdict_counts": {"pass": 9, "weak": 0, "fail": 0, "needs_human": 1},
            "blocking_high_impact_count": 0,
            "polish_recommended_path": "ready_for_svg_polish",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "human_gate_required"
    assert "editorial art-direction" in summary["reason"]


def test_polish_mode_routes_editorial_semantic_backport_to_boundary(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "fail",
            "polish_recommended_path": "semantic_backport_required",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "polish_handoff_stop"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "semantic_backport_required"
    assert "semantic_backport_required" in summary["reason"]


def test_polish_mode_reports_semantic_backport_required_for_blocked_final_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    synthetic_status = {
        "stage": 4,
        "name": "driver_demo",
        "notes": [],
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "FRESH",
        "acceptance_state": "NOT_DECLARED",
        "final_artifact_state": "BLOCKED",
        "final_artifact_kind": "polished_svg",
        "final_artifact_path": "polish/driver_demo.polished.svg",
        "workflow_ready": True,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "polish_handoff_stop"
    assert summary["stop_boundary"] == "semantic_backport_required"


def test_polish_mode_completes_when_polished_svg_is_fresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    synthetic_status = {
        "stage": 4,
        "name": "driver_demo",
        "notes": [],
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "FRESH",
        "acceptance_state": "NOT_DECLARED",
        "final_artifact_state": "FRESH",
        "final_artifact_kind": "polished_svg",
        "final_artifact_path": "polish/driver_demo.polished.svg",
        "workflow_ready": True,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] is None


# --- stage 0 / 1 -------------------------------------------------------------


def test_create_or_fix_source_when_directory_missing(tmp_path: Path) -> None:
    (tmp_path / "examples").mkdir()

    summary = _run_driver("driver_demo", mode="review", goal="scaffold", repo_root=tmp_path)

    assert summary["action"] == "create_or_fix_source"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] is None


def test_create_or_fix_source_when_tex_missing(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "driver_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: driver_demo\npanels: []\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("brief\n", encoding="utf-8")

    summary = _run_driver("driver_demo", mode="authoring", goal="author", repo_root=tmp_path)

    assert summary["action"] == "create_or_fix_source"


# --- release-mode critique recommendation (Review 1 HIGH regression test) ----


def test_release_mode_recommends_critique_without_self_contradicting_forbidden_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Release mode hitting MISSING critique must not forbid the action it returns."""
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    synthetic_status = {
        "stage": 4,
        "name": "driver_demo",
        "notes": ["critique_missing"],
        "render_state": "FRESH",
        "critique_state": "MISSING",
        "export_state": "FRESH",
        "acceptance_state": "NOT_DECLARED",
        "final_artifact_state": "NONE",
        "final_artifact_kind": "generated_export",
        "final_artifact_path": None,
        "workflow_ready": False,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
    }
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "run_critique"
    assert summary["stop_boundary"] == "host_llm_critique_required"
    assert summary["safe_command"] == "/fig_critique driver_demo"
    assert summary["action"] not in summary["forbidden_actions"]


# --- no-mutation guarantee ---------------------------------------------------


def test_driver_dry_run_does_not_mutate_fixture_files(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    before = {
        path.relative_to(fixture): path.read_bytes()
        for path in fixture.rglob("*")
        if path.is_file()
    }

    _run_driver("driver_demo", mode="review", goal="dry", repo_root=tmp_path)

    after = {
        path.relative_to(fixture): path.read_bytes()
        for path in fixture.rglob("*")
        if path.is_file()
    }
    assert after == before
