from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import fixture_fork  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIG_AGENT = PLUGIN_ROOT / "bin" / "fig-agent"


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def _tree(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _write_source_fixture(workspace: Path, name: str = "source_fig") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        f"""
name: {name}
panels: []
style_profile: polymer-default
""".lstrip(),
        encoding="utf-8",
    )
    (fixture / "aesthetic_intent.yaml").write_text(
        f"schema: figure-agent.aesthetic-intent.v2\nfixture: {name}\n",
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text(f"# Briefing - {name}\n", encoding="utf-8")
    (fixture / f"{name}.tex").write_text(
        f"% {name}\n\\node at (0,0) {{{name}}};\n",
        encoding="utf-8",
    )
    (fixture / "reference").mkdir()
    (fixture / "reference" / "style.txt").write_text(f"reference for {name}\n", encoding="utf-8")
    (fixture / "build").mkdir()
    (fixture / "build" / f"{name}.png").write_bytes(b"generated\n")
    (fixture / "exports").mkdir()
    (fixture / "exports" / f"{name}.svg").write_text("<svg />\n", encoding="utf-8")
    (fixture / "critique.md").write_text("critique\n", encoding="utf-8")
    (fixture / "human_attestation.json").write_text("{}\n", encoding="utf-8")
    return fixture


def test_fork_fixture_copies_only_source_side_files_and_rewrites_identity(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    source = _write_source_fixture(workspace)
    before_source = _tree(source)

    receipt = fixture_fork.fork_fixture(
        "source_fig",
        "target_fig",
        reason="new visual lane",
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )

    target = workspace / "examples" / "target_fig"
    assert receipt["schema"] == fixture_fork.SCHEMA
    assert receipt["acceptance_state"] == "NOT_DECLARED"
    assert receipt["source_fixture"] == "source_fig"
    assert receipt["target_fixture"] == "target_fig"
    assert (target / "target_fig.tex").is_file()
    assert not (target / "source_fig.tex").exists()
    assert not (target / "build").exists()
    assert not (target / "exports").exists()
    assert not (target / "critique.md").exists()
    assert not (target / "human_attestation.json").exists()
    assert "name: target_fig" in (target / "spec.yaml").read_text(encoding="utf-8")
    assert "fixture: target_fig" in (target / "aesthetic_intent.yaml").read_text(
        encoding="utf-8"
    )
    assert "source_fig" not in (target / "target_fig.tex").read_text(encoding="utf-8")
    assert (target / "fork_receipt.json").is_file()
    assert _tree(source) == before_source


def test_fork_fixture_dry_run_does_not_create_target(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_source_fixture(workspace)

    receipt = fixture_fork.fork_fixture(
        "source_fig",
        "target_fig",
        reason="preview only",
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
        dry_run=True,
    )

    assert receipt["dry_run"] is True
    assert "build" in receipt["skipped_generated_or_state_entries"]
    assert "exports" in receipt["skipped_generated_or_state_entries"]
    assert not (workspace / "examples" / "target_fig").exists()


def test_fork_fixture_skips_source_symlinks(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    source = _write_source_fixture(workspace)
    shutil_target = workspace / "shared_reference"
    shutil_target.mkdir()
    (source / "reference").rename(source / "reference_real")
    (source / "reference_real" / "style.txt").write_text("real reference\n", encoding="utf-8")
    os.symlink(shutil_target, source / "reference")

    receipt = fixture_fork.fork_fixture(
        "source_fig",
        "target_fig",
        reason="new visual lane",
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )

    target = workspace / "examples" / "target_fig"
    assert receipt["skipped_symlink_entries"] == ["reference"]
    assert not (target / "reference").exists()
    assert (target / "reference_real").is_dir()


def test_fork_fixture_rejects_existing_target(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_source_fixture(workspace)
    _write_source_fixture(workspace, "target_fig")

    result = fixture_fork.main(
        ["source_fig", "target_fig", "--reason", "duplicate", "--json"],
        workspace_root=workspace,
        plugin_root=PLUGIN_ROOT,
    )

    assert result == 1


def test_fork_fixture_cli_creates_target(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_source_fixture(workspace)

    result = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(PLUGIN_ROOT),
            "python",
            str(FIG_AGENT),
            "fork-fixture",
            "source_fig",
            "target_fig",
            "--reason",
            "cli fork",
            "--json",
        ],
        cwd=workspace,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == fixture_fork.SCHEMA
    assert (workspace / "examples" / "target_fig" / "target_fig.tex").is_file()
