from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "checks"))

import check_silhouette_morphology as morphology  # noqa: E402
from svgpathtools import CubicBezier, Line


def _curve(path: list[tuple]) -> dict[str, object]:
    return {
        "path": path,
        "fill": True,
        "stroking_color": (0.48, 0.38, 0.09),
        "x0": 0.0,
        "top": 0.0,
        "x1": 50.0,
        "bottom": 60.0,
    }


def test_analyze_curve_rejects_self_crossing_finite_width_member() -> None:
    curve = _curve(
        [
            ("m", (20.0, 0.0)),
            ("c", (20.0, 20.0), (13.0, 40.0), (4.0, 55.0)),
            ("c", (2.0, 58.0), (0.0, 56.0), (3.0, 53.0)),
            ("c", (14.0, 42.0), (30.0, 25.0), (28.0, 0.0)),
            ("h",),
        ]
    )

    result = morphology.analyze_curve(
        curve,
        max_width_to_length_ratio=0.20,
        max_width_variation_ratio=3.0,
    )

    assert "self_intersection" in result["violations"]


def test_self_intersection_filter_ignores_only_shared_closure_endpoint() -> None:
    segments = [
        Line(0 + 0j, 10 + 0j),
        CubicBezier(10 + 0j, 5 + 10j, 5 - 10j, 0 + 0j),
    ]

    intersections = morphology._self_intersections(segments)

    assert len(intersections) == 1
    assert intersections[0] == 5 + 0j


def test_analyze_curve_accepts_smooth_narrow_member() -> None:
    curve = _curve(
        [
            ("m", (20.0, 0.0)),
            ("c", (20.0, 20.0), (17.0, 39.0), (8.0, 55.0)),
            ("c", (7.0, 57.0), (9.0, 59.0), (11.0, 56.0)),
            ("c", (20.0, 40.0), (28.0, 20.0), (28.0, 0.0)),
            ("h",),
        ]
    )

    result = morphology.analyze_curve(
        curve,
        max_width_to_length_ratio=0.20,
        max_width_variation_ratio=3.0,
    )

    assert result["violations"] == []
    assert result["metrics"]["self_intersection_count"] == 0


def test_analyze_curve_rejects_banana_width_ratio_without_self_intersection() -> None:
    curve = _curve(
        [
            ("m", (18.0, 0.0)),
            ("c", (18.0, 18.0), (20.0, 37.0), (31.0, 52.0)),
            ("c", (36.0, 58.0), (43.0, 52.0), (38.0, 47.0)),
            ("c", (29.0, 35.0), (30.0, 18.0), (31.0, 0.0)),
            ("h",),
        ]
    )

    result = morphology.analyze_curve(
        curve,
        max_width_to_length_ratio=0.15,
        max_width_variation_ratio=3.0,
    )

    assert "width_to_length_ratio" in result["violations"]


def test_select_curve_uses_declared_bbox_and_color_without_fixture_recipe() -> None:
    target = _curve([("m", (0.0, 0.0)), ("l", (1.0, 1.0)), ("h",)])
    wrong_color = dict(target, stroking_color=(0.1, 0.1, 0.1))
    wrong_bbox = dict(target, x0=80.0, x1=90.0, top=80.0, bottom=90.0)

    selected = morphology.select_curve(
        [wrong_color, wrong_bbox, target],
        bbox_pt=[0.0, 0.0, 60.0, 70.0],
        stroke_rgb=[0.48, 0.38, 0.09],
        color_tolerance=0.03,
    )

    assert selected is target
