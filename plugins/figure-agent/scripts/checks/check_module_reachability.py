#!/usr/bin/env python3
"""Report scripts/ modules no entry point can reach.

The 2026-08-28 review measured 22.4k unreachable lines that had accumulated
because nothing ever asked. Deleting them is a one-off; noticing the next one
is not, so this reports the dormant set and a ratchet pins it.

The analysis fails loudly rather than quietly: if the import graph cannot be
walked, every module looks reachable and the report reads clean. Named live
modules are therefore asserted as controls before any result is returned.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

SCHEMA = "figure-agent.module-reachability.v1"

# Modules that must always come back reachable. A result that loses one of
# these describes a broken walk, not a clean repository.
REACHABILITY_CONTROLS = (
    "status",
    "run_export",
    "candidate_apply",
    "experience_log",
    "check_document_status",
)

_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_SCRIPT_PATH_RE = re.compile(r"scripts/(?:[\w-]+/)*(\w+)\.py")


class ModuleReachabilityError(RuntimeError):
    """Raised when the reachability walk cannot be trusted."""


def _module_index(scripts_dir: Path) -> dict[str, list[Path]]:
    modules: dict[str, list[Path]] = {}
    for path in sorted(scripts_dir.rglob("*.py")):
        if "__pycache__" in path.parts or path.name == "__init__.py":
            continue
        modules.setdefault(path.stem, []).append(path)
    return modules


def _imported_names(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def _entry_point_files(plugin_root: Path) -> list[Path]:
    """Every surface a module can legitimately be invoked from."""
    files: list[Path] = []
    cli = plugin_root / "bin" / "fig-agent"
    if cli.is_file():
        files.append(cli)
    files.extend(sorted((plugin_root / "mcp").glob("*.py")))
    files.extend(sorted((plugin_root / "scripts").glob("*.sh")))
    files.extend(sorted((plugin_root / "commands").glob("*.md")))
    skills = plugin_root / "skills"
    if skills.is_dir():
        files.extend(sorted(skills.rglob("*.md")))
    workflows = plugin_root.parents[1] / ".github" / "workflows"
    if workflows.is_dir():
        files.extend(sorted(workflows.rglob("*.yml")))
    return files


def dormant_modules(plugin_root: Path) -> list[str]:
    """Return module stems under scripts/ that no entry point reaches."""
    modules = _module_index(plugin_root / "scripts")
    if not modules:
        raise ModuleReachabilityError("no modules found under scripts/")

    seeds: set[str] = set()
    for source in _entry_point_files(plugin_root):
        try:
            body = source.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Markdown is prose: a bare word like "publication" or "critique" is a
        # sentence, not a call, and seeding from it reports word-stem orphans
        # as reachable. Only an explicit scripts/<path>.py reference counts.
        if source.suffix != ".md":
            seeds.update(token for token in set(_NAME_RE.findall(body)) if token in modules)
        seeds.update(name for name in _SCRIPT_PATH_RE.findall(body) if name in modules)

    reached = set(seeds)
    frontier = list(seeds)
    while frontier:
        for path in modules.get(frontier.pop(), []):
            for dependency in _imported_names(path):
                if dependency in modules and dependency not in reached:
                    reached.add(dependency)
                    frontier.append(dependency)

    # A renamed control used to drop out of the positive control silently,
    # leaving the walk unverified against anything.
    absent = [name for name in REACHABILITY_CONTROLS if name not in modules]
    if absent:
        raise ModuleReachabilityError(f"reachability controls missing: {sorted(absent)}")
    missed = [name for name in REACHABILITY_CONTROLS if name not in reached]
    if missed:
        raise ModuleReachabilityError(f"reachability controls unreachable: {sorted(missed)}")
    return sorted(set(modules) - reached)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        dormant = dormant_modules(args.plugin_root.resolve())
    except ModuleReachabilityError as exc:
        print(f"check_module_reachability: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"schema": SCHEMA, "dormant": dormant}, indent=2, sort_keys=True))
    else:
        print(f"dormant modules: {len(dormant)}")
        for name in dormant:
            print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
