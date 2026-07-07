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
from hashlib import sha256
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
SCRIPT_IMPORT_DIRS = (
    SCRIPTS_DIR,
    SCRIPTS_DIR / "checks",
    SCRIPTS_DIR / "candidates",
    SCRIPTS_DIR / "quality",
    SCRIPTS_DIR / "loop",
    SCRIPTS_DIR / "driver",
    SCRIPTS_DIR / "svg_polish",
)
for script_dir in reversed(SCRIPT_IMPORT_DIRS):
    sys.path.insert(0, str(script_dir))

import runtime_paths  # noqa: E402

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "figure-agent"
SERVER_VERSION = "0.9.3"
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
    return PLUGIN_ROOT


def _workspace_root(plugin_root: Path) -> Path | None:
    workspace_root, _source = runtime_paths.workspace_root_with_source(plugin_root)
    return workspace_root


def _examples_dir(workspace_root: Path) -> Path:
    return workspace_root / "examples"


def _is_safe_fixture_name(name: Any) -> bool:
    if not isinstance(name, str) or not name.strip():
        return False
    relative = Path(name)
    return not relative.is_absolute() and len(relative.parts) == 1 and ".." not in relative.parts


def _is_safe_panel_id(panel_id: Any) -> bool:
    if not isinstance(panel_id, str) or not panel_id.strip():
        return False
    return all(char.isalnum() or char in {"_", "-"} for char in panel_id)


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
    paths = runtime_paths.resolve_runtime_paths(plugin_root=plugin_root, workspace_root=Path.cwd())
    return runtime_paths.bundle_diagnostics(paths)


