from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from plugin_install_freshness import (  # noqa: E402
    compare_plugin_install,
    latest_installed_root,
    main,
)


def _write_plugin(
    root: Path,
    *,
    status_text: str = "status",
    version: str = "0.1.0",
) -> None:
    (root / ".claude-plugin").mkdir(parents=True)
    (root / "commands").mkdir(parents=True)
    (root / "scripts").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "figure-agent", "version": version}) + "\n",
        encoding="utf-8",
    )
    (root / "commands" / "fig_status.md").write_text(status_text, encoding="utf-8")
    (root / "scripts" / "status.py").write_text("print('status')\n", encoding="utf-8")


def test_compare_plugin_install_reports_fresh_when_payloads_match(tmp_path: Path) -> None:
    source = tmp_path / "source"
    installed = tmp_path / "cache" / "0.1.0"
    _write_plugin(source)
    _write_plugin(installed)

    result = compare_plugin_install(source, installed)

    assert result["schema"] == "figure-agent.plugin-install-freshness.v1"
    assert result["state"] == "fresh"
    assert result["changed_files"] == []
    assert result["missing_files"] == []
    assert result["extra_files"] == []
    assert result["refresh_strategy"] == "none"
    assert result["source_package_hygiene"] == {
        "state": "clean",
        "junk_count": 0,
        "junk_paths": [],
        "next_action": "development plugin tree package has no generated junk",
    }
    assert result["installed_package_hygiene"] == {
        "state": "clean",
        "junk_count": 0,
        "junk_paths": [],
        "next_action": "installed plugin cache package has no generated junk",
    }


def test_compare_plugin_install_reports_stale_file_differences(tmp_path: Path) -> None:
    source = tmp_path / "source"
    installed = tmp_path / "cache" / "0.1.0"
    _write_plugin(source, status_text="new status")
    _write_plugin(installed, status_text="old status", version="0.0.9")
    (source / "commands" / "fig_drive.md").write_text("drive\n", encoding="utf-8")
    (installed / "commands" / "old.md").write_text("old\n", encoding="utf-8")

    result = compare_plugin_install(source, installed)

    assert result["state"] == "stale"
    assert result["changed_files"] == [
        ".claude-plugin/plugin.json",
        "commands/fig_status.md",
    ]
    assert result["missing_files"] == ["commands/fig_drive.md"]
    assert result["extra_files"] == ["commands/old.md"]
    assert result["source_version"] == "0.1.0"
    assert result["installed_version"] == "0.0.9"
    assert result["refresh_strategy"] == "update"
    assert "claude plugin update figure-agent@figure-agent-local" in result["next_action"]


