from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_generator  # noqa: E402
import candidate_render  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402


def _fixture(workspace: Path, name: str = "candidate_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "reference").mkdir()
    (fixture / "reference" / "panel_a.png").write_bytes(b"fake")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / "spec.yaml").write_text(
        """
name: candidate_demo
panels:
  - id: A
    reference_image: reference/panel_a.png
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (fixture / f"{name}.tex").write_text(
        "\\node (label-a) at (0,0) {Old Label};\n",
        encoding="utf-8",
    )
    return fixture


def _write_undeclared_candidate_defect(fixture: Path) -> None:
    build = fixture / "build"
    build.mkdir(exist_ok=True)
    (build / "undeclared_geometry.json").write_text(
        json.dumps(
            {
                "source_hashes": {
                    "examples/candidate_demo/candidate_demo.tex": file_sha256(
                        fixture / "candidate_demo.tex"
                    )
                },
                "candidates": [
                    {
                        "id": "UG001",
                        "recommended_action": "add_micro_defect",
                        "source_line": 1,
                        "panel": "A",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _candidate_set(workspace: Path, fixture: Path) -> dict:
    _write_undeclared_candidate_defect(fixture)
    return candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )


def _minimal_candidate_set() -> dict:
    return {
        "schema": "figure-agent.candidate-set.v1",
        "fixture": "candidate_demo",
        "base": {
            "tex_hash": "sha256:" + "0" * 64,
            "status_hash": "sha256:" + "0" * 64,
            "intent_model_hash": "sha256:" + "0" * 64,
        },
        "candidates": [
            {
                "id": "CAND001",
                "candidate_hash": "sha256:" + "1" * 64,
                "target": {"panel": "unknown"},
                "operations": [],
                "apply_authority": "review_only",
            }
        ],
        "refusals": [],
    }


def _ppm(width: int, height: int, pixels: list[tuple[int, int, int]]) -> bytes:
    values = " ".join(f"{red} {green} {blue}" for red, green, blue in pixels)
    return f"P3\n{width} {height}\n255\n{values}\n".encode("ascii")


def test_render_writes_manifest_without_touching_exports(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    exports = fixture / "exports"
    exports.mkdir()
    (exports / "candidate_demo.svg").write_text("<svg />\n", encoding="utf-8")
    before_exports = {
        path.relative_to(exports).as_posix(): path.read_bytes()
        for path in sorted(exports.rglob("*"))
        if path.is_file()
    }
    candidate_set = _candidate_set(workspace, fixture)
    candidate_set["candidates"][0]["candidate_hash"] = "sha256:" + "3" * 64
    candidate_set["candidates"][0]["target"]["panel"] = "C"
    candidate_set["candidates"][0]["selectors"] = [
        {"kind": "tex_selector.v1", "line_start": 1, "line_end": 1}
    ]
    candidate_set["candidates"][0]["visual_review"] = {"status": "missing_render"}

    result = candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
        candidate_set_path=Path("build/candidates/panel_C_candidate_set.json"),
    )

    manifest = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    assert result["rendered"][0]["candidate_id"] == "CAND001"
    assert result["rendered"][0]["manifest"] == "build/candidates/CAND001/candidate_manifest.json"
    assert manifest.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["schema"] == "figure-agent.candidate-manifest.v1"
    assert data["base"]["source_commit"]
    assert data["tool_versions"]["fig_agent"]
    assert data["tool_versions"]["tex_engine"] == "not_run"
    assert data["candidate_hash"] == "sha256:" + "3" * 64
    assert data["source_defect"]["id"] == "QD001"
    assert data["edit_class"] == "label_offset"
    assert data["edit_family"] == "bounded_coordinate_offset"
    assert data["family"] == "bounded-coordinate-offset"
    assert data["variant_id"] == "dx+0.10cm"
    assert data["operations"][0]["semantic_kind"] == "bounded_coordinate_offset"
    assert data["panel"] == "C"
    assert data["selectors"] == [{"kind": "tex_selector.v1", "line_start": 1, "line_end": 1}]
    assert data["candidate_set_path"] == "build/candidates/panel_C_candidate_set.json"
    assert data["stages"] == {
        "prepare": "passed",
        "compile": "not_run",
        "export": "not_run",
        "crop": "not_run",
    }
    assert data["visual_review"] == {"status": "missing_render"}
    assert data["verification"]["hard_gate_state"] == "human_required"
    assert data["effective_apply_authority"] == "review_only"
    after_exports = {
        path.relative_to(exports).as_posix(): path.read_bytes()
        for path in sorted(exports.rglob("*"))
        if path.is_file()
    }
    assert after_exports == before_exports


def test_render_source_copy_respects_line_scoped_replace_text(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    repeated = "\\draw[cGray!55!black, line width=0.30pt] (0,0) -- (1,0);\n"
    (fixture / "candidate_demo.tex").write_text(repeated + repeated, encoding="utf-8")
    candidate_set = {
        **_minimal_candidate_set(),
        "candidates": [
            {
                "id": "CAND001",
                "candidate_hash": "sha256:" + "1" * 64,
                "target": {"panel": "F"},
                "selectors": [{"kind": "tex_selector.v1", "line_start": 2, "line_end": 2}],
                "operations": [
                    {
                        "kind": "replace_text",
                        "path": "examples/candidate_demo/candidate_demo.tex",
                        "line_start": 2,
                        "line_end": 2,
                        "original": repeated.rstrip("\n"),
                        "replacement": repeated.replace("0.30pt", "0.80pt").rstrip("\n"),
                    }
                ],
                "apply_authority": "review_only",
            }
        ],
    }

    candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
    )

    sandbox_source = fixture / "build" / "candidates" / "CAND001" / "candidate_demo.tex"
    assert sandbox_source.read_text(encoding="utf-8") == (
        repeated + repeated.replace("0.30pt", "0.80pt")
    )


def test_render_source_copy_respects_exact_multiline_replace_text(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = "\n".join(
        [
            "% Panel F -- mechanical",
            "\\begin{scope}[shift={(9.5,0)}]",
            "\\draw[cGray!64!black, line width=0.34pt] (0,0) rectangle (1,1);",
            "\\node at (0.5,0.5) {Coulomb repulsion};",
            "\\end{scope}",
        ]
    ) + "\n"
    replacement = source.replace("line width=0.34pt", "line width=0.92pt").replace(
        "{Coulomb repulsion}",
        "{Coulomb repulsion strengthened}",
    )
    (fixture / "candidate_demo.tex").write_text(source, encoding="utf-8")
    candidate_set = {
        **_minimal_candidate_set(),
        "candidates": [
            {
                "id": "CAND001",
                "candidate_hash": "sha256:" + "1" * 64,
                "target": {"panel": "F"},
                "selectors": [{"kind": "tex_selector.v1", "line_start": 2, "line_end": 5}],
                "operations": [
                    {
                        "kind": "replace_text",
                        "path": "examples/candidate_demo/candidate_demo.tex",
                        "line_start": 2,
                        "line_end": 5,
                        "original": "".join(source.splitlines(keepends=True)[1:5]),
                        "replacement": "".join(replacement.splitlines(keepends=True)[1:5]),
                    }
                ],
                "apply_authority": "review_only",
            }
        ],
    }

    candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
    )

    sandbox_source = fixture / "build" / "candidates" / "CAND001" / "candidate_demo.tex"
    assert sandbox_source.read_text(encoding="utf-8") == replacement
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == source


def test_render_rejects_multiline_replace_text_when_range_does_not_match(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = "alpha\nbeta\ngamma\n"
    (fixture / "candidate_demo.tex").write_text(source, encoding="utf-8")
    candidate_set = {
        **_minimal_candidate_set(),
        "candidates": [
            {
                "id": "CAND001",
                "candidate_hash": "sha256:" + "1" * 64,
                "target": {"panel": "F"},
                "selectors": [{"kind": "tex_selector.v1", "line_start": 1, "line_end": 3}],
                "operations": [
                    {
                        "kind": "replace_text",
                        "path": "examples/candidate_demo/candidate_demo.tex",
                        "line_start": 1,
                        "line_end": 2,
                        "original": "alpha\nbeta\ngamma\n",
                        "replacement": "ALPHA\nBETA\nGAMMA\n",
                    }
                ],
                "apply_authority": "review_only",
            }
        ],
    }

    with pytest.raises(candidate_render.CandidateRenderError, match="original not found"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
        )


def test_render_compile_request_writes_render_manifest_dependency_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set = _candidate_set(workspace, fixture)
    monkeypatch.setattr(candidate_render, "_which", lambda _name: None, raising=False)

    result = candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
        compile=True,
        export=True,
        crop_panel="C",
        evaluate=True,
    )

    render_manifest = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    assert render_manifest.is_file()
    data = json.loads(render_manifest.read_text(encoding="utf-8"))
    assert result["rendered"][0]["render_manifest"] == (
        "build/candidates/CAND001/render_manifest.json"
    )
    assert data["schema"] == "figure-agent.candidate-render-manifest.v1"
    assert data["figure_name"] == "candidate_demo"
    assert data["candidate_id"] == "CAND001"
    assert data["candidate_set_path"] == "build/candidates/candidate_set.json"
    assert data["sandbox_path"] == "build/candidates/CAND001"
    assert data["stages"]["prepare"]["status"] == "success"
    assert data["stages"]["compile"]["status"] == "dependency_missing"
    assert data["stages"]["export"]["status"] == "not_run"
    assert data["stages"]["crop"]["status"] == "not_run"
    assert data["stages"]["evaluate"]["status"] == "dependency_missing"
    assert data["diagnostics"] == [
        {
            "stage": "compile",
            "category": "dependency_missing",
            "dependency": "lualatex",
            "message": "lualatex not found",
        }
    ]
    assert data["artifacts"]["source_copy"] == "build/candidates/CAND001/source/candidate.tex"
    assert not (fixture / "build" / "candidate_demo.pdf").exists()


def test_render_compile_export_success_writes_sandbox_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set = _candidate_set(workspace, fixture)
    calls: list[list[str]] = []

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        if command[0] == "lualatex":
            (cwd / "render" / "candidate.pdf").write_bytes(b"%PDF-1.7\n")
        if command[0] == "pdftocairo":
            (cwd / "render" / "candidate.png").write_bytes(b"png")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(candidate_render, "_which", lambda name: f"/fake/{name}")
    monkeypatch.setattr(candidate_render, "_run_process", fake_run)

    candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
        compile=True,
        export=True,
        evaluate=True,
    )

    render_manifest = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    data = json.loads(render_manifest.read_text(encoding="utf-8"))
    assert calls[0][:3] == ["lualatex", "-interaction=nonstopmode", "-halt-on-error"]
    assert calls[1][0] == "pdftocairo"
    assert data["stages"]["compile"]["status"] == "success"
    assert data["stages"]["export"]["status"] == "success"
    assert data["stages"]["evaluate"]["status"] == "rendered_needs_human_review"
    assert data["artifacts"]["pdf"] == "build/candidates/CAND001/render/candidate.pdf"
    assert data["artifacts"]["png"] == "build/candidates/CAND001/render/candidate.png"
    assert not (fixture / "build" / "candidate_demo.pdf").exists()


def test_render_crop_panel_writes_before_after_sandbox_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "build").mkdir()
    (fixture / "build" / "candidate_demo.png").write_bytes(b"original-png")
    candidate_set = _candidate_set(workspace, fixture)

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        if command[0] == "lualatex":
            (cwd / "render" / "candidate.pdf").write_bytes(b"%PDF-1.7\n")
        if command[0] == "pdftocairo":
            (cwd / "render" / "candidate.png").write_bytes(b"candidate-png")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(candidate_render, "_which", lambda name: f"/fake/{name}")
    monkeypatch.setattr(candidate_render, "_run_process", fake_run)

    candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
        compile=True,
        export=True,
        crop_panel="C",
    )

    render_manifest = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    data = json.loads(render_manifest.read_text(encoding="utf-8"))
    assert data["stages"]["crop"]["status"] == "success"
    assert data["artifacts"]["before_crop"] == (
        "build/candidates/CAND001/crops/original_panel_C.png"
    )
    assert data["artifacts"]["after_crop"] == (
        "build/candidates/CAND001/crops/candidate_panel_C.png"
    )
    assert (
        fixture / "build" / "candidates" / "CAND001" / "crops" / "original_panel_C.png"
    ).read_bytes() == b"original-png"
    assert (
        fixture / "build" / "candidates" / "CAND001" / "crops" / "candidate_panel_C.png"
    ).read_bytes() == b"candidate-png"


def test_render_evaluate_records_visual_delta_when_crops_are_comparable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "build").mkdir()
    (fixture / "build" / "candidate_demo.png").write_bytes(
        _ppm(2, 1, [(255, 255, 255), (255, 255, 255)])
    )
    candidate_set = _candidate_set(workspace, fixture)

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        if command[0] == "lualatex":
            (cwd / "render" / "candidate.pdf").write_bytes(b"%PDF-1.7\n")
        if command[0] == "pdftocairo":
            (cwd / "render" / "candidate.png").write_bytes(_ppm(2, 1, [(255, 255, 255), (0, 0, 0)]))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(candidate_render, "_which", lambda name: f"/fake/{name}")
    monkeypatch.setattr(candidate_render, "_run_process", fake_run)

    candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
        compile=True,
        export=True,
        crop_panel="C",
        evaluate=True,
    )

    render_manifest = fixture / "build" / "candidates" / "CAND001" / "render_manifest.json"
    data = json.loads(render_manifest.read_text(encoding="utf-8"))
    assert data["stages"]["evaluate"]["status"] == "rendered_needs_human_review"
    assert data["visual_deltas"]["pixel_diff_max"] == 255
    assert data["visual_deltas"]["changed_bbox"] == [1, 0, 1, 0]


def test_render_canonicalizes_candidate_set_path(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set = _candidate_set(workspace, fixture)

    candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
        candidate_set_path=fixture / "build" / "candidates" / "panel_C_candidate_set.json",
    )

    manifest = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["candidate_set_path"] == "build/candidates/panel_C_candidate_set.json"


def test_render_writes_candidate_source_copy_only_in_sandbox(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    original = (fixture / "candidate_demo.tex").read_text(encoding="utf-8")
    candidate_set = _candidate_set(workspace, fixture)

    candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
    )

    sandbox_source = fixture / "build" / "candidates" / "CAND001" / "candidate_demo.tex"
    assert sandbox_source.read_text(encoding="utf-8") == (
        "\\node (label-a) at (0.10, 0) {Old Label};\n"
    )
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == original


def test_render_records_operation_source_hash_for_apply_drift_gate(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set = _candidate_set(workspace, fixture)

    candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
    )

    manifest = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    source_hash = (
        "sha256:" + hashlib.sha256((fixture / "candidate_demo.tex").read_bytes()).hexdigest()
    )
    assert data["operations"][0]["source_sha256"] == source_hash


def test_render_preserves_review_only_authority(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    (fixture / "spec.yaml").write_text(
        """
name: candidate_demo
panels:
  - id: A
    reference_image: missing.png
""".strip()
        + "\n",
        encoding="utf-8",
    )
    candidate_set = _candidate_set(workspace, fixture)

    candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
    )

    manifest = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["apply_authority"] == "review_only"
    assert data["effective_apply_authority"] == "review_only"


def test_render_rejects_candidate_id_path_escape(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    candidate_set = _minimal_candidate_set()
    candidate_set["candidates"][0]["id"] = "../escape"

    with pytest.raises(candidate_render.CandidateRenderError, match="candidate_id"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
        )


def test_render_rejects_sandbox_source_copy_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    candidate_set = _candidate_set(workspace, fixture)
    sandbox = fixture / "build" / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    source = fixture / "candidate_demo.tex"
    before = source.read_text(encoding="utf-8")
    (sandbox / "candidate_demo.tex").symlink_to(source)

    with pytest.raises(candidate_render.CandidateRenderError, match="sandbox_symlink_forbidden"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
        )

    assert source.read_text(encoding="utf-8") == before


def test_render_rejects_sandbox_manifest_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    exports = fixture / "exports"
    exports.mkdir()
    export = exports / "candidate_demo.svg"
    export.write_text("<svg />\n", encoding="utf-8")
    candidate_set = _minimal_candidate_set()
    sandbox = fixture / "build" / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    (sandbox / "candidate_manifest.json").symlink_to(export)

    with pytest.raises(candidate_render.CandidateRenderError, match="sandbox_symlink_forbidden"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
        )

    assert export.read_text(encoding="utf-8") == "<svg />\n"


def test_render_rejects_render_manifest_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    exports = fixture / "exports"
    exports.mkdir()
    export = exports / "candidate_demo.svg"
    export.write_text("<svg />\n", encoding="utf-8")
    candidate_set = _minimal_candidate_set()
    sandbox = fixture / "build" / "candidates" / "CAND001"
    sandbox.mkdir(parents=True)
    (sandbox / "render_manifest.json").symlink_to(export)

    with pytest.raises(candidate_render.CandidateRenderError, match="sandbox_symlink_forbidden"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
            evaluate=True,
        )

    assert export.read_text(encoding="utf-8") == "<svg />\n"


def test_render_rejects_render_source_copy_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    source = fixture / "candidate_demo.tex"
    before = source.read_text(encoding="utf-8")
    candidate_set = _candidate_set(workspace, fixture)
    render_source_dir = fixture / "build" / "candidates" / "CAND001" / "source"
    render_source_dir.mkdir(parents=True)
    (render_source_dir / "candidate.tex").symlink_to(source)

    with pytest.raises(candidate_render.CandidateRenderError, match="sandbox_symlink_forbidden"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
            evaluate=True,
        )

    assert source.read_text(encoding="utf-8") == before


def test_render_rejects_render_source_directory_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    outside = tmp_path / "outside"
    outside.mkdir()
    candidate_set = _candidate_set(workspace, fixture)
    render_source_dir = fixture / "build" / "candidates" / "CAND001" / "source"
    render_source_dir.parent.mkdir(parents=True)
    render_source_dir.symlink_to(outside)

    with pytest.raises(candidate_render.CandidateRenderError, match="sandbox_symlink_forbidden"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
            evaluate=True,
        )

    assert list(outside.iterdir()) == []


def test_render_rejects_render_directory_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    outside = tmp_path / "outside"
    outside.mkdir()
    candidate_set = _candidate_set(workspace, fixture)
    render_dir = fixture / "build" / "candidates" / "CAND001" / "render"
    render_dir.parent.mkdir(parents=True)
    render_dir.symlink_to(outside)

    with pytest.raises(candidate_render.CandidateRenderError, match="sandbox_symlink_forbidden"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
            compile=True,
        )

    assert list(outside.iterdir()) == []


def test_render_rejects_crops_directory_symlink(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    outside = tmp_path / "outside"
    outside.mkdir()
    (fixture / "build").mkdir()
    (fixture / "build" / "candidate_demo.png").write_bytes(b"original-png")
    candidate_set = _candidate_set(workspace, fixture)
    crops_dir = fixture / "build" / "candidates" / "CAND001" / "crops"
    crops_dir.parent.mkdir(parents=True)
    crops_dir.symlink_to(outside)

    with pytest.raises(candidate_render.CandidateRenderError, match="sandbox_symlink_forbidden"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
            crop_panel="C",
        )

    assert list(outside.iterdir()) == []


def test_render_rejects_unsafe_crop_panel_before_path_use(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _fixture(workspace)
    candidate_set = _minimal_candidate_set()

    with pytest.raises(candidate_render.CandidateRenderError, match="invalid crop_panel"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
            crop_panel="../escape",
        )


def test_render_rejects_sandbox_root_symlink_to_exports(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    exports = fixture / "exports"
    exports.mkdir()
    candidates_parent = fixture / "build"
    candidates_parent.mkdir()
    (candidates_parent / "candidates").symlink_to(exports)
    candidate_set = _minimal_candidate_set()

    with pytest.raises(candidate_render.CandidateRenderError, match="sandbox_symlink_forbidden"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
        )

    assert list(exports.rglob("*")) == []


def test_render_rejects_build_dir_symlink_to_exports(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    exports = fixture / "exports"
    exports.mkdir()
    (fixture / "build").symlink_to(exports)
    candidate_set = _minimal_candidate_set()

    with pytest.raises(candidate_render.CandidateRenderError, match="sandbox_symlink_forbidden"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
        )

    assert list(exports.rglob("*")) == []