def _workspace_diagnostics(plugin_root: Path) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(plugin_root=plugin_root, workspace_root=Path.cwd())
    diagnostics = runtime_paths.workspace_diagnostics(paths)
    if diagnostics["workspace_root"] is None:
        diagnostics["reason"] = (
            "no FIGURE_AGENT_WORKSPACE or CLAUDE_PROJECT_DIR; cwd is plugin root"
        )
    return diagnostics


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
        bundle["state"] == "ok" and workspace["state"] == "ok" and dependencies["state"] == "ok"
    )
    return _tool_envelope(
        "figure-agent.mcp.doctor.v1",
        success=success,
        started=started,
        bundle=bundle,
        workspace=workspace,
        dependencies=dependencies,
        error=None if success else _error("doctor_failed", "One or more doctor checks failed."),
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


def _validated_workspace(
    started: float,
    schema: str,
) -> Path | dict[str, Any]:
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
    return workspace_root


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


def _resource_specs(name: str) -> dict[tuple[str, ...], tuple[Path, str]]:
    fixture = Path("examples") / name
    return {
        ("build", "png"): (fixture / "build" / f"{name}.png", "image/png"),
        ("build", "pdf"): (fixture / "build" / f"{name}.pdf", "application/pdf"),
        ("exports", "pdf"): (fixture / "exports" / f"{name}.pdf", "application/pdf"),
        ("exports", "svg"): (fixture / "exports" / f"{name}.svg", "image/svg+xml"),
        ("exports", "png"): (fixture / "exports" / f"{name}.png", "image/png"),
        ("exports", "tif"): (fixture / "exports" / f"{name}.tif", "image/tiff"),
        ("audit", "visual-clash"): (
            fixture / "build" / "visual_clash.json",
            "application/json",
        ),
        ("audit", "text-boundary"): (
            fixture / "build" / "text_boundary_clash.json",
            "application/json",
        ),
        ("audit", "label-path"): (
            fixture / "build" / "label_path_proximity.json",
            "application/json",
        ),
        ("audit", "undeclared-geometry"): (
            fixture / "build" / "undeclared_geometry.json",
            "application/json",
        ),
        ("perception", "extract"): (
            fixture / "build" / "perception" / "extract.yaml",
            "application/yaml",
        ),
    }


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _path_metadata(
    *,
    workspace_root: Path,
    relative_path: Path,
    uri: str,
    media_type: str,
) -> dict[str, Any]:
    path = workspace_root / relative_path
    payload: dict[str, Any] = {
        "schema": "figure-agent.mcp.resource-metadata.v1",
        "success": True,
        "uri": uri,
        "path": relative_path.as_posix(),
        "exists": path.exists(),
        "media_type": media_type,
    }
    if not path.exists():
        return payload
    try:
        resolved = path.resolve(strict=True)
        workspace_resolved = workspace_root.resolve(strict=True)
    except OSError as exc:
        payload.update(
            {
                "success": False,
                "blocked": True,
                "reason": f"resolve_failed:{exc.__class__.__name__}",
            }
        )
        return payload
    if not (resolved == workspace_resolved or resolved.is_relative_to(workspace_resolved)):
        payload.update({"success": False, "blocked": True, "reason": "path_escape"})
        return payload
    if resolved.is_file():
        payload["size_bytes"] = resolved.stat().st_size
        payload["sha256"] = _sha256_file(resolved)
    return payload


def _candidate_manifest_metadata(
    *,
    workspace_root: Path,
    name: str,
    candidate_id: str,
    uri: str,
) -> dict[str, Any]:
    relative_path = (
        Path("examples") / name / "build" / "candidates" / candidate_id / "candidate_manifest.json"
    )
    path = workspace_root / relative_path
    payload: dict[str, Any] = {
        "schema": "figure-agent.mcp.resource-metadata.v1",
        "success": True,
        "uri": uri,
        "path": relative_path.as_posix(),
        "exists": path.exists(),
        "media_type": "application/json",
    }
    build_dir = workspace_root / "examples" / name / "build"
    root = build_dir / "candidates"
    sandbox = path.parent
    for label, candidate in (
        ("build", build_dir),
        ("candidates", root),
        (candidate_id, sandbox),
    ):
        if candidate.is_symlink():
            payload.update(
                {
                    "success": False,
                    "blocked": True,
                    "reason": f"sandbox_symlink_forbidden:{label}",
                }
            )
            return payload
    if path.is_symlink():
        payload.update(
            {
                "success": False,
                "blocked": True,
                "reason": "sandbox_symlink_forbidden:candidate_manifest.json",
            }
        )
        return payload
    if not path.exists():
        return payload
    try:
        resolved = path.resolve(strict=True)
        sandbox_resolved = sandbox.resolve(strict=True)
    except OSError as exc:
        payload.update(
            {
                "success": False,
                "blocked": True,
                "reason": f"resolve_failed:{exc.__class__.__name__}",
            }
        )
        return payload
    if not (resolved == sandbox_resolved or resolved.is_relative_to(sandbox_resolved)):
        payload.update({"success": False, "blocked": True, "reason": "path_escape"})
        return payload
    if resolved.is_file():
        payload["size_bytes"] = resolved.stat().st_size
        payload["sha256"] = _sha256_file(resolved)
    return payload


def _parse_figure_uri(uri: str) -> tuple[str, tuple[str, ...]] | None:
    parsed = urlparse(uri)
    if parsed.scheme != "figure" or not _is_safe_fixture_name(parsed.netloc):
        return None
    parts = tuple(part for part in parsed.path.split("/") if part)
    if not parts:
        return None
    return parsed.netloc, parts


def _resource_metadata(uri: str) -> dict[str, Any]:
    parsed = _parse_figure_uri(uri)
    if parsed is None:
        return {
            "schema": "figure-agent.mcp.resource-metadata.v1",
            "success": False,
            "uri": uri,
            "error": _error(
                "invalid_request",
                "resource uri must match a supported figure://{name}/... template",
            ),
        }
    name, resource_key = parsed
    plugin_root = _plugin_root()
    workspace_root = _workspace_root(plugin_root)
    if workspace_root is None or not _examples_dir(workspace_root).is_dir():
        return {
            "schema": "figure-agent.mcp.resource-metadata.v1",
            "success": False,
            "uri": uri,
            "error": _error(
                "workspace_missing",
                "workspace examples/ directory not found",
                "Set FIGURE_AGENT_WORKSPACE or CLAUDE_PROJECT_DIR to a project with examples/.",
            ),
        }
    if resource_key == ("audit", "evidence-graph"):
        return {
            "schema": "figure-agent.mcp.resource-metadata.v1",
            "success": True,
            "uri": uri,
            "path": f"examples/{name}/build/audit_evidence_graph.json",
            "exists": False,
            "media_type": "application/json",
            "virtual": True,
            "content_schema": "figure-agent.audit-evidence-graph.v1",
        }
    specs = _resource_specs(name)
    if len(resource_key) == 3 and resource_key[0] == "panel" and resource_key[2] == "intent":
        panel_id = resource_key[1]
        if not _is_safe_panel_id(panel_id):
            return {
                "schema": "figure-agent.mcp.resource-metadata.v1",
                "success": False,
                "uri": uri,
                "error": _error("invalid_request", "invalid panel id"),
            }
        return {
            "schema": "figure-agent.mcp.resource-metadata.v1",
            "success": True,
            "uri": uri,
            "virtual": True,
            "content_schema": "figure-agent.candidate-panel-model.v1",
            "recommended_tool": "figure_agent_analyze_panel",
            "arguments": {"name": name, "panel_id": panel_id},
        }
    if (
        len(resource_key) == 3
        and resource_key[0] == "candidates"
        and resource_key[2] in {"manifest", "review"}
    ):
        candidate_id = resource_key[1]
        if not _is_safe_fixture_name(candidate_id):
            return {
                "schema": "figure-agent.mcp.resource-metadata.v1",
                "success": False,
                "uri": uri,
                "error": _error("invalid_request", "invalid candidate id"),
            }
        if resource_key[2] == "review":
            return {
                "schema": "figure-agent.mcp.resource-metadata.v1",
                "success": True,
                "uri": uri,
                "virtual": True,
                "content_schema": "figure-agent.candidate-review-packet.v1",
                "recommended_tool": "figure_agent_compare_candidate",
                "arguments": {"name": name, "candidate_id": candidate_id},
            }
        return _candidate_manifest_metadata(
            workspace_root=workspace_root,
            name=name,
            candidate_id=candidate_id,
            uri=uri,
        )
    if resource_key not in specs:
        return {
            "schema": "figure-agent.mcp.resource-metadata.v1",
            "success": False,
            "uri": uri,
            "error": _error(
                "unsupported_operation",
                f"unsupported resource uri: {uri}",
            ),
        }
    relative_path, media_type = specs[resource_key]
    return _path_metadata(
        workspace_root=workspace_root,
        relative_path=relative_path,
        uri=uri,
        media_type=media_type,
    )


def _status_artifacts(workspace_root: Path, name: str) -> list[dict[str, Any]]:
    return [
        _artifact_descriptor(
            workspace_root,
            workspace_root / path,
            f"figure://{name}/{'/'.join(key)}",
            mime_type,
        )
        for key, (path, mime_type) in _resource_specs(name).items()
    ]


def _tool_env(plugin_root: Path, workspace_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(plugin_root)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace_root)
    import_paths = os.pathsep.join(str(path) for path in SCRIPT_IMPORT_DIRS)
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        import_paths
        if not existing_pythonpath
        else os.pathsep.join((import_paths, existing_pythonpath))
    )
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


def _operation_in_progress(
    *,
    schema: str,
    started: float,
    name: str,
    lock: dict[str, Any],
) -> dict[str, Any]:
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


def _run_fig_agent_enveloped(
    *,
    schema: str,
    started: float,
    command: list[str],
    workspace_root: Path,
    timeout_seconds: int,
    timeout_message: str,
    name: str | None = None,
) -> subprocess.CompletedProcess[str] | dict[str, Any]:
    payload = {"name": name} if name is not None else {}
    try:
        return _run_fig_agent(
            command,
            workspace_root=workspace_root,
            timeout_seconds=timeout_seconds,
        )
    except FileNotFoundError:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            **payload,
            error=_error("dependency_missing", "Python executable for fig-agent not found"),
        )
    except subprocess.TimeoutExpired as exc:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            **payload,
            stdout=_bounded(exc.stdout or ""),
            stderr=_bounded(exc.stderr or ""),
            error=_error("timeout", timeout_message),
        )


