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
    assert payload["rule_catalog"]["promotion_state"] == "n1_hypotheses"
    assert "briefing" in payload["paper_context"]


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
