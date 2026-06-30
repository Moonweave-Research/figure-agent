from __future__ import annotations

import json
import os
import subprocess
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
        "acceptance_freshness_state": "not_accepted",
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


def test_closeout_rejects_unsafe_fixture_name_before_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "examples").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "spec.yaml").write_text("name: outside\npanels: []\n", encoding="utf-8")

    def status_should_not_run(_example_dir: Path) -> dict:
        raise AssertionError("unsafe fixture name reached status inference")

    monkeypatch.setattr(fig_closeout_mod, "infer_stage", status_should_not_run)

    with pytest.raises(
        fig_closeout_mod.FigCloseoutError,
        match="fixture name must be a single examples/<name> directory name",
    ):
        compute_closeout("../outside", repo_root=tmp_path)


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
    assert report["evidence_index_path"] == "build/evidence/evidence_index.json"
    assert report["candidate_apply"]["status"] == "not_required"
    assert report["golden_acceptance"]["state"] == "missing"
    assert steps["text_boundary_checks"]["state"] == "not_required"
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
    assert report["next_action_summary"]["action"] == "run_compile"
    assert report["next_action_summary"]["safe_command"] == "/fig_compile loop_demo"


def test_closeout_reports_latest_candidate_apply_and_golden_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    sandbox = fixture / "build" / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    (sandbox / "apply_result.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.candidate-apply-result.v1",
                "candidate_id": "CAND001",
                "status": "applied",
                "post_apply": {
                    "compile": {"status": "success"},
                    "export": {"status": "success"},
                    "status": {"status": "success"},
                },
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    closeout_dir = fixture / "build" / "closeout"
    closeout_dir.mkdir()
    (closeout_dir / "golden_acceptance.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.golden-acceptance.v1",
                "decision": "accept",
                "reviewer": "local-user",
                "reviewed_at": "2026-06-08T00:00:00Z",
                "accept_golden": True,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(fig_closeout_mod, "infer_stage", lambda _example_dir: _status())

    report = compute_closeout("loop_demo", repo_root=tmp_path)

    assert report["candidate_apply"] == {
        "status": "applied",
        "candidate_id": "CAND001",
        "apply_result_path": "build/candidates/CAND001/apply_result.json",
        "post_apply": {
            "compile": "success",
            "export": "success",
            "status": "success",
        },
    }
    assert report["golden_acceptance"]["state"] == "present"
    assert report["golden_acceptance"]["accept_golden"] is True


def test_closeout_passes_matching_text_boundary_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "spec.yaml").write_text(
        "name: loop_demo\n"
        "panels: []\n"
        "style_profile: polymer-default\n"
        "text_boundary_layout:\n"
        "  column_rules:\n"
        "    - id: de\n"
        "      x_pdf_cm: 4.62\n"
        "      y_range_pdf_cm: [0.0, 4.5]\n"
        "text_boundary_checks:\n"
        "  - id: de_column_rule\n"
        "    kind: vertical_line\n"
        "    role: column_rule\n"
        "    x_pdf_cm: 4.62\n"
        "    y_range_pdf_cm: [0.0, 4.5]\n"
        "    clearance_pt: 0.5\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(fig_closeout_mod, "infer_stage", lambda _example_dir: _status())

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    step = _steps_by_id(report)["text_boundary_checks"]

    assert step["state"] == "passed"
    assert step["command"] is None


def test_closeout_requests_text_boundary_helper_when_checks_are_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "spec.yaml").write_text(
        "name: loop_demo\n"
        "panels: []\n"
        "style_profile: polymer-default\n"
        "text_boundary_layout:\n"
        "  row_boxes:\n"
        "    - id: row2\n"
        "      bbox_pdf_cm: [0.0, 0.0, 13.8, 4.5]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(fig_closeout_mod, "infer_stage", lambda _example_dir: _status())

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    step = _steps_by_id(report)["text_boundary_checks"]

    assert step["state"] == "needs_action"
    assert step["command"] == (
        "fig-agent text-boundary loop_demo --write"
    )
    assert report["next_action"] == step["command"]
    assert report["next_action_summary"]["action"] == "create_or_fix_source"
    assert report["next_action_summary"]["safe_command"] == step["command"]
    assert "text_boundary_checks" in report["blocking_step_ids"]


def test_closeout_requests_text_boundary_helper_when_checks_are_stale(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "spec.yaml").write_text(
        "name: loop_demo\n"
        "panels: []\n"
        "style_profile: polymer-default\n"
        "text_boundary_layout:\n"
        "  column_rules:\n"
        "    - id: de\n"
        "      x_pdf_cm: 4.62\n"
        "      y_range_pdf_cm: [0.0, 4.5]\n"
        "text_boundary_checks:\n"
        "  - id: stale\n"
        "    kind: vertical_line\n"
        "    role: column_rule\n"
        "    x_pdf_cm: 1.0\n"
        "    y_range_pdf_cm: [0.0, 1.0]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(fig_closeout_mod, "infer_stage", lambda _example_dir: _status())

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    step = _steps_by_id(report)["text_boundary_checks"]

    assert step["state"] == "needs_action"
    assert step["reason"] == "text_boundary_checks do not match text_boundary_layout"


def test_closeout_blocks_on_malformed_text_boundary_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "spec.yaml").write_text(
        "name: loop_demo\n"
        "panels: []\n"
        "style_profile: polymer-default\n"
        "text_boundary_layout:\n"
        "  row_boxes:\n"
        "    - id: row2\n"
        "      bbox_pdf_cm: [0.0, 1.0]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(fig_closeout_mod, "infer_stage", lambda _example_dir: _status())

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    step = _steps_by_id(report)["text_boundary_checks"]

    assert step["state"] == "blocked"
    assert "text_boundary_layout is invalid" in step["reason"]
    assert step["command"] is None


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


def test_closeout_passes_current_tracked_golden_acceptance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    tex_path = fixture / "loop_demo.tex"
    tex_path.write_text("\\node {accepted};\n", encoding="utf-8")
    export_path = fixture / "exports" / "loop_demo.pdf"
    export_path.parent.mkdir()
    export_path.write_bytes(b"%PDF-accepted\n")
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(fixture, critique)
    closeout_dir = fixture / "build" / "closeout"
    closeout_dir.mkdir(parents=True)
    (closeout_dir / "golden_acceptance.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.golden-acceptance.v1",
                "decision": "accept",
                "reviewer": "local-user",
                "reviewed_at": "2026-06-08T00:00:00Z",
                "accept_golden": True,
                "source_sha256": fig_closeout_mod._sha256_file(tex_path),
                "exports": {"pdf": fig_closeout_mod._sha256_file(export_path)},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: _status(critique_state="FRESH", export_state="TRACKED_GOLDEN"),
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    export_step = _steps_by_id(report)["export"]

    assert export_step["state"] == "passed"
    assert export_step["reason"] == "tracked golden export has current explicit acceptance"


def test_closeout_reports_stale_tracked_golden_acceptance_as_accepted_but_stale(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _make_fixture(tmp_path)
    tex_path = fixture / "loop_demo.tex"
    tex_path.write_text("\\node {accepted};\n", encoding="utf-8")
    export_path = fixture / "exports" / "loop_demo.pdf"
    export_path.parent.mkdir()
    export_path.write_bytes(b"%PDF-accepted\n")
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(fixture, critique)
    closeout_dir = fixture / "build" / "closeout"
    closeout_dir.mkdir(parents=True)
    (closeout_dir / "golden_acceptance.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.golden-acceptance.v1",
                "decision": "accept",
                "reviewer": "local-user",
                "reviewed_at": "2026-06-08T00:00:00Z",
                "accept_golden": True,
                "source_sha256": "sha256:" + "0" * 64,
                "exports": {"pdf": fig_closeout_mod._sha256_file(export_path)},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        fig_closeout_mod,
        "infer_stage",
        lambda _example_dir: {
            **_status(critique_state="FRESH", export_state="TRACKED_GOLDEN"),
            "acceptance_state": "ACCEPTED",
            "acceptance_freshness_state": "accepted_but_stale",
            "publication_gate_state": "PASS",
            "publication_gate_failures": [],
        },
    )

    report = compute_closeout("loop_demo", repo_root=tmp_path)
    export_step = _steps_by_id(report)["export"]

    assert report["status"]["acceptance_freshness_state"] == "accepted_but_stale"
    assert export_step["state"] == "blocked"
    assert export_step["reason"] == (
        "accepted_but_stale: fixture has an accepted historical state, but current "
        "source, render, critique, or export evidence is stale. Re-run "
        "compile/critique/export and refresh acceptance before closeout."
    )
    assert "manual approval" not in export_step["reason"]


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


def test_closeout_cli_accepts_format_json_as_output_alias(
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

    exit_code = main(["loop_demo", "--repo-root", str(tmp_path), "--format", "json"])

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


def test_fig_agent_closeout_uses_plugin_workspace_from_repo_root() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    repo_root = plugin_root.parents[1]
    env = os.environ.copy()
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("FIGURE_AGENT_WORKSPACE", None)
    result = subprocess.run(
        [str(plugin_root / "bin" / "fig-agent"), "closeout", "smoke_trap_demo", "--json"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert "examples/smoke_trap_demo/ not found" not in result.stderr
    data = json.loads(result.stdout)
    assert data["fixture"] == "smoke_trap_demo"
    assert result.returncode == (0 if data["closeout_complete"] else 1)
