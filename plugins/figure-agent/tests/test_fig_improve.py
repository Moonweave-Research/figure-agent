from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fig_driver  # noqa: E402
import fig_improve  # noqa: E402
import fig_run  # noqa: E402


def _driver(
    *,
    action: str,
    safe_command: str | None = None,
    stop_boundary: str | None = None,
    ready_improvement_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "schema": fig_driver.SCHEMA,
        "fixture": "demo",
        "mode": "review",
        "goal": "improve",
        "status": {"render_state": "FRESH", "critique_state": "FRESH"},
        "action": action,
        "safe_command": safe_command,
        "stop_boundary": stop_boundary,
        "reason": "driver reason",
        "forbidden_actions": [],
        "workspace_warnings": [],
        "may_execute": False,
        "next_action_summary": {
            "action": action,
            "safe_command": safe_command,
            "required_actor": "workflow_agent",
        },
    }
    if ready_improvement_summary is not None:
        payload["ready_improvement_summary"] = ready_improvement_summary
    return payload


def _run_payload(
    *,
    final_action: str,
    final_stop_reason: str,
    final_stop_boundary: str | None = None,
    boundary_handoff: dict[str, Any] | None = None,
    ready_improvement_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    driver = _driver(
        action=final_action,
        stop_boundary=final_stop_boundary,
        ready_improvement_summary=ready_improvement_summary,
    )
    payload = {
        "schema": fig_run.SCHEMA,
        "fixture": "demo",
        "mode": "review",
        "goal": "improve",
        "execute": False,
        "max_steps": 5,
        "executable_actions": sorted(fig_run.EXECUTABLE_ACTIONS),
        "steps": [
            {
                "index": 1,
                "action": final_action,
                "safe_command": driver["safe_command"],
                "stop_boundary": final_stop_boundary,
                "would_execute": False,
                "executed": False,
                "stop_reason": final_stop_reason,
                "driver": driver,
            }
        ],
        "final_action": final_action,
        "final_safe_command": driver["safe_command"],
        "final_stop_boundary": final_stop_boundary,
        "final_stop_reason": final_stop_reason,
        "executed_count": 0,
    }
    if boundary_handoff is not None:
        payload["boundary_handoff"] = boundary_handoff
    return payload


def _boundary_handoff(
    *,
    action: str,
    stop_boundary: str | None,
    required_actor: str = "workflow_agent",
    closeout_checks: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "schema": fig_run.BOUNDARY_HANDOFF_SCHEMA,
        "action": action,
        "stop_boundary": stop_boundary,
        "required_actor": required_actor,
        "blocking_reason": "boundary reason",
        "evidence_refs": [f"driver.stop_boundary:{stop_boundary}"],
        "allowed_scope": ["read-only"],
        "forbidden_scope": ["hidden source edits"],
        "closeout_checks": closeout_checks or ["rerun live /fig_drive"],
        "continuation_guidance": {"rerun_live_driver_first": True},
    }


def _install_runs(
    monkeypatch: Any,
    runs: list[dict[str, Any]],
) -> list[tuple[str, bool, int]]:
    calls: list[tuple[str, bool, int]] = []

    def _fake_run_workflow(
        name: str,
        *,
        mode: str,
        goal: str,
        execute: bool = False,
        max_steps: int = fig_run.DEFAULT_MAX_STEPS,
        repo_root: Path = fig_run.REPO_ROOT,
    ) -> dict[str, Any]:
        calls.append((name, execute, max_steps))
        index = min(len(calls) - 1, len(runs) - 1)
        return dict(runs[index])

    monkeypatch.setattr(fig_improve, "_run_workflow", _fake_run_workflow)
    return calls


def test_improve_stops_at_host_critique_boundary(
    tmp_path: Path, monkeypatch: Any
) -> None:
    calls = _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_RUN_CRITIQUE,
                final_stop_reason=fig_run.STOP_HOST_BOUNDARY,
                final_stop_boundary=fig_driver.STOP_HOST_LLM_CRITIQUE,
            )
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        max_loops=10,
        repo_root=tmp_path,
    )

    assert calls == [("demo", True, fig_run.DEFAULT_MAX_STEPS)]
    assert payload["schema"] == "figure-agent.improve.v1"
    assert payload["final_stop_reason"] == "host_boundary"
    assert payload["final_required_actor"] == "host_llm"
    assert payload["next_operator_instruction"] == (
        "Run /fig_critique demo, then rerun /fig_improve."
    )
    assert payload["cycles"][0]["stop_reason"] == "host_boundary"