def _json_payload_from_result(
    *,
    result: subprocess.CompletedProcess[str],
    schema: str,
    started: float,
    invalid_json_message: str,
    name: str | None = None,
    required: bool = True,
    error_category: str = "unsupported_operation",
) -> tuple[Any, dict[str, Any] | None]:
    if not result.stdout.strip() and not required:
        return {}, None
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError:
        if not required:
            return {"stdout": _bounded(result.stdout)}, None
        payload = {"name": name} if name is not None else {}
        return None, _tool_envelope(
            schema,
            success=False,
            started=started,
            **payload,
            stdout=_bounded(result.stdout),
            stderr=_bounded(result.stderr),
            error=_error(error_category, invalid_json_message),
        )


def _status(arguments: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    schema = "figure-agent.mcp.status.v1"
    resolved = _validated_workspace_and_name(arguments, started, schema)
    if isinstance(resolved, dict):
        return resolved
    workspace_root, name = resolved
    result = _run_fig_agent_enveloped(
        schema=schema,
        started=started,
        command=["status", name, "--json"],
        workspace_root=workspace_root,
        timeout_seconds=120,
        timeout_message="fig-agent status timed out",
        name=name,
    )
    if isinstance(result, dict):
        return result
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
    status_payload, json_error = _json_payload_from_result(
        result=result,
        schema=schema,
        started=started,
        name=name,
        invalid_json_message="fig-agent status returned invalid JSON",
        error_category="status_failed",
    )
    if json_error is not None:
        return json_error
    return _tool_envelope(
        schema,
        success=True,
        started=started,
        name=name,
        status=status_payload,
        artifacts=_status_artifacts(workspace_root, name),
    )


def _run_json_fig_agent_tool(
    *,
    arguments: dict[str, Any],
    schema: str,
    command: list[str],
    payload_key: str,
    failure_message: str,
) -> dict[str, Any]:
    started = time.monotonic()
    resolved = _validated_workspace_and_name(arguments, started, schema, require_fixture=True)
    if isinstance(resolved, dict):
        return resolved
    workspace_root, name = resolved
    result = _run_fig_agent_enveloped(
        schema=schema,
        started=started,
        command=command,
        workspace_root=workspace_root,
        timeout_seconds=120,
        timeout_message=f"{failure_message} timed out",
        name=name,
    )
    if isinstance(result, dict):
        return result
    if result.returncode != 0:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            exit_code=result.returncode,
            stdout=_bounded(result.stdout),
            stderr=_bounded(result.stderr),
            error=_error("unsupported_operation", failure_message),
        )
    payload, json_error = _json_payload_from_result(
        result=result,
        schema=schema,
        started=started,
        name=name,
        invalid_json_message=f"{failure_message} returned invalid JSON",
    )
    if json_error is not None:
        return json_error
    if (
        isinstance(payload, dict)
        and isinstance(payload.get("candidates"), list)
        and len(payload["candidates"]) == 0
        and payload.get("refusals")
    ):
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            no_op=True,
            refusals=payload["refusals"],
            **{payload_key: payload},
        )
    return _tool_envelope(
        schema,
        success=True,
        started=started,
        name=name,
        **{payload_key: payload},
    )


def _run_workspace_json_fig_agent_tool(
    *,
    schema: str,
    command: list[str],
    payload_key: str,
    failure_message: str,
) -> dict[str, Any]:
    started = time.monotonic()
    resolved = _validated_workspace(started, schema)
    if isinstance(resolved, dict):
        return resolved
    workspace_root = resolved
    result = _run_fig_agent_enveloped(
        schema=schema,
        started=started,
        command=command,
        workspace_root=workspace_root,
        timeout_seconds=120,
        timeout_message=f"{failure_message} timed out",
    )
    if isinstance(result, dict):
        return result
    if result.returncode != 0:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            exit_code=result.returncode,
            stdout=_bounded(result.stdout),
            stderr=_bounded(result.stderr),
            error=_error("unsupported_operation", failure_message),
        )
    payload, json_error = _json_payload_from_result(
        result=result,
        schema=schema,
        started=started,
        invalid_json_message=f"{failure_message} returned invalid JSON",
    )
    if json_error is not None:
        return json_error
    return _tool_envelope(
        schema,
        success=True,
        started=started,
        **{payload_key: payload},
    )


def _quality_map(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.quality-map.v1",
        command=["quality-map", name, "--json"],
        payload_key="ledger",
        failure_message="fig-agent quality-map failed",
    )


def _context_pack(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.context-pack.v1",
        command=["context-pack", name, "--json"],
        payload_key="context_pack",
        failure_message="fig-agent context-pack failed",
    )


def _propose_patch(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.propose-patch.v1",
        command=["propose", name, "--json"],
        payload_key="plan",
        failure_message="fig-agent propose failed",
    )


def _analyze_figure(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.analyze-figure.v1",
        command=["intent", name, "--json"],
        payload_key="intent",
        failure_message="fig-agent intent failed",
    )


def _propose_improvements(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.propose-improvements.v1",
        command=["candidates", name, "--json"],
        payload_key="candidate_set",
        failure_message="fig-agent candidates failed",
    )


def _materialize_candidate_set(arguments: dict[str, Any]) -> dict[str, Any]:
    schema = "figure-agent.mcp.materialize-candidate-set.v1"
    started = time.monotonic()
    resolved = _validated_workspace_and_name(arguments, started, schema, require_fixture=True)
    if isinstance(resolved, dict):
        return resolved
    workspace_root, name = resolved
    candidate_set = str(arguments.get("candidate_set") or "build/candidates/candidate_set.json")
    panel_id = arguments.get("panel_id")
    family = arguments.get("family")
    if panel_id is not None and not _is_safe_panel_id(panel_id):
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            error=_error("invalid_request", "panel_id must match [A-Za-z0-9_-]+"),
        )
    if family is not None and not _is_safe_fixture_name(family):
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            error=_error("invalid_fixture_name", "family must be a single candidate family name"),
        )
    command = ["candidates", name, "--json", "--output", candidate_set]
    if panel_id is not None:
        command.extend(["--panel", str(panel_id)])
    if family is not None:
        command.extend(["--family", str(family)])
    with _fixture_lock(workspace_root, name, "materialize_candidate_set") as lock:
        if lock is not None:
            return _operation_in_progress(schema=schema, started=started, name=name, lock=lock)
        result = _run_fig_agent_enveloped(
            schema=schema,
            started=started,
            command=command,
            workspace_root=workspace_root,
            timeout_seconds=120,
            timeout_message="fig-agent candidates timed out",
            name=name,
        )
        if isinstance(result, dict):
            return result
    if result.returncode != 0:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            exit_code=result.returncode,
            stdout=_bounded(result.stdout),
            stderr=_bounded(result.stderr),
            error=_error("unsupported_operation", "fig-agent candidates failed"),
        )
    payload, json_error = _json_payload_from_result(
        result=result,
        schema=schema,
        started=started,
        name=name,
        invalid_json_message="fig-agent candidates returned invalid JSON",
    )
    if json_error is not None:
        return json_error
    return _tool_envelope(
        schema,
        success=True,
        started=started,
        name=name,
        candidate_set_path=candidate_set,
        candidate_set=payload,
    )


