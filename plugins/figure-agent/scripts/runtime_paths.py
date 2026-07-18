"""Resolve figure-agent plugin resources separately from user workspaces."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimePaths:
    plugin_root: Path
    workspace_root: Path
    scripts_dir: Path
    styles_dir: Path
    examples_dir: Path


EXPECTED_PACKAGE_TOP_LEVEL = {
    ".claude-plugin",
    ".mcp.json",
    "AGENTS.md",
    "CHANGELOG.md",
    "README.md",
    "bin",
    "commands",
    "docs",
    "examples",
    "mcp",
    "pyproject.toml",
    "scripts",
    "skills",
    "styles",
    "uv.lock",
}


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


def workspace_root_with_source(plugin_root: Path | None = None) -> tuple[Path | None, str]:
    """Return workspace root plus its source, treating plugin-root cwd as missing."""
    plugin = (plugin_root or default_plugin_root()).expanduser().resolve()
    figure_workspace = os.environ.get("FIGURE_AGENT_WORKSPACE")
    if figure_workspace:
        return Path(figure_workspace).expanduser().resolve(), "FIGURE_AGENT_WORKSPACE"
    claude_project = os.environ.get("CLAUDE_PROJECT_DIR")
    if claude_project:
        return Path(claude_project).expanduser().resolve(), "CLAUDE_PROJECT_DIR"
    cwd = Path.cwd().resolve()
    if cwd == plugin:
        return None, "missing"
    return cwd, "cwd"


def plugin_root_kind(plugin_root: Path) -> str:
    """Classify plugin root conservatively for diagnostics."""
    root = plugin_root.expanduser().resolve()
    parts = root.parts
    if ".claude" in parts and "plugins" in parts and "cache" in parts:
        return "installed_cache"
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        result = None
    if result is not None:
        git_root = Path(result.stdout.strip()).resolve()
        if root == git_root or root.is_relative_to(git_root):
            return "source_tree"
    if (root / ".claude-plugin" / "plugin.json").is_file():
        return "unpacked_zip"
    return "unknown"


def _workspace_for_fixture(fixture_name: str, *, workspace: Path, plugin: Path) -> Path:
    """Prefer the caller/env workspace (user-authored figures) but fall back to
    the plugin root for plugin-bundled cohort fixtures (fig1-5) when the
    workspace has no examples/<fixture_name>/<fixture_name>.tex. The cohort
    fixtures live in <plugin>/examples, so an env workspace pointing at a repo
    root that only *contains* the plugin (CLAUDE_PROJECT_DIR) would otherwise
    resolve them to a non-existent <repo>/examples/<name> and refuse
    source_missing. The presence test is the source file, not just the directory:
    a stray/partial examples/<name>/ tree (e.g. a review-artifact fragment with
    no <name>.tex) must not shadow the real plugin fixture. Fixtures that exist in
    neither location leave the workspace unchanged so callers still emit an honest
    source_missing refusal."""
    source_rel = Path("examples") / fixture_name / f"{fixture_name}.tex"
    if (workspace / source_rel).is_file():
        return workspace
    if (plugin / source_rel).is_file():
        return plugin
    return workspace


def resolve_runtime_paths(
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
    fixture_name: str | None = None,
) -> RuntimePaths:
    plugin = (plugin_root or default_plugin_root()).expanduser().resolve()
    workspace = (workspace_root or default_workspace_root()).expanduser().resolve()
    if fixture_name is not None:
        workspace = _workspace_for_fixture(fixture_name, workspace=workspace, plugin=plugin)
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
    kind = plugin_root_kind(paths.plugin_root)
    return {
        "state": "ok" if not missing else "missing",
        "plugin_root": str(paths.plugin_root),
        "plugin_root_kind": kind,
        "missing": missing,
        "unexpected_cache_state": unexpected_cache_state(paths.plugin_root, kind=kind),
    }


def workspace_diagnostics(paths: RuntimePaths) -> dict:
    workspace_root, source = workspace_root_with_source(paths.plugin_root)
    missing = []
    examples_dir = workspace_root / "examples" if workspace_root is not None else None
    if examples_dir is None or not examples_dir.is_dir():
        missing.append("examples")
    return {
        "state": "ok" if not missing else "missing",
        "workspace_root": str(workspace_root) if workspace_root is not None else None,
        "workspace_source": source,
        "missing": missing,
    }


def workspace_source_for_cli(_: RuntimePaths) -> str:
    if os.environ.get("FIGURE_AGENT_WORKSPACE"):
        return "FIGURE_AGENT_WORKSPACE"
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        return "CLAUDE_PROJECT_DIR"
    return "cwd"


def workspace_diagnostics_for_cli(paths: RuntimePaths) -> dict:
    if (
        workspace_source_for_cli(paths) == "cwd"
        and paths.workspace_root == paths.plugin_root
        and plugin_root_kind(paths.plugin_root) != "source_tree"
    ):
        return workspace_diagnostics(paths)
    missing = []
    if not paths.examples_dir.is_dir():
        missing.append("examples")
    return {
        "state": "ok" if not missing else "missing",
        "workspace_root": str(paths.workspace_root),
        "workspace_source": workspace_source_for_cli(paths),
        "missing": missing,
    }


def unexpected_cache_state(plugin_root: Path, *, kind: str | None = None) -> list[str]:
    """Return unexpected installed/unpacked package paths without deleting anything."""
    root = plugin_root.expanduser().resolve()
    root_kind = kind or plugin_root_kind(root)
    if root_kind not in {"installed_cache", "unpacked_zip"} or not root.is_dir():
        return []

    unexpected: set[str] = set()
    for child in root.iterdir():
        if child.name not in EXPECTED_PACKAGE_TOP_LEVEL:
            unexpected.add(child.name + ("/" if child.is_dir() else ""))

    try:
        import plugin_package_audit
    except ImportError:
        return sorted(unexpected)

    for path in plugin_package_audit.find_packaging_junk(root):
        try:
            unexpected.add(path.relative_to(root).as_posix())
        except ValueError:
            unexpected.add(str(path))
    return sorted(unexpected)
