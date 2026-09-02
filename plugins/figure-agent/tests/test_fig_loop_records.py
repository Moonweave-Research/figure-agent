from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_closeout  # noqa: E402
from fig_loop import run_loop  # noqa: E402
from fig_loop_records import (  # noqa: E402
    json_stdout_summary,
    run_input_hashes,
    write_json,
)
from quality_manifest import file_sha256  # noqa: E402


def test_write_json_serializes_paths_and_tuples(tmp_path: Path) -> None:
    path = tmp_path / "record.json"

    write_json(
        path,
        {
            "artifact_path": tmp_path / "artifact.svg",
            "command": ("uv", "run", "pytest"),
        },
    )

    assert path.read_text(encoding="utf-8").endswith("\n")
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "artifact_path": str(tmp_path / "artifact.svg"),
        "command": ["uv", "run", "pytest"],
    }


def test_json_stdout_summary_reads_manifest_and_iteration_contract(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "loop_demo"
    run_dir.mkdir(parents=True)
    write_json(
        run_dir / "run_manifest.json",
        {
            "run_dir": str(run_dir),
            "final_stop_reason": "status_action_required",
        },
    )
    write_json(
        run_dir / "iteration_001.json",
        {
            "escalation_level": "agent_action_required",
            "patch_handoff": {"target_id": "C001"},
            "auto_patch_eligibility": {"may_auto_patch": False},
            "patch_evidence": None,
            "post_patch_evidence": {"verdict": "needs_human_review"},
            "status": {
                "final_artifact_state": "STALE",
                "final_artifact_kind": "polished_svg",
                "final_artifact_path": "examples/loop_demo/final.svg",
            },
            "top_tier_audit_summary": {"evaluation_state": "passed"},
            "editorial_art_direction_summary": {
                "polish_recommended_path": "ready_for_svg_polish"
            },
            "next_action_summary": {
                "schema": "figure-agent.next-action-summary.v1",
                "action": "run_fig_loop",
            },
            "recommended_next_action": "inspect figure state",
        },
    )

    assert json_stdout_summary(run_dir) == {
        "run_dir": str(run_dir),
        "manifest_path": str(run_dir / "run_manifest.json"),
        "iteration_path": str(run_dir / "iteration_001.json"),
        "final_stop_reason": "status_action_required",
        "escalation_level": "agent_action_required",
        "patch_handoff_present": True,
        "auto_patch_eligibility": {"may_auto_patch": False},
        "patch_evidence_present": False,
        "post_patch_evidence_verdict": "needs_human_review",
        "final_artifact_state": "STALE",
        "final_artifact_kind": "polished_svg",
        "final_artifact_path": "examples/loop_demo/final.svg",
        "top_tier_audit_summary": {"evaluation_state": "passed"},
        "editorial_art_direction_summary": {
            "polish_recommended_path": "ready_for_svg_polish"
        },
        "crop_audit_summary": None,
        "aesthetic_lever_summary": None,
        "journal_art_direction_playbook_summary": None,
        "external_vision_review_summary": None,
        "journal_grade_assessment": None,
        "next_action_summary": {
            "schema": "figure-agent.next-action-summary.v1",
            "action": "run_fig_loop",
        },
        "recommended_next_action": "inspect figure state",
    }


def _fixture_with_render(repo: Path, name: str = "loop_demo") -> Path:
    fixture = repo / "examples" / name
    (fixture / "build").mkdir(parents=True)
    (fixture / f"{name}.tex").write_text("% tikz\n", encoding="utf-8")
    (fixture / "build" / f"{name}.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    return fixture


def test_run_input_hashes_name_the_render_and_source(tmp_path: Path) -> None:
    fixture = _fixture_with_render(tmp_path)

    hashes = run_input_hashes(fixture, "loop_demo")

    assert hashes == {
        "render_pdf_sha256": file_sha256(fixture / "build" / "loop_demo.pdf"),
        "source_tex_sha256": file_sha256(fixture / "loop_demo.tex"),
    }


def test_run_input_hashes_are_none_when_the_artifacts_are_absent(tmp_path: Path) -> None:
    fixture = tmp_path / "examples" / "loop_demo"
    fixture.mkdir(parents=True)

    assert run_input_hashes(fixture, "loop_demo") == {
        "render_pdf_sha256": None,
        "source_tex_sha256": None,
    }


def _write_record(run_dir: Path, manifest: dict) -> Path:
    run_dir.mkdir(parents=True)
    iteration = run_dir / "iteration_001.json"
    write_json(iteration, {"iteration": 1})
    write_json(run_dir / "run_manifest.json", manifest)
    return iteration


def test_closeout_rejects_a_fabricated_run_record(tmp_path: Path) -> None:
    """The attack: two hand-written JSON files of the right shape, touched
    newer than the fixture inputs, used to satisfy the loop_rerun gate."""
    fixture = _fixture_with_render(tmp_path)
    iteration = _write_record(
        tmp_path / ".scratch" / "fig-loop-runs" / "20260902-000000-loop_demo",
        {
            "schema": "figure-agent.fig-loop-run.v1",
            "fixture": "loop_demo",
            "iterations": ["iteration_001.json"],
        },
    )
    now = time.time() + 60
    os.utime(iteration, (now, now))
    os.utime(iteration.parent / "run_manifest.json", (now, now))

    assert not fig_closeout._valid_loop_iteration(iteration, "loop_demo", fixture)


def test_closeout_rejects_a_record_whose_hashes_describe_another_render(tmp_path: Path) -> None:
    fixture = _fixture_with_render(tmp_path)
    manifest = {
        "schema": "figure-agent.fig-loop-run.v1",
        "fixture": "loop_demo",
        "iterations": ["iteration_001.json"],
        **run_input_hashes(fixture, "loop_demo"),
    }
    iteration = _write_record(
        tmp_path / ".scratch" / "fig-loop-runs" / "20260902-000000-loop_demo", manifest
    )
    assert fig_closeout._valid_loop_iteration(iteration, "loop_demo", fixture)

    # Recompile: the record now describes a render that no longer exists.
    (fixture / "build" / "loop_demo.pdf").write_bytes(b"%PDF-1.4\n% redrawn\n%%EOF\n")

    assert not fig_closeout._valid_loop_iteration(iteration, "loop_demo", fixture)


def test_closeout_accepts_a_record_the_real_writer_produced(tmp_path: Path) -> None:
    """Positive control: the loop's own manifest satisfies the gate."""
    fixture = tmp_path / "examples" / "loop_demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        "name: loop_demo\npanels: []\nstyle_profile: polymer-default\n", encoding="utf-8"
    )
    (fixture / "briefing.md").write_text("briefing", encoding="utf-8")
    (fixture / "loop_demo.tex").write_text("% tikz\n", encoding="utf-8")
    (fixture / "build").mkdir()
    (fixture / "build" / "loop_demo.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

    run_dir = run_loop("loop_demo", "inspect", repo_root=tmp_path)

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["render_pdf_sha256"] == file_sha256(fixture / "build" / "loop_demo.pdf")
    assert manifest["source_tex_sha256"] == file_sha256(fixture / "loop_demo.tex")
    assert fig_closeout._valid_loop_iteration(
        run_dir / "iteration_001.json", "loop_demo", fixture
    )
