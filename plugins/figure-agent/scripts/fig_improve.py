"""Loop-centered improvement orchestrator over fig_run."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "quality"))

import fig_driver  # noqa: E402
import fig_run  # noqa: E402
import runtime_paths  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.improve.v1"
DEFAULT_MAX_LOOPS = 10

STOP_OPTIONAL_IMPROVEMENT = "optional_improvement_available"
STOP_REPEATED_BOUNDARY = "repeated_boundary"
CandidateRunner = Callable[..., dict[str, Any]]


def _run_workflow(
    name: str,
    *,
    mode: str,
    goal: str,
    execute: bool = False,
    max_steps: int = fig_run.DEFAULT_MAX_STEPS,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    return fig_run.run_workflow(
        name,
        mode=mode,
        goal=goal,
        execute=execute,
        max_steps=max_steps,
        repo_root=repo_root,
    )


def _final_driver(run_payload: dict[str, Any]) -> dict[str, Any]:
    steps = run_payload.get("steps")
    if not isinstance(steps, list) or not steps:
        return {}
    last_step = steps[-1]
    if not isinstance(last_step, dict):
        return {}
    driver = last_step.get("driver")
    return driver if isinstance(driver, dict) else {}


def _ready_improvement_summary(driver: dict[str, Any]) -> dict[str, Any] | None:
    summary = driver.get("ready_improvement_summary")
    return summary if isinstance(summary, dict) else None


def _has_optional_improvements(driver: dict[str, Any]) -> bool:
    summary = _ready_improvement_summary(driver)
    return isinstance(summary, dict) and summary.get("state") == "ready_but_improvable"


def _classify_stop(run_payload: dict[str, Any]) -> str:
    driver = _final_driver(run_payload)
    stop_reason = str(run_payload.get("final_stop_reason") or "")
    if stop_reason == fig_run.STOP_COMPLETE and _has_optional_improvements(driver):
        return STOP_OPTIONAL_IMPROVEMENT
    return stop_reason


def _required_actor(run_payload: dict[str, Any], stop_reason: str) -> str:
    if stop_reason == fig_run.STOP_COMPLETE:
        return "none"
    if stop_reason == STOP_OPTIONAL_IMPROVEMENT:
        return "workflow_agent"
    boundary = run_payload.get("boundary_handoff")
    if isinstance(boundary, dict):
        actor = boundary.get("required_actor")
        if isinstance(actor, str) and actor.strip():
            return actor.strip()
    action = run_payload.get("final_action")
    stop_boundary = run_payload.get("final_stop_boundary")
    if stop_reason == fig_run.STOP_HOST_BOUNDARY or action == fig_driver.ACTION_RUN_CRITIQUE:
        return "host_llm"
    if action == fig_driver.ACTION_HUMAN_GATE_STOP:
        return "human"
    if action == fig_driver.ACTION_POLISH_HANDOFF_STOP:
        return "svg_editor"
    if action == fig_driver.ACTION_RELEASE_BLOCKED or stop_boundary in {
        fig_driver.STOP_ACCEPTED_OR_FINAL_READY,
        fig_driver.STOP_FORCE_GOLDEN,
    }:
        return "release_operator"
    return "workflow_agent"


def _boundary_handoff(run_payload: dict[str, Any]) -> dict[str, Any]:
    handoff = run_payload.get("boundary_handoff")
    return handoff if isinstance(handoff, dict) else {}


def _closeout_checks(run_payload: dict[str, Any]) -> list[str]:
    handoff = _boundary_handoff(run_payload)
    checks = handoff.get("closeout_checks")
    if isinstance(checks, list) and all(isinstance(item, str) for item in checks):
        return [item for item in checks if item.strip()]
    return []


def _instruction(
    name: str, stop_reason: str, actor: str, run_payload: dict[str, Any]
) -> str:
    stop_boundary = run_payload.get("final_stop_boundary")
    action = run_payload.get("final_action")
    closeout_checks = _closeout_checks(run_payload)
    if stop_reason == fig_run.STOP_COMPLETE:
        return "No required plugin action remains."
    if stop_reason == STOP_OPTIONAL_IMPROVEMENT:
        return (
            "Review ready_improvement_summary.candidates and choose at most one "
            "optional polish target before rerunning /fig_improve."
        )
    if stop_boundary == fig_driver.STOP_REFERENCE_MISSING:
        return "Fix reference path or provide reference image, then rerun /fig_improve."
    if stop_boundary == fig_driver.STOP_SEMANTIC_BACKPORT:
        return "Backport semantic changes to source/spec, then rerun /fig_improve."
    if action == fig_driver.ACTION_PATCH_HANDOFF_STOP or stop_boundary in {
        fig_driver.STOP_PATCH_HANDOFF,
        fig_driver.STOP_AMBIGUOUS_PATCH,
    }:
        return (
            "Review the patch handoff and verify executor currentness before source "
            "mutation, then rerun /fig_improve."
        )
    if stop_boundary == fig_driver.STOP_CLOSEOUT:
        if any("fig_closeout.py" in check for check in closeout_checks):
            return "Run fig_closeout.py for closeout guidance, then rerun /fig_improve."
        return "Complete the listed closeout checks, then rerun /fig_improve."
    if actor == "host_llm":
        return f"Run /fig_critique {name}, then rerun /fig_improve."
    if actor == "human":
        return "Record the required human decision, then rerun /fig_improve."
    if actor == "svg_editor":
        return "Follow the SVG polish handoff; do not edit source under polish mode."
    if actor == "release_operator":
        return "Resolve the release, accepted, or golden gate explicitly."
    if stop_reason == STOP_REPEATED_BOUNDARY:
        return "Repeated boundary detected; inspect the latest cycle before continuing."
    if stop_reason == fig_run.STOP_PLAN_ONLY:
        return "Run again with --execute to perform safe mechanical steps."
    if stop_reason == fig_run.STOP_MAX_STEPS:
        return "Reached the loop cap; inspect the final cycle before continuing."
    return "Inspect the final cycle and rerun live /fig_status or /fig_drive."


def _aggressive_candidate_instruction(candidate_run: dict[str, Any]) -> str:
    run_dir = candidate_run.get("run_dir")
    if isinstance(run_dir, str) and run_dir.strip():
        return (
            "Review aggressive_candidate_run and rendered quality-search artifacts "
            f"at {run_dir}; source mutation remains forbidden until explicit apply."
        )
    return (
        "Review aggressive_candidate_run; source mutation remains forbidden until "
        "explicit apply."
    )


def _cycle_payload(index: int, run_payload: dict[str, Any], stop_reason: str) -> dict[str, Any]:
    return {
        "index": index,
        "run": run_payload,
        "stop_reason": stop_reason,
        "required_actor": _required_actor(run_payload, stop_reason),
    }


def _boundary_signature(run_payload: dict[str, Any], stop_reason: str) -> tuple[Any, ...]:
    return (
        stop_reason,
        run_payload.get("final_action"),
        run_payload.get("final_stop_boundary"),
        run_payload.get("final_safe_command"),
    )


def _should_run_aggressive_candidates(
    run_payload: dict[str, Any],
    *,
    stop_reason: str,
    actor: str,
) -> bool:
    stop_boundary = run_payload.get("final_stop_boundary")
    if stop_boundary == "basin_detected":
        return True
    if stop_reason in {fig_run.STOP_COMPLETE, STOP_OPTIONAL_IMPROVEMENT}:
        return False
    if actor in {"release_operator", "host_llm", "svg_editor"}:
        return False
    if stop_boundary in {
        fig_driver.STOP_ACCEPTED_OR_FINAL_READY,
        fig_driver.STOP_FORCE_GOLDEN,
        fig_driver.STOP_REFERENCE_MISSING,
        fig_driver.STOP_SEMANTIC_BACKPORT,
        fig_driver.STOP_PATCH_HANDOFF,
        fig_driver.STOP_AMBIGUOUS_PATCH,
    }:
        return False
    return stop_reason == STOP_REPEATED_BOUNDARY or actor == "human"


def _run_aggressive_candidate_search(
    name: str,
    *,
    goal: str,
    max_iterations: int,
    repo_root: Path,
) -> dict[str, Any]:
    import quality_search  # noqa: PLC0415

    return quality_search.build_quality_search_execution(
        name,
        goal=goal,
        max_iterations=max_iterations,
        workspace_root=repo_root,
    )


def _candidate_run_summary(candidate_run: dict[str, Any]) -> dict[str, Any]:
    decision = candidate_run.get("decision")
    safety = candidate_run.get("safety")
    specs = candidate_run.get("candidate_specs")
    scores = candidate_run.get("candidate_scores")
    visual_evidence = candidate_run.get("visual_evidence")
    summary: dict[str, Any] = {
        "schema": "figure-agent.improve.aggressive-candidate-run.v1",
        "status": candidate_run.get("status"),
        "mode": candidate_run.get("mode"),
        "run_dir": candidate_run.get("run_dir"),
        "source_mutation": None,
        "selected_candidate_id": None,
        "selected_family": None,
        "candidate_count": None,
        "visual_evidence_status": None,
        "render_mode": None,
        "competitive_candidates": [],
    }
    if isinstance(safety, dict):
        summary["source_mutation"] = safety.get("source_mutation")
        summary["accepted_golden_release_mutation"] = safety.get(
            "accepted_golden_release_mutation"
        )
    if isinstance(decision, dict):
        summary["selected_candidate_id"] = decision.get("selected_candidate_id")
        summary["selected_family"] = decision.get("selected_family")
    if isinstance(specs, list):
        summary["candidate_count"] = len(specs)
    if isinstance(visual_evidence, dict):
        summary["visual_evidence_status"] = (
            visual_evidence.get("status") or visual_evidence.get("state")
        )
        summary["render_mode"] = visual_evidence.get("render_mode")
    if isinstance(scores, list):
        summary["competitive_candidates"] = [
            {
                "candidate_id": item.get("candidate_id"),
                "family": item.get("family"),
                "operation_scale": item.get("operation_scale"),
                "template_id": item.get("template_id"),
                "policy_score": item.get("policy_score"),
                "evidence_score": item.get("evidence_score"),
            }
            for item in scores[:5]
            if isinstance(item, dict)
        ]
    return summary


def run_improvement(
    name: str,
    *,
    goal: str,
    execute: bool = False,
    max_loops: int = DEFAULT_MAX_LOOPS,
    max_steps_per_loop: int = fig_run.DEFAULT_MAX_STEPS,
    repo_root: Path = REPO_ROOT,
    aggressive_candidates: bool = False,
    candidate_iterations: int = 1,
    candidate_runner: CandidateRunner | None = None,
) -> dict[str, Any]:
    if max_loops < 1:
        raise ValueError("max_loops must be >= 1")
    if max_steps_per_loop < 1:
        raise ValueError("max_steps_per_loop must be >= 1")
    if candidate_iterations < 1:
        raise ValueError("candidate_iterations must be >= 1")

    cycles: list[dict[str, Any]] = []
    seen_boundaries: set[tuple[Any, ...]] = set()
    final_stop_reason = fig_run.STOP_MAX_STEPS

    for index in range(1, max_loops + 1):
        run_payload = _run_workflow(
            name,
            mode="review",
            goal=goal,
            execute=execute,
            max_steps=max_steps_per_loop,
            repo_root=repo_root,
        )
        stop_reason = _classify_stop(run_payload)
        signature = _boundary_signature(run_payload, stop_reason)
        if signature in seen_boundaries:
            stop_reason = STOP_REPEATED_BOUNDARY
        seen_boundaries.add(signature)
        cycles.append(_cycle_payload(index, run_payload, stop_reason))
        final_stop_reason = stop_reason
        if stop_reason == STOP_REPEATED_BOUNDARY:
            break
        if stop_reason != fig_run.STOP_MAX_STEPS:
            break
    final_cycle = cycles[-1]
    final_run = final_cycle["run"]
    final_driver = _final_driver(final_run)
    ready_improvement = _ready_improvement_summary(final_driver)
    final_actor = final_cycle["required_actor"]
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "fixture": name,
        "mode": "review",
        "goal": goal,
        "execute": execute,
        "max_loops": max_loops,
        "max_steps_per_loop": max_steps_per_loop,
        "cycles": cycles,
        "final_stop_reason": final_stop_reason,
        "final_required_actor": final_actor,
        "final_action": final_run.get("final_action"),
        "final_stop_boundary": final_run.get("final_stop_boundary"),
        "next_operator_instruction": _instruction(
            name, final_stop_reason, final_actor, final_run
        ),
    }
    if ready_improvement is not None:
        payload["ready_improvement_summary"] = ready_improvement
    if aggressive_candidates and _should_run_aggressive_candidates(
        final_run,
        stop_reason=final_stop_reason,
        actor=final_actor,
    ):
        runner = candidate_runner or _run_aggressive_candidate_search
        candidate_run = runner(
            name,
            goal=goal,
            max_iterations=candidate_iterations,
            repo_root=repo_root,
        )
        candidate_summary = _candidate_run_summary(candidate_run)
        payload["aggressive_candidate_run"] = candidate_summary
        payload["next_operator_instruction"] = _aggressive_candidate_instruction(
            candidate_summary
        )
    return payload


def main(argv: list[str] | None = None, *, repo_root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(prog="fig_improve.py")
    parser.add_argument("name")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-loops", type=int, default=DEFAULT_MAX_LOOPS)
    parser.add_argument("--max-steps-per-loop", type=int, default=fig_run.DEFAULT_MAX_STEPS)
    parser.add_argument("--aggressive-candidates", action="store_true")
    parser.add_argument("--candidate-iterations", type=int, default=1)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args(argv)
    try:
        resolved_repo_root = (
            runtime_paths.resolve_runtime_paths().workspace_root
            if repo_root == REPO_ROOT
            else repo_root
        )
        payload = run_improvement(
            args.name,
            goal=args.goal,
            execute=args.execute,
            max_loops=args.max_loops,
            max_steps_per_loop=args.max_steps_per_loop,
            repo_root=resolved_repo_root,
            aggressive_candidates=args.aggressive_candidates,
            candidate_iterations=args.candidate_iterations,
        )
    except ValueError as exc:
        print(f"fig_improve.py: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
