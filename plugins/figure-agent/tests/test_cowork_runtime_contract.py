from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _write_fixture(workspace: Path, name: str = "smoke_trap_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text("name: smoke_trap_demo\n", encoding="utf-8")
    (fixture / "briefing.md").write_text("# Brief\n", encoding="utf-8")
    return fixture


def _public_entry_env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    venv = env.pop("VIRTUAL_ENV", None)
    if venv:
        venv_bin = str(Path(venv) / "bin")
        env["PATH"] = os.pathsep.join(
            part for part in env.get("PATH", "").split(os.pathsep) if part != venv_bin
        )
    return env


def test_fig_agent_status_reads_workspace_fixture_and_bundled_style(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    _write_fixture(workspace)

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "status",
            "smoke_trap_demo",
            "--json",
        ],
        cwd=tmp_path,
        env=_public_entry_env(workspace),
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
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "status",
            "missing_demo",
            "--json",
        ],
        cwd=tmp_path,
        env=_public_entry_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["name"] == "missing_demo"
    assert payload["stage"] == 0


def test_fig_agent_closeout_uses_public_wrapper_without_type_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake_main(argv: list[str]) -> int:
        calls.append(argv)
        return 7

    loader = importlib.machinery.SourceFileLoader(
        "fig_agent_bin_contract",
        str(PLUGIN_ROOT / "bin" / "fig-agent"),
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    monkeypatch.setitem(sys.modules, "fig_closeout", types.SimpleNamespace(main=fake_main))

    assert module._closeout(["smoke_trap_demo", "--json"]) == 7
    assert calls == [["smoke_trap_demo", "--json"]]


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
    assert payload["bundle"]["plugin_root_kind"] in {
        "source_tree",
        "installed_cache",
        "unpacked_zip",
        "unknown",
    }
    assert isinstance(payload["bundle"]["unexpected_cache_state"], list)
    assert payload["workspace"]["state"] == "missing"
    assert payload["workspace"]["workspace_source"] == "FIGURE_AGENT_WORKSPACE"
    assert "examples" in payload["workspace"]["missing"]
    assert "lualatex" in payload["dependencies"]["missing"]


def test_doctor_reports_plugin_root_cwd_as_source_tree_workspace() -> None:
    result = subprocess.run(
        [sys.executable, str(PLUGIN_ROOT / "bin" / "fig-agent"), "doctor", "--json"],
        cwd=PLUGIN_ROOT,
        env={
            "FIGURE_AGENT_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "PATH": os.environ.get("PATH", ""),
        },
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["bundle"]["state"] == "ok"
    assert payload["workspace"]["state"] == "ok"
    assert payload["workspace"]["workspace_root"] == str(PLUGIN_ROOT)
    assert payload["workspace"]["workspace_source"] == "cwd"


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
    assert payload["bundle"]["plugin_root_kind"] == "unpacked_zip"
    assert any("styles" in item for item in payload["bundle"]["missing"])


def test_bundle_diagnostics_reports_unexpected_unpacked_cache_state(tmp_path: Path) -> None:
    sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
    import runtime_paths  # noqa: PLC0415

    plugin_root = tmp_path / "plugin"
    (plugin_root / ".claude-plugin").mkdir(parents=True)
    (plugin_root / "scripts").mkdir()
    (plugin_root / "styles").mkdir()
    (plugin_root / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    (plugin_root / "styles" / "polymer-paper-preamble.sty").write_text("% style", encoding="utf-8")
    (plugin_root / "unexpected-local-backup").mkdir()
    (plugin_root / ".venv").mkdir()
    paths = runtime_paths.resolve_runtime_paths(plugin_root=plugin_root, workspace_root=tmp_path)

    payload = runtime_paths.bundle_diagnostics(paths)

    assert payload["plugin_root_kind"] == "unpacked_zip"
    assert ".venv" in payload["unexpected_cache_state"]
    assert "unexpected-local-backup/" in payload["unexpected_cache_state"]



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
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "helper",
            "critique_lint.py",
            "--help",
        ],
        cwd=tmp_path,
        env=_public_entry_env(workspace),
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
