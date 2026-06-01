"""Loop-centered improvement orchestrator over fig_run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fig_driver  # noqa: E402
import fig_run  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.improve.v1"
DEFAULT_MAX_LOOPS = 10

STOP_OPTIONAL_IMPROVEMENT = "optional_improvement_available"
STOP_REPEATED_BOUNDARY = "repeated_boundary"


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


def run_improvement(
    name: str,
    *,
    goal: str,
    execute: bool = False,
    max_loops: int = DEFAULT_MAX_LOOPS,
    max_steps_per_loop: int = fig_run.DEFAULT_MAX_STEPS,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    if max_loops < 1:
        raise ValueError("max_loops must be >= 1")
    if max_steps_per_loop < 1:
        raise ValueError("max_steps_per_loop must be >= 1")

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
    return payload


def main(argv: list[str] | None = None, *, repo_root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(prog="fig_improve.py")
    parser.add_argument("name")
    parser.add_argument("--goal", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-loops", type=int, default=DEFAULT_MAX_LOOPS)
    parser.add_argument("--max-steps-per-loop", type=int, default=fig_run.DEFAULT_MAX_STEPS)
    args = parser.parse_args(argv)
    try:
        payload = run_improvement(
            args.name,
            goal=args.goal,
            execute=args.execute,
            max_loops=args.max_loops,
            max_steps_per_loop=args.max_steps_per_loop,
            repo_root=repo_root,
        )
    except ValueError as exc:
        print(f"fig_improve.py: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
