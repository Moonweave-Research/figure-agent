from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


import pytest  # noqa: E402
from semantic_assertions import (  # noqa: E402
    SemanticAssertionError,
    check_semantic_assertions,
    parse_assertions,
    semantic_assertions_payload,
)


def _word(text: str, x: float, y: float) -> dict:
    # bbox in pdftotext points: origin top-left, y increases downward
    return {"text": text, "xmin": x, "ymin": y, "xmax": x + 10.0, "ymax": y + 5.0}


def test_parse_empty_when_absent():
    assert parse_assertions({}) == []


def test_parse_valid_assertion():
    spec = {
        "semantic_assertions": [
            {"id": "a", "relation": "above", "subject": "shallow", "reference": "deep"}
        ]
    }
    parsed = parse_assertions(spec)
    assert parsed == [{"id": "a", "relation": "above", "subject": "shallow", "reference": "deep"}]


def test_parse_rejects_bad_relation():
    spec = {
        "semantic_assertions": [
            {"id": "a", "relation": "diagonal", "subject": "s", "reference": "d"}
        ]
    }
    with pytest.raises(SemanticAssertionError, match="relation"):
        parse_assertions(spec)


def test_parse_rejects_missing_field():
    spec = {"semantic_assertions": [{"id": "a", "relation": "above", "subject": "s"}]}
    with pytest.raises(SemanticAssertionError, match="reference"):
        parse_assertions(spec)


def test_above_holds_and_below_violates():
    # "shallow" higher on page (smaller y) than "deep"
    words = [_word("shallow", 100, 20), _word("deep", 100, 80)]
    assertions = [{"id": "sd", "relation": "above", "subject": "shallow", "reference": "deep"}]
    assert check_semantic_assertions(words, assertions) == []

    bad = [{"id": "sd", "relation": "below", "subject": "shallow", "reference": "deep"}]
    issues = check_semantic_assertions(words, bad)
    assert len(issues) == 1 and issues[0]["status"] == "violated"


def test_left_right_relations():
    words = [_word("plus", 20, 50), _word("minus", 200, 50)]
    assert (
        check_semantic_assertions(
            words, [{"id": "lr", "relation": "left_of", "subject": "plus", "reference": "minus"}]
        )
        == []
    )
    issues = check_semantic_assertions(
        words, [{"id": "lr", "relation": "right_of", "subject": "plus", "reference": "minus"}]
    )
    assert issues[0]["status"] == "violated"


def test_near_tie_is_indeterminate():
    # centres differ by 1pt along y (< default 2.0pt tolerance) -> too close to call
    words = [_word("shallow", 100, 20.0), _word("deep", 100, 21.0)]
    assertions = [{"id": "sd", "relation": "above", "subject": "shallow", "reference": "deep"}]
    issues = check_semantic_assertions(words, assertions)
    assert len(issues) == 1 and issues[0]["status"] == "indeterminate"


def test_per_assertion_tolerance_overrides_default():
    # 3pt margin: clears the 2.0pt default (satisfied) but a 5pt band calls it indeterminate
    words = [_word("shallow", 100, 20.0), _word("deep", 100, 23.0)]
    base = {"id": "sd", "relation": "above", "subject": "shallow", "reference": "deep"}
    assert check_semantic_assertions(words, [base]) == []

    widened = parse_assertions({"semantic_assertions": [{**base, "tolerance_pt": 5.0}]})
    issues = check_semantic_assertions(words, widened)
    assert len(issues) == 1 and issues[0]["status"] == "indeterminate"


def test_parse_rejects_non_positive_tolerance():
    spec = {
        "semantic_assertions": [
            {"id": "a", "relation": "above", "subject": "s", "reference": "d", "tolerance_pt": 0}
        ]
    }
    with pytest.raises(SemanticAssertionError, match="tolerance_pt"):
        parse_assertions(spec)


def test_parse_valid_alignment_assertion():
    spec = {
        "semantic_assertions": [
            {
                "id": "row-subtitle-baseline",
                "kind": "baseline_aligned",
                "targets": ["kinetic", "ISPD", "mechanical"],
                "tolerance_cm": 0.05,
            }
        ]
    }

    parsed = parse_assertions(spec)

    assert parsed == [
        {
            "id": "row-subtitle-baseline",
            "kind": "baseline_aligned",
            "targets": ["kinetic", "ISPD", "mechanical"],
            "tolerance_cm": 0.05,
        }
    ]


def test_parse_rejects_bad_alignment_kind_and_too_few_targets():
    with pytest.raises(SemanticAssertionError, match="kind"):
        parse_assertions(
            {
                "semantic_assertions": [
                    {"id": "bad", "kind": "diagonal_aligned", "targets": ["a", "b"]}
                ]
            }
        )

    with pytest.raises(SemanticAssertionError, match="targets"):
        parse_assertions(
            {"semantic_assertions": [{"id": "short", "kind": "left_aligned", "targets": ["a"]}]}
        )


