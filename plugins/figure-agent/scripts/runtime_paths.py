"""Resolve figure-agent plugin resources separately from user workspaces."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    plugin_root: Path
    workspace_root: Path
    scripts_dir: Path
    styles_dir: Path
    examples_dir: Path


def default_plugin_root() -> Path:
    value = os.environ.get("FIGURE_AGENT_PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")
    if value:
        return Path(value).expanduser().resolve()
    return Path(__file__).resolve().parent.parent


def default_workspace_root() -> Path:
    value = os.environ.get("FIGURE_AGENT_WORKSPACE") or os.environ.get("CLAUDE_PROJECT_DIR")
    if value:
        return Path(value).expanduser().resolve()
    return Path.cwd().resolve()


def resolve_runtime_paths(
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> RuntimePaths:
    plugin = (plugin_root or default_plugin_root()).expanduser().resolve()
    workspace = (workspace_root or default_workspace_root()).expanduser().resolve()
    return RuntimePaths(
        plugin_root=plugin,
        workspace_root=workspace,
        scripts_dir=plugin / "scripts",
        styles_dir=plugin / "styles",
        examples_dir=workspace / "examples",
    )


def resolve_example_dir_for_cli(value: str, *, workspace_root: Path | None = None) -> Path:
    paths = resolve_runtime_paths(workspace_root=workspace_root)
    path = Path(value)
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "examples":
        if len(path.parts) != 2 or ".." in path.parts:
            raise ValueError("expected examples/<fixture-name>")
        import fixture_identity

        fixture_identity.validate_fixture_name(path.parts[1])
        return paths.examples_dir / path.parts[1]
    if len(path.parts) == 1:
        import fixture_identity

        fixture_identity.validate_fixture_name(value)
        return paths.examples_dir / value
    raise ValueError("expected fixture name, examples/<fixture-name>, or an absolute path")


def bundle_diagnostics(paths: RuntimePaths) -> dict:
    required = [
        paths.plugin_root / ".claude-plugin" / "plugin.json",
        paths.scripts_dir,
        paths.styles_dir,
        paths.styles_dir / "polymer-paper-preamble.sty",
    ]
    missing = [str(path.relative_to(paths.plugin_root)) for path in required if not path.exists()]
    return {
        "state": "ok" if not missing else "missing",
        "plugin_root": str(paths.plugin_root),
        "missing": missing,
    }


def workspace_diagnostics(paths: RuntimePaths) -> dict:
    missing = []
    if not paths.examples_dir.is_dir():
        missing.append("examples")
    return {
        "state": "ok" if not missing else "missing",
        "workspace_root": str(paths.workspace_root),
        "missing": missing,
    }
