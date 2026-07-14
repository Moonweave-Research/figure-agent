from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

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


def test_find_styled_draws_requires_an_exact_tikz_style_token():
    assert cta.find_styled_draws("\\draw[xfer-helper] (0,0) -- (1,1);", "xfer") == []


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


def test_parse_tex_assertions_rejects_non_positive_minimum_matches():
    with pytest.raises(cta.TexAssertionError, match="minimum_matches"):
        cta.parse_tex_assertions({"tex_assertions": [{**ASSERTION, "minimum_matches": 0}]})


def test_parse_tex_assertions_scopes_a_contract_to_its_declared_source_name():
    spec = {"tex_assertions": [{**ASSERTION, "source_name": "current.tex"}]}

    assert cta.parse_tex_assertions(spec, source_name="current.tex") == [
        {**ASSERTION, "source_name": "current.tex"}
    ]
    assert cta.parse_tex_assertions(spec, source_name="historical.tex") == []


def test_parse_tex_assertions_rejects_invalid_scoped_contract_for_other_source():
    spec = {"tex_assertions": [{**ASSERTION, "source_name": "current.tex", "minimum_matches": 0}]}

    with pytest.raises(cta.TexAssertionError, match="minimum_matches"):
        cta.parse_tex_assertions(spec, source_name="historical.tex")


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


def test_check_passes_repeated_curved_capture_arrows_by_semantic_style():
    tex = "\n".join(
        [
            r"\draw[capture] (1.0,3.0) to[out=-100,in=80] (1.1,2.0);",
            r"\draw[capture] (2.0,3.0) to[out=-100,in=80] (2.1,2.0);",
        ]
    )
    assertion = {
        "id": "repeated-capture",
        "anchor_style": "capture",
        "axis": "y",
        "direction": "decreasing",
        "minimum_matches": 2,
    }

    assert cta.check_tex_assertions(tex, [assertion]) == []


def test_check_ignores_commented_out_curved_paths_for_minimum_matches():
    tex = """
    % \\draw[capture] (1,3) to[out=-90,in=90] (1,2);
    % \\draw[capture] (2,3) to[out=-90,in=90] (2,2);
    """
    assertion = {
        "id": "two-captures",
        "anchor_style": "capture",
        "axis": "y",
        "direction": "decreasing",
        "minimum_matches": 2,
    }

    issues = cta.check_tex_assertions(tex, [assertion])

    assert issues[0]["id"] == "two-captures"
    assert issues[0]["status"] == "insufficient_matches"


def test_check_rejects_insufficient_repeated_curved_semantic_arrows():
    tex = r"\draw[capture] (1.0,3.0) to[out=-100,in=80] (1.1,2.0);"
    assertion = {
        "id": "repeated-capture",
        "anchor_style": "capture",
        "axis": "y",
        "direction": "decreasing",
        "minimum_matches": 2,
    }

    issues = cta.check_tex_assertions(tex, [assertion])

    assert issues[0]["status"] == "insufficient_matches"
    assert issues[0]["id"] == "repeated-capture"


def test_check_rejects_reversed_curved_semantic_arrow_in_a_repeated_role():
    tex = "\n".join(
        [
            r"\draw[capture] (1.0,3.0) to[out=-100,in=80] (1.1,2.0);",
            r"\draw[capture] (2.0,2.0) to[out=80,in=-100] (2.1,3.0);",
        ]
    )
    assertion = {
        "id": "repeated-capture",
        "anchor_style": "capture",
        "axis": "y",
        "direction": "decreasing",
        "minimum_matches": 2,
    }

    issues = cta.check_tex_assertions(tex, [assertion])

    assert issues[0]["status"] == "insufficient_matches"


def test_fig3_carrier_sequence_declares_and_satisfies_repeated_capture_release_contract():
    plugin_root = Path(__file__).resolve().parents[1]
    fixture = plugin_root / "examples" / "fig3_resistance_mechanism"
    assertions = cta.parse_tex_assertions(
        yaml.safe_load((fixture / "spec.yaml").read_text(encoding="utf-8")),
        source_name="fig3_resistance_mechanism.tex",
    )

    assert {assertion["id"] for assertion in assertions} >= {
        "carrier-sequence-repeated-capture",
        "carrier-sequence-repeated-release",
    }
    assert (
        cta.check_tex_assertions(
            (fixture / "fig3_resistance_mechanism.tex").read_text(encoding="utf-8"),
            assertions,
        )
        == []
    )


