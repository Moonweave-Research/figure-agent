# MCP Envelope Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce duplicated MCP subprocess envelope code without changing the public MCP tool contract.

**Architecture:** Keep the single-file MCP facade for this slice, but centralize repeated subprocess, timeout, return-code, JSON, and lock-conflict envelope branches behind small local helpers. Refactor only tools whose behavior can be preserved exactly.

**Tech Stack:** Python 3, stdlib subprocess/json/pathlib, pytest, ruff.

---

### Task 1: Add Regression Tests For Envelope-Sensitive Behavior

**Files:**
- Modify: `plugins/figure-agent/tests/test_mcp_facade.py`

- [ ] **Step 1: Add tests that pin legacy behavior**

Add tests that call existing MCP tools through the JSON-RPC harness:

```python
def test_mcp_export_rejects_force_golden_before_running_cli(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    _write_minimal_fixture(workspace, name="export_demo")

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_export",
                    "arguments": {"name": "export_demo", "force_golden": True},
                },
                request_id=1,
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    assert payload["schema"] == "figure-agent.mcp.export.v1"
    assert payload["success"] is False
    assert payload["error"]["category"] == "unsupported_operation"
    assert payload["error"]["message"] == "force_golden_requires_cli_closeout_accept"
    assert "stdout" not in payload
```

```python
def test_mcp_compile_reports_operation_in_progress(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    fixture = _write_minimal_fixture(workspace, name="compile_demo")
    lock_root = fixture / "build" / ".mcp-locks"
    lock_root.mkdir(parents=True)
    (lock_root / "mutation.lock").write_text(
        json.dumps({"operation": "export"}),
        encoding="utf-8",
    )

    result = _run_mcp_server(
        [
            _mcp_request(
                "tools/call",
                {
                    "name": "figure_agent_compile",
                    "arguments": {"name": "compile_demo"},
                },
                request_id=1,
            )
        ],
        cwd=tmp_path,
        env={"FIGURE_AGENT_WORKSPACE": str(workspace)},
    )

    payload = _tool_payload(_response_lines(result)[0])
    assert payload["schema"] == "figure-agent.mcp.compile.v1"
    assert payload["success"] is False
    assert payload["error"]["category"] == "operation_in_progress"
    assert payload["operation"] == "export"
```

- [ ] **Step 2: Run tests before refactor**

Run:

```bash
uv run --project plugins/figure-agent pytest -q plugins/figure-agent/tests/test_mcp_facade.py
```

Expected: PASS.

### Task 2: Extract Shared MCP Envelope Helpers

**Files:**
- Modify: `plugins/figure-agent/mcp/figure_agent_server.py`

- [ ] **Step 1: Add helper functions near `_run_json_fig_agent_tool`**

Add `_operation_in_progress`, `_run_fig_agent_enveloped`, and
`_json_payload_from_result`.

```python
def _operation_in_progress(
    *,
    schema: str,
    started: float,
    name: str,
    lock: dict[str, Any],
) -> dict[str, Any]:
    ...


def _run_fig_agent_enveloped(
    *,
    schema: str,
    started: float,
    command: list[str],
    workspace_root: Path,
    timeout_seconds: int,
    timeout_message: str,
    name: str | None = None,
) -> subprocess.CompletedProcess[str] | dict[str, Any]:
    ...


def _json_payload_from_result(
    *,
    result: subprocess.CompletedProcess[str],
    schema: str,
    started: float,
    invalid_json_message: str,
    name: str | None = None,
    required: bool = True,
) -> tuple[Any, dict[str, Any] | None]:
    ...
```

- [ ] **Step 2: Refactor compile/export/loop checkpoint**

Refactor `_compile`, `_export`, and `_loop_checkpoint` to use shared helpers
while preserving fixture locking and public payload fields.

The refactor must preserve these branches exactly:

```python
if isinstance(result, dict):
    return result
success = result.returncode == 0
```

`_compile` keeps `compile_failed`; `_export` keeps `export_failed`;
`_loop_checkpoint` keeps optional JSON parsing with non-JSON stdout fallback.

- [ ] **Step 3: Refactor quality next experiment**

Refactor `_quality_next_experiment` to use shared subprocess and JSON parsing
helpers while preserving plugin-root fallback.

```python
workspace_root = _workspace_root(plugin_root)
if workspace_root is None or not _examples_dir(workspace_root).is_dir():
    workspace_root = plugin_root
```

- [ ] **Step 4: Refactor render candidates only for safe shared branches**

Keep validation, seed generation, command assembly, and lock behavior local.
Use shared helpers only for operation-in-progress envelope and final
return-code/JSON branches if that preserves identical output.

The default candidate-set seed must still run before render:

```python
if candidate_set == "build/candidates/candidate_set.json":
    seed = _run_fig_agent_enveloped(...)
    if isinstance(seed, dict):
        return seed
    if seed.returncode != 0:
        return _tool_envelope(..., error=_error("unsupported_operation", "fig-agent candidates failed"))
```

### Task 3: Verify And Commit

**Files:**
- Modify: `plugins/figure-agent/mcp/figure_agent_server.py`
- Modify: `plugins/figure-agent/tests/test_mcp_facade.py`
- Create: `plugins/figure-agent/docs/superpowers/specs/2026-06-09-mcp-envelope-consolidation-design.md`
- Create: `plugins/figure-agent/docs/superpowers/plans/2026-06-09-mcp-envelope-consolidation.md`

- [ ] **Step 1: Run targeted tests**

```bash
uv run --project plugins/figure-agent pytest -q plugins/figure-agent/tests/test_mcp_facade.py plugins/figure-agent/tests/test_agent_next.py plugins/figure-agent/tests/test_release_contract.py
```

Expected: PASS.

- [ ] **Step 2: Run style checks**

```bash
uv run --project plugins/figure-agent ruff check plugins/figure-agent/mcp/figure_agent_server.py plugins/figure-agent/tests/test_mcp_facade.py
git diff --check
```

Expected: PASS.

- [ ] **Step 3: Commit only this slice**

```bash
git add plugins/figure-agent/mcp/figure_agent_server.py plugins/figure-agent/tests/test_mcp_facade.py plugins/figure-agent/docs/superpowers/specs/2026-06-09-mcp-envelope-consolidation-design.md plugins/figure-agent/docs/superpowers/plans/2026-06-09-mcp-envelope-consolidation.md
git commit -m "Consolidate MCP subprocess envelopes"
```

Do not stage manuscript fixture edits or generated ZIP artifacts.

## Self-Review

- Spec coverage: The plan covers public contract preservation, duplicated
  subprocess envelopes, lock conflict behavior, and read-only tool behavior.
- Placeholder scan: No TBD/TODO/fill-in-later placeholders remain.
- Type consistency: Helper names and test function names are consistent with
  the current Python module naming style.
