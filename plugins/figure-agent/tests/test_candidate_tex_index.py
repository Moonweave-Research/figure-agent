from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import candidate_tex_index  # noqa: E402


def _fixture_with_tex(tmp_path: Path, text: str, name: str = "candidate_demo") -> Path:
    workspace = tmp_path / "workspace"
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: candidate_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(text, encoding="utf-8")
    return fixture


def test_panel_boundaries_use_comments_but_only_active_commands_are_elements(
    tmp_path: Path,
) -> None:
    _fixture_with_tex(
        tmp_path,
        "% Panel C -- Energy\n"
        "% shallow only comment\n"
        "\\draw (0,0) -- (1,0);\n"
        "% Panel D\n"
        "\\node at (0,0) {not C};\n",
    )

    index = candidate_tex_index.build_tex_index(
        "candidate_demo",
        workspace_root=tmp_path / "workspace",
    )

    panel_c = [item for item in index["selectors"] if item["panel"] == "C"]
    assert index["schema"] == "figure-agent.candidate-tex-index.v1"
    assert len(panel_c) == 1
    assert panel_c[0]["line_start"] == 3
    assert panel_c[0]["line_end"] == 3
    assert panel_c[0]["selector_text_hash"].startswith("sha256:")
    assert "shallow only comment" not in panel_c[0]["text"]


def test_multiline_draw_selector_captures_full_command(tmp_path: Path) -> None:
    _fixture_with_tex(
        tmp_path,
        "% Panel C\n"
        "\\draw[red]\n"
        "  (0,0) --\n"
        "  (1,0);\n",
    )

    index = candidate_tex_index.build_tex_index(
        "candidate_demo",
        workspace_root=tmp_path / "workspace",
    )

    selector = index["selectors"][0]
    assert selector["line_start"] == 2
    assert selector["line_end"] == 4
    assert selector["text"] == "\\draw[red]\n  (0,0) --\n  (1,0);"


def test_comment_only_panel_does_not_produce_selectors(tmp_path: Path) -> None:
    _fixture_with_tex(
        tmp_path,
        "% Panel C\n"
        "% \\draw (0,0) -- (1,0);\n"
        "% shallow deep mobility edge\n",
    )

    index = candidate_tex_index.build_tex_index(
        "candidate_demo",
        workspace_root=tmp_path / "workspace",
    )

    assert index["selectors"] == []


def test_tex_index_rejects_symlinked_source(tmp_path: Path) -> None:
    fixture = _fixture_with_tex(tmp_path, "\\draw (0,0) -- (1,0);\n")
    source = fixture / "candidate_demo.tex"
    source.unlink()
    outside = tmp_path / "outside.tex"
    outside.write_text("\\draw (9,9) -- (10,10);\n", encoding="utf-8")
    source.symlink_to(outside)

    with pytest.raises(candidate_tex_index.CandidateTexIndexError, match="source_symlink"):
        candidate_tex_index.build_tex_index(
            "candidate_demo",
            workspace_root=tmp_path / "workspace",
        )


def test_dirty_metadata_is_scoped_to_selected_fixture(tmp_path: Path) -> None:
    _fixture_with_tex(tmp_path, "\\draw (0,0) -- (1,0);\n", name="candidate_demo")
    _fixture_with_tex(tmp_path, "\\draw (2,0) -- (3,0);\n", name="other_demo")
    workspace = tmp_path / "workspace"
    subprocess.run(["git", "init"], cwd=workspace, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.test"],
        cwd=workspace,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=workspace,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "examples"], cwd=workspace, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=workspace, check=True, capture_output=True)
    (workspace / "examples" / "other_demo" / "other_demo.tex").write_text(
        "\\draw (9,0) -- (10,0);\n",
        encoding="utf-8",
    )

    index = candidate_tex_index.build_tex_index(
        "candidate_demo",
        workspace_root=workspace,
    )

    assert index["fixture_dirty"] is False
    assert index["affected_files_dirty"] is False