def test_improve_continues_after_safe_step_cap(
    tmp_path: Path, monkeypatch: Any
) -> None:
    calls = _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_RUN_COMPILE,
                final_stop_reason=fig_run.STOP_MAX_STEPS,
            ),
            _run_payload(
                final_action=fig_driver.ACTION_COMPLETE,
                final_stop_reason=fig_run.STOP_COMPLETE,
            ),
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        max_loops=3,
        max_steps_per_loop=1,
        repo_root=tmp_path,
    )

    assert calls == [("demo", True, 1), ("demo", True, 1)]
    assert payload["final_stop_reason"] == "complete"
    assert len(payload["cycles"]) == 2


def test_improve_reports_complete_without_optional_candidates(
    tmp_path: Path, monkeypatch: Any
) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_COMPLETE,
                final_stop_reason=fig_run.STOP_COMPLETE,
            )
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        repo_root=tmp_path,
    )

    assert payload["final_stop_reason"] == "complete"
    assert payload["final_required_actor"] == "none"
    assert payload["next_operator_instruction"] == "No required plugin action remains."


def test_aggressive_candidates_run_when_complete_if_flag_is_explicit(
    tmp_path: Path, monkeypatch: Any
) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_COMPLETE,
                final_stop_reason=fig_run.STOP_COMPLETE,
            )
        ],
    )
    candidate_calls: list[tuple[str, str, int, Path]] = []

    def _fake_candidate_runner(
        name: str,
        *,
        goal: str,
        max_iterations: int,
        repo_root: Path,
    ) -> dict[str, Any]:
        candidate_calls.append((name, goal, max_iterations, repo_root))
        return {
            "schema": "figure-agent.quality-search-execute.v0",
            "status": "dry_run_complete",
            "mode": "execute_dry_witness",
            "run_dir": ".scratch/quality-search-runs/demo-ready",
            "safety": {"source_mutation": "forbidden_in_dry_executor"},
            "decision": {
                "selected_candidate_id": "CAND007",
                "selected_family": "vector-clearance-offset",
            },
        }

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve detector-backed vector clearance",
        execute=True,
        repo_root=tmp_path,
        aggressive_candidates=True,
        candidate_iterations=2,
        candidate_runner=_fake_candidate_runner,
    )

    assert candidate_calls == [
        ("demo", "improve detector-backed vector clearance", 2, tmp_path)
    ]
    assert payload["final_stop_reason"] == "complete"
    assert payload["final_required_actor"] == "none"
    assert payload["aggressive_candidate_run"]["status"] == "dry_run_complete"
    assert payload["aggressive_candidate_run"]["selected_candidate_id"] == "CAND007"
    assert payload["aggressive_candidate_run"]["selected_family"] == (
        "vector-clearance-offset"
    )
    assert "Review aggressive_candidate_run" in payload["next_operator_instruction"]


def test_improve_surfaces_optional_improvement_candidates(
    tmp_path: Path, monkeypatch: Any
) -> None:
    ready_improvement = {
        "schema": "figure-agent.ready-improvement-summary.v1",
        "state": "ready_but_improvable",
        "safe_to_ship": True,
        "blocks_release": False,
        "auto_patch_allowed": False,
        "candidate_count": 1,
        "candidates": [{"id": "I001", "source": "editorial_art_direction_summary"}],
    }
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_COMPLETE,
                final_stop_reason=fig_run.STOP_COMPLETE,
                ready_improvement_summary=ready_improvement,
            )
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        repo_root=tmp_path,
    )

    assert payload["final_stop_reason"] == "optional_improvement_available"
    assert payload["final_required_actor"] == "workflow_agent"
    assert payload["ready_improvement_summary"] == ready_improvement
    assert "Review ready_improvement_summary.candidates" in payload["next_operator_instruction"]


