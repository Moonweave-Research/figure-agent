from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]


def test_package_cowork_plugin_zip_contract(tmp_path: Path) -> None:
    output_dir = tmp_path / "dist"

    result = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "scripts" / "package_cowork_plugin.py"),
            "--output",
            str(output_dir),
        ],
        cwd=PLUGIN_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    zip_path = output_dir / "figure-agent-cowork-0.9.3.zip"
    assert zip_path.is_file()

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())

    required = {
        ".mcp.json",
        ".claude-plugin/plugin.json",
        "skills/figure-agent/SKILL.md",
        "commands/fig_status.md",
        "mcp/figure_agent_server.py",
        "scripts/status.py",
        "styles/polymer-paper-preamble.sty",
        "bin/fig-agent",
    }
    assert required <= names
    assert not any(name.startswith("examples/fig1_overview_v2") for name in names)
    assert not any(name.startswith("docs/trials/") for name in names)
    assert not any(name.startswith("docs/historical/") for name in names)
    assert not any(name.startswith("docs/milestones/") for name in names)
    assert not any(name.startswith("docs/superpowers/") for name in names)
    assert not any("/build/" in name or name.startswith("build/") for name in names)
    assert not any("/exports/" in name or name.startswith("exports/") for name in names)
    assert not any(".venv/" in name for name in names)


def test_package_cowork_plugin_includes_installed_smoke_fixtures(tmp_path: Path) -> None:
    output_dir = tmp_path / "dist"
    suites = yaml.safe_load(
        (PLUGIN_ROOT / "benchmarks" / "quality_suites.yaml").read_text(encoding="utf-8")
    )
    smoke_fixtures = suites["suites"]["smoke"]["fixtures"]

    result = subprocess.run(
        [
            sys.executable,
            str(PLUGIN_ROOT / "scripts" / "package_cowork_plugin.py"),
            "--output",
            str(output_dir),
        ],
        cwd=PLUGIN_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    zip_path = output_dir / "figure-agent-cowork-0.9.3.zip"
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())

    for fixture in smoke_fixtures:
        assert f"examples/{fixture}/spec.yaml" in names
        assert f"examples/{fixture}/briefing.md" in names
        assert f"examples/{fixture}/{fixture}.tex" in names
        assert f"examples/{fixture}/benchmark_contract.yaml" in names
    assert "examples/smoke_label_overlap_demo/benchmark_reports/text_boundary.json" in names