def test_alignment_baseline_violation_reports_numeric_delta():
    words = [
        _word("kinetic", 10, 100.0),
        _word("ISPD", 40, 92.0),
        _word("mechanical", 80, 100.0),
    ]
    assertions = parse_assertions(
        {
            "semantic_assertions": [
                {
                    "id": "row-subtitle-baseline",
                    "kind": "baseline_aligned",
                    "targets": ["kinetic", "ISPD", "mechanical"],
                    "tolerance_cm": 0.05,
                }
            ]
        }
    )

    issues = check_semantic_assertions(words, assertions)

    assert len(issues) == 1
    issue = issues[0]
    assert issue["status"] == "violated"
    assert issue["kind"] == "baseline_aligned"
    assert issue["targets"] == ["kinetic", "ISPD", "mechanical"]
    assert issue["edit_target"] == "ISPD"
    assert issue["measured_delta_pt"] == pytest.approx(8.0)
    assert issue["measured_delta_cm"] == pytest.approx(8.0 / (72.0 / 2.54))
    assert issue["tolerance_cm"] == 0.05


def test_alignment_without_unique_outlier_omits_edit_target():
    words = [_word("a", 10, 100.0), _word("b", 40, 92.0), _word("c", 70, 108.0)]
    assertions = parse_assertions(
        {
            "semantic_assertions": [
                {"id": "spread", "kind": "baseline_aligned", "targets": ["a", "b", "c"]}
            ]
        }
    )

    issues = check_semantic_assertions(words, assertions)

    assert issues[0]["status"] == "violated"
    assert "edit_target" not in issues[0]


def test_alignment_variants_pass_within_tolerance():
    words = [_word("a", 10.0, 20.0), _word("b", 10.5, 20.4), _word("c", 10.2, 20.2)]
    for kind in (
        "top_aligned",
        "left_aligned",
        "right_aligned",
        "center_aligned_x",
        "center_aligned_y",
    ):
        assertions = parse_assertions(
            {
                "semantic_assertions": [
                    {
                        "id": kind,
                        "kind": kind,
                        "targets": ["a", "b", "c"],
                        "tolerance_cm": 0.05,
                    }
                ]
            }
        )

        assert check_semantic_assertions(words, assertions) == []


def test_p5_multi_match_is_anchor_ambiguous_for_relations_and_alignment():
    words = [_word("deep", 10, 20), _word("deep", 30, 20), _word("shallow", 10, 80)]

    relation_issues = check_semantic_assertions(
        words, [{"id": "sd", "relation": "above", "subject": "shallow", "reference": "deep"}]
    )
    assert relation_issues[0]["status"] == "anchor_ambiguous"
    assert relation_issues[0]["anchor"] == "deep"

    alignment = parse_assertions(
        {
            "semantic_assertions": [
                {"id": "ambiguous", "kind": "baseline_aligned", "targets": ["deep", "shallow"]}
            ]
        }
    )
    alignment_issues = check_semantic_assertions(words, alignment)
    assert alignment_issues[0]["status"] == "anchor_ambiguous"
    assert alignment_issues[0]["anchor"] == "deep"


def test_cross_figure_recall_deliberate_baseline_float_on_non_v5f_fixture():
    words = [_word("CB", 10, 100.0), _word("trap", 40, 92.0), _word("VB", 70, 100.0)]
    assertions = parse_assertions(
        {
            "semantic_assertions": [
                {
                    "id": "fig3-deliberate-baseline-float",
                    "kind": "baseline_aligned",
                    "targets": ["CB", "trap", "VB"],
                }
            ]
        }
    )

    issues = check_semantic_assertions(words, assertions)

    assert issues[0]["status"] == "violated"
    assert issues[0]["measured_delta_pt"] == pytest.approx(8.0)


def test_missing_anchor_reported():
    words = [_word("shallow", 100, 20)]
    issues = check_semantic_assertions(
        words, [{"id": "sd", "relation": "above", "subject": "shallow", "reference": "deep"}]
    )
    assert len(issues) == 1 and issues[0]["status"] == "anchor_missing"


def test_payload_structure():
    payload = semantic_assertions_payload(Path("build/fig.pdf"), [], 3)
    assert payload["schema"] == "figure-agent.semantic-assertions.v1"
    assert payload["checked"] == 3
    assert payload["total"] == 0


