from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_driver  # noqa: E402
import fig_driver_guidance  # noqa: E402
import status as status_mod  # noqa: E402


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


def _write_visual_clash_report(fixture: Path, *, total: int, name: str = "driver_demo") -> None:
    build = fixture / "build"
    build.mkdir(exist_ok=True)
    (build / "visual_clash.json").write_text(
        json.dumps(
            {
                "fixture": name,
                "render_pdf": f"build/{name}.pdf",
                "candidates": [],
                "total": total,
            }
        ),
        encoding="utf-8",
    )


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
    svg_polish_readiness: dict[str, Any] | None = None,
    crop_audit_summary: dict[str, Any] | None = None,
    aesthetic_lever_summary: dict[str, Any] | None = None,
    journal_art_direction_playbook_summary: dict[str, Any] | None = None,
    basin_summary: dict[str, Any] | None = None,
    next_action_summary: dict[str, Any] | None = None,
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
    if svg_polish_readiness is not None:
        iteration["svg_polish_readiness"] = svg_polish_readiness
    if crop_audit_summary is not None:
        iteration["crop_audit_summary"] = crop_audit_summary
    if aesthetic_lever_summary is not None:
        iteration["aesthetic_lever_summary"] = aesthetic_lever_summary
    if journal_art_direction_playbook_summary is not None:
        iteration["journal_art_direction_playbook_summary"] = journal_art_direction_playbook_summary
    if basin_summary is not None:
        iteration["basin_summary"] = basin_summary
    if next_action_summary is not None:
        iteration["next_action_summary"] = next_action_summary
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
        "publication_gate_state": "PASS",
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
    assert payload["next_action_summary"]["action"] == payload["action"]
    assert payload["next_action_summary"]["safe_command"] == payload["safe_command"]
    for key in ("action", "safe_command", "stop_boundary", "reason"):
        assert key in payload


def test_main_accepts_json_flag_as_output_compatibility_noop(
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
            "--json",
        ],
        repo_root=tmp_path,
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["schema"] == "figure-agent.driver.v1"
    assert payload["fixture"] == "driver_demo"
    assert payload["may_execute"] is False
    assert isinstance(payload["status"], dict)
    assert isinstance(payload["forbidden_actions"], list)
    assert isinstance(payload["workspace_warnings"], list)
    assert payload["next_action_summary"]["action"] == payload["action"]
    assert payload["next_action_summary"]["safe_command"] == payload["safe_command"]
    for key in ("action", "safe_command", "stop_boundary", "reason"):
        assert key in payload


def test_main_accepts_format_json_as_output_compatibility_noop(
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
            "--format",
            "json",
        ],
        repo_root=tmp_path,
    )

    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["schema"] == "figure-agent.driver.v1"
    assert payload["fixture"] == "driver_demo"
    assert payload["may_execute"] is False


def test_build_driver_summary_rejects_unsafe_fixture_name_before_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "examples").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "spec.yaml").write_text("name: outside\n", encoding="utf-8")

    def status_should_not_run(_example_dir: Path) -> dict[str, Any]:
        raise AssertionError("unsafe fixture name reached status inference")

    monkeypatch.setattr(fig_driver, "_status_for", status_should_not_run)

    with pytest.raises(
        ValueError,
        match="fixture name must be a single examples/<name> directory name",
    ):
        fig_driver.build_driver_summary(
            "../outside",
            mode="review",
            goal="triage",
            repo_root=tmp_path,
        )


def test_main_rejects_unsafe_fixture_name_cleanly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "examples").mkdir()

    result = fig_driver.main(
        ["../outside", "--mode", "review", "--goal", "triage", "--dry-run"],
        repo_root=tmp_path,
    )

    captured = capsys.readouterr()
    assert result == 2
    assert "fixture name must be a single examples/<name> directory name" in captured.err
    assert captured.out == ""


