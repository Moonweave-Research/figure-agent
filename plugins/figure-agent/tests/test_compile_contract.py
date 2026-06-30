"""Compile contract smoke test for canonical build/ artifacts."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.render


def test_compile_script_pins_uv_project_after_changing_to_workspace_fixture() -> None:
    script = (REPO_ROOT / "scripts" / "compile.sh").read_text(encoding="utf-8")

    assert 'UV_RUN=(uv run --project "$WORKFLOW_DIR")' in script
    assert 'uv run python3 "$WORKFLOW_DIR/scripts/perception_pack.py"' not in script
    assert '"${UV_RUN[@]}" python3 "$WORKFLOW_DIR/scripts/perception_pack.py" "$BASE"' in script


@pytest.mark.skipif(
    shutil.which("lualatex") is None
    or shutil.which("pdftocairo") is None
    or shutil.which("pdftotext") is None
    or shutil.which("pdftoppm") is None,
    reason="requires lualatex, pdftocairo, pdftotext, and pdftoppm",
)
def test_compile_writes_pdf_and_png_to_build_dir(tmp_path: Path) -> None:
    tex_path = tmp_path / "smoke.tex"
    tex_path.write_text(
        r"""\documentclass[border=2pt]{standalone}
\usepackage{polymer-paper-preamble}
\begin{document}
compile smoke
\end{document}
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["bash", "scripts/compile.sh", str(tex_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (tmp_path / "build" / "smoke.pdf").exists()
    assert (tmp_path / "build" / "smoke.png").exists()
    assert (tmp_path / "build" / "label_path_proximity.json").exists()
    assert not (tmp_path / "smoke.pdf").exists()
    assert not (tmp_path / "smoke.png").exists()
    combined = result.stdout + result.stderr
    assert "OK: no collisions found" in combined
    assert "visual clash" in combined
    assert "label-path proximity" in combined


@pytest.mark.skipif(
    shutil.which("lualatex") is None
    or shutil.which("pdftocairo") is None
    or shutil.which("pdftotext") is None
    or shutil.which("pdftoppm") is None,
    reason="requires lualatex, pdftocairo, pdftotext, and pdftoppm",
)
def test_compile_wraps_bare_tikz_snippet(tmp_path: Path) -> None:
    tex_path = tmp_path / "bare_snippet.tex"
    tex_path.write_text(r"\node (label-a) at (0,0) {Bare Label};
", encoding="utf-8")

    result = subprocess.run(
        ["bash", "scripts/compile.sh", str(tex_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (tmp_path / "build" / "bare_snippet.pdf").exists()
    assert (tmp_path / "build" / "bare_snippet.png").exists()
    assert not (tmp_path / "bare_snippet.pdf").exists()
    assert not (tmp_path / "bare_snippet.png").exists()


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_failed_latex_compile_removes_stale_pdf_and_png(tmp_path: Path) -> None:
    tex_path = tmp_path / "stale_guard.tex"
    tex_path.write_text(
        r"""\documentclass[border=2pt]{standalone}
\usepackage{polymer-paper-preamble}
\begin{document}
valid
\end{document}
""",
        encoding="utf-8",
    )
    first = subprocess.run(
        ["bash", "scripts/compile.sh", str(tex_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert first.returncode == 0, first.stderr + first.stdout
    assert (tmp_path / "build" / "stale_guard.pdf").exists()
    assert (tmp_path / "build" / "stale_guard.png").exists()

    tex_path.write_text(
        r"""\documentclass[border=2pt]{standalone}
\usepackage{polymer-paper-preamble}
\begin{document}
\undefinedcommand
\end{document}
""",
        encoding="utf-8",
    )
    failed = subprocess.run(
        ["bash", "scripts/compile.sh", str(tex_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert failed.returncode != 0
    assert not (tmp_path / "build" / "stale_guard.pdf").exists()
    assert not (tmp_path / "build" / "stale_guard.png").exists()


@pytest.mark.skipif(
    shutil.which("lualatex") is None
    or shutil.which("pdftocairo") is None
    or shutil.which("pdftotext") is None
    or shutil.which("pdftoppm") is None,
    reason="requires lualatex, pdftocairo, pdftotext, and pdftoppm",
)
def test_golden_trap_depth_picture_compiles_with_shared_preamble() -> None:
    tex_path = (
        REPO_ROOT
        / "examples"
        / "golden_trap_depth_picture"
        / "golden_trap_depth_picture.tex"
    )
    if not tex_path.is_file():
        pytest.skip(
            "optional golden_trap_depth_picture real fixture is not present in this plugin tree"
        )

    result = subprocess.run(
        ["bash", "scripts/compile.sh", str(tex_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (
        REPO_ROOT
        / "examples"
        / "golden_trap_depth_picture"
        / "build"
        / "golden_trap_depth_picture.pdf"
    ).exists()


@pytest.mark.skipif(
    shutil.which("lualatex") is None
    or shutil.which("pdftocairo") is None
    or shutil.which("pdftotext") is None
    or shutil.which("pdftoppm") is None,
    reason="requires lualatex, pdftocairo, pdftotext, and pdftoppm",
)
@pytest.mark.parametrize(
    ("fixture_dir", "tex_name"),
    [
        ("polymer_chain", "polymer_chain_smoke"),
        ("log_plot", "log_plot_smoke"),
    ],
)
def test_l3_snippet_smoke_fixtures_compile(fixture_dir: str, tex_name: str) -> None:
    tex_path = (
        REPO_ROOT
        / "examples"
        / "_snippet_smoke"
        / fixture_dir
        / f"{tex_name}.tex"
    )

    result = subprocess.run(
        ["bash", "scripts/compile.sh", str(tex_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert (
        REPO_ROOT
        / "examples"
        / "_snippet_smoke"
        / fixture_dir
        / "build"
        / f"{tex_name}.pdf"
    ).exists()


@pytest.mark.skipif(
    shutil.which("lualatex") is None
    or shutil.which("pdftocairo") is None
    or shutil.which("rsvg-convert") is None,
    reason="requires lualatex, pdftocairo, and rsvg-convert",
)
def test_export_flow_writes_pdf_svg_tiff_png(tmp_path: Path) -> None:
    tex_path = tmp_path / "export_smoke.tex"
    tex_path.write_text(
        r"""\documentclass[border=2pt]{standalone}
\usepackage{polymer-paper-preamble}
\begin{document}
export smoke
\end{document}
""",
        encoding="utf-8",
    )

    subprocess.run(
        ["bash", "scripts/compile.sh", str(tex_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    build_pdf = tmp_path / "build" / "export_smoke.pdf"
    exports = tmp_path / "exports"
    exports.mkdir()
    export_pdf = exports / "export_smoke.pdf"
    export_svg = exports / "export_smoke.svg"
    export_tiff = exports / "export_smoke.tif"
    export_png = exports / "export_smoke.png"

    shutil.copyfile(build_pdf, export_pdf)
    subprocess.run(
        ["bash", "scripts/export_svg.sh", str(build_pdf), str(export_svg)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        [
            "pdftocairo",
            "-tiff",
            "-r",
            "600",
            "-singlefile",
            str(build_pdf),
            str(exports / "export_smoke"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    subprocess.run(
        ["bash", "scripts/svg_to_png.sh", str(export_svg), str(export_png)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    for path in (export_pdf, export_svg, export_tiff, export_png):
        assert path.exists()
        assert path.stat().st_size > 0
