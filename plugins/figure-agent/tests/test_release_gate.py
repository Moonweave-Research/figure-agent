from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PLUGIN_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_ROOT))

import release_gate  # noqa: E402


def test_release_gate_builds_and_audits_package_with_skipped_heavy_checks(tmp_path: Path) -> None:
    report = release_gate.run_release_gate(
        output_dir=tmp_path / "dist",
        max_mib=50,
        run_targeted_tests=False,
        run_full_pytest=False,
        run_ruff=False,
        run_claude_validate=False,
    )

    assert report["schema"] == release_gate.SCHEMA
    assert report["success"] is True
    assert Path(report["zip_path"]).is_file()
    assert report["package_size_mib"] < 50
    states = {step["name"]: step["state"] for step in report["steps"]}
    assert states["targeted_tests"] == "skipped"
    assert states["full_pytest"] == "skipped"
    assert states["ruff"] == "skipped"
    assert states["package_required_paths"] == "passed"
    assert states["package_excluded_paths"] == "passed"
    assert states["package_audit"] == "passed"
    assert states["claude_validate_package"] == "skipped"
    assert states["claude_validate_marketplace"] == "skipped"
    package_audit = next(step for step in report["steps"] if step["name"] == "package_audit")
    assert "--clean" not in package_audit["command"]


def test_release_gate_cli_emits_json_report(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_ROOT / "release_gate.py"),
            "--output",
            str(tmp_path / "dist"),
            "--max-mib",
            "50",
            "--skip-targeted-tests",
            "--skip-full-pytest",
            "--skip-ruff",
            "--skip-claude-validate",
            "--json",
        ],
        cwd=PLUGIN_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == release_gate.SCHEMA
    assert payload["success"] is True
    assert Path(payload["zip_path"]).is_file()


def test_release_gate_zip_contains_release_gate_script(tmp_path: Path) -> None:
    report = release_gate.run_release_gate(
        output_dir=tmp_path / "dist",
        max_mib=50,
        run_targeted_tests=False,
        run_full_pytest=False,
        run_ruff=False,
        run_claude_validate=False,
    )

    import zipfile

    with zipfile.ZipFile(report["zip_path"]) as archive:
        names = set(archive.namelist())

    assert "scripts/release_gate.py" in names


def test_release_gate_reports_missing_required_package_path() -> None:
    names = {".mcp.json", "bin/fig-agent"}

    step = release_gate._verify_required_paths(names)

    assert step["state"] == "failed"
    assert ".claude-plugin/plugin.json" in step["details"]["missing"]


def test_release_gate_reports_excluded_package_paths() -> None:
    names = {
        ".mcp.json",
        "examples/fig1_overview_v2/spec.yaml",
        "examples/smoke_trap_demo/build/smoke_trap_demo.pdf",
        ".venv/bin/python",
    }

    step = release_gate._verify_excluded_paths(names)

    assert step["state"] == "failed"
    assert step["details"]["unexpected_count"] == 3


def test_fig_agent_helper_allowlist_includes_release_gate() -> None:
    fig_agent = (PLUGIN_ROOT / "bin" / "fig-agent").read_text(encoding="utf-8")

    assert '"release_gate.py"' in fig_agent