def test_improve_plan_only_runs_one_cycle_without_execution(
    tmp_path: Path, monkeypatch: Any
) -> None:
    calls = _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_RUN_COMPILE,
                final_stop_reason=fig_run.STOP_PLAN_ONLY,
            )
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=False,
        max_loops=5,
        repo_root=tmp_path,
    )

    assert calls == [("demo", False, fig_run.DEFAULT_MAX_STEPS)]
    assert payload["final_stop_reason"] == "plan_only"
    assert payload["final_required_actor"] == "workflow_agent"
    assert len(payload["cycles"]) == 1


def test_improve_explains_reference_missing_boundary(
    tmp_path: Path, monkeypatch: Any
) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_RUN_CRITIQUE,
                final_stop_reason=fig_run.STOP_HOST_BOUNDARY,
                final_stop_boundary=fig_driver.STOP_REFERENCE_MISSING,
                boundary_handoff=_boundary_handoff(
                    action=fig_driver.ACTION_RUN_CRITIQUE,
                    stop_boundary=fig_driver.STOP_REFERENCE_MISSING,
                    closeout_checks=[
                        "fix reference path or provide reference image",
                        "rerun live /fig_drive",
                    ],
                ),
            )
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        repo_root=tmp_path,
    )

    assert payload["final_required_actor"] == "workflow_agent"
    assert payload["next_operator_instruction"] == (
        "Fix reference path or provide reference image, then rerun /fig_improve."
    )


def test_improve_explains_semantic_backport_boundary(
    tmp_path: Path, monkeypatch: Any
) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_POLISH_HANDOFF_STOP,
                final_stop_reason=fig_run.STOP_NOT_EXECUTABLE,
                final_stop_boundary=fig_driver.STOP_SEMANTIC_BACKPORT,
                boundary_handoff=_boundary_handoff(
                    action=fig_driver.ACTION_POLISH_HANDOFF_STOP,
                    stop_boundary=fig_driver.STOP_SEMANTIC_BACKPORT,
                    closeout_checks=[
                        "backport semantic changes to source/spec",
                        "rerun live /fig_drive",
                    ],
                ),
            )
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        repo_root=tmp_path,
    )

    assert payload["final_required_actor"] == "workflow_agent"
    assert payload["next_operator_instruction"] == (
        "Backport semantic changes to source/spec, then rerun /fig_improve."
    )


def test_improve_explains_deferred_patch_handoff_boundary(
    tmp_path: Path, monkeypatch: Any
) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_PATCH_HANDOFF_STOP,
                final_stop_reason=fig_run.STOP_NOT_EXECUTABLE,
                final_stop_boundary=fig_driver.STOP_PATCH_HANDOFF,
                boundary_handoff=_boundary_handoff(
                    action=fig_driver.ACTION_PATCH_HANDOFF_STOP,
                    stop_boundary=fig_driver.STOP_PATCH_HANDOFF,
                    closeout_checks=[
                        "verify patch executor currentness",
                        "rerun live /fig_drive",
                    ],
                ),
            )
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        repo_root=tmp_path,
    )

    assert payload["final_required_actor"] == "workflow_agent"
    assert payload["next_operator_instruction"] == (
        "Review the patch handoff and verify executor currentness before source "
        "mutation, then rerun /fig_improve."
    )


def test_improve_explains_closeout_boundary(
    tmp_path: Path, monkeypatch: Any
) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_RUN_FIG_LOOP,
                final_stop_reason=fig_run.STOP_NOT_EXECUTABLE,
                final_stop_boundary=fig_driver.STOP_CLOSEOUT,
                boundary_handoff=_boundary_handoff(
                    action=fig_driver.ACTION_RUN_FIG_LOOP,
                    stop_boundary=fig_driver.STOP_CLOSEOUT,
                    closeout_checks=[
                        "run uv run python3 scripts/fig_closeout.py demo --json",
                        "follow closeout.next_action",
                        "rerun live /fig_drive",
                    ],
                ),
            )
        ],
    )

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        repo_root=tmp_path,
    )

    assert payload["final_required_actor"] == "workflow_agent"
    assert payload["next_operator_instruction"] == (
        "Run fig_closeout.py for closeout guidance, then rerun /fig_improve."
    )


