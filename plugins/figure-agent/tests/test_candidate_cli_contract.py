from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def _fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: candidate_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    return fixture


def _run(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(FIG_AGENT), *args],
        cwd=workspace,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )


def _tree(workspace: Path) -> list[str]:
    return sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))


def test_fig_agent_intent_and_candidates_are_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    before = _tree(workspace)

    intent = _run(workspace, "intent", "candidate_demo", "--json")
    candidates = _run(workspace, "candidates", "candidate_demo", "--json")

    assert intent.returncode == 0, intent.stderr
    assert candidates.returncode == 0, candidates.stderr
    assert json.loads(intent.stdout)["schema"] == "figure-agent.intent-model.v1"
    assert json.loads(candidates.stdout)["schema"] == "figure-agent.candidate-set.v1"
    assert _tree(workspace) == before


def test_fig_agent_candidates_output_is_fixture_local(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)

    result = _run(
        workspace,
        "candidates",
        "candidate_demo",
        "--json",
        "--output",
        "build/candidates/candidate_set.json",
    )

    output = fixture / "build" / "candidates" / "candidate_set.json"
    assert result.returncode == 0, result.stderr
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["schema"] == (
        "figure-agent.candidate-set.v1"
    )


def test_fig_agent_render_and_rank_candidate_set(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)

    candidates = _run(
        workspace,
        "candidates",
        "candidate_demo",
        "--json",
        "--output",
        "build/candidates/candidate_set.json",
    )
    render = _run(
        workspace,
        "render-candidates",
        "candidate_demo",
        "--candidate-set",
        "build/candidates/candidate_set.json",
    )
    rank = _run(
        workspace,
        "rank-candidates",
        "candidate_demo",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--json",
    )

    manifest = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    assert candidates.returncode == 0, candidates.stderr
    assert render.returncode == 0, render.stderr
    assert rank.returncode == 0, rank.stderr
    assert manifest.exists()
    assert json.loads(render.stdout)["schema"] == "figure-agent.candidate-render-result.v1"
    payload = json.loads(rank.stdout)
    assert payload["schema"] == "figure-agent.candidate-rank-result.v1"
    assert payload["scores"][0]["schema"] == "figure-agent.candidate-score.v1"
    assert payload["scores"][0]["candidate_id"] == "CAND001"
