"""Audit and clean generated files from an installed figure-agent plugin cache.

Claude Code copies marketplace plugins into ~/.claude/plugins/cache. For local
directory marketplaces, generated project files can be copied too. This helper
keeps the cache package focused on commands, skills, scripts, styles, and docs.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

JUNK_DIR_NAMES = {
    ".claude",
    ".mypy_cache",
    ".pytest_cache",
    ".ralph",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "exports",
    "figure_agent.egg-info",
}
JUNK_FILE_NAMES = {".DS_Store"}
EMPTY_WRAPPER_DIR_NAMES = {"plugins"}


def _is_empty_dir(path: Path) -> bool:
    return path.is_dir() and not any(path.iterdir())


def _is_plugin_root(root: Path) -> bool:
    return (root / ".claude-plugin" / "plugin.json").is_file()


def _tracked_paths(root: Path) -> set[Path]:
    try:
        git_root_result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
    git_root = Path(git_root_result.stdout.strip()).resolve()
    try:
        files_result = subprocess.run(
            ["git", "-C", str(git_root), "ls-files", "-z", "--", str(root)],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()
    tracked: set[Path] = set()
    for raw_path in files_result.stdout.split(b"\0"):
        if not raw_path:
            continue
        tracked_file = (git_root / raw_path.decode()).resolve()
        if not tracked_file.is_relative_to(root):
            continue
        tracked.add(tracked_file)
        tracked.update(tracked_file.parents)
    return tracked


def find_packaging_junk(root: Path) -> list[Path]:
    """Return generated paths that should not live in a plugin cache package."""
    root = root.resolve()
    junk: list[Path] = []
    root_is_plugin = _is_plugin_root(root)
    protected_tracked_paths = _tracked_paths(root)
    for path in root.rglob("*"):
        path = path.resolve()
        if path in protected_tracked_paths:
            continue
        if path.name in JUNK_FILE_NAMES:
            junk.append(path)
            continue
        if path.is_dir() and path.name in JUNK_DIR_NAMES:
            junk.append(path)
            continue
        if root_is_plugin and path.parent == root and path.name == "plugins":
            junk.append(path)
            continue
        if path.name in EMPTY_WRAPPER_DIR_NAMES and _is_empty_dir(path):
            junk.append(path)
    return sorted(junk, key=lambda item: (len(item.parts), str(item)))


def remove_paths(paths: list[Path]) -> None:
    for path in sorted(paths, key=lambda item: len(item.parts), reverse=True):
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def _directory_size_mib(root: Path) -> float:
    total = 0
    for path in root.rglob("*"):
        if path.is_file():
            total += path.stat().st_size
    return total / (1024 * 1024)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="installed plugin cache root to audit")
    parser.add_argument("--clean", action="store_true", help="remove generated package junk")
    parser.add_argument("--max-mib", type=float, default=None, help="fail if package exceeds limit")
    args = parser.parse_args(argv)

    if not args.root.is_dir():
        print(f"plugin_package_audit.py: not a directory: {args.root}", file=sys.stderr)
        return 2

    junk = find_packaging_junk(args.root)
    if junk:
        for path in junk:
            print(f"JUNK {path}")
        if args.clean:
            remove_paths(junk)
            print(f"removed {len(junk)} generated path(s)")
        else:
            print("run with --clean to remove generated package junk", file=sys.stderr)
            return 1

    size_mib = _directory_size_mib(args.root)
    print(f"package_size_mib={size_mib:.1f}")
    if args.max_mib is not None and size_mib > args.max_mib:
        print(
            "plugin_package_audit.py: package too large: "
            f"{size_mib:.1f} MiB > {args.max_mib:.1f} MiB",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
