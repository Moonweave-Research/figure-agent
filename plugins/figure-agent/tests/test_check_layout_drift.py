"""Tests for check_layout_drift (Layer 6 anchor-driven layout drift gate)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_layout_drift  # noqa: E402


def _hints(text_labels: list[dict], size: tuple[int, int] = (1000, 1000)) -> dict:
    return {"reference_image_size": list(size), "text_labels": text_labels}


def _word(text: str, x1: float, y1: float, x2: float, y2: float) -> dict:
    return {"text": text, "xmin": x1, "ymin": y1, "xmax": x2, "ymax": y2}


def test_matched_ok_within_threshold():
    hints = _hints([{"text": "Energy", "bbox": [400, 200, 500, 240], "conf": 95.0}])
    pdf_words = [_word("Energy", 400, 200, 500, 240)]
    results = check_layout_drift.evaluate_drift(["Energy"], hints, pdf_words, (1000.0, 1000.0))
    assert len(results) == 1
    r = results[0]
    assert r.status == "matched_ok"
    assert r.drift == pytest.approx(0.0, abs=1e-6)


def test_drifted_above_threshold():
    hints = _hints([{"text": "deep", "bbox": [950, 540, 1000, 580], "conf": 95.0}])
    pdf_words = [_word("deep", 580, 470, 620, 510)]
    results = check_layout_drift.evaluate_drift(["deep"], hints, pdf_words, (1000.0, 1000.0))
    r = results[0]
    assert r.status == "matched_ok"  # status pre-threshold; flagging is in main()
    assert r.drift is not None and r.drift > 0.05


def test_phrase_matches_consecutive_words():
    hints = _hints(
        [
            {"text": "Mathematical", "bbox": [100, 100, 250, 130], "conf": 95.0},
            {"text": "interpretation", "bbox": [255, 100, 420, 130], "conf": 95.0},
        ]
    )
    pdf_words = [
        _word("Mathematical", 100, 100, 250, 130),
        _word("interpretation", 255, 100, 420, 130),
    ]
    results = check_layout_drift.evaluate_drift(
        ["Mathematical interpretation"], hints, pdf_words, (1000.0, 1000.0)
    )
    r = results[0]
    assert r.status == "matched_ok"
    assert r.drift == pytest.approx(0.0, abs=1e-6)


def test_alternates_match_when_first_form_misses():
    hints = _hints([{"text": "et", "bbox": [600, 600, 640, 630], "conf": 88.0}])
    pdf_words = [_word("et", 600, 600, 640, 630)]
    results = check_layout_drift.evaluate_drift([["e t", "et"]], hints, pdf_words, (1000.0, 1000.0))
    r = results[0]
    assert r.status == "matched_ok"
    assert r.matched_form is not None and "et" in r.matched_form


def test_punctuation_normalization_strips_surrounding_punct():
    hints = _hints([{"text": "(Debye", "bbox": [800, 100, 920, 130], "conf": 96.0}])
    pdf_words = [_word("(Debye", 800, 100, 920, 130)]
    results = check_layout_drift.evaluate_drift(["Debye"], hints, pdf_words, (1000.0, 1000.0))
    assert results[0].status == "matched_ok"


def test_uncovered_ref_when_label_absent_from_hints():
    hints = _hints([])
    pdf_words = [_word("Experiment", 100, 100, 250, 130)]
    results = check_layout_drift.evaluate_drift(["Experiment"], hints, pdf_words, (1000.0, 1000.0))
    assert results[0].status == "uncovered_ref"


def test_uncovered_build_when_label_absent_from_pdf():
    hints = _hints([{"text": "Experiment", "bbox": [100, 100, 250, 130], "conf": 95.0}])
    pdf_words: list[dict] = []
    results = check_layout_drift.evaluate_drift(["Experiment"], hints, pdf_words, (1000.0, 1000.0))
    assert results[0].status == "uncovered_build"


def test_uncovered_both_when_label_in_neither():
    hints = _hints([{"text": "other", "bbox": [0, 0, 10, 10], "conf": 95.0}])
    pdf_words = [_word("nothing", 0, 0, 10, 10)]
    results = check_layout_drift.evaluate_drift(["Experiment"], hints, pdf_words, (1000.0, 1000.0))
    assert results[0].status == "uncovered_both"


def test_aspect_line_reports_mismatch_percentage():
    line = check_layout_drift._aspect_line([1693, 929], (612.0, 792.0))
    assert "ref=1.822" in line
    assert "pdf=0.773" in line
    assert "mismatch=" in line


def test_aspect_line_handles_missing_data():
    assert "insufficient" in check_layout_drift._aspect_line([], (612.0, 792.0))
    assert "insufficient" in check_layout_drift._aspect_line([1693, 0], (612.0, 792.0))


def test_main_skips_when_no_required_labels(tmp_path, monkeypatch, capsys):
    example = tmp_path / "ordinary"
    example.mkdir()
    (example / "spec.yaml").write_text("panels: []\n")
    monkeypatch.setattr(sys, "argv", ["check_layout_drift.py", str(example)])
    assert check_layout_drift.main() == 0
    assert "SKIP" in capsys.readouterr().out


def test_main_skips_when_no_hints_file(tmp_path, monkeypatch, capsys):
    example = tmp_path / "fixture"
    example.mkdir()
    (example / "spec.yaml").write_text(
        yaml.safe_dump({"panels": [], "golden_contract": {"required_labels": ["Energy"]}})
    )
    monkeypatch.setattr(sys, "argv", ["check_layout_drift.py", str(example)])
    assert check_layout_drift.main() == 0
    assert "no coordinate_hints.yaml" in capsys.readouterr().out


def test_main_strict_exits_one_when_drift_exceeds_threshold(tmp_path, monkeypatch):
    example = tmp_path / "drift_fixture"
    example.mkdir()
    (example / "spec.yaml").write_text(
        yaml.safe_dump({"panels": [], "golden_contract": {"required_labels": ["deep"]}})
    )
    (example / "coordinate_hints.yaml").write_text(
        yaml.safe_dump(
            {
                "reference_image_size": [1000, 1000],
                "text_labels": [{"text": "deep", "bbox": [950, 540, 1000, 580], "conf": 95.0}],
            }
        )
    )
    fake_pdf = example / "build" / "drift_fixture.pdf"
    fake_pdf.parent.mkdir()
    fake_pdf.write_bytes(b"%PDF-1.4 stub\n")

    def fake_extract(_pdf_path):
        return ([_word("deep", 580, 470, 620, 510)], (1000.0, 1000.0))

    monkeypatch.setattr(check_layout_drift, "extract_pdf_words_and_page", fake_extract)
    monkeypatch.setattr(sys, "argv", ["check_layout_drift.py", str(example), "--strict"])
    assert check_layout_drift.main() == 1


def test_main_strict_exits_zero_when_only_uncovered(tmp_path, monkeypatch):
    """uncovered_* are not the drift gate's failure mode (other gates own coverage)."""
    example = tmp_path / "uncov_fixture"
    example.mkdir()
    (example / "spec.yaml").write_text(
        yaml.safe_dump({"panels": [], "golden_contract": {"required_labels": ["Experiment"]}})
    )
    (example / "coordinate_hints.yaml").write_text(
        yaml.safe_dump({"reference_image_size": [1000, 1000], "text_labels": []})
    )
    fake_pdf = example / "build" / "uncov_fixture.pdf"
    fake_pdf.parent.mkdir()
    fake_pdf.write_bytes(b"%PDF-1.4 stub\n")

    def fake_extract(_pdf_path):
        return ([], (1000.0, 1000.0))

    monkeypatch.setattr(check_layout_drift, "extract_pdf_words_and_page", fake_extract)
    monkeypatch.setattr(sys, "argv", ["check_layout_drift.py", str(example), "--strict"])
    assert check_layout_drift.main() == 0
