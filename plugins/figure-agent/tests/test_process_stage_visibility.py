from __future__ import annotations

import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "checks"))

from check_process_stage_visibility import (  # noqa: E402
    ProcessStageVisibilityError,
    detect_process_stage_visibility,
    load_process_stage_visibility_checks,
    process_stage_visibility_payload,
)


def _word(text: str, xmin: float, ymin: float, xmax: float, ymax: float) -> dict[str, float | str]:
    return {"text": text, "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}


def _check() -> dict:
    return {
        "id": "charge-off-reversal",
        "panel_id": "A",
        "reading_axis": "x",
        "minimum_stage_separation_pt": 14.0,
        "stages": [
            {"id": "charge", "text_phrases": [{"id": "charge_label", "words": ["CHARGE"]}]},
            {"id": "off_float", "text_phrases": [{"id": "off_label", "words": ["OFF"]}]},
            {"id": "reverse", "text_phrases": [{"id": "reverse_label", "words": ["REVERSE"]}]},
        ],
    }


def test_detect_process_stage_visibility_accepts_rendered_ordered_stage_anchors() -> None:
    words = [
        _word("CHARGE", 12, 20, 44, 28),
        _word("OFF", 76, 20, 90, 28),
        _word("REVERSE", 120, 20, 158, 28),
    ]
    candidates = detect_process_stage_visibility(
        words,
        page_size_pt=(220, 140),
        panel_bboxes={"A": [0, 0, 200, 100]},
        checks=[_check()],
    )

    assert candidates == []


def test_detect_process_stage_visibility_flags_missing_intermediate_state() -> None:
    words = [
        _word("CHARGE", 12, 20, 44, 28),
        _word("REVERSE", 120, 20, 158, 28),
    ]
    candidates = detect_process_stage_visibility(
        words,
        page_size_pt=(220, 140),
        panel_bboxes={"A": [0, 0, 200, 100]},
        checks=[_check()],
    )

    assert candidates == [
        {
            "id": "PS001",
            "kind": "process_stage_anchor_missing",
            "check_id": "charge-off-reversal",
            "panel_id": "A",
            "stage_id": "off_float",
            "required_phrase_ids": ["off_label"],
        }
    ]


def test_detect_process_stage_visibility_flags_reversed_stage_order() -> None:
    words = [
        _word("CHARGE", 80, 20, 112, 28),
        _word("OFF", 20, 20, 34, 28),
        _word("REVERSE", 130, 20, 168, 28),
    ]
    candidates = detect_process_stage_visibility(
        words,
        page_size_pt=(220, 140),
        panel_bboxes={"A": [0, 0, 200, 100]},
        checks=[_check()],
    )

    assert candidates[0]["kind"] == "process_stage_order_invalid"
    assert candidates[0]["before_stage_id"] == "charge"
    assert candidates[0]["after_stage_id"] == "off_float"


def test_detect_process_stage_visibility_uses_label_start_for_long_stage_copy() -> None:
    check = _check()
    check["stages"][0]["text_phrases"].append(
        {"id": "charge_explanation", "words": ["LONG", "COPY"]}
    )
    words = [
        _word("CHARGE", 12, 20, 44, 28),
        _word("LONG", 48, 20, 70, 28),
        _word("COPY", 74, 20, 98, 28),
        _word("OFF", 76, 38, 90, 46),
        _word("REVERSE", 120, 20, 158, 28),
    ]

    candidates = detect_process_stage_visibility(
        words,
        page_size_pt=(220, 140),
        panel_bboxes={"A": [0, 0, 200, 100]},
        checks=[check],
    )

    assert candidates == []


def test_load_process_stage_visibility_checks_rejects_duplicate_stage_id(tmp_path: Path) -> None:
    spec = tmp_path / "spec.yaml"
    spec.write_text(
        """
panels:
  - id: A
    bbox_pdf_cm: [0, 0, 4, 4]
process_stage_visibility_checks:
  - id: bad
    panel_id: A
    reading_axis: x
    stages:
      - id: duplicate
        text_phrases: [{id: first, words: [ONE]}]
      - id: duplicate
        text_phrases: [{id: second, words: [TWO]}]
""",
        encoding="utf-8",
    )

    with pytest.raises(ProcessStageVisibilityError, match="duplicate stage id"):
        load_process_stage_visibility_checks(spec, page_size_pt=(220, 140))


def test_process_stage_visibility_payload_names_fixture_from_build_parent() -> None:
    payload = process_stage_visibility_payload(
        Path("examples/fig5/build/figure.pdf"), [], checked=2
    )

    assert payload["fixture"] == "fig5"
