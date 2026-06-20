# Agent-Native Next Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `fig-agent next <name> --json` and an MCP facade tool that return one read-only, schema-stable next action using the existing status and next-action policy modules.

**Architecture:** Create a focused `agent_next.py` module that calls `status.infer_stage()` and reuses the existing `next_action_summary` already attached by status. Wire it into `bin/fig-agent` as `next`, then expose the same CLI response through the MCP facade as `figure_agent_next`. The command is read-only and returns the standard fields `schema`, `success`, `state`, `name`, `diagnostics`, `writes`, `next`, `alternatives`, and `duration_ms`.

**Tech Stack:** Python stdlib, existing `runtime_paths.py`, `status.py`, `next_action_summary.py`, `quality_next_experiment.py`, `fig-agent` CLI wrapper, MCP JSON-RPC tests, pytest, ruff.

---

### Task 1: Agent Next Core and CLI

**Files:**
- Create: `plugins/figure-agent/scripts/agent_next.py`
- Modify: `plugins/figure-agent/bin/fig-agent`
- Test: `plugins/figure-agent/tests/test_agent_next.py`

- [ ] **Step 1: Write the failing tests**

Create `plugins/figure-agent/tests/test_agent_next.py`:

```python
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

    payload = agent_next.build_next("missing_demo", plugin_root=PLUGIN_ROOT, workspace_root=workspace)

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
    assert payload["next"]["command"]
    assert _tree(workspace) == before
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_agent_next.py
```

Expected: FAIL because `agent_next.py` and `fig-agent next` do not exist yet.

- [ ] **Step 3: Implement `agent_next.py`**

Create `plugins/figure-agent/scripts/agent_next.py` with:

```python
"""Read-only state-router for the next safe figure-agent action."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import fixture_identity
import quality_next_experiment
import runtime_paths
import status

SCHEMA = "figure-agent.next.v1"


def _diagnostic(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _command_writes(command: str | None) -> bool:
    if not command:
        return False
    return any(token in command for token in (" --write", " --apply", " --accept"))


def _state(summary: dict[str, Any]) -> str:
    if summary.get("requires_human") is True:
        return "human_required"
    boundary = summary.get("decision_boundary")
    if isinstance(boundary, dict) and boundary.get("blocks_progress") is False:
        return "ready"
    return "blocked"


def _safe_command(summary: dict[str, Any]) -> str | None:
    command = summary.get("safe_command")
    return command if isinstance(command, str) and command else None


def _next_payload(summary: dict[str, Any]) -> dict[str, Any]:
    command = _safe_command(summary)
    return {
        "command": command,
        "reason": str(summary.get("reason") or "inspect figure status"),
        "action": str(summary.get("action") or "inspect_status"),
        "requires_human": summary.get("requires_human") is True,
        "writes": _command_writes(command),
    }


def _alternatives(name: str, *, plugin_root: Path, workspace_root: Path) -> list[dict[str, Any]]:
    experiment = quality_next_experiment.build_next_experiment(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    recommendation = experiment.get("recommendation")
    benchmark_command = None
    if isinstance(recommendation, dict) and recommendation.get("allowed") is True:
        command = recommendation.get("command")
        benchmark_command = command if isinstance(command, str) else None
    alternatives = [
        {
            "command": f"fig-agent status {name} --json",
            "reason": "Inspect the full status vector before taking action.",
            "writes": False,
        }
    ]
    if benchmark_command:
        alternatives.append(
            {
                "command": benchmark_command,
                "reason": "Run the read-only smoke benchmark preview.",
                "writes": False,
            }
        )
    return alternatives


def build_next(
    name: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    fixture_identity.validate_fixture_name(name)
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    example_dir = paths.examples_dir / name
    if not example_dir.is_dir():
        return {
            "schema": SCHEMA,
            "success": False,
            "state": "missing_fixture",
            "name": name,
            "diagnostics": [
                _diagnostic("fixture_missing", f"examples/{name} does not exist.")
            ],
            "writes": [],
            "next": {
                "command": None,
                "reason": "Create or select an existing fixture under examples/.",
                "action": "create_or_select_fixture",
                "requires_human": False,
                "writes": False,
            },
            "alternatives": [],
            "duration_ms": int((time.monotonic() - started) * 1000),
        }
    status_payload = status.infer_stage(example_dir)
    summary = status_payload.get("next_action_summary")
    if not isinstance(summary, dict):
        summary = status.status_next_action_summary(status_payload)
    return {
        "schema": SCHEMA,
        "success": True,
        "state": _state(summary),
        "name": name,
        "diagnostics": [],
        "writes": [],
        "status": summary,
        "next": _next_payload(summary),
        "alternatives": _alternatives(
            name,
            plugin_root=paths.plugin_root,
            workspace_root=paths.workspace_root,
        ),
        "duration_ms": int((time.monotonic() - started) * 1000),
    }
```