def _analyze_panel(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    panel_id = str(arguments.get("panel_id") or "")
    if not _is_safe_panel_id(panel_id):
        return _tool_envelope(
            "figure-agent.mcp.analyze-panel.v1",
            success=False,
            started=time.monotonic(),
            name=name,
            error=_error("invalid_request", "panel_id must match [A-Za-z0-9_-]+"),
        )
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.analyze-panel.v1",
        command=["analyze-panel", name, panel_id, "--json"],
        payload_key="panel_model",
        failure_message="fig-agent analyze-panel failed",
    )


def _propose_panel_improvements(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    panel_id = str(arguments.get("panel_id") or "")
    family = str(arguments.get("family") or "")
    if not _is_safe_panel_id(panel_id):
        return _tool_envelope(
            "figure-agent.mcp.propose-panel-improvements.v1",
            success=False,
            started=time.monotonic(),
            name=name,
            error=_error("invalid_request", "panel_id must match [A-Za-z0-9_-]+"),
        )
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.propose-panel-improvements.v1",
        command=["candidates", name, "--panel", panel_id, "--family", family, "--json"],
        payload_key="candidate_set",
        failure_message="fig-agent candidates failed",
    )


def _compare_candidate(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    candidate_id = str(arguments.get("candidate_id") or "")
    if not _is_safe_fixture_name(candidate_id):
        return _tool_envelope(
            "figure-agent.mcp.compare-candidate.v1",
            success=False,
            started=time.monotonic(),
            name=name,
            error=_error(
                "invalid_fixture_name",
                "candidate_id must be a single build/candidates/<id> directory name",
            ),
        )
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.compare-candidate.v1",
        command=["compare-candidate", name, candidate_id, "--json"],
        payload_key="review_packet",
        failure_message="fig-agent compare-candidate failed",
    )


def _render_candidates(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    candidate_set = str(arguments.get("candidate_set") or "build/candidates/candidate_set.json")
    candidate_id = arguments.get("candidate_id")
    crop_panel = arguments.get("crop_panel")
    schema = "figure-agent.mcp.render-candidates.v1"
    started = time.monotonic()
    if candidate_id is not None and not _is_safe_fixture_name(candidate_id):
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            error=_error(
                "invalid_fixture_name",
                "candidate_id must be a single build/candidates/<id> directory name",
            ),
        )
    if crop_panel is not None and not _is_safe_panel_id(crop_panel):
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            error=_error("invalid_request", "crop_panel must match [A-Za-z0-9_-]+"),
        )
    resolved = _validated_workspace_and_name(arguments, started, schema, require_fixture=True)
    if isinstance(resolved, dict):
        return resolved
    workspace_root, name = resolved
    with _fixture_lock(workspace_root, name, "render_candidates") as lock:
        if lock is not None:
            return _operation_in_progress(schema=schema, started=started, name=name, lock=lock)
        if candidate_set == "build/candidates/candidate_set.json":
            seed = _run_fig_agent_enveloped(
                schema=schema,
                started=started,
                command=[
                    "candidates",
                    name,
                    "--json",
                    "--output",
                    candidate_set,
                ],
                workspace_root=workspace_root,
                timeout_seconds=120,
                timeout_message="fig-agent render-candidates timed out",
                name=name,
            )
            if isinstance(seed, dict):
                return seed
            if seed.returncode != 0:
                return _tool_envelope(
                    schema,
                    success=False,
                    started=started,
                    name=name,
                    exit_code=seed.returncode,
                    stdout=_bounded(seed.stdout),
                    stderr=_bounded(seed.stderr),
                    error=_error(
                        "unsupported_operation",
                        "fig-agent candidates failed",
                    ),
                )
        command = ["render-candidates", name, "--candidate-set", candidate_set]
        if candidate_id is not None:
            command.extend(["--candidate-id", str(candidate_id)])
        if bool(arguments.get("compile")):
            command.append("--compile")
        if bool(arguments.get("export")):
            command.append("--export")
        if crop_panel is not None:
            command.extend(["--crop-panel", str(crop_panel)])
        if bool(arguments.get("evaluate")):
            command.append("--evaluate")
        command.append("--json")
        result = _run_fig_agent_enveloped(
            schema=schema,
            started=started,
            command=command,
            workspace_root=workspace_root,
            timeout_seconds=120,
            timeout_message="fig-agent render-candidates timed out",
            name=name,
        )
        if isinstance(result, dict):
            return result
    if result.returncode != 0:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            exit_code=result.returncode,
            stdout=_bounded(result.stdout),
            stderr=_bounded(result.stderr),
            error=_error("unsupported_operation", "fig-agent render-candidates failed"),
        )
    payload, json_error = _json_payload_from_result(
        result=result,
        schema=schema,
        started=started,
        name=name,
        invalid_json_message="fig-agent render-candidates returned invalid JSON",
    )
    if json_error is not None:
        return json_error
    return _tool_envelope(
        schema,
        success=True,
        started=started,
        name=name,
        render_result=payload,
    )


def _rank_candidates(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    candidate_set = str(arguments.get("candidate_set") or "build/candidates/candidate_set.json")
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.rank-candidates.v1",
        command=["rank-candidates", name, "--candidate-set", candidate_set, "--json"],
        payload_key="rank_result",
        failure_message="fig-agent rank-candidates failed",
    )