def test_review_complete_surfaces_ready_improvement_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(tmp_path / "examples" / "driver_demo")
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary={
            "polish_recommended_path": "continue_tikz",
            "polish_trigger_verdict": "pass",
            "polish_route_detail": "tighten Panel C annotation spacing",
            "human_art_direction_gate_verdict": "pass",
            "worst_verdict": "pass",
            "blocking_high_impact_count": 0,
        },
    )
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda *_args: False)

    payload = _run_driver(
        "driver_demo",
        mode="review",
        goal="find optional polish",
        repo_root=tmp_path,
    )

    assert payload["action"] == "complete"
    summary = payload["ready_improvement_summary"]
    assert summary["state"] == "ready_but_improvable"
    assert summary["safe_to_ship"] is True
    assert summary["blocks_release"] is False
    assert summary["auto_patch_allowed"] is False
    assert summary["candidates"][0]["source"] == "editorial_art_direction_summary"
    next_action = payload["next_action_summary"]
    assert next_action["ready_improvement_state"] == "ready_but_improvable"
    assert next_action["optional_candidate_count"] == 1
    assert next_action["marginal_return_state"] == "stop_recommended"
    assert next_action["ready_improvement_safe_to_ship"] is True
    assert "ready_improvement.marginal_return:stop_recommended" in next_action["evidence_refs"]
    assert next_action["decision_boundary"]["kind"] == "advisory_only"
    assert next_action["decision_boundary"]["blocks_release"] is False
    assert payload["operator_guidance"]["decision_boundary"] == next_action["decision_boundary"]


def test_release_blocked_by_manual_gate_can_still_surface_safe_optional_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_basic_fixture(tmp_path)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary={
            "polish_recommended_path": "continue_tikz",
            "polish_trigger_verdict": "pass",
            "polish_route_detail": "optional paper-wide palette cleanup",
            "human_art_direction_gate_verdict": "pass",
            "worst_verdict": "pass",
            "blocking_high_impact_count": 0,
        },
    )
    status = _release_ready_status()
    status.update(
        {
            "export_state": "TRACKED_GOLDEN",
            "release_ready": False,
            "final_ready": False,
        }
    )
    monkeypatch.setattr(fig_driver, "_status_for", lambda _example_dir: status)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda *_args: False)

    payload = _run_driver(
        "driver_demo",
        mode="release",
        goal="release",
        repo_root=tmp_path,
    )

    assert payload["action"] == "release_blocked"
    summary = payload["ready_improvement_summary"]
    assert summary["state"] == "ready_but_improvable"
    assert summary["safe_to_ship"] is True
    assert summary["candidate_count"] == 1


def test_human_gate_driver_result_does_not_offer_optional_improvement_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(tmp_path / "examples" / "driver_demo")
    _write_loop_run(
        tmp_path,
        stop_reason="human_gate_required",
        escalation_level="basin_detected",
        recommended_next_action="review art direction",
        editorial_art_direction_summary={
            "polish_recommended_path": "continue_tikz",
            "polish_trigger_verdict": "pass",
            "polish_route_detail": "tighten Panel C annotation spacing",
            "human_art_direction_gate_verdict": "needs_human",
            "worst_verdict": "needs_human",
            "blocking_high_impact_count": 1,
        },
    )
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda *_args: False)

    payload = _run_driver(
        "driver_demo",
        mode="review",
        goal="review",
        repo_root=tmp_path,
    )

    assert payload["action"] == "human_gate_stop"
    summary = payload["ready_improvement_summary"]
    assert summary["state"] == "not_ready"
    assert summary["safe_to_ship"] is False
    assert summary["candidate_count"] == 0
    next_action = payload["next_action_summary"]
    assert next_action["ready_improvement_state"] == "not_ready"
    assert next_action["optional_candidate_count"] == 0
    assert next_action["marginal_return_state"] == "not_ready"


