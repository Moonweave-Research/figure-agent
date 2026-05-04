"""API contract tests for the \\PlotCallout annotation macro."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

_HEADER = (
    r"\documentclass[border=2pt]{standalone}"
    "\n"
    r"\usepackage{polymer-paper-preamble}"
    "\n"
    r"\begin{document}"
    "\n"
    r"\begin{tikzpicture}[x=1cm, y=1cm]"
    "\n"
)
_FOOTER = (
    "\n"
    r"\end{tikzpicture}"
    "\n"
    r"\end{document}"
    "\n"
)


def _compile(tmp_path: Path, body: str) -> subprocess.CompletedProcess:
    tex = tmp_path / "fixture.tex"
    tex.write_text(_HEADER + body + _FOOTER, encoding="utf-8")
    return subprocess.run(
        ["bash", "scripts/compile.sh", str(tex)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_plot_callout_compiles_with_node_options(tmp_path: Path) -> None:
    result = _compile(
        tmp_path,
        r"\draw[cBlue, line width=0.8pt] (0,0) -- (2,1);"
        "\n"
        r"\PlotCallout[text=cBlue, anchor=west]{(1.0,0.5)}{(2.4,1.3)}{slope = $-n$}",
    )

    assert result.returncode == 0, result.stderr + result.stdout
