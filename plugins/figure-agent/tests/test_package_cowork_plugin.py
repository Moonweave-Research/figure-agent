from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import package_cowork_plugin
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]


def test_package_cowork_plugin_default_output_is_plugin_local(
    tmp_path: Path, monkeypatch
) -> None:
    built: list[Path] = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        package_cowork_plugin,
        "build_zip",
        lambda output: built.append(output) or output / "figure-agent-cowork-test.zip",
    )

    assert package_cowork_plugin.main([]) == 0
    assert built == [PLUGIN_ROOT / "dist" / "cowork"]


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
        ".codex-plugin/plugin.json",
        "skills/figure-agent/SKILL.md",
        "skills/figure-agent/references/vision-critique-rubric.md",
        "commands/fig_status.md",
        "mcp/figure_agent_server.py",
        "scripts/claim_authority.py",
        "scripts/status.py",
        "scripts/checks/check_silhouette_morphology.py",
        "styles/polymer-paper-preamble.sty",
        "bin/fig-agent",
        "docs/figure-agent.md",
        "docs/architecture-overview.md",
        "docs/document-status.yaml",
    }
    assert required <= names
    assert not any(name.startswith("examples/fig1_overview_v2") for name in names)
    assert not any(name.startswith("docs/trials/") for name in names)
    assert not any(name.startswith("docs/historical/") for name in names)
    assert not any(name.startswith("docs/milestones/") for name in names)
    assert not any(name.startswith("docs/superpowers/") for name in names)
    assert "docs/current-sulfur-paper-figure-state.md" not in names
    assert "docs/paper_figure_map.yaml" not in names
    assert "docs/product-spec.md" not in names
    assert "docs/execution-plan.md" not in names
    assert not any(name.startswith("docs/architecture-v0.") for name in names)
    assert not any(name.startswith("docs/golden-target-") for name in names)
    assert not any(name.startswith("docs/style-benchmark-comparisons/") for name in names)
    assert not any(name.startswith("docs/decision-packets/") for name in names)
    assert not any(name.startswith("docs/decision-records/") for name in names)
    assert not any(name.startswith("docs/experience-log/") for name in names)
    assert not any("/build/" in name or name.startswith("build/") for name in names)
    assert not any("/exports/" in name or name.startswith("exports/") for name in names)
    assert not any(".venv/" in name for name in names)


def test_package_cowork_plugin_rejects_personal_absolute_paths(
    tmp_path: Path, monkeypatch
) -> None:
    import package_cowork_plugin

    unsafe_shell = tmp_path / "install.sh"
    unsafe_shell.write_text("root=/Users/example/private/file\n", encoding="utf-8")
    unsafe_extensionless = tmp_path / "fig-agent"
    unsafe_extensionless.write_text(
        "workspace=/home/example/private/file\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        package_cowork_plugin,
        "_included_files",
        lambda: [unsafe_shell, unsafe_extensionless],
    )
    monkeypatch.setattr(package_cowork_plugin, "PLUGIN_ROOT", tmp_path)
    monkeypatch.setattr(package_cowork_plugin, "_version", lambda: "test")

    try:
        package_cowork_plugin.build_zip(tmp_path / "dist")
    except ValueError as exc:
        assert "personal absolute paths" in str(exc)
        assert "install.sh" in str(exc)
        assert "fig-agent" in str(exc)
    else:
        raise AssertionError("personal absolute path was packaged")


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
