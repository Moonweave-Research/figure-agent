import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE_ROOT = PLUGIN_ROOT.parents[1]

sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from plugin_package_audit import find_mcp_config_issues  # noqa: E402


def test_codex_manifest_exposes_the_shared_skill_and_its_own_mcp_facade() -> None:
    """Codex resolves a plugin-local ``cwd: .`` inside its installed package;
    Claude Code resolves the same value against the user's project. The two
    runtimes therefore cannot share one manifest."""
    manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    codex_mcp = json.loads(
        (PLUGIN_ROOT / ".codex-plugin" / "mcp.json").read_text(encoding="utf-8")
    )

    assert manifest["name"] == "figure-agent"
    assert manifest["skills"] == "./skills/"
    assert manifest["mcpServers"] == "./.codex-plugin/mcp.json"
    assert codex_mcp["mcpServers"]["figure-agent"] == {
        "command": "uv",
        "args": ["run", "--project", ".", "python3", "mcp/figure_agent_server.py"],
        "cwd": ".",
    }


def test_codex_runtime_does_not_borrow_the_claude_manifest() -> None:
    manifest = json.loads(
        (PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    claude_mcp = json.loads((PLUGIN_ROOT / ".mcp.json").read_text(encoding="utf-8"))
    server = claude_mcp["mcpServers"]["figure-agent"]

    assert manifest["mcpServers"] != "./.mcp.json"
    assert server["cwd"] == "${CLAUDE_PLUGIN_ROOT}"
    assert server["env"]["FIGURE_AGENT_PLUGIN_ROOT"] == "${CLAUDE_PLUGIN_ROOT}"
    assert find_mcp_config_issues(PLUGIN_ROOT) == []


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