- [ ] **Step 4: Wire `bin/fig-agent`**

Add `_next(argv)` to import `agent_next`, parse `name` and `--json`, call
`agent_next.build_next()`, print JSON, and dispatch `command == "next"`.

- [ ] **Step 5: Run tests and commit**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_agent_next.py
uv run ruff check plugins/figure-agent/scripts/agent_next.py plugins/figure-agent/bin/fig-agent plugins/figure-agent/tests/test_agent_next.py
```

Commit:

```bash
git add plugins/figure-agent/scripts/agent_next.py plugins/figure-agent/bin/fig-agent plugins/figure-agent/tests/test_agent_next.py
git commit -m "Add agent-native next command"
```

### Task 2: MCP Facade for Next

**Files:**
- Modify: `plugins/figure-agent/mcp/figure_agent_server.py`
- Test: `plugins/figure-agent/tests/test_mcp_facade.py`

- [ ] **Step 1: Write failing MCP tests**

Add tests to `plugins/figure-agent/tests/test_mcp_facade.py` that assert
`figure_agent_next` is listed, has required `name`, and returns a read-only
`figure-agent.mcp.next.v1` envelope with nested `next_result.schema ==
"figure-agent.next.v1"` and `writes == []`.

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_mcp_facade.py -k "next"
```

Expected: FAIL because `figure_agent_next` is not registered.

- [ ] **Step 3: Implement MCP handler**

Add `_next(arguments)` that calls `_run_json_fig_agent_tool()` with:

```python
schema="figure-agent.mcp.next.v1"
command=["next", name, "--json"]
payload_key="next_result"
failure_message="fig-agent next failed"
```

Register the tool in `TOOLS` with a read-only description and required `name`.

- [ ] **Step 4: Run tests and commit**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_mcp_facade.py -k "next"
uv run ruff check plugins/figure-agent/mcp/figure_agent_server.py plugins/figure-agent/tests/test_mcp_facade.py
```

Commit:

```bash
git add plugins/figure-agent/mcp/figure_agent_server.py plugins/figure-agent/tests/test_mcp_facade.py
git commit -m "Expose next command through MCP"
```

### Task 3: Contract Docs and Release Gate

**Files:**
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md`
- Modify: `plugins/figure-agent/tests/test_release_contract.py`
- Modify: `plugins/figure-agent/scripts/release_gate.py`

- [ ] **Step 1: Add contract checks**

Add schema map coverage for `figure-agent.next.v1`, include
`tests/test_agent_next.py` in `TARGETED_TESTS`, and add a release-contract test
that the schema map mentions `agent_next.py`.

- [ ] **Step 2: Run contract tests**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_agent_next.py \
  plugins/figure-agent/tests/test_mcp_facade.py -k "next" \
  plugins/figure-agent/tests/test_release_contract.py
```

- [ ] **Step 3: Final verification and commit**

Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_agent_next.py \
  plugins/figure-agent/tests/test_mcp_facade.py \
  plugins/figure-agent/tests/test_release_contract.py \
  plugins/figure-agent/tests/test_quality_next_experiment.py \
  plugins/figure-agent/tests/test_next_action_summary.py
uv run ruff check plugins/figure-agent/scripts/agent_next.py \
  plugins/figure-agent/bin/fig-agent \
  plugins/figure-agent/mcp/figure_agent_server.py \
  plugins/figure-agent/tests/test_agent_next.py \
  plugins/figure-agent/tests/test_mcp_facade.py \
  plugins/figure-agent/tests/test_release_contract.py
plugins/figure-agent/bin/fig-agent next smoke_label_overlap_demo --json
```

Commit:

```bash
git add plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md \
  plugins/figure-agent/tests/test_release_contract.py \
  plugins/figure-agent/scripts/release_gate.py
git commit -m "Register next workflow release contract"
```

## Self-Review

- Spec coverage: covers `fig-agent next`, read-only writes, existing policy reuse,
  MCP facade, schema docs, and focused tests.
- Scope: one vertical slice only; envelope normalization for all commands and
  dogfood promotion remain later slices.
- Ambiguity: `next` is explicitly a wrapper over existing status/next modules,
  not a new routing policy.
