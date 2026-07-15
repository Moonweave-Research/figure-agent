"""Shared fail-closed file transaction primitives for bounded repair paths."""

from __future__ import annotations

import fcntl
import json
import os
import stat
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class RepairTransactionError(RuntimeError):
    """Raised when an exclusive repair transaction cannot start."""


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def fsync_directory(path: Path) -> None:
    """Durably record a directory-entry mutation such as a rollback unlink."""
    _fsync_directory(path)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        if existing_mode is not None:
            os.fchmod(fd, existing_mode)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def atomic_create_text(path: Path, text: str) -> None:
    """Atomically publish a new file without ever replacing an existing path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
        _fsync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def atomic_create_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_create_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


@contextmanager
def exclusive_lock(path: Path, *, owner: str) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RepairTransactionError("transaction lock exists") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(owner + "\n")
        yield
    finally:
        path.unlink(missing_ok=True)


@contextmanager
def recoverable_exclusive_lock(path: Path, *, owner: str) -> Iterator[None]:
    """Hold a process-lifetime lock that a later process can reclaim after a crash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise RepairTransactionError("transaction lock is invalid") from exc
    lock_record = json.dumps(
        {"schema": "figure-agent.recoverable-lock.v1", "owner": owner},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    owns_record = False
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RepairTransactionError("transaction lock exists") from exc
        current = os.pread(fd, 4096, 0)
        if current not in {b"", lock_record}:
            raise RepairTransactionError("transaction lock exists")
        os.ftruncate(fd, 0)
        os.pwrite(fd, lock_record, 0)
        os.fsync(fd)
        owns_record = True
        yield
    finally:
        try:
            opened = os.fstat(fd)
            current = path.lstat()
            if owns_record and (opened.st_dev, opened.st_ino) == (
                current.st_dev,
                current.st_ino,
            ):
                path.unlink()
                _fsync_directory(path.parent)
        except FileNotFoundError:
            pass
        finally:
            os.close(fd)