def test_driver_summary_includes_status_explanation_and_first_blocker_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    synthetic_status = _release_ready_status()
    synthetic_status.update(
        {
            "export_state": "MISSING",
            "acceptance_state": "NOT_DECLARED",
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
    assert summary["safe_command"] == "fig-agent export driver_demo"


def test_driver_summary_copies_critique_freshness_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    synthetic_status = _release_ready_status()
    synthetic_status.update(
        {
            "critique_state": "STALE",
            "critique_freshness": {
                "metadata_complete": True,
                "is_fresh": False,
                "mismatch_reasons": ["generator_version"],
            },
        }
    )
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["critique_freshness"]["mismatch_reasons"] == ["generator_version"]


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


def test_driver_summary_includes_spine_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    synthetic_status = _release_ready_status()
    synthetic_status["spine_evidence"] = {
        "schema": "figure-agent.spine-evidence-summary.v1",
        "state": "present",
        "tex_assertions": {"state": "passed", "checked": 2, "issue_count": 0},
        "convention_receipt": {"state": "present", "total": 3},
        "physics_grounding": {"state": "present", "status": "grounded"},
    }
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["status"]["spine_evidence"]["state"] == "present"
    assert summary["spine_evidence"]["tex_assertions"]["state"] == "passed"


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

    assert warnings == ["tracked_worktree_dirty: plugins/figure-agent/scripts/foo.py"]


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


# --- final mode --------------------------------------------------------------


def test_final_mode_recommends_strict_compile_for_stale_render(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_basic_fixture(tmp_path)
    synthetic_status = _release_ready_status()
    synthetic_status.update(
        {
            "render_state": "STALE",
            "workflow_ready": False,
            "golden_ready": False,
            "release_ready": False,
            "final_ready": False,
        }
    )
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="final", goal="final", repo_root=tmp_path)

    assert summary["action"] == "run_compile"
    assert (
        summary["safe_command"]
        == "fig-agent compile driver_demo --strict"
    )
    assert summary["final_readiness_profile"]["strict_compile"]["state"] == "needs_action"
    assert summary["operator_guidance"]["required_actor"] == "workflow_agent"
    assert "strict compile" in summary["operator_guidance"]["next_step"]


def test_final_mode_explains_tracked_golden_as_release_operator_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_visual_clash_report(fixture, total=0)
    synthetic_status = _release_ready_status()
    synthetic_status.update(
        {
            "export_state": "TRACKED_GOLDEN",
            "release_ready": False,
            "final_ready": False,
        }
    )
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda *_args: False)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        recommended_next_action="release is ready after human golden roll-forward",
    )

    summary = _run_driver("driver_demo", mode="final", goal="final", repo_root=tmp_path)

    assert summary["action"] == "release_blocked"
    assert summary["stop_boundary"] == "accepted_or_final_ready_required"
    assert summary["safe_command"] is None
    assert summary["operator_guidance"]["required_actor"] == "release_operator"
    assert "force-golden" in summary["operator_guidance"]["next_step"]
    assert summary["operator_guidance"]["decision_boundary"]["kind"] == "release_decision"
    assert summary["operator_guidance"]["decision_boundary"]["blocks_release"] is True
    assert summary["final_readiness_profile"]["release_gate"]["state"] == "human_required"


def test_final_mode_complete_explains_no_required_plugin_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_visual_clash_report(fixture, total=0)
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: _release_ready_status())
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda *_args: False)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        recommended_next_action="release is ready",
    )

    summary = _run_driver("driver_demo", mode="final", goal="final", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] is None
    assert summary["operator_guidance"]["state"] == "complete"
    assert summary["operator_guidance"]["required_actor"] == "none"
    assert "No required plugin action remains" in summary["operator_guidance"]["next_step"]
    assert summary["final_readiness_profile"]["overall_state"] == "pass"
    assert summary["final_readiness_profile"]["warning_budget"]["state"] == "pass"
    assert summary["final_readiness_profile"]["publication_gate"]["state"] == "pass"