def test_compare_plugin_install_recommends_reinstall_for_same_version_stale_cache(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    installed = tmp_path / "cache" / "0.1.0"
    _write_plugin(source, status_text="new status")
    _write_plugin(installed, status_text="old status")

    result = compare_plugin_install(source, installed)

    assert result["state"] == "stale"
    assert result["source_version"] == "0.1.0"
    assert result["installed_version"] == "0.1.0"
    assert result["refresh_strategy"] == "reinstall_same_version"
    assert result["next_action"] == (
        "claude plugin uninstall figure-agent && "
        "claude plugin install figure-agent@figure-agent-local"
    )


def test_compare_plugin_install_reports_missing_install(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _write_plugin(source)

    result = compare_plugin_install(source, None)

    assert result["state"] == "missing"
    assert result["installed_root"] is None
    assert result["source_version"] == "0.1.0"
    assert result["installed_version"] is None
    assert result["refresh_strategy"] == "install_missing"
    assert result["next_action"] == "claude plugin install figure-agent@figure-agent-local"
    assert result["installed_package_hygiene"] == {
        "state": "unknown",
        "junk_count": 0,
        "junk_paths": [],
        "next_action": "install plugin before auditing package hygiene",
    }


def test_compare_plugin_install_reports_invalid_install_root(tmp_path: Path) -> None:
    source = tmp_path / "source"
    installed = tmp_path / "not-a-plugin"
    _write_plugin(source)
    installed.mkdir()

    result = compare_plugin_install(source, installed)

    assert result["state"] == "invalid"
    assert result["installed_root"] == str(installed.resolve())
    assert result["source_version"] == "0.1.0"
    assert result["installed_version"] is None
    assert result["refresh_strategy"] == "reinstall_invalid"
    assert result["next_action"] == (
        "claude plugin uninstall figure-agent && "
        "claude plugin install figure-agent@figure-agent-local"
    )
    assert result["installed_package_hygiene"] == {
        "state": "unknown",
        "junk_count": 0,
        "junk_paths": [],
        "next_action": "reinstall plugin before auditing package hygiene",
    }


def test_compare_plugin_install_ignores_generated_cache_junk(tmp_path: Path) -> None:
    source = tmp_path / "source"
    installed = tmp_path / "cache" / "0.1.0"
    _write_plugin(source)
    _write_plugin(installed)
    (installed / ".venv" / "bin").mkdir(parents=True)
    (installed / ".venv" / "bin" / "python").write_text("generated\n", encoding="utf-8")
    (installed / "examples" / "demo" / "build").mkdir(parents=True)
    (installed / "examples" / "demo" / "build" / "demo.pdf").write_bytes(b"%PDF")
    (installed / ".in_use").mkdir()
    (installed / ".in_use" / "123").write_text("active\n", encoding="utf-8")
    (installed / "examples" / "demo" / "demo.aux").write_text("aux\n", encoding="utf-8")
    (installed / "examples" / "demo" / "demo.log").write_text("log\n", encoding="utf-8")
    (installed / "examples" / "demo" / "previews").mkdir()
    (installed / "examples" / "demo" / "previews" / "dummy.png").write_bytes(b"PNG")

    result = compare_plugin_install(source, installed)

    assert result["state"] == "fresh"
    assert result["extra_files"] == []
    assert result["installed_package_hygiene"]["state"] == "dirty"
    assert result["installed_package_hygiene"]["junk_count"] == 2
    assert result["installed_package_hygiene"]["junk_paths"] == [
        ".venv",
        "examples/demo/build",
    ]
    assert "plugin_package_audit.py" in result["installed_package_hygiene"]["next_action"]


def test_compare_plugin_install_reports_dirty_source_package_hygiene(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    installed = tmp_path / "cache" / "0.1.0"
    _write_plugin(source)
    _write_plugin(installed)
    (source / ".venv" / "bin").mkdir(parents=True)
    (source / ".venv" / "bin" / "python").write_text("generated\n", encoding="utf-8")

    result = compare_plugin_install(source, installed)

    assert result["state"] == "fresh"
    assert result["installed_package_hygiene"]["state"] == "clean"
    assert result["source_package_hygiene"]["state"] == "dirty"
    assert result["source_package_hygiene"]["junk_paths"] == [".venv"]
    assert "plugin_package_audit.py" in result["source_package_hygiene"]["next_action"]


def test_package_hygiene_next_actions_quote_shell_special_paths(tmp_path: Path) -> None:
    source = tmp_path / "[figure-agent]" / "source"
    installed = tmp_path / "[figure-agent]" / "cache" / "0.1.0"
    _write_plugin(source)
    _write_plugin(installed)
    (source / ".venv" / "bin").mkdir(parents=True)
    (source / ".venv" / "bin" / "python").write_text("generated\n", encoding="utf-8")
    (installed / ".venv" / "bin").mkdir(parents=True)
    (installed / ".venv" / "bin" / "python").write_text("generated\n", encoding="utf-8")

    result = compare_plugin_install(source, installed)

    assert f"'{source.resolve()}'" in result["source_package_hygiene"]["next_action"]
    assert (
        f"'{installed.resolve()}'"
        in result["installed_package_hygiene"]["next_action"]
    )


def test_cli_returns_zero_for_fresh_clean_installed_package(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    installed = tmp_path / "cache" / "0.1.0"
    _write_plugin(source)
    _write_plugin(installed)

    exit_code = main([str(installed), "--source-root", str(source)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["state"] == "fresh"
    assert output["source_package_hygiene"]["state"] == "clean"
    assert output["installed_package_hygiene"]["state"] == "clean"


def test_cli_returns_nonzero_for_fresh_but_dirty_source_package(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    installed = tmp_path / "cache" / "0.1.0"
    _write_plugin(source)
    _write_plugin(installed)
    (source / ".venv" / "bin").mkdir(parents=True)
    (source / ".venv" / "bin" / "python").write_text("generated\n", encoding="utf-8")

    exit_code = main([str(installed), "--source-root", str(source)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["state"] == "fresh"
    assert output["source_package_hygiene"]["state"] == "dirty"
    assert output["installed_package_hygiene"]["state"] == "clean"


def test_cli_returns_nonzero_for_fresh_but_dirty_installed_package(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "source"
    installed = tmp_path / "cache" / "0.1.0"
    _write_plugin(source)
    _write_plugin(installed)
    (installed / ".venv" / "bin").mkdir(parents=True)
    (installed / ".venv" / "bin" / "python").write_text("generated\n", encoding="utf-8")

    exit_code = main([str(installed), "--source-root", str(source)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["state"] == "fresh"
    assert output["source_package_hygiene"]["state"] == "clean"
    assert output["installed_package_hygiene"]["state"] == "dirty"


def test_compare_plugin_install_ignores_real_example_work_product(tmp_path: Path) -> None:
    source = tmp_path / "source"
    installed = tmp_path / "cache" / "0.1.0"
    _write_plugin(source)
    _write_plugin(installed)
    (source / "examples" / "demo").mkdir(parents=True)
    (installed / "examples" / "demo").mkdir(parents=True)
    (source / "examples" / "demo" / "demo.tex").write_text("new figure\n", encoding="utf-8")
    (installed / "examples" / "demo" / "demo.tex").write_text("old figure\n", encoding="utf-8")

    result = compare_plugin_install(source, installed)

    assert result["state"] == "fresh"
    assert result["changed_files"] == []


def test_latest_installed_root_selects_highest_version_with_manifest(tmp_path: Path) -> None:
    cache = tmp_path / "cache" / "figure-agent-local" / "figure-agent"
    _write_plugin(cache / "0.8.1")
    _write_plugin(cache / "0.9.2")
    (cache / "scratch").mkdir(parents=True)

    assert latest_installed_root(cache) == cache / "0.9.2"
