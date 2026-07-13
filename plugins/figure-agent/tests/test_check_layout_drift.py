"""Tests for the compile-stage layout drift checker."""

from __future__ import annotations

import json
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


def test_evaluate_drift_matches_decorated_and_split_tokens() -> None:
    hints = {
        "reference_image_size": [1000, 1000],
        "text_labels": [
            {"text": "HV+", "bbox": [100, 100, 140, 120]},
            {"text": "V", "bbox": [200, 100, 210, 120]},
            {"text": "active", "bbox": [212, 100, 260, 120]},
            {"text": "q", "bbox": [300, 100, 310, 120]},
            {"text": "tr", "bbox": [312, 100, 330, 120]},
        ],
    }
    pdf_words = [
        _word("HV", 100, 100, 140, 120),
        _word("V", 200, 100, 210, 120),
        _word("active", 212, 100, 260, 120),
        _word("qtr", 300, 100, 330, 120),
    ]

    results = check_layout_drift.evaluate_drift(
        ["HV", "Vactive", "qtr"],
        hints,
        pdf_words,
        (1000.0, 1000.0),
    )

    assert [result.status for result in results] == ["matched", "matched", "matched"]
    assert all(result.drift is not None and result.drift < 0.05 for result in results)


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


def test_main_checks_coordinate_hints_fixture_instead_of_skipping(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
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
        lambda _path: ([_word("Energy", 105, 105, 205, 145)], (1000.0, 1000.0)),
    )

    exit_code = check_layout_drift.main([str(fixture), "--strict"])

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "OK layout drift Energy: 0.007"


def test_layout_lane_contract_flags_narrative_group_overlapping_bias_marker() -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "label_groups": [
            {
                "id": "narrative",
                "required_terms": ["applied", "trapping", "during", "conduction"],
            },
            {"id": "bias", "required_terms": ["V"]},
        ],
        "rules": [
            {
                "id": "narrative_clear_of_bias",
                "kind": "minimum_clearance",
                "first": "narrative",
                "second": "bias",
                "minimum_normalized_clearance": 0.015,
            }
        ],
    }
    words = [
        _word("applied", 20, 20, 60, 30),
        _word("V", 65, 20, 75, 30),
        _word("trapping", 80, 20, 120, 30),
        _word("during", 125, 20, 165, 30),
        _word("conduction", 170, 20, 230, 30),
    ]

    results = check_layout_drift.evaluate_layout_lanes(contract, words, (400.0, 200.0))

    assert len(results) == 1
    assert results[0].rule_id == "narrative_clear_of_bias"
    assert results[0].status == "violation"
    assert results[0].clearance == 0.0


def test_layout_lane_contract_accepts_separated_groups_and_reports_missing_terms() -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "label_groups": [
            {"id": "title", "required_terms": ["applied", "conduction"]},
            {"id": "bias", "required_terms": ["V"]},
        ],
        "rules": [
            {
                "id": "title_clear_of_bias",
                "kind": "minimum_clearance",
                "first": "title",
                "second": "bias",
                "minimum_normalized_clearance": 0.05,
            }
        ],
    }

    clear = check_layout_drift.evaluate_layout_lanes(
        contract,
        [
            _word("applied", 20, 20, 60, 30),
            _word("conduction", 70, 20, 120, 30),
            _word("V", 250, 20, 260, 30),
        ],
        (400.0, 200.0),
    )
    missing = check_layout_drift.evaluate_layout_lanes(
        contract,
        [_word("applied", 20, 20, 60, 30), _word("V", 250, 20, 260, 30)],
        (400.0, 200.0),
    )

    assert clear[0].status == "ok"
    assert clear[0].clearance is not None and clear[0].clearance > 0.05
    assert missing[0].status == "missing_label_group"
    assert missing[0].missing_groups == ("title",)


def test_direct_layout_lane_cli_writes_machine_readable_failure_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = tmp_path / "layout_lanes.yaml"
    contract.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.layout-lanes.v1",
                "label_groups": [
                    {"id": "title", "required_terms": ["applied"]},
                    {"id": "bias", "required_terms": ["V"]},
                ],
                "rules": [
                    {
                        "id": "title_clear_of_bias",
                        "kind": "minimum_clearance",
                        "first": "title",
                        "second": "bias",
                        "minimum_normalized_clearance": 0.01,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "layout_report.json"
    monkeypatch.setattr(
        check_layout_drift,
        "extract_pdf_words_and_page",
        lambda _path: (
            [_word("applied", 20, 20, 60, 30), _word("V", 40, 20, 50, 30)],
            (100.0, 100.0),
        ),
    )

    exit_code = check_layout_drift.main(
        [
            "--pdf",
            str(tmp_path / "render.pdf"),
            "--layout-contract",
            str(contract),
            "--json-output",
            str(output),
            "--strict",
        ]
    )

    assert exit_code == 1
    assert json.loads(output.read_text(encoding="utf-8"))["results"][0]["status"] == "violation"
