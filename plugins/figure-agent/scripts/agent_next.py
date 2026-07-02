"""Read-only state-router for the next safe figure-agent action."""

from __future__ import annotations

import shlex
import time
from pathlib import Path
from typing import Any

import fixture_identity
import quality_next_experiment
import runtime_paths
import status

SCHEMA = "figure-agent.next.v1"
_SLASH_COMMANDS = {
    "/fig_adjudicate": "adjudicate",
    "/fig_closeout": "closeout",
    "/fig_compile": "compile",
    "/fig_drive": "drive",
    "/fig_e2e_smoke": "e2e-smoke",
    "/fig_export": "export",
    "/fig_improve": "improve",
    "/fig_loop": "loop",
    "/fig_queue": "queue",
    "/fig_queue_run": "queue-run",
    "/fig_run": "run",
    "/fig_status": "status",
}
_WRITING_COMMANDS = {
    "accept-candidate",
    "adjudicate",
    "apply-candidate",
    "apply-plan",
    "closeout-accept",
    "compile",
    "e2e-smoke",
    "export",
    "improve",
    "loop",
    "queue-run",
    "render-candidates",
    "run",
}
_WRITE_FLAGS = {"--accept", "--apply", "--execute", "--force-golden", "--write"}
_RELEASE_STATE_COMMANDS = {"closeout-accept"}
_RELEASE_STATE_FLAGS = {"--accept-golden", "--force-golden"}


def _diagnostic(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _command_writes(command: str | None) -> bool:
    if not command:
        return False
    try:
        parts = shlex.split(command)
    except ValueError:
        return True
    if not parts:
        return False
    if any(flag in parts for flag in _WRITE_FLAGS):
        return True
    if parts[0] == "fig-agent" and len(parts) > 1:
        return parts[1] in _WRITING_COMMANDS
    if parts[0].startswith("/fig_"):
        return _SLASH_COMMANDS.get(parts[0], parts[0].removeprefix("/fig_")) in _WRITING_COMMANDS
    return False


def _command_mutates_release_state(command: str | None) -> bool:
    if not command:
        return False
    try:
        parts = shlex.split(command)
    except ValueError:
        return True
    if not parts:
        return False
    if any(flag in parts for flag in _RELEASE_STATE_FLAGS):
        return True
    if parts[0] == "fig-agent" and len(parts) > 1:
        return parts[1] in _RELEASE_STATE_COMMANDS
    if parts[0].startswith("/fig_"):
        return _SLASH_COMMANDS.get(parts[0], parts[0].removeprefix("/fig_")) in (
            _RELEASE_STATE_COMMANDS
        )
    return False


def _state(summary: dict[str, Any]) -> str:
    if summary.get("requires_human") is True:
        return "human_required"
    boundary = summary.get("decision_boundary")
    if isinstance(boundary, dict) and boundary.get("blocks_progress") is False:
        return "ready"
    return "blocked"


def _safe_command(summary: dict[str, Any]) -> str | None:
    command = summary.get("safe_command")
    if not isinstance(command, str) or not command:
        return None
    try:
        parts = shlex.split(command)
    except ValueError:
        return None
    if not parts:
        return None
    if parts[0] == "fig-agent":
        return command
    mapped = _SLASH_COMMANDS.get(parts[0])
    if mapped is None:
        return None if parts[0].startswith("/fig_") else command
    return shlex.join(["fig-agent", mapped, *parts[1:]])


def _next_payload(summary: dict[str, Any]) -> dict[str, Any]:
    command = _safe_command(summary)
    if _command_mutates_release_state(command):
        return {
            "command": None,
            "reason": (
                "accepted/golden/publication state mutation requires explicit "
                "manual release handling; inspect status before proceeding."
            ),
            "action": "manual_release_state_gate",
            "requires_human": True,
            "writes": False,
        }
    return {
        "command": command,
        "reason": str(summary.get("reason") or "inspect figure status"),
        "action": str(summary.get("action") or "inspect_status"),
        "requires_human": summary.get("requires_human") is True,
        "writes": _command_writes(command),
    }


def _alternatives(name: str, *, plugin_root: Path, workspace_root: Path) -> list[dict[str, Any]]:
    experiment = quality_next_experiment.build_next_experiment(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    recommendation = experiment.get("recommendation")
    benchmark_command = None
    if isinstance(recommendation, dict) and recommendation.get("allowed") is True:
        command = recommendation.get("command")
        benchmark_command = command if isinstance(command, str) else None
    alternatives = [
        {
            "command": f"fig-agent status {name} --json",
            "reason": "Inspect the full status vector before taking action.",
            "writes": False,
        }
    ]
    if benchmark_command:
        alternatives.append(
            {
                "command": benchmark_command,
                "reason": "Run the read-only smoke benchmark preview.",
                "writes": False,
            }
        )
    return alternatives


def build_next(
    name: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    if not example_dir.is_dir():
        return {
            "schema": SCHEMA,
            "success": False,
            "state": "missing_fixture",
            "name": name,
            "diagnostics": [
                _diagnostic("fixture_missing", f"examples/{name} does not exist.")
            ],
            "writes": [],
            "next": {
                "command": None,
                "reason": "Create or select an existing fixture under examples/.",
                "action": "create_or_select_fixture",
                "requires_human": False,
                "writes": False,
            },
            "alternatives": [],
            "duration_ms": int((time.monotonic() - started) * 1000),
        }
    status_payload = status.infer_stage(example_dir)
    summary = status_payload.get("next_action_summary")
    if not isinstance(summary, dict):
        summary = status.status_next_action_summary(status_payload)
    return {
        "schema": SCHEMA,
        "success": True,
        "state": _state(summary),
        "name": name,
        "diagnostics": [],
        "writes": [],
        "status": summary,
        "next": _next_payload(summary),
        "alternatives": _alternatives(
            name,
            plugin_root=paths.plugin_root,
            workspace_root=paths.workspace_root,
        ),
        "duration_ms": int((time.monotonic() - started) * 1000),
    }
