from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "checks"))

import check_tex_assertions as cta  # noqa: E402

FORCE_AWAY = "\\draw[forceArr] (3.50,4.85) -- (2.55,4.85);"  # points -x (repulsion)
FORCE_TOWARD = "\\draw[forceArr] (4.28,4.85) -- (5.35,4.85);"  # points +x (attraction)


def test_find_styled_draws_returns_coords():
    assert cta.find_styled_draws(FORCE_AWAY, "forceArr") == [(3.50, 4.85, 2.55, 4.85)]


def test_find_styled_draws_matches_style_among_other_options():
    line = "\\draw[line width=1.3pt, forceArr, ->] (1.0,2.0) -- (3.0,2.0);"
    assert cta.find_styled_draws(line, "forceArr") == [(1.0, 2.0, 3.0, 2.0)]


def test_find_styled_draws_empty_when_style_absent():
    assert cta.find_styled_draws("\\draw[defArr] (0,0) -- (1,1);", "forceArr") == []


def test_find_styled_draws_does_not_match_a_different_style_substring():
    # "forceArr" must be word-bounded — "forceArrow" should not match "forceArr".
    assert cta.find_styled_draws("\\draw[forceArrow] (0,0) -- (1,1);", "forceArr") == []


def test_find_styled_draws_returns_all_matches():
    tex = FORCE_AWAY + "\n" + FORCE_TOWARD
    assert len(cta.find_styled_draws(tex, "forceArr")) == 2


def test_check_direction_pass_when_decreasing_x_holds():
    assert cta.check_direction((3.50, 4.85, 2.55, 4.85), axis="x", direction="decreasing") == "pass"


def test_check_direction_violated_when_decreasing_x_is_actually_increasing():
    assert (
        cta.check_direction((4.28, 4.85, 5.35, 4.85), axis="x", direction="decreasing")
        == "violated"
    )


def test_check_direction_pass_for_increasing():
    assert cta.check_direction((1.0, 0.0, 3.0, 0.0), axis="x", direction="increasing") == "pass"


def test_check_direction_indeterminate_within_tolerance():
    assert (
        cta.check_direction((3.50, 4.85, 3.50, 5.40), axis="x", direction="decreasing")
        == "indeterminate"
    )


def test_check_direction_uses_the_y_axis():
    # y2 < y1 => decreasing on y.
    assert cta.check_direction((0.0, 4.0, 0.0, 1.0), axis="y", direction="decreasing") == "pass"


import pytest  # noqa: E402

ASSERTION = {
    "id": "force-repels",
    "anchor_style": "forceArr",
    "axis": "x",
    "direction": "decreasing",
}


def test_parse_tex_assertions_returns_validated_list():
    parsed = cta.parse_tex_assertions({"tex_assertions": [ASSERTION]})
    assert parsed == [ASSERTION]


def test_parse_tex_assertions_empty_when_absent():
    assert cta.parse_tex_assertions({"name": "x"}) == []


def test_parse_tex_assertions_rejects_missing_field():
    with pytest.raises(cta.TexAssertionError):
        cta.parse_tex_assertions({"tex_assertions": [{"id": "a", "anchor_style": "forceArr"}]})


def test_parse_tex_assertions_rejects_bad_axis():
    bad = {**ASSERTION, "axis": "z"}
    with pytest.raises(cta.TexAssertionError):
        cta.parse_tex_assertions({"tex_assertions": [bad]})


def test_check_passes_a_correct_repulsion_figure():
    issues = cta.check_tex_assertions(FORCE_AWAY, [ASSERTION])
    assert issues == []


def test_check_flags_a_reversed_attraction_figure():
    issues = cta.check_tex_assertions(FORCE_TOWARD, [ASSERTION])
    assert len(issues) == 1
    assert issues[0]["id"] == "force-repels"
    assert issues[0]["status"] == "violated"


def test_check_reports_anchor_missing():
    issues = cta.check_tex_assertions("\\draw[defArr] (0,0) -- (1,1);", [ASSERTION])
    assert issues[0]["status"] == "anchor_missing"


def test_check_reports_anchor_ambiguous_when_style_matches_twice():
    tex = FORCE_AWAY + "\n" + FORCE_TOWARD
    issues = cta.check_tex_assertions(tex, [ASSERTION])
    assert issues[0]["status"] == "anchor_ambiguous"


def test_payload_has_stable_shape():
    payload = cta.tex_assertions_payload(
        Path("examples/demo/build/demo.tex"),
        cta.check_tex_assertions(FORCE_TOWARD, [ASSERTION]),
        assertion_count=1,
    )
    assert payload["schema"] == "figure-agent.tex-assertions.v1"
    assert payload["checked"] == 1
    assert payload["total"] == 1


P3 = (11.05, 3.55, 11.62, 3.55)  # forceArr points +x
P4 = (14.20, 3.55, 13.63, 3.55)  # forceArr points -x


def test_select_draw_near_picks_the_closest_start():
    assert cta.select_draw([P3, P4], near=(11.05, 3.55)) == ("ok", P3)
    assert cta.select_draw([P3, P4], near=(14.20, 3.55)) == ("ok", P4)


def test_select_draw_single_without_near_is_ok():
    assert cta.select_draw([P3], near=None) == ("ok", P3)


def test_select_draw_multiple_without_near_is_ambiguous():
    assert cta.select_draw([P3, P4], near=None) == ("ambiguous", None)


def test_select_draw_near_matching_none_is_missing():
    assert cta.select_draw([P3, P4], near=(50.0, 50.0)) == ("missing", None)


