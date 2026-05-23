from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import text_boundary_spec_helper as helper  # noqa: E402


def _write_fixture(tmp_path: Path, spec: str) -> Path:
    fixture = tmp_path / "examples" / "demo"
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(spec, encoding="utf-8")
    return fixture


def test_build_text_boundary_checks_from_layout_sections() -> None:
    layout = {
        "clearance_pt": 0.5,
        "row_boxes": [
            {
                "id": "row2",
                "bbox_pdf_cm": [0.0, 0.0, 13.8, 4.5],
                "text_allowlist": ["polymer", "SMU"],
            }
        ],
        "column_rules": [{"id": "de", "x_pdf_cm": 4.62, "y_range_pdf_cm": [0.0, 4.5]}],
        "horizontal_rules": [
            {
                "id": "row2_bottom",
                "y_pdf_cm": 4.5,
                "x_range_pdf_cm": [0.0, 13.8],
                "role": "panel_boundary",
            }
        ],
        "forbidden_rects": [
            {
                "id": "vs_meter_display",
                "bbox_pdf_cm": [8.08, 3.58, 9.0, 4.05],
                "role": "instrument_internal_drawing",
                "clearance_pt": 0.2,
            }
        ],
    }

    checks = helper.build_text_boundary_checks(layout)

    assert checks == [
        {
            "id": "row2_contain_text",
            "kind": "rect",
            "role": "row_box",
            "bbox_pdf_cm": [0.0, 0.0, 13.8, 4.5],
            "mode": "contain_text",
            "clearance_pt": 0.5,
            "text_allowlist": ["polymer", "SMU"],
        },
        {
            "id": "de_column_rule",
            "kind": "vertical_line",
            "role": "column_rule",
            "x_pdf_cm": 4.62,
            "y_range_pdf_cm": [0.0, 4.5],
            "clearance_pt": 0.5,
        },
        {
            "id": "row2_bottom_horizontal_rule",
            "kind": "horizontal_line",
            "role": "panel_boundary",
            "y_pdf_cm": 4.5,
            "x_range_pdf_cm": [0.0, 13.8],
            "clearance_pt": 0.5,
        },
        {
            "id": "vs_meter_display_avoid_inside",
            "kind": "rect",
            "role": "instrument_internal_drawing",
            "bbox_pdf_cm": [8.08, 3.58, 9.0, 4.05],
            "mode": "avoid_inside",
            "clearance_pt": 0.2,
        },
    ]


def test_build_text_boundary_checks_rejects_malformed_bbox() -> None:
    layout = {"row_boxes": [{"id": "row2", "bbox_pdf_cm": [0.0, 1.0, 2.0]}]}

    with pytest.raises(helper.TextBoundarySpecHelperError, match="bbox_pdf_cm"):
        helper.build_text_boundary_checks(layout)


def test_build_text_boundary_checks_rejects_malformed_text_allowlist() -> None:
    layout = {
        "row_boxes": [
            {
                "id": "row2",
                "bbox_pdf_cm": [0.0, 0.0, 13.8, 4.5],
                "text_allowlist": ["polymer", ""],
            }
        ]
    }

    with pytest.raises(helper.TextBoundarySpecHelperError, match="text_allowlist"):
        helper.build_text_boundary_checks(layout)


def test_main_prints_yaml_snippet_without_writing(tmp_path: Path, capsys, monkeypatch) -> None:
    fixture = _write_fixture(
        tmp_path,
        "name: demo\n"
        "text_boundary_layout:\n"
        "  clearance_pt: 0.5\n"
        "  column_rules:\n"
        "    - id: de\n"
        "      x_pdf_cm: 4.62\n"
        "      y_range_pdf_cm: [0.0, 4.5]\n",
    )
    before = (fixture / "spec.yaml").read_text(encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["text_boundary_spec_helper.py", str(fixture)])

    assert helper.main() == 0

    captured = capsys.readouterr()
    assert "text_boundary_checks:" in captured.out
    assert "id: de_column_rule" in captured.out
    assert (fixture / "spec.yaml").read_text(encoding="utf-8") == before


def test_main_write_updates_spec_checks_deterministically(tmp_path: Path, monkeypatch) -> None:
    fixture = _write_fixture(
        tmp_path,
        "name: demo\n"
        "text_boundary_checks:\n"
        "  - id: stale\n"
        "    kind: vertical_line\n"
        "    role: column_rule\n"
        "    x_pdf_cm: 1.0\n"
        "    y_range_pdf_cm: [0.0, 1.0]\n"
        "text_boundary_layout:\n"
        "  row_boxes:\n"
        "    - id: row2\n"
        "      bbox_pdf_cm: [0.0, 0.0, 13.8, 4.5]\n",
    )
    monkeypatch.setattr(sys, "argv", ["text_boundary_spec_helper.py", str(fixture), "--write"])

    assert helper.main() == 0

    spec = yaml.safe_load((fixture / "spec.yaml").read_text(encoding="utf-8"))
    assert spec["text_boundary_checks"] == [
        {
            "id": "row2_contain_text",
            "kind": "rect",
            "role": "row_box",
            "bbox_pdf_cm": [0.0, 0.0, 13.8, 4.5],
            "mode": "contain_text",
            "clearance_pt": 0.5,
        }
    ]
    first_write = (fixture / "spec.yaml").read_text(encoding="utf-8")

    assert helper.main() == 0

    assert (fixture / "spec.yaml").read_text(encoding="utf-8") == first_write


def test_main_returns_two_when_layout_missing(tmp_path: Path, capsys, monkeypatch) -> None:
    fixture = _write_fixture(tmp_path, "name: demo\n")
    monkeypatch.setattr(sys, "argv", ["text_boundary_spec_helper.py", str(fixture)])

    assert helper.main() == 2

    captured = capsys.readouterr()
    assert "text_boundary_layout is missing" in captured.err
