from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "checks"))

from check_print_size_contract import evaluate_contract  # noqa: E402, I001


CONTRACT = {
    "natural_size_mm": [150.7, 153.6],
    "target_width_mm": 166.8,
    "max_height_mm": 170.0,
    "min_print_font_pt": 4.4,
}


def test_height_limited_contract_passes_for_fig1_geometry() -> None:
    result = evaluate_contract(
        page_size_pt=(427.064, 435.31),
        source_font_sizes_pt=[4.0, 4.5, 5.2, 5.8, 6.2],
        contract=CONTRACT,
    )
    assert result["status"] == "passed"
    assert result["width_at_max_height_mm"] == pytest.approx(166.8, abs=0.1)
    assert result["print_min_font_pt"] >= 4.4


def test_contract_rejects_full_double_column_width_when_too_tall() -> None:
    result = evaluate_contract(
        page_size_pt=(427.064, 435.31),
        source_font_sizes_pt=[4.0, 5.8],
        contract={**CONTRACT, "target_width_mm": 180.0},
    )
    assert result["status"] == "failed"
    assert any("above max_height" in item for item in result["violations"])


def test_contract_rejects_under_sized_print_font() -> None:
    result = evaluate_contract(
        page_size_pt=(427.064, 435.31),
        source_font_sizes_pt=[3.4, 5.8],
        contract=CONTRACT,
    )
    assert result["status"] == "failed"
    assert any("below min_print_font_pt" in item for item in result["violations"])