def test_final_mode_blocks_complete_when_warning_budget_exceeds_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_visual_clash_report(fixture, total=3)
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: _release_ready_status())
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda *_args: False)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        recommended_next_action="release is ready",
    )

    summary = _run_driver("driver_demo", mode="final", goal="final", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["stop_boundary"] == "human_gate_required"
    assert summary["safe_command"] is None
    assert "warning budget exceeded" in summary["reason"]
    assert summary["operator_guidance"]["required_actor"] == "human"
    assert summary["final_readiness_profile"]["overall_state"] == "human_required"
    assert summary["final_readiness_profile"]["warning_budget"]["budget_state"] == "needs_action"
    assert summary["final_readiness_profile"]["warning_budget"]["visual_clash"] == {
        "present": True,
        "total": 3,
        "cap": 0,
        "over_by": 3,
        "status": "over_budget",
    }


def test_final_mode_requests_strict_compile_when_warning_budget_report_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_basic_fixture(tmp_path)
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: _release_ready_status())
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda *_args: False)
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        recommended_next_action="release is ready",
    )

    summary = _run_driver("driver_demo", mode="final", goal="final", repo_root=tmp_path)

    assert summary["action"] == "run_compile"
    assert (
        summary["safe_command"]
        == "fig-agent compile driver_demo --strict"
    )
    assert "warning budget input is missing" in summary["reason"]
    assert summary["final_readiness_profile"]["warning_budget"]["state"] == "needs_action"
    assert summary["final_readiness_profile"]["warning_budget"]["budget_state"] == "missing_input"


def test_final_mode_requires_loop_checkpoint_before_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_visual_clash_report(fixture, total=0)
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: _release_ready_status())
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda *_args: False)

    summary = _run_driver("driver_demo", mode="final", goal="final", repo_root=tmp_path)

    assert summary["action"] == "run_fig_loop"
    assert summary["safe_command"] == (
        "fig-agent loop driver_demo --goal final --json"
    )
    assert summary["operator_guidance"]["required_actor"] == "workflow_agent"
    assert summary["final_readiness_profile"]["loop_checkpoint"]["state"] == "needs_action"
    assert summary["final_readiness_profile"]["overall_state"] == "needs_action"


def test_operator_guidance_does_not_suggest_force_golden_for_non_golden_first_blocker() -> None:
    summary = {
        "fixture": "driver_demo",
        "action": "release_blocked",
        "safe_command": None,
        "stop_boundary": "accepted_or_final_ready_required",
        "status": {"export_state": "TRACKED_GOLDEN"},
        "status_explanation": {
            "first_blocker": {
                "code": "not_accepted",
                "category": "human_blocker",
                "manual": True,
            }
        },
    }

    guidance = fig_driver_guidance.operator_guidance(summary)

    assert guidance["required_actor"] == "release_operator"
    assert guidance["decision_boundary"]["kind"] == "release_decision"
    assert "force-golden" not in guidance["next_step"]
    assert "accepted" in guidance["next_step"]


def test_operator_guidance_fallback_preserves_advisory_ready_improvement_boundary() -> None:
    guidance = fig_driver_guidance.operator_guidance(
        {
            "action": "complete",
            "stop_boundary": None,
            "ready_improvement_summary": {
                "state": "ready_but_improvable",
                "safe_to_ship": True,
            },
        }
    )

    assert guidance["required_actor"] == "none"
    assert guidance["decision_boundary"]["kind"] == "advisory_only"
    assert guidance["decision_boundary"]["blocks_release"] is False


# --- authoring mode ----------------------------------------------------------


def test_authoring_mode_recommends_compile_when_render_missing(tmp_path: Path) -> None:
    _write_basic_fixture(tmp_path)

    summary = _run_driver("driver_demo", mode="authoring", goal="author", repo_root=tmp_path)

    assert summary["action"] == "run_compile"
    assert summary["safe_command"] == "fig-agent compile driver_demo"
    assert summary["stop_boundary"] is None


def test_authoring_mode_completes_when_render_fresh(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="authoring", goal="author", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] is None
    assert summary["operator_guidance"]["state"] == "complete"
    assert "authoring mode" in summary["operator_guidance"]["next_step"]
    assert "--mode review" in summary["operator_guidance"]["next_step"]
    assert "whole-figure" in summary["operator_guidance"]["next_step"]


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
    assert summary["operator_guidance"]["required_actor"] == "workflow_agent"
    assert "reference" in summary["operator_guidance"]["next_step"]


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
        == "fig-agent adjudicate driver_demo"
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
            == "fig-agent loop driver_demo --goal review --json"
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
            == "fig-agent loop driver_demo --goal review --json"
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
    assert summary["safe_command"] == "fig-agent export driver_demo"
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
    assert summary["safe_command"] == "fig-agent export driver_demo"
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
        == "fig-agent loop driver_demo --goal 'it'\"'\"'s a goal' --json"
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


