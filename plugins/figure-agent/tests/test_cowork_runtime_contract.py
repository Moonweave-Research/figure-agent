from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _write_fixture(workspace: Path, name: str = "smoke_trap_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: smoke_trap_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    return fixture


def test_fig_agent_status_reads_workspace_fixture_and_bundled_style(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _write_fixture(workspace)

    result = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "status",
            "smoke_trap_demo",
            "--json",
        ],
        cwd=tmp_path,
        env={
            "FIGURE_AGENT_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "FIGURE_AGENT_WORKSPACE": str(workspace),
        },
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["name"] == "smoke_trap_demo"
    assert payload["stage"] == 1


def test_fig_agent_status_missing_name_still_targets_workspace_examples(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples").mkdir(parents=True)

    result = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "status",
            "missing_demo",
            "--json",
        ],
        cwd=tmp_path,
        env={
            "FIGURE_AGENT_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "FIGURE_AGENT_WORKSPACE": str(workspace),
        },
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["name"] == "missing_demo"
    assert payload["stage"] == 0


def test_doctor_reports_workspace_missing_without_bundle_false_positive(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = subprocess.run(
        [sys.executable, str(PLUGIN_ROOT / "bin" / "fig-agent"), "doctor", "--json"],
        cwd=tmp_path,
        env={
            "FIGURE_AGENT_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "FIGURE_AGENT_WORKSPACE": str(workspace),
            "PATH": "",
        },
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["bundle"]["state"] == "ok"
    assert payload["workspace"]["state"] == "missing"
    assert "examples" in payload["workspace"]["missing"]
    assert "lualatex" in payload["dependencies"]["missing"]


def test_doctor_reports_bundle_missing_styles(tmp_path: Path) -> None:
    plugin_root = tmp_path / "plugin"
    (plugin_root / ".claude-plugin").mkdir(parents=True)
    (plugin_root / "scripts").mkdir()
    (plugin_root / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    workspace = tmp_path / "workspace"
    _write_fixture(workspace)

    result = subprocess.run(
        [sys.executable, str(PLUGIN_ROOT / "bin" / "fig-agent"), "doctor", "--json"],
        cwd=tmp_path,
        env={
            "FIGURE_AGENT_PLUGIN_ROOT": str(plugin_root),
            "FIGURE_AGENT_WORKSPACE": str(workspace),
            "PATH": "",
        },
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["bundle"]["state"] == "missing"
    assert any("styles" in item for item in payload["bundle"]["missing"])


def test_fig_agent_rejects_unsafe_fixture_names_before_path_join(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples").mkdir(parents=True)

    result = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "compile",
            "../outside",
        ],
        cwd=tmp_path,
        env={
            "FIGURE_AGENT_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "FIGURE_AGENT_WORKSPACE": str(workspace),
        },
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "fixture name must be a single examples/<name> directory name" in result.stderr


def test_fig_agent_helper_allows_whitelisted_scripts_from_plugin_root(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples").mkdir(parents=True)

    result = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "helper",
            "critique_lint.py",
            "--help",
        ],
        cwd=tmp_path,
        env={
            "FIGURE_AGENT_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "FIGURE_AGENT_WORKSPACE": str(workspace),
        },
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "usage: critique_lint.py" in result.stdout


def test_fig_agent_helper_rejects_unlisted_or_path_scripts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "examples").mkdir(parents=True)

    result = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "helper",
            "../critique_lint.py",
            "--help",
        ],
        cwd=tmp_path,
        env={
            "FIGURE_AGENT_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "FIGURE_AGENT_WORKSPACE": str(workspace),
        },
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "unsupported helper script" in result.stderr
