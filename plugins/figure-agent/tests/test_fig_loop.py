from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from fig_loop import FigLoopError, ensure_safe_command, run_loop  # noqa: E402
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


def _fixture_files(fixture: Path) -> dict[str, str]:
    return {
        str(path.relative_to(fixture)): path.read_text(encoding="utf-8")
        for path in sorted(fixture.rglob("*"))
        if path.is_file()
    }


def _write_adjudication(
    fixture: Path,
    critique_hash: str,
    decisions: list[dict[str, str]] | None = None,
) -> None:
    (fixture / "critique_adjudication.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.critique-adjudication.v1",
                "fixture": fixture.name,
                "source_critique_hash": critique_hash,
                "decisions": decisions
                or [
                    {
                        "finding_id": "C001",
                        "decision": "dismiss",
                        "reason": "false positive in current render",
                        "patch_target": "",
                        "evidence": "",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_verify_only_loop_writes_manifest_iteration_and_decision(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    before_files = _fixture_files(fixture)

    run_dir = run_loop(
        "loop_demo",
        "inspect current loop state",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    assert (run_dir / "run_manifest.json").is_file()
    assert (run_dir / "iteration_001.json").is_file()
    assert (run_dir / "decision.md").is_file()
    assert _fixture_files(fixture) == before_files

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")

    assert manifest["fixture"] == "loop_demo"
    assert manifest["goal"] == "inspect current loop state"
    assert manifest["mode"] == "verify-only"
    assert manifest["final_stop_reason"] == "status_action_required"
    assert iteration["status"]["stage"] == 1
    assert set(iteration["axis_verdicts"]) == {
        "render",
        "static_visual",
        "critique",
        "adjudication",
        "theory",
        "reference_fidelity",
        "story_hierarchy",
        "export",
        "publication_safety",
    }
    assert iteration["adjudication"]["state"] == "missing"
    assert iteration["stop_reason"] == "status_action_required"
    assert "status_action_required" in decision


def test_loop_records_fresh_adjudication(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(fixture, file_sha256(critique))

    run_dir = run_loop(
        "loop_demo",
        "check adjudication",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["adjudication"]["state"] == "fresh"
    assert iteration["adjudication"]["decision_count"] == 1
    assert iteration["stop_reason"] == "no_actionable_findings"
    assert iteration["axis_verdicts"]["adjudication"]["verdict"] == "complete"


def test_loop_records_stale_adjudication(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique v1\n", encoding="utf-8")
    _write_adjudication(fixture, file_sha256(critique))
    critique.write_text("# critique v2\n", encoding="utf-8")

    run_dir = run_loop(
        "loop_demo",
        "check adjudication",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["adjudication"]["state"] == "stale"
    assert iteration["recommended_next_action"] == "review or refresh critique_adjudication.yaml"
    assert iteration["stop_reason"] == "stale_adjudication"


def test_loop_records_invalid_adjudication_without_traceback(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "critique_adjudication.yaml").write_text(
        "schema: [unterminated\n",
        encoding="utf-8",
    )

    run_dir = run_loop(
        "loop_demo",
        "check invalid adjudication",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["adjudication"]["state"] == "invalid"
    assert "error" in iteration["adjudication"]
    assert iteration["recommended_next_action"] == "fix critique_adjudication.yaml"
    assert iteration["stop_reason"] == "invalid_adjudication"


def test_loop_identifies_apply_decision_patch_target(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C001",
                "decision": "apply",
                "reason": "label overlaps the arrow",
                "patch_target": "panel A label cluster",
                "evidence": "critique.md C001",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")

    assert manifest["final_stop_reason"] == "patch_target_recommended"
    assert iteration["stop_reason"] == "patch_target_recommended"
    assert iteration["active_patch_target"] == {
        "finding_id": "C001",
        "patch_target": "panel A label cluster",
        "reason": "label overlaps the arrow",
    }
    assert iteration["axis_verdicts"]["adjudication"]["verdict"] == "actionable"
    assert iteration["recommended_next_action"] == "patch C001: panel A label cluster"
    assert iteration["patch_handoff"] == {
        "target_type": "finding",
        "target_id": "C001",
        "patch_target": "panel A label cluster",
        "reason": "label overlaps the arrow",
        "allowed_edit_scope": [
            "examples/loop_demo/loop_demo.tex",
            "examples/loop_demo/authoring_plan.md",
            "examples/loop_demo/subregion_iteration_log.md",
        ],
        "forbidden_edit_scope": [
            "accepted",
            "golden_contract",
            "examples/loop_demo/exports/",
            "examples/loop_demo/build/",
            "examples/loop_demo/critique.md",
            "unrelated examples",
            "broad refactors",
            "multiple findings in one patch",
        ],
        "required_closeout_checks": [
            "/fig_compile loop_demo",
            "/fig_critique loop_demo when critique freshness requires it",
            "update or recreate examples/loop_demo/critique_adjudication.yaml",
            "preserve unresolved findings",
            "/fig_loop loop_demo --goal <same goal or next goal>",
        ],
        "unresolved_findings_requirement": (
            "Do not delete, rewrite, or hide unresolved critique findings; record only the"
            " selected target decision in critique_adjudication.yaml."
        ),
    }
    assert "active_patch_target: C001 -> panel A label cluster" in decision
    assert "patch_handoff_target: finding C001" in decision


def test_loop_stops_on_human_gated_decision(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    critique = fixture / "critique.md"
    critique.write_text("# critique\n", encoding="utf-8")
    _write_adjudication(
        fixture,
        file_sha256(critique),
        [
            {
                "finding_id": "C002",
                "decision": "needs_human",
                "reason": "changes the mechanism arrow semantics",
                "patch_target": "",
                "evidence": "",
            }
        ],
    )

    run_dir = run_loop(
        "loop_demo",
        "choose next patch",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "human_gate_required"
    assert iteration["human_gate_status"] == "required"
    assert iteration["active_patch_target"] is None
    assert iteration["patch_handoff"] is None
    assert iteration["axis_verdicts"]["publication_safety"]["verdict"] == "human_gate"
    assert iteration["recommended_next_action"] == "human review required for C002"


def test_loop_stops_on_missing_reference_input(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "spec.yaml").write_text(
        "name: loop_demo\n"
        "style_profile: polymer-default\n"
        "reference_image: reference/missing.png\n"
        "panels: []\n",
        encoding="utf-8",
    )

    run_dir = run_loop(
        "loop_demo",
        "inspect reference gate",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert manifest["final_stop_reason"] == "reference_input_missing"
    assert iteration["stop_reason"] == "reference_input_missing"
    assert iteration["axis_verdicts"]["reference_fidelity"]["verdict"] == "blocked"
    assert iteration["recommended_next_action"] == (
        "fix declared reference inputs before continuing"
    )


def test_loop_uses_active_subregion_when_no_apply_decision(tmp_path: Path) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "subregion_iteration_log.md").write_text(
        "## Active Target Set\n\n"
        "| State | Sub-region ID | Evidence | Notes |\n"
        "|---|---|---|---|\n"
        "| active target | D-2 | current loop | label spacing |\n",
        encoding="utf-8",
    )

    run_dir = run_loop(
        "loop_demo",
        "inspect active target",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["stop_reason"] == "active_subregion_recommended"
    assert iteration["active_patch_target"] == {
        "finding_id": None,
        "patch_target": "D-2",
        "reason": "active sub-region target",
    }
    assert iteration["patch_handoff"]["target_type"] == "subregion"
    assert iteration["patch_handoff"]["target_id"] == "D-2"
    assert iteration["patch_handoff"]["patch_target"] == "D-2"


def test_loop_requires_adjudication_before_active_subregion_for_fresh_critique(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    reference = fixture / "reference" / "target.png"
    reference.parent.mkdir()
    reference.write_bytes(b"png")
    (fixture / "spec.yaml").write_text(
        "name: loop_demo\n"
        "style_profile: polymer-default\n"
        "reference_image: reference/target.png\n"
        "panels: []\n",
        encoding="utf-8",
    )
    (fixture / "subregion_iteration_log.md").write_text(
        "## Active Target Set\n\n"
        "| State | Sub-region ID | Evidence | Notes |\n"
        "|---|---|---|---|\n"
        "| active target | D-2 | current loop | label spacing |\n",
        encoding="utf-8",
    )
    (fixture / "critique.md").write_text(
        "---\n"
        "schema: figure-agent.critique.v1\n"
        "fixture: loop_demo\n"
        "---\n"
        "# critique\n",
        encoding="utf-8",
    )

    run_dir = run_loop(
        "loop_demo",
        "inspect active target",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    assert iteration["status"]["critique_state"] == "FRESH"
    assert iteration["stop_reason"] == "missing_adjudication"
    assert iteration["active_patch_target"] is None
    assert iteration["patch_handoff"] is None
    assert iteration["recommended_next_action"] == "create critique_adjudication.yaml"


def test_loop_marks_status_action_required_when_status_next_blocks_patch(
    tmp_path: Path,
) -> None:
    fixture = _make_fixture(tmp_path)
    (fixture / "loop_demo.tex").write_text("\\documentclass{standalone}\n", encoding="utf-8")

    run_dir = run_loop(
        "loop_demo",
        "inspect stale status",
        repo_root=tmp_path,
        runs_root=tmp_path / ".scratch" / "fig-loop-runs",
    )

    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    iteration = json.loads((run_dir / "iteration_001.json").read_text(encoding="utf-8"))
    decision = (run_dir / "decision.md").read_text(encoding="utf-8")
    assert iteration["status"]["render_state"] == "MISSING"
    assert manifest["final_stop_reason"] == "status_action_required"
    assert iteration["stop_reason"] == "status_action_required"
    assert iteration["patch_handoff"] is None
    assert iteration["recommended_next_action"] == (
        "run /fig_compile loop_demo to compile the TikZ source."
    )
    assert "stop_reason: status_action_required" in decision


def test_loop_fails_for_missing_fixture(tmp_path: Path) -> None:
    with pytest.raises(FigLoopError, match="not found"):
        run_loop(
            "missing",
            "inspect",
            repo_root=tmp_path,
            runs_root=tmp_path / ".scratch" / "fig-loop-runs",
        )


def test_git_mutation_commands_are_rejected() -> None:
    with pytest.raises(FigLoopError, match="git mutation"):
        ensure_safe_command(("git", "commit"))

    with pytest.raises(FigLoopError, match="git mutation"):
        ensure_safe_command(("git", "-C", ".", "commit"))

    assert ensure_safe_command(("uv", "run", "pytest")) == ("uv", "run", "pytest")