def _memory_summary(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.memory-summary.v1",
        command=["memory-index", "--fixture", name, "--json"],
        payload_key="memory_index",
        failure_message="fig-agent memory-index failed",
    )


def _benchmark_list(arguments: dict[str, Any]) -> dict[str, Any]:
    del arguments
    return _run_workspace_json_fig_agent_tool(
        schema="figure-agent.mcp.benchmark-list.v1",
        command=["benchmark-list", "--json"],
        payload_key="benchmark_list",
        failure_message="fig-agent benchmark-list failed",
    )


def _benchmark_run_preview(arguments: dict[str, Any]) -> dict[str, Any]:
    suite = arguments.get("suite")
    if not _is_safe_fixture_name(suite):
        return _tool_envelope(
            "figure-agent.mcp.benchmark-run-preview.v1",
            success=False,
            started=time.monotonic(),
            error=_error(
                "invalid_fixture_name",
                "suite must be a single benchmark suite name",
            ),
        )
    command = ["benchmark-run", "--suite", str(suite), "--json"]
    limit = arguments.get("limit")
    if limit is not None:
        try:
            parsed_limit = int(limit)
        except (TypeError, ValueError):
            return _tool_envelope(
                "figure-agent.mcp.benchmark-run-preview.v1",
                success=False,
                started=time.monotonic(),
                error=_error("invalid_request", "limit must be an integer"),
            )
        command.extend(["--limit", str(parsed_limit)])
    return _run_workspace_json_fig_agent_tool(
        schema="figure-agent.mcp.benchmark-run-preview.v1",
        command=command,
        payload_key="benchmark_run",
        failure_message="fig-agent benchmark-run failed",
    )


def _benchmark_compare(arguments: dict[str, Any]) -> dict[str, Any]:
    baseline_run = arguments.get("baseline_run")
    candidate_run = arguments.get("candidate_run")
    if not _is_safe_fixture_name(baseline_run) or not _is_safe_fixture_name(candidate_run):
        return _tool_envelope(
            "figure-agent.mcp.benchmark-compare.v1",
            success=False,
            started=time.monotonic(),
            error=_error("invalid_fixture_name", "benchmark run ids must be single names"),
        )
    return _run_workspace_json_fig_agent_tool(
        schema="figure-agent.mcp.benchmark-compare.v1",
        command=[
            "benchmark-compare",
            str(baseline_run),
            str(candidate_run),
            "--json",
        ],
        payload_key="benchmark_comparison",
        failure_message="fig-agent benchmark-compare failed",
    )


def _benchmark_detectors_preview(arguments: dict[str, Any]) -> dict[str, Any]:
    name = arguments.get("name")
    suite = arguments.get("suite", "smoke")
    if not _is_safe_fixture_name(name):
        return _tool_envelope(
            "figure-agent.mcp.benchmark-detectors-preview.v1",
            success=False,
            started=time.monotonic(),
            error=_error(
                "invalid_fixture_name",
                "name must be a single fixture name",
            ),
        )
    if not _is_safe_fixture_name(suite):
        return _tool_envelope(
            "figure-agent.mcp.benchmark-detectors-preview.v1",
            success=False,
            started=time.monotonic(),
            error=_error(
                "invalid_fixture_name",
                "suite must be a single benchmark suite name",
            ),
        )
    return _run_workspace_json_fig_agent_tool(
        schema="figure-agent.mcp.benchmark-detectors-preview.v1",
        command=[
            "benchmark-detectors",
            str(name),
            "--suite",
            str(suite),
            "--json",
        ],
        payload_key="detector_reports",
        failure_message="fig-agent benchmark-detectors failed",
    )


def _quality_next_experiment(arguments: dict[str, Any]) -> dict[str, Any]:
    del arguments
    started = time.monotonic()
    schema = "figure-agent.mcp.quality-next-experiment.v1"
    plugin_root = _plugin_root()
    workspace_root = _workspace_root(plugin_root)
    if workspace_root is None or not _examples_dir(workspace_root).is_dir():
        workspace_root = plugin_root
    result = _run_fig_agent_enveloped(
        schema=schema,
        started=started,
        command=["quality-next-experiment", "--json"],
        workspace_root=workspace_root,
        timeout_seconds=120,
        timeout_message="fig-agent quality-next-experiment timed out",
    )
    if isinstance(result, dict):
        return result
    if result.returncode != 0:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            exit_code=result.returncode,
            stdout=_bounded(result.stdout),
            stderr=_bounded(result.stderr),
            error=_error("unsupported_operation", "fig-agent quality-next-experiment failed"),
        )
    payload, json_error = _json_payload_from_result(
        result=result,
        schema=schema,
        started=started,
        invalid_json_message="fig-agent quality-next-experiment returned invalid JSON",
    )
    if json_error is not None:
        return json_error
    return _tool_envelope(
        schema,
        success=True,
        started=started,
        next_experiment=payload,
    )


def _next(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.next.v1",
        command=["next", name, "--json"],
        payload_key="next_result",
        failure_message="fig-agent next failed",
    )


