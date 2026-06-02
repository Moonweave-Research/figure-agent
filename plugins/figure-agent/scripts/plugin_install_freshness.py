"""Compare the development plugin tree with an installed Claude plugin cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from plugin_package_audit import JUNK_DIR_NAMES, JUNK_FILE_NAMES, find_packaging_junk

SCHEMA = "figure-agent.plugin-install-freshness.v1"
DEFAULT_CACHE_PARENT = (
    Path.home() / ".claude" / "plugins" / "cache" / "figure-agent-local" / "figure-agent"
)
UPDATE_COMMAND = "claude plugin update figure-agent@figure-agent-local"
INSTALL_COMMAND = "claude plugin install figure-agent@figure-agent-local"
REINSTALL_COMMAND = (
    "claude plugin uninstall figure-agent && "
    "claude plugin install figure-agent@figure-agent-local"
)

EXTRA_JUNK_DIR_NAMES = {
    ".git",
    ".in_use",
    ".scratch",
    ".worktrees",
    "previews",
}
EXTRA_JUNK_FILE_SUFFIXES = {
    ".aux",
    ".fdb_latexmk",
    ".fls",
    ".log",
    ".synctex.gz",
}


def _is_plugin_root(root: Path) -> bool:
    return (root / ".claude-plugin" / "plugin.json").is_file()


def _plugin_version(root: Path) -> str | None:
    try:
        payload = json.loads((root / ".claude-plugin" / "plugin.json").read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    version = payload.get("version") if isinstance(payload, dict) else None
    return version if isinstance(version, str) and version else None


def _version_key(path: Path) -> tuple[tuple[int, ...], str]:
    parts: list[int] = []
    for raw_part in path.name.split("."):
        try:
            parts.append(int(raw_part))
        except ValueError:
            return ((), path.name)
    return (tuple(parts), path.name)


def latest_installed_root(cache_parent: Path) -> Path | None:
    """Return the highest-version installed plugin root under a cache parent."""
    if _is_plugin_root(cache_parent):
        return cache_parent
    if not cache_parent.is_dir():
        return None
    candidates = [
        path for path in cache_parent.iterdir() if path.is_dir() and _is_plugin_root(path)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=_version_key)[-1]


def _iter_payload_files(root: Path) -> list[Path]:
    ignored_dir_names = JUNK_DIR_NAMES | EXTRA_JUNK_DIR_NAMES
    result: list[Path] = []

    def walk(directory: Path) -> None:
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.name in JUNK_FILE_NAMES:
                continue
            if any(path.name.endswith(suffix) for suffix in EXTRA_JUNK_FILE_SUFFIXES):
                continue
            if path.is_dir():
                if path.name in ignored_dir_names:
                    continue
                if directory == root and path.name in {"examples", "plugins"}:
                    continue
                walk(path)
                continue
            if path.is_file():
                result.append(path)

    walk(root)
    return result


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _payload_manifest(root: Path) -> dict[str, str]:
    root = root.resolve()
    return {
        path.resolve().relative_to(root).as_posix(): _file_sha256(path)
        for path in _iter_payload_files(root)
    }


def _fingerprint(manifest: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for relative_path, file_hash in sorted(manifest.items()):
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("utf-8"))
        digest.update(b"\n")
    return f"sha256:{digest.hexdigest()}"


def _installed_package_hygiene(installed_root: Path | None) -> dict[str, Any]:
    if installed_root is None:
        return {
            "state": "unknown",
            "junk_count": 0,
            "junk_paths": [],
            "next_action": "install plugin before auditing package hygiene",
        }
    root = installed_root.resolve()
    if not _is_plugin_root(root):
        return {
            "state": "unknown",
            "junk_count": 0,
            "junk_paths": [],
            "next_action": "reinstall plugin before auditing package hygiene",
        }
    junk_paths = [
        path.resolve().relative_to(root).as_posix()
        for path in find_packaging_junk(root)
    ]
    if not junk_paths:
        return {
            "state": "clean",
            "junk_count": 0,
            "junk_paths": [],
            "next_action": "installed plugin cache package has no generated junk",
        }
    return {
        "state": "dirty",
        "junk_count": len(junk_paths),
        "junk_paths": junk_paths,
        "next_action": (
            "python3 scripts/plugin_package_audit.py "
            f"{root} --clean --max-mib 300"
        ),
    }


def _source_package_hygiene(source_root: Path) -> dict[str, Any]:
    root = source_root.resolve()
    junk_paths = [
        path.resolve().relative_to(root).as_posix()
        for path in find_packaging_junk(root)
    ]
    if not junk_paths:
        return {
            "state": "clean",
            "junk_count": 0,
            "junk_paths": [],
            "next_action": "development plugin tree package has no generated junk",
        }
    return {
        "state": "dirty",
        "junk_count": len(junk_paths),
        "junk_paths": junk_paths,
        "next_action": (
            "python3 scripts/plugin_package_audit.py "
            f"{root} --clean --max-mib 300"
        ),
    }


def compare_plugin_install(source_root: Path, installed_root: Path | None) -> dict[str, Any]:
    """Return a deterministic freshness comparison between source and install."""
    source_root = source_root.resolve()
    if not _is_plugin_root(source_root):
        raise ValueError(f"source_root is not a plugin root: {source_root}")
    source_version = _plugin_version(source_root)
    source_manifest = _payload_manifest(source_root)
    source_package_hygiene = _source_package_hygiene(source_root)
    if installed_root is None:
        return {
            "schema": SCHEMA,
            "state": "missing",
            "source_root": str(source_root),
            "installed_root": None,
            "source_version": source_version,
            "installed_version": None,
            "source_fingerprint": _fingerprint(source_manifest),
            "installed_fingerprint": None,
            "changed_files": [],
            "missing_files": [],
            "extra_files": [],
            "refresh_strategy": "install_missing",
            "next_action": INSTALL_COMMAND,
            "source_package_hygiene": source_package_hygiene,
            "installed_package_hygiene": _installed_package_hygiene(None),
        }

    installed_root = installed_root.resolve()
    if not _is_plugin_root(installed_root):
        return {
            "schema": SCHEMA,
            "state": "invalid",
            "source_root": str(source_root),
            "installed_root": str(installed_root),
            "source_version": source_version,
            "installed_version": None,
            "source_fingerprint": _fingerprint(source_manifest),
            "installed_fingerprint": None,
            "changed_files": [],
            "missing_files": [],
            "extra_files": [],
            "refresh_strategy": "reinstall_invalid",
            "next_action": REINSTALL_COMMAND,
            "source_package_hygiene": source_package_hygiene,
            "installed_package_hygiene": _installed_package_hygiene(installed_root),
        }

    installed_manifest = _payload_manifest(installed_root)
    installed_version = _plugin_version(installed_root)
    changed_files = sorted(
        path
        for path in source_manifest.keys() & installed_manifest.keys()
        if source_manifest[path] != installed_manifest[path]
    )
    missing_files = sorted(source_manifest.keys() - installed_manifest.keys())
    extra_files = sorted(installed_manifest.keys() - source_manifest.keys())
    state = "fresh"
    refresh_strategy = "none"
    next_action = "installed plugin cache matches the development plugin tree"
    if changed_files or missing_files or extra_files:
        state = "stale"
        refresh_strategy = "update"
        next_action = UPDATE_COMMAND
        if source_version is not None and source_version == installed_version:
            refresh_strategy = "reinstall_same_version"
            next_action = REINSTALL_COMMAND

    return {
        "schema": SCHEMA,
        "state": state,
        "source_root": str(source_root),
        "installed_root": str(installed_root),
        "source_version": source_version,
        "installed_version": installed_version,
        "source_fingerprint": _fingerprint(source_manifest),
        "installed_fingerprint": _fingerprint(installed_manifest),
        "changed_files": changed_files,
        "missing_files": missing_files,
        "extra_files": extra_files,
        "refresh_strategy": refresh_strategy,
        "next_action": next_action,
        "source_package_hygiene": source_package_hygiene,
        "installed_package_hygiene": _installed_package_hygiene(installed_root),
    }


def _default_source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "installed_root",
        type=Path,
        nargs="?",
        default=DEFAULT_CACHE_PARENT,
        help="installed plugin root, or cache parent containing version directories",
    )
    parser.add_argument("--source-root", type=Path, default=_default_source_root())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        installed_root = latest_installed_root(args.installed_root)
        result = compare_plugin_install(args.source_root, installed_root)
    except ValueError as exc:
        print(f"plugin_install_freshness.py: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    source_hygiene = result.get("source_package_hygiene")
    source_hygiene_state = (
        source_hygiene.get("state") if isinstance(source_hygiene, dict) else None
    )
    hygiene = result.get("installed_package_hygiene")
    hygiene_state = hygiene.get("state") if isinstance(hygiene, dict) else None
    return (
        0
        if result["state"] == "fresh"
        and source_hygiene_state == "clean"
        and hygiene_state == "clean"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
