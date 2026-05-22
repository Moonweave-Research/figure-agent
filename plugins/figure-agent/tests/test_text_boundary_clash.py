from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_text_boundary_clash as boundary  # noqa: E402


def _word(text: str, xmin: float, ymin: float, xmax: float, ymax: float) -> dict[str, float | str]:
    return {"text": text, "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}


def test_detects_text_crossing_vertical_column_rule() -> None:
    checks = [
        {
            "id": "de_column_rule",
            "kind": "vertical_line",
            "role": "column_rule",
            "x_pdf_cm": 2.54,
            "y_range_pdf_cm": [0.0, 5.08],
            "clearance_pt": 0.5,
        }
    ]
    words = [_word("polymer", 70.0, 20.0, 75.0, 30.0)]

    candidates = boundary.detect_text_boundary_clashes(words, (200.0, 200.0), checks)

    assert [candidate["id"] for candidate in candidates] == ["TB001"]
    assert candidates[0]["kind"] == "text_crosses_vertical_boundary"
    assert candidates[0]["text"] == "polymer"
    assert candidates[0]["boundary_id"] == "de_column_rule"
    assert candidates[0]["boundary_role"] == "column_rule"
    assert candidates[0]["boundary_pt"] == {"x": 72.0, "y_range": [0.0, 144.0]}


def test_ignores_text_outside_vertical_rule_y_range() -> None:
    checks = [
        {
            "id": "de_column_rule",
            "kind": "vertical_line",
            "role": "column_rule",
            "x_pdf_cm": 2.54,
            "y_range_pdf_cm": [0.0, 1.0],
            "clearance_pt": 0.5,
        }
    ]
    words = [_word("polymer", 70.0, 90.0, 75.0, 100.0)]

    assert boundary.detect_text_boundary_clashes(words, (200.0, 200.0), checks) == []


def test_detects_text_crossing_horizontal_panel_boundary() -> None:
    checks = [
        {
            "id": "row2_bottom",
            "kind": "horizontal_line",
            "role": "panel_boundary",
            "y_pdf_cm": 2.54,
            "x_range_pdf_cm": [0.0, 5.08],
            "clearance_pt": 0.0,
        }
    ]
    words = [_word("Debye", 20.0, 70.0, 60.0, 75.0)]

    candidates = boundary.detect_text_boundary_clashes(words, (200.0, 200.0), checks)

    assert candidates[0]["kind"] == "text_crosses_horizontal_boundary"
    assert candidates[0]["boundary_pt"] == {"y": 72.0, "x_range": [0.0, 144.0]}


def test_detects_text_outside_containing_row_box() -> None:
    checks = [
        {
            "id": "row2_box",
            "kind": "rect",
            "role": "row_box",
            "mode": "contain_text",
            "bbox_pdf_cm": [0.0, 0.0, 5.08, 2.54],
            "clearance_pt": 0.0,
        }
    ]
    words = [_word("film", 20.0, 68.0, 50.0, 75.0)]

    candidates = boundary.detect_text_boundary_clashes(words, (200.0, 200.0), checks)

    assert candidates[0]["kind"] == "text_outside_rect"
    assert candidates[0]["boundary_role"] == "row_box"


def test_detects_text_inside_forbidden_rect() -> None:
    checks = [
        {
            "id": "display_region",
            "kind": "rect",
            "role": "instrument_internal_drawing",
            "mode": "avoid_inside",
            "bbox_pdf_cm": [1.0, 1.0, 2.0, 2.0],
            "clearance_pt": 0.0,
        }
    ]
    words = [_word("V", 35.0, 35.0, 45.0, 45.0)]

    candidates = boundary.detect_text_boundary_clashes(words, (200.0, 200.0), checks)

    assert candidates[0]["kind"] == "text_inside_forbidden_rect"
    assert candidates[0]["boundary_id"] == "display_region"


def test_payload_uses_stable_json_contract(tmp_path: Path) -> None:
    pdf = tmp_path / "demo" / "build" / "demo.pdf"
    candidate = {
        "id": "TB001",
        "kind": "text_crosses_vertical_boundary",
        "text": "polymer",
        "boundary_id": "de_column_rule",
        "boundary_role": "column_rule",
        "bbox_pt": [70.0, 20.0, 75.0, 30.0],
        "boundary_pt": {"x": 72.0, "y_range": [0.0, 144.0]},
        "clearance_pt": 0.5,
    }

    assert boundary.text_boundary_clash_payload(pdf, [candidate]) == {
        "schema": "figure-agent.text-boundary-clash.v1",
        "fixture": "demo",
        "render_pdf": "build/demo.pdf",
        "source": "spec.yaml:text_boundary_checks",
        "candidates": [candidate],
        "total": 1,
    }


def test_payload_infers_fixture_name_for_compile_sh_relative_pdf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = tmp_path / "demo"
    (fixture / "build").mkdir(parents=True)
    monkeypatch.chdir(fixture)

    payload = boundary.text_boundary_clash_payload(Path("build/demo.pdf"), [])

    assert payload["fixture"] == "demo"
    assert payload["render_pdf"] == "build/demo.pdf"


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
    output = build / "text_boundary_clash.json"
    monkeypatch.setattr(boundary, "extract_pdf_words_and_page", lambda _pdf: ([], (200.0, 200.0)))
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_text_boundary_clash.py", str(pdf), "--json-output", str(output)],
    )

    assert boundary.main() == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema"] == "figure-agent.text-boundary-clash.v1"
    assert report["candidates"] == []
    assert report["total"] == 0


def test_main_strict_returns_one_when_boundary_candidates_exist(
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
        "text_boundary_checks:\n"
        "  - id: de_column_rule\n"
        "    kind: vertical_line\n"
        "    role: column_rule\n"
        "    x_pdf_cm: 2.54\n"
        "    y_range_pdf_cm: [0.0, 5.08]\n"
        "    clearance_pt: 0.5\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        boundary,
        "extract_pdf_words_and_page",
        lambda _pdf: ([_word("polymer", 70.0, 20.0, 75.0, 30.0)], (200.0, 200.0)),
    )
    monkeypatch.setattr(sys, "argv", ["check_text_boundary_clash.py", str(pdf), "--strict"])

    assert boundary.main() == 1
