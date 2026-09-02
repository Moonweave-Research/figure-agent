from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import vector_clearance  # noqa: E402

DECLARING_FIXTURES = (
    "fig2_charge_transport_mechanism",
    "fig5_cantilever_actuation_artifact_v2",
    "fig1_overview_v5f_art_direction_001_vault",
)


def test_parse_absent_vector_clearance_checks_is_empty() -> None:
    assert vector_clearance.parse_vector_clearance_checks({}) == []


def test_parse_rejects_malformed_vector_clearance_schema() -> None:
    with pytest.raises(vector_clearance.VectorClearanceError, match="must be a list"):
        vector_clearance.parse_vector_clearance_checks({"vector_clearance_checks": {}})

    with pytest.raises(vector_clearance.VectorClearanceError, match="exactly one relation"):
        vector_clearance.parse_vector_clearance_checks(
            {
                "vector_clearance_checks": [
                    {
                        "id": "bad",
                        "element_a": {"source_line": 1},
                        "element_b": {"source_line": 2},
                    }
                ]
            }
        )


def test_source_line_selector_zero_match_is_loud_issue() -> None:
    tex = r"\draw (0,0) -- (1,0);"
    checks = vector_clearance.parse_vector_clearance_checks(
        {
            "vector_clearance_checks": [
                {
                    "id": "line-gap",
                    "element_a": {"source_line": 99},
                    "element_b": {"source_line": 1},
                    "must_not_cross": True,
                }
            ]
        }
    )

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert issues == [
        {
            "id": "line-gap",
            "status": "selector_missing",
            "selector": "element_a",
            "message": "vector_clearance 'line-gap' element_a selector matched 0 elements",
        }
    ]


def test_stable_selector_recovers_when_source_line_drifts() -> None:
    tex = "\n".join(
        [
            "% inserted comment shifts declared source lines",
            r"\draw[a] (0,0) -- (2,0);",
            r"\draw[b] (1,-1) -- (1,1);",
        ]
    )
    checks = vector_clearance.parse_vector_clearance_checks(
        {
            "vector_clearance_checks": [
                {
                    "id": "drifted-source-line",
                    "element_a": {"source_line": 1, "matched_text": "[a]", "kind": "line"},
                    "element_b": {"source_line": 2, "matched_text": "[b]", "kind": "line"},
                    "must_not_cross": True,
                }
            ]
        }
    )

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert issues[0]["id"] == "drifted-source-line"
    assert issues[0]["status"] == "violated"
    assert issues[0]["selector_line_drifts"] == [
        {"selector": "element_a", "declared_source_line": 1, "actual_source_line": 2},
        {"selector": "element_b", "declared_source_line": 2, "actual_source_line": 3},
    ]


def test_stable_selector_drift_fallback_still_fails_loud_on_multi_match() -> None:
    tex = "\n".join(
        [
            "% inserted comment shifts declared source lines",
            r"\draw[probe] (0,0) -- (1,0);",
            r"\draw[probe] (0,1) -- (1,1);",
            r"\draw[target] (0,2) -- (1,2);",
        ]
    )
    checks = vector_clearance.parse_vector_clearance_checks(
        {
            "vector_clearance_checks": [
                {
                    "id": "drifted-ambiguous",
                    "element_a": {
                        "source_line": 1,
                        "matched_text": "probe",
                        "kind": "line",
                    },
                    "element_b": {"matched_text": "target", "kind": "line"},
                    "must_not_cross": True,
                }
            ]
        }
    )

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert issues[0]["status"] == "selector_ambiguous"
    assert issues[0]["selector"] == "element_a"
    assert issues[0]["match_count"] == 2


def test_matched_text_selector_multi_match_is_loud_issue() -> None:
    tex = "\n".join(
        [
            r"\draw[probe] (0,0) -- (1,0);",
            r"\draw[probe] (0,1) -- (1,1);",
            r"\draw[target] (0,2) -- (1,2);",
        ]
    )
    checks = vector_clearance.parse_vector_clearance_checks(
        {
            "vector_clearance_checks": [
                {
                    "id": "ambiguous",
                    "element_a": {"matched_text": "probe"},
                    "element_b": {"matched_text": "target"},
                    "must_not_cross": True,
                }
            ]
        }
    )

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert issues[0]["status"] == "selector_ambiguous"
    assert issues[0]["selector"] == "element_a"
    assert issues[0]["match_count"] == 2


