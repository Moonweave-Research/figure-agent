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
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fig_driver  # noqa: E402
from driver_actor import required_actor_for_driver_summary  # noqa: E402
from fig_run_records import write_run_journal  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.run.v1"
BOUNDARY_HANDOFF_SCHEMA = "figure-agent.boundary-handoff.v1"
DEFAULT_MAX_STEPS = 5
RUN_MODES = tuple(mode for mode in fig_driver.MODES if mode != "final")
EXECUTABLE_ACTIONS = frozenset(
    {
        fig_driver.ACTION_RUN_ADJUDICATE,
        fig_driver.ACTION_RUN_COMPILE,
        fig_driver.ACTION_RUN_EXPORT,
        fig_driver.ACTION_RUN_FIG_LOOP,
    }
)

STOP_PLAN_ONLY = "plan_only"
STOP_HOST_BOUNDARY = "host_boundary"
STOP_NOT_EXECUTABLE = "not_executable_action"
STOP_COMMAND_FAILED = "command_failed"
STOP_COMPLETE = "complete"
STOP_MAX_STEPS = "max_steps_exceeded"
STOP_REPEATED_ACTION = "repeated_executable_action"
PATCH_DEFERRED = "patch_source_mutation_deferred_until_70c"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


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


def _has_forbidden_export_flag(command: str) -> bool:
    try:
        parts = shlex.split(command)
    except ValueError:
        return True
    return "--force-golden" in parts or "--skip-critique" in parts


def _command_parts(command: str) -> list[str] | None:
    try:
        return shlex.split(command)
    except ValueError:
        return None


def _compile_command_matches_fixture(command: str, name: str) -> bool:
    parts = _command_parts(command)
    return parts == [
        "bash",
        "scripts/compile.sh",
        f"examples/{name}/{name}.tex",
    ]


def _adjudicate_command_matches_fixture(command: str, name: str) -> bool:
    parts = _command_parts(command)
    return parts == [
        "uv",
        "run",
        "python3",
        "scripts/critique_adjudication.py",
        "scaffold",
        name,
    ]


def _fig_loop_command_matches_fixture(command: str, name: str, goal: str) -> bool:
    parts = _command_parts(command)
    return parts == [
        "uv",
        "run",
        "python3",
        "scripts/fig_loop.py",
        name,
        "--goal",
        goal,
        "--json",
    ]


def _export_command_matches_fixture(command: str, name: str) -> bool:
    parts = _command_parts(command)
    return parts == ["uv", "run", "python3", "scripts/run_export.py", name]


def _export_is_safe(summary: dict[str, Any], *, name: str) -> bool:
    status = summary.get("status")
    command = summary.get("safe_command")
    if not isinstance(status, dict):
        return False
    if not isinstance(command, str) or _has_forbidden_export_flag(command):
        return False
    if not _export_command_matches_fixture(command, name):
        return False
    return (
        status.get("acceptance_state") == "NOT_DECLARED"
        and status.get("export_state") in {"MISSING", "STALE"}
        and status.get("critique_state") in {"FRESH", "NOT_REQUIRED"}
    )


def _would_execute(
    summary: dict[str, Any], *, name: str, goal: str, repo_root: Path
) -> bool:
    if not _is_executable_action(summary):
        return False
    command = summary["safe_command"]
    if summary.get("action") == fig_driver.ACTION_RUN_COMPILE:
        return _compile_command_matches_fixture(command, name)
    if summary.get("action") == fig_driver.ACTION_RUN_ADJUDICATE:
        return _adjudicate_command_matches_fixture(
            command, name
        ) and _adjudication_scaffold_is_safe(name, repo_root=repo_root)
    if summary.get("action") == fig_driver.ACTION_RUN_FIG_LOOP:
        return _fig_loop_command_matches_fixture(command, name, goal)
    if summary.get("action") == fig_driver.ACTION_RUN_EXPORT:
        return _export_is_safe(summary, name=name)
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


def _list_from_summary(summary: dict[str, Any], key: str, fallback: list[str]) -> list[str]:
    next_action = summary.get("next_action_summary")
    if isinstance(next_action, dict):
        value = next_action.get(key)
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return list(value)
    return list(fallback)


