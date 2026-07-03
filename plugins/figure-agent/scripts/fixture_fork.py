"""Safely fork a fixture lane without copying generated state."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import fixture_identity
import runtime_paths
import yaml

SCHEMA = "figure-agent.fixture-fork.v1"
GENERATED_TOP_LEVEL = {
    "build",
    "exports",
    "previews",
    "runs",
    "closeout",
    ".cache",
    "__pycache__",
}
STATE_FILES = {
    "critique.md",
    "QUALITY_AUDIT.md",
    "human_attestation.json",
    "golden_acceptance.json",
}
REWRITE_SUFFIXES = {".md", ".tex", ".yaml", ".yml", ".json"}
YAML_FIXTURE_KEYS = ("name", "fixture")


class FixtureForkError(ValueError):
    """Raised when a fixture fork would be unsafe or incoherent."""


def _validate_fixture_name(name: str) -> str:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise FixtureForkError(str(exc)) from exc
    return name


def _fixture_dir(workspace_root: Path, name: str) -> Path:
    examples = workspace_root / "examples"
    path = examples / _validate_fixture_name(name)
    if path.is_symlink():
        raise FixtureForkError(f"fixture_symlink_forbidden: {name}")
    try:
        path.resolve().relative_to(examples.resolve())
    except ValueError as exc:
        raise FixtureForkError("fixture path_escape") from exc
    return path


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _source_entries(source_dir: Path) -> tuple[list[Path], list[str], list[str]]:
    copied: list[Path] = []
    skipped: list[str] = []
    skipped_symlinks: list[str] = []
    for entry in sorted(source_dir.iterdir(), key=lambda item: item.name):
        if entry.name in GENERATED_TOP_LEVEL or entry.name in STATE_FILES:
            skipped.append(entry.name)
            continue
        if entry.is_symlink():
            skipped_symlinks.append(entry.name)
            continue
        copied.append(entry)
    return copied, skipped, skipped_symlinks


def _copy_entry(source_dir: Path, target_dir: Path, entry: Path, source: str, target: str) -> str:
    destination_name = (
        target + entry.suffix if entry.name == f"{source}{entry.suffix}" else entry.name
    )
    if entry.name == f"{source}.tex":
        destination_name = f"{target}.tex"
    destination = target_dir / destination_name
    if entry.is_dir():
        shutil.copytree(entry, destination, symlinks=False)
    else:
        shutil.copy2(entry, destination)
    return destination.name


def _rewrite_yaml_identity(path: Path, target: str) -> bool:
    if path.suffix not in {".yaml", ".yml"}:
        return False
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return False
    if not isinstance(payload, dict):
        return False
    changed = False
    for key in YAML_FIXTURE_KEYS:
        if key in payload and isinstance(payload[key], str):
            payload[key] = target
            changed = True
    if not changed:
        return False
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return True


def _rewrite_text_identity(path: Path, source: str, target: str) -> bool:
    if path.suffix not in REWRITE_SUFFIXES:
        return False
    if path.name == "fork_receipt.json":
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    replaced = text.replace(source, target)
    if replaced == text:
        return False
    path.write_text(replaced, encoding="utf-8")
    return True


def _rewrite_target_files(target_dir: Path, source: str, target: str) -> list[str]:
    rewritten: list[str] = []
    for path in sorted(target_dir.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise FixtureForkError(f"target_symlink_forbidden: {_relative(target_dir, path)}")
        if not path.is_file():
            continue
        yaml_changed = _rewrite_yaml_identity(path, target)
        text_changed = _rewrite_text_identity(path, source, target)
        if yaml_changed or text_changed:
            rewritten.append(_relative(target_dir, path))
    return rewritten


def _receipt(
    *,
    source: str,
    target: str,
    reason: str,
    copied_entries: list[str],
    skipped_entries: list[str],
    skipped_symlink_entries: list[str],
    rewritten_files: list[str],
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "source_fixture": source,
        "target_fixture": target,
        "reason": reason,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "copied_entries": copied_entries,
        "skipped_generated_or_state_entries": skipped_entries,
        "skipped_symlink_entries": skipped_symlink_entries,
        "rewritten_files": rewritten_files,
        "acceptance_state": "NOT_DECLARED",
        "mutation_boundary": "source_read_only_target_source_files_only",
        "dry_run": dry_run,
    }


def fork_fixture(
    source: str,
    target: str,
    *,
    reason: str,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    if not reason.strip():
        raise FixtureForkError("reason_required")
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    source_dir = _fixture_dir(paths.workspace_root, source)
    target_dir = _fixture_dir(paths.workspace_root, target)
    if source == target:
        raise FixtureForkError("source_target_must_differ")
    if not source_dir.is_dir():
        raise FixtureForkError(f"source_fixture_missing: {source}")
    if target_dir.exists():
        raise FixtureForkError(f"target_fixture_exists: {target}")
    entries, skipped, skipped_symlinks = _source_entries(source_dir)
    copied_names = [
        target + entry.suffix if entry.name == f"{source}{entry.suffix}" else entry.name
        for entry in entries
    ]
    copied_names = [f"{target}.tex" if name == f"{source}.tex" else name for name in copied_names]
    if dry_run:
        return _receipt(
            source=source,
            target=target,
            reason=reason,
            copied_entries=copied_names,
            skipped_entries=skipped,
            skipped_symlink_entries=skipped_symlinks,
            rewritten_files=[],
            dry_run=True,
        )

    target_dir.mkdir(parents=False)
    try:
        actual_copied = [
            _copy_entry(source_dir, target_dir, entry, source, target) for entry in entries
        ]
        rewritten = _rewrite_target_files(target_dir, source, target)
        receipt = _receipt(
            source=source,
            target=target,
            reason=reason,
            copied_entries=actual_copied,
            skipped_entries=skipped,
            skipped_symlink_entries=skipped_symlinks,
            rewritten_files=rewritten,
            dry_run=False,
        )
        (target_dir / "fork_receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except Exception:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise
    return receipt


def main(
    argv: list[str] | None = None,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="fig-agent fork-fixture")
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument("--reason", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = fork_fixture(
            args.source,
            args.target,
            reason=args.reason,
            workspace_root=workspace_root,
            plugin_root=plugin_root,
            dry_run=args.dry_run,
        )
    except FixtureForkError as exc:
        print(f"fig-agent fork-fixture: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
