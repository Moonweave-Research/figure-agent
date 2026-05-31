from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_undeclared_geometry import (  # noqa: E402
    detect_undeclared_geometry,
    undeclared_geometry_payload,
)


def _word(text: str, x0: float, y0: float, x1: float, y1: float) -> dict:
    return {"text": text, "xmin": x0, "ymin": y0, "xmax": x1, "ymax": y1}


def test_empty_source_writes_empty_report(tmp_path: Path) -> None:
    pdf_path = tmp_path / "examples" / "demo" / "build" / "demo.pdf"
    pdf_path.parent.mkdir(parents=True)

    candidates = detect_undeclared_geometry("", [], {})
    payload = undeclared_geometry_payload(pdf_path, candidates)

    assert payload["schema"] == "figure-agent.undeclared-geometry.v1"
    assert payload["candidates"] == []
    assert payload["total"] == 0


def test_undeclared_rect_boundary_is_reported() -> None:
    tex = r"\draw[cGray] (1.0,2.0) rectangle (3.0,2.5);"

    candidates = detect_undeclared_geometry(tex, [], {})

    assert [candidate["kind"] for candidate in candidates] == ["undeclared_rect_boundary"]
    assert candidates[0]["id"] == "UG001"
    assert candidates[0]["recommended_action"] == "add_spec_check"


def test_declared_rect_boundary_suppresses_candidate() -> None:
    tex = r"\draw[cGray] (1.0,2.0) rectangle (3.0,2.5);"
    spec = {
        "text_boundary_checks": [
            {
                "id": "box-a",
                "kind": "rect",
                "role": "instrument_box",
                "bbox_pdf_cm": [1.0, 2.0, 3.0, 2.5],
            }
        ]
    }

    assert detect_undeclared_geometry(tex, [], spec) == []


def test_undeclared_column_rule_is_reported() -> None:
    tex = r"\draw[cGray] (4.62,1.0) -- (4.62,6.0);"

    candidates = detect_undeclared_geometry(tex, [], {})

    assert [candidate["kind"] for candidate in candidates] == ["undeclared_column_rule"]


def test_declared_vertical_rule_suppresses_candidate() -> None:
    tex = r"\draw[cGray] (4.62,1.0) -- (4.62,6.0);"
    spec = {
        "text_boundary_checks": [
            {
                "id": "de-rule",
                "kind": "vertical_line",
                "role": "column_rule",
                "pdf_cm_x": 4.62,
                "pdf_cm_y_range": [1.0, 6.0],
            }
        ]
    }

    assert detect_undeclared_geometry(tex, [], spec) == []


def test_label_endpoint_near_miss_is_reported() -> None:
    tex = r"\draw[cGray] (1.0,1.0) -- (2.0,1.0);"
    # Horizontal rule at y ~= 28.346 pt. This word sits within the default
    # near-miss band but does not intersect the line.
    words = [_word("mobility", 58.0, 30.0, 90.0, 38.0)]

    candidates = detect_undeclared_geometry(tex, words, {})

    assert candidates[0]["kind"] == "undeclared_horizontal_rule"
    assert candidates[1]["kind"] == "label_endpoint_near_miss"
    assert candidates[1]["nearest_text"] == "mobility"
    assert 0 < candidates[1]["distance_pt"] < 4


def test_candidate_ids_are_deterministic() -> None:
    tex = "\n".join(
        [
            r"\draw[cGray] (4.62,1.0) -- (4.62,6.0);",
            r"\draw[cGray] (1.0,2.0) rectangle (3.0,2.5);",
        ]
    )

    first = detect_undeclared_geometry(tex, [], {})
    second = detect_undeclared_geometry(tex, [], {})

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