def test_review_mode_surfaces_latest_basin_checkpoint_as_step_out_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    basin_summary = {
        "schema": "figure-agent.loop-basin.v1",
        "evaluation_state": "basin_detected",
        "threshold": 3,
        "history_count": 4,
        "signal": {
            "signal_class": "patch_target",
            "signal_value": "C001",
            "signal_key": "patch_target:C001",
            "source": "active_patch_target",
        },
        "recommended_step_out_actions": [
            "run external second-opinion review on the repeated issue",
            "request human art-direction review before another local patch",
        ],
        "next_action": "step out of the local polish loop",
    }
    _write_loop_run(
        tmp_path,
        stop_reason="basin_detected",
        escalation_level="basin_detected",
        recommended_next_action="step out of the local polish loop",
        basin_summary=basin_summary,
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] == "basin_detected"
    assert summary["safe_command"] is None
    assert summary["loop_checkpoint"]["basin_summary"] == basin_summary
    assert "repeated loop basin" in summary["reason"]
    assert "patch_target=C001" in summary["reason"]
    assert "4 times" in summary["reason"]


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
    assert "review mode" in summary["operator_guidance"]["next_step"]
    assert "--mode release" in summary["operator_guidance"]["next_step"]
    assert "final" in summary["operator_guidance"]["next_step"]


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


def test_review_mode_completes_when_latest_loop_next_action_is_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)
    _write_loop_run(
        tmp_path,
        stop_reason="status_action_required",
        escalation_level="agent_action_required",
        recommended_next_action=(
            "fixture has no accepted or final-ready declaration; no plugin action remains"
        ),
        next_action_summary={
            "schema": "figure-agent.next-action-summary.v1",
            "action": "complete",
            "requires_human": False,
            "safe_command": None,
            "decision_boundary": {
                "schema": "figure-agent.decision-boundary.v1",
                "kind": "none",
                "authority": "none",
                "blocks_progress": False,
                "blocks_release": False,
            },
        },
    )

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "complete"
    assert summary["stop_boundary"] is None
    assert summary["safe_command"] is None
    assert summary["loop_checkpoint"]["final_stop_reason"] == "status_action_required"
    assert summary["loop_checkpoint"]["next_action_summary"]["action"] == "complete"


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




def test_review_mode_surfaces_adjudication_and_release_blockers(
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
        "adjudication_state": "MISSING",
        "export_state": "TRACKED_GOLDEN",
        "acceptance_state": "ACCEPTED",
        "final_artifact_state": "NONE",
        "final_artifact_kind": "generated_export",
        "final_artifact_path": None,
        "workflow_ready": True,
        "golden_ready": True,
        "release_ready": False,
        "final_ready": False,
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
    from status_explanation import build_status_explanation

    synthetic_status["status_explanation"] = build_status_explanation(synthetic_status)
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: True)

    summary = _run_driver("driver_demo", mode="review", goal="review", repo_root=tmp_path)

    assert summary["action"] == "run_adjudicate"
    assert summary["safe_command"] == "fig-agent adjudicate driver_demo"
    next_action = summary["next_action_summary"]
    assert next_action["action"] == "run_adjudicate"
    assert next_action["release_blockers"][0]["blocking_source"] == "export_tracked_golden"
    assert next_action["release_blockers"][0]["stop_boundary"] == "force_golden_required"
    assert next_action["release_blockers"][1]["blocking_source"] == "publication_gate_required"
    assert summary["operator_guidance"]["required_actor"] == "workflow_agent"

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


def test_release_mode_surfaces_acceptance_not_declared_first_blocker(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="release", goal="release", repo_root=tmp_path)

    assert summary["action"] == "release_blocked"
    assert summary["stop_boundary"] == "accepted_or_final_ready_required"
    assert summary["status_explanation"]["first_blocker"]["code"] == ("acceptance_not_declared")
    assert "first blocker acceptance_not_declared" in summary["reason"]


