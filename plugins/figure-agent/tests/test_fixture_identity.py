from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fixture_identity  # noqa: E402


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("fig1", True),
        ("fig with spaces", True),
        ("", False),
        ("   ", False),
        ("../outside", False),
        ("nested/fixture", False),
        ("/tmp/fixture", False),
    ],
)
def test_is_safe_fixture_name_accepts_only_single_relative_components(
    name: str, expected: bool
) -> None:
    assert fixture_identity.is_safe_fixture_name(name) is expected


def test_validate_fixture_name_raises_shared_message() -> None:
    with pytest.raises(
        ValueError,
        match="fixture name must be a single examples/<name> directory name",
    ):
        fixture_identity.validate_fixture_name("../outside")