def _evidence_refs(summary: dict[str, Any], final_stop_reason: str) -> list[str]:
    if final_stop_reason == STOP_REPEATED_ACTION:
        return [f"runner.stop_reason:{STOP_REPEATED_ACTION}"]
    refs = _list_from_summary(summary, "evidence_refs", [])
    if refs:
        return refs
    stop_boundary = summary.get("stop_boundary")
    if isinstance(stop_boundary, str) and stop_boundary:
        return [f"driver.stop_boundary:{stop_boundary}"]
    action = summary.get("action")
    if isinstance(action, str) and action:
        return [f"driver.action:{action}", f"runner.stop_reason:{final_stop_reason}"]
    return [f"runner.stop_reason:{final_stop_reason}"]


def _required_actor(summary: dict[str, Any], final_stop_reason: str) -> str:
    return required_actor_for_driver_summary(
        summary,
        final_stop_reason=final_stop_reason,
    )


def _blocking_reason(
    summary: dict[str, Any],
    final_stop_reason: str,
    last_step: dict[str, Any] | None,
) -> str:
    if final_stop_reason == STOP_REPEATED_ACTION:
        return (
            "same executable action and command was selected again after a "
            "successful run; stopped to avoid no-progress replay"
        )
    reason = summary.get("reason")
    if not isinstance(reason, str) or not reason:
        reason = final_stop_reason
    if final_stop_reason == STOP_COMMAND_FAILED and isinstance(last_step, dict):
        stderr_tail = last_step.get("stderr_tail")
        if isinstance(stderr_tail, str) and stderr_tail:
            return f"{reason} command failed: {stderr_tail}"
    return reason


def _basin_summary(summary: dict[str, Any]) -> dict[str, Any] | None:
    loop_checkpoint = summary.get("loop_checkpoint")
    if not isinstance(loop_checkpoint, dict):
        return None
    basin = loop_checkpoint.get("basin_summary")
    if not isinstance(basin, dict) or basin.get("evaluation_state") != "basin_detected":
        return None
    return basin


def _closeout_checks(final_stop_reason: str, summary: dict[str, Any]) -> list[str]:
    basin = _basin_summary(summary)
    if basin is not None:
        actions = basin.get("recommended_step_out_actions")
        checks = (
            [item for item in actions if isinstance(item, str) and item]
            if isinstance(actions, list)
            else []
        )
        checks.extend(
            [
                "rerun live /fig_loop after step-out decision is recorded",
                "rerun live /fig_drive",
            ]
        )
        return checks
    if final_stop_reason == STOP_COMMAND_FAILED:
        return ["inspect command stderr_tail", "rerun live /fig_status"]
    if final_stop_reason in {STOP_MAX_STEPS, STOP_REPEATED_ACTION}:
        return [
            "inspect repeated action",
            "rerun live /fig_status",
            "rerun live /fig_drive",
        ]
    stop_boundary = summary.get("stop_boundary")
    if stop_boundary == fig_driver.STOP_REFERENCE_MISSING:
        return [
            "fix reference path or provide reference image",
            "rerun live /fig_status",
            "rerun live /fig_drive",
        ]
    if stop_boundary == fig_driver.STOP_SEMANTIC_BACKPORT:
        return [
            "backport semantic changes to source/spec",
            "rerun live /fig_status",
            "rerun live /fig_drive",
        ]
    if stop_boundary == fig_driver.STOP_CLOSEOUT:
        fixture = summary.get("fixture")
        if isinstance(fixture, str) and fixture:
            quoted_fixture = shlex.quote(fixture)
            return [
                f"run uv run python3 scripts/fig_closeout.py {quoted_fixture} --json",
                "read JSON output even when exit code is 1",
                "follow closeout.next_action",
                "rerun live /fig_drive",
            ]
        return ["run read-only closeout inspection", "rerun live /fig_drive"]
    action = summary.get("action")
    if action == fig_driver.ACTION_RUN_CRITIQUE:
        return [
            "write or refresh critique.md",
            "rerun live /fig_status",
            "rerun live /fig_drive",
        ]
    if action == fig_driver.ACTION_RUN_ADJUDICATE:
        return [
            "inspect critique_adjudication.yaml",
            "rerun live /fig_status",
            "rerun live /fig_drive",
        ]
    if action == fig_driver.ACTION_RUN_EXPORT:
        return ["complete closeout/export step", "rerun live /fig_status"]
    if action == fig_driver.ACTION_RUN_FIG_LOOP:
        return ["complete closeout loop rerun", "rerun live /fig_drive"]
    if action == fig_driver.ACTION_RELEASE_BLOCKED:
        return ["obtain explicit release/golden approval", "rerun live /fig_drive"]
    if action == fig_driver.ACTION_HUMAN_GATE_STOP:
        return ["record human decision", "rerun live /fig_loop or /fig_drive"]
    return ["rerun live /fig_status", "rerun live /fig_drive"]


