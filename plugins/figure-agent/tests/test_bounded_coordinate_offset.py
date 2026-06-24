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
