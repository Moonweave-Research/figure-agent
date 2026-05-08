from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

REPO_ROOT = Path(__file__).resolve().parents[1]


def _helper_module():
    try:
        return importlib.import_module("spec_bbox_helper")
    except ModuleNotFoundError:
        pytest.fail("scripts/spec_bbox_helper.py should exist")


def test_fig1_overview_v2_tex_geometry_matches_spec_sanity_values():
    helper = _helper_module()
    tex_path = REPO_ROOT / "examples" / "fig1_overview_v2" / "fig1_overview_v2.tex"

    geometry = helper.parse_tex_geometry(tex_path.read_text(encoding="utf-8"))

    assert geometry.cm_per_source == pytest.approx(17.8 / 14.0, abs=1e-6)
    assert geometry.origin_offset_cm == pytest.approx(4.0 * 2.54 / 72.0, abs=1e-6)
    assert geometry.source_size_cm == pytest.approx((14.0, 9.0), abs=1e-6)


def test_fig1_overview_v2_source_bbox_converts_to_pdf_cm_top_left_y_down():
    helper = _helper_module()
    tex_path = REPO_ROOT / "examples" / "fig1_overview_v2" / "fig1_overview_v2.tex"
    geometry = helper.parse_tex_geometry(tex_path.read_text(encoding="utf-8"))

    bbox = helper.convert_source_bbox_to_pdf_cm((0.0, 5.0, 3.5, 9.0), geometry)

    assert bbox == pytest.approx(
        [
            0.141111,
            0.141111,
            4.591111,
            5.226825,
        ],
        abs=1e-5,
    )


def test_spec_bbox_helper_formats_panel_yaml_line():
    helper = _helper_module()

    line = helper.format_panel_bbox("row1", [0.141111, 0.141111, 4.591111, 5.226825])

    assert line == "  - id: row1\n    bbox_pdf_cm: [0.141, 0.141, 4.591, 5.227]"
