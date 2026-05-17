"""Deterministic input hashing helpers for quality-state manifests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _relative_manifest_path(path: Path, base_dir: Path) -> str:
    try:
        return str(path.resolve().relative_to(base_dir.resolve()))
    except ValueError:
        return str(path.resolve())


def input_manifest_hash(paths: tuple[Path, ...], *, base_dir: Path) -> str:
    entries = [
        {
            "path": _relative_manifest_path(path, base_dir),
            "sha256": file_sha256(path),
        }
        for path in sorted(dict.fromkeys(paths), key=lambda item: str(item.resolve()))
    ]
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"