def test_improve_stops_on_repeated_boundary(
    tmp_path: Path, monkeypatch: Any
) -> None:
    run = _run_payload(
        final_action=fig_driver.ACTION_RUN_COMPILE,
        final_stop_reason=fig_run.STOP_MAX_STEPS,
    )
    _install_runs(monkeypatch, [run, run])

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        max_loops=3,
        repo_root=tmp_path,
    )

    assert payload["final_stop_reason"] == "repeated_boundary"
    assert payload["final_required_actor"] == "workflow_agent"
    assert len(payload["cycles"]) == 2


def test_aggressive_candidates_run_on_repeated_boundary(
    tmp_path: Path, monkeypatch: Any
) -> None:
    run = _run_payload(
        final_action=fig_driver.ACTION_RUN_COMPILE,
        final_stop_reason=fig_run.STOP_MAX_STEPS,
    )
    _install_runs(monkeypatch, [run, run])
    candidate_calls: list[tuple[str, str, int, Path]] = []

    def _fake_candidate_runner(
        name: str,
        *,
        goal: str,
        max_iterations: int,
        repo_root: Path,
    ) -> dict[str, Any]:
        candidate_calls.append((name, goal, max_iterations, repo_root))
        return {
            "schema": "figure-agent.quality-search-execute.v0",
            "status": "dry_run_complete",
            "mode": "execute_dry_witness",
            "run_dir": ".scratch/quality-search-runs/demo-run",
            "safety": {"source_mutation": "forbidden_in_dry_executor"},
            "decision": {"selected_candidate_id": "QS001"},
            "visual_evidence": {
                "state": "complete",
                "render_mode": "compile_export_crop_evaluate",
            },
            "candidate_scores": [
                {
                    "candidate_id": "QS001",
                    "family": "hierarchy_rebalance",
                    "operation_scale": "local_style_token",
                    "template_id": "line_width_minimum_v1",
                    "policy_score": 0.93,
                    "evidence_score": 0.85,
                },
                {
                    "candidate_id": "QS002",
                    "family": "apparatus_strengthen",
                    "operation_scale": "panel_block",
                    "template_id": "v5f_panel_f_redraw_overlay_v1",
                    "policy_score": 0.92,
                    "evidence_score": 0.81,
                },
            ],
        }

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        max_loops=3,
        repo_root=tmp_path,
        aggressive_candidates=True,
        candidate_iterations=2,
        candidate_runner=_fake_candidate_runner,
    )

    assert candidate_calls == [("demo", "improve", 2, tmp_path)]
    assert payload["final_stop_reason"] == "repeated_boundary"
    assert payload["aggressive_candidate_run"]["status"] == "dry_run_complete"
    assert payload["aggressive_candidate_run"]["source_mutation"] == (
        "forbidden_in_dry_executor"
    )
    assert payload["aggressive_candidate_run"]["selected_candidate_id"] == "QS001"
    assert payload["aggressive_candidate_run"]["render_mode"] == (
        "compile_export_crop_evaluate"
    )
    assert payload["aggressive_candidate_run"]["competitive_candidates"][1] == {
        "candidate_id": "QS002",
        "family": "apparatus_strengthen",
        "operation_scale": "panel_block",
        "template_id": "v5f_panel_f_redraw_overlay_v1",
        "policy_score": 0.92,
        "evidence_score": 0.81,
    }
    assert "Review aggressive_candidate_run" in payload["next_operator_instruction"]


def test_aggressive_candidates_do_not_run_for_release_operator(
    tmp_path: Path, monkeypatch: Any
) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_RELEASE_BLOCKED,
                final_stop_reason=fig_run.STOP_NOT_EXECUTABLE,
                final_stop_boundary=fig_driver.STOP_ACCEPTED_OR_FINAL_READY,
            )
        ],
    )

    def _unexpected_candidate_runner(
        name: str,
        *,
        goal: str,
        max_iterations: int,
        repo_root: Path,
    ) -> dict[str, Any]:
        raise AssertionError("release boundaries must not run aggressive candidates")

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        repo_root=tmp_path,
        aggressive_candidates=True,
        candidate_runner=_unexpected_candidate_runner,
    )

    assert "aggressive_candidate_run" not in payload
    assert payload["final_required_actor"] == "release_operator"


