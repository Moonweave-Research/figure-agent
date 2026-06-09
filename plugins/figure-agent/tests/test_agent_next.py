from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import agent_next  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def _workspace_fixture(workspace: Path, name: str = "next_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(f"name: {name}\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    return fixture


def _tree(workspace: Path) -> list[str]:
    return sorted(path.relative_to(workspace).as_posix() for path in workspace.rglob("*"))


def _run_fig_agent(workspace: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), "python", str(FIG_AGENT), *args],
        cwd=workspace,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_build_next_returns_read_only_envelope(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _workspace_fixture(workspace)
    before = _tree(workspace)

    payload = agent_next.build_next("next_demo", plugin_root=PLUGIN_ROOT, workspace_root=workspace)

    assert payload["schema"] == "figure-agent.next.v1"
    assert payload["success"] is True
    assert payload["state"] == "blocked"
    assert payload["name"] == "next_demo"
    assert payload["writes"] == []
    assert payload["diagnostics"] == []
    assert payload["status"]["schema"] == "figure-agent.next-action-summary.v1"
    assert payload["next"]["command"] == payload["status"]["safe_command"]
    assert payload["next"]["requires_human"] is False
    assert payload["next"]["writes"] is False
    assert payload["alternatives"][0]["command"] == "fig-agent status next_demo --json"
    assert _tree(workspace) == before


def test_build_next_missing_fixture_returns_workspace_diagnostic(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples").mkdir(parents=True)

    payload = agent_next.build_next(
        "missing_demo",
        plugin_root=PLUGIN_ROOT,
        workspace_root=workspace,
    )

    assert payload["schema"] == "figure-agent.next.v1"
    assert payload["success"] is False
    assert payload["state"] == "missing_fixture"
    assert payload["writes"] == []
    assert payload["diagnostics"][0]["code"] == "fixture_missing"
    assert payload["next"]["command"] is None


def test_fig_agent_next_cli_json_is_read_only(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _workspace_fixture(workspace)
    before = _tree(workspace)

    result = _run_fig_agent(workspace, "next", "next_demo", "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.next.v1"
    assert payload["success"] is True
    assert payload["writes"] == []
    assert payload["next"]["command"] is None
    assert payload["next"]["action"] == "create_or_fix_source"
    assert payload["alternatives"][0]["command"] == "fig-agent status next_demo --json"
    assert _tree(workspace) == before
