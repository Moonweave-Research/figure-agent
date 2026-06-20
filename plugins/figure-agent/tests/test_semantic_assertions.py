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
