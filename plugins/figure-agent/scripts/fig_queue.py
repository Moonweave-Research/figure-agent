"""Read-only fixture queue over the dry-run figure driver."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fig_driver  # noqa: E402
import runtime_paths  # noqa: E402
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
    "svg_polish_gate_state",
    "can_start_svg_polish",
    "svg_polish_recommended_path",
    "svg_polish_next_action",
    "svg_polish_blocking_sources",
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
    row = {
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
    guidance = summary.get("operator_guidance")
    if isinstance(guidance, dict):
        row["operator_guidance"] = guidance
    row.update(_svg_polish_fields(summary, mode=mode))
    return row


def _svg_polish_fields(summary: dict[str, Any], *, mode: str) -> dict[str, Any]:
    if mode != "polish":
        return {}
    fields: dict[str, Any] = {}
    gate = summary.get("svg_polish_gate")
    if isinstance(gate, dict):
        fields["svg_polish_gate_state"] = gate.get("state")
        fields["can_start_svg_polish"] = gate.get("can_start_svg_polish")
        fields["svg_polish_next_action"] = gate.get("next_action")
        gate_sources = _svg_polish_blocking_sources(gate)
        if gate_sources:
            fields["svg_polish_blocking_sources"] = gate_sources
    readiness = summary.get("svg_polish_readiness")
    if isinstance(readiness, dict):
        fields.setdefault("can_start_svg_polish", readiness.get("can_start_svg_polish"))
        fields.setdefault("svg_polish_next_action", readiness.get("next_action"))
        fields["svg_polish_recommended_path"] = readiness.get("recommended_path")
        readiness_sources = _svg_polish_blocking_sources(readiness)
        if readiness_sources:
            fields["svg_polish_blocking_sources"] = _merge_unique_strings(
                fields.get("svg_polish_blocking_sources"),
                readiness_sources,
            )
    return {key: value for key, value in fields.items() if value is not None}


def _merge_unique_strings(existing: Any, incoming: list[str]) -> list[str]:
    merged: list[str] = []
    for values in (existing, incoming):
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, str) and value and value not in merged:
                merged.append(value)
    return merged


def _svg_polish_blocking_sources(readiness: dict[str, Any]) -> list[str]:
    sources: list[str] = []
    blocking_items = readiness.get("blocking_items")
    if not isinstance(blocking_items, list):
        return sources
    for item in blocking_items:
        if not isinstance(item, dict):
            continue
        source = item.get("source")
        if isinstance(source, str) and source and source not in sources:
            sources.append(source)
    return sources


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


def _count_list_items(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        value = row.get(key)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str) and item:
                counts[item] += 1
    return dict(sorted(counts.items()))


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "total": len(rows),
        "errors": sum(1 for row in rows if row.get("action") == "error"),
        "by_action": _count(rows, "action"),
        "by_stop_boundary": _count(rows, "stop_boundary"),
        "by_first_blocker": _count(rows, "first_blocker"),
        "by_required_actor": _count(rows, "required_actor"),
        "by_blocking_source": _count(rows, "blocking_source"),
    }
    by_svg_gate = _count(rows, "svg_polish_gate_state")
    if by_svg_gate:
        summary["by_svg_polish_gate_state"] = by_svg_gate
    by_svg_path = _count(rows, "svg_polish_recommended_path")
    if by_svg_path:
        summary["by_svg_polish_recommended_path"] = by_svg_path
    by_svg_next = _count(rows, "svg_polish_next_action")
    if by_svg_next:
        summary["by_svg_polish_next_action"] = by_svg_next
    by_svg_blocker = _count_list_items(rows, "svg_polish_blocking_sources")
    if by_svg_blocker:
        summary["by_svg_polish_blocking_source"] = by_svg_blocker
    return summary


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
        if all(_filter_value_matches(row.get(key), value) for key, value in filters.items())
    ]


def _filter_value_matches(row_value: Any, filter_value: str) -> bool:
    if isinstance(row_value, bool):
        lowered = filter_value.lower()
        if lowered not in {"true", "false"}:
            return False
        return row_value is (lowered == "true")
    if isinstance(row_value, list):
        return filter_value in row_value
    return row_value == filter_value


def _blocked_reason(row: dict[str, Any]) -> str | None:
    actor = row.get("required_actor")
    if actor != "workflow_agent":
        return f"required_actor:{_cell(actor)}"
    if row.get("requires_human") is True:
        return "requires_human:true"
    stop_boundary = row.get("stop_boundary")
    if isinstance(stop_boundary, str) and stop_boundary:
        return f"stop_boundary:{stop_boundary}"
    safe_command = row.get("safe_command")
    if not isinstance(safe_command, str) or not safe_command:
        return "safe_command:missing"
    action = row.get("action")
    if action not in _EXECUTABLE_ACTIONS:
        return f"action:not_executable:{_cell(action)}"
    if action == fig_driver.ACTION_RUN_EXPORT and not _export_row_is_safe(row):
        return "export:safety_predicate_failed"
    return None


def _export_row_is_safe(row: dict[str, Any]) -> bool:
    command = row.get("safe_command")
    fixture = row.get("fixture")
    if not isinstance(command, str) or not isinstance(fixture, str) or not fixture:
        return False
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    return (
        parts == ["fig-agent", "export", fixture]
        and row.get("acceptance_state") == "NOT_DECLARED"
        and row.get("export_state") in {"MISSING", "STALE"}
        and row.get("critique_state") in {"FRESH", "NOT_REQUIRED"}
    )


def _operator_handoff(row: dict[str, Any], *, reason: str) -> dict[str, Any]:
    fixture = _cell(row.get("fixture"))
    actor = _cell(row.get("required_actor"))
    common_forbidden = [
        "source edits",
        "export mutation",
        "accepted/golden mutation",
        "publication state mutation",
    ]
    if row.get("action") == fig_driver.ACTION_COMPLETE:
        guidance = row.get("operator_guidance")
        if isinstance(guidance, dict):
            next_step = guidance.get("next_step")
            if isinstance(next_step, str) and next_step.strip():
                return {
                    "schema": OPERATOR_HANDOFF_SCHEMA,
                    "fixture": fixture,
                    "required_actor": actor,
                    "next_step": next_step,
                    "command": None,
                    "reason": reason,
                    "allowed_scope": ["read-only broader-mode inspection"],
                    "forbidden_scope": common_forbidden,
                    "closeout_checks": ["rerun /fig_queue in the next broader mode"],
                }
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
            "next_step": "Run read-only closeout inspection before continuing automation.",
            "command": f"fig-agent closeout {shlex.quote(fixture)} --json",
            "reason": reason,
            "allowed_scope": ["read-only closeout inspection"],
            "forbidden_scope": common_forbidden,
            "closeout_checks": [
                "read JSON output even when exit code is 1",
                "follow closeout.next_action",
                "rerun /fig_queue after resolving the blocked row",
            ],
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
    complete: list[dict[str, Any]] = []
    for row in rows:
        if row.get("action") == fig_driver.ACTION_COMPLETE:
            reason = "mode_scoped_complete"
            complete.append(
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
            continue
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
        "complete_count": len(complete),
        "executable": executable,
        "blocked": blocked,
        "complete": complete,
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
        if not fig_driver.is_safe_fixture_name(name):
            rows.append(
                _error_row(
                    name,
                    mode=mode,
                    stop_boundary="unsafe_fixture_name",
                    error="fixture name must be a single examples/<name> directory name",
                )
            )
            continue
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
    if isinstance(value, list):
        if not value:
            return "-"
        return ",".join(str(item) for item in value)
    return str(value)


def _table_next_step(row: dict[str, Any]) -> str:
    reason = _blocked_reason(row)
    if row.get("action") == fig_driver.ACTION_COMPLETE:
        guidance = row.get("operator_guidance")
        if isinstance(guidance, dict):
            next_step = guidance.get("next_step")
            if isinstance(next_step, str) and next_step.strip():
                return next_step
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
    rows = queue.get("rows", [])
    show_svg_columns = _has_svg_polish_columns(rows)
    header = ["fixture", "actor", "action", "stop_boundary", "first_blocker"]
    if show_svg_columns:
        header.extend(
            ["svg_gate", "can_svg", "polish_path", "polish_next", "polish_blockers"]
        )
    header.extend(["next_step", "next_command"])
    print("\t".join(header))
    for row in rows:
        cells = [
            _cell(row.get("fixture")),
            _cell(row.get("required_actor")),
            _cell(row.get("action")),
            _cell(row.get("stop_boundary")),
            _cell(row.get("first_blocker")),
        ]
        if show_svg_columns:
            cells.extend(
                [
                    _cell(row.get("svg_polish_gate_state")),
                    _cell(row.get("can_start_svg_polish")),
                    _cell(row.get("svg_polish_recommended_path")),
                    _cell(row.get("svg_polish_next_action")),
                    _cell(row.get("svg_polish_blocking_sources")),
                ]
            )
        cells.extend(
            [
                _cell(_table_next_step(row)),
                _cell(_table_next_command(row)),
            ]
        )
        print("\t".join(cells))
    summary = queue.get("summary", {})
    print(
        "summary "
        f"total={summary.get('total', 0)} "
        f"errors={summary.get('errors', 0)}"
    )
    for key in _summary_table_keys():
        formatted = _format_summary_counts(summary.get(key))
        if formatted:
            print(f"summary {key}={formatted}")


def _summary_table_keys() -> tuple[str, ...]:
    return (
        "by_action",
        "by_stop_boundary",
        "by_first_blocker",
        "by_required_actor",
        "by_blocking_source",
        "by_svg_polish_gate_state",
        "by_svg_polish_recommended_path",
        "by_svg_polish_next_action",
        "by_svg_polish_blocking_source",
    )


def _format_summary_counts(value: Any) -> str | None:
    if not isinstance(value, dict) or not value:
        return None
    parts: list[str] = []
    for key in sorted(value):
        count = value[key]
        if not isinstance(key, str) or not isinstance(count, int):
            continue
        parts.append(f"{key}:{count}")
    if not parts:
        return None
    return ",".join(parts)


def _has_svg_polish_columns(rows: Any) -> bool:
    if not isinstance(rows, list):
        return False
    keys = {
        "svg_polish_gate_state",
        "can_start_svg_polish",
        "svg_polish_recommended_path",
        "svg_polish_next_action",
        "svg_polish_blocking_sources",
    }
    return any(isinstance(row, dict) and not keys.isdisjoint(row) for row in rows)


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
    parser.add_argument("--svg-polish-gate-state")
    parser.add_argument("--can-start-svg-polish", choices=("true", "false"))
    parser.add_argument("--svg-polish-recommended-path")
    parser.add_argument("--svg-polish-next-action")
    parser.add_argument("--svg-polish-blocking-source", dest="svg_polish_blocking_sources")
    parser.add_argument("--command-plan", action="store_true")
    parser.add_argument("--commands", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--format", choices=("table", "json"), default="table")
    args = parser.parse_args(argv)

    resolved_repo_root = (
        runtime_paths.resolve_runtime_paths().workspace_root
        if repo_root == REPO_ROOT
        else repo_root
    )
    queue = build_queue(
        repo_root=resolved_repo_root,
        mode=args.mode,
        goal=args.goal,
        fixtures=list(args.fixtures) or None,
        filters={
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
        },
        include_command_plan=args.command_plan or args.commands,
    )
    if args.commands:
        command_plan = queue["command_plan"]
        for item in command_plan["executable"]:
            print(item["safe_command"])
    elif args.json or args.format == "json":
        print(json.dumps(queue, indent=2, sort_keys=True))
    else:
        print_table(queue)
    return 0


if __name__ == "__main__":
    sys.exit(main())