def test_declared_must_not_cross_line_violation_reports_delta() -> None:
    tex = "\n".join(
        [
            r"\draw[a] (0,0) -- (2,0);",
            r"\draw[b] (1,-1) -- (1,1);",
        ]
    )
    checks = vector_clearance.parse_vector_clearance_checks(
        {
            "vector_clearance_checks": [
                {
                    "id": "crossing-lines",
                    "element_a": {"source_line": 1},
                    "element_b": {"source_line": 2},
                    "must_not_cross": True,
                }
            ]
        }
    )

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert issues[0]["id"] == "crossing-lines"
    assert issues[0]["status"] == "violated"
    assert issues[0]["relation"] == "must_not_cross"
    assert issues[0]["measured_clearance_cm"] == pytest.approx(0.0)
    assert issues[0]["element_a_source_line"] == 1
    assert issues[0]["element_b_source_line"] == 2
    assert issues[0]["element_a_bbox_cm"] == [0.0, 0.0, 2.0, 0.0]
    assert issues[0]["element_b_bbox_cm"] == [1.0, -1.0, 1.0, 1.0]
    assert issues[0]["promotion_tier"] == "auto"
    assert issues[0]["non_auto_promotable"] is False


def test_declared_min_clearance_line_violation_reports_margin() -> None:
    tex = "\n".join(
        [
            r"\draw[a] (0,0) -- (1,0);",
            r"\draw[b] (0,0.05) -- (1,0.05);",
        ]
    )
    checks = vector_clearance.parse_vector_clearance_checks(
        {
            "vector_clearance_checks": [
                {
                    "id": "parallel-gap",
                    "element_a": {"matched_text": "[a]"},
                    "element_b": {"matched_text": "[b]"},
                    "min_clearance_cm": 0.1,
                }
            ]
        }
    )

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert issues[0]["status"] == "violated"
    assert issues[0]["relation"] == "min_clearance_cm"
    assert issues[0]["measured_clearance_cm"] == pytest.approx(0.05)
    assert issues[0]["required_clearance_cm"] == pytest.approx(0.1)
    assert issues[0]["clearance_delta_cm"] == pytest.approx(-0.05)


def test_declared_must_touch_reports_violation_when_separated() -> None:
    tex = "\n".join(
        [
            r"\draw[a] (0,0) -- (1,0);",
            r"\draw[b] (0,0.2) -- (1,0.2);",
        ]
    )
    checks = vector_clearance.parse_vector_clearance_checks(
        {
            "vector_clearance_checks": [
                {
                    "id": "must-touch",
                    "element_a": {"source_line": 1},
                    "element_b": {"source_line": 2},
                    "must_touch": True,
                }
            ]
        }
    )

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert issues[0]["status"] == "violated"
    assert issues[0]["relation"] == "must_touch"
    assert issues[0]["measured_clearance_cm"] == pytest.approx(0.2)


def test_circle_and_curve_envelopes_are_non_auto_promotable() -> None:
    tex = "\n".join(
        [
            r"\draw[line] (0,0) -- (2,0);",
            r"\fill[mark] (1,0) circle (0.08);",
            r"\draw[curve] (0,-0.1) .. controls (0.5,0.3) and (1.5,0.3) .. (2,-0.1);",
        ]
    )
    checks = vector_clearance.parse_vector_clearance_checks(
        {
            "vector_clearance_checks": [
                {
                    "id": "line-through-marker",
                    "element_a": {"matched_text": "[line]"},
                    "element_b": {"matched_text": "[mark]"},
                    "must_not_cross": True,
                },
                {
                    "id": "line-through-curve-envelope",
                    "element_a": {"matched_text": "[line]"},
                    "element_b": {"matched_text": "[curve]"},
                    "must_not_cross": True,
                },
            ]
        }
    )

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert [issue["id"] for issue in issues] == [
        "line-through-marker",
        "line-through-curve-envelope",
    ]
    assert all(issue["non_auto_promotable"] is True for issue in issues)
    assert all(issue["promotion_tier"] == "review_queue" for issue in issues)


def test_small_filled_circle_extracts_as_marker_and_matches_kind_selector() -> None:
    tex = "\n".join(
        [
            r"\draw[line] (0,0) -- (2,0);",
            r"\fill[mark] (1,0) circle (0.08);",
        ]
    )
    elements = vector_clearance.extract_vector_elements(tex)
    marker = next(element for element in elements if element["tex_anchor"].startswith(r"\fill"))
    assert marker["kind"] == "marker"

    checks = vector_clearance.parse_vector_clearance_checks(
        {
            "vector_clearance_checks": [
                {
                    "id": "line-through-marker",
                    "element_a": {"matched_text": "[line]", "kind": "line"},
                    "element_b": {"matched_text": "[mark]", "kind": "marker"},
                    "must_not_cross": True,
                }
            ]
        }
    )

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert issues[0]["element_b_kind"] == "marker"
    assert issues[0]["non_auto_promotable"] is True


