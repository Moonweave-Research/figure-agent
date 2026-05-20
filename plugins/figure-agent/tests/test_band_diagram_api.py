"""API contract tests for the \\BandDiagram macro after caller-pgfkeys decoupling.

Validates the three supported call patterns (default, per-call override via [#1],
figure-wide tikzset). Tests assert compile-success only; structural-diff
verification is in tests/test_band_diagram_byte_classifier.py.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.render


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
def test_per_call_override_compiles(tmp_path: Path) -> None:
    """Caller may pass TikZ \\path keys via the optional [#1] argument.
    The .append style form patches the figure-wide bandFrame default for
    this single call only."""
    result = _compile(
        tmp_path,
        r"\BandDiagram[bandFrame/.append style={draw=cAmber, line width=0.8pt}]"
        r"{0,0,4,3, 2.5, 0.5, 1.5, {}, {}}",
    )
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_default_invocation_compiles(tmp_path: Path) -> None:
    """Backwards-compatibility: \\BandDiagram with no optional [#1] arg
    must still compile. The new [2][] signature treats the missing optional
    as empty, so \\BD@opts is the empty token list — \\begin{scope}[band
    diagram, ] is a no-op style application."""
    result = _compile(
        tmp_path,
        r"\BandDiagram{0,0,4,3, 2.5, 0.5, 1.5, {3.5,3.2,2.9}, {1.8,1.5}}",
    )
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_figure_wide_tikzset_path_still_works(tmp_path: Path) -> None:
    """Pre-pilot caller pattern: figure-wide \\tikzset patches a sub-style
    once, all subsequent \\BandDiagram calls inherit it. The new [#1] slot
    is additive — it does not break this path."""
    result = _compile(
        tmp_path,
        r"\tikzset{bandFrame/.append style={draw=cAmber}}"
        "\n"
        r"\BandDiagram{0,0,4,3, 2.5, 0.5, 1.5, {}, {}}",
    )
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_no_et_option_compiles(tmp_path: Path) -> None:
    """Gap 3: callers can suppress the Et dashed line and auto label."""
    result = _compile(
        tmp_path,
        r"\BandDiagram[no_et]{0,0,4,3, 2.5, 0.5, 1.5, {2.2}, {1.2}}",
    )
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_traps_none_option_compiles(tmp_path: Path) -> None:
    """Gap 5: callers can suppress all trap-level dash glyphs."""
    result = _compile(
        tmp_path,
        r"\BandDiagram[traps=none]{0,0,4,3, 2.5, 0.5, 1.5, {2.2,2.0}, {1.2}}",
    )
    assert result.returncode == 0, result.stderr + result.stdout
