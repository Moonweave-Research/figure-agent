from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import bounded_coordinate_offset  # noqa: E402

_COORD_RE = re.compile(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)")


def test_bare_coordinate_offsets_first_x_only() -> None:
    line = "\\draw[line width=0.5pt] (0.45,6.15) -- (4.78,6.15);"
    result = bounded_coordinate_offset.offset_first_coordinate(line)
    assert result is not None
    assert "(0.55, 6.15)" in result
    assert result.endswith("-- (4.78,6.15);")
    coords = _COORD_RE.findall(result)
    assert coords[0] == ("0.55", "6.15")
    assert coords[1] == ("4.78", "6.15")


def test_first_coordinate_y_unchanged() -> None:
    line = "\\draw (1.00,2.00) -- (3.00,4.00);"
    result = bounded_coordinate_offset.offset_first_coordinate(line)
    assert result is not None
    first = _COORD_RE.findall(result)[0]
    assert first[1] == "2.00"


def test_node_at_form_still_offsets() -> None:
    line = "\\node[anchor=west] at (3.0, 2.4) {mobility edge};"
    result = bounded_coordinate_offset.offset_first_coordinate(line)
    assert result == "\\node[anchor=west] at (3.10, 2.4) {mobility edge};"


def test_offset_too_large_returns_none() -> None:
    line = "\\draw (0.45,6.15) -- (4.78,6.15);"
    assert bounded_coordinate_offset.offset_first_coordinate(line, dx_cm=0.5) is None


def test_no_coordinate_returns_none() -> None:
    line = "\\node[anchor=west] {mobility edge};"
    assert bounded_coordinate_offset.offset_first_coordinate(line) is None


def test_parse_back_delta_is_exactly_max_translate() -> None:
    line = "\\draw (0.45,6.15) -- (4.78,6.15);"
    result = bounded_coordinate_offset.offset_first_coordinate(line)
    assert result is not None
    old_x = float(_COORD_RE.findall(line)[0][0])
    new_x = float(_COORD_RE.findall(result)[0][0])
    assert abs((new_x - old_x) - bounded_coordinate_offset.MAX_TRANSLATE_CM) < 1e-9


def test_negative_coordinate_offsets() -> None:
    line = "\\draw (-0.50,1.00) -- (1.00,1.00);"
    result = bounded_coordinate_offset.offset_first_coordinate(line)
    assert result is not None
    assert _COORD_RE.findall(result)[0] == ("-0.40", "1.00")


def test_offset_all_coordinates_translates_whole_line_on_y() -> None:
    line = "\\draw (0.45,6.15) -- (4.78,6.15);"
    result = bounded_coordinate_offset.offset_all_coordinates(line, axis="y", dx_cm=-0.10)
    assert result is not None
    coords = _COORD_RE.findall(result)
    assert coords[0] == ("0.45", "6.05")
    assert coords[1] == ("4.78", "6.05")


def test_offset_all_coordinates_translates_whole_line_on_x() -> None:
    line = "\\draw[axisArr] (6.10,3.90) -- (6.10,9.15);"
    result = bounded_coordinate_offset.offset_all_coordinates(line, axis="x", dx_cm=-0.10)
    assert result is not None
    coords = _COORD_RE.findall(result)
    assert coords[0] == ("6.00", "3.90")
    assert coords[1] == ("6.00", "9.15")


def test_offset_all_coordinates_rejects_overlarge_offset() -> None:
    line = "\\draw (0.45,6.15) -- (4.78,6.15);"
    assert bounded_coordinate_offset.offset_all_coordinates(line, axis="y", dx_cm=0.5) is None


def test_offset_direction_horizontal_line_text_above_in_pt_moves_negative_tikz_y() -> None:
    # fig2 line 49: horizontal line at pt-y 174.33; word 'shallow' sits at SMALLER
    # pt-y (165-172). pdfplumber y grows downward and tikz-y is flipped, so moving
    # the line AWAY (to larger pt-y) is a NEGATIVE tikz-y offset.
    line_bbox = [12.76, 174.33, 135.50, 174.33]
    word_bbox = [21.5, 165.5, 45.6, 172.1]
    axis, dx_cm = bounded_coordinate_offset.offset_direction(line_bbox, word_bbox)
    assert axis == "y"
    assert dx_cm < 0


def test_offset_direction_horizontal_line_text_below_in_pt_moves_positive_tikz_y() -> None:
    line_bbox = [12.76, 174.33, 135.50, 174.33]
    word_bbox = [21.5, 176.0, 45.6, 182.0]
    axis, dx_cm = bounded_coordinate_offset.offset_direction(line_bbox, word_bbox)
    assert axis == "y"
    assert dx_cm > 0


def test_offset_direction_vertical_line_text_right_moves_negative_tikz_x() -> None:
    # fig2 line 72/81: vertical line; word sits to the RIGHT (larger pt-x). x is not
    # flipped, so moving the line AWAY (to smaller pt-x) is a NEGATIVE tikz-x offset.
    line_bbox = [140.31, 12.76, 140.31, 276.38]
    word_bbox = [141.6, 57.6, 145.7, 64.3]
    axis, dx_cm = bounded_coordinate_offset.offset_direction(line_bbox, word_bbox)
    assert axis == "x"
    assert dx_cm < 0


def test_offset_direction_vertical_line_text_left_moves_positive_tikz_x() -> None:
    line_bbox = [140.31, 12.76, 140.31, 276.38]
    word_bbox = [120.8, 57.6, 139.2, 64.3]
    axis, dx_cm = bounded_coordinate_offset.offset_direction(line_bbox, word_bbox)
    assert axis == "x"
    assert dx_cm > 0


def test_offset_direction_returns_none_for_diagonal_line() -> None:
    line_bbox = [10.0, 10.0, 50.0, 80.0]
    word_bbox = [60.0, 60.0, 70.0, 70.0]
    assert bounded_coordinate_offset.offset_direction(line_bbox, word_bbox) is None