def _boundary_handoff(
    *,
    summary: dict[str, Any],
    final_stop_reason: str,
    last_step: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if final_stop_reason == STOP_COMPLETE:
        return None
    action = summary.get("action")
    stop_boundary = summary.get("stop_boundary")
    handoff = {
        "schema": BOUNDARY_HANDOFF_SCHEMA,
        "action": action,
        "stop_boundary": stop_boundary,
        "required_actor": _required_actor(summary, final_stop_reason),
        "blocking_reason": _blocking_reason(summary, final_stop_reason, last_step),
        "evidence_refs": _evidence_refs(summary, final_stop_reason),
        "allowed_scope": _list_from_summary(summary, "allowed_scope", ["read-only"]),
        "forbidden_scope": _list_from_summary(
            summary,
            "forbidden_scope",
            [
                "hidden source edits",
                "accepted/golden state without explicit approval",
                "unrelated examples",
            ],
        ),
        "closeout_checks": _closeout_checks(final_stop_reason, summary),
        "continuation_guidance": {
            "rerun_live_status_first": True,
            "rerun_live_driver_first": True,
            "note": "Do not replay this handoff; rerun live status and driver state first.",
        },
    }
    if action == fig_driver.ACTION_PATCH_HANDOFF_STOP or stop_boundary in {
        fig_driver.STOP_PATCH_HANDOFF,
        fig_driver.STOP_AMBIGUOUS_PATCH,
    }:
        handoff.update(
            {
                "required_actor": "workflow_agent",
                "deferred_boundary": PATCH_DEFERRED,
                "allowed_scope": ["read-only"],
                "forbidden_scope": [
                    "source mutation before patch executor currentness is verified"
                ],
            }
        )
    basin = _basin_summary(summary)
    if basin is not None:
        handoff["basin_summary"] = basin
    return handoff


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
    payload = {
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
    handoff = _boundary_handoff(
        summary=final_summary,
        final_stop_reason=final_stop_reason,
        last_step=steps[-1] if steps else None,
    )
    if handoff is not None:
        payload["boundary_handoff"] = handoff
    return payload


def run_workflow(
    name: str,
    *,
    mode: str,
    goal: str,
    execute: bool = False,
    max_steps: int = DEFAULT_MAX_STEPS,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    if mode == "final":
        raise ValueError(
            "final mode is driver-only; use fig_driver.py --mode final --dry-run"
        )
    if mode not in RUN_MODES:
        raise ValueError(f"unsupported mode: {mode}")
    if max_steps < 1:
        raise ValueError("max_steps must be >= 1")

    steps: list[dict[str, Any]] = []
    executed_count = 0
    final_summary: dict[str, Any] | None = None
    final_stop_reason = STOP_MAX_STEPS
    executed_signatures: set[tuple[str, str]] = set()

    for index in range(1, max_steps + 1):
        summary = _driver_summary(name, mode=mode, goal=goal, repo_root=repo_root)
        final_summary = summary
        would_execute = _would_execute(
            summary, name=name, goal=goal, repo_root=repo_root
        )

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
        signature = (summary["action"], command)
        if signature in executed_signatures:
            steps.append(
                _step_payload(
                    index=index,
                    summary=summary,
                    would_execute=False,
                    executed=False,
                    stop_reason=STOP_REPEATED_ACTION,
                )
            )
            final_stop_reason = STOP_REPEATED_ACTION
            break

        result = _run_command(command, repo_root=repo_root)
        executed_count += 1
        executed_signatures.add(signature)
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
    parser.add_argument("--mode", choices=list(RUN_MODES), required=True)
    parser.add_argument("--goal", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    parser.add_argument("--runs-root", type=Path, default=None)
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--no-record", action="store_true")
    parser.add_argument("--format", choices=("json",), default="json")
    args = parser.parse_args(argv)
    started_at = _utc_now()
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
    completed_at = _utc_now()
    should_record = not args.no_record and (args.execute or args.record)
    if should_record:
        try:
            payload = write_run_journal(
                payload,
                runs_root=args.runs_root or repo_root / ".scratch" / "fig-run-runs",
                repo_root=repo_root,
                started_at=started_at,
                completed_at=completed_at,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            payload["journal_error"] = {
                "schema": "figure-agent.fig-run-journal-error.v1",
                "recording_requested": True,
                "authoritative": False,
                "replay_allowed": False,
                "commands_are_evidence_only": True,
                "message": str(exc),
            }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
