from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _write_context_fixture(workspace: Path, name: str = "context_demo") -> Path:
    fixture = workspace / "examples" / name
    fixture.mkdir(parents=True)
    (fixture / "spec.yaml").write_text(
        """
name: context_demo
title: Context Demo
style_profile: polymer-paper
authoring_context_pack:
  enabled: true
panels:
  - id: C
    caption: Trap energy diagram
    semantic_claims:
      - id: trap-depth
        claim: Deep traps are harder to escape than shallow traps.
    locked_invariants:
      - id: energy-up
        invariant: Energy increases upward in the trap diagram.
""".lstrip(),
        encoding="utf-8",
    )
    (fixture / "briefing.md").write_text("## §1. Topic\nCharge trapping\n", encoding="utf-8")
    (fixture / "design.md").write_text("Use compact visual grammar.\n", encoding="utf-8")
    return fixture


def _env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FIGURE_AGENT_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    env["FIGURE_AGENT_WORKSPACE"] = str(workspace)
    return env


def test_context_pack_cli_compiles_read_only_json_payload(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    result = subprocess.run(
        [str(PLUGIN_ROOT / "bin" / "fig-agent"), "context-pack", "context_demo", "--json"],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema"] == "figure-agent.authoring-context-pack.v1"
    assert payload["read_only"] is True
    assert payload["scope_boundary"]["generation_executor"] is False
    assert payload["scope_boundary"]["durable_paper_specific_knowledge_compilation"] is True
    assert payload["semantic_contracts"]["enabled"] is True
    assert payload["semantic_contracts"]["semantic_claims"][0]["id"] == "trap-depth"
    # context_demo != fig1_overview_v2_pair_001_vault: the per-fixture catalog is
    # scoped to its own fixture, so a non-matching fixture gets no per-fixture catalog
    assert payload["rule_catalog"] is None
    assert payload["sources"]["rule_catalog"] == ""
    assert "briefing" in payload["paper_context"]


def test_context_pack_scopes_per_fixture_catalog_to_its_own_fixture() -> None:
    # the per-fixture pair001 catalog must reach only its own fixture; any other
    # figure inherits the universal project catalog but no per-fixture rules
    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "fig1_overview_v2_pair_001_vault",
            "--json",
        ],
        cwd=PLUGIN_ROOT,
        env=_env(PLUGIN_ROOT),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    catalog = payload["rule_catalog"]
    assert catalog is not None
    assert catalog["fixture"] == "fig1_overview_v2_pair_001_vault"
    assert payload["sources"]["rule_catalog"].endswith("authoring-rules-pair001.md")
    rule_ids = [rule["id"] for rule in catalog["rules"]]
    assert "pair001.panel-c-hero-split" in rule_ids


def test_context_pack_accepts_format_json_spelling(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    result = subprocess.run(
        [
            str(PLUGIN_ROOT / "bin" / "fig-agent"),
            "context-pack",
            "context_demo",
            "--format",
            "json",
        ],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["name"] == "context_demo"


def test_context_pack_injects_project_scope_conventions(tmp_path: Path) -> None:
    # cross-figure conventions (e.g. vertical cantilever) must reach every figure's
    # context pack, not stay locked to the fig1 pilot catalog
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    result = subprocess.run(
        [str(PLUGIN_ROOT / "bin" / "fig-agent"), "context-pack", "context_demo", "--json"],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    project = payload["project_rule_catalog"]
    assert project is not None
    rule_ids = [rule["id"] for rule in project["rules"]]
    assert "polymer_paper_project.cantilever-vertical-clip-top" in rule_ids
    assert payload["sources"]["project_rule_catalog"].endswith("authoring-rules-project.md")


def test_context_pack_text_renders_project_conventions(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_context_fixture(workspace)

    result = subprocess.run(
        [str(PLUGIN_ROOT / "bin" / "fig-agent"), "context-pack", "context_demo"],
        cwd=tmp_path,
        env=_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Project Rule Catalog" in result.stdout
    assert "cantilever vertical" in result.stdout.lower()
