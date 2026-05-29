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


def build_queue(
    *,
    repo_root: Path = REPO_ROOT,
    mode: str,
    goal: str,
    fixtures: list[str] | None,
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
    return {
        "schema": SCHEMA,
        "mode": mode,
        "goal": goal,
        "rows": rows,
        "summary": _summary(rows),
    }


def _cell(value: Any) -> str:
    if value is None:
        return "-"
    return str(value)


def print_table(queue: dict[str, Any]) -> None:
    print("fixture actor action stop_boundary first_blocker safe_command")
    for row in queue.get("rows", []):
        print(
            " ".join(
                _cell(row.get(key))
                for key in (
                    "fixture",
                    "required_actor",
                    "action",
                    "stop_boundary",
                    "first_blocker",
                    "safe_command",
                )
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
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    queue = build_queue(
        repo_root=repo_root,
        mode=args.mode,
        goal=args.goal,
        fixtures=list(args.fixtures) or None,
    )
    if args.json:
        print(json.dumps(queue, indent=2, sort_keys=True))
    else:
        print_table(queue)
    return 0


if __name__ == "__main__":
    sys.exit(main())
