from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import bounded_text_width  # noqa: E402

NODE = "\\node[labelMute, anchor=north, text width=2.6cm, align=center] at (7.60,4.12)"


def test_set_text_width_replaces_the_width_token():
    result = bounded_text_width.set_text_width(NODE, target_cm=5.6)
    assert result == (
        "\\node[labelMute, anchor=north, text width=5.60cm, align=center] at (7.60,4.12)"
    )


def test_set_text_width_returns_none_without_a_text_width_key():
    assert bounded_text_width.set_text_width("\\node at (1,2) {x}", target_cm=5.6) is None


def test_set_text_width_returns_none_when_delta_exceeds_cap():
    # current 2.6cm -> 9.0cm is a 6.4cm change, past MAX_TEXT_WIDTH_DELTA_CM.
    assert bounded_text_width.set_text_width(NODE, target_cm=9.0) is None


def test_set_text_width_allows_a_change_at_the_cap():
    result = bounded_text_width.set_text_width(
        NODE, target_cm=2.6 + bounded_text_width.MAX_TEXT_WIDTH_DELTA_CM
    )
    assert result is not None
    assert "text width=6.60cm" in result


def test_set_text_width_returns_none_for_nonpositive_target():
    assert bounded_text_width.set_text_width(NODE, target_cm=0.0) is None
    assert bounded_text_width.set_text_width(NODE, target_cm=-1.0) is None


def test_set_text_width_tolerates_spaces_around_equals():
    line = "\\node[text width = 3cm] at (0,0)"
    assert (
        bounded_text_width.set_text_width(line, target_cm=4.0)
        == "\\node[text width=4.00cm] at (0,0)"
    )
