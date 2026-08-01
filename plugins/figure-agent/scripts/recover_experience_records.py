#!/usr/bin/env python3
"""Recover append-only experience records without overwriting active history."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# This helper is invoked directly during repository recovery, outside the
# ``bin/fig-agent`` import bootstrap.
_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS / "quality"))
sys.path.insert(0, str(_SCRIPTS / "candidates"))

import experience_log
import fixture_identity


class RecoveryError(ValueError):
    """Raised when a recovery source cannot be safely merged."""


def _json_lines(text: str, source: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RecoveryError(f"invalid_json:{source}:{line_number}") from exc
        if not isinstance(record, dict):
            raise RecoveryError(f"invalid_record:{source}:{line_number}")
        record_id = record.get("record_id")
        fixture = record.get("fixture")
        if not isinstance(record_id, str) or not record_id:
            raise RecoveryError(f"record_id_missing:{source}:{line_number}")
        if not isinstance(fixture, str) or not fixture:
            raise RecoveryError(f"fixture_missing:{source}:{line_number}")
        fixture_identity.validate_fixture_name(fixture)
        records.append(record)
    return records


def _read_file_source(path: Path) -> tuple[str, str]:
    if path.is_symlink() or not path.is_file():
        raise RecoveryError(f"file_source_invalid:{path}")
    return path.read_text(encoding="utf-8"), path.as_posix()


def _read_git_source(git_root: Path, revision_path: str) -> tuple[str, str]:
    result = subprocess.run(
        ["git", "-C", str(git_root), "show", revision_path],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise RecoveryError(f"git_source_unreadable:{revision_path}")
    return result.stdout, f"git:{revision_path}"


def _canonical(record: dict[str, Any]) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def recover_records(
    plugin_root: Path,
    source_records: list[tuple[str, list[dict[str, Any]]]],
    *,
    execute: bool,
) -> dict[str, Any]:
    # Recovery is intentionally bound to the supplied checkout.  Unlike normal
    # runtime writes, it must not follow a process-wide log override and merge
    # records into some other workspace.
    log_dir = plugin_root / "docs" / "experience-log"
    if log_dir.is_symlink():
        raise RecoveryError("experience_log_symlink")

    existing: dict[str, dict[str, str]] = defaultdict(dict)
    additions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    added_ids: dict[str, set[str]] = defaultdict(set)

    for path in sorted(log_dir.glob("*.jsonl")):
        if path.is_symlink():
            raise RecoveryError(f"experience_log_symlink:{path.name}")
        for record in _json_lines(path.read_text(encoding="utf-8"), path.as_posix()):
            fixture = str(record["fixture"])
            record_id = str(record["record_id"])
            encoded = _canonical(record)
            prior = existing[fixture].get(record_id)
            if prior is not None and prior != encoded:
                raise RecoveryError(f"active_record_conflict:{fixture}:{record_id}")
            existing[fixture][record_id] = encoded

    source_counts: dict[str, int] = {}
    for source, records in source_records:
        source_counts[source] = len(records)
        for record in records:
            fixture = str(record["fixture"])
            record_id = str(record["record_id"])
            encoded = _canonical(record)
            prior = existing[fixture].get(record_id)
            if prior is not None:
                if prior != encoded:
                    raise RecoveryError(f"record_conflict:{fixture}:{record_id}")
                continue
            if record_id in added_ids[fixture]:
                continue
            additions[fixture].append(record)
            added_ids[fixture].add(record_id)
            existing[fixture][record_id] = encoded

    writes: list[str] = []
    if execute:
        for fixture in sorted(additions):
            destination = log_dir / f"{fixture}.jsonl"
            if destination.is_symlink():
                raise RecoveryError(f"destination_symlink:{fixture}")
            with destination.open("a", encoding="utf-8") as handle:
                for record in additions[fixture]:
                    handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
                    handle.write("\n")
            writes.append(destination.relative_to(plugin_root).as_posix())

    return {
        "execute": execute,
        "source_records": source_counts,
        "recovered_records": {fixture: len(records) for fixture, records in sorted(additions.items())},
        "recovered_total": sum(len(records) for records in additions.values()),
        "writes": writes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin-root", type=Path, required=True)
    parser.add_argument("--file-source", action="append", default=[], type=Path)
    parser.add_argument("--git-root", type=Path)
    parser.add_argument("--git-source", action="append", default=[])
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.git_source and args.git_root is None:
        parser.error("--git-root is required with --git-source")

    sources: list[tuple[str, list[dict[str, Any]]]] = []
    for path in args.file_source:
        text, label = _read_file_source(path)
        sources.append((label, _json_lines(text, label)))
    for revision_path in args.git_source:
        text, label = _read_git_source(args.git_root, revision_path)
        sources.append((label, _json_lines(text, label)))
    if not sources:
        parser.error("at least one --file-source or --git-source is required")

    print(json.dumps(recover_records(args.plugin_root, sources, execute=args.execute), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
