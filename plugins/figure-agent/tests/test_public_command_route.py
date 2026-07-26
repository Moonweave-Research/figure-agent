from __future__ import annotations

from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]


def _route_commands(text: str, start: str, end: str) -> set[str]:
    section = text.partition(start)[2].partition(end)[0]
    return {
        token[1:]
        for token in section.split()
        if token.startswith("/fig_")
    }


def test_root_and_plugin_readmes_share_the_declared_default_route() -> None:
    contract = yaml.safe_load(
        (PLUGIN_ROOT / "docs" / "public-command-route.yaml").read_text(
            encoding="utf-8"
        )
    )
    expected = set(contract["default_route"])
    root = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    plugin = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")

    root_route = _route_commands(
        root,
        "The canonical documented workflow route is:",
        "This route does not retire",
    )
    plugin_route = _route_commands(
        plugin,
        "Canonical documented workflow route:",
        "Supporting commands are explicit",
    )

    assert root_route == expected
    assert plugin_route == expected
    assert not (set(contract["supporting"]) & expected)
    assert not (set(contract["compatibility"]) & expected)


def test_route_contract_does_not_claim_callable_surface_compaction() -> None:
    root = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    plugin = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")

    for text in (root, plugin):
        assert "callable-surface compaction" in text
        assert "remains" in text


def test_route_contract_declares_runtime_entry_route() -> None:
    contract = yaml.safe_load(
        (PLUGIN_ROOT / "docs" / "public-command-route.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert contract["runtime_entry_route"] == ["fig_status", "fig_run"]
