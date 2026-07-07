from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


import pytest  # noqa: E402
from check_undeclared_geometry import (  # noqa: E402
    UndeclaredGeometryError,
    _parse_tikz_geometry,
    _undeclared_geometry_profile,
    detect_rendered_boundary_crossings,
    detect_undeclared_geometry,
    geometry_parse_coverage,
    partition_candidates_by_profile,
    rendered_curve_coverage,
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
    assert "source_hashes" not in payload


def test_payload_emits_source_hashes_when_tex_path_given(tmp_path: Path) -> None:
    from quality_manifest import file_sha256

    fixture_dir = tmp_path / "examples" / "demo"
    pdf_path = fixture_dir / "build" / "demo.pdf"
    pdf_path.parent.mkdir(parents=True)
    tex_path = fixture_dir / "demo.tex"
    tex_path.write_text(r"\draw (0,0) -- (1,1);", encoding="utf-8")

    payload = undeclared_geometry_payload(pdf_path, [], tex_path=tex_path)

    assert payload["source_hashes"] == {"examples/demo/demo.tex": file_sha256(tex_path)}


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
    # B1: the declared boundary must use the SAME key form the rest of the pipeline
    # uses (check_text_boundary_clash + real spec.yaml): x_pdf_cm / y_range_pdf_cm.
    tex = r"\draw[cGray] (4.62,1.0) -- (4.62,6.0);"
    spec = {
        "text_boundary_checks": [
            {
                "id": "de-rule",
                "kind": "vertical_line",
                "role": "column_rule",
                "x_pdf_cm": 4.62,
                "y_range_pdf_cm": [1.0, 6.0],
            }
        ]
    }

    assert detect_undeclared_geometry(tex, [], spec) == []


def test_declared_horizontal_rule_suppresses_candidate() -> None:
    # B1: y_pdf_cm / x_range_pdf_cm must be recognized (they were read as the
    # nonexistent pdf_cm_y / pdf_cm_x_range, so a declared rule was re-flagged).
    tex = r"\draw[cGray] (1.0,2.0) -- (6.0,2.0);"
    spec = {
        "text_boundary_checks": [
            {
                "id": "de-hrule",
                "kind": "horizontal_line",
                "role": "axis_rule",
                "y_pdf_cm": 2.0,
                "x_range_pdf_cm": [1.0, 6.0],
            }
        ]
    }

    assert detect_undeclared_geometry(tex, [], spec) == []


def test_literal_circle_parses_as_typed_geometry() -> None:
    tex = r"\fill[cRed] (2.0,3.0) circle (0.25);"

    geometry = _parse_tikz_geometry(tex)

    assert [item["kind"] for item in geometry] == ["circle"]
    assert geometry[0]["center_pt"] == [56.692913, 85.03937]
    assert geometry[0]["radius_pt"] == 7.086614
    assert geometry[0]["bbox_pt"] == [49.606299, 77.952756, 63.779527, 92.125984]
    assert geometry[0]["source_line"] == 1


def test_bezier_controls_parse_as_conservative_curve_hull() -> None:
    tex = r"\draw[walk] (1.0,1.0) .. controls (1.5,2.0) and (2.5,2.0) .. (3.0,1.0);"

    geometry = _parse_tikz_geometry(tex)

    assert [item["kind"] for item in geometry] == ["curve"]
    assert geometry[0]["clearance_mode"] == "conservative_hull"
    assert geometry[0]["bbox_pt"] == [28.346457, 28.346457, 85.03937, 56.692913]
    assert geometry[0]["control_hull_pt"] == [
        [28.346457, 28.346457],
        [42.519685, 56.692913],
        [70.866142, 56.692913],
        [85.03937, 28.346457],
    ]


def test_parse_coverage_reports_unknown_nonliteral_circle() -> None:
    tex = "\n".join(
        [
            r"\draw (0,0) -- (1,0);",
            r"\shade[opacity=0.2] (\cx,\cy) circle ({2.35*\rr});",
        ]
    )

    coverage = geometry_parse_coverage(tex)

    assert coverage["total_operations"] == 2
    assert coverage["parsed_operations"] == 1
    assert coverage["unknown_operations"] == 1
    assert coverage["parsed_geometry_counts"] == {"horizontal_line": 1}
    assert coverage["unknown_reasons"] == {"nonliteral_circle": 1}
    assert coverage["unknown_samples"][0]["source_line"] == 2
    assert coverage["unknown_samples"][0]["reason"] == "nonliteral_circle"


def test_parse_coverage_reports_specific_unknown_reasons() -> None:
    tex = "\n".join(
        [
            r"\draw plot[smooth] coordinates {(0,0)(1,1)};",
            r"\fill[white] (7.78, 7.52) ellipse (1.8mm and 0.4mm);",
            r"\draw[xfer] (1.48,3.18) to[out=-105,in=82] (1.55,2.52);",
        ]
    )

    coverage = geometry_parse_coverage(tex)

    assert coverage["unknown_operations"] == 3
    assert coverage["unknown_reasons"] == {
        "unsupported_ellipse": 1,
        "unsupported_plot": 1,
        "unsupported_to_curve": 1,
    }


def test_parse_coverage_reports_mixed_parsed_and_unknown_operation() -> None:
    tex = r"\draw (0,0) -- (1,0) plot[smooth] coordinates {(1,0)(2,1)};"

    coverage = geometry_parse_coverage(tex)

    assert coverage["total_operations"] == 1
    assert coverage["parsed_operations"] == 1
    assert coverage["fully_parsed_operations"] == 0
    assert coverage["partial_unknown_operations"] == 1
    assert coverage["unknown_operations"] == 0
    assert coverage["parsed_geometry_counts"] == {"horizontal_line": 1}
    assert coverage["unknown_reasons"] == {"unsupported_plot": 1}


def test_payload_includes_geometry_parse_coverage() -> None:
    tex = r"\fill (2,3) circle (0.25);"
    candidates = detect_undeclared_geometry(tex, [], {})
    payload = undeclared_geometry_payload(Path("fixture/build/fig.pdf"), candidates, tex_text=tex)

    assert payload["geometry_parse_coverage"]["total_operations"] == 1
    assert payload["geometry_parse_coverage"]["parsed_geometry_counts"] == {"circle": 1}
    assert payload["geometry_parse_coverage"]["non_auto_promotable_geometry"] == [
        "circle_envelope",
        "curve_conservative_hull",
    ]


def test_payload_persists_rendered_curve_coverage() -> None:
    tex = r"\fill (2,3) circle (0.25);"
    payload = undeclared_geometry_payload(
        Path("fixture/build/fig.pdf"),
        [],
        tex_text=tex,
        rendered_curves=[
            {
                "pts": [(10.0, 20.0), (14.0, 18.0), (18.0, 22.0)],
                "linewidth": 0.5,
            }
        ],
    )

    assert (
        payload["geometry_parse_coverage"]["rendered_curves"]["rendered_curve_count"] == 1
    )


def test_circle_and_curve_do_not_emit_undeclared_geometry_candidates() -> None:
    tex = "\n".join(
        [
            r"\fill[cRed] (2.0,3.0) circle (0.25);",
            r"\draw[walk] (1.0,1.0) .. controls (1.5,2.0) and (2.5,2.0) .. (3.0,1.0);",
        ]
    )

    assert detect_undeclared_geometry(tex, [], {}) == []


def test_rendered_curve_coverage_consumes_pdfplumber_curves() -> None:
    curves = [
        {
            "pts": [(10.0, 20.0), (14.0, 18.0), (18.0, 22.0)],
            "linewidth": 0.5,
            "stroking_color": (0.1, 0.2, 0.3),
        }
    ]

    coverage = rendered_curve_coverage(curves)

    assert coverage == {
        "rendered_curve_count": 1,
        "rendered_curve_envelopes": [
            {
                "bbox_pt": [10.0, 18.0, 18.0, 22.0],
                "clearance_mode": "rendered_curve_bbox",
                "linewidth_pt": 0.5,
            }
        ],
    }


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


def test_label_crossing_horizontal_rule_is_reported() -> None:
    tex = r"\draw[cGray!22, line width=0.30pt] (1.0,1.0) -- (3.0,1.0);"
    # Horizontal rule at y ~= 28.346 pt crosses the rendered glyph bbox.
    words = [_word("log t", 40.0, 26.0, 70.0, 34.0)]

    candidates = detect_undeclared_geometry(tex, words, {})

    assert [candidate["kind"] for candidate in candidates] == [
        "undeclared_horizontal_rule",
        "label_crosses_horizontal_rule",
    ]
    assert candidates[1]["nearest_text"] == "log t"
    assert candidates[1]["distance_pt"] == 0.0
    assert candidates[1]["recommended_action"] == "add_micro_defect"


def test_label_clear_of_horizontal_rule_is_not_reported_as_crossing() -> None:
    tex = r"\draw[cGray!22, line width=0.30pt] (1.0,1.0) -- (3.0,1.0);"
    words = [_word("log t", 40.0, 34.0, 70.0, 42.0)]

    candidates = detect_undeclared_geometry(tex, words, {})

    assert "label_crosses_horizontal_rule" not in [candidate["kind"] for candidate in candidates]


def test_source_label_crossing_preserves_source_coordinate_behavior() -> None:
    tex = r"\draw[cGray!22, line width=0.30pt] (1.0,1.0) -- (3.0,1.0);"
    words = [_word("log t", 40.0, 26.0, 70.0, 34.0)]

    candidates = detect_undeclared_geometry(
        tex,
        words,
        {},
        page_size_pt=(100.0, 100.0),
    )

    assert [candidate["kind"] for candidate in candidates] == [
        "undeclared_horizontal_rule",
        "label_crosses_horizontal_rule",
    ]
    assert candidates[1]["bbox_pt"] == [28.346457, 28.346457, 85.03937, 28.346457]


def test_source_near_miss_preserves_existing_coordinate_behavior() -> None:
    tex = r"\draw[cGray!70!black, line width=0.45pt] (1.0,1.0) -- (3.0,1.0);"
    # Source-discovered near-miss candidates keep the historical coordinate
    # behavior; exact rendered crossings are handled by PDF path coordinates.
    words = [_word("mobility", 40.0, 30.0, 70.0, 38.0)]

    candidates = detect_undeclared_geometry(
        tex,
        words,
        {},
        page_size_pt=(100.0, 100.0),
    )

    assert [candidate["kind"] for candidate in candidates] == [
        "undeclared_horizontal_rule",
        "label_endpoint_near_miss",
    ]
    assert candidates[1]["nearest_text"] == "mobility"
    assert 0 < candidates[1]["distance_pt"] < 4


def test_rendered_boundary_crossing_uses_pdf_path_coordinates() -> None:
    words = [_word("derive", 260.0, 280.0, 286.0, 292.0)]
    rendered_lines = [
        {
            "x0": 268.0,
            "x1": 268.0,
            "top": 250.0,
            "bottom": 325.0,
            "linewidth": 0.4,
            "stroking_color": (0.84, 0.84, 0.84),
        }
    ]

    candidates = detect_rendered_boundary_crossings(words, rendered_lines, [])

    assert [candidate["kind"] for candidate in candidates] == ["label_crosses_column_rule"]
    assert candidates[0]["nearest_text"] == "derive"
    assert candidates[0]["distance_pt"] == 0.0


def test_rendered_boundary_crossing_ignores_colored_plot_lines() -> None:
    words = [_word("shallow", 468.0, 69.0, 499.0, 77.0)]
    rendered_lines = [
        {
            "x0": 484.0,
            "x1": 484.0,
            "top": 45.0,
            "bottom": 128.0,
            "linewidth": 0.6,
            "stroking_color": (0.6, 0.3, 0.35),
        }
    ]

    assert detect_rendered_boundary_crossings(words, rendered_lines, []) == []


def test_label_crossing_ignores_non_frame_like_geometry() -> None:
    tex = "\n".join(
        [
            r"\draw[cGray!70!black, line width=0.45pt] (1.0,1.0) -- (3.0,1.0);",
            r"\fill[cGray!22] (1.0,1.0) rectangle (5.5,4.2);",
        ]
    )
    words = [_word("axis", 40.0, 26.0, 70.0, 34.0)]

    candidates = detect_undeclared_geometry(tex, words, {})

    assert not any(candidate["kind"].startswith("label_crosses") for candidate in candidates)


def test_label_crossing_semantic_arrow_is_reported_even_when_not_frame_like() -> None:
    tex = (
        r"\draw[-{Stealth[length=3pt,width=2pt]}, cRed!75!black, "
        r"line width=0.50pt] (2.0,1.0) -- (2.0,3.0);"
    )
    # Vertical semantic arrow at x ~= 56.693 pt crosses the rendered glyph bbox.
    words = [_word("shallow", 45.0, 40.0, 70.0, 48.0)]

    candidates = detect_undeclared_geometry(tex, words, {})

    assert [candidate["kind"] for candidate in candidates] == [
        "undeclared_column_rule",
        "label_crosses_semantic_path",
    ]
    assert candidates[1]["nearest_text"] == "shallow"
    assert candidates[1]["distance_pt"] == 0.0
    assert candidates[1]["recommended_action"] == "add_micro_defect"


def test_label_crossing_semantic_arrow_is_reported_when_source_crossings_disabled() -> None:
    tex = (
        r"\draw[-{Stealth[length=3pt,width=2pt]}, cRed!75!black, "
        r"line width=0.50pt] (2.0,1.0) -- (2.0,3.0);"
    )
    words = [_word("shallow", 45.0, 40.0, 70.0, 48.0)]

    candidates = detect_undeclared_geometry(tex, words, {}, source_crossings=False)

    assert [candidate["kind"] for candidate in candidates] == [
        "undeclared_column_rule",
        "label_crosses_semantic_path",
    ]


def test_label_crossing_semantic_arrow_ignores_single_character_ocr_fragments() -> None:
    tex = (
        r"\draw[-{Stealth[length=3pt,width=2pt]}, cGray!70!black, "
        r"line width=0.70pt] (2.0,1.0) -- (2.0,3.0);"
    )
    words = [_word("a", 55.0, 40.0, 58.0, 48.0)]

    candidates = detect_undeclared_geometry(tex, words, {}, source_crossings=False)

    assert [candidate["kind"] for candidate in candidates] == ["undeclared_column_rule"]


def test_label_crossing_rect_boundary_is_reported() -> None:
    tex = r"\draw[cGray!22, line width=0.30pt] (1.0,1.0) rectangle (5.5,4.2);"
    # Bottom side of the rectangle is at y ~= 28.346 pt and crosses the label.
    words = [_word("E_t", 40.0, 26.0, 58.0, 34.0)]

    candidates = detect_undeclared_geometry(tex, words, {})

    assert [candidate["kind"] for candidate in candidates] == [
        "undeclared_rect_boundary",
        "label_crosses_rect_boundary",
    ]
    assert candidates[1]["nearest_text"] == "E_t"
    assert candidates[1]["distance_pt"] == 0.0
    assert candidates[1]["recommended_action"] == "add_micro_defect"


def test_undeclared_geometry_profile_reads_schematic() -> None:
    assert _undeclared_geometry_profile({}) is None
    assert _undeclared_geometry_profile({"undeclared_geometry_profile": None}) is None
    assert _undeclared_geometry_profile({"undeclared_geometry_profile": "schematic"}) == "schematic"


def test_undeclared_geometry_profile_rejects_unknown_value() -> None:
    with pytest.raises(UndeclaredGeometryError):
        _undeclared_geometry_profile({"undeclared_geometry_profile": "fixed_grid"})


def test_schematic_profile_downranks_conceptual_geometry() -> None:
    # Mix conceptual geometry (undeclared rect + column rule) with an actual
    # defect (a frame rule that crosses a label).
    tex = "\n".join(
        [
            r"\draw[cGray] (1.0,2.0) rectangle (3.0,2.5);",
            r"\draw[cGray] (4.62,1.0) -- (4.62,6.0);",
            r"\draw[cGray!22, line width=0.30pt] (1.0,1.0) -- (3.0,1.0);",
        ]
    )
    # Word sits on the y~=28.346 pt rule so the third draw crosses it.
    words = [_word("log t", 40.0, 26.0, 70.0, 34.0)]

    candidates = detect_undeclared_geometry(tex, words, {})
    kinds = {candidate["kind"] for candidate in candidates}
    assert "undeclared_rect_boundary" in kinds
    assert "undeclared_column_rule" in kinds
    assert "label_crosses_horizontal_rule" in kinds

    downranked, actionable = partition_candidates_by_profile(candidates, "schematic")

    downranked_kinds = {candidate["kind"] for candidate in downranked}
    actionable_kinds = {candidate["kind"] for candidate in actionable}
    assert downranked_kinds == {
        "undeclared_rect_boundary",
        "undeclared_column_rule",
        "undeclared_horizontal_rule",
    }
    assert actionable_kinds == {"label_crosses_horizontal_rule"}
    # Nothing is dropped: partition is a complete split of the input.
    assert len(downranked) + len(actionable) == len(candidates)


def test_default_profile_leaves_all_candidates_actionable() -> None:
    tex = "\n".join(
        [
            r"\draw[cGray] (1.0,2.0) rectangle (3.0,2.5);",
            r"\draw[cGray] (4.62,1.0) -- (4.62,6.0);",
        ]
    )
    candidates = detect_undeclared_geometry(tex, [], {})

    downranked, actionable = partition_candidates_by_profile(candidates, None)

    assert downranked == []
    assert actionable == candidates


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


def test_schematic_profile_excludes_downranked_from_accounted_candidates() -> None:
    # main() writes the actionable partition as the accounted `candidates` under the
    # schematic profile, so downranked conceptual geometry is NOT subject to the
    # critique undeclared-geometry accounting gate; real defects (label crossings) are.
    candidates = [
        {"kind": "undeclared_column_rule", "id": "UG001"},
        {"kind": "label_crosses_horizontal_rule", "id": "UG002"},
        {"kind": "undeclared_rect_boundary", "id": "UG003"},
    ]

    downranked, actionable = partition_candidates_by_profile(candidates, "schematic")
    payload = undeclared_geometry_payload(Path("fixture/build/fig.pdf"), actionable)

    accounted_kinds = {candidate["kind"] for candidate in payload["candidates"]}
    assert accounted_kinds == {"label_crosses_horizontal_rule"}
    assert {candidate["kind"] for candidate in downranked} == {
        "undeclared_column_rule",
        "undeclared_rect_boundary",
    }
