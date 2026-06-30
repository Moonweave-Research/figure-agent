from __future__ import annotations

import json
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = (
    PLUGIN_ROOT
    / "docs"
    / "decision-packets"
    / "2026-06-30-wave-c"
    / "smoke_panel_spacing_demo.json"
)
DECISION_RECORD_PATH = (
    PLUGIN_ROOT
    / "docs"
    / "decision-records"
    / "2026-06-30-wave-c"
    / "smoke_panel_spacing_demo.json"
)
BENCHMARK_CONTRACT_PATH = (
    PLUGIN_ROOT / "examples" / "smoke_panel_spacing_demo" / "benchmark_contract.yaml"
)


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_smoke_panel_spacing_packet_matches_decision_record_boundary() -> None:
    packet = _read_json(PACKET_PATH)
    decision_record = _read_json(DECISION_RECORD_PATH)

    assert packet["schema"] == decision_record["packet_schema"]
    assert packet["fixture"] == decision_record["fixture"]
    assert packet["decision_kind"] == decision_record["decision_kind"]
    assert packet["source_queue_run_id"] == decision_record["queue_run_id"]
    assert packet["bounded_scope"]["mutation_boundary"] == decision_record["mutation_boundary"]
    assert "manuscript acceptance" in packet["risk"]["primary"]


def test_smoke_panel_spacing_packet_is_tied_to_benchmark_contract() -> None:
    packet = _read_json(PACKET_PATH)
    benchmark = yaml.safe_load(BENCHMARK_CONTRACT_PATH.read_text(encoding="utf-8"))
    state = packet["current_state"]

    assert state["benchmark_contract"] == (
        "examples/smoke_panel_spacing_demo/benchmark_contract.yaml"
    )
    assert state["primary_defect_class"] == benchmark["defect_class"]
    assert state["candidate_family"] in benchmark["candidate_families"]
    assert state["candidate_edit_class"] in benchmark["candidate_edit_classes"]
    assert state["detector_expectation"] == benchmark["expected_movement"][
        state["detector_metric"]
    ]
    assert "source_compile_failure" in benchmark["hard_regressions"]
    assert any(
        "write generated exports" in forbidden
        for forbidden in packet["bounded_scope"]["forbidden_adjustments"]
    )
