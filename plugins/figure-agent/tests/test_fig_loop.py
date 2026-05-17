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


def _write_adjudication(fixture: Path, critique_hash: str) -> None:
    (fixture / "critique_adjudication.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.critique-adjudication.v1",
                "fixture": fixture.name,
                "source_critique_hash": critique_hash,
                "decisions": [
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
    assert manifest["final_stop_reason"] == "verify_only_complete"
    assert iteration["status"]["stage"] == 1
    assert iteration["adjudication"]["state"] == "missing"
    assert "verify_only_complete" in decision


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