def test_v5f_panel_e_peak_crowding_declaration_is_resolved() -> None:
    fixture = ROOT / "examples" / "fig1_overview_v5f_art_direction_001_vault"
    tex = (fixture / "fig1_overview_v5f_art_direction_001_vault.tex").read_text(encoding="utf-8")
    checks = vector_clearance.parse_vector_clearance_checks(
        vector_clearance._load_spec(fixture / "spec.yaml")
    )

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert [item for item in issues if item["id"] == "panelE-deep-peak-caliper-min-clearance"] == []


def test_foreach_ball_shaded_markers_are_extracted_for_declared_checks() -> None:
    tex = "\n".join(
        [
            r"\draw[debye] (1.80, 2.30) .. controls (2.05, 2.28) and (2.12, 0.80) .. (2.22, 0.55);",
            r"\foreach \mx/\my in {1.20/2.00, 2.00/1.56} {",
            r"  \shade[ball color=cRed!75!black] (\mx, \my) circle (0.045);",
            r"  \draw[cRed!95!black, line width=0.18pt] (\mx, \my) circle (0.045);",
            r"}",
        ]
    )
    elements = vector_clearance.extract_vector_elements(tex)

    marker = next(
        element
        for element in elements
        if element["kind"] == "marker" and element["center_cm"] == [2.0, 1.56]
    )
    assert marker["source_line"] == 3

    checks = vector_clearance.parse_vector_clearance_checks(
        {
            "vector_clearance_checks": [
                {
                    "id": "debye-through-red-marker",
                    "element_a": {"matched_text": "[debye]", "kind": "curve"},
                    "element_b": {
                        "bbox_cm": marker["bbox_cm"],
                        "kind": "marker",
                    },
                    "must_not_cross": True,
                }
            ]
        }
    )

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert issues[0]["id"] == "debye-through-red-marker"
    assert issues[0]["status"] == "violated"
    assert issues[0]["promotion_tier"] == "review_queue"


def test_bbox_coordinate_selector_matches_single_declared_element() -> None:
    tex = "\n".join(
        [
            r"\draw[a] (0,0) -- (2,0);",
            r"\draw[b] (1,-1) -- (1,1);",
        ]
    )
    checks = vector_clearance.parse_vector_clearance_checks(
        {
            "vector_clearance_checks": [
                {
                    "id": "bbox-selected-crossing",
                    "element_a": {"bbox_cm": [0, 0, 2, 0], "kind": "line"},
                    "element_b": {"bbox_cm": [1, -1, 1, 1], "kind": "line"},
                    "must_not_cross": True,
                }
            ]
        }
    )

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert issues[0]["id"] == "bbox-selected-crossing"
    assert issues[0]["status"] == "violated"


def test_no_declarations_means_no_universal_detection() -> None:
    tex = "\n".join(
        [
            r"\draw (0,0) -- (2,0);",
            r"\fill (1,0) circle (0.08);",
        ]
    )

    assert vector_clearance.check_vector_clearance(tex, []) == []


def test_payload_structure_records_source_hashes(tmp_path: Path) -> None:
    fixture = tmp_path / "fig_demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    tex_path = fixture / "fig_demo.tex"
    tex_path.write_text(r"\draw (0,0) -- (1,0);", encoding="utf-8")
    pdf_path = build / "fig_demo.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")

    payload = vector_clearance.vector_clearance_payload(pdf_path, [], 2, tex_path=tex_path)

    assert payload["schema"] == "figure-agent.vector-clearance.v1"
    assert payload["checked"] == 2
    assert payload["total"] == 0
    assert payload["source_hashes"]["examples/fig_demo/fig_demo.tex"].startswith("sha256:")


def test_polyline_chain_is_one_element_with_every_point() -> None:
    text = r"\draw[thick] (0,0) -- (0,1.2) -- (2.5,1.2) -- (2.5,0);"

    elements = vector_clearance.extract_vector_elements(text)

    assert len(elements) == 1
    assert elements[0]["kind"] == "line"
    assert elements[0]["points_cm"] == [(0.0, 0.0), (0.0, 1.2), (2.5, 1.2), (2.5, 0.0)]


