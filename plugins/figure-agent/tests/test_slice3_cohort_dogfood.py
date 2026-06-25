# tests/test_slice3_cohort_dogfood.py
from __future__ import annotations

from pathlib import Path

import fig_loop
from dogfood_metrics import is_degenerate, load_cohort, roll_up_run_dirs
from fig_loop_stop_diagnoser import diagnose_run

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
COHORT = PLUGIN_ROOT / "scripts" / "dogfood_cohort.json"


def test_cohort_dogfood_gate_is_non_degenerate(tmp_path):
    cohort = load_cohort(COHORT)
    # Run the active-improvement set (fig2, fig3); fig1 is the recorded anchor.
    active = ["fig2_trap_design_space", "fig3_resistance_mechanism"]
    assert all(fixture in cohort["fixtures"] for fixture in active)
    run_dirs: list[Path] = []
    for fixture in active:
        run_dir = fig_loop.run_loop(fixture, "slice3 cohort dogfood", runs_root=tmp_path)
        diagnose_run(fixture, run_dir)
        assert (run_dir / "stop_report.json").is_file()
        run_dirs.append(run_dir)

    summary = roll_up_run_dirs(run_dirs)
    # Empirical (this branch): fig2 -> decision_weak, fig3 -> lever_exhausted.
    assert summary["dominant_premature_cause"] is not None, (
        "GATE FAILED: cohort produced no quality cause — fix plumbing/setup first. "
        f"histogram={summary['cohort_histogram']}"
    )
    assert is_degenerate(summary) is False
    assert summary["cohort_histogram"]["decision_weak"] >= 1
    assert summary["cohort_histogram"]["lever_exhausted"] >= 1


def test_fig1_anchor_run_also_diagnoses(tmp_path):
    run_dir = fig_loop.run_loop(
        "fig1_overview_v2_pair_001_vault", "slice3 anchor", runs_root=tmp_path
    )
    report = diagnose_run("fig1_overview_v2_pair_001_vault", run_dir)
    assert report["schema"] == "figure-agent.stop-report.v1"
    # fig1 has a real subregion_iteration_log.md; mirror of dominant rows is allowed.
    assert set(report["cause_histogram"]) == {
        "gate_capped",
        "lever_exhausted",
        "decision_weak",
        "headroom_blind",
        "settled_verified",
        "plumbing_stop",
        "not_stopped",
    }
