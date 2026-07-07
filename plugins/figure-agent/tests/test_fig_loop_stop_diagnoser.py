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


def test_run_loop_persists_stop_diagnosis_contract(fig2_run):
    iteration = json.loads((fig2_run / "iteration_001.json").read_text(encoding="utf-8"))
    manifest = json.loads((fig2_run / "run_manifest.json").read_text(encoding="utf-8"))

    assert (fig2_run / "stop_report.json").is_file()
    assert manifest["stop_report"] == "stop_report.json"
    assert iteration["stop_diagnosis"]["stop_report"] == "stop_report.json"
    assert set(iteration["stop_diagnosis"]) == {
        "stop_report",
        "dominant_premature_cause",
        "dominant_premature_count",
        "cause_histogram",
    }
    assert iteration["stop_routes"]
    first_route = iteration["stop_routes"][0]
    assert set(first_route) == {
        "subregion_id",
        "stop_cause",
        "fix_mode",
        "action",
        "payload",
        "blocked_by",
    }


def test_auto_remedy_executes_critique_scaffold_and_fails_loud_when_unchanged(
    tmp_path: Path,
) -> None:
    commands: list[list[str]] = []

    def runner(command: list[str], *, repo_root: Path) -> fig_loop.CommandResult:
        commands.append(command)
        return fig_loop.CommandResult(returncode=0, stdout="ok", stderr="")

    def diagnose(_name: str, _run_dir: Path, **_kwargs) -> dict:
        return {
            "subregions": [],
            "cause_histogram": {},
            "dominant_premature_cause": None,
            "dominant_premature_count": 0,
        }

    def status_reader(_example_dir: Path) -> dict:
        return {"critique_state": "MISSING"}

    remedy, _report = fig_loop._apply_auto_remedy(
        "fig2_trap_design_space",
        tmp_path,
        repo_root=tmp_path,
        status_result={"critique_state": "MISSING"},
        stop_report={"subregions": []},
        runner=runner,
        diagnose=diagnose,
        status_reader=status_reader,
    )

    assert commands == [
        [
            str(fig_loop.REPO_ROOT / "bin" / "fig-agent"),
            "critique-scaffold",
            "fig2_trap_design_space",
            "--json",
        ]
    ]
    assert remedy is not None
    assert remedy["cause"] == "critique_missing"
    assert remedy["status"] == "remedy_ineffective"


def test_auto_remedy_does_not_repeat_same_cause_in_one_run(tmp_path: Path) -> None:
    commands: list[list[str]] = []
    (tmp_path / "iteration_001.json").write_text(
        json.dumps(
            {
                "auto_remedy": {
                    "cause": "critique_missing",
                    "status": "remedy_ineffective",
                }
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    def runner(command: list[str], *, repo_root: Path) -> fig_loop.CommandResult:
        commands.append(command)
        return fig_loop.CommandResult(returncode=0, stdout="ok", stderr="")

    remedy, _report = fig_loop._apply_auto_remedy(
        "fig2_trap_design_space",
        tmp_path,
        repo_root=tmp_path,
        status_result={"critique_state": "MISSING"},
        stop_report={"subregions": []},
        runner=runner,
        diagnose=lambda *_args, **_kwargs: {},
        status_reader=lambda _example_dir: {"critique_state": "MISSING"},
    )

    assert commands == []
    assert remedy == {
        "cause": "critique_missing",
        "status": "remedy_ineffective",
        "reason": "auto_remedy_already_attempted_for_cause",
        "previous_status": "remedy_ineffective",
        "command_results": [],
    }


def test_auto_remedy_fails_closed_when_history_is_malformed(tmp_path: Path) -> None:
    commands: list[list[str]] = []
    (tmp_path / "iteration_001.json").write_text("{not-json", encoding="utf-8")

    def runner(command: list[str], *, repo_root: Path) -> fig_loop.CommandResult:
        commands.append(command)
        return fig_loop.CommandResult(returncode=0, stdout="ok", stderr="")

    remedy, _report = fig_loop._apply_auto_remedy(
        "fig2_trap_design_space",
        tmp_path,
        repo_root=tmp_path,
        status_result={"critique_state": "MISSING"},
        stop_report={"subregions": []},
        runner=runner,
        diagnose=lambda *_args, **_kwargs: {},
        status_reader=lambda _example_dir: {"critique_state": "MISSING"},
    )

    assert commands == []
    assert remedy is not None
    assert remedy["cause"] == "critique_missing"
    assert remedy["status"] == "remedy_ineffective"
    assert remedy["reason"] == "auto_remedy_history_unreadable"
    assert remedy["previous_status"] == "history_unreadable"
    assert remedy["command_results"] == []


def test_auto_remedy_reruns_compile_for_stale_detector_evidence(tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def runner(command: list[str], *, repo_root: Path) -> fig_loop.CommandResult:
        commands.append(command)
        return fig_loop.CommandResult(returncode=0, stdout="ok", stderr="")

    stale_report = {
        "subregions": [
            {
                "subregion_id": "sel:abc",
                "stop_cause": "decision_weak",
                "evidence": [{"signal_key": "stale_detector_evidence"}],
            }
        ],
        "cause_histogram": {"decision_weak": 1},
        "dominant_premature_cause": "decision_weak",
        "dominant_premature_count": 1,
    }

    def diagnose(_name: str, _run_dir: Path, **_kwargs) -> dict:
        return stale_report

    remedy, _report = fig_loop._apply_auto_remedy(
        "fig2_trap_design_space",
        tmp_path,
        repo_root=tmp_path,
        status_result={"critique_state": "FRESH"},
        stop_report=stale_report,
        runner=runner,
        diagnose=diagnose,
        status_reader=lambda _example_dir: {"critique_state": "FRESH"},
    )

    assert commands == [
        [
            str(fig_loop.REPO_ROOT / "bin" / "fig-agent"),
            "compile",
            "fig2_trap_design_space",
            "--strict",
        ]
    ]
    assert remedy is not None
    assert remedy["cause"] == "stale_detector_evidence"
    assert remedy["status"] == "remedy_ineffective"


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
