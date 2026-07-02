from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import label_refit_derive as lrd  # noqa: E402

NODE = (
    "\\node[labelMute, anchor=north, text width=2.6cm, align=center] at (7.60,4.12)"
    " {PI, PDMS, PET (shallow, leaky)};"
)
AXIS = "\\draw[axisArr] (6.10,3.90) -- (17.25,3.90);"


def test_parse_node_reads_coord_and_text_width():
    assert lrd.parse_node(NODE) == (7.60, 4.12, 2.6)


def test_parse_node_returns_none_without_text_width():
    assert lrd.parse_node("\\node[anchor=north] at (7.60,4.12) {x};") is None


def test_parse_node_returns_none_without_coordinate():
    assert lrd.parse_node("\\node[text width=2.6cm] {x};") is None


def test_nearest_crossed_hline_finds_the_axis_below_the_node():
    assert lrd.nearest_crossed_hline(7.60, 4.12, ["% pre", AXIS, "% post"]) == 3.90


def test_nearest_crossed_hline_ignores_vertical_draw():
    vaxis = "\\draw[axisArr] (6.10,3.90) -- (6.10,9.15);"
    assert lrd.nearest_crossed_hline(7.60, 4.12, [vaxis]) is None


def test_nearest_crossed_hline_ignores_hline_not_under_the_node_x():
    far = "\\draw (20.0,3.90) -- (30.0,3.90);"
    assert lrd.nearest_crossed_hline(7.60, 4.12, [far]) is None


def test_nearest_crossed_hline_ignores_hline_above_the_node():
    above = "\\draw (6.10,4.50) -- (17.25,4.50);"
    assert lrd.nearest_crossed_hline(7.60, 4.12, [above]) is None


def test_nearest_crossed_hline_picks_the_closest_below_when_multiple():
    near = "\\draw (6.10,3.90) -- (17.25,3.90);"
    farther = "\\draw (6.10,3.50) -- (17.25,3.50);"
    assert lrd.nearest_crossed_hline(7.60, 4.12, [farther, near]) == 3.90


def test_nearest_crossed_hline_ignores_lines_beyond_search_distance():
    # A horizontal line far below the node is not the one it crosses.
    deep = "\\draw (6.10,1.00) -- (17.25,1.00);"
    assert lrd.nearest_crossed_hline(7.60, 4.12, [deep]) is None


def test_count_lines_single_row():
    boxes = [(0, 0, 30, 18), (35, 0, 60, 18), (65, 0, 90, 18)]
    assert lrd.count_lines(boxes) == 1


def test_count_lines_two_rows():
    boxes = [(0, 0, 30, 18), (35, 0, 60, 18), (0, 24, 30, 42)]
    assert lrd.count_lines(boxes) == 2


def test_derive_refit_produces_combined_widen_and_reposition():
    # fig2 C001: 2-line caption (text width 2.6cm) crossing the axis at y=3.90.
    edit = lrd.derive_refit(NODE, ["% pre", AXIS], lines_count=2)
    assert edit == {
        "edit_class": "label_refit",
        "text_width_cm": 5.72,  # lines x current width x 1.10 margin
        "reposition": {"axis": "y", "dx_cm": -0.34},  # (3.90 - 0.12) - 4.12
    }


def test_derive_refit_none_without_text_width():
    assert lrd.derive_refit("\\node at (7.60,4.12) {x};", [AXIS], lines_count=2) is None


def test_derive_refit_none_without_crossed_line():
    assert lrd.derive_refit(NODE, ["% no draws here"], lines_count=2) is None


def test_node_line_count_matches_node_words_and_counts_rows():
    node_text = "PI, PDMS, PET (shallow, leaky)"
    words = [
        {"text": "PI,", "xmin": 0, "ymin": 0, "xmax": 10, "ymax": 18},
        {"text": "PDMS,", "xmin": 12, "ymin": 0, "xmax": 30, "ymax": 18},
        {"text": "PET", "xmin": 32, "ymin": 0, "xmax": 45, "ymax": 18},
        {"text": "(shallow,", "xmin": 0, "ymin": 24, "xmax": 25, "ymax": 42},
        {"text": "leaky)", "xmin": 27, "ymin": 24, "xmax": 45, "ymax": 42},
        {"text": "UNRELATED", "xmin": 200, "ymin": 200, "xmax": 220, "ymax": 218},
    ]
    assert lrd.node_line_count(node_text, words) == 2


def test_node_line_count_returns_one_when_no_words_match():
    words = [{"text": "XYZ", "xmin": 0, "ymin": 0, "xmax": 1, "ymax": 1}]
    assert lrd.node_line_count("ABC DEF", words) == 1
