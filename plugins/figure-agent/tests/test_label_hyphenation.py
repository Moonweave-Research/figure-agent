from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


from check_label_hyphenation import (  # noqa: E402
    detect_label_hyphenation,
    label_hyphenation_payload,
)


def _word(text: str, xmin: float = 0.0, ymin: float = 0.0) -> dict:
    return {"text": text, "xmin": xmin, "ymin": ymin, "xmax": xmin + 1.0, "ymax": ymin + 1.0}


def test_detects_word_ending_in_ascii_hyphen():
    issues = detect_label_hyphenation([_word("nar-")])
    assert len(issues) == 1
    assert issues[0]["text"] == "nar-"
    assert "hyphenated line break" in issues[0]["message"]


def test_ignores_word_not_ending_in_hyphen():
    assert detect_label_hyphenation([_word("narrow")]) == []


def test_ignores_single_char_hyphen():
    # a standalone "-" is a real glyph (e.g. a minus label), not a broken word
    assert detect_label_hyphenation([_word("-")]) == []


def test_ignores_en_dash_and_minus_sign():
    # en dash (U+2013) and minus sign (U+2212) are not line-break artifacts
    assert detect_label_hyphenation([_word("S–S"), _word("−V")]) == []


def test_multiple_words_detects_broken_only():
    words = [_word("nar-"), _word("row"), _word("elec-"), _word("trode")]
    issues = detect_label_hyphenation(words)
    assert sorted(i["text"] for i in issues) == ["elec-", "nar-"]


def test_payload_structure():
    payload = label_hyphenation_payload(
        Path("build/fig.pdf"), detect_label_hyphenation([_word("in-")])
    )
    assert payload["schema"] == "figure-agent.label-hyphenation.v1"
    assert payload["total"] == 1
    assert payload["render_pdf"] == "build/fig.pdf"
    assert payload["issues"][0]["text"] == "in-"
