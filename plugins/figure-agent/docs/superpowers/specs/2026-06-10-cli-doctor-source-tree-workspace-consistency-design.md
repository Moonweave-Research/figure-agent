# CLI Doctor Source-Tree Workspace Consistency Design

## Problem

`fig-agent doctor` and ordinary CLI commands do not report the same workspace
truth when the operator runs from the plugin source tree.

Current behavior:

- `cd plugins/figure-agent && bin/fig-agent doctor --json` reports
  `workspace.state: missing`.
- `cd plugins/figure-agent && bin/fig-agent status smoke_label_overlap_demo --json`
  reads `plugins/figure-agent/examples/smoke_label_overlap_demo` successfully.
- MCP intentionally treats plugin-root `cwd` as missing because `.mcp.json`
  starts the server from the installed plugin root and must not silently treat
  bundled smoke fixtures as user workspaces.

This creates a false negative for direct source-tree CLI use while preserving a
valid MCP safety invariant.

## Goal

Make CLI `fig-agent doctor` report the same workspace that CLI `status`,
`next`, `compile`, and `export` would use, without weakening MCP workspace
separation.

During verification, keep the MCP launch contract aligned with the current
`.mcp.json`: MCP startup is `uv run --project ${CLAUDE_PLUGIN_ROOT} python3
${CLAUDE_PLUGIN_ROOT}/mcp/figure_agent_server.py`. Older docs and tests that
still require bare `python3` are contract drift, not the current runtime truth.

## Non-Goals

- Do not change MCP `figure_agent_doctor` behavior.
- Do not treat an installed plugin cache root as a user workspace for MCP tools.
- Do not add workspace path arguments to MCP tools.
- Do not package manuscript fixtures or generated artifacts.
- Do not alter `status`, `next`, `compile`, or `export` workspace resolution.
- Do not change the `.mcp.json` launch command in this slice; only align docs
  and tests with the existing pinned-`uv` command.

## Design

Add a CLI-specific workspace diagnostic path:

- Keep `runtime_paths.workspace_diagnostics()` unchanged for MCP and strict
  host diagnostics. It continues to use `workspace_root_with_source()` and
  treats plugin-root `cwd` as missing unless `FIGURE_AGENT_WORKSPACE` or
  `CLAUDE_PROJECT_DIR` is set.
- Add `runtime_paths.workspace_diagnostics_for_cli(paths)` that reports
  `paths.workspace_root` and `paths.examples_dir`.
- Use this CLI-specific diagnostic only in `bin/fig-agent doctor`.

This makes the direct CLI report match the direct CLI execution model while
leaving the MCP server's stricter boundary intact.

## Acceptance

- Source-tree direct CLI:
  - `cd plugins/figure-agent`
  - `bin/fig-agent doctor --json`
  - expected: `workspace.state == "ok"` and `workspace.workspace_source == "cwd"`.
- Repo-root direct CLI:
  - `plugins/figure-agent/bin/fig-agent doctor --json`
  - expected: `workspace.state == "missing"` when repo root has no `examples/`.
- MCP doctor:
  - `cwd=plugins/figure-agent`, no `FIGURE_AGENT_WORKSPACE`,
  - expected: `workspace.state == "missing"` and `workspace.workspace_source == "missing"`.
- Explicit workspace:
  - `FIGURE_AGENT_WORKSPACE=<tmp workspace with examples/> fig-agent doctor --json`
  - expected: `workspace.state == "ok"` and source is `FIGURE_AGENT_WORKSPACE`.

## Tests

- Update `tests/test_cowork_runtime_contract.py` for direct CLI doctor behavior.
- Keep `tests/test_mcp_facade.py::test_mcp_doctor_reports_plugin_cwd_as_workspace_missing`
  unchanged to guard MCP safety.
- Update `.mcp.json` contract docs/tests only where they still describe the old
  bare-`python3` launch path.
- Run:
  - `uv run --project plugins/figure-agent pytest -q plugins/figure-agent/tests/test_cowork_runtime_contract.py plugins/figure-agent/tests/test_mcp_facade.py`
  - `uv run --project plugins/figure-agent ruff check plugins/figure-agent/bin/fig-agent plugins/figure-agent/scripts/runtime_paths.py plugins/figure-agent/tests/test_cowork_runtime_contract.py plugins/figure-agent/tests/test_mcp_facade.py`
  - `git diff --check`

## Self-Review

- Placeholder scan: no placeholder requirements remain.
- Consistency: CLI direct use and MCP host use are intentionally different and
  tested separately.
- Scope: one runtime diagnostic helper plus tests; no unrelated package or MCP
  surface changes.