def test_select_draw_empty_is_missing():
    assert cta.select_draw([], near=None) == ("missing", None)


def test_parse_accepts_near():
    parsed = cta.parse_tex_assertions({"tex_assertions": [{**ASSERTION, "near": [1.0, 2.0]}]})
    assert parsed[0]["near"] == [1.0, 2.0]


def test_parse_rejects_malformed_near():
    with pytest.raises(cta.TexAssertionError):
        cta.parse_tex_assertions({"tex_assertions": [{**ASSERTION, "near": [1.0]}]})


def test_check_with_near_resolves_two_same_style_draws():
    # fig3_floating_clip's polarity-dependent P3(+x)/P4(-x) forceArrs share a style.
    tex = (
        "\\draw[forceArr] (11.05,3.55) -- (11.62,3.55);\n"
        "\\draw[forceArr] (14.20,3.55) -- (13.63,3.55);\n"
    )
    p3 = {
        "id": "p3",
        "anchor_style": "forceArr",
        "axis": "x",
        "direction": "increasing",
        "near": [11.05, 3.55],
    }
    p4 = {
        "id": "p4",
        "anchor_style": "forceArr",
        "axis": "x",
        "direction": "decreasing",
        "near": [14.20, 3.55],
    }
    assert cta.check_tex_assertions(tex, [p3, p4]) == []


def test_find_all_draws_matches_inline_styled_draw():
    tex = "\\draw[-{Stealth}, cRed!80!black, line width=0.7pt] (11.55,1.3) -- (10.85,1.3);"
    assert cta.find_all_draws(tex) == [(11.55, 1.3, 10.85, 1.3)]


def test_find_all_draws_matches_unstyled_draw():
    assert cta.find_all_draws("\\draw (0,0) -- (1,2);") == [(0.0, 0.0, 1.0, 2.0)]


def test_find_all_draws_handles_nested_option_brackets():
    # fig1's Coulomb arrow has an inline arrow-tip spec with NESTED brackets.
    tex = "\\draw[-{Stealth[length=6pt,width=4.5pt]}, cRed!80!black, line width=0.7pt] (11.55, 1.3) -- (10.85, 1.3);"
    assert cta.find_all_draws(tex) == [(11.55, 1.3, 10.85, 1.3)]


def test_find_all_draws_returns_multiple():
    assert len(cta.find_all_draws("\\draw[a] (0,0)--(1,0);\n\\draw[b] (5,5)--(6,5);")) == 2


def test_find_all_draws_ignores_bezier_curves():
    assert cta.find_all_draws("\\draw[beam] (0,0) .. controls (1,1) .. (2,2);") == []


def test_parse_accepts_near_only_without_anchor_style():
    parsed = cta.parse_tex_assertions(
        {
            "tex_assertions": [
                {"id": "x", "near": [11.55, 1.3], "axis": "x", "direction": "decreasing"}
            ]
        }
    )
    assert "anchor_style" not in parsed[0]
    assert parsed[0]["near"] == [11.55, 1.3]


def test_parse_rejects_neither_anchor_style_nor_near():
    with pytest.raises(cta.TexAssertionError):
        cta.parse_tex_assertions(
            {"tex_assertions": [{"id": "x", "axis": "x", "direction": "decreasing"}]}
        )


def test_check_near_only_resolves_inline_styled_draw():
    tex = (
        "\\draw[axisArr] (0,0) -- (5,0);\n"
        "\\draw[-{Stealth}, cRed!80!black] (11.55,1.3) -- (10.85,1.3);\n"
    )
    a = {"id": "coulomb-left", "near": [11.55, 1.3], "axis": "x", "direction": "decreasing"}
    assert cta.check_tex_assertions(tex, [a]) == []


def test_read_blocking_issues_filters_to_blocking_statuses(tmp_path):
    p = tmp_path / "tex_assertions.json"
    p.write_text(
        json.dumps(
            {
                "issues": [
                    {"id": "a", "status": "violated"},
                    {"id": "b", "status": "indeterminate"},
                    {"id": "c", "status": "anchor_missing"},
                    {"id": "d", "status": "anchor_ambiguous"},
                ]
            }
        ),
        encoding="utf-8",
    )
    assert {i["id"] for i in cta.read_blocking_issues(p)} == {"a", "c", "d"}


def test_read_blocking_issues_empty_when_no_file(tmp_path):
    assert cta.read_blocking_issues(tmp_path / "nope.json") == []


def test_read_blocking_issues_empty_when_all_pass(tmp_path):
    p = tmp_path / "tex_assertions.json"
    p.write_text(json.dumps({"issues": []}), encoding="utf-8")
    assert cta.read_blocking_issues(p) == []


def test_cli_strict_flags_violation_and_writes_json(tmp_path):
    import json
    import subprocess

    fixture = tmp_path / "demo"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text(
        "name: demo\n"
        "tex_assertions:\n"
        "  - id: force-repels\n"
        "    anchor_style: forceArr\n"
        "    axis: x\n"
        "    direction: decreasing\n",
        encoding="utf-8",
    )
    (fixture / "demo.tex").write_text(FORCE_TOWARD + "\n", encoding="utf-8")  # attraction = wrong
    script = Path(__file__).resolve().parents[1] / "scripts" / "checks" / "check_tex_assertions.py"
    jout = fixture / "tex_assertions.json"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(fixture / "demo.tex"),
            "--strict",
            "--json-output",
            str(jout),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "violated" in result.stdout
    data = json.loads(jout.read_text(encoding="utf-8"))
    assert data["schema"] == "figure-agent.tex-assertions.v1"
    assert data["total"] == 1
