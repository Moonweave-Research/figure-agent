from __future__ import annotations

import sys
from pathlib import Path

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
