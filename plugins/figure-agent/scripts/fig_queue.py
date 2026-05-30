"""Read-only fixture queue over the dry-run figure driver."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fig_driver  # noqa: E402
from driver_actor import (  # noqa: E402
    blocking_source_for_driver_summary,
    required_actor_for_driver_summary,
    requires_human_for_driver_summary,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "figure-agent.fixture-driver-queue.v1"
COMMAND_PLAN_SCHEMA = "figure-agent.fixture-command-plan.v1"
OPERATOR_HANDOFF_SCHEMA = "figure-agent.queue-operator-handoff.v1"
_FILTER_KEYS = (
    "required_actor",
    "action",
    "stop_boundary",
    "first_blocker",
    "blocking_source",
)
_ACTORS = (
    "workflow_agent",
    "host_llm",
    "human",
    "release_operator",
    "svg_editor",
)
_EXECUTABLE_ACTIONS = frozenset(
    {
        fig_driver.ACTION_RUN_ADJUDICATE,
        fig_driver.ACTION_RUN_COMPILE,
        fig_driver.ACTION_RUN_EXPORT,
        fig_driver.ACTION_RUN_FIG_LOOP,
    }
)


def _fixture_names(repo_root: Path, fixtures: list[str] | None) -> list[str]:
    if fixtures:
        return list(fixtures)
    examples_dir = repo_root / "examples"
    if not examples_dir.is_dir():
        return []
    return sorted(
        path.name
        for path in examples_dir.iterdir()
        if path.is_dir() and (path / "spec.yaml").is_file()
    )


def _first_blocker(summary: dict[str, Any]) -> str | None:
    status_explanation = summary.get("status_explanation")
    if not isinstance(status_explanation, dict):
        return None
    blocker = status_explanation.get("first_blocker")
    if not isinstance(blocker, dict):
        return None
    code = blocker.get("code")
    if not isinstance(code, str):
        return None
    stripped = code.strip()
    if not stripped or stripped == "none":
        return None
    return stripped


def _row_from_summary(summary: dict[str, Any], *, mode: str) -> dict[str, Any]:
    status = summary.get("status")
    if not isinstance(status, dict):
        status = {}
    return {
        "fixture": summary.get("fixture"),
        "mode": mode,
        "action": summary.get("action"),
        "stop_boundary": summary.get("stop_boundary"),
        "first_blocker": _first_blocker(summary),
        "safe_command": summary.get("safe_command"),
        "render_state": status.get("render_state"),
        "critique_state": status.get("critique_state"),
        "export_state": status.get("export_state"),
        "acceptance_state": status.get("acceptance_state"),
        "publication_gate_state": status.get("publication_gate_state"),
        "release_ready": status.get("release_ready"),
        "required_actor": required_actor_for_driver_summary(summary),
        "blocking_source": blocking_source_for_driver_summary(summary),
        "requires_human": requires_human_for_driver_summary(summary),
    }


def _error_row(name: str, *, mode: str, stop_boundary: str, error: str) -> dict[str, Any]:
    return {
        "fixture": name,
        "mode": mode,
        "action": "error",
        "stop_boundary": stop_boundary,
        "first_blocker": stop_boundary,
        "safe_command": None,
        "render_state": None,
        "critique_state": None,
        "export_state": None,
        "acceptance_state": None,
        "publication_gate_state": None,
        "release_ready": None,
        "required_actor": "workflow_agent",
        "blocking_source": stop_boundary,
        "requires_human": False,
        "error": error,
    }


def _count(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        value = row.get(key)
        if isinstance(value, str) and value:
            counts[value] += 1
    return dict(sorted(counts.items()))


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total": len(rows),
        "errors": sum(1 for row in rows if row.get("action") == "error"),
        "by_action": _count(rows, "action"),
        "by_stop_boundary": _count(rows, "stop_boundary"),
        "by_first_blocker": _count(rows, "first_blocker"),
        "by_required_actor": _count(rows, "required_actor"),
        "by_blocking_source": _count(rows, "blocking_source"),
    }


def _active_filters(filters: dict[str, str | None] | None) -> dict[str, str]:
    if not filters:
        return {}
    return {
        key: value.strip()
        for key, value in filters.items()
        if key in _FILTER_KEYS and isinstance(value, str) and value.strip()
    }


def _filter_rows(
    rows: list[dict[str, Any]],
    filters: dict[str, str],
) -> list[dict[str, Any]]:
    if not filters:
        return list(rows)
    return [
        row
        for row in rows
        if all(row.get(key) == value for key, value in filters.items())
    ]


def _blocked_reason(row: dict[str, Any]) -> str | None:
    actor = row.get("required_actor")
    if actor != "workflow_agent":
        return f"required_actor:{_cell(actor)}"
    if row.get("requires_human") is True:
        return "requires_human:true"
    safe_command = row.get("safe_command")
    if not isinstance(safe_command, str) or not safe_command:
        return "safe_command:missing"
    stop_boundary = row.get("stop_boundary")
    if isinstance(stop_boundary, str) and stop_boundary:
        return f"stop_boundary:{stop_boundary}"
    action = row.get("action")
    if action not in _EXECUTABLE_ACTIONS:
        return f"action:not_executable:{_cell(action)}"
    return None


def _operator_handoff(row: dict[str, Any], *, reason: str) -> dict[str, Any]:
    fixture = _cell(row.get("fixture"))
    actor = _cell(row.get("required_actor"))
    common_forbidden = [
        "source edits",
        "export mutation",
        "accepted/golden mutation",
        "publication state mutation",
    ]
    if actor == "host_llm":
        return {
            "schema": OPERATOR_HANDOFF_SCHEMA,
            "fixture": fixture,
            "required_actor": actor,
            "next_step": "Refresh host-vision critique for this fixture.",
            "command": row.get("safe_command"),
            "reason": reason,
            "allowed_scope": [
                f"examples/{fixture}/critique.md",
                f"examples/{fixture}/build/audit_crops/",
            ],
            "forbidden_scope": common_forbidden,
            "closeout_checks": [
                "run critique_lint",
                "sync or scaffold critique_adjudication.yaml",
                "rerun /fig_queue",
            ],
        }
    if actor == "human":
        return {
            "schema": OPERATOR_HANDOFF_SCHEMA,
            "fixture": fixture,
            "required_actor": actor,
            "next_step": "Record the required human decision before continuing automation.",
            "command": None,
            "reason": reason,
            "allowed_scope": ["human decision record or acceptance decision"],
            "forbidden_scope": common_forbidden,
            "closeout_checks": ["rerun /fig_queue after recording the decision"],
        }
    if actor == "release_operator":
        return {
            "schema": OPERATOR_HANDOFF_SCHEMA,
            "fixture": fixture,
            "required_actor": actor,
            "next_step": (
                "Perform explicit release/golden review; do not force golden implicitly."
            ),
            "command": None,
            "reason": reason,
            "allowed_scope": ["release/golden review with explicit approval"],
            "forbidden_scope": [
                "implicit --force-golden",
                "implicit accepted mutation",
                "source edits",
                "unreviewed export mutation",
            ],
            "closeout_checks": ["rerun /fig_queue after release decision"],
        }
    if actor == "svg_editor":
        return {
            "schema": OPERATOR_HANDOFF_SCHEMA,
            "fixture": fixture,
            "required_actor": actor,
            "next_step": "Complete SVG polish handoff outside queue automation.",
            "command": None,
            "reason": reason,
            "allowed_scope": ["declared polished SVG handoff scope"],
            "forbidden_scope": common_forbidden,
            "closeout_checks": ["rerun /fig_queue after polish handoff"],
        }
    if reason == "stop_boundary:closeout_required":
        return {
            "schema": OPERATOR_HANDOFF_SCHEMA,
            "fixture": fixture,
            "required_actor": actor,
            "next_step": "Run read-only closeout inspection before attempting export.",
            "command": f"uv run python3 scripts/fig_closeout.py {fixture} --json",
            "reason": reason,
            "allowed_scope": ["read-only closeout inspection"],
            "forbidden_scope": common_forbidden,
            "closeout_checks": ["rerun /fig_queue after resolving the blocked row"],
        }
    return {
        "schema": OPERATOR_HANDOFF_SCHEMA,
        "fixture": fixture,
        "required_actor": actor,
        "next_step": "Inspect the blocked queue row and rerun live driver state.",
        "command": None,
        "reason": reason,
        "allowed_scope": ["read-only inspection"],
        "forbidden_scope": common_forbidden,
        "closeout_checks": ["rerun /fig_queue after resolving the blocked row"],
    }


def build_command_plan(rows: list[dict[str, Any]]) -> dict[str, Any]:
    executable: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for row in rows:
        reason = _blocked_reason(row)
        if reason is None:
            executable.append(
                {
                    "fixture": row.get("fixture"),
                    "action": row.get("action"),
                    "safe_command": row.get("safe_command"),
                    "required_actor": row.get("required_actor"),
                }
            )
            continue
        blocked.append(
            {
                "fixture": row.get("fixture"),
                "action": row.get("action"),
                "required_actor": row.get("required_actor"),
                "blocking_source": row.get("blocking_source"),
                "stop_boundary": row.get("stop_boundary"),
                "reason": reason,
                "operator_handoff": _operator_handoff(row, reason=reason),
            }
        )
    return {
        "schema": COMMAND_PLAN_SCHEMA,
        "executable_count": len(executable),
        "blocked_count": len(blocked),
        "executable": executable,
        "blocked": blocked,
    }


def build_queue(
    *,
    repo_root: Path = REPO_ROOT,
    mode: str,
    goal: str,
    fixtures: list[str] | None,
    filters: dict[str, str | None] | None = None,
    include_command_plan: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for name in _fixture_names(repo_root, fixtures):
        example_dir = repo_root / "examples" / name
        if not example_dir.is_dir():
            rows.append(
                _error_row(
                    name,
                    mode=mode,
                    stop_boundary="fixture_not_found",
                    error=f"examples/{name}/ not found",
                )
            )
            continue
        try:
            driver_summary = fig_driver.build_driver_summary(
                name,
                mode=mode,
                goal=goal,
                repo_root=repo_root,
            )
        except (OSError, ValueError) as exc:
            rows.append(
                _error_row(
                    name,
                    mode=mode,
                    stop_boundary="driver_error",
                    error=str(exc),
                )
            )
            continue
        rows.append(_row_from_summary(driver_summary, mode=mode))
    active_filters = _active_filters(filters)
    filtered_rows = _filter_rows(rows, active_filters)
    queue = {
        "schema": SCHEMA,
        "mode": mode,
        "goal": goal,
        "filters": active_filters,
        "unfiltered_total": len(rows),
        "rows": filtered_rows,
        "summary": _summary(filtered_rows),
    }
    if include_command_plan:
        queue["command_plan"] = build_command_plan(filtered_rows)
    return queue


def _cell(value: Any) -> str:
    if value is None:
        return "-"
    return str(value)


def _table_next_step(row: dict[str, Any]) -> str:
    reason = _blocked_reason(row)
    if reason is None:
        return "Executable workflow-agent command."
    handoff = _operator_handoff(row, reason=reason)
    next_step = handoff.get("next_step")
    if isinstance(next_step, str) and next_step:
        return next_step
    return "Inspect blocked row and rerun /fig_queue."


def _table_next_command(row: dict[str, Any]) -> str | None:
    reason = _blocked_reason(row)
    if reason is None:
        command = row.get("safe_command")
        return command if isinstance(command, str) else None
    handoff = _operator_handoff(row, reason=reason)
    command = handoff.get("command")
    return command if isinstance(command, str) and command else None


def print_table(queue: dict[str, Any]) -> None:
    print("fixture actor action stop_boundary first_blocker next_step next_command")
    for row in queue.get("rows", []):
        print(
            " ".join(
                [
                    _cell(row.get("fixture")),
                    _cell(row.get("required_actor")),
                    _cell(row.get("action")),
                    _cell(row.get("stop_boundary")),
                    _cell(row.get("first_blocker")),
                    _cell(_table_next_step(row)),
                    _cell(_table_next_command(row)),
                ]
            )
        )
    summary = queue.get("summary", {})
    print(
        "summary "
        f"total={summary.get('total', 0)} "
        f"errors={summary.get('errors', 0)}"
    )


def main(argv: list[str] | None = None, *, repo_root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(prog="fig_queue.py")
    parser.add_argument("fixtures", nargs="*")
    parser.add_argument("--mode", choices=list(fig_driver.MODES), required=True)
    parser.add_argument("--goal", default="triage fixture queue")
    parser.add_argument("--actor", choices=list(_ACTORS), dest="required_actor")
    parser.add_argument("--action")
    parser.add_argument("--stop-boundary")
    parser.add_argument("--first-blocker")
    parser.add_argument("--blocking-source")
    parser.add_argument("--command-plan", action="store_true")
    parser.add_argument("--commands", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    queue = build_queue(
        repo_root=repo_root,
        mode=args.mode,
        goal=args.goal,
        fixtures=list(args.fixtures) or None,
        filters={
            "required_actor": args.required_actor,
            "action": args.action,
            "stop_boundary": args.stop_boundary,
            "first_blocker": args.first_blocker,
            "blocking_source": args.blocking_source,
        },
        include_command_plan=args.command_plan or args.commands,
    )
    if args.commands:
        command_plan = queue["command_plan"]
        for item in command_plan["executable"]:
            print(item["safe_command"])
    elif args.json:
        print(json.dumps(queue, indent=2, sort_keys=True))
    else:
        print_table(queue)
    return 0


if __name__ == "__main__":
    sys.exit(main())
