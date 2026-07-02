# tests/test_dogfood_metrics.py
from __future__ import annotations

import json
from pathlib import Path

from dogfood_metrics import (
    is_degenerate,
    load_cohort,
    main,
    roll_up_run_dirs,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _write_report(run_dir: Path, histogram: dict[str, int], dominant):
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "stop_report.json").write_text(
        json.dumps(
            {
                "schema": "figure-agent.stop-report.v1",
                "cause_histogram": histogram,
                "dominant_premature_cause": dominant,
            }
        ),
        encoding="utf-8",
    )


def _hist(**kw):
    base = {
        "gate_capped": 0,
        "lever_exhausted": 0,
        "decision_weak": 0,
        "headroom_blind": 0,
        "settled_verified": 0,
        "plumbing_stop": 0,
        "not_stopped": 0,
    }
    base.update(kw)
    return base


def test_cohort_json_lists_three_verified_fixtures():
    cohort = load_cohort(PLUGIN_ROOT / "scripts" / "dogfood_cohort.json")
    assert cohort["fixtures"] == [
        "fig1_overview_v2_pair_001_vault",
        "fig2_trap_design_space",
        "fig3_resistance_mechanism",
    ]
    assert cohort["regression_anchor"] == "fig1_overview_v2_pair_001_vault"


def test_roll_up_sums_histograms_and_finds_dominant(tmp_path):
    _write_report(tmp_path / "r1", _hist(decision_weak=3), "decision_weak")
    _write_report(tmp_path / "r2", _hist(decision_weak=1, lever_exhausted=2), "decision_weak")
    summary = roll_up_run_dirs([tmp_path / "r1", tmp_path / "r2"])
    assert summary["cohort_histogram"]["decision_weak"] == 4
    assert summary["cohort_histogram"]["lever_exhausted"] == 2
    assert summary["dominant_premature_cause"] == "decision_weak"


def test_degenerate_when_all_plumbing(tmp_path):
    _write_report(tmp_path / "r1", _hist(plumbing_stop=5), None)
    summary = roll_up_run_dirs([tmp_path / "r1"])
    assert is_degenerate(summary) is True
    assert summary["dominant_premature_cause"] is None


def test_degenerate_when_all_settled(tmp_path):
    _write_report(tmp_path / "r1", _hist(settled_verified=5), None)
    summary = roll_up_run_dirs([tmp_path / "r1"])
    assert is_degenerate(summary) is True


def test_non_degenerate_with_quality_cause(tmp_path):
    _write_report(tmp_path / "r1", _hist(decision_weak=2, plumbing_stop=3), "decision_weak")
    summary = roll_up_run_dirs([tmp_path / "r1"])
    assert is_degenerate(summary) is False


def test_check_exit_nonzero_on_degenerate(tmp_path):
    _write_report(tmp_path / "r1", _hist(plumbing_stop=5), None)
    code = main(["--check", "--run-dir", str(tmp_path / "r1")])
    assert code == 1


def test_check_exit_zero_on_non_degenerate(tmp_path):
    _write_report(tmp_path / "r1", _hist(decision_weak=2), "decision_weak")
    code = main(["--check", "--run-dir", str(tmp_path / "r1")])
    assert code == 0
