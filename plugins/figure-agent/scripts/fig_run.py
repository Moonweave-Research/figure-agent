"""Bounded executor for safe figure workflow steps.

`fig_driver.py` remains the canonical next-action selector. This module wraps
the driver and executes only a narrow allowlist of deterministic shell actions,
then re-queries the driver until it reaches a boundary.

Schema: figure-agent.run.v1.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fig_driver  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.run.v1"
DEFAULT_MAX_STEPS = 5
EXECUTABLE_ACTIONS = frozenset(
    {
        fig_driver.ACTION_RUN_ADJUDICATE,
        fig_driver.ACTION_RUN_COMPILE,
        fig_driver.ACTION_RUN_FIG_LOOP,
    }
)

STOP_PLAN_ONLY = "plan_only"
STOP_HOST_BOUNDARY = "host_boundary"
STOP_NOT_EXECUTABLE = "not_executable_action"
STOP_COMMAND_FAILED = "command_failed"
STOP_COMPLETE = "complete"
STOP_MAX_STEPS = "max_steps_exceeded"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def _driver_summary(
    name: str,
    *,
    mode: str,
    goal: str,
    repo_root: Path,
) -> dict[str, Any]:
    return fig_driver.build_driver_summary(
        name,
        mode=mode,
        goal=goal,
        repo_root=repo_root,
    )


def _run_command(command: str, *, repo_root: Path) -> CommandResult:
    result = subprocess.run(
        shlex.split(command),
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _tail(text: str, *, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _is_slash_command(command: str | None) -> bool:
    return isinstance(command, str) and command.strip().startswith("/")


def _is_executable_action(summary: dict[str, Any]) -> bool:
    action = summary.get("action")
    command = summary.get("safe_command")
    return (
        isinstance(action, str)
        and action in EXECUTABLE_ACTIONS
        and summary.get("stop_boundary") is None
        and isinstance(command, str)
        and command.strip() != ""
        and not _is_slash_command(command)
    )


def _adjudication_scaffold_is_safe(name: str, *, repo_root: Path) -> bool:
    return not (repo_root / "examples" / name / "critique_adjudication.yaml").exists()


def _would_execute(summary: dict[str, Any], *, name: str, repo_root: Path) -> bool:
    if not _is_executable_action(summary):
        return False
    if summary.get("action") == fig_driver.ACTION_RUN_ADJUDICATE:
        return _adjudication_scaffold_is_safe(name, repo_root=repo_root)
    return True


def _boundary_stop_reason(summary: dict[str, Any]) -> str:
    action = summary.get("action")
    if action == fig_driver.ACTION_COMPLETE:
        return STOP_COMPLETE
    if action == fig_driver.ACTION_RUN_CRITIQUE or _is_slash_command(
        summary.get("safe_command")
    ):
        return STOP_HOST_BOUNDARY
    return STOP_NOT_EXECUTABLE


def _step_payload(
    *,
    index: int,
    summary: dict[str, Any],
    would_execute: bool,
    executed: bool,
    stop_reason: str | None,
    result: CommandResult | None = None,
) -> dict[str, Any]:
    return {
        "index": index,
        "action": summary.get("action"),
        "safe_command": summary.get("safe_command"),
        "stop_boundary": summary.get("stop_boundary"),
        "reason": summary.get("reason"),
        "would_execute": would_execute,
        "executed": executed,
        "returncode": result.returncode if result is not None else None,
        "stdout_tail": _tail(result.stdout) if result is not None else "",
        "stderr_tail": _tail(result.stderr) if result is not None else "",
        "stop_reason": stop_reason,
        "driver": summary,
    }


def _result_payload(
    *,
    name: str,
    mode: str,
    goal: str,
    execute: bool,
    max_steps: int,
    steps: list[dict[str, Any]],
    final_summary: dict[str, Any],
    final_stop_reason: str,
    executed_count: int,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": name,
        "mode": mode,
        "goal": goal,
        "execute": execute,
        "max_steps": max_steps,
        "executable_actions": sorted(EXECUTABLE_ACTIONS),
        "steps": steps,
        "final_action": final_summary.get("action"),
        "final_safe_command": final_summary.get("safe_command"),
        "final_stop_boundary": final_summary.get("stop_boundary"),
        "final_stop_reason": final_stop_reason,
        "executed_count": executed_count,
    }


def run_workflow(
    name: str,
    *,
    mode: str,
    goal: str,
    execute: bool = False,
    max_steps: int = DEFAULT_MAX_STEPS,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    if max_steps < 1:
        raise ValueError("max_steps must be >= 1")

    steps: list[dict[str, Any]] = []
    executed_count = 0
    final_summary: dict[str, Any] | None = None
    final_stop_reason = STOP_MAX_STEPS

    for index in range(1, max_steps + 1):
        summary = _driver_summary(name, mode=mode, goal=goal, repo_root=repo_root)
        final_summary = summary
        would_execute = _would_execute(summary, name=name, repo_root=repo_root)

        if not execute:
            stop_reason = STOP_PLAN_ONLY if would_execute else _boundary_stop_reason(summary)
            steps.append(
                _step_payload(
                    index=index,
                    summary=summary,
                    would_execute=would_execute,
                    executed=False,
                    stop_reason=stop_reason,
                )
            )
            final_stop_reason = stop_reason
            break

        if not would_execute:
            stop_reason = _boundary_stop_reason(summary)
            steps.append(
                _step_payload(
                    index=index,
                    summary=summary,
                    would_execute=False,
                    executed=False,
                    stop_reason=stop_reason,
                )
            )
            final_stop_reason = stop_reason
            break

        command = summary["safe_command"]
        result = _run_command(command, repo_root=repo_root)
        executed_count += 1
        stop_reason = STOP_COMMAND_FAILED if result.returncode != 0 else None
        steps.append(
            _step_payload(
                index=index,
                summary=summary,
                would_execute=True,
                executed=True,
                stop_reason=stop_reason,
                result=result,
            )
        )
        if result.returncode != 0:
            final_stop_reason = STOP_COMMAND_FAILED
            break
    else:
        final_stop_reason = STOP_MAX_STEPS

    if final_summary is None:
        raise ValueError("driver did not produce a summary")
    return _result_payload(
        name=name,
        mode=mode,
        goal=goal,
        execute=execute,
        max_steps=max_steps,
        steps=steps,
        final_summary=final_summary,
        final_stop_reason=final_stop_reason,
        executed_count=executed_count,
    )


def main(argv: list[str] | None = None, *, repo_root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(prog="fig_run.py")
    parser.add_argument("name")
    parser.add_argument("--mode", choices=list(fig_driver.MODES), required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    args = parser.parse_args(argv)
    try:
        payload = run_workflow(
            args.name,
            mode=args.mode,
            goal=args.goal,
            execute=args.execute,
            max_steps=args.max_steps,
            repo_root=repo_root,
        )
    except ValueError as exc:
        print(f"fig_run.py: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