def test_polyline_middle_segment_violation_is_detected() -> None:
    """Pairwise segment parsing dropped the middle segment of a chain, so an
    obstacle under it was invisible to every declared clearance check."""
    tex = (
        r"\draw[thick] (0,0) -- (0,1.2) -- (2.5,1.2) -- (2.5,0);"
        "\n"
        r"\draw (1.0,1.0) rectangle (1.5,1.1);"
    )
    checks = [
        {
            "id": "VC-mid",
            "relation": "min_clearance_cm",
            "min_clearance_cm": 0.3,
            "element_a": {"source_line": 2, "kind": "rect"},
            "element_b": {"source_line": 1, "kind": "line"},
        }
    ]

    issues = vector_clearance.check_vector_clearance(tex, checks)

    assert [issue["id"] for issue in issues if issue.get("status") == "violated"] == ["VC-mid"]


def test_polyline_circle_clearance_uses_nearest_segment() -> None:
    tex = (
        r"\draw (0,0) -- (0,1) -- (3,1) -- (3,0);"
        "\n"
        r"\draw (1.5,0.5) circle (0.1);"
    )
    checks = [
        {
            "id": "VC-circ",
            "relation": "min_clearance_cm",
            "min_clearance_cm": 0.5,
            "element_a": {"source_line": 2, "kind": "circle"},
            "element_b": {"source_line": 1, "kind": "line"},
        }
    ]

    issues = vector_clearance.check_vector_clearance(tex, checks)

    violated = [issue for issue in issues if issue.get("status") == "violated"]
    assert [issue["id"] for issue in violated] == ["VC-circ"]
    # nearest segment is the middle one: 1.0 - 0.5 - 0.1 = 0.4 < 0.5
    assert violated[0]["measured_clearance_cm"] == pytest.approx(0.4, abs=1e-6)


DECLARED_CHECK_TEX = r"""\documentclass[border=2pt]{standalone}
\usepackage{polymer-paper-preamble}
\begin{document}
\begin{tikzpicture}
\draw[line width=0.5pt] (0,0)--(2,0);
\draw[line width=0.5pt] (0,0.4)--(2,0.4);
\end{tikzpicture}
\end{document}
"""

DECLARED_CHECK_SPEC = {
    "name": "vector_clearance_declared_demo",
    "style_profile": "polymer-default",
    "panels": [],
    "vector_clearance_checks": [
        {
            "id": "rails-stay-apart",
            "element_a": {
                "source_line": 5,
                "matched_text": "(0,0)--(2,0)",
                "kind": "line",
            },
            "element_b": {
                "source_line": 6,
                "matched_text": "(0,0.4)--(2,0.4)",
                "kind": "line",
            },
            "min_clearance_cm": 0.2,
        }
    ],
}


def _compile_declared_demo(workspace: Path, spec: dict) -> dict:
    fixture = workspace / "examples" / "vector_clearance_declared_demo"
    fixture.mkdir(parents=True, exist_ok=True)
    (fixture / "spec.yaml").write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    tex_path = fixture / "vector_clearance_declared_demo.tex"
    tex_path.write_text(DECLARED_CHECK_TEX, encoding="utf-8")

    result = subprocess.run(
        ["bash", "scripts/compile.sh", str(tex_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "FIGURE_AGENT_WORKSPACE": str(workspace)},
    )
    report = fixture / "build" / "vector_clearance.json"
    assert report.is_file(), result.stdout + result.stderr
    return json.loads(report.read_text(encoding="utf-8"))


@pytest.mark.render
def test_compile_measures_a_declared_clearance_check(tmp_path: Path) -> None:
    """A declared check makes the detector measure something; without the
    declaration the same compile reports `checked: 0`, which is the state every
    canonical fixture was in before its spec declared any pair."""
    declared = _compile_declared_demo(tmp_path / "declared", DECLARED_CHECK_SPEC)

    assert declared["checked"] == 1
    assert declared["issues"] == []

    undeclared_spec = {
        key: value for key, value in DECLARED_CHECK_SPEC.items() if key != "vector_clearance_checks"
    }
    undeclared = _compile_declared_demo(tmp_path / "undeclared", undeclared_spec)

    assert undeclared["checked"] == 0


@pytest.mark.parametrize("fixture_name", DECLARING_FIXTURES)
def test_declared_fixture_checks_parse_and_bind(fixture_name: str) -> None:
    """Every declaring fixture must parse against the schema, resolve each
    selector to exactly one live element, and hold its declared relations."""
    fixture = ROOT / "examples" / fixture_name
    spec = yaml.safe_load((fixture / "spec.yaml").read_text(encoding="utf-8"))
    tex = (fixture / f"{fixture_name}.tex").read_text(encoding="utf-8")

    checks = vector_clearance.parse_vector_clearance_checks(spec)

    assert checks, f"{fixture_name} declares no vector_clearance_checks"
    assert vector_clearance.check_vector_clearance(tex, checks) == []
