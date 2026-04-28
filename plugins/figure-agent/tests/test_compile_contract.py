"""Compile contract smoke test for canonical build/ artifacts."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
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
    assert not (tmp_path / "smoke.pdf").exists()
    assert not (tmp_path / "smoke.png").exists()


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