def test_fig3_carrier_sequence_binds_each_transfer_to_declared_named_states():
    plugin_root = Path(__file__).resolve().parents[1]
    fixture = plugin_root / "examples" / "fig3_resistance_mechanism"
    spec = yaml.safe_load((fixture / "spec.yaml").read_text(encoding="utf-8"))
    assertions = cta.parse_named_endpoint_assertions(
        spec,
        source_name="fig3_resistance_mechanism.tex",
    )

    assert [assertion["id"] for assertion in assertions] == [
        "carrier-sequence-binds-every-transfer-to-a-declared-state",
        "terminal-state-label-binds-to-terminal-trap",
    ]
    assert cta.check_named_endpoint_assertions(
        (fixture / "fig3_resistance_mechanism.tex").read_text(encoding="utf-8"),
        assertions,
    ) == []


def test_named_endpoint_assertion_rejects_a_literal_detached_transfer_path():
    tex = "\n".join(
        [
            r"\coordinate (carrier) at (1.0,3.0);",
            r"\coordinate (trap) at (1.0,2.0);",
            r"\draw[xfer] (carrier) to[out=-90,in=90] (1.0,2.0);",
        ]
    )
    assertion = {
        "id": "named-transfer",
        "anchor_style": "xfer",
        "minimum_paths": 1,
        "required_anchors": ["carrier", "trap"],
        "allowed_anchors": ["carrier", "trap"],
    }

    issues = cta.check_named_endpoint_assertions(tex, [assertion])

    assert issues[0]["id"] == "named-transfer"
    assert issues[0]["status"] == "insufficient_named_paths"


def test_named_endpoint_assertion_binds_a_straight_leader_to_its_named_target():
    tex = "\n".join(
        [
            r"\coordinate (trap) at (1.0,2.0);",
            r"\coordinate (label_anchor) at (1.0,1.5);",
            r"\draw[terminalLabelLeader] (trap) -- (label_anchor);",
            r"\node (label) at (label_anchor) {slow-release};",
        ]
    )
    assertion = {
        "id": "terminal-label",
        "anchor_style": "terminalLabelLeader",
        "minimum_paths": 1,
        "required_anchors": ["trap", "label_anchor"],
        "allowed_anchors": ["trap", "label_anchor"],
        "required_node_bindings": [{"node": "label", "anchor": "label_anchor"}],
    }

    assert cta.check_named_endpoint_assertions(tex, [assertion]) == []


def test_named_endpoint_assertion_rejects_a_leader_when_its_label_node_detaches():
    tex = "\n".join(
        [
            r"\coordinate (trap) at (1.0,2.0);",
            r"\coordinate (label_anchor) at (1.0,1.5);",
            r"\draw[terminalLabelLeader] (trap) -- (label_anchor);",
            r"\node (label) at (1.6,1.5) {slow-release};",
        ]
    )
    assertion = {
        "id": "terminal-label",
        "anchor_style": "terminalLabelLeader",
        "minimum_paths": 1,
        "required_anchors": ["trap", "label_anchor"],
        "allowed_anchors": ["trap", "label_anchor"],
        "required_node_bindings": [{"node": "label", "anchor": "label_anchor"}],
    }

    issues = cta.check_named_endpoint_assertions(tex, [assertion])

    assert issues[0]["status"] == "named_label_binding_missing"


def test_payload_has_stable_shape(tmp_path):
    tex_path = tmp_path / "demo.tex"
    tex_path.write_text(FORCE_TOWARD, encoding="utf-8")
    payload = cta.tex_assertions_payload(
        tex_path,
        cta.check_tex_assertions(FORCE_TOWARD, [ASSERTION]),
        assertion_count=1,
    )
    assert payload["schema"] == "figure-agent.tex-assertions.v1"
    assert payload["checked"] == 1
    assert payload["total"] == 1
    assert payload["source_hashes"]["examples/demo/demo.tex"].startswith("sha256:")


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
    tex = (
        "\\draw[-{Stealth[length=6pt,width=4.5pt]}, cRed!80!black, "
        "line width=0.7pt] (11.55, 1.3) -- (10.85, 1.3);"
    )
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
                    {"id": "e", "status": "insufficient_matches"},
                ]
            }
        ),
        encoding="utf-8",
    )
    assert {i["id"] for i in cta.read_blocking_issues(p)} == {"a", "c", "d", "e"}


def test_read_blocking_issues_missing_artifact_blocks(tmp_path):
    issues = cta.read_blocking_issues(tmp_path / "tex_assertions.json")
    assert issues, "missing evidence must block export, not pass it"


def test_read_blocking_issues_corrupt_artifact_blocks(tmp_path):
    p = tmp_path / "tex_assertions.json"
    p.write_text("{truncated", encoding="utf-8")
    assert cta.read_blocking_issues(p)


def test_read_blocking_issues_old_schema_blocks(tmp_path):
    p = tmp_path / "tex_assertions.json"
    p.write_text(json.dumps({"no_issues_key": True}), encoding="utf-8")
    assert cta.read_blocking_issues(p)


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
    assert data["source_hashes"]["examples/demo/demo.tex"].startswith("sha256:")