def test_fig3_declares_visible_temporal_and_composition_ordering_contracts():
    plugin_root = Path(__file__).resolve().parents[1]
    spec = yaml.safe_load(
        (
            plugin_root / "examples" / "fig3_resistance_mechanism" / "spec.yaml"
        ).read_text(encoding="utf-8")
    )

    assertions = parse_assertions(spec)

    assert {
        (assertion["id"], assertion["relation"], assertion["subject"], assertion["reference"])
        for assertion in assertions
    } >= {
        ("fig3-capture-before-release", "left_of", "capture", "release"),
        ("fig3-release-before-retained", "left_of", "release", "retained"),
        ("fig3-s60-before-s80", "left_of", "S60", "S80"),
    }


def test_fig3_declares_three_column_qualitative_response_and_landscape_grammar() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    fixture = plugin_root / "examples" / "fig3_resistance_mechanism"
    spec = yaml.safe_load((fixture / "spec.yaml").read_text(encoding="utf-8"))
    source = (fixture / "fig3_resistance_mechanism.tex").read_text(encoding="utf-8")
    objects = spec["composition_model"]["panels"]

    assert objects["B"]["objects"]["qualitative_current_decay"]["invariant"] == (
        "qualitative_not_measured_and_current_decay_implies_resistance_increase"
    )
    assert objects["C"]["objects"]["s60_discrete_states"]["invariant"] == (
        "low_sulfur_discrete_state_set_not_spectrum_bar_chart"
    )
    assert "object=qualitative_current_decay panel=B kind=qualitative_relation" in source
    assert "object=s60_discrete_states panel=C kind=energy_landscape" in source
    assert "($(trap_deep)+(-0.78,-0.32)$)" in source
    assert "at (retained_label_anchor) {retained}" in source
    assert "$\\rho_{60" not in source
    assert {
        (assertion["id"], assertion["relation"], assertion["subject"], assertion["reference"])
        for assertion in parse_assertions(spec)
    } >= {
        ("fig3-mechanism-before-response", "left_of", "retained", "qualitative"),
        ("fig3-response-before-landscape", "left_of", "qualitative", "S60"),
    }


def test_fig3_qualitative_current_trace_is_a_shallowing_power_law_not_a_terminal_drop() -> None:
    plugin_root = Path(__file__).resolve().parents[1]
    source = (
        plugin_root
        / "examples"
        / "fig3_resistance_mechanism"
        / "fig3_resistance_mechanism.tex"
    ).read_text(encoding="utf-8")

    assert "(1+2.8*(\\x-5.98)/2.82)^(-0.85)" in source
    assert "((8.80-\\x)/2.82)^0.52" not in source
    assert "dashed, line width=0.35pt] (5.98,1.62) -- (8.80,1.62)" not in source

    def current_at(normalized_time: float) -> float:
        return 1.18 + 2.05 * (1 + 2.8 * normalized_time) ** -0.85

    values = [current_at(time) for time in (0.0, 0.25, 0.5, 0.75, 1.0)]
    drops = [values[index] - values[index + 1] for index in range(len(values) - 1)]
    assert all(later < earlier for earlier, later in zip(values, values[1:]))
    assert all(later < earlier for earlier, later in zip(drops, drops[1:]))


def test_load_spec_missing_returns_empty(tmp_path: Path) -> None:
    from semantic_assertions import _load_spec

    assert _load_spec(tmp_path / "spec.yaml") == {}


def test_load_spec_empty_file_returns_empty(tmp_path: Path) -> None:
    from semantic_assertions import _load_spec

    spec = tmp_path / "spec.yaml"
    spec.write_text("", encoding="utf-8")
    assert _load_spec(spec) == {}


def test_load_spec_non_dict_blocks(tmp_path: Path) -> None:
    from semantic_assertions import _load_spec

    spec = tmp_path / "spec.yaml"
    spec.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(SemanticAssertionError, match="not a mapping"):
        _load_spec(spec)


def test_load_spec_unreadable_yaml_blocks(tmp_path: Path) -> None:
    from semantic_assertions import _load_spec

    spec = tmp_path / "spec.yaml"
    spec.write_text("semantic_assertions: [unterminated\n", encoding="utf-8")
    with pytest.raises(SemanticAssertionError, match="unreadable spec.yaml"):
        _load_spec(spec)


def test_main_blocks_on_non_dict_spec(tmp_path: Path) -> None:
    from semantic_assertions import main

    fixture = tmp_path / "fig"
    build = fixture / "build"
    build.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("- not\n- a\n- mapping\n", encoding="utf-8")
    pdf = build / "fig.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")

    assert main([str(pdf)]) == 2


def test_main_passes_when_spec_missing(tmp_path: Path) -> None:
    from semantic_assertions import main

    fixture = tmp_path / "fig"
    build = fixture / "build"
    build.mkdir(parents=True)
    pdf = build / "fig.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")

    # No spec.yaml -> nothing declared -> pass without touching the PDF.
    assert main([str(pdf)]) == 0
