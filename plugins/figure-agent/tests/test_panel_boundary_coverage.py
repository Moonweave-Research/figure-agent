from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "checks"))

import check_panel_boundary_coverage as pbc  # noqa: E402

CM = 72.0 / 2.54


def _word(text: str, xmin: float, ymin: float, xmax: float, ymax: float) -> dict[str, object]:
    return {"text": text, "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}


# One panel A, scope shift (0,0), frame rectangle (0,0)-(5,4) cm.
# Rendered with scale=CM/cm, tx=10, ty=200 (top origin) -> pdf frame:
#   x0 = 10, x1 = 5*CM+10, top = 200-4*CM, bottom = 200.
_SINGLE_PANEL_TEX = "\n".join(
    [
        r"\begin{tikzpicture}[panel frame/.style={draw=gray}]",
        r"% Panel A",
        r"\begin{scope}[shift={(0,0)}]",
        r"  \draw[panel frame] (0,0) rectangle (5,4);",
        r"  \node at (2.5,2) {inside};",
        r"\end{scope}",
        r"\end{tikzpicture}",
    ]
)


def _single_panel_pdf_frames() -> list[tuple[float, float, float, float]]:
    return [(10.0, 200.0 - 4.0 * CM, 5.0 * CM + 10.0, 200.0)]


def test_parse_extracts_ordered_panel_frames() -> None:
    frames = pbc.parse_panel_frames(_SINGLE_PANEL_TEX)
    assert [frame.panel_id for frame in frames] == ["A"]
    xmin, ymin, xmax, ymax = frames[0].source_bbox
    assert (round(xmin, 3), round(ymin, 3), round(xmax, 3), round(ymax, 3)) == (0.0, 0.0, 5.0, 4.0)


def test_text_node_protruding_past_own_frame_is_flagged() -> None:
    # A word straddling the panel-A left edge (pdf x=10): xmin=4 < 10 < xmax=16.
    words = [_word("sulfur", 4.0, 100.0, 16.0, 110.0)]
    report = pbc.evaluate_panel_boundary_coverage(
        _SINGLE_PANEL_TEX,
        _single_panel_pdf_frames(),
        words,
        (300.0, 300.0),
    )
    assert report["total"] == 1
    candidate = report["candidates"][0]
    assert candidate["text"] == "sulfur"
    assert candidate["panel"] == "A"
    assert candidate["boundary_role"] == "panel_A_frame_left"
    assert report["coverage"] == {"A": "covered"}
    assert report["zero_coverage_panels"] == []


def test_declared_intentional_overflow_suppresses_the_flag() -> None:
    words = [_word("sulfur", 4.0, 100.0, 16.0, 110.0)]
    report = pbc.evaluate_panel_boundary_coverage(
        _SINGLE_PANEL_TEX,
        _single_panel_pdf_frames(),
        words,
        (300.0, 300.0),
        intentional_overflow=[{"panel": "A", "text": "sulfur"}],
    )
    assert report["total"] == 0
    assert report["candidates"] == []
    # Coverage stays reported; the panel is still checked, the overflow is declared-intentional.
    assert report["coverage"] == {"A": "covered"}
    assert report["intentional_overflow_suppressed"] == 1


def test_text_node_fully_inside_frame_is_clean() -> None:
    words = [_word("inside", 40.0, 100.0, 60.0, 110.0)]
    report = pbc.evaluate_panel_boundary_coverage(
        _SINGLE_PANEL_TEX,
        _single_panel_pdf_frames(),
        words,
        (300.0, 300.0),
    )
    assert report["total"] == 0
    assert report["coverage"] == {"A": "covered"}


def test_intentional_overflow_is_panel_scoped() -> None:
    # Allowlisting panel B's "sulfur" must NOT suppress panel A's overflow.
    words = [_word("sulfur", 4.0, 100.0, 16.0, 110.0)]
    report = pbc.evaluate_panel_boundary_coverage(
        _SINGLE_PANEL_TEX,
        _single_panel_pdf_frames(),
        words,
        (300.0, 300.0),
        intentional_overflow=[{"panel": "B", "text": "sulfur"}],
    )
    assert report["total"] == 1


def test_duplicate_panel_markers_fail_closed() -> None:
    tex = "\n".join(
        [
            r"\begin{tikzpicture}",
            r"% Panel A",
            r"\draw[panel frame] (0,0) rectangle (5,4);",
            r"% Panel A",
            r"\draw[panel frame] (6,0) rectangle (11,4);",
            r"\end{tikzpicture}",
        ]
    )
    with pytest.raises(pbc.PanelBoundaryError):
        pbc.parse_panel_frames(tex)


def test_missing_panel_markers_fail_closed() -> None:
    tex = r"\begin{tikzpicture}\draw (0,0) rectangle (5,4);\end{tikzpicture}"
    with pytest.raises(pbc.PanelBoundaryError):
        pbc.parse_panel_frames(tex)


def test_multiple_panel_frames_in_one_block_fail_closed() -> None:
    tex = "\n".join(
        [
            r"\begin{tikzpicture}",
            r"% Panel A",
            r"\draw[panel frame] (0,0) rectangle (5,4);",
            r"\draw[panel frame] (6,0) rectangle (11,4);",
            r"\end{tikzpicture}",
        ]
    )
    with pytest.raises(pbc.PanelBoundaryError):
        pbc.parse_panel_frames(tex)


def test_frameless_panel_reports_zero_coverage_loudly() -> None:
    tex = "\n".join(
        [
            r"\begin{tikzpicture}[panel frame/.style={draw=gray}]",
            r"% Panel A",
            r"\begin{scope}[shift={(0,0)}]",
            r"  \draw[panel frame] (0,0) rectangle (5,4);",
            r"\end{scope}",
            r"% Panel B",
            r"\begin{scope}[shift={(6,0)}]",
            r"  \node at (2,2) {hero, no frame};",
            r"\end{scope}",
            r"\end{tikzpicture}",
        ]
    )
    words = [_word("inside", 40.0, 100.0, 60.0, 110.0)]
    report = pbc.evaluate_panel_boundary_coverage(
        tex,
        _single_panel_pdf_frames(),
        words,
        (300.0, 300.0),
    )
    assert report["coverage"] == {"A": "covered", "B": "zero_coverage"}
    assert report["zero_coverage_panels"] == ["B"]
    assert report["zero_coverage"] is True


def test_all_frameless_reports_total_zero_coverage() -> None:
    tex = "\n".join(
        [
            r"\begin{tikzpicture}",
            r"% Panel A",
            r"\node at (2,2) {no frame here};",
            r"\end{tikzpicture}",
        ]
    )
    report = pbc.evaluate_panel_boundary_coverage(tex, [], [], (300.0, 300.0))
    assert report["coverage"] == {"A": "zero_coverage"}
    assert report["zero_coverage"] is True
    assert report["covered_panels"] == []
    assert report["total"] == 0


def test_frame_count_mismatch_with_pdf_fails_closed() -> None:
    # Source declares one frame; the rendered PDF exposes none that match.
    with pytest.raises(pbc.PanelBoundaryError):
        pbc.evaluate_panel_boundary_coverage(
            _SINGLE_PANEL_TEX,
            [],  # no pdf frame bboxes for a source that has a frame
            [],
            (300.0, 300.0),
        )