def test_aggressive_candidates_run_on_basin_complete_boundary(
    tmp_path: Path, monkeypatch: Any
) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_COMPLETE,
                final_stop_reason=fig_run.STOP_COMPLETE,
                final_stop_boundary="basin_detected",
            )
        ],
    )

    def _fake_candidate_runner(
        name: str,
        *,
        goal: str,
        max_iterations: int,
        repo_root: Path,
    ) -> dict[str, Any]:
        return {
            "status": "dry_run_complete",
            "mode": "execute_dry_witness",
            "run_dir": ".scratch/quality-search-runs/demo-basin",
            "safety": {
                "source_mutation": "forbidden_in_dry_executor",
                "accepted_golden_release_mutation": (
                    "forbidden_without_explicit_human_approval"
                ),
            },
            "decision": {"selected_candidate_id": "QS003"},
        }

    payload = fig_improve.run_improvement(
        "demo",
        goal="improve",
        execute=True,
        repo_root=tmp_path,
        aggressive_candidates=True,
        candidate_runner=_fake_candidate_runner,
    )

    assert payload["final_stop_reason"] == "complete"
    assert payload["aggressive_candidate_run"]["run_dir"].endswith("demo-basin")
    assert payload["aggressive_candidate_run"]["selected_candidate_id"] == "QS003"


def test_main_accepts_aggressive_candidates_flag(
    tmp_path: Path, monkeypatch: Any, capsys: Any
) -> None:
    run = _run_payload(
        final_action=fig_driver.ACTION_HUMAN_GATE_STOP,
        final_stop_reason=fig_run.STOP_NOT_EXECUTABLE,
    )
    _install_runs(monkeypatch, [run])

    def _fake_candidate_runner(
        name: str,
        *,
        goal: str,
        max_iterations: int,
        repo_root: Path,
    ) -> dict[str, Any]:
        return {
            "status": "dry_run_complete",
            "mode": "execute_dry_witness",
            "run_dir": ".scratch/quality-search-runs/demo-run",
            "safety": {"source_mutation": "forbidden_in_dry_executor"},
            "decision": {"selected_candidate_id": "QS002"},
        }

    monkeypatch.setattr(fig_improve, "_run_aggressive_candidate_search", _fake_candidate_runner)

    result = fig_improve.main(
        [
            "demo",
            "--goal",
            "improve",
            "--aggressive-candidates",
            "--candidate-iterations",
            "3",
        ],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["aggressive_candidate_run"]["selected_candidate_id"] == "QS002"


def test_main_rejects_invalid_max_loops(
    tmp_path: Path, capsys: Any
) -> None:
    result = fig_improve.main(
        ["demo", "--goal", "improve", "--max-loops", "0"],
        repo_root=tmp_path,
    )

    captured = capsys.readouterr()
    assert result == 2
    assert "max_loops must be >= 1" in captured.err


def test_main_emits_json(tmp_path: Path, monkeypatch: Any, capsys: Any) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_COMPLETE,
                final_stop_reason=fig_run.STOP_COMPLETE,
            )
        ],
    )

    result = fig_improve.main(["demo", "--goal", "improve"], repo_root=tmp_path)

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.improve.v1"
    assert payload["fixture"] == "demo"


def test_main_accepts_format_json_alias(
    tmp_path: Path, monkeypatch: Any, capsys: Any
) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_COMPLETE,
                final_stop_reason=fig_run.STOP_COMPLETE,
            )
        ],
    )

    result = fig_improve.main(
        ["demo", "--goal", "improve", "--format", "json"],
        repo_root=tmp_path,
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.improve.v1"
    assert payload["fixture"] == "demo"


def test_main_accepts_json_noop_flag(
    tmp_path: Path, monkeypatch: Any, capsys: Any
) -> None:
    _install_runs(
        monkeypatch,
        [
            _run_payload(
                final_action=fig_driver.ACTION_COMPLETE,
                final_stop_reason=fig_run.STOP_COMPLETE,
            )
        ],
    )

    result = fig_improve.main(["demo", "--goal", "improve", "--json"], repo_root=tmp_path)

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "figure-agent.improve.v1"
    assert payload["fixture"] == "demo"
