"""API contract tests for the \\BellCurve macro after style/shape decoupling.

Validates the four supported call patterns (default, local-override,
scope-override) and that the legacy 6-positional signature is rejected.
Tests assert compile-success/failure only; byte-identical content-stream
verification is a separate manual step using `scripts/diff_pdf_content.py`.
"""

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
def test_default_style_compiles(tmp_path: Path) -> None:
    """\\BellCurve{...,side} with no optional style compiles using the
    palette-neutral cGray outline default declared in `bell curve/.style`."""
    result = _compile(tmp_path, r"\BellCurve{0,0,1,1,side}")
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_local_style_override_compiles(tmp_path: Path) -> None:
    """Caller may pass any TikZ \\path keys via the optional [#1] argument;
    this exercises the canonical translation pattern used by migrated callsites."""
    result = _compile(
        tmp_path,
        r"\BellCurve[draw=cAmber!80!black, fill=cAmber!18, line width=0.8pt]"
        r"{0,0,1,1,side}",
    )
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_scope_style_override_compiles(tmp_path: Path) -> None:
    """`\\tikzset{bell curve/.append style={...}}` lets a figure declare a
    figure-wide style once; subsequent \\BellCurve calls inherit it."""
    result = _compile(
        tmp_path,
        r"\tikzset{bell curve/.append style={fill=cAmber!18}}"
        "\n"
        r"\BellCurve{0,0,1,1,side}",
    )
    assert result.returncode == 0, result.stderr + result.stdout


@pytest.mark.skipif(
    shutil.which("lualatex") is None or shutil.which("pdftocairo") is None,
    reason="requires lualatex and pdftocairo",
)
def test_legacy_six_positional_signature_rejected(tmp_path: Path) -> None:
    """Old \\BellCurve{x1,y1,x2,y2,color,orientation} (6 positional, color
    embedded) MUST fail compile. With the new 5-positional parser the 6th
    field collapses into the orientation match-string (`cAmber, side`),
    matching neither `up` nor `side`, triggering \\PackageError."""
    result = _compile(tmp_path, r"\BellCurve{0,0,1,1,cAmber,side}")
    assert result.returncode != 0, (
        "Expected compile failure for legacy 6-positional call; "
        "the new macro must reject the ambiguous old signature."
    )
    combined = result.stdout + result.stderr
    assert "Invalid BellCurve orientation" in combined, combined