def _accept_candidate(arguments: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    schema = "figure-agent.mcp.accept-candidate.v1"
    resolved = _validated_workspace_and_name(arguments, started, schema, require_fixture=True)
    if isinstance(resolved, dict):
        return resolved
    workspace_root, name = resolved
    candidate_id = arguments.get("candidate_id")
    if not _is_safe_fixture_name(candidate_id):
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            error=_error(
                "invalid_fixture_name",
                "candidate_id must be a single build/candidates/<id> directory name",
            ),
        )
    decision = str(arguments.get("decision") or "")
    reviewer = str(arguments.get("reviewer") or "")
    rationale = str(arguments.get("rationale") or "")
    if decision not in {"accept", "reject"} or not reviewer.strip() or not rationale.strip():
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            candidate_id=str(candidate_id),
            error=_error(
                "invalid_request",
                "decision must be accept or reject, and reviewer and rationale are required",
            ),
        )
    candidate_set = str(arguments.get("candidate_set") or "build/candidates/candidate_set.json")
    with _fixture_lock(workspace_root, name, "accept_candidate") as lock:
        if lock is not None:
            return _operation_in_progress(schema=schema, started=started, name=name, lock=lock)
        result = _run_fig_agent_enveloped(
            schema=schema,
            started=started,
            command=[
                "accept-candidate",
                name,
                str(candidate_id),
                "--candidate-set",
                candidate_set,
                "--decision",
                decision,
                "--reviewer",
                reviewer,
                "--rationale",
                rationale,
                "--json",
            ],
            workspace_root=workspace_root,
            timeout_seconds=120,
            timeout_message="fig-agent accept-candidate timed out",
            name=name,
        )
        if isinstance(result, dict):
            return result
    if result.returncode != 0:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            candidate_id=str(candidate_id),
            exit_code=result.returncode,
            stdout=_bounded(result.stdout),
            stderr=_bounded(result.stderr),
            error=_error("unsupported_operation", "fig-agent accept-candidate failed"),
        )
    payload, json_error = _json_payload_from_result(
        result=result,
        schema=schema,
        started=started,
        name=name,
        invalid_json_message="fig-agent accept-candidate returned invalid JSON",
    )
    if json_error is not None:
        return json_error
    return _tool_envelope(
        schema,
        success=True,
        started=started,
        name=name,
        candidate_id=str(candidate_id),
        acceptance=payload,
    )


def _candidate_apply_readiness(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    candidate_id = str(arguments.get("candidate_id") or "")
    candidate_set = str(arguments.get("candidate_set") or "")
    if not candidate_set:
        return _tool_envelope(
            "figure-agent.mcp.candidate-apply-readiness.v1",
            success=False,
            started=time.monotonic(),
            name=name,
            error=_error("invalid_request", "candidate_set is required"),
        )
    if not _is_safe_fixture_name(candidate_id):
        return _tool_envelope(
            "figure-agent.mcp.candidate-apply-readiness.v1",
            success=False,
            started=time.monotonic(),
            name=name,
            error=_error(
                "invalid_fixture_name",
                "candidate_id must be a single build/candidates/<id> directory name",
            ),
        )
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.candidate-apply-readiness.v1",
        command=[
            "apply-candidate-ready",
            name,
            candidate_id,
            "--candidate-set",
            candidate_set,
            "--json",
        ],
        payload_key="apply_readiness",
        failure_message="fig-agent apply-candidate-ready failed",
    )


def _evidence_sync_preview(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    command = ["evidence-sync", name]
    candidate_id = arguments.get("candidate_id")
    candidate_set = arguments.get("candidate_set")
    if candidate_id is not None:
        if not _is_safe_fixture_name(candidate_id):
            return _tool_envelope(
                "figure-agent.mcp.evidence-sync-preview.v1",
                success=False,
                started=time.monotonic(),
                name=name,
                error=_error(
                    "invalid_fixture_name",
                    "candidate_id must be a single build/candidates/<id> directory name",
                ),
            )
        command.extend(["--candidate-id", str(candidate_id)])
    if candidate_set is not None:
        command.extend(["--candidate-set", str(candidate_set)])
    command.append("--json")
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.evidence-sync-preview.v1",
        command=command,
        payload_key="evidence_sync",
        failure_message="fig-agent evidence-sync preview failed",
    )


def _closeout_ready(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    command = ["closeout-ready", name]
    candidate_id = arguments.get("candidate_id")
    candidate_set = arguments.get("candidate_set")
    if candidate_id is not None:
        if not _is_safe_fixture_name(candidate_id):
            return _tool_envelope(
                "figure-agent.mcp.closeout-ready.v1",
                success=False,
                started=time.monotonic(),
                name=name,
                error=_error(
                    "invalid_fixture_name",
                    "candidate_id must be a single build/candidates/<id> directory name",
                ),
            )
        command.extend(["--candidate-id", str(candidate_id)])
    if candidate_set is not None:
        command.extend(["--candidate-set", str(candidate_set)])
    command.append("--json")
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.closeout-ready.v1",
        command=command,
        payload_key="closeout_ready",
        failure_message="fig-agent closeout-ready failed",
    )


def _prepare_human_review(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    candidate_id = str(arguments.get("candidate_id") or "")
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.prepare-human-review.v1",
        command=["review-candidate", name, candidate_id, "--json"],
        payload_key="review_packet",
        failure_message="fig-agent review-candidate failed",
    )


