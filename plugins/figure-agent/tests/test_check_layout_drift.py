"""Tests for the compile-stage layout drift checker."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "checks"))

import check_layout_drift  # noqa: E402


def _word(text: str, x0: float, y0: float, x1: float, y1: float) -> dict:
    return {"text": text, "xmin": x0, "ymin": y0, "xmax": x1, "ymax": y1}


def test_evaluate_drift_flags_position_change() -> None:
    hints = {
        "reference_image_size": [1000, 1000],
        "text_labels": [{"text": "Energy", "bbox": [100, 100, 200, 140]}],
    }
    results = check_layout_drift.evaluate_drift(
        ["Energy"],
        hints,
        [_word("Energy", 700, 700, 800, 740)],
        (1000.0, 1000.0),
    )

    assert results[0].status == "matched"
    assert results[0].drift is not None and results[0].drift > 0.05


def test_run_check_skips_without_coordinate_hints(tmp_path: Path) -> None:
    fixture = tmp_path / "demo"
    fixture.mkdir()
    (fixture / "spec.yaml").write_text(
        "golden_contract:\n  required_labels: [Energy]\n",
        encoding="utf-8",
    )

    failures, lines = check_layout_drift.run_check(fixture)

    assert failures == 0
    assert lines == [f"SKIP layout drift: missing coordinate_hints.yaml in {fixture}"]


def test_run_check_reports_drift_from_coordinate_hints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = tmp_path / "demo"
    build = fixture / "build"
    build.mkdir(parents=True)
    (build / "demo.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    (fixture / "spec.yaml").write_text(
        "golden_contract:\n  required_labels: [Energy]\n",
        encoding="utf-8",
    )
    (fixture / "coordinate_hints.yaml").write_text(
        yaml.safe_dump(
            {
                "reference_image_size": [1000, 1000],
                "text_labels": [{"text": "Energy", "bbox": [100, 100, 200, 140]}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        check_layout_drift,
        "extract_pdf_words_and_page",
        lambda _path: ([_word("Energy", 700, 700, 800, 740)], (1000.0, 1000.0)),
    )

    failures, lines = check_layout_drift.run_check(fixture)

    assert failures == 1
    assert lines == ["WARN layout drift Energy: 0.849 > 0.050"]
