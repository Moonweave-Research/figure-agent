# CLI Doctor Source-Tree Workspace Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `fig-agent doctor` report the same workspace root that direct CLI commands use when run from the plugin source tree, while preserving MCP's stricter plugin-root workspace rejection.

**Architecture:** Add a CLI-only workspace diagnostic helper in `runtime_paths.py` and call it from `bin/fig-agent doctor`. Leave the existing `workspace_diagnostics()` path in place for MCP and strict host diagnostics.

**Tech Stack:** Python stdlib, pytest, ruff.

---

### Task 1: Pin CLI And MCP Doctor Boundary Tests

**Files:**
- Modify: `plugins/figure-agent/tests/test_cowork_runtime_contract.py`
- Read-only guard: `plugins/figure-agent/tests/test_mcp_facade.py`

- [ ] **Step 1: Update source-tree CLI doctor regression**

Change `test_doctor_reports_plugin_root_cwd_as_missing_workspace` so it expects
direct CLI doctor to accept source-tree `cwd` as the workspace:

```python
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
```

- [ ] **Step 2: Verify RED**

Run:

```bash
uv run --project plugins/figure-agent pytest -q plugins/figure-agent/tests/test_cowork_runtime_contract.py::test_doctor_reports_plugin_root_cwd_as_source_tree_workspace
```

Expected: FAIL because doctor currently reports missing.

### Task 2: Add CLI Workspace Diagnostics

**Files:**
- Modify: `plugins/figure-agent/scripts/runtime_paths.py`
- Modify: `plugins/figure-agent/bin/fig-agent`
- Modify: `plugins/figure-agent/tests/test_mcp_facade.py`
- Modify: `plugins/figure-agent/docs/mcp-facade-design.md`

- [ ] **Step 1: Add helper**

Add this helper beside `workspace_diagnostics()`:

```python
def workspace_diagnostics_for_cli(paths: RuntimePaths) -> dict:
    examples_dir = paths.examples_dir
    missing = []
    if not examples_dir.is_dir():
        missing.append("examples")
    return {
        "state": "ok" if not missing else "missing",
        "workspace_root": str(paths.workspace_root),
        "workspace_source": workspace_source_for_cli(paths),
        "missing": missing,
    }
```

Add:

```python
def workspace_source_for_cli(paths: RuntimePaths) -> str:
    if os.environ.get("FIGURE_AGENT_WORKSPACE"):
        return "FIGURE_AGENT_WORKSPACE"
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        return "CLAUDE_PROJECT_DIR"
    return "cwd"
```

- [ ] **Step 2: Use helper in `fig-agent doctor`**

Change:

```python
"workspace": runtime_paths.workspace_diagnostics(paths),
```

to:

```python
"workspace": runtime_paths.workspace_diagnostics_for_cli(paths),
```

- [ ] **Step 3: Align MCP launch contract docs/tests**

If the broader verification suite fails because `.mcp.json` now launches with
`uv run --project ${CLAUDE_PLUGIN_ROOT}`, update only the stale assertion and
design prose:

```python
assert server["command"] == "uv"
assert server["args"][:4] == ["run", "--project", "${CLAUDE_PLUGIN_ROOT}", "python3"]
```

The MCP doctor plugin-root workspace rejection test must remain unchanged.

### Task 3: Verify And Commit

**Files:**
- Create: `plugins/figure-agent/docs/superpowers/specs/2026-06-10-cli-doctor-source-tree-workspace-consistency-design.md`
- Create: `plugins/figure-agent/docs/superpowers/plans/2026-06-10-cli-doctor-source-tree-workspace-consistency.md`
- Modify: `plugins/figure-agent/scripts/runtime_paths.py`
- Modify: `plugins/figure-agent/bin/fig-agent`
- Modify: `plugins/figure-agent/tests/test_cowork_runtime_contract.py`
- Modify: `plugins/figure-agent/tests/test_mcp_facade.py`
- Modify: `plugins/figure-agent/docs/mcp-facade-design.md`

- [ ] **Step 1: Run targeted verification**

```bash
uv run --project plugins/figure-agent pytest -q plugins/figure-agent/tests/test_cowork_runtime_contract.py plugins/figure-agent/tests/test_mcp_facade.py
uv run --project plugins/figure-agent ruff check plugins/figure-agent/bin/fig-agent plugins/figure-agent/scripts/runtime_paths.py plugins/figure-agent/tests/test_cowork_runtime_contract.py plugins/figure-agent/tests/test_mcp_facade.py
git diff --check
```

Expected: PASS.

- [ ] **Step 2: Commit only this slice**

```bash
git add plugins/figure-agent/docs/superpowers/specs/2026-06-10-cli-doctor-source-tree-workspace-consistency-design.md plugins/figure-agent/docs/superpowers/plans/2026-06-10-cli-doctor-source-tree-workspace-consistency.md plugins/figure-agent/scripts/runtime_paths.py plugins/figure-agent/bin/fig-agent plugins/figure-agent/tests/test_cowork_runtime_contract.py plugins/figure-agent/tests/test_mcp_facade.py plugins/figure-agent/docs/mcp-facade-design.md
git commit -m "Align CLI doctor source-tree workspace diagnostics"
```

Do not stage manuscript caption edits or generated `dist/` ZIPs.

## Self-Review

- Spec coverage: direct CLI, repo-root CLI, MCP doctor, explicit workspace, and
  test commands are covered.
- Placeholder scan: no TBD/TODO/fill-in-later instructions remain.
- Type consistency: helper names and payload keys match existing runtime path
  style.