def _apply_candidate(arguments: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    schema = "figure-agent.mcp.apply-candidate.v1"
    resolved = _validated_workspace_and_name(arguments, started, schema, require_fixture=True)
    if isinstance(resolved, dict):
        return resolved
    workspace_root, name = resolved
    candidate_id = arguments.get("candidate_id")
    if not _is_safe_fixture_name(candidate_id):
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            error=_error(
                "invalid_fixture_name",
                "candidate_id must be a single build/candidates/<id> directory name",
            ),
        )
    candidate_set_path = str(
        arguments.get("candidate_set_path") or "build/candidates/candidate_set.json"
    )
    acceptance_path = str(
        arguments.get("acceptance_path") or f"build/candidates/{candidate_id}/acceptance.json"
    )
    result = _run_fig_agent_enveloped(
        schema=schema,
        started=started,
        command=[
            "apply-candidate",
            name,
            str(candidate_id),
            "--candidate-set",
            candidate_set_path,
            "--acceptance",
            acceptance_path,
            "--json",
        ],
        workspace_root=workspace_root,
        timeout_seconds=300,
        timeout_message="fig-agent apply-candidate timed out",
        name=name,
    )
    if isinstance(result, dict):
        return result
    # apply-candidate prints the candidate-apply-result payload on stdout even when
    # the acceptance/drift/lock gate blocks the candidate (CLI exit 1), so derive
    # success from the apply status rather than the process return code. Hard errors
    # raised before the payload is emitted (e.g. candidate_set_missing) leave stdout
    # empty and exit non-zero; surface the CLI stderr as the diagnostic in that case.
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            candidate_id=str(candidate_id),
            status=None,
            stdout=_bounded(result.stdout),
            stderr=_bounded(result.stderr),
            error=_error(
                "unsupported_operation",
                _bounded(result.stderr.strip() or "fig-agent apply-candidate failed"),
            ),
        )
    status = payload.get("status") if isinstance(payload, dict) else None
    success = status == "applied"
    if success:
        error = None
    elif status == "rolled_back":
        post = payload.get("post_apply", {}) if isinstance(payload, dict) else {}
        rollback_exports = post.get("rollback_exports", {}) if isinstance(post, dict) else {}
        suffix = (
            " Source and generated exports were restored."
            if isinstance(rollback_exports, dict) and rollback_exports.get("status") == "success"
            else (
                " Source was restored; inspect apply_result.post_apply for "
                "generated artifact cleanup."
            )
        )
        error = _error(
            "unsupported_operation",
            "apply-candidate post-apply verification failed (status rolled_back); "
            f"the edit was automatically rolled back.{suffix}",
        )
    elif status == "applied_with_failed_verification":
        # Post-apply verification failed. The efficacy recheck and the
        # value-preservation gate AUTO-ROLL-BACK the .tex, so when rolled_back is
        # set the working tree is already restored; otherwise (e.g. an
        # export/compile stage failed) the mutation persists and the caller rolls
        # back via apply_result.rollback_patch.
        post = payload.get("post_apply", {}) if isinstance(payload, dict) else {}
        verifiers = post.get("class_verifiers", {}) if isinstance(post, dict) else {}
        if isinstance(verifiers, dict) and verifiers.get("rolled_back"):
            rollback_exports = post.get("rollback_exports", {}) if isinstance(post, dict) else {}
            suffix = (
                " Source and generated exports were restored."
                if isinstance(rollback_exports, dict)
                and rollback_exports.get("status") == "success"
                else (
                    " Source was restored; inspect apply_result.post_apply for "
                    "generated artifact cleanup."
                )
            )
            error = _error(
                "unsupported_operation",
                "apply-candidate post-apply verification failed (status "
                "applied_with_failed_verification); the edit was automatically rolled "
                f"back.{suffix}",
            )
        else:
            error = _error(
                "unsupported_operation",
                "apply-candidate mutated the working tree but post-apply verification "
                "failed (status applied_with_failed_verification); roll back via "
                "apply_result.rollback_patch.",
            )
    else:
        # blocked/ready and any other non-applied status: the gate refused the
        # candidate before mutating; the working tree is unchanged.
        error = _error(
            "unsupported_operation",
            f"apply-candidate refused before mutation (status {status}); working tree unchanged.",
        )
    return _tool_envelope(
        schema,
        success=success,
        started=started,
        name=name,
        candidate_id=str(candidate_id),
        status=status,
        apply_result=payload,
        artifacts=_status_artifacts(workspace_root, name),
        error=error,
    )


