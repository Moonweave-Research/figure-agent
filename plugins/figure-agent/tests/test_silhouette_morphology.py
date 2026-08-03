from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

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


def test_select_curve_fails_closed_on_ambiguous_rendered_targets() -> None:
    first = _curve([("m", (0.0, 0.0)), ("l", (1.0, 1.0)), ("h",)])
    second = dict(first)

    with pytest.raises(
        morphology.SilhouetteMorphologyError,
        match="target_curve_ambiguous",
    ):
        morphology.select_curve(
            [first, second],
            bbox_pt=[0.0, 0.0, 60.0, 70.0],
            stroke_rgb=[0.48, 0.38, 0.09],
            color_tolerance=0.03,
        )


def test_analyze_stroked_centerline_reports_rendered_member_metrics() -> None:
    curve = _curve(
        [
            ("m", (20.0, 0.0)),
            ("c", (20.0, 20.0), (24.0, 39.0), (30.0, 55.0)),
        ]
    )
    curve["fill"] = False
    curve["linewidth"] = 4.0

    result = morphology.analyze_stroked_centerline(
        curve,
        max_width_to_length_ratio=0.10,
    )

    assert result["violations"] == []
    assert result["metrics"]["stroke_width_pt"] == 4.0
    assert result["metrics"]["tip_displacement_x_pt"] == 10.0
    assert result["metrics"]["centerline_length_pt"] > 55.0


def test_analyze_stroked_centerline_rejects_single_cubic_loop() -> None:
    curve = _curve(
        [
            ("m", (0.0, 0.0)),
            ("c", (10.0, 10.0), (-10.0, 10.0), (1.0, 0.0)),
        ]
    )
    curve["fill"] = False
    curve["linewidth"] = 1.0

    result = morphology.analyze_stroked_centerline(
        curve,
        max_width_to_length_ratio=0.20,
    )

    assert "self_intersection" in result["violations"]


def test_group_comparison_rejects_scale_drift_and_wrong_bend_order() -> None:
    results = [
        {
            "id": "residual",
            "metrics": {
                "centerline_length_pt": 70.0,
                "stroke_width_pt": 6.0,
                "tip_displacement_x_pt": 14.0,
            },
        },
        {
            "id": "reverse",
            "metrics": {
                "centerline_length_pt": 78.0,
                "stroke_width_pt": 7.0,
                "tip_displacement_x_pt": -10.0,
            },
        },
        {
            "id": "drive",
            "metrics": {
                "centerline_length_pt": 71.0,
                "stroke_width_pt": 6.0,
                "tip_displacement_x_pt": 26.0,
            },
        },
    ]
    groups = [
        {
            "id": "sequence",
            "member_ids": ["residual", "reverse", "drive"],
            "max_centerline_length_ratio": 1.06,
            "max_stroke_width_ratio": 1.10,
            "minimum_bend_step_pt": 3.0,
            "absolute_bend_order": ["residual", "reverse", "drive"],
            "tip_directions": {
                "residual": "positive",
                "reverse": "negative",
                "drive": "positive",
            },
        }
    ]

    compared = morphology.analyze_groups(results, groups)

    assert compared[0]["violations"] == [
        "centerline_length_ratio",
        "stroke_width_ratio",
        "absolute_bend_order",
    ]


def test_group_comparison_accepts_complete_order_without_pairing_error() -> None:
    results = [
        {
            "id": member_id,
            "metrics": {
                "centerline_length_pt": 70.0,
                "stroke_width_pt": 6.0,
                "tip_displacement_x_pt": displacement,
            },
        }
        for member_id, displacement in (
            ("residual", 10.0),
            ("reverse", -20.0),
            ("drive", 30.0),
        )
    ]

    compared = morphology.analyze_groups(
        results,
        [
            {
                "id": "sequence",
                "member_ids": ["residual", "reverse", "drive"],
                "absolute_bend_order": ["residual", "reverse", "drive"],
                "minimum_bend_step_pt": 5.0,
            }
        ],
    )

    assert compared[0]["violations"] == []


def test_report_binds_render_and_spec_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf = tmp_path / "figure.pdf"
    spec = tmp_path / "spec.yaml"
    pdf.write_bytes(b"render-bytes")
    spec.write_text(
        "silhouette_morphology_checks: []\n"
        "silhouette_morphology_groups: []\n",
        encoding="utf-8",
    )

    class _Page:
        curves: list[dict[str, object]] = []

    class _Document:
        pages = [_Page()]

        def __enter__(self) -> _Document:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr(morphology.pdfplumber, "open", lambda _path: _Document())

    report = morphology.check_pdf(pdf, spec)

    assert report["render_pdf_sha256"] == hashlib.sha256(pdf.read_bytes()).hexdigest()
    assert report["spec_sha256"] == hashlib.sha256(spec.read_bytes()).hexdigest()


def test_product_contract_keeps_morphology_gate_narrow_and_render_based() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    contract = (plugin_root / "docs" / "figure-agent.md").read_text(
        encoding="utf-8"
    )
    skill = (plugin_root / "skills" / "figure-agent" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "`filled_boundary`" in contract
    assert "`stroked_centerline`" in contract
    assert "`silhouette_morphology_groups`" in contract
    assert "not an aesthetic score" in contract
    assert "representation: stroked_centerline" in skill
    assert "regression evidence only" in skill
