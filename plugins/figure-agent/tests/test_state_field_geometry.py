from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "checks"))

from check_state_field_geometry import (  # noqa: E402
    StateFieldGeometryError,
    evaluate_state_field,
    state_field_geometry_payload,
)


def test_rejects_a_center_widening_field_that_reads_as_a_density_envelope() -> None:
    marks = [
        (1.0, 10.0, 0.20),
        (1.2, 10.0, 0.40),
        (1.4, 10.0, 0.80),
        (1.6, 10.0, 0.40),
        (1.8, 10.0, 0.20),
    ]

    result = evaluate_state_field(
        marks,
        min_marks=5,
        min_vertical_span_cm=0.7,
        min_center_std_cm=0.0,
        max_width_abs_midpoint_correlation=-0.35,
    )

    assert result["status"] == "violated"
    assert result["violations"] == ["symmetric_density_silhouette"]


def test_accepts_an_irregular_field_without_a_centered_width_envelope() -> None:
    marks = [
        (1.0, 9.4, 0.32),
        (1.2, 10.8, 0.44),
        (1.4, 9.8, 0.27),
        (1.6, 10.5, 0.36),
        (1.8, 9.6, 0.41),
        (2.0, 10.2, 0.29),
    ]

    result = evaluate_state_field(
        marks,
        min_marks=6,
        min_vertical_span_cm=0.9,
        min_center_std_cm=0.35,
        max_width_abs_midpoint_correlation=-0.35,
    )

    assert result["status"] == "passed"
    assert result["violations"] == []


def test_rejects_invalid_thresholds() -> None:
    with pytest.raises(StateFieldGeometryError, match="max_width_abs_midpoint_correlation"):
        evaluate_state_field(
            [(1.0, 10.0, 0.2), (2.0, 10.5, 0.3)],
            min_marks=2,
            min_vertical_span_cm=0.5,
            min_center_std_cm=0.0,
            max_width_abs_midpoint_correlation=1.1,
        )


def test_fig3_s80_state_field_passes_the_declared_non_envelope_contract() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    fixture = plugin_root / "examples" / "fig3_resistance_mechanism"

    payload = state_field_geometry_payload(
        fixture / "fig3_resistance_mechanism.tex", fixture / "spec.yaml"
    )

    assert payload["issues"] == []
    assert payload["results"] == [
        {
            "id": "fig3-s80-irregular-state-field",
            "source_object": "s80_continuous_support",
            "status": "passed",
            "metrics": {
                "mark_count": 14,
                "vertical_span_cm": 1.56,
                "center_std_cm": 0.48787,
                "width_abs_midpoint_correlation": -0.087962,
            },
            "violations": [],
        }
    ]
