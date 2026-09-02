"""Single content-hash primitive for every evidence binding in the plugin."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

CHUNK_BYTES = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()
