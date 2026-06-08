from __future__ import annotations

import json
import os
import subprocess
import sys
from hashlib import sha256
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
    (fixture / "spec.yaml").write_text(
        """
name: candidate_demo
panels:
  - id: C
    caption: Energy diagram
    bbox_pdf_cm: [0.0, 0.0, 1.0, 1.0]
""".strip()
        + "\n",
        encoding="utf-8",
    )
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


def test_fig_agent_analyze_panel_is_read_only_json(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "% Panel C\n"
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    before = _tree(workspace)

    result = _run(workspace, "analyze-panel", "candidate_demo", "C", "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.candidate-panel-model.v1"
    assert payload["panel"]["id"] == "C"
    assert payload["panel"]["bbox_pdf_cm"] == [0.0, 0.0, 1.0, 1.0]
    assert payload["selector_count"] == 1
    assert payload["visual_review"]["status"] == "missing_render"
    assert _tree(workspace) == before


def test_fig_agent_analyze_panel_rejects_unsafe_panel_id(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    result = _run(workspace, "analyze-panel", "candidate_demo", "../C", "--json")

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "invalid_panel_id" in result.stderr


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


def test_fig_agent_candidates_accepts_panel_family_filters(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "% Panel C\n"
        "\\coordinate (siteS1) at (1.0, 2.0);\n"
        "\\coordinate (siteD1) at (1.0, 1.0);\n"
        "\\node[anchor=west] at (3.0, 2.4) {mobility edge};\n"
        "\\node[anchor=west] at (3.0, 2.0) {shallow};\n"
        "\\node[anchor=west] at (3.0, 1.0) {deep};\n",
        encoding="utf-8",
    )

    result = _run(
        workspace,
        "candidates",
        "candidate_demo",
        "--panel",
        "C",
        "--family",
        "energy-trap-alignment",
        "--json",
        "--output",
        "build/candidates/panel_C_candidate_set.json",
    )

    output = fixture / "build" / "candidates" / "panel_C_candidate_set.json"
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["candidates"][0]["family"] == "energy-trap-alignment"
    assert payload["candidates"][0]["target"]["panel"] == "C"
    assert payload["candidates"][0]["candidate_hash"].startswith("sha256:")
    assert output.is_file()


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
    review = _run(
        workspace,
        "review-candidate",
        "candidate_demo",
        "CAND001",
        "--json",
    )
    compare = _run(
        workspace,
        "compare-candidate",
        "candidate_demo",
        "CAND001",
        "--json",
    )

    manifest = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    assert candidates.returncode == 0, candidates.stderr
    assert render.returncode == 0, render.stderr
    assert rank.returncode == 0, rank.stderr
    assert review.returncode == 0, review.stderr
    assert compare.returncode == 0, compare.stderr
    assert manifest.exists()
    assert json.loads(render.stdout)["schema"] == "figure-agent.candidate-render-result.v1"
    payload = json.loads(rank.stdout)
    assert payload["schema"] == "figure-agent.candidate-rank-result.v1"
    assert payload["scores"][0]["schema"] == "figure-agent.candidate-score.v1"
    assert payload["scores"][0]["candidate_id"] == "CAND001"
    review_payload = json.loads(review.stdout)
    assert review_payload["schema"] == "figure-agent.candidate-review-packet.v1"
    assert review_payload["candidate_id"] == "CAND001"
    compare_payload = json.loads(compare.stdout)
    assert compare_payload["schema"] == "figure-agent.candidate-review-packet.v1"
    assert compare_payload["candidate_id"] == "CAND001"
    assert compare_payload["visual_review"]["status"] == "missing_render"


def test_fig_agent_render_candidates_accepts_evaluation_flags(tmp_path: Path) -> None:
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
        "--candidate-id",
        "CAND001",
        "--compile",
        "--export",
        "--crop-panel",
        "C",
        "--evaluate",
        "--json",
    )
    rank = _run(
        workspace,
        "rank-candidates",
        "candidate_demo",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--json",
    )

    assert candidates.returncode == 0, candidates.stderr
    assert render.returncode == 0, render.stderr
    assert rank.returncode == 0, rank.stderr
    payload = json.loads(render.stdout)
    assert payload["rendered"] == [
        {
            "candidate_id": "CAND001",
            "manifest": "build/candidates/CAND001/candidate_manifest.json",
            "render_manifest": "build/candidates/CAND001/render_manifest.json",
        }
    ]
    render_manifest = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    assert json.loads(render_manifest.read_text(encoding="utf-8"))["stages"]["evaluate"][
        "status"
    ] in {"dependency_missing", "blocked", "rendered_needs_human_review"}
    rank_payload = json.loads(rank.stdout)
    assert rank_payload["scores"][0]["render_status"] != "not_rendered"


def test_fig_agent_acceptance_readiness_and_acceptance_cli(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source_hash = "sha256:" + sha256(
        (fixture / "candidate_demo.tex").read_bytes()
    ).hexdigest()

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
        "--candidate-id",
        "CAND001",
        "--compile",
        "--export",
        "--evaluate",
        "--json",
    )
    manifest_path = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    render_manifest_path = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["operations"][0]["source_sha256"] = source_hash
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    render_manifest = json.loads(render_manifest_path.read_text(encoding="utf-8"))
    render_manifest["stages"] = {
        "compile": {"status": "success"},
        "export": {"status": "success"},
        "crop": {"status": "success"},
        "evaluate": {"status": "rendered_needs_human_review"},
    }
    render_manifest_path.write_text(
        json.dumps(render_manifest, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    ready = _run(
        workspace,
        "apply-candidate-ready",
        "candidate_demo",
        "CAND001",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--json",
    )
    accept = _run(
        workspace,
        "accept-candidate",
        "candidate_demo",
        "CAND001",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--decision",
        "accept",
        "--reviewer",
        "local-user",
        "--rationale",
        "Rendered evidence reviewed.",
        "--json",
    )

    assert candidates.returncode == 0, candidates.stderr
    assert render.returncode == 0, render.stderr
    assert ready.returncode == 0, ready.stderr
    assert accept.returncode == 0, accept.stderr
    assert json.loads(ready.stdout)["status"] == "ready_for_local_acceptance"
    assert json.loads(accept.stdout)["path"] == "build/candidates/CAND001/acceptance.json"
    assert (fixture / "build" / "candidates" / "CAND001" / "acceptance.json").is_file()


def test_fig_agent_candidates_output_escape_is_user_error(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    result = _run(
        workspace,
        "candidates",
        "candidate_demo",
        "--json",
        "--output",
        "../escape.json",
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "path_escape" in result.stderr
    assert not (workspace / "examples" / "escape.json").exists()


def test_fig_agent_render_invalid_json_is_user_error(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set = fixture / "build" / "candidates" / "candidate_set.json"
    candidate_set.parent.mkdir(parents=True)
    candidate_set.write_text("{not-json", encoding="utf-8")

    result = _run(
        workspace,
        "render-candidates",
        "candidate_demo",
        "--candidate-set",
        "build/candidates/candidate_set.json",
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "render-candidates" in result.stderr


def test_fig_agent_rank_rejects_candidate_id_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set = fixture / "build" / "candidates" / "candidate_set.json"
    secret_manifest = fixture / "build" / "secret" / "candidate_manifest.json"
    candidate_set.parent.mkdir(parents=True)
    secret_manifest.parent.mkdir(parents=True)
    candidate_set.write_text(
        json.dumps({"candidates": [{"id": "../secret"}]}) + "\n",
        encoding="utf-8",
    )
    secret_manifest.write_text(
        json.dumps(
            {
                "candidate_id": "SECRET",
                "apply_authority": "apply_eligible",
                "verification": {"hard_gate_state": "pass"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = _run(
        workspace,
        "rank-candidates",
        "candidate_demo",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--json",
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "fixture name must be a single" in result.stderr
    assert result.stdout == ""
