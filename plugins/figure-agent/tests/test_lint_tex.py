"""Tests for scripts/lint_tex.py — Style Lock BLOCKER-tier lint contract."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lint_tex import lint, parse_palette  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write(tmp_path: Path, content: str) -> Path:
    tex = tmp_path / "fixture.tex"
    tex.write_text(content, encoding="utf-8")
    return tex


def test_clean_palette_only_no_violations(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\node[fill=cAmber] {};" + "\n")
    assert lint(tex) == []


def test_definecolor_line5(tmp_path: Path) -> None:
    lines = [
        "line1\n",
        "line2\n",
        "line3\n",
        "line4\n",
        r"\definecolor{myRed}{HTML}{FF0000}" + "\n",
    ]
    tex = tmp_path / "fixture.tex"
    tex.write_text("".join(lines), encoding="utf-8")
    violations = lint(tex)
    dc_violations = [v for v in violations if v.category == "definecolor"]
    assert len(dc_violations) == 1
    assert dc_violations[0].line == 5


def test_setmainfont_font_override(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\setmainfont{Arial}" + "\n")
    violations = lint(tex)
    fo_violations = [v for v in violations if v.category == "font_override"]
    assert len(fo_violations) == 1


def test_raw_hex_node_fill(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\node[fill=#FF0000] {};" + "\n")
    violations = lint(tex)
    hex_violations = [v for v in violations if v.category == "raw_hex"]
    assert len(hex_violations) >= 1


def test_fill_red_non_palette_color(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\node[fill=red] {};" + "\n")
    violations = lint(tex)
    np_violations = [v for v in violations if v.category == "non_palette_color"]
    assert len(np_violations) == 1
    assert "red" in np_violations[0].message


def test_fill_camber_modifier_no_violation(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\node[fill=cAmber!50!white] {};" + "\n")
    assert lint(tex) == []


def test_commented_definecolor_no_violation(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"% \definecolor{x}{HTML}{000000}" + "\n")
    assert lint(tex) == []


def test_live_definecolor_with_comment_definecolor_one_violation(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\definecolor{x}{HTML}{ABCDEF} % comment with \definecolor" + "\n")
    violations = lint(tex)
    dc_violations = [v for v in violations if v.category == "definecolor"]
    assert len(dc_violations) == 1


def test_regression_fig3_trapping_concept_zero_violations() -> None:
    fixture = REPO_ROOT / "examples" / "fig3_trapping_concept" / "fig3_trapping_concept.tex"
    if not fixture.exists():
        return
    assert lint(fixture) == []


def test_regression_smoke_trap_demo_zero_violations() -> None:
    fixture = REPO_ROOT / "examples" / "smoke_trap_demo" / "smoke_trap_demo.tex"
    if not fixture.exists():
        return
    assert lint(fixture) == []


def test_parse_palette_superset_of_expected() -> None:
    palette = parse_palette()
    required = {
        "cAmber",
        "cBlue",
        "cRed",
        "cTeal",
        "cGray",
        "cLGray",
        "cBrown",
        "cArmAmber",
        "cAmberSphere",
    }
    assert required <= palette
