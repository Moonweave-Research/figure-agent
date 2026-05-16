"""Tests for parsing role-typed reference packs."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from reference_pack import (  # noqa: E402
    anti_reference_entries,
    parse_reference_roles,
    reference_pack_failures,
)


def test_parse_reference_roles_reads_role_table() -> None:
    text = """
# Reference Pack

| File | Role | Use | Do Not Transfer |
|---|---|---|---|
| `reference/a.png` | style, layout | palette only | Do not transfer topology. |
| `reference/b.png` | anti_reference, motif | sulfur motif | Do Not Transfer network reading. |
"""

    entries = parse_reference_roles(text)

    assert entries[0].source == "reference/a.png"
    assert entries[0].roles == ["style", "layout"]
    assert entries[0].do_not_transfer == "Do not transfer topology."
    assert entries[1].roles == ["anti_reference", "motif"]
    assert anti_reference_entries(entries) == [entries[1]]


def test_reference_pack_failures_requires_role_and_transfer_boundary(tmp_path: Path) -> None:
    pack = tmp_path / "reference_pack.md"
    pack.write_text(
        "| File | Role | Use | Do Not Transfer |\n"
        "|---|---|---|---|\n"
        "| `reference/a.png` |  | palette only |  |\n",
        encoding="utf-8",
    )

    failures = reference_pack_failures(pack)

    assert "reference row missing role: reference/a.png" in failures
    assert "reference row missing Do Not Transfer boundary: reference/a.png" in failures


def test_pilot_reference_pack_has_roles_and_anti_reference_boundary() -> None:
    pack = (
        Path(__file__).resolve().parents[1]
        / "examples"
        / "fig1_overview_v2_pair_001_vault"
        / "reference"
        / "reference_pack.md"
    )

    entries = parse_reference_roles(pack.read_text(encoding="utf-8"))

    assert reference_pack_failures(pack) == []
    assert any("anti_reference" in entry.roles for entry in entries)
    assert any("network topology" in entry.do_not_transfer for entry in entries)
