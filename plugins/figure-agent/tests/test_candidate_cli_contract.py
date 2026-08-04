from __future__ import annotations

import json
import os
import subprocess
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
    build = fixture / "build"
    build.mkdir()
    (build / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "source_hashes": {
                    f"examples/{name}/{name}.tex": "sha256:"
                    + sha256((fixture / f"{name}.tex").read_bytes()).hexdigest()
                },
                "candidates": [
                    {
                        "id": "UG001",
                        "recommended_action": "add_micro_defect",
                        "source_line": 1,
                        "panel": "C",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return fixture


def _run(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), "python", str(FIG_AGENT), *args],
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


def test_fig_agent_attest_requires_interactive_terminal(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)

    result = _run(workspace, "attest", "candidate_demo")

    assert result.returncode == 1
    assert "human attestation requires an interactive terminal" in result.stderr
    assert not (fixture / "human_attestation.json").exists()


def test_fig_agent_analyze_panel_is_read_only_json(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "% Panel C\n\\node (label-a) at (0,0) {Old Label};\n",
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


def test_fig_agent_analyze_panel_can_select_a_fixture_local_repair_source(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    repair_source = fixture / "review" / "repair-candidate" / "repaired.tex"
    repair_source.parent.mkdir(parents=True)
    repair_source.write_text(
        "% Panel E\n\\node (derived-distribution) at (0,0) {$g(E_t)$};\n",
        encoding="utf-8",
    )
    before = _tree(workspace)

    result = _run(
        workspace,
        "analyze-panel",
        "candidate_demo",
        "E",
        "--source",
        "review/repair-candidate/repaired.tex",
        "--json",
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["selector_count"] == 1
    assert payload["selectors"][0]["path"] == (
        "examples/candidate_demo/review/repair-candidate/repaired.tex"
    )
    assert payload["inputs"]["source"] == (
        "examples/candidate_demo/review/repair-candidate/repaired.tex"
    )
    assert _tree(workspace) == before


def test_fig_agent_analyze_panel_rejects_unsafe_panel_id(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)

    result = _run(workspace, "analyze-panel", "candidate_demo", "../C", "--json")

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "invalid_panel_id" in result.stderr


def test_fig_agent_analyze_panel_rejects_a_source_outside_the_fixture(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    outside = workspace / "examples" / "outside.tex"
    outside.write_text("% Panel E\n\\node at (0,0) {outside};\n", encoding="utf-8")

    result = _run(
        workspace,
        "analyze-panel",
        "candidate_demo",
        "E",
        "--source",
        "../outside.tex",
        "--json",
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "source_path_escape" in result.stderr


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


def test_fig_agent_candidates_accepts_design_safe_family_aliases(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "% Panel C\n"
        "\\node[anchor=west, text width=2.0cm] at (3.0, 2.4) {mobility edge};\n"
        "\\node[anchor=west] at (3.0, 2.0) {shallow};\n"
        "\\draw[line width=0.50pt] (0,0) -- (1,0);\n"
        "\\fill[cAmber!12] (0,0) rectangle (1,1);\n",
        encoding="utf-8",
    )

    families = {
        "label_offset": "label_offset",
        "text_width_refit": "text_width_refit",
        "stroke_hierarchy_adjustment": "line_weight_style",
        "nonsemantic_background_quieting": "gradient_depth_fill",
    }
    for family, edit_class in families.items():
        result = _run(
            workspace,
            "candidates",
            "candidate_demo",
            "--panel",
            "C",
            "--family",
            family,
            "--json",
        )

        assert result.returncode == 0, result.stderr
        candidate = json.loads(result.stdout)["candidates"][0]
        assert candidate["family"] == family
        assert candidate["edit_class"] == edit_class
        assert candidate["candidate_hash"].startswith("sha256:")
        assert candidate["boundedness"]["not_svg_polish"] is True
        assert "fig-agent compile candidate_demo --strict" in candidate["verification"][
            "required_commands"
        ]


def test_fig_agent_candidates_refuses_unimplemented_family_aliases(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "candidate_demo.tex").write_text(
        "% Panel C\n\\node at (3.0, 2.4) {mobility edge};\n", encoding="utf-8"
    )
    for family in ("connector-routing", "panel-layout", "contrast-repair", "annotation-box-layout"):
        result = _run(
            workspace,
            "candidates",
            "candidate_demo",
            "--panel",
            "C",
            "--family",
            family,
            "--json",
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["candidates"] == []
        assert payload["refusals"] == [{"code": "edit_family_not_implemented"}]


def test_fig_agent_render_and_review_candidate_set(tmp_path: Path) -> None:
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
    assert review.returncode == 0, review.stderr
    assert compare.returncode == 0, compare.stderr
    assert manifest.exists()
    assert json.loads(render.stdout)["schema"] == "figure-agent.candidate-render-result.v1"
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
    assert candidates.returncode == 0, candidates.stderr
    assert render.returncode == 0, render.stderr
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


def test_fig_agent_acceptance_readiness_and_acceptance_cli(tmp_path: Path) -> None:
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
        "--evaluate",
        "--json",
    )
    manifest_path = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    render_manifest_path = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    (fixture / "candidate_demo.tex").write_text(
        "\\documentclass[border=8pt]{standalone}\n"
        "\\usepackage{polymer-paper-preamble}\n"
        "\\begin{document}\n"
        "\\begin{tikzpicture}\n"
        "\\node (label-a) at (0,0) {Old Label};\n"
        "\\end{tikzpicture}\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    source_hash = "sha256:" + sha256((fixture / "candidate_demo.tex").read_bytes()).hexdigest()
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
    apply = _run(
        workspace,
        "apply-candidate",
        "candidate_demo",
        "CAND001",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--acceptance",
        "build/candidates/CAND001/acceptance.json",
        "--json",
    )

    assert candidates.returncode == 0, candidates.stderr
    assert render.returncode == 0, render.stderr
    assert ready.returncode == 0, ready.stderr
    assert accept.returncode == 0, accept.stderr
    assert apply.returncode in {0, 1}, apply.stderr
    assert json.loads(ready.stdout)["status"] == "ready_for_local_acceptance"
    assert json.loads(accept.stdout)["path"] == "build/candidates/CAND001/acceptance.json"
    apply_payload = json.loads(apply.stdout)
    assert apply_payload["schema"] == "figure-agent.candidate-apply-result.v1"
    assert apply_payload["status"] in {"applied", "applied_with_failed_verification", "rolled_back"}
    assert set(apply_payload["post_apply"]) >= {
        "compile",
        "detector_recheck",
        "class_verifiers",
        "export",
        "status",
    }
    assert (fixture / "build" / "candidates" / "CAND001" / "acceptance.json").is_file()


def test_fig_agent_apply_candidate_exits_nonzero_when_post_apply_fails(
    tmp_path: Path,
) -> None:
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
        "--evaluate",
        "--json",
    )
    manifest_path = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    render_manifest_path = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    (fixture / "candidate_demo.tex").write_text(
        "\\documentclass[border=8pt]{standalone}\n"
        "\\usepackage{tikz}\n"
        "\\begin{document}\n"
        "\\begin{tikzpicture}\n"
        "\\node (label-a) at (0,0) {Old Label};\n"
        "\\end{tikzpicture}\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    source_hash = "sha256:" + sha256((fixture / "candidate_demo.tex").read_bytes()).hexdigest()
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
    apply = _run(
        workspace,
        "apply-candidate",
        "candidate_demo",
        "CAND001",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--acceptance",
        "build/candidates/CAND001/acceptance.json",
        "--json",
    )

    assert candidates.returncode == 0, candidates.stderr
    assert render.returncode == 0, render.stderr
    assert accept.returncode == 0, accept.stderr
    assert apply.returncode == 1
    payload = json.loads(apply.stdout)
    assert payload["status"] in {"applied_with_failed_verification", "rolled_back"}
    assert payload["post_apply"]["compile"]["status"] == "failed"


def test_fig_agent_evidence_sync_preview_and_write(tmp_path: Path) -> None:
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
        "--evaluate",
        "--json",
    )

    preview = _run(
        workspace,
        "evidence-sync",
        "candidate_demo",
        "--candidate-id",
        "CAND001",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--json",
    )
    write = _run(
        workspace,
        "evidence-sync",
        "candidate_demo",
        "--candidate-id",
        "CAND001",
        "--candidate-set",
        "build/candidates/candidate_set.json",
        "--write",
        "--json",
    )

    assert candidates.returncode == 0, candidates.stderr
    assert render.returncode == 0, render.stderr
    assert preview.returncode == 0, preview.stderr
    assert write.returncode == 0, write.stderr
    assert json.loads(preview.stdout)["mode"] == "preview"
    payload = json.loads(write.stdout)
    assert payload["mode"] == "write"
    assert payload["writes"] == ["build/evidence/evidence_index.json"]
    assert (fixture / "build" / "evidence" / "evidence_index.json").is_file()


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
