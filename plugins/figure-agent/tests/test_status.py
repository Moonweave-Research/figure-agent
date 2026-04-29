"""Tests for scripts/status.py — infer_stage contract."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from status import infer_stage  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _make_spec(directory: Path, selected_preview: str | None = None) -> None:
    preview_val = selected_preview if selected_preview else "null"
    content = (
        f"name: {directory.name}\npanels: []\nstyle_profile: polymer-default\n"
        f"selected_preview: {preview_val}\n"
    )
    (directory / "spec.yaml").write_text(content, encoding="utf-8")


def test_stage_0_missing_directory(tmp_path: Path) -> None:
    result = infer_stage(tmp_path / "nonexistent")
    assert result["stage"] == 0


def test_stage_1_spec_only_empty_previews(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    previews = fig_dir / "previews"
    previews.mkdir()
    result = infer_stage(fig_dir)
    assert result["stage"] == 1


def test_stage_2_previews_has_image_selected_preview_null(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview=None)
    previews = fig_dir / "previews"
    previews.mkdir()
    (previews / ".gitkeep").touch()
    (previews / "candidate_01.png").write_bytes(b"\x89PNG")
    result = infer_stage(fig_dir)
    assert result["stage"] == 2


def test_stage_3_selected_preview_set_no_tex(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview="chosen.png")
    previews = fig_dir / "previews"
    previews.mkdir()
    (previews / ".gitkeep").touch()
    result = infer_stage(fig_dir)
    assert result["stage"] == 3


def test_stage_4_tex_stale_pdf(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview="chosen.png")
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    pdf = build_dir / "myfig.pdf"
    pdf.write_bytes(b"%PDF")
    # Make tex newer than pdf
    old_time = time.time() - 100
    os.utime(pdf, (old_time, old_time))
    new_time = time.time() - 10
    os.utime(tex, (new_time, new_time))
    result = infer_stage(fig_dir)
    assert result["stage"] == 4


def test_stage_4_tex_no_build_pdf(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    result = infer_stage(fig_dir)
    assert result["stage"] == 4


def test_stage_5_fresh_pdf_no_exports(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    pdf = build_dir / "myfig.pdf"
    pdf.write_bytes(b"%PDF")
    # Make pdf newer than tex
    old_time = time.time() - 100
    os.utime(tex, (old_time, old_time))
    new_time = time.time() - 10
    os.utime(pdf, (new_time, new_time))
    result = infer_stage(fig_dir)
    assert result["stage"] == 5


def test_stage_6_partial_export_svg_only(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    (exports_dir / "myfig.svg").write_bytes(b"<svg/>")
    result = infer_stage(fig_dir)
    assert result["stage"] == 6
    assert "partial_export" in result["notes"]


def test_stage_6_all_four_exports_no_note(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    (exports_dir / "myfig.pdf").write_bytes(b"%PDF")
    (exports_dir / "myfig.svg").write_bytes(b"<svg/>")
    (exports_dir / "myfig.tif").write_bytes(b"TIFF")
    (exports_dir / "myfig.png").write_bytes(b"\x89PNG")
    result = infer_stage(fig_dir)
    assert result["stage"] == 6
    assert "partial_export" not in result["notes"]


def test_stage_4_briefing_newer_than_pdf(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    briefing = fig_dir / "briefing.md"
    briefing.write_text("# briefing", encoding="utf-8")
    build_dir = fig_dir / "build"
    build_dir.mkdir()
    pdf = build_dir / "myfig.pdf"
    pdf.write_bytes(b"%PDF")
    old_time = time.time() - 100
    os.utime(tex, (old_time, old_time))
    os.utime(pdf, (old_time + 10, old_time + 10))
    new_time = time.time() - 5
    os.utime(briefing, (new_time, new_time))
    result = infer_stage(fig_dir)
    assert result["stage"] == 4
    assert ("build_pdf", "stale") in result["checks"]


def test_stage_6_stale_export_when_source_newer(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    tex = fig_dir / "myfig.tex"
    tex.write_text("% tikz", encoding="utf-8")
    briefing = fig_dir / "briefing.md"
    briefing.write_text("# briefing", encoding="utf-8")
    exports_dir = fig_dir / "exports"
    exports_dir.mkdir()
    pdf = exports_dir / "myfig.pdf"
    svg = exports_dir / "myfig.svg"
    tif = exports_dir / "myfig.tif"
    png = exports_dir / "myfig.png"
    for path, content in (
        (pdf, b"%PDF"),
        (svg, b"<svg/>"),
        (tif, b"TIFF"),
        (png, b"\x89PNG"),
    ):
        path.write_bytes(content)
    old_time = time.time() - 100
    for path in (pdf, svg, tif, png, briefing):
        os.utime(path, (old_time, old_time))
    new_time = time.time() - 5
    os.utime(tex, (new_time, new_time))
    result = infer_stage(fig_dir)
    assert result["stage"] == 6
    assert "stale_export" in result["notes"]
    assert "partial_export" not in result["notes"]
    assert "/fig_compile" in result["next"]
    assert "done" not in result["next"]


def test_stage_3_selected_preview_missing_note(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview="ghost.png")
    previews = fig_dir / "previews"
    previews.mkdir()
    (previews / ".gitkeep").touch()
    result = infer_stage(fig_dir)
    assert result["stage"] == 3
    assert "selected_preview_missing" in result["notes"]


def test_stage_3_selected_preview_present_no_note(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir, selected_preview="real.png")
    previews = fig_dir / "previews"
    previews.mkdir()
    (previews / "real.png").write_bytes(b"\x89PNG")
    result = infer_stage(fig_dir)
    assert result["stage"] == 3
    assert "selected_preview_missing" not in result["notes"]


def test_previews_as_file_not_directory_does_not_crash(tmp_path: Path) -> None:
    fig_dir = tmp_path / "myfig"
    fig_dir.mkdir()
    _make_spec(fig_dir)
    (fig_dir / "previews").write_text("not a dir", encoding="utf-8")
    result = infer_stage(fig_dir)
    assert result["stage"] == 1
    assert "previews_not_directory" in result["notes"]


def test_smoke_fixture_smoke_trap_demo() -> None:
    fixture = REPO_ROOT / "examples" / "smoke_trap_demo"
    if not fixture.exists():
        return
    result = infer_stage(fixture)
    assert result["stage"] == 6
    assert "partial_export" not in result["notes"]


def test_no_arg_all_figures(tmp_path: Path, capsys, monkeypatch) -> None:
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()

    # Stage 1 figure
    fig1 = examples_dir / "alpha_fig"
    fig1.mkdir()
    _make_spec(fig1)
    (fig1 / "previews").mkdir()

    # Stage 6 figure
    fig2 = examples_dir / "zeta_fig"
    fig2.mkdir()
    _make_spec(fig2)
    exports = fig2 / "exports"
    exports.mkdir()
    (exports / "zeta_fig.pdf").write_bytes(b"%PDF")
    (exports / "zeta_fig.svg").write_bytes(b"<svg/>")
    (exports / "zeta_fig.tif").write_bytes(b"TIFF")
    (exports / "zeta_fig.png").write_bytes(b"\x89PNG")

    monkeypatch.chdir(tmp_path)

    import status as status_mod

    old_argv = sys.argv
    sys.argv = ["status.py"]
    try:
        status_mod.main()
    finally:
        sys.argv = old_argv

    captured = capsys.readouterr()
    assert "alpha_fig" in captured.out
    assert "stage 1" in captured.out
    assert "zeta_fig" in captured.out
    assert "stage 6" in captured.out
    lines = [ln for ln in captured.out.splitlines() if ln.strip()]
    names = [ln.split()[0] for ln in lines]
    assert names == sorted(names)
