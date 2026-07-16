"""Tests for the compile-stage layout drift checker."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
FIG3_FIXTURE = REPO_ROOT / "examples" / "fig3_resistance_mechanism"
HISTORICAL_LAYOUT_TRANSFER_RECEIPT = (
    FIG3_FIXTURE
    / "review"
    / "failure-first"
    / "historical_layout_transfer_receipt_v1.yaml"
)
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "checks"))

import check_layout_drift  # noqa: E402


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_fig3_history_retains_the_v64_to_v66_collision_transfer() -> None:
    """A tracked receipt preserves the ignored historical report findings."""
    receipt = yaml.safe_load(
        HISTORICAL_LAYOUT_TRANSFER_RECEIPT.read_text(encoding="utf-8")
    )
    energy = "breadth_clear_of_declared_neighbors:energy_axis_label"

    assert receipt["schema"] == "figure-agent.historical-layout-transfer-receipt.v1"
    assert receipt["fixture"] == "fig3_resistance_mechanism"
    assert receipt["rule"] == {
        "id": energy,
        "minimum_clearance": 0.008,
    }
    assert receipt["never_recompile_historical_sources"] is True
    for version in ("v64", "v66"):
        record = receipt["versions"][version]
        source = FIG3_FIXTURE / record["source_path"]
        assert source.is_file()
        assert record["source_sha256"] == _sha256(source)
        assert record["ignored_layout_report_path"].endswith(
            f"execution-repair-{version}/build/layout_lanes.json"
        )
        assert record["ignored_layout_report_sha256"].startswith("sha256:")
    assert receipt["versions"]["v64"]["status"] == "ok"
    assert receipt["versions"]["v64"]["clearance"] == 0.019776
    assert receipt["versions"]["v66"]["status"] == "violation"
    assert receipt["versions"]["v66"]["clearance"] == 0.004272
    assert receipt["publication_acceptance"] == "not_claimed"


def test_fig3_layout_contract_is_fail_closed_for_missing_breadth_label() -> None:
    contract = yaml.safe_load(
        (FIG3_FIXTURE / "layout_lanes.yaml").read_text(encoding="utf-8")
    )
    words = [
        _word("trap", 100, 100, 120, 112),
        _word("energy", 122, 100, 150, 112),
        _word("E", 152, 100, 158, 112),
    ]

    payload = check_layout_drift.layout_lane_payload(
        contract,
        words,
        (400.0, 200.0),
        artifact_path=Path("next-layout-attempt/build/repaired_generated.pdf"),
    )

    assert payload.get("applicable", True) is True
    assert payload["failure_count"] == 2
    assert {result["status"] for result in payload["results"]} == {
        "missing_label_group"
    }


def test_fig3_layout_contract_does_not_rejudge_pre_v64_history() -> None:
    contract = yaml.safe_load(
        (FIG3_FIXTURE / "layout_lanes.yaml").read_text(encoding="utf-8")
    )

    payload = check_layout_drift.layout_lane_payload(
        contract,
        [],
        (400.0, 200.0),
        artifact_path=Path("execution-repair-v12/build/repaired_generated.pdf"),
    )

    assert payload["applicable"] is False
    assert payload["failure_count"] == 0
    assert payload["results"] == []


def test_fig3_layout_contract_still_checks_the_live_fixture_build() -> None:
    contract = yaml.safe_load(
        (FIG3_FIXTURE / "layout_lanes.yaml").read_text(encoding="utf-8")
    )

    payload = check_layout_drift.layout_lane_payload(
        contract,
        [],
        (400.0, 200.0),
        artifact_path=Path(
            "examples/fig3_resistance_mechanism/build/fig3_resistance_mechanism.pdf"
        ),
    )

    assert payload.get("applicable", True) is True
    assert payload["failure_count"] == 2
    assert {result["status"] for result in payload["results"]} == {
        "missing_label_group"
    }


def test_fig3_live_source_exposes_the_live_layout_relation_anchors() -> None:
    source = (FIG3_FIXTURE / "fig3_resistance_mechanism.tex").read_text(
        encoding="utf-8"
    )
    contract = yaml.safe_load(
        (FIG3_FIXTURE / "layout_lanes.yaml").read_text(encoding="utf-8")
    )
    phrases = {
        group["id"]: group["required_phrase"] for group in contract["label_groups"]
    }

    assert phrases == {
        "response_equation": "I(t)",
        "energy_axis_label": "energy, E",
        "energy_support_label": "energy support",
        "panel_c_heading": "composition-dependent",
        "sulfur_content_annotation": "sulfur content",
    }
    rules = {rule["id"]: rule for rule in contract["rules"]}
    assert rules["panel_c_heading_clear_of_sulfur_content_annotation"] == {
        "id": "panel_c_heading_clear_of_sulfur_content_annotation",
        "kind": "minimum_clearance",
        "first": "panel_c_heading",
        "second": "sulfur_content_annotation",
        "minimum_normalized_clearance": 0.015,
    }
    assert "qualitative CvS decay" not in source
    assert "not measured data" not in source
    assert "at (9.53,4.60) {c};" in source
    assert "at (9.87,4.60)" in source
    assert "at (12.24,4.13) {sulfur content $\\uparrow$};" in source
    assert "energy, $E$" in source
    assert "$\\rho_{60" not in source
    assert "$n$ = breadth" not in source


def test_fig3_layout_contract_applies_to_unfamiliar_future_artifact_names() -> None:
    contract = yaml.safe_load(
        (FIG3_FIXTURE / "layout_lanes.yaml").read_text(encoding="utf-8")
    )
    words = [
        _word("trap", 100, 100, 120, 112),
        _word("energy", 122, 100, 150, 112),
        _word("E", 152, 100, 158, 112),
    ]

    payload = check_layout_drift.layout_lane_payload(
        contract,
        words,
        (400.0, 200.0),
        artifact_path=Path("next-layout-attempt/build/candidate.pdf"),
    )

    assert payload.get("applicable", True) is True
    assert payload["failure_count"] == 2
    assert {result["status"] for result in payload["results"]} == {
        "missing_label_group"
    }


def test_direct_cli_reports_when_a_legacy_artifact_is_explicitly_excluded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    contract_path = tmp_path / "layout_lanes.yaml"
    contract_path.write_text(
        yaml.safe_dump(
            {
                "schema": "figure-agent.layout-lanes.v1",
                "exclude_path_regex": r"(?:^|/)legacy/",
                "label_groups": [],
                "rules": [],
            }
        ),
        encoding="utf-8",
    )
    pdf_path = tmp_path / "legacy" / "build" / "candidate.pdf"
    pdf_path.parent.mkdir(parents=True)
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    monkeypatch.setattr(
        check_layout_drift,
        "extract_pdf_words_and_page",
        lambda _path: ([], (400.0, 200.0)),
    )

    exit_code = check_layout_drift.main(
        [
            "--pdf",
            str(pdf_path),
            "--layout-contract",
            str(contract_path),
            "--strict",
        ]
    )

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == (
        "SKIP layout contract: artifact_path_matches_exclude_path_regex "
        f"for artifact {pdf_path}"
    )


def test_layout_contract_preserves_v1_include_path_compatibility() -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "applies_to_path_regex": r"(?:^|/)accepted/",
        "label_groups": [],
        "rules": [],
    }

    payload = check_layout_drift.layout_lane_payload(
        contract,
        [],
        (400.0, 200.0),
        artifact_path=Path("legacy/build/candidate.pdf"),
    )

    assert payload["applicable"] is False
    assert payload["exclusion_reason"] == "artifact_path_outside_applies_to_path_regex"


def test_fig3_strict_compile_does_not_rejudge_v64_to_v66_with_live_contract(
) -> None:
    receipt = yaml.safe_load(
        HISTORICAL_LAYOUT_TRANSFER_RECEIPT.read_text(encoding="utf-8")
    )
    contract = yaml.safe_load(
        (FIG3_FIXTURE / "layout_lanes.yaml").read_text(encoding="utf-8")
    )

    assert receipt["never_recompile_historical_sources"] is True
    for record in receipt["versions"].values():
        payload = check_layout_drift.layout_lane_payload(
            contract,
            [],
            (400.0, 200.0),
            artifact_path=Path(record["ignored_layout_report_path"]).with_name(
                "repaired_generated.pdf"
            ),
        )
        assert payload["applicable"] is False
        assert payload["failure_count"] == 0
        assert payload["results"] == []


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

    results = check_layout_drift.evaluate_layout_lanes(
        contract, words, (400.0, 200.0)
    )

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


def test_layout_contract_checks_one_moved_group_against_each_declared_neighbor() -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "label_groups": [
            {"id": "moved_label", "required_phrase": "distribution breadth"},
            {"id": "axis_label", "required_phrase": "trap energy E"},
            {"id": "magnitude_label", "required_phrase": "magnitude"},
        ],
        "rules": [
            {
                "id": "moved_label_neighbor_clearance",
                "kind": "minimum_clearance_from_groups",
                "group": "moved_label",
                "other_groups": ["axis_label", "magnitude_label"],
                "minimum_normalized_clearance": 0.01,
            }
        ],
    }
    words = [
        _word("distribution", 100, 100, 150, 112),
        _word("breadth", 152, 100, 182, 112),
        _word("trap", 140, 110, 160, 122),
        _word("energy", 162, 110, 190, 122),
        _word("E", 192, 110, 198, 122),
        _word("magnitude", 300, 100, 350, 112),
    ]

    results = check_layout_drift.evaluate_layout_lanes(contract, words, (400.0, 200.0))

    assert [(result.rule_id, result.status) for result in results] == [
        ("moved_label_neighbor_clearance:axis_label", "violation"),
        ("moved_label_neighbor_clearance:magnitude_label", "ok"),
    ]


def test_group_clearance_rule_fails_closed_or_explicitly_skips_missing_target() -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "label_groups": [
            {"id": "moved", "required_phrase": "distribution breadth"},
            {"id": "axis", "required_phrase": "trap energy E"},
            {"id": "magnitude", "required_phrase": "magnitude"},
        ],
        "rules": [
            {
                "id": "moved_neighbors",
                "kind": "minimum_clearance_from_groups",
                "group": "moved",
                "other_groups": ["axis", "magnitude"],
                "minimum_normalized_clearance": 0.01,
            }
        ],
    }
    words = [
        _word("trap", 10, 10, 30, 20),
        _word("energy", 32, 10, 60, 20),
        _word("E", 62, 10, 68, 20),
        _word("magnitude", 100, 10, 150, 20),
    ]

    failed = check_layout_drift.evaluate_layout_lanes(contract, words, (400, 200))
    contract["rules"][0]["missing_policy"] = "skip_rule"
    skipped = check_layout_drift.evaluate_layout_lanes(contract, words, (400, 200))

    assert [result.status for result in failed] == [
        "missing_label_group",
        "missing_label_group",
    ]
    assert all(result.missing_groups == ("moved",) for result in failed)
    assert [result.status for result in skipped] == [
        "not_applicable",
        "not_applicable",
    ]


@pytest.mark.parametrize(
    "other_groups",
    [["axis", "axis"], ["moved"], ["unknown"]],
)
def test_group_clearance_rule_rejects_invalid_neighbor_sets(
    other_groups: list[str],
) -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "label_groups": [
            {"id": "moved", "required_phrase": "distribution breadth"},
            {"id": "axis", "required_phrase": "trap energy E"},
        ],
        "rules": [
            {
                "id": "moved_neighbors",
                "kind": "minimum_clearance_from_groups",
                "group": "moved",
                "other_groups": other_groups,
                "minimum_normalized_clearance": 0.01,
            }
        ],
    }

    with pytest.raises(ValueError, match="group-clearance rule is invalid"):
        check_layout_drift.evaluate_layout_lanes(contract, [], (400, 200))


def test_layout_contract_rejects_colliding_expanded_result_ids() -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "label_groups": [
            {"id": "moved", "required_phrase": "distribution breadth"},
            {"id": "axis", "required_phrase": "trap energy E"},
        ],
        "rules": [
            {
                "id": "moved_neighbors",
                "kind": "minimum_clearance_from_groups",
                "group": "moved",
                "other_groups": ["axis"],
                "minimum_normalized_clearance": 0.01,
            },
            {
                "id": "moved_neighbors:axis",
                "kind": "minimum_clearance",
                "first": "moved",
                "second": "axis",
                "minimum_normalized_clearance": 0.01,
            },
        ],
    }

    with pytest.raises(ValueError, match="duplicate layout lane result id"):
        check_layout_drift.evaluate_layout_lanes(contract, [], (400, 200))


def test_layout_lane_rule_can_explicitly_skip_when_a_group_is_not_applicable() -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "label_groups": [
            {"id": "breadth", "required_phrase": "distribution breadth"},
            {"id": "axis", "required_phrase": "trap energy E"},
        ],
        "rules": [
            {
                "id": "breadth_clear_of_axis",
                "kind": "minimum_clearance",
                "first": "breadth",
                "second": "axis",
                "minimum_normalized_clearance": 0.01,
                "missing_policy": "skip_rule",
            }
        ],
    }

    axis_words = [
        _word("trap", 20, 20, 30, 30),
        _word("energy", 32, 20, 50, 30),
        _word("E", 52, 20, 58, 30),
    ]
    results = check_layout_drift.evaluate_layout_lanes(
        contract, axis_words, (100.0, 100.0)
    )

    assert results[0].status == "not_applicable"
    assert results[0].missing_groups == ("breadth",)
    assert check_layout_drift.layout_lane_payload(
        contract,
        axis_words,
        (100.0, 100.0),
    )["failure_count"] == 0


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


def test_layout_lane_contract_flags_text_outside_declared_panel_region() -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "label_groups": [{"id": "panel_a_title", "required_terms": ["Mechanism"]}],
        "regions": [
            {"id": "panel_a", "normalized_bbox": [0.0, 0.0, 0.5, 1.0]}
        ],
        "rules": [
            {
                "id": "panel_a_title_contained",
                "kind": "contained_in_region",
                "group": "panel_a_title",
                "region": "panel_a",
                "minimum_normalized_inset": 0.01,
            }
        ],
    }

    results = check_layout_drift.evaluate_layout_lanes(
        contract,
        [_word("Mechanism", 195, 20, 215, 30)],
        (400.0, 200.0),
    )

    assert results[0].status == "violation"
    assert results[0].clearance == -0.0375
    assert results[0].minimum_clearance == 0.01


def test_layout_lane_contract_flags_annotation_too_close_to_plot_region() -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "label_groups": [{"id": "decay_note", "required_terms": ["decays"]}],
        "regions": [
            {"id": "decay_plot", "normalized_bbox": [0.1, 0.2, 0.5, 0.8]}
        ],
        "rules": [
            {
                "id": "decay_note_clear_of_plot",
                "kind": "minimum_clearance_from_region",
                "group": "decay_note",
                "region": "decay_plot",
                "minimum_normalized_clearance": 0.02,
            }
        ],
    }

    results = check_layout_drift.evaluate_layout_lanes(
        contract,
        [_word("decays", 205, 100, 225, 110)],
        (400.0, 200.0),
    )

    assert results[0].status == "violation"
    assert results[0].clearance == 0.01118


def test_layout_contract_flags_panel_and_figure_text_budget_overflow() -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "label_groups": [],
        "regions": [
            {"id": "page", "normalized_bbox": [0.0, 0.0, 1.0, 1.0]},
            {"id": "panel_a", "normalized_bbox": [0.0, 0.0, 0.5, 1.0]},
        ],
        "text_budgets": [
            {"id": "figure_text", "region": "page", "maximum_words": 4},
            {"id": "panel_a_text", "region": "panel_a", "maximum_words": 2},
        ],
        "rules": [],
    }
    words = [
        _word("Applied", 10, 10, 40, 20),
        _word("bias", 42, 10, 60, 20),
        _word("trapping", 62, 10, 100, 20),
        _word("S60", 220, 10, 245, 20),
        _word("broad", 250, 10, 280, 20),
    ]

    results = check_layout_drift.evaluate_text_budgets(
        contract, words, (400.0, 200.0)
    )

    assert [(result.budget_id, result.status) for result in results] == [
        ("figure_text", "violation"),
        ("panel_a_text", "violation"),
    ]
    assert [(result.word_count, result.maximum_words) for result in results] == [
        (5, 4),
        (3, 2),
    ]


def test_layout_lane_payload_includes_text_budget_failures() -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "label_groups": [],
        "regions": [
            {"id": "page", "normalized_bbox": [0.0, 0.0, 1.0, 1.0]}
        ],
        "text_budgets": [
            {"id": "figure_text", "region": "page", "maximum_words": 1}
        ],
        "rules": [],
    }

    payload = check_layout_drift.layout_lane_payload(
        contract,
        [_word("too", 10, 10, 20, 20), _word("many", 22, 10, 40, 20)],
        (100.0, 100.0),
    )

    assert payload["failure_count"] == 1
    assert payload["text_budget_results"] == [
        {
            "budget_id": "figure_text",
            "status": "violation",
            "word_count": 2,
            "maximum_words": 1,
            "region": "page",
        }
    ]


def test_layout_contract_requires_phrase_inside_its_owned_panel_region() -> None:
    contract = {
        "schema": "figure-agent.layout-lanes.v1",
        "label_groups": [
            {
                "id": "panel_b_x_axis_label",
                "required_phrase": "trap energy E",
                "region": "panel_b",
            }
        ],
        "regions": [
            {"id": "panel_b", "normalized_bbox": [0.5, 0.0, 1.0, 1.0]}
        ],
        "rules": [
            {
                "id": "panel_b_x_axis_label_owned",
                "kind": "contained_in_region",
                "group": "panel_b_x_axis_label",
                "region": "panel_b",
                "minimum_normalized_inset": 0.005,
            }
        ],
    }
    clipped = [_word("trap", 380, 180, 400, 195)]
    complete = [
        _word("trap", 300, 180, 320, 195),
        _word("energy", 322, 180, 355, 195),
        _word("E", 357, 180, 365, 195),
    ]

    missing = check_layout_drift.evaluate_layout_lanes(
        contract, clipped, (400.0, 200.0)
    )
    present = check_layout_drift.evaluate_layout_lanes(
        contract, complete, (400.0, 200.0)
    )

    assert missing[0].status == "missing_label_group"
    assert missing[0].missing_groups == ("panel_b_x_axis_label",)
    assert present[0].status == "ok"