def _verify_plan(arguments: dict[str, Any]) -> dict[str, Any]:
    name = str(arguments.get("name") or "")
    plan = str(arguments.get("plan") or "build/quality/patch_plan.json")
    return _run_json_fig_agent_tool(
        arguments=arguments,
        schema="figure-agent.mcp.verify-plan.v1",
        command=["verify-plan", name, "--plan", plan, "--json"],
        payload_key="result",
        failure_message="fig-agent verify-plan failed",
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
            return _operation_in_progress(schema=schema, started=started, name=name, lock=lock)
        result = _run_fig_agent_enveloped(
            schema=schema,
            started=started,
            command=command,
            workspace_root=workspace_root,
            timeout_seconds=300,
            timeout_message="fig-agent compile timed out",
            name=name,
        )
        if isinstance(result, dict):
            return result
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
    if "force_golden" in arguments:
        return _tool_envelope(
            schema,
            success=False,
            started=started,
            name=name,
            error=_error("unsupported_operation", "force_golden_requires_cli_closeout_accept"),
        )
    command = ["export", name]
    if bool(arguments.get("skip_critique")):
        command.append("--skip-critique")
    with _fixture_lock(workspace_root, name, "export") as lock:
        if lock is not None:
            return _operation_in_progress(schema=schema, started=started, name=name, lock=lock)
        result = _run_fig_agent_enveloped(
            schema=schema,
            started=started,
            command=command,
            workspace_root=workspace_root,
            timeout_seconds=300,
            timeout_message="fig-agent export timed out",
            name=name,
        )
        if isinstance(result, dict):
            return result
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
            return _operation_in_progress(schema=schema, started=started, name=name, lock=lock)
        result = _run_fig_agent_enveloped(
            schema=schema,
            started=started,
            command=["loop", name, "--goal", goal, "--json"],
            workspace_root=workspace_root,
            timeout_seconds=300,
            timeout_message="fig-agent loop checkpoint timed out",
            name=name,
        )
        if isinstance(result, dict):
            return result
    payload, _ = _json_payload_from_result(
        result=result,
        schema=schema,
        started=started,
        name=name,
        invalid_json_message="fig-agent loop returned invalid JSON",
        required=False,
    )
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
    "figure_agent_next": {
        "description": "Return one read-only next action using the CLI state router.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        "handler": _next,
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
                "skip_critique": {"type": "boolean"},
            },
        },
        "handler": _export,
    },
    "figure_agent_quality_map": {
        "description": "Return a read-only quality defect ledger for one fixture.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        "handler": _quality_map,
    },
    "figure_agent_context_pack": {
        "description": "Return a read-only authoring context pack for one fixture.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        "handler": _context_pack,
    },
    "figure_agent_propose_patch": {
        "description": "Return a read-only safe mechanical patch proposal.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        "handler": _propose_patch,
    },
    "figure_agent_analyze_figure": {
        "description": "Return the read-only candidate-search intent model for one fixture.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        "handler": _analyze_figure,
    },
    "figure_agent_propose_improvements": {
        "description": "Return deterministic read-only candidate improvements.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        "handler": _propose_improvements,
    },
    "figure_agent_materialize_candidate_set": {
        "description": "Persist deterministic candidate improvements to the fixture sandbox.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "candidate_set": {"type": "string"},
                "panel_id": {"type": "string"},
                "family": {"type": "string"},
            },
        },
        "handler": _materialize_candidate_set,
    },
    "figure_agent_analyze_panel": {
        "description": "Return a read-only panel model with TeX selectors.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "panel_id"],
            "properties": {
                "name": {"type": "string"},
                "panel_id": {"type": "string"},
            },
        },
        "handler": _analyze_panel,
    },
    "figure_agent_propose_panel_improvements": {
        "description": "Return deterministic read-only candidates for one panel family.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "panel_id", "family"],
            "properties": {
                "name": {"type": "string"},
                "panel_id": {"type": "string"},
                "family": {"type": "string"},
            },
        },
        "handler": _propose_panel_improvements,
    },
    "figure_agent_render_candidates": {
        "description": "Render candidate manifests in the fixture-local sandbox.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "candidate_set": {"type": "string"},
                "candidate_id": {"type": "string"},
                "compile": {"type": "boolean"},
                "export": {"type": "boolean"},
                "crop_panel": {"type": "string"},
                "evaluate": {"type": "boolean"},
            },
        },
        "handler": _render_candidates,
    },
    "figure_agent_rank_candidates": {
        "description": "Rank rendered candidate manifests without applying changes.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "candidate_set": {"type": "string"},
            },
        },
        "handler": _rank_candidates,
    },
    "figure_agent_memory_summary": {
        "description": "Return a read-only quality memory index preview for one fixture.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        "handler": _memory_summary,
    },
    "figure_agent_benchmark_list": {
        "description": "Return read-only quality benchmark suites.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {},
        },
        "handler": _benchmark_list,
    },
    "figure_agent_benchmark_run_preview": {
        "description": "Run a read-only lightweight benchmark preview.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["suite"],
            "properties": {
                "suite": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
        "handler": _benchmark_run_preview,
    },
    "figure_agent_benchmark_compare": {
        "description": "Compare two saved benchmark runs without writing.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["baseline_run", "candidate_run"],
            "properties": {
                "baseline_run": {"type": "string"},
                "candidate_run": {"type": "string"},
            },
        },
        "handler": _benchmark_compare,
    },
    "figure_agent_quality_next_experiment": {
        "description": "Return the next read-only quality benchmark experiment.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {},
        },
        "handler": _quality_next_experiment,
    },
    "figure_agent_benchmark_detectors_preview": {
        "description": "Preview benchmark detector report generation without writing files.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "suite": {"type": "string"},
            },
        },
        "handler": _benchmark_detectors_preview,
    },
    "figure_agent_prepare_human_review": {
        "description": "Return a read-only human review packet for one candidate.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "candidate_id"],
            "properties": {
                "name": {"type": "string"},
                "candidate_id": {"type": "string"},
            },
        },
        "handler": _prepare_human_review,
    },
    "figure_agent_candidate_apply_readiness": {
        "description": "Return read-only apply readiness for one rendered candidate.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "candidate_id", "candidate_set"],
            "properties": {
                "name": {"type": "string"},
                "candidate_id": {"type": "string"},
                "candidate_set": {"type": "string"},
            },
        },
        "handler": _candidate_apply_readiness,
    },
    "figure_agent_accept_candidate": {
        "description": "Record an explicit local human verdict (accept or reject) for one rendered candidate.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "candidate_id", "decision", "reviewer", "rationale"],
            "properties": {
                "name": {"type": "string"},
                "candidate_id": {"type": "string"},
                "candidate_set": {"type": "string"},
                "decision": {"type": "string", "enum": ["accept", "reject"]},
                "reviewer": {"type": "string"},
                "rationale": {"type": "string"},
            },
        },
        "handler": _accept_candidate,
    },
    "figure_agent_evidence_sync_preview": {
        "description": "Preview read-only evidence index sync for one fixture.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "candidate_id": {"type": "string"},
                "candidate_set": {"type": "string"},
            },
        },
        "handler": _evidence_sync_preview,
    },
    "figure_agent_closeout_ready": {
        "description": "Return read-only closeout readiness for one fixture.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "candidate_id": {"type": "string"},
                "candidate_set": {"type": "string"},
            },
        },
        "handler": _closeout_ready,
    },
    "figure_agent_compare_candidate": {
        "description": "Return a read-only comparison packet for one rendered candidate.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "candidate_id"],
            "properties": {
                "name": {"type": "string"},
                "candidate_id": {"type": "string"},
            },
        },
        "handler": _compare_candidate,
    },
    "figure_agent_apply_candidate": {
        "description": "Apply an accepted candidate through the acceptance/drift/lock gate.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name", "candidate_id"],
            "properties": {
                "name": {"type": "string"},
                "candidate_id": {"type": "string"},
                "candidate_set_path": {"type": "string"},
                "acceptance_path": {"type": "string"},
            },
        },
        "handler": _apply_candidate,
    },
    "figure_agent_verify_plan": {
        "description": "Return the latest explicit patch verification result.",
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {
                "name": {"type": "string"},
                "plan": {"type": "string"},
            },
        },
        "handler": _verify_plan,
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
            "uriTemplate": "figure://{name}/exports/pdf",
            "name": "Export PDF",
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
            "uriTemplate": "figure://{name}/exports/tif",
            "name": "Export TIFF",
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
            "uriTemplate": "figure://{name}/audit/undeclared-geometry",
            "name": "Undeclared geometry audit",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "figure://{name}/audit/evidence-graph",
            "name": "Audit evidence graph",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "figure://{name}/perception/extract",
            "name": "Perception extract",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "figure://{name}/panel/{panel_id}/intent",
            "name": "Panel intent model",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "figure://{name}/candidates/{candidate_id}/manifest",
            "name": "Candidate manifest",
            "mimeType": "application/json",
        },
        {
            "uriTemplate": "figure://{name}/candidates/{candidate_id}/review",
            "name": "Candidate review packet",
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
        uri = params.get("uri") if isinstance(params, dict) else None
        if not isinstance(uri, str):
            payload = {
                "schema": "figure-agent.mcp.resource-metadata.v1",
                "success": False,
                "error": _error("invalid_request", "resources/read requires string uri"),
            }
        else:
            payload = _resource_metadata(uri)
        return {
            "contents": [
                {
                    "uri": uri if isinstance(uri, str) else "",
                    "mimeType": "application/json",
                    "text": json.dumps(payload, sort_keys=True),
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
