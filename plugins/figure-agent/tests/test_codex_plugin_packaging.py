import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_ROOT = PLUGIN_ROOT.parents[1]


def test_codex_manifest_exposes_the_shared_skill_and_mcp_facade() -> None:
    manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    mcp = json.loads((PLUGIN_ROOT / ".mcp.json").read_text(encoding="utf-8"))

    assert manifest["name"] == "figure-agent"
    assert manifest["skills"] == "./skills/"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert mcp["mcpServers"]["figure-agent"] == {
        "command": "uv",
        "args": ["run", "--project", ".", "python3", "mcp/figure_agent_server.py"],
        "cwd": ".",
    }


def test_repo_marketplace_points_at_the_active_plugin_source() -> None:
    marketplace = json.loads(
        (MARKETPLACE_ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
    )

    assert marketplace["name"] == "figure-agent-local"
    assert marketplace["plugins"] == [
        {
            "name": "figure-agent",
            "source": {"source": "local", "path": "./plugins/figure-agent"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Developer Tools",
        }
    ]