def test_cli_strict_rejects_commented_out_minimum_matches(tmp_path):
    import subprocess

    fixture = tmp_path / "demo"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text(
        "name: demo\n"
        "tex_assertions:\n"
        "  - id: repeated-capture\n"
        "    anchor_style: capture\n"
        "    axis: y\n"
        "    direction: decreasing\n"
        "    minimum_matches: 2\n",
        encoding="utf-8",
    )
    (fixture / "demo.tex").write_text(
        "% \\draw[capture] (1,3) to[out=-90,in=90] (1,2);\n"
        "% \\draw[capture] (2,3) to[out=-90,in=90] (2,2);\n",
        encoding="utf-8",
    )
    script = Path(__file__).resolve().parents[1] / "scripts" / "checks" / "check_tex_assertions.py"
    result = subprocess.run(
        [sys.executable, str(script), str(fixture / "demo.tex"), "--strict"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "insufficient_matches" in result.stdout


# --- M1: direction must follow the arrowhead, not coordinate order ---


def test_check_direction_flips_on_reverse_tip():
    # coords go +x, but the head is at the START, so the arrow physically points -x.
    coords = (0.0, 0.0, 2.0, 0.0)
    assert cta.check_direction(coords, axis="x", direction="decreasing", tip="reverse") == "pass"
    assert (
        cta.check_direction(coords, axis="x", direction="increasing", tip="reverse") == "violated"
    )


def test_check_direction_forward_tip_is_the_default():
    coords = (0.0, 0.0, 2.0, 0.0)
    assert cta.check_direction(coords, axis="x", direction="increasing") == cta.check_direction(
        coords, axis="x", direction="increasing", tip="forward"
    )


def test_check_tex_assertions_flags_reversed_arrowhead():
    # Head flipped to the start: coords decrease in x but the arrow physically points
    # +x, so a "decreasing" (points -x) assertion must be VIOLATED, not passed on
    # coordinate order alone. This is the reversed-force-arrow the checker exists for.
    tex = "\\draw[forceArr,{Stealth}-] (2,0) -- (0,0);"
    assertions = [
        {"id": "force-away", "anchor_style": "forceArr", "axis": "x", "direction": "decreasing"}
    ]
    issues = cta.check_tex_assertions(tex, assertions)
    assert len(issues) == 1
    assert issues[0]["status"] == "violated"


def test_check_tex_assertions_forward_arrowhead_passes():
    # Same coords, head at the end: physically points -x, decreasing holds -> pass.
    tex = "\\draw[forceArr,-{Stealth}] (2,0) -- (0,0);"
    assertions = [
        {"id": "force-away", "anchor_style": "forceArr", "axis": "x", "direction": "decreasing"}
    ]
    assert cta.check_tex_assertions(tex, assertions) == []


def test_check_tex_assertions_honors_reverse_arrowhead_on_curved_to_path():
    # The endpoint order is decreasing-x, but the head is at the start of the
    # curved path, so the physical direction is increasing-x.
    tex = r"\draw[forceArr] (2,0) to[{Stealth}-] (0,0);"
    assertions = [
        {"id": "force-away", "anchor_style": "forceArr", "axis": "x", "direction": "decreasing"}
    ]

    issues = cta.check_tex_assertions(tex, assertions)

    assert issues[0]["status"] == "violated"


def test_check_tex_assertions_matches_styled_draw_with_inline_tip_bracket():
    # C2: an inline tip spec with an inner ] must not break the styled-draw anchor.
    tex = "\\draw[forceArr,-{Stealth[length=6pt,width=4.5pt]}] (0,0) -- (-1,0);"
    assertions = [
        {"id": "force-away", "anchor_style": "forceArr", "axis": "x", "direction": "decreasing"}
    ]
    # forward tip, coords -x -> decreasing holds -> pass (NOT anchor_missing).
    assert cta.check_tex_assertions(tex, assertions) == []


def test_named_style_arrowhead_satisfies_unidirectional_assertion():
    tex = "\\tikzset{xfer/.style={-{Stealth[length=1mm]}}}\n\\draw[xfer] (0,1) -- (0,0);"
    assertion = {
        "id": "capture",
        "anchor_style": "xfer",
        "axis": "y",
        "direction": "decreasing",
        "require_unidirectional_arrow": True,
    }
    assert cta.check_tex_assertions(tex, [assertion]) == []


def test_unidirectional_assertion_rejects_missing_or_bidirectional_arrowhead():
    assertion = {
        "id": "capture",
        "anchor_style": "xfer",
        "axis": "y",
        "direction": "decreasing",
        "require_unidirectional_arrow": True,
    }
    for options in ("xfer", "xfer,<->"):
        issues = cta.check_tex_assertions(f"\\draw[{options}] (0,1) -- (0,0);", [assertion])
        assert issues[0]["status"] == "arrowhead_invalid"
