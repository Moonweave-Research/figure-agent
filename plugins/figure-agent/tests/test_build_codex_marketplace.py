from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

import build_codex_marketplace  # noqa: E402
import plugin_package_audit  # noqa: E402


def test_builds_lean_self_contained_codex_marketplace(tmp_path: Path) -> None:
    output = tmp_path / "marketplace"

    result = build_codex_marketplace.build_marketplace(output)

    plugin = output / "plugins" / "figure-agent"
    marketplace = json.loads(
        (output / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
    )
    assert result["plugin_root"] == plugin.as_posix()
    assert result["source"] == "release_zip"
    assert marketplace["plugins"][0]["source"] == {
        "source": "local",
        "path": "./plugins/figure-agent",
    }
    assert (plugin / ".codex-plugin" / "plugin.json").is_file()
    assert (plugin / ".claude-plugin" / "plugin.json").is_file()
    assert (plugin / "scripts" / "checks" / "check_silhouette_morphology.py").is_file()
    assert not (plugin / "examples" / "fig5_actuation_mechanism" / "build").exists()
    assert plugin_package_audit.find_packaging_junk(plugin) == []
    assert plugin_package_audit.find_mcp_config_issues(plugin) == []


def test_refuses_to_overwrite_existing_marketplace(tmp_path: Path) -> None:
    output = tmp_path / "marketplace"
    output.mkdir()

    with pytest.raises(
        build_codex_marketplace.CodexMarketplaceBuildError,
        match="output_already_exists",
    ):
        build_codex_marketplace.build_marketplace(output)
