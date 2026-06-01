"""Fixture-name boundary helpers."""

from __future__ import annotations

from pathlib import Path

UNSAFE_FIXTURE_NAME_MESSAGE = (
    "fixture name must be a single examples/<name> directory name"
)


def is_safe_fixture_name(name: str) -> bool:
    if not isinstance(name, str) or not name.strip():
        return False
    relative = Path(name)
    return (
        not relative.is_absolute()
        and len(relative.parts) == 1
        and ".." not in relative.parts
    )


def validate_fixture_name(name: str) -> None:
    if not is_safe_fixture_name(name):
        raise ValueError(UNSAFE_FIXTURE_NAME_MESSAGE)
