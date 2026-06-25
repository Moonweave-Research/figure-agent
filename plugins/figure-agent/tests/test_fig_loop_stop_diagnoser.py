# tests/test_fig_loop_stop_diagnoser.py
from __future__ import annotations

import json
from pathlib import Path

import fig_loop
import pytest
from fig_loop_stop_diagnoser import build_signal_bundle, diagnose_run, enumerate_subregions

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = PLUGIN_ROOT / "examples"


@pytest.fixture
def fig2_run(tmp_path):
    return fig_loop.run_loop("fig2_trap_design_space", "slice3 test", runs_root=tmp_path)


@pytest.fixture
def fig3_run(tmp_path):
    return fig_loop.run_loop("fig3_resistance_mechanism", "slice3 test", runs_root=tmp_path)


def test_enumerate_subregions_uses_real_string_keys(fig2_run):
    subregions = enumerate_subregions("fig2_trap_design_space", fig2_run)
    assert subregions, "fig2 must enumerate ledger sub-regions"
    for sub in subregions:
        assert sub.startswith("sel:") or "#" in sub  # real key forms only


def test_build_signal_bundle_reinvokes_candidate_set(fig2_run):
    bundle = build_signal_bundle("fig2_trap_design_space", fig2_run)
    assert "candidate_set" in bundle and "candidates" in bundle["candidate_set"]
    assert "refusals" in bundle["candidate_set"]
    assert "defects" in bundle
    assert "audit_evidence_summary" in bundle
    assert "raw_stop_reason" in bundle


def test_diagnose_run_writes_stop_report_v1(fig2_run):
    report = diagnose_run("fig2_trap_design_space", fig2_run)
    report_path = fig2_run / "stop_report.json"
    assert report_path.is_file()
    written = json.loads(report_path.read_text())
    assert written == report  # write_json round-trips the in-memory report
    assert written["schema"] == "figure-agent.stop-report.v1"
    assert set(written["cause_histogram"]) == {
        "gate_capped",
        "lever_exhausted",
        "decision_weak",
        "headroom_blind",
        "settled_verified",
        "plumbing_stop",
        "not_stopped",
    }
    assert written["dominant_premature_cause"] in (
        None,
        "gate_capped",
        "lever_exhausted",
        "decision_weak",
        "headroom_blind",
    )
    # fig2 sub-regions all carry stale_detector_evidence -> decision_weak.
    assert written["cause_histogram"]["decision_weak"] >= 1
    for sub in written["subregions"]:
        assert sub["subregion_id"].startswith("sel:") or "#" in sub["subregion_id"]
        for ev in sub["evidence"]:
            assert ev["source_module"] and ev["source_ref"]


def test_diagnose_run_fig3_is_lever_exhausted(fig3_run):
    report = diagnose_run("fig3_resistance_mechanism", fig3_run)
    assert report["cause_histogram"]["lever_exhausted"] >= 1


def test_mirror_skipped_when_log_absent(fig2_run):
    # fig2 has no subregion_iteration_log.md -> mirror must not raise.
    diagnose_run("fig2_trap_design_space", fig2_run)  # no exception
    assert not (EXAMPLES / "fig2_trap_design_space" / "subregion_iteration_log.md").exists()
