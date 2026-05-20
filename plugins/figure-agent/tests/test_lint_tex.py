"""Tests for scripts/lint_tex.py — Style Lock BLOCKER- and WARN-tier lint contract."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lint_tex import lint, main, parse_palette  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write(tmp_path: Path, content: str) -> Path:
    tex = tmp_path / "fixture.tex"
    tex.write_text(content, encoding="utf-8")
    return tex


def _blockers(tex_path: Path) -> list:
    return [v for v in lint(tex_path) if v.severity == "blocker"]


_DOC_HEADER_WITH_PREAMBLE = (
    r"\documentclass[border=4pt]{standalone}"
    "\n"
    r"\usepackage{polymer-paper-preamble}"
    "\n"
    r"\begin{document}"
    "\n"
)
_DOC_FOOTER = "\n" + r"\end{document}" + "\n"


def test_missing_preamble_blocker_when_document_boundary_present(tmp_path: Path) -> None:
    """A real \\documentclass-bearing file without the preamble import must
    fail Style Lock; otherwise the palette and flagship macros it claims to
    enforce are not actually available at compile time."""
    tex = _write(
        tmp_path,
        r"\documentclass[border=4pt]{standalone}"
        "\n"
        r"\begin{document}"
        "\n"
        r"\node {x};"
        "\n"
        r"\end{document}"
        "\n",
    )
    blockers = _blockers(tex)
    categories = [v.category for v in blockers]
    assert "missing_preamble" in categories


def test_preamble_import_via_usepackage_passes(tmp_path: Path) -> None:
    tex = _write(tmp_path, _DOC_HEADER_WITH_PREAMBLE + r"\node {x};" + _DOC_FOOTER)
    categories = [v.category for v in _blockers(tex)]
    assert "missing_preamble" not in categories


def test_preamble_import_via_requirepackage_passes(tmp_path: Path) -> None:
    tex = _write(
        tmp_path,
        r"\documentclass[border=4pt]{standalone}"
        "\n"
        r"\RequirePackage{polymer-paper-preamble}"
        "\n"
        r"\begin{document}"
        "\n"
        r"\node {x};"
        "\n"
        r"\end{document}"
        "\n",
    )
    categories = [v.category for v in _blockers(tex)]
    assert "missing_preamble" not in categories


def test_commented_preamble_import_does_not_satisfy(tmp_path: Path) -> None:
    """A commented-out preamble import must not silently pass the gate."""
    tex = _write(
        tmp_path,
        r"\documentclass[border=4pt]{standalone}"
        "\n"
        r"% \usepackage{polymer-paper-preamble}"
        "\n"
        r"\begin{document}"
        "\n"
        r"\end{document}"
        "\n",
    )
    categories = [v.category for v in _blockers(tex)]
    assert "missing_preamble" in categories


def test_snippet_without_document_boundary_skips_preamble_check(tmp_path: Path) -> None:
    """Test snippets without \\documentclass or \\begin{document} are exempt
    from the preamble check so legacy unit-test snippets do not break."""
    tex = _write(tmp_path, r"\node[fill=cAmber] {};" + "\n")
    categories = [v.category for v in _blockers(tex)]
    assert "missing_preamble" not in categories


def test_clean_palette_only_no_violations(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\node[fill=cAmber] {};" + "\n")
    assert _blockers(tex) == []


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
    assert _blockers(tex) == []


def test_commented_definecolor_no_violation(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"% \definecolor{x}{HTML}{000000}" + "\n")
    assert _blockers(tex) == []


def test_live_definecolor_with_comment_definecolor_one_violation(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\definecolor{x}{HTML}{ABCDEF} % comment with \definecolor" + "\n")
    violations = lint(tex)
    dc_violations = [v for v in violations if v.category == "definecolor"]
    assert len(dc_violations) == 1


def test_regression_fig3_trapping_concept_no_blockers_flags_warn() -> None:
    fixture = REPO_ROOT / "examples" / "fig3_trapping_concept" / "fig3_trapping_concept.tex"
    if not fixture.exists():
        return
    blockers = [v for v in lint(fixture) if v.severity == "blocker"]
    assert blockers == []
    assert any(v.category == "flagship_macros_unused" for v in lint(fixture))


def test_regression_smoke_trap_demo_no_blockers_flags_warn() -> None:
    fixture = REPO_ROOT / "examples" / "smoke_trap_demo" / "smoke_trap_demo.tex"
    if not fixture.exists():
        return
    blockers = [v for v in lint(fixture) if v.severity == "blocker"]
    assert blockers == []
    assert any(v.category == "flagship_macros_unused" for v in lint(fixture))


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


def test_implicit_color_in_option_block(tmp_path: Path) -> None:
    """Bypass attempt: positional color arg without fill=/draw= prefix."""
    tex = _write(tmp_path, r"\node[red] {};" + "\n")
    violations = lint(tex)
    np_violations = [v for v in violations if v.category == "non_palette_color"]
    assert len(np_violations) == 1
    assert "red" in np_violations[0].message


def test_implicit_color_among_other_tikz_options(tmp_path: Path) -> None:
    """Bypass attempt: color mixed with non-color positional options."""
    tex = _write(tmp_path, r"\draw[thick, blue] (0,0) -- (1,1);" + "\n")
    violations = lint(tex)
    np_violations = [v for v in violations if v.category == "non_palette_color"]
    assert len(np_violations) == 1
    assert "blue" in np_violations[0].message


def test_palette_token_as_positional_in_option_block_no_violation(tmp_path: Path) -> None:
    """Palette names used positionally must pass."""
    tex = _write(tmp_path, r"\draw[thick, cBlue] (0,0) -- (1,1);" + "\n")
    assert _blockers(tex) == []


def test_brace_enclosed_color_value(tmp_path: Path) -> None:
    """Bypass attempt: fill={red} with TikZ brace-enclosed value."""
    tex = _write(tmp_path, r"\node[fill={red}] {};" + "\n")
    violations = lint(tex)
    np_violations = [v for v in violations if v.category == "non_palette_color"]
    assert len(np_violations) == 1
    assert "red" in np_violations[0].message


def test_double_backslash_then_comment_strips_correctly(tmp_path: Path) -> None:
    r"""LaTeX \\ is newline; the following % opens a real comment.

    Authors must be free to write `\\% \node[fill=red]` as a commented-out
    diagnostic without lint flagging the dead code.
    """
    tex = _write(tmp_path, r"\\% \node[fill=red] {};" + "\n")
    assert _blockers(tex) == []


def test_escaped_percent_preserves_literal(tmp_path: Path) -> None:
    r"""\% is a literal percent character; lint must NOT truncate the line."""
    tex = _write(tmp_path, r"\node {50\% efficiency, fill=red comment} \draw[red];" + "\n")
    violations = lint(tex)
    np_violations = [v for v in violations if v.category == "non_palette_color"]
    assert len(np_violations) >= 1


def test_parse_palette_missing_sty_returns_empty_set(tmp_path: Path) -> None:
    missing = tmp_path / "no_such_preamble.sty"
    assert parse_palette(missing) == set()


def test_parse_palette_explicit_path_works(tmp_path: Path) -> None:
    sty = tmp_path / "fake.sty"
    sty.write_text(
        r"\definecolor{cTest}{HTML}{ABCDEF}" + "\n" + r"\definecolor{cOther}{RGB}{1,2,3}" + "\n",
        encoding="utf-8",
    )
    assert parse_palette(sty) == {"cTest", "cOther"}


# WARN tier unit tests


def test_flagship_macro_used_no_flagship_warn(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\IsoBlock{1}{1}{1}{cAmber}{}" + "\n")
    violations = lint(tex)
    assert not any(v.category == "flagship_macros_unused" for v in violations)


def test_polymer_chain_counts_as_flagship_macro(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\PolymerChain{0}{0}{11}{3,7,8,9}" + "\n")
    violations = lint(tex)
    assert not any(v.category == "flagship_macros_unused" for v in violations)


def test_paper_loglog_style_counts_as_flagship_usage(tmp_path: Path) -> None:
    tex = _write(
        tmp_path,
        r"\begin{loglogaxis}[paper loglog={3.6cm}{2.6cm}]\end{loglogaxis}" + "\n",
    )
    violations = lint(tex)
    assert not any(v.category == "flagship_macros_unused" for v in violations)


def test_plot_callout_counts_as_flagship_macro(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\PlotCallout{(0,0)}{(1,1)}{label}" + "\n")
    violations = lint(tex)
    assert not any(v.category == "flagship_macros_unused" for v in violations)


def test_no_flagship_macro_emits_warn(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\node[fill=cAmber] {};" + "\n")
    violations = lint(tex)
    flagship_warns = [v for v in violations if v.category == "flagship_macros_unused"]
    assert len(flagship_warns) == 1
    assert flagship_warns[0].severity == "warn"


def test_thin_stroke_below_threshold_emits_warn(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\draw[line width=0.20pt] (0,0) -- (1,1);" + "\n")
    violations = lint(tex)
    ts_violations = [v for v in violations if v.category == "thin_stroke"]
    assert len(ts_violations) == 1
    assert ts_violations[0].severity == "warn"


def test_thick_stroke_at_threshold_no_warn(tmp_path: Path) -> None:
    # 0.25pt is exactly at boundary; exclusive rule means no warn
    tex = _write(tmp_path, r"\draw[line width=0.25pt] (0,0) -- (1,1);" + "\n")
    violations = lint(tex)
    ts_violations = [v for v in violations if v.category == "thin_stroke"]
    assert len(ts_violations) == 0


def test_thin_stroke_dot_decimal_form(tmp_path: Path) -> None:
    # .10pt (no leading zero) must be caught
    tex = _write(tmp_path, r"\draw[line width=.10pt] (0,0) -- (1,1);" + "\n")
    violations = lint(tex)
    ts_violations = [v for v in violations if v.category == "thin_stroke"]
    assert len(ts_violations) == 1


def test_filled_label_before_later_draw_emits_source_order_warn(tmp_path: Path) -> None:
    tex = _write(
        tmp_path,
        "\n".join(
            [
                r"\node[fill=white, inner sep=1pt] at (0,0) {d};",
                r"\draw[cBlue] (-0.4,0) -- (0.4,0);",
            ]
        )
        + "\n",
    )

    violations = lint(tex)
    source_order = [v for v in violations if v.category == "label_fill_source_order"]

    assert len(source_order) == 1
    assert source_order[0].line == 1
    assert source_order[0].severity == "warn"
    assert "move protected label after later draw commands" in source_order[0].message


def test_filled_shape_without_text_avoids_source_order_warn(tmp_path: Path) -> None:
    tex = _write(
        tmp_path,
        "\n".join(
            [
                r"\node[fill=white] at (0,0) {};",
                r"\draw[cBlue] (-0.4,0) -- (0.4,0);",
            ]
        )
        + "\n",
    )

    assert not any(v.category == "label_fill_source_order" for v in lint(tex))


def test_filled_label_after_draw_avoids_source_order_warn(tmp_path: Path) -> None:
    tex = _write(
        tmp_path,
        "\n".join(
            [
                r"\draw[cBlue] (-0.4,0) -- (0.4,0);",
                r"\node[fill=white, inner sep=1pt] at (0,0) {d};",
            ]
        )
        + "\n",
    )

    assert not any(v.category == "label_fill_source_order" for v in lint(tex))


def test_non_painting_path_node_after_filled_label_avoids_source_order_warn(
    tmp_path: Path,
) -> None:
    tex = _write(
        tmp_path,
        "\n".join(
            [
                r"\node[fill=white, inner sep=1pt] at (0,0) {d};",
                r"\path (0,0) node[above] {annotation};",
            ]
        )
        + "\n",
    )

    assert not any(v.category == "label_fill_source_order" for v in lint(tex))


def test_filldraw_after_filled_label_emits_source_order_warn(tmp_path: Path) -> None:
    tex = _write(
        tmp_path,
        "\n".join(
            [
                r"\node[fill=white, inner sep=1pt] at (0,0) {d};",
                r"\filldraw[cBlue] (-0.4,0) rectangle (0.4,0.2);",
            ]
        )
        + "\n",
    )

    assert any(v.category == "label_fill_source_order" for v in lint(tex))


def test_short_double_arrow_emits_warn(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\draw[<->, >=Stealth] (0,0) -- (0.18,0);" + "\n")

    violations = lint(tex)
    arrow_warns = [v for v in violations if v.category == "short_double_arrow"]

    assert len(arrow_warns) == 1
    assert arrow_warns[0].severity == "warn"
    assert "short double-headed arrow" in arrow_warns[0].message


def test_long_double_arrow_avoids_warn(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\draw[<->, >=Stealth] (0,0) -- (1.2,0);" + "\n")

    assert not any(v.category == "short_double_arrow" for v in lint(tex))


def test_double_arrow_at_threshold_avoids_warn(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\draw[<->, >=Stealth] (0,0) -- (0.35,0);" + "\n")

    assert not any(v.category == "short_double_arrow" for v in lint(tex))


def test_stealth_stealth_short_arrow_emits_warn(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\draw[Stealth-Stealth] (0,0) -- (0.18,0);" + "\n")

    assert any(v.category == "short_double_arrow" for v in lint(tex))


def test_latex_latex_short_arrow_emits_warn(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\draw[Latex-Latex] (0,0) -- (0.18,0);" + "\n")

    assert any(v.category == "short_double_arrow" for v in lint(tex))


def test_single_arrow_avoids_short_double_arrow_warn(tmp_path: Path) -> None:
    tex = _write(tmp_path, r"\draw[->, >=Stealth] (0,0) -- (0.18,0);" + "\n")

    assert not any(v.category == "short_double_arrow" for v in lint(tex))


def test_warn_lint_cli_outputs_path_line_code_and_remediation(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    tex = _write(tmp_path, r"\draw[<->, >=Stealth] (0,0) -- (0.18,0);" + "\n")
    monkeypatch.setattr(sys, "argv", ["lint_tex.py", str(tex)])

    assert main() == 0
    captured = capsys.readouterr()
    assert f"{tex}:1: WARN: short_double_arrow:" in captured.out
    assert "lengthen it or use a single semantic cue" in captured.out
