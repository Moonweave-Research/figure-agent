from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "checks"))

from check_print_size_contract import (  # noqa: E402, I001
    _journal_policy_floor,
    evaluate_contract,
)


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
    assert result["placement_size_mm"] == pytest.approx([166.8, 170.0], abs=0.1)
    assert result["print_min_font_pt"] >= 4.4


def test_contract_reports_actual_width_limited_placement_not_height_capacity() -> None:
    result = evaluate_contract(
        page_size_pt=(512.548, 151.769),
        source_font_sizes_pt=[5.1, 5.5, 6.6],
        contract={
            "natural_size_mm": [180.8, 53.5],
            "target_width_mm": 180.0,
            "max_height_mm": 170.0,
            "min_print_font_pt": 5.0,
        },
    )

    assert result["status"] == "passed"
    assert result["placement_size_mm"] == pytest.approx([180.0, 53.3], abs=0.1)
    assert result["width_at_max_height_mm"] > 500.0


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


def test_nature_family_policy_rejects_a_declared_floor_below_five_points() -> None:
    result = evaluate_contract(
        page_size_pt=(427.064, 435.31),
        source_font_sizes_pt=[4.0, 5.8],
        contract={**CONTRACT, "basis": "height_limited_nature_family_main_figure"},
        policy_min_print_font_pt=5.0,
    )

    assert result["status"] == "failed"
    assert result["effective_min_print_font_pt"] == 5.0
    assert any("built-in journal floor" in item for item in result["violations"])
    assert any("effective min_print_font_pt 5.00 pt" in item for item in result["violations"])


def test_non_nature_policy_keeps_the_declared_floor_as_authority() -> None:
    result = evaluate_contract(
        page_size_pt=(427.064, 435.31),
        source_font_sizes_pt=[4.6, 5.8],
        contract={**CONTRACT, "basis": "project_schematic"},
    )

    assert result["status"] == "passed"
    assert result["policy_min_print_font_pt"] is None
    assert result["effective_min_print_font_pt"] == 4.4


def test_journal_policy_floor_is_selected_only_by_explicit_nature_basis() -> None:
    assert (
        _journal_policy_floor(
            {"basis": "height_limited_nature_family_main_figure"}
        )
        == 5.0
    )
    assert _journal_policy_floor({"basis": "project_schematic"}) is None
