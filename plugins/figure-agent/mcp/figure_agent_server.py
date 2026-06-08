#!/usr/bin/env python3
"""Dependency-light MCP facade for figure-agent.

The server intentionally imports only the standard library at startup. Runtime
dependencies are diagnosed by doctor or exercised inside tool subprocesses.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "figure-agent"
SERVER_VERSION = "0.1.0"
ERROR_CATEGORIES = {
    "compile_failed",
    "dependency_missing",
    "doctor_failed",
    "export_failed",
    "fixture_missing",
    "invalid_fixture_name",
    "invalid_request",
    "operation_in_progress",
    "status_failed",
    "timeout",
    "unsupported_operation",
    "workspace_missing",
}


def _plugin_root() -> Path:
    value = os.environ.get("FIGURE_AGENT_PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")
    if value:
        return Path(value).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def _workspace_root(plugin_root: Path) -> Path | None:
    value = os.environ.get("FIGURE_AGENT_WORKSPACE") or os.environ.get("CLAUDE_PROJECT_DIR")
    if value:
        return Path(value).expanduser().resolve()
    cwd = Path.cwd().resolve()
    if cwd == plugin_root:
        return None
    return cwd


def _examples_dir(workspace_root: Path) -> Path:
    return workspace_root / "examples"


def _is_safe_fixture_name(name: Any) -> bool:
    if not isinstance(name, str) or not name.strip():
        return False
    relative = Path(name)
    return not relative.is_absolute() and len(relative.parts) == 1 and ".." not in relative.parts


def _tool_envelope(
    schema: str,
    *,
    success: bool,
    started: float,
    error: dict[str, Any] | None = None,
    **payload: Any,
) -> dict[str, Any]:
    result = {
        "schema": schema,
        "success": success,
        "artifacts": payload.pop("artifacts", []),
        "duration_ms": int((time.monotonic() - started) * 1000),
    }
    result.update(payload)
    if error is not None:
        result["error"] = error
    return result


def _error(category: str, message: str, next_action: str | None = None) -> dict[str, str]:
    if category not in ERROR_CATEGORIES:
        raise ValueError(f"unknown MCP error category: {category}")
    payload = {"category": category, "message": message}
    if next_action:
        payload["next_action"] = next_action
    return payload


@contextmanager
def _fixture_lock(
    workspace_root: Path,
    name: str,
    operation: str,
) -> Iterator[dict[str, Any] | None]:
    lock_root = workspace_root / "examples" / name / "build" / ".mcp-locks"
    lock_root.mkdir(parents=True, exist_ok=True)
    lock_path = lock_root / "mutation.lock"
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        active = "unknown"
        try:
            data = json.loads(lock_path.read_text(encoding="utf-8"))
            active = str(data.get("operation") or "unknown")
        except (OSError, json.JSONDecodeError):
            pass
        yield {
            "active_operation": active,
            "lock_path": lock_path.relative_to(workspace_root).as_posix(),
        }
        return
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"operation": operation, "created_at": time.time()}, handle, sort_keys=True)
        yield None
    finally:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def _bundle_diagnostics(plugin_root: Path) -> dict[str, Any]:
    required = [
        plugin_root / ".claude-plugin" / "plugin.json",
        plugin_root / "scripts",
        plugin_root / "styles",
        plugin_root / "styles" / "polymer-paper-preamble.sty",
    ]
    missing = [str(path.relative_to(plugin_root)) for path in required if not path.exists()]
    return {
        "state": "ok" if not missing else "missing",
        "plugin_root": str(plugin_root),
        "missing": missing,
    }


def _workspace_diagnostics(plugin_root: Path) -> dict[str, Any]:
    workspace_root = _workspace_root(plugin_root)
    if workspace_root is None:
        return {
            "state": "missing",
            "workspace_root": None,
            "missing": ["examples"],
            "reason": "no FIGURE_AGENT_WORKSPACE or CLAUDE_PROJECT_DIR; cwd is plugin root",
        }
    missing = []
    if not _examples_dir(workspace_root).is_dir():
        missing.append("examples")
    return {
        "state": "ok" if not missing else "missing",
        "workspace_root": str(workspace_root),
        "missing": missing,
    }


def _dependency_diagnostics() -> dict[str, Any]:
    tex_engine = os.environ.get("LATEX_ENGINE") or "lualatex"
    binaries = ("uv", "python3", tex_engine, "pdftocairo", "rsvg-convert")
    missing = [name for name in binaries if shutil.which(name) is None]
    for module_name in ("yaml", "PIL"):
        try:
            __import__(module_name)
        except ImportError:
            missing.append(f"python:{module_name}")
    return {"state": "ok" if not missing else "missing", "missing": missing}


def _doctor(_: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    plugin_root = _plugin_root()
    bundle = _bundle_diagnostics(plugin_root)
    workspace = _workspace_diagnostics(plugin_root)
    dependencies = _dependency_diagnostics()
    success = (
        bundle["state"] == "ok"
        and workspace["state"] == "ok"
        and dependencies["state"] == "ok"
    )
    return _tool_envelope(
        "figure-agent.mcp.doctor.v1",
        success=success,
        started=started,
        bundle=bundle,
        workspace=workspace,
        dependencies=dependencies,
        error=None
        if success
        else _error("doctor_failed", "One or more doctor checks failed."),
    )


def _validated_workspace_and_name(
    arguments: dict[str, Any],
    started: float,
    schema: str,
    *,
    require_fixture: bool = False,
) -> tuple[Path, str] | dict[str, Any]:
    name = arguments.get("name")
    if not _is_safe_fixture_name(name):
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            error=_error(
                "invalid_fixture_name",
                "fixture name must be a single examples/<name> directory name",
            ),
        )
    plugin_root = _plugin_root()
    workspace_root = _workspace_root(plugin_root)
    if workspace_root is None or not _examples_dir(workspace_root).is_dir():
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            error=_error(
                "workspace_missing",
                "workspace examples/ directory not found",
                "Set FIGURE_AGENT_WORKSPACE or CLAUDE_PROJECT_DIR to a project with examples/.",
            ),
        )
    if require_fixture and not (_examples_dir(workspace_root) / str(name)).is_dir():
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=str(name),
            error=_error(
                "fixture_missing",
                f"examples/{name} not found",
                f"Create examples/{name} or choose an existing fixture.",
            ),
        )
    return workspace_root, str(name)


def _artifact_descriptor(
    workspace_root: Path,
    path: Path,
    uri: str,
    media_type: str,
) -> dict[str, Any]:
    return {
        "uri": uri,
        "path": path.relative_to(workspace_root).as_posix(),
        "exists": path.exists(),
        "media_type": media_type,
    }


def _status_artifacts(workspace_root: Path, name: str) -> list[dict[str, Any]]:
    fixture = _examples_dir(workspace_root) / name
    return [
        _artifact_descriptor(
            workspace_root,
            fixture / "build" / f"{name}.png",
            f"figure://{name}/build/png",
            "image/png",
        ),
        _artifact_descriptor(
            workspace_root,
            fixture / "build" / f"{name}.pdf",
            f"figure://{name}/build/pdf",
            "application/pdf",
        ),
        _artifact_descriptor(
            workspace_root,
            fixture / "exports" / f"{name}.svg",
            f"figure://{name}/exports/svg",
            "image/svg+xml",
        ),
        _artifact_descriptor(
            workspace_root,
            fixture / "exports" / f"{name}.png",
            f"figure://{name}/exports/png",
            "image/png",
        ),
        _artifact_descriptor(
            workspace_root,
            fixture / "build" / "visual_clash.json",
            f"figure://{name}/audit/visual-clash",
            "application/json",
        ),
        _artifact_descriptor(
            workspace_root,
            fixture / "build" / "text_boundary_clash.json",
            f"figure://{name}/audit/text-boundary",
            "application/json",
        ),
        _artifact_descriptor(
            workspace_root,
            fixture / "build" / "label_path_proximity.json",
            f"figure://{name}/audit/label-path",
            "application/json",
        ),
        _artifact_descriptor(
            workspace_root,
            fixture / "build" / "perception" / "extract.yaml",
            f"figure://{name}/perception/extract",
            "application/yaml",
        ),
    ]


def _tool_env(plugin_root: Path, workspace_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(plugin_root)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace_root)
    return env


def _run_fig_agent(
    args: list[str],
    *,
    workspace_root: Path,
    timeout_seconds: int = 120,
) -> subprocess.CompletedProcess[str]:
    plugin_root = _plugin_root()
    command = [
        sys.executable,
        str(plugin_root / "bin" / "fig-agent"),
        *args,
    ]
    return subprocess.run(
        command,
        cwd=workspace_root,
        env=_tool_env(plugin_root, workspace_root),
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout_seconds,
    )


def _bounded(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def _status(arguments: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    schema = "figure-agent.mcp.status.v1"
    resolved = _validated_workspace_and_name(arguments, started, schema)
    if isinstance(resolved, dict):
        return resolved
    workspace_root, name = resolved
    try:
        result = _run_fig_agent(["status", name, "--json"], workspace_root=workspace_root)
    except FileNotFoundError:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            error=_error("dependency_missing", "Python executable for fig-agent not found"),
        )
    except subprocess.TimeoutExpired as exc:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            stdout=_bounded(exc.stdout or ""),
            stderr=_bounded(exc.stderr or ""),
            error=_error("timeout", "fig-agent status timed out"),
        )
    if result.returncode != 0:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            exit_code=result.returncode,
            stdout=_bounded(result.stdout),
            stderr=_bounded(result.stderr),
            error=_error("status_failed", "fig-agent status failed"),
        )
    try:
        status_payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            stdout=_bounded(result.stdout),
            stderr=_bounded(result.stderr),
            error=_error("status_failed", "fig-agent status returned invalid JSON"),
        )
    return _tool_envelope(
        schema,
        success=True,
        started=started,
        name=name,
        status=status_payload,
        artifacts=_status_artifacts(workspace_root, name),
    )


def _compile(arguments: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    schema = "figure-agent.mcp.compile.v1"
    resolved = _validated_workspace_and_name(arguments, started, schema, require_fixture=True)
    if isinstance(resolved, dict):
        return resolved
    workspace_root, name = resolved
    command = ["compile", name]
    if bool(arguments.get("strict")):
        command.append("--strict")
    with _fixture_lock(workspace_root, name, "compile") as lock:
        if lock is not None:
            return _tool_envelope(
                schema,
                success=False,
                started=started,
                name=name,
                operation=lock["active_operation"],
                error=_error(
                    "operation_in_progress",
                    f"another mutating operation is active for examples/{name}",
                    "Retry after the active operation finishes.",
                ),
            )
        try:
            result = _run_fig_agent(command, workspace_root=workspace_root, timeout_seconds=300)
        except FileNotFoundError:
            return _tool_envelope(
                schema,
                success=False,
                started=started,
                name=name,
                error=_error("dependency_missing", "Python executable for fig-agent not found"),
            )
        except subprocess.TimeoutExpired as exc:
            return _tool_envelope(
                schema,
                success=False,
                started=started,
                name=name,
                stdout=_bounded(exc.stdout or ""),
                stderr=_bounded(exc.stderr or ""),
                error=_error("timeout", "fig-agent compile timed out"),
            )
    success = result.returncode == 0
    return _tool_envelope(
        schema,
        success=success,
        started=started,
        name=name,
        exit_code=result.returncode,
        stdout=_bounded(result.stdout),
        stderr=_bounded(result.stderr),
        artifacts=_status_artifacts(workspace_root, name),
        warnings=[],
        error=None if success else _error("compile_failed", "fig-agent compile failed"),
    )


def _export(arguments: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    schema = "figure-agent.mcp.export.v1"
    resolved = _validated_workspace_and_name(arguments, started, schema, require_fixture=True)
    if isinstance(resolved, dict):
        return resolved
    workspace_root, name = resolved
    command = ["export", name]
    if bool(arguments.get("force_golden")):
        command.append("--force-golden")
    if bool(arguments.get("skip_critique")):
        command.append("--skip-critique")
    with _fixture_lock(workspace_root, name, "export") as lock:
        if lock is not None:
            return _tool_envelope(
                schema,
                success=False,
                started=started,
                name=name,
                operation=lock["active_operation"],
                error=_error(
                    "operation_in_progress",
                    f"another mutating operation is active for examples/{name}",
                    "Retry after the active operation finishes.",
                ),
            )
        try:
            result = _run_fig_agent(command, workspace_root=workspace_root, timeout_seconds=300)
        except FileNotFoundError:
            return _tool_envelope(
                schema,
                success=False,
                started=started,
                name=name,
                error=_error("dependency_missing", "Python executable for fig-agent not found"),
            )
        except subprocess.TimeoutExpired as exc:
            return _tool_envelope(
                schema,
                success=False,
                started=started,
                name=name,
                stdout=_bounded(exc.stdout or ""),
                stderr=_bounded(exc.stderr or ""),
                error=_error("timeout", "fig-agent export timed out"),
            )
    success = result.returncode == 0
    return _tool_envelope(
        schema,
        success=success,
        started=started,
        name=name,
        exit_code=result.returncode,
        stdout=_bounded(result.stdout),
        stderr=_bounded(result.stderr),
        artifacts=_status_artifacts(workspace_root, name),
        error=None if success else _error("export_failed", "fig-agent export failed"),
    )


def _next_action(arguments: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    schema = "figure-agent.mcp.next-action.v1"
    status_payload = _status(arguments)
    if not status_payload.get("success"):
        status_payload["schema"] = schema
        return status_payload
    name = str(arguments["name"])
    status = status_payload.get("status", {})
    goal = str(arguments.get("goal") or "review current figure state")
    next_hint = status.get("next") if isinstance(status, dict) else None
    return _tool_envelope(
        schema,
        success=True,
        started=started,
        action="run_loop_checkpoint",
        stop_boundary=next_hint,
        safe_command=None,
        mcp_tool={
            "name": "figure_agent_loop_checkpoint",
            "arguments": {"name": name, "goal": goal},
        },
        requires_human=False,
        requires_host_vision=False,
        status=status,
    )


def _loop_checkpoint(arguments: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    schema = "figure-agent.mcp.loop-checkpoint.v1"
    resolved = _validated_workspace_and_name(arguments, started, schema, require_fixture=True)
    if isinstance(resolved, dict):
        return resolved
    workspace_root, name = resolved
    goal = str(arguments.get("goal") or "verify current figure state")
    with _fixture_lock(workspace_root, name, "loop_checkpoint") as lock:
        if lock is not None:
            return _tool_envelope(
                schema,
                success=False,
                started=started,
                name=name,
                operation=lock["active_operation"],
                error=_error(
                    "operation_in_progress",
                    f"another mutating operation is active for examples/{name}",
                    "Retry after the active operation finishes.",
                ),
            )
        try:
            result = _run_fig_agent(
                ["loop", name, "--goal", goal, "--json"],
                workspace_root=workspace_root,
                timeout_seconds=300,
            )
        except FileNotFoundError:
            return _tool_envelope(
                schema,
                success=False,
                started=started,
                name=name,
                error=_error("dependency_missing", "Python executable for fig-agent not found"),
            )
        except subprocess.TimeoutExpired as exc:
            return _tool_envelope(
                schema,
                success=False,
                started=started,
                name=name,
                stdout=_bounded(exc.stdout or ""),
                stderr=_bounded(exc.stderr or ""),
                error=_error("timeout", "fig-agent loop checkpoint timed out"),
            )
    payload: dict[str, Any] = {}
    if result.stdout.strip():
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {"stdout": _bounded(result.stdout)}
    success = result.returncode == 0
    return _tool_envelope(
        schema,
        success=success,
        started=started,
        name=name,
        exit_code=result.returncode,
        checkpoint=payload,
        stderr=_bounded(result.stderr),
        error=None if success else _error("unsupported_operation", "fig-agent loop failed"),
    )


TOOLS: dict[str, dict[str, Any]] = {
    "figure_agent_doctor": {
        "description": "Diagnose figure-agent bundle, workspace, and host dependencies.",
        "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
        "handler": _doctor,
    },
    "figure_agent_status": {
        "description": "Return structured figure status and artifact descriptors.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        "handler": _status,
    },
    "figure_agent_compile": {
        "description": "Run the existing compile chain for one fixture.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {"name": {"type": "string"}, "strict": {"type": "boolean"}},
        },
        "handler": _compile,
    },
    "figure_agent_export": {
        "description": "Run the existing export policy for one fixture.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "force_golden": {"type": "boolean"},
                "skip_critique": {"type": "boolean"},
            },
        },
        "handler": _export,
    },
    "figure_agent_next_action": {
        "description": "Summarize the next structured figure-agent action.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "mode": {"type": "string"},
                "goal": {"type": "string"},
            },
        },
        "handler": _next_action,
    },
    "figure_agent_loop_checkpoint": {
        "description": "Record a verify-only loop checkpoint for one fixture.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {"name": {"type": "string"}, "goal": {"type": "string"}},
        },
        "handler": _loop_checkpoint,
    },
}


def _resource_templates() -> list[dict[str, str]]:
    return [
        {
            "uriTemplate": "figure://{name}/build/png",
            "name": "Build PNG",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "figure://{name}/build/pdf",
            "name": "Build PDF",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "figure://{name}/exports/svg",
            "name": "Export SVG",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "figure://{name}/exports/png",
            "name": "Export PNG",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "figure://{name}/audit/visual-clash",
            "name": "Visual clash audit",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "figure://{name}/audit/text-boundary",
            "name": "Text boundary audit",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "figure://{name}/audit/label-path",
            "name": "Label path audit",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "figure://{name}/perception/extract",
            "name": "Perception extract",
            "mimeType": "application/json",
        },
    ]


def _list_tools() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": name,
                "description": spec["description"],
                "inputSchema": spec["inputSchema"],
            }
            for name, spec in TOOLS.items()
        ]
    }


def _call_tool(params: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(params, dict):
        payload = _tool_envelope(
            "figure-agent.mcp.error.v1",
            success=False,
            started=time.monotonic(),
            error=_error("invalid_request", "tools/call params must be an object"),
        )
        return _tool_result(payload, is_error=True)
    name = params.get("name")
    arguments = params["arguments"] if "arguments" in params else {}
    if not isinstance(arguments, dict):
        payload = _tool_envelope(
            "figure-agent.mcp.error.v1",
            success=False,
            started=time.monotonic(),
            error=_error("invalid_request", "tools/call arguments must be an object"),
        )
        return _tool_result(payload, is_error=True)
    if name not in TOOLS:
        payload = _tool_envelope(
            "figure-agent.mcp.error.v1",
            success=False,
            started=time.monotonic(),
            error=_error("unsupported_operation", f"unknown tool: {name}"),
        )
        return _tool_result(payload, is_error=True)
    payload = TOOLS[str(name)]["handler"](arguments)
    return _tool_result(payload, is_error=not bool(payload.get("success")))


def _tool_result(payload: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, sort_keys=True),
            }
        ],
        "isError": is_error,
    }


def _handle(method: str, params: dict[str, Any]) -> dict[str, Any] | None:
    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return _list_tools()
    if method == "tools/call":
        return _call_tool(params)
    if method == "resources/list":
        return {"resources": []}
    if method == "resources/templates/list":
        return {"resourceTemplates": _resource_templates()}
    if method == "resources/read":
        return {
            "contents": [
                {
                    "uri": str(params.get("uri", "")),
                    "mimeType": "application/json",
                    "text": json.dumps(
                        {
                            "schema": "figure-agent.mcp.resource.v1",
                            "success": False,
                            "error": _error(
                                "unsupported_operation",
                                "Phase 1 resources expose descriptors only; "
                                "use figure_agent_status.",
                            ),
                        },
                        sort_keys=True,
                    ),
                }
            ]
        }
    raise ValueError(f"unsupported method: {method}")


def serve() -> int:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"parse error: {exc.msg}"},
            }
            print(json.dumps(response, separators=(",", ":")), flush=True)
            continue
        if not isinstance(request, dict):
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "invalid request"},
            }
            print(json.dumps(response, separators=(",", ":")), flush=True)
            continue
        if "id" not in request:
            continue
        request_id = request.get("id")
        try:
            params = request["params"] if "params" in request else {}
            result = _handle(str(request.get("method")), params)
        except Exception as exc:  # keep protocol alive for structured host errors
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": str(exc)},
            }
        else:
            if result is None:
                continue
            response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        print(json.dumps(response, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(serve())
