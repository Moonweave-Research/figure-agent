"""Bounded batch runner over the read-only fixture queue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fig_driver  # noqa: E402
import fig_queue  # noqa: E402
import fig_run  # noqa: E402
import runtime_paths  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.queue-run.v1"
DEFAULT_MAX_FIXTURES = 10
QUEUE_FILTER_KEYS = fig_queue._FILTER_KEYS


def _planned_run(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "fixture": item.get("fixture"),
        "action": item.get("action"),
        "safe_command": item.get("safe_command"),
        "would_execute": True,
        "executed": False,
        "result": None,
    }


def _executed_run(
    item: dict[str, Any],
    *,
    mode: str,
    goal: str,
    execute: bool,
    max_steps: int,
    repo_root: Path,
) -> dict[str, Any]:
    fixture = item.get("fixture")
    if not isinstance(fixture, str) or not fixture:
        return _planned_run(item) | {
            "would_execute": False,
            "stop_reason": "invalid_fixture",
        }
    result = fig_run.run_workflow(
        fixture,
        mode=mode,
        goal=goal,
        execute=execute,
        max_steps=max_steps,
        repo_root=repo_root,
    )
    return {
        "fixture": fixture,
        "action": item.get("action"),
        "safe_command": item.get("safe_command"),
        "would_execute": True,
        "executed": execute,
        "result": result,
    }


def _summary(
    *,
    command_plan: dict[str, Any],
    runs: list[dict[str, Any]],
) -> dict[str, int]:
    executed_commands = 0
    failed = 0
    for run in runs:
        result = run.get("result")
        if not isinstance(result, dict):
            continue
        executed_count = result.get("executed_count")
        if isinstance(executed_count, int) and not isinstance(executed_count, bool):
            executed_commands += executed_count
        if result.get("final_stop_reason") == fig_run.STOP_COMMAND_FAILED:
            failed += 1
    planned_executable = int(command_plan.get("executable_count", 0))
    attempted = len(runs)
    return {
        "planned_executable": planned_executable,
        "planned_blocked": int(command_plan.get("blocked_count", 0)),
        "planned_complete": int(command_plan.get("complete_count", 0)),
        "attempted": attempted,
        "executed_commands": executed_commands,
        "failed": failed,
        "blocked": int(command_plan.get("blocked_count", 0)),
        "unattempted_executable": max(planned_executable - attempted, 0),
    }


def _queue_filters_from_args(args: argparse.Namespace) -> dict[str, str | None]:
    values = {
        "required_actor": args.required_actor,
        "action": args.action,
        "stop_boundary": args.stop_boundary,
        "first_blocker": args.first_blocker,
        "blocking_source": args.blocking_source,
        "svg_polish_gate_state": args.svg_polish_gate_state,
        "can_start_svg_polish": args.can_start_svg_polish,
        "svg_polish_recommended_path": args.svg_polish_recommended_path,
        "svg_polish_next_action": args.svg_polish_next_action,
        "svg_polish_blocking_sources": args.svg_polish_blocking_sources,
    }
    missing = set(QUEUE_FILTER_KEYS) - set(values)
    extra = set(values) - set(QUEUE_FILTER_KEYS)
    if missing or extra:
        raise ValueError(
            "fig_queue_run filter surface does not match fig_queue: "
            f"missing={sorted(missing)} extra={sorted(extra)}"
        )
    return values


def run_queue(
    *,
    repo_root: Path = REPO_ROOT,
    mode: str,
    goal: str,
    execute: bool = False,
    max_steps: int = fig_run.DEFAULT_MAX_STEPS,
    max_fixtures: int = DEFAULT_MAX_FIXTURES,
    fixtures: list[str] | None,
    filters: dict[str, str | None] | None = None,
) -> dict[str, Any]:
    if max_fixtures < 1:
        raise ValueError("max_fixtures must be >= 1")
    queue = fig_queue.build_queue(
        repo_root=repo_root,
        mode=mode,
        goal=goal,
        fixtures=fixtures,
        filters=filters,
        include_command_plan=True,
    )
    command_plan = queue["command_plan"]
    planned_items = command_plan["executable"][:max_fixtures]
    runs = [
        (
            _executed_run(
                item,
                mode=mode,
                goal=goal,
                execute=execute,
                max_steps=max_steps,
                repo_root=repo_root,
            )
            if execute
            else _planned_run(item)
        )
        for item in planned_items
    ]
    queue_payload = {
        "schema": queue.get("schema"),
        "summary": queue.get("summary"),
        "bottleneck_report": queue.get("bottleneck_report"),
        "unfiltered_total": queue.get("unfiltered_total"),
        "command_plan": command_plan,
    }
    if "workspace_diagnostic" in queue:
        queue_payload["workspace_diagnostic"] = queue["workspace_diagnostic"]
    return {
        "schema": SCHEMA,
        "mode": mode,
        "goal": goal,
        "execute": execute,
        "max_steps": max_steps,
        "max_fixtures": max_fixtures,
        "fixtures": list(fixtures or []),
        "filters": queue.get("filters", {}),
        "queue": queue_payload,
        "runs": runs,
        "summary": _summary(command_plan=command_plan, runs=runs),
    }


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(prog="fig_queue_run.py")
    parser.add_argument("fixtures", nargs="*")
    parser.add_argument("--mode", choices=list(fig_driver.MODES), required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("json",), default="json")
    parser.add_argument("--max-steps", type=int, default=fig_run.DEFAULT_MAX_STEPS)
    parser.add_argument("--max-fixtures", type=int, default=DEFAULT_MAX_FIXTURES)
    parser.add_argument("--actor", choices=list(fig_queue._ACTORS), dest="required_actor")
    parser.add_argument("--action")
    parser.add_argument("--stop-boundary")
    parser.add_argument("--first-blocker")
    parser.add_argument("--blocking-source")
    parser.add_argument("--svg-polish-gate-state")
    parser.add_argument("--can-start-svg-polish", choices=("true", "false"))
    parser.add_argument("--svg-polish-recommended-path")
    parser.add_argument("--svg-polish-next-action")
    parser.add_argument("--svg-polish-blocking-source", dest="svg_polish_blocking_sources")
    args = parser.parse_args(argv)
    if args.execute and args.dry_run:
        print(
            "fig_queue_run.py: choose either --execute or --dry-run, not both",
            file=sys.stderr,
        )
        return 2
    try:
        resolved_repo_root = (
            runtime_paths.resolve_runtime_paths().workspace_root
            if repo_root is None
            else repo_root
        )
        payload = run_queue(
            repo_root=resolved_repo_root,
            mode=args.mode,
            goal=args.goal,
            execute=args.execute,
            max_steps=args.max_steps,
            max_fixtures=args.max_fixtures,
            fixtures=list(args.fixtures) or None,
            filters=_queue_filters_from_args(args),
        )
    except ValueError as exc:
        print(f"fig_queue_run.py: {exc}", file=sys.stderr)
        return 2
    fig_queue._print_workspace_diagnostic(payload.get("queue", {}))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
