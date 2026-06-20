# MCP Envelope Consolidation Design

## Problem

The MCP facade still has several tools that rebuild the same subprocess envelope
by hand: validate workspace/name, run `fig-agent`, handle missing interpreter,
handle timeout, attach bounded stdout/stderr, and parse JSON. This is useful
behavior, but duplicated control flow makes new MCP surfaces easier to drift and
harder to audit.

The goal is not to add another orchestration surface. The goal is to reduce
implementation surface while preserving the current public MCP contracts.

## Non-Goals

- Do not add new MCP tools.
- Do not change public tool names.
- Do not change accepted workspace/fixture path policy.
- Do not make hidden write decisions on behalf of the agent.
- Do not change golden, closeout, or human-gated flows.

## Scope

Consolidate repeated MCP subprocess envelope logic in
`plugins/figure-agent/mcp/figure_agent_server.py`.

Primary targets:

- `figure_agent_compile`
- `figure_agent_export`
- `figure_agent_loop_checkpoint`
- `figure_agent_quality_next_experiment`

Partial target:

- `figure_agent_render_candidates`, only where common subprocess execution can
  be shared without weakening its candidate seed and fixture-lock policy.

Out of scope for this slice:

- `figure_agent_status`, because it adds status-specific artifact enrichment.
- MCP tool schema redesign.
- Full server module split.

## Contract

Existing MCP responses remain stable:

- All tool responses keep `schema`, `success`, `duration_ms`, `artifacts`, and
  `error` envelope behavior.
- Mutating tools keep fixture locking.
- `compile` and `export` keep `stdout`, `stderr`, `exit_code`, and artifact
  fields.
- `export` continues to reject MCP `force_golden`.
- `loop_checkpoint` keeps JSON `checkpoint` when stdout is valid JSON and
  falls back to `{"stdout": ...}` when stdout is non-JSON.
- `quality_next_experiment` remains read-only and falls back to plugin root when
  no workspace `examples/` exists.
- `render_candidates` keeps candidate id/panel validation, seed generation,
  mutation lock, and evaluation flags.

## Design

Add focused helpers inside `figure_agent_server.py`:

- `_run_fig_agent_enveloped(...)`: one place for subprocess execution,
  FileNotFoundError, TimeoutExpired, return code, bounded stdout/stderr, and
  failure envelope generation.
- `_json_payload_from_result(...)`: one place for optional/required JSON parsing
  from successful stdout.
- `_operation_in_progress(...)`: one place for fixture lock conflict envelopes.

Then refactor target tools to compose those helpers rather than rewriting the
same exception and return-code branches.

## Acceptance

- `figure_agent_next_action` remains absent.
- MCP list/startup remains side-effect free.
- Read-only tools remain read-only.
- Candidate render lock behavior remains unchanged.
- `compile/export/loop_checkpoint` still expose the same success/failure shape.
- Tests:
  - `uv run --project plugins/figure-agent pytest -q plugins/figure-agent/tests/test_mcp_facade.py plugins/figure-agent/tests/test_agent_next.py plugins/figure-agent/tests/test_release_contract.py`
  - `uv run --project plugins/figure-agent ruff check plugins/figure-agent/mcp/figure_agent_server.py plugins/figure-agent/tests/test_mcp_facade.py`
  - `git diff --check`
