from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_label_path_proximity as proximity  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]


def _word(text: str, xmin: float, ymin: float, xmax: float, ymax: float) -> dict[str, float | str]:
    return {"text": text, "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}


def test_detects_phrase_stacked_on_horizontal_reference_line() -> None:
    checks = [
        {
            "id": "mobility_edge_reference",
            "kind": "horizontal_line",
            "role": "reference_line",
            "y_pdf_cm": 2.0,
            "x_range_pdf_cm": [14.8, 18.0],
            "clearance_pt": 3.0,
            "text_phrases": [{"id": "mobility_edge", "words": ["mobility", "edge"]}],
        }
    ]
    words = [
        _word("mobility", 443.0, 53.5, 471.0, 61.0),
        _word("edge", 473.0, 53.5, 492.0, 61.0),
    ]

    candidates = proximity.detect_label_path_proximity(words, (520.0, 360.0), checks)

    assert [candidate["id"] for candidate in candidates] == ["LP001"]
    assert candidates[0]["kind"] == "label_stacked_on_reference_line"
    assert candidates[0]["text"] == "mobility edge"
    assert candidates[0]["path_id"] == "mobility_edge_reference"
    assert candidates[0]["path_role"] == "reference_line"
    assert candidates[0]["distance_pt"] < 3.0
    assert candidates[0]["path_pt"]["kind"] == "horizontal_line"


def test_ignores_label_beyond_clearance_from_horizontal_line() -> None:
    checks = [
        {
            "id": "mobility_edge_reference",
            "kind": "horizontal_line",
            "role": "reference_line",
            "y_pdf_cm": 2.0,
            "x_range_pdf_cm": [14.8, 18.0],
            "clearance_pt": 1.0,
            "text_allowlist": ["mobility"],
        }
    ]
    words = [_word("mobility", 443.0, 45.0, 471.0, 51.0)]

    assert proximity.detect_label_path_proximity(words, (520.0, 360.0), checks) == []


def test_detects_label_near_polyline_curve() -> None:
    checks = [
        {
            "id": "deep_escape_curve",
            "kind": "polyline",
            "role": "semantic_curve",
            "points_pdf_cm": [[15.8, 2.45], [16.0, 2.55], [16.2, 2.65]],
            "clearance_pt": 5.0,
            "text_allowlist": ["shallow"],
        }
    ]
    words = [_word("shallow", 430.0, 71.0, 460.0, 79.0)]

    candidates = proximity.detect_label_path_proximity(words, (520.0, 360.0), checks)

    assert candidates[0]["kind"] == "label_curve_near_label"
    assert candidates[0]["text"] == "shallow"
    assert candidates[0]["path_pt"]["kind"] == "polyline"
    assert candidates[0]["distance_pt"] < 5.0


def test_detects_label_near_vertical_path() -> None:
    checks = [
        {
            "id": "leader_line",
            "kind": "vertical_line",
            "role": "leader_line",
            "x_pdf_cm": 2.54,
            "y_range_pdf_cm": [0.0, 5.08],
            "clearance_pt": 2.0,
            "text_allowlist": ["label"],
        }
    ]
    words = [_word("label", 70.5, 20.0, 90.0, 30.0)]

    candidates = proximity.detect_label_path_proximity(words, (200.0, 200.0), checks)

    assert candidates[0]["kind"] == "label_path_near_miss"
    assert candidates[0]["path_pt"] == {"kind": "vertical_line", "x": 72.0, "y_range": [0.0, 144.0]}


def test_rejects_malformed_polyline_points() -> None:
    checks = [
        {
            "id": "curve",
            "kind": "polyline",
            "role": "semantic_curve",
            "points_pdf_cm": [[1.0, 2.0]],
            "clearance_pt": 1.0,
        }
    ]

    with pytest.raises(proximity.LabelPathProximityError, match="points_pdf_cm"):
        proximity.detect_label_path_proximity([], (200.0, 200.0), checks)


def test_payload_uses_stable_json_contract(tmp_path: Path) -> None:
    pdf = tmp_path / "demo" / "build" / "demo.pdf"
    candidate = {
        "id": "LP001",
        "kind": "label_path_near_miss",
        "text": "label",
        "path_id": "leader",
        "path_role": "leader_line",
        "bbox_pt": [70.0, 20.0, 80.0, 30.0],
        "path_pt": {"kind": "vertical_line", "x": 72.0, "y_range": [0.0, 144.0]},
        "clearance_pt": 2.0,
        "distance_pt": 1.0,
    }

    assert proximity.label_path_proximity_payload(pdf, [candidate]) == {
        "schema": "figure-agent.label-path-proximity.v1",
        "fixture": "demo",
        "render_pdf": "build/demo.pdf",
        "source": "spec.yaml:label_path_proximity_checks",
        "candidates": [candidate],
        "total": 1,
    }


def test_main_writes_zero_candidate_json_when_spec_has_no_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = tmp_path / "demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    pdf = build / "demo.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    (fixture / "spec.yaml").write_text("name: demo\n", encoding="utf-8")
    output = build / "label_path_proximity.json"
    monkeypatch.setattr(proximity, "extract_pdf_words_and_page", lambda _pdf: ([], (200.0, 200.0)))
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_label_path_proximity.py", str(pdf), "--json-output", str(output)],
    )

    assert proximity.main() == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema"] == "figure-agent.label-path-proximity.v1"
    assert report["candidates"] == []
    assert report["total"] == 0


def test_main_strict_returns_one_when_candidates_exist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = tmp_path / "demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    pdf = build / "demo.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    (fixture / "spec.yaml").write_text(
        "name: demo\n"
        "label_path_proximity_checks:\n"
        "  - id: reference_line\n"
        "    kind: horizontal_line\n"
        "    role: reference_line\n"
        "    y_pdf_cm: 2.0\n"
        "    x_range_pdf_cm: [14.8, 18.0]\n"
        "    clearance_pt: 3.0\n"
        "    text_allowlist: [mobility]\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        proximity,
        "extract_pdf_words_and_page",
        lambda _pdf: ([_word("mobility", 443.0, 53.5, 471.0, 61.0)], (520.0, 360.0)),
    )
    monkeypatch.setattr(sys, "argv", ["check_label_path_proximity.py", str(pdf), "--strict"])

    assert proximity.main() == 1


def test_fig1_vault_declares_minimal_label_path_proximity_checks() -> None:
    spec_path = (
        REPO_ROOT
        / "examples"
        / "fig1_overview_v2_pair_001_vault"
        / "spec.yaml"
    )

    checks = proximity.load_label_path_proximity_checks(spec_path)
    by_id = {str(check["id"]): check for check in checks}

    assert set(by_id) == {
        "panel_c_mobility_edge_reference",
        "panel_c_deep_escape_curve",
    }
    mobility = by_id["panel_c_mobility_edge_reference"]
    assert mobility["kind"] == "horizontal_line"
    assert mobility["role"] == "reference_line"
    assert mobility["clearance_pt"] == 4.0
    assert mobility["text_phrases"] == [
        {"id": "mobility_edge", "words": ["mobility", "edge"]}
    ]
    shallow = by_id["panel_c_deep_escape_curve"]
    assert shallow["kind"] == "polyline"
    assert shallow["role"] == "semantic_curve"
    assert shallow["clearance_pt"] == 5.0
    assert shallow["text_allowlist"] == ["shallow"]
