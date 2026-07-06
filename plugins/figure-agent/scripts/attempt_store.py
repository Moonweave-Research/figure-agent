"""Append-only storage for structured figure convergence attempts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import convergence_models
import fixture_identity


class AttemptStoreError(ValueError):
    """Raised when attempt storage would be unsafe or invalid."""


def _attempt_log_path(plugin_root: Path, fixture: str) -> Path:
    try:
        fixture_identity.validate_fixture_name(fixture)
    except ValueError as exc:
        raise AttemptStoreError("fixture_name_invalid") from exc
    root = (plugin_root / "docs" / "attempts").resolve()
    path = root / f"{fixture}.jsonl"
    if path.is_symlink():
        raise AttemptStoreError("attempt_log_symlink")
    try:
        path.resolve().relative_to(root)
    except ValueError as exc:
        raise AttemptStoreError("attempt_log_path_escape") from exc
    return path


def _with_record_hash(attempt: dict[str, Any]) -> dict[str, Any]:
    record = dict(convergence_models.validate_figure_attempt(attempt))
    record.pop("record_hash", None)
    record["record_hash"] = convergence_models.canonical_hash(record)
    return record


def append_attempt(
    fixture: str,
    attempt: dict[str, Any],
    *,
    plugin_root: Path,
) -> dict[str, Any]:
    path = _attempt_log_path(plugin_root, fixture)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise AttemptStoreError("attempt_log_dir_symlink")
    record = _with_record_hash(attempt)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(convergence_models.canonical_json(record) + "\n")
    return {
        "schema": "figure-agent.attempt-store-write.v1",
        "writes": [f"docs/attempts/{fixture}.jsonl"],
        "record_hash": record["record_hash"],
    }


def read_attempts(fixture: str, *, plugin_root: Path) -> list[dict[str, Any]]:
    path = _attempt_log_path(plugin_root, fixture)
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AttemptStoreError(f"attempt_log_json_invalid:{line_number}") from exc
        if not isinstance(payload, dict):
            raise AttemptStoreError(f"attempt_log_row_invalid:{line_number}")
        rows.append(convergence_models.validate_figure_attempt(payload))
    return rows
