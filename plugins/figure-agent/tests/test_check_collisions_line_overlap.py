"""Regression: word-pair IoU cannot see two-line crowding.

The boxes below are the measured pdftotext geometry of the
fig2_charge_transport_mechanism strip before the 2026-08-07 header repair, when
its group title sat 0.03 cm above an italic sub-line.  A reader saw the two
lines touching, but every word pair scored under the 0.05 IoU threshold because
the intersection band is thin next to the union of two wide word boxes.
"""

from __future__ import annotations

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "checks"))

from check_collisions import (  # noqa: E402
    find_collisions,
    find_line_overlaps,
    group_text_runs,
)


def _word(text: str, xmin: float, ymin: float, xmax: float, ymax: float) -> dict:
    return {"text": text, "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}


# Title line and the sub-line beneath it; y grows downward (pdftotext origin).
CROWDED_TITLE = [
    _word("Sulfur-rich", 151.7, 21.2, 184.1, 27.3),
    _word("copolymer:", 185.9, 21.2, 220.5, 27.3),
    _word("progressive", 223.0, 21.2, 259.6, 27.3),
    _word("trapping", 261.3, 21.2, 287.2, 27.3),
    _word("same", 142.4, 26.3, 155.9, 31.6),
    _word("MIM", 157.4, 26.3, 168.2, 31.6),
    _word("geometry;", 169.7, 26.3, 194.0, 31.6),
    _word("held", 195.5, 26.3, 205.9, 31.6),
    _word("field", 207.4, 26.3, 217.6, 31.6),
    _word("and", 219.1, 26.3, 228.3, 31.6),
    _word("time", 229.8, 26.3, 240.3, 31.6),
    _word("progress", 242.0, 26.3, 263.3, 31.6),
    _word("left", 264.8, 26.3, 272.2, 31.6),
    _word("to", 273.8, 26.3, 278.3, 31.6),
    _word("right", 279.8, 26.3, 290.5, 31.6),
]

# Two labels on one baseline, a normal figure with no crowding at all.
SEPARATE_LABELS = [
    _word("early", 121.4, 114.7, 133.3, 120.0),
    _word("field-on", 134.8, 114.7, 153.0, 120.0),
    _word("progressive", 194.6, 114.7, 222.9, 120.0),
    _word("trapping", 224.4, 114.7, 244.3, 120.0),
]

# A math subscript sitting between glyphs its own run already owns.
SUBSCRIPT_RUN = [
    _word("E", 340.7, 9.3, 346.2, 14.1),
    _word("app", 346.2, 10.4, 358.1, 15.2),
    _word("=", 360.9, 9.3, 366.5, 14.1),
]


def test_word_pair_iou_cannot_decide_the_crowded_title() -> None:
    """The visible overlap scores on the knife edge of the IoU threshold.

    Fourteen word pairs genuinely intersect here, yet the best of them scores
    0.055: the overlap band is thin next to the union of two wide word boxes.
    The same layout was reported or silently accepted depending on which font
    the engine resolved, and a threshold one hundredth higher loses all of it.
    """
    scores = [score for _, _, score in find_collisions(CROWDED_TITLE, 0.0)]
    assert len(scores) >= 10, "the words do intersect, many times over"
    assert max(scores) < 0.06
    assert find_collisions(CROWDED_TITLE, 0.06) == []


def test_line_band_overlap_catches_the_crowded_title() -> None:
    overlaps = find_line_overlaps(CROWDED_TITLE)
    assert len(overlaps) == 1
    first, second, vertical, horizontal = overlaps[0]
    assert "progressive" in first["text"]
    assert "geometry;" in second["text"]
    assert vertical > 0.5
    assert horizontal > 2.0


def test_separate_labels_on_one_baseline_are_one_row_of_two_runs() -> None:
    assert len(group_text_runs(SEPARATE_LABELS)) == 2
    assert find_line_overlaps(SEPARATE_LABELS) == []


def test_subscript_stays_inside_its_own_run() -> None:
    runs = group_text_runs(SUBSCRIPT_RUN)
    base = next(run for run in runs if "E" in run["text"].split())
    assert "app" in base["text"], "the subscript belongs to its base glyph"
    assert find_line_overlaps(SUBSCRIPT_RUN) == []
