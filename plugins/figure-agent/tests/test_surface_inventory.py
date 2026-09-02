"""Keep the canonical document's operator-surface inventory bound to the live registry."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DOC = PLUGIN_ROOT / "docs" / "figure-agent.md"
sys.path.insert(0, str(PLUGIN_ROOT / "mcp"))

import server_impl  # noqa: E402

INVENTORY_HEADING = "## 8. Live operator surface inventory"


def _inventory_section() -> str:
    text = CANONICAL_DOC.read_text(encoding="utf-8")
    assert INVENTORY_HEADING in text, "canonical doc lost its operator surface inventory"
    return text.partition(INVENTORY_HEADING)[2]


def _documented_tools() -> set[str]:
    return set(re.findall(r"`(figure_agent_[a-z_]+)`", _inventory_section()))


def test_inventory_lists_exactly_the_live_mcp_tools() -> None:
    live = set(server_impl.TOOLS)
    documented = _documented_tools()

    assert not live - documented, f"undocumented live tools: {sorted(live - documented)}"
    assert not documented - live, f"documented tools that do not exist: {sorted(documented - live)}"


def test_inventory_declares_an_effect_and_route_for_every_tool() -> None:
    rows = {
        match.group(1): match.group(0)
        for match in re.finditer(r"^\| `(figure_agent_[a-z_]+)` \|.*$", _inventory_section(), re.M)
    }

    assert set(rows) == set(server_impl.TOOLS)
    for name, row in sorted(rows.items()):
        columns = [cell.strip() for cell in row.strip("|").split("|")]
        assert len(columns) == 5, f"{name}: inventory row must keep all five columns"
        assert columns[1], f"{name}: missing read-only/writes effect"
        assert columns[2], f"{name}: missing CLI route"
        assert columns[4], f"{name}: missing description"


def test_canonical_doc_records_the_commit_the_surface_was_reconciled_against() -> None:
    header = CANONICAL_DOC.read_text(encoding="utf-8").partition("## 1. Outcome")[0]

    assert re.search(r"\*\*Operator surface last reconciled against:\*\* `[0-9a-f]{7,40}`", header)
