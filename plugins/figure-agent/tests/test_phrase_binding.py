from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "checks"))

import phrase_binding  # noqa: E402

TOLERANCES = {"max_gap": 6.0, "max_center_delta": 6.0}


def _word(text: str, xmin: float, ymin: float, xmax: float, ymax: float) -> dict[str, float | str]:
    return {"text": text, "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax}


def _phrase(phrase_id: str, *words: str) -> dict[str, object]:
    return {"id": phrase_id, "words": list(words)}


def test_single_line_phrase_span_is_unchanged() -> None:
    words = [
        _word("polymer", 90.0, 20.0, 120.0, 30.0),
        _word("film", 124.0, 20.0, 140.0, 30.0),
        _word("caption", 200.0, 20.0, 230.0, 30.0),
    ]

    matches = phrase_binding.group_phrase_words(
        words, _phrase("polymer_film", "polymer", "film"), **TOLERANCES
    )

    assert matches == [
        {
            "text": "polymer film",
            "phrase_id": "polymer_film",
            "words": ["polymer", "film"],
            "text_source": "text_phrases",
            "xmin": 90.0,
            "ymin": 20.0,
            "xmax": 140.0,
            "ymax": 30.0,
        }
    ]


def test_subscript_lifts_the_next_word_above_the_first_word_top_edge() -> None:
    # Rendered Vs (subscript) / meter from fig1 Panel E: "meter" has the
    # smaller ymin, so a forward-only scan over the top-edge sort never
    # reaches it from "Vs".
    words = [
        _word("meter", 251.273, 309.764, 264.516, 314.561),
        _word("Vs", 241.874, 310.016, 249.335, 315.435),
    ]

    matches = phrase_binding.group_phrase_words(
        words, _phrase("vs-meter", "Vs", "meter"), **TOLERANCES
    )

    assert [match["text"] for match in matches] == ["Vs meter"]
    assert matches[0]["xmin"] == 241.874
    assert matches[0]["xmax"] == 264.516


def test_subscript_between_two_baseline_words_still_binds() -> None:
    # Rendered q_tr (hyp.) from fig1 Panel F: the "(hyp.)" run sorts before
    # both "q" and its "tr" subscript.
    words = [
        _word("(hyp.)", 300.432, 416.534, 313.675, 421.331),
        _word("q", 292.997, 416.786, 296.279, 421.209),
        _word("tr", 296.280, 418.643, 298.495, 422.001),
    ]

    matches = phrase_binding.group_phrase_words(
        words, _phrase("q_tr_hyp", "q", "tr", "(hyp.)"), **TOLERANCES
    )

    assert [match["text"] for match in matches] == ["q tr (hyp.)"]
    assert matches[0]["ymin"] == 416.534
    assert matches[0]["ymax"] == 422.001


def test_two_line_node_binds_across_the_line_break() -> None:
    # Rendered "grounded\\substrate" node from fig1 Panel E.
    words = [
        _word("grounded", 243.674, 352.689, 265.569, 357.486),
        _word("substrate", 243.674, 358.866, 264.984, 363.663),
    ]

    matches = phrase_binding.group_phrase_words(
        words, _phrase("grounded_substrate", "grounded", "substrate"), **TOLERANCES
    )

    assert [match["text"] for match in matches] == ["grounded substrate"]
    assert matches[0]["ymin"] == 352.689
    assert matches[0]["ymax"] == 363.663


def test_two_line_node_binds_when_the_second_line_is_centred() -> None:
    # Rendered "manual sample\\transfer" node from fig1 Panel E: the second
    # line starts left of the word it continues.
    words = [
        _word("manual", 183.863, 355.523, 200.202, 360.136),
        _word("sample", 201.582, 355.523, 217.640, 360.136),
        _word("transfer", 192.309, 360.803, 209.197, 365.416),
    ]

    matches = phrase_binding.group_phrase_words(
        words, _phrase("manual_sample_transfer", "manual", "sample", "transfer"), **TOLERANCES
    )

    assert [match["text"] for match in matches] == ["manual sample transfer"]
    assert matches[0]["xmin"] == 183.863
    assert matches[0]["ymax"] == 365.416


def test_next_line_further_than_one_word_height_does_not_bind() -> None:
    words = [
        _word("grounded", 243.674, 352.689, 265.569, 357.486),
        _word("substrate", 243.674, 363.000, 264.984, 367.797),
    ]

    assert (
        phrase_binding.group_phrase_words(
            words, _phrase("grounded_substrate", "grounded", "substrate"), **TOLERANCES
        )
        == []
    )


def test_next_line_outside_the_span_horizontal_extent_does_not_bind() -> None:
    words = [
        _word("grounded", 243.674, 352.689, 265.569, 357.486),
        _word("substrate", 300.000, 358.866, 321.310, 363.663),
    ]

    assert (
        phrase_binding.group_phrase_words(
            words, _phrase("grounded_substrate", "grounded", "substrate"), **TOLERANCES
        )
        == []
    )


def test_a_word_is_never_reused_inside_one_span() -> None:
    words = [_word("S", 90.0, 20.0, 96.0, 28.0)]

    assert phrase_binding.group_phrase_words(words, _phrase("s_s", "S", "S"), **TOLERANCES) == []


def test_repeated_word_binds_two_distinct_rendered_runs() -> None:
    words = [
        _word("S", 90.0, 20.0, 96.0, 28.0),
        _word("S", 98.0, 20.0, 104.0, 28.0),
    ]

    matches = phrase_binding.group_phrase_words(words, _phrase("s_s", "S", "S"), **TOLERANCES)

    assert [(match["xmin"], match["xmax"]) for match in matches] == [(90.0, 104.0)]


def test_nearest_words_report_what_the_render_says_instead() -> None:
    words = [
        _word("Maxwell", 350.602, 380.848, 367.875, 385.276),
        _word("stress", 369.199, 380.848, 381.953, 385.276),
    ]

    nearest = phrase_binding.nearest_phrase_words(
        words, _phrase("maxwell_vacuum", "Maxwell", "vacuum"), **TOLERANCES
    )

    assert nearest == ["Maxwell", "stress"]


def test_nearest_words_are_empty_when_the_first_word_is_not_drawn() -> None:
    words = [_word("broad", 69.483, 367.452, 82.734, 372.249)]

    assert (
        phrase_binding.nearest_phrase_words(
            words, _phrase("trap_mediated_decay", "trap-mediated", "decay"), **TOLERANCES
        )
        == []
    )


def test_phrase_unmatched_failure_carries_declaration_and_render_evidence() -> None:
    failure = phrase_binding.phrase_unmatched_failure(
        "panel-f-force-labels",
        _phrase("maxwell_vacuum", "Maxwell", "vacuum"),
        ["Maxwell", "stress"],
    )

    assert failure == {
        "check_id": "panel-f-force-labels",
        "kind": "phrase_unmatched",
        "phrase_id": "maxwell_vacuum",
        "words": ["Maxwell", "vacuum"],
        "nearest_words": ["Maxwell", "stress"],
        "detail": "Maxwell vacuum (nearest rendered: Maxwell, stress)",
    }


def test_binding_state_distinguishes_absent_from_clean() -> None:
    assert phrase_binding.binding_state(0, []) == "not_declared"
    assert phrase_binding.binding_state(3, []) == "passed"
    assert phrase_binding.binding_state(3, [{"kind": "phrase_unmatched"}]) == "failed"


def test_allowlist_matches_returns_every_named_word_in_reading_order() -> None:
    words = [
        _word("head", 251.273, 309.764, 264.516, 314.561),
        _word("ESVM", 241.874, 310.016, 249.335, 315.435),
        _word("film", 190.0, 340.0, 205.0, 348.0),
    ]

    matched = phrase_binding.allowlist_matches(words, {"ESVM", "head"})

    assert [word["text"] for word in matched] == ["head", "ESVM"]
    assert phrase_binding.allowlist_matches(words, {"probe"}) == []


def test_allowlist_unmatched_failure_names_the_declared_and_the_rendered_words() -> None:
    failure = phrase_binding.allowlist_unmatched_failure(
        "panel-e-probe-shaft",
        {"probe", "shaft"},
        ["ESVM", "head"],
    )

    assert failure == {
        "check_id": "panel-e-probe-shaft",
        "kind": "allowlist_unmatched",
        "words": ["probe", "shaft"],
        "nearest_words": ["ESVM", "head"],
        "detail": "probe, shaft (nearest rendered: ESVM, head)",
    }
    assert phrase_binding.allowlist_unmatched_failure("x", {"probe"}, [])["detail"] == (
        "probe (nearest rendered: none)"
    )


def test_unbound_allowlist_words_names_only_the_words_the_render_never_draws() -> None:
    words = [
        _word("ESVM", 241.874, 310.016, 249.335, 315.435),
        _word("head", 251.273, 309.764, 264.516, 314.561),
    ]

    assert phrase_binding.unbound_allowlist_words(words, {"ESVM", "head"}) == []
    assert phrase_binding.unbound_allowlist_words(words, {"ESVM", "probe", "shaft"}) == [
        "probe",
        "shaft",
    ]


def test_allowlist_word_unmatched_failure_names_only_the_dead_words() -> None:
    failure = phrase_binding.allowlist_word_unmatched_failure(
        "panel-f-ground-return",
        ["return", "source"],
        ["grounded", "clip"],
    )

    assert failure == {
        "check_id": "panel-f-ground-return",
        "kind": "allowlist_word_unmatched",
        "words": ["return", "source"],
        "nearest_words": ["grounded", "clip"],
        "detail": "return, source (nearest rendered: grounded, clip)",
    }
