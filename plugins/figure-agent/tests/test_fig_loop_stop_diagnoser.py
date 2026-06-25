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
    # Machinery invariant (stable as the figure is worked): every enumerated
    # sub-region is classified into exactly one of the seven causes, so the
    # histogram sums to the sub-region count. We do NOT pin a specific cause
    # here — fig2's stop-point legitimately moves as critique/adjudication
    # advance it. Specific-cause classification is pinned deterministically in
    # test_stop_cause_classify.py, not against the evolving real fixture.
    assert written["subregions"], "fig2 must enumerate at least one sub-region"
    assert sum(written["cause_histogram"].values()) == len(written["subregions"])
    for sub in written["subregions"]:
        assert sub["subregion_id"].startswith("sel:") or "#" in sub["subregion_id"]
        for ev in sub["evidence"]:
            assert ev["source_module"] and ev["source_ref"]


def test_diagnose_run_fig3_produces_consistent_report(fig3_run):
    # Same anti-pattern guard as the fig2 test: assert the diagnoser MACHINERY
    # is consistent on the real fixture (histogram sums to sub-region count),
    # not a transient cause value that moves as fig3 is worked. Cause-specific
    # behaviour lives in test_stop_cause_classify.py.
    report = diagnose_run("fig3_resistance_mechanism", fig3_run)
    assert report["schema"] == "figure-agent.stop-report.v1"
    assert report["subregions"], "fig3 must enumerate at least one sub-region"
    assert sum(report["cause_histogram"].values()) == len(report["subregions"])


def test_mirror_skipped_when_log_absent(fig2_run):
    # fig2 has no subregion_iteration_log.md -> mirror must not raise.
    diagnose_run("fig2_trap_design_space", fig2_run)  # no exception
    assert not (EXAMPLES / "fig2_trap_design_space" / "subregion_iteration_log.md").exists()