def test_release_mode_does_not_surface_not_accepted_export_as_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    synthetic_status = {
        "stage": 3,
        "name": "driver_demo",
        "notes": [],
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "MISSING",
        "acceptance_state": "NOT_ACCEPTED",
        "final_artifact_state": "NONE",
        "final_artifact_kind": "generated_export",
        "final_artifact_path": "exports/driver_demo.svg",
        "workflow_ready": False,
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
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "accepted_or_final_ready_required"
    assert "acceptance_state is NOT_DECLARED" in summary["reason"]


def test_polish_mode_does_not_surface_not_accepted_export_as_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    synthetic_status = {
        "stage": 3,
        "name": "driver_demo",
        "notes": [],
        "render_state": "FRESH",
        "critique_state": "NOT_REQUIRED",
        "export_state": "MISSING",
        "acceptance_state": "NOT_ACCEPTED",
        "final_artifact_state": "NONE",
        "final_artifact_kind": "generated_export",
        "final_artifact_path": "exports/driver_demo.svg",
        "workflow_ready": False,
        "golden_ready": False,
        "release_ready": False,
        "final_ready": False,
        "publication_gate_state": "HUMAN_ACCEPTANCE_REQUIRED",
        "publication_gate_failures": [],
    }
    monkeypatch.setattr(fig_driver, "_status_for", lambda _ex: synthetic_status)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "polish_handoff_stop"
    assert summary["safe_command"] is None
    assert summary["stop_boundary"] == "accepted_or_final_ready_required"
    assert "acceptance_state is NOT_DECLARED" in summary["reason"]
    assert summary["svg_polish_gate"]["state"] == "blocked"
    assert summary["svg_polish_gate"]["source"] == "driver_prerequisite"
    assert summary["svg_polish_gate"]["next_action"] == "resolve_release_boundary"
    assert summary["svg_polish_gate"]["blocking_items"] == [
        {"source": "driver_prerequisite", "id": "accepted_or_final_ready_required"}
    ]


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
        "fig-agent adjudicate driver_demo"
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
    assert summary["svg_polish_gate"]["state"] == "blocked"
    assert summary["svg_polish_gate"]["source"] == "driver_prerequisite"
    assert summary["svg_polish_gate"]["next_action"] == "run_fig_compile"
    assert summary["svg_polish_gate"]["blocking_items"] == [
        {"source": "driver_prerequisite", "id": "run_compile"}
    ]


def test_polish_mode_svg_gate_points_to_export_before_loop(tmp_path: Path) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    shutil.rmtree(fixture / "exports")

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "run_export"
    assert summary["svg_polish_gate"]["state"] == "blocked"
    assert summary["svg_polish_gate"]["source"] == "driver_prerequisite"
    assert summary["svg_polish_gate"]["next_action"] == "run_fig_export"
    assert summary["svg_polish_gate"]["blocking_items"] == [
        {"source": "driver_prerequisite", "id": "run_export"}
    ]


def test_polish_mode_not_required_critique_routes_to_release_or_final(
    tmp_path: Path,
) -> None:
    # NOT_REQUIRED critique: no reference declared, so an editorial
    # art-direction summary (and thus ready_for_svg_polish) can never be
    # produced. Guidance must route to release/final, not the unreachable
    # ready_for_svg_polish condition.
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["status"]["critique_state"] == "NOT_REQUIRED"
    assert summary["action"] == "run_fig_loop"
    assert summary["stop_boundary"] == "mode_forbidden_action"
    assert summary["safe_command"] == (
            "fig-agent loop driver_demo --goal polish --json"
    )
    assert "ready_for_svg_polish" not in summary["reason"]
    assert "NOT_REQUIRED" in summary["reason"]
    assert "--mode release" in summary["reason"]
    assert summary["svg_polish_gate"]["state"] == "no_current_checkpoint"
    assert summary["svg_polish_gate"]["can_start_svg_polish"] is False
    assert summary["svg_polish_gate"]["next_action"] == "rerun_fig_loop"
    next_step = summary["operator_guidance"]["next_step"]
    assert "Run the selected command" not in next_step
    assert "ready_for_svg_polish" not in next_step
    assert "--mode review" not in next_step
    assert "--mode release" in next_step
    assert "--mode final" in next_step
def test_polish_mode_fresh_critique_requires_loop_checkpoint_before_svg_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # FRESH critique with no current loop checkpoint: the editorial summary is
    # possible, so guidance correctly waits for a loop checkpoint that routes
    # ready_for_svg_polish.
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
    monkeypatch.setattr(fig_driver, "_adjudication_needs_action", lambda _ex, _st: False)

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["status"]["critique_state"] == "FRESH"
    assert summary["action"] == "run_fig_loop"
    assert summary["stop_boundary"] == "mode_forbidden_action"
    assert summary["safe_command"] == (
            "fig-agent loop driver_demo --goal polish --json"
    )
    assert "ready_for_svg_polish" in summary["reason"]
    assert summary["svg_polish_gate"]["state"] == "no_current_checkpoint"
    assert summary["svg_polish_gate"]["can_start_svg_polish"] is False
    assert summary["svg_polish_gate"]["next_action"] == "rerun_fig_loop"
    next_step = summary["operator_guidance"]["next_step"]
    assert "Run the selected command" not in next_step
    assert "not executable in polish mode" in next_step
    assert "--mode review" in next_step


def test_polish_mode_surfaces_existing_svg_polish_readiness_checkpoint(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    readiness = {
        "schema": "figure-agent.svg-polish-readiness.v1",
        "source": "latest_loop_checkpoint",
        "can_start_svg_polish": False,
        "recommended_path": "continue_tikz",
        "next_action": "run_fig_loop",
        "blocking_reason": "existing checkpoint readiness",
        "blocking_items": [],
    }
    _write_loop_run(
        tmp_path,
        stop_reason="verify_only_complete",
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "weak",
            "polish_recommended_path": "continue_tikz",
        },
        svg_polish_readiness=readiness,
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "run_fig_loop"
    assert summary["svg_polish_readiness"] == readiness


def test_polish_mode_readiness_prefers_loop_human_gate_over_legacy_pass_trigger(
    tmp_path: Path,
) -> None:
    fixture = _write_basic_fixture(tmp_path)
    _write_fresh_build_and_exports(fixture)
    _write_loop_run(
        tmp_path,
        stop_reason="human_gate_required",
        escalation_level="human_review_required",
        recommended_next_action="human review required for C001",
        editorial_art_direction_summary={
            "source": "critique.editorial_art_direction",
            "worst_verdict": "pass",
            "polish_trigger_verdict": "pass",
            "polish_recommended_path": "continue_tikz",
        },
    )

    summary = _run_driver("driver_demo", mode="polish", goal="polish", repo_root=tmp_path)

    assert summary["action"] == "human_gate_stop"
    assert summary["svg_polish_readiness"]["can_start_svg_polish"] is False
    assert summary["svg_polish_readiness"]["next_action"] == "human_review"
    assert summary["svg_polish_gate"]["state"] == "needs_human"
    assert summary["svg_polish_gate"]["next_action"] == "human_art_direction"
    assert summary["svg_polish_readiness"]["blocking_items"] == [
        {
            "source": "latest_loop_checkpoint",
            "id": "human_gate_required",
            "recommended_next_action": "human review required for C001",
        }
    ]


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
    assert summary["svg_polish_readiness"]["can_start_svg_polish"] is False
    assert summary["svg_polish_readiness"]["blocking_items"][0]["source"] == (
        "top_tier_audit_summary"
    )


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
            "fig-agent loop driver_demo --goal polish --json"
    )
    assert summary["stop_boundary"] == "mode_forbidden_action"
    assert "continue_tikz" in summary["reason"]
    assert "Run the selected command" not in summary["operator_guidance"]["next_step"]
    assert "not executable in polish mode" in summary["operator_guidance"]["next_step"]
    assert "--mode review" in summary["operator_guidance"]["next_step"]


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
    assert summary["svg_polish_readiness"]["can_start_svg_polish"] is False
    assert summary["svg_polish_readiness"]["next_action"] == "review_crop_audit"


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
