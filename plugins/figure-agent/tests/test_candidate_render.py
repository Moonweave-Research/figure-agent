from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_generator  # noqa: E402
import candidate_render  # noqa: E402


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
    candidate_set = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    result = candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
    )

    manifest = fixture / "build" / "candidates" / "CAND001" / "candidate_manifest.json"
    assert result["rendered"][0]["candidate_id"] == "CAND001"
    assert manifest.is_file()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["schema"] == "figure-agent.candidate-manifest.v1"
    assert data["base"]["source_commit"]
    assert data["tool_versions"]["fig_agent"]
    assert data["tool_versions"]["tex_engine"] == "not_run"
    assert data["verification"]["hard_gate_state"] == "human_required"
    assert data["effective_apply_authority"] == "review_only"
    after_exports = {
        path.relative_to(exports).as_posix(): path.read_bytes()
        for path in sorted(exports.rglob("*"))
        if path.is_file()
    }
    assert after_exports == before_exports


def test_render_writes_candidate_source_copy_only_in_sandbox(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    original = (fixture / "candidate_demo.tex").read_text(encoding="utf-8")
    candidate_set = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    candidate_render.render_candidate_set(
        "candidate_demo",
        candidate_set,
        workspace_root=workspace,
    )

    sandbox_source = (
        fixture / "build" / "candidates" / "CAND001" / "candidate_demo.tex"
    )
    assert sandbox_source.read_text(encoding="utf-8") == (
        "\\node (label-a) at (0.2,0) {Old Label};\n"
    )
    assert (fixture / "candidate_demo.tex").read_text(encoding="utf-8") == original


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
    candidate_set = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

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
    candidate_set = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )
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
    candidate_set = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )
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
    candidate_set = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )
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


def test_render_rejects_sandbox_root_symlink_to_exports(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _fixture(workspace)
    exports = fixture / "exports"
    exports.mkdir()
    candidates_parent = fixture / "build"
    candidates_parent.mkdir()
    (candidates_parent / "candidates").symlink_to(exports)
    candidate_set = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

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
    candidate_set = candidate_generator.build_candidate_set(
        "candidate_demo",
        workspace_root=workspace,
    )

    with pytest.raises(candidate_render.CandidateRenderError, match="sandbox_symlink_forbidden"):
        candidate_render.render_candidate_set(
            "candidate_demo",
            candidate_set,
            workspace_root=workspace,
        )

    assert list(exports.rglob("*")) == []
