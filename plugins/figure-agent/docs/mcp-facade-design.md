# figure-agent MCP Facade Design

Status: draft approved for planning
Date: 2026-06-07
Target: figure-agent 0.10.x after the 0.9.3 Cowork plugin package

## Current State

figure-agent is currently a Claude/Cowork plugin with a stable CLI core:

- `bin/fig-agent` is the public entrypoint.
- `scripts/runtime_paths.py` separates installed plugin resources from the user workspace.
- Plugin resources live under the installed plugin root: `scripts/`, `styles/`, `commands/`, `skills/`.
- User figures live under the workspace root: `examples/<name>/`.
- Cowork ZIP packaging is deterministic and excludes manuscript fixtures, generated artifacts, caches, and development-only docs.
- The Cowork smoke path has passed in a real installed environment: doctor, compile, checkers, perception pack, export, status, and loop checkpoint.

There is no MCP server yet. The only supported machine interface is command execution through `fig-agent` and JSON-emitting helper scripts.

## External Contract Baseline

The design follows the current Claude Code plugin and MCP documentation:

- Claude plugins can bundle MCP servers through `.mcp.json` at the plugin root
  or inline `plugin.json` `mcpServers`.
- Plugin MCP servers start automatically when the plugin is enabled.
- `${CLAUDE_PLUGIN_ROOT}` is substituted in MCP configs and exported to MCP
  subprocesses.
- `bin/` executables are added to the Bash tool `PATH` while the plugin is enabled,
  but MCP configs should still use explicit `${CLAUDE_PLUGIN_ROOT}` paths for
  reproducibility.
- MCP remains an active protocol. The first implementation should avoid relying on
  draft-only features unless the target Claude/Cowork runtime is verified.

Reference pages checked for this design:

- <https://code.claude.com/docs/en/plugins>
- <https://code.claude.com/docs/en/plugins-reference>
- <https://code.claude.com/docs/en/mcp>
- <https://modelcontextprotocol.info/specification/>

## Goal

Add a thin MCP facade that makes figure-agent easier for Claude/Cowork agents to use without replacing the CLI core.

The facade should improve figure quality by giving the host agent structured access to:

- current figure state,
- next recommended action,
- compile/export results,
- audit findings,
- render and crop artifact paths,
- bounded loop and closeout evidence.

The MCP layer should reduce command-string interpretation and file-path guessing. It should not become a second workflow engine.

## Non-goals

- Do not rewrite compile, status, export, or loop logic for MCP.
- Do not add a learned aesthetic judge to the core.
- Do not call external vision, image-generation, or paper-search APIs.
- Do not mutate user source files through MCP in the first release.
- Do allow explicit generated-artifact mutation for existing operations such as
  compile, export, and loop checkpoint creation.
- Do not package user manuscript fixtures inside the plugin or MCP server.
- Do not make MCP required for CLI/Cowork ZIP operation.

## Architecture

Use a three-layer design:

1. **CLI Core**
   Existing Python scripts and `fig-agent` remain the source of truth for behavior.

2. **MCP Facade**
   A small server exposes typed tools and resources. It invokes existing Python module functions where stable, and falls back to `fig-agent` subprocess calls where that is safer.

3. **Host Agent**
   Claude/Cowork calls MCP tools for state and artifact discovery, then performs host-only visual critique by reading returned artifacts. Human approval gates remain explicit.

```text
Claude/Cowork
  -> MCP tool/resource call
    -> figure-agent MCP facade
      -> runtime_paths.resolve_runtime_paths()
      -> existing fig-agent scripts/modules
      -> workspace examples/<name>/ artifacts
```

The MCP server must use the same root contract as the CLI:

- `FIGURE_AGENT_PLUGIN_ROOT` or `CLAUDE_PLUGIN_ROOT` for plugin resources.
- `FIGURE_AGENT_WORKSPACE` or `CLAUDE_PROJECT_DIR` for user figures.
- current working directory only as a final workspace fallback when it is not the
  plugin root.
- client-provided fixture names are resolved only under `workspace_root/examples`.

The MCP server should not accept a workspace path argument in ordinary tool calls.
Workspace selection is host/runtime configuration, not model-generated input.
Because `.mcp.json` sets `cwd` to the plugin root, MCP code must not treat that
`cwd` as a valid user workspace. If neither `FIGURE_AGENT_WORKSPACE` nor
`CLAUDE_PROJECT_DIR` is available, `figure_agent_doctor` should report
`workspace_missing` even if the plugin bundle contains smoke fixtures under its
own `examples/` directory.

## Startup and Side Effects

Plugin MCP servers can be started automatically by the host. Server startup,
tool listing, and resource listing must therefore be fast and side-effect-free.

On startup the MCP server may:

- import lightweight modules,
- resolve plugin root,
- register tool and resource schemas,
- defer workspace validation until a tool/resource call.

On startup the MCP server must not:

- run TeX, export, checkers, package audits, or visual extraction,
- deeply scan every workspace fixture,
- create `build/`, `exports/`, `.scratch/`, cache, or log files,
- rewrite plugin metadata or workspace files,
- fail the whole MCP server only because the current host project lacks
  `examples/`.

Workspace and dependency problems should surface through `figure_agent_doctor`
or the relevant tool response, not as noisy MCP startup failures.

## Packaging Model

The MCP facade should be packaged inside the existing plugin bundle, not as a separate project.

Recommended files:

- `.mcp.json`
- `mcp/figure_agent_server.py`
- tests under `tests/test_mcp_*.py`
- package builder updates only after the server contract is covered by tests

Recommended `.mcp.json` shape:

```json
{
  "mcpServers": {
    "figure-agent": {
      "command": "python3",
      "args": [
        "${CLAUDE_PLUGIN_ROOT}/mcp/figure_agent_server.py"
      ],
      "cwd": "${CLAUDE_PLUGIN_ROOT}",
      "env": {
        "FIGURE_AGENT_PLUGIN_ROOT": "${CLAUDE_PLUGIN_ROOT}"
      }
    }
  }
}
```

This keeps server bootstrap independent from `uv` and project Python packages.
If `.mcp.json` uses `uv` to start the MCP server, then a missing `uv` binary
becomes an MCP startup failure and `figure_agent_doctor` cannot report it as a
structured `dependency_missing` result. The server process should therefore be a
dependency-light stdio wrapper that can start with only host `python3` and the
Python standard library.
Tool subprocesses should invoke `${CLAUDE_PLUGIN_ROOT}/bin/fig-agent` through
the running Python interpreter rather than `uv run --project`, so normal MCP
tool calls do not create virtualenv state inside the installed plugin cache.

The server must still resolve the workspace through `FIGURE_AGENT_WORKSPACE`,
`CLAUDE_PROJECT_DIR`, or a non-plugin-root current working directory.
The `.mcp.json` file should not hard-code `FIGURE_AGENT_WORKSPACE`; a package
uploaded to Cowork must be reusable across projects.

If the implementation chooses the official Python MCP SDK or another package,
that is a new runtime dependency and must be approved explicitly before landing.
The first implementation should try to keep dependencies inside the existing
`pyproject.toml` unless SDK support is required for compatibility.

If an SDK is required and prevents dependency-light startup, the design must
explicitly downgrade the MCP doctor promise: `python3` or SDK import failures
would be host MCP startup errors, while `figure_agent_doctor` would only cover
dependencies reachable after the server starts.

The Cowork ZIP builder must include `.mcp.json` and `mcp/` only after they are
validated. The package audit must continue to reject generated artifacts,
manuscript fixtures, virtualenvs, caches, and local install backups.

## Tool Surface

Phase 1 should expose read-mostly tools plus existing safe workflow steps.
Tool names are prefixed with `figure_agent_` to reduce collisions with other MCP
servers.

The MCP facade must not accidentally expand the public shell contract. If a tool
uses an existing internal `fig-agent` subcommand, that command remains an
implementation detail unless it is also documented as a supported public CLI
command. Operator-facing `safe_command` strings should only reference public
commands.

Every tool response should use a common envelope:

- `schema`: stable schema name with a version suffix.
- `success`: boolean result.
- `error`: structured error object when `success` is false.
- `artifacts`: zero or more resource descriptors, never unbounded raw file
  contents.
- `duration_ms`: best-effort elapsed time for observability.

Schema version bumps are required for backward-incompatible output changes.
Adding optional fields is allowed within the same version.

MCP prompts are out of scope for Phase 1. Existing plugin commands and skills
remain the prompt layer; the MCP facade only exposes tools and resources.

### `figure_agent_doctor`

Input:

```json
{}
```

Output:

```json
{
  "schema": "figure-agent.mcp.doctor.v1",
  "success": true,
  "bundle": {},
  "workspace": {},
  "dependencies": {}
}
```

Purpose:

- Verify bundle, workspace, and host dependencies.
- Mirror `fig-agent doctor --json`.
- Do not create files.

### `figure_agent_status`

Input:

```json
{
  "name": "smoke_trap_demo"
}
```

Output:

```json
{
  "schema": "figure-agent.mcp.status.v1",
  "name": "smoke_trap_demo",
  "status": {},
  "artifacts": []
}
```

Purpose:

- Return the current status vector for one fixture.
- Include normalized artifact paths for build, export, audit crop, and perception outputs when present.
- Do not infer visual quality from artifact existence.

### `figure_agent_compile`

Input:

```json
{
  "name": "smoke_trap_demo",
  "strict": false
}
```

Output:

```json
{
  "schema": "figure-agent.mcp.compile.v1",
  "success": true,
  "exit_code": 0,
  "artifacts": [],
  "warnings": []
}
```

Purpose:

- Run the existing compile chain.
- Return structured artifact paths and checker summaries.
- Preserve current report-only default for collision/clash checks.
- Write only generated build/audit/perception artifacts under `examples/<name>/build`.
- Never edit `<name>.tex`, `spec.yaml`, `briefing.md`, `critique.md`, or source files.

### `figure_agent_export`

Input:

```json
{
  "name": "smoke_trap_demo",
  "force_golden": false,
  "skip_critique": false
}
```

Output:

```json
{
  "schema": "figure-agent.mcp.export.v1",
  "success": true,
  "exit_code": 0,
  "export_state_before": "MISSING",
  "artifacts": []
}
```

Purpose:

- Run the existing export policy.
- Preserve critique freshness gates and tracked-golden protection.
- Write only generated export artifacts under `examples/<name>/exports`.

### `figure_agent_next_action`

Input:

```json
{
  "name": "smoke_trap_demo",
  "mode": "review",
  "goal": "resolve the next safe critique target"
}
```

Output:

```json
{
  "schema": "figure-agent.mcp.next-action.v1",
  "action": "run_loop_checkpoint",
  "stop_boundary": null,
  "safe_command": null,
  "mcp_tool": {
    "name": "figure_agent_loop_checkpoint",
    "arguments": {
      "name": "smoke_trap_demo",
      "goal": "resolve the next safe critique target"
    }
  },
  "requires_human": false,
  "requires_host_vision": false
}
```

Purpose:

- Wrap the existing driver summary.
- Keep `safe_command` for auditability, but make structured fields primary.
- Convert non-public internal commands into structured MCP tool recommendations
  instead of exposing them as operator shell commands.

### `figure_agent_loop_checkpoint`

Input:

```json
{
  "name": "smoke_trap_demo",
  "goal": "contract matrix"
}
```

Output:

```json
{
  "schema": "figure-agent.mcp.loop-checkpoint.v1",
  "success": true,
  "run_dir": ".scratch/fig-loop-runs/...",
  "final_stop_reason": "status_action_required",
  "recommended_next_action": "..."
}
```

Purpose:

- Record the same verify-only loop checkpoint as `fig-agent loop`.
- The public MCP contract is this tool; the underlying shell command may remain
  internal.
- No source edits.

## Resource Surface

Phase 1 resources should be file references, not binary streaming, unless the host MCP runtime clearly supports image payloads.

Recommended Phase 1 resource templates:

- `figure://<name>/build/png`
- `figure://<name>/build/pdf`
- `figure://<name>/exports/svg`
- `figure://<name>/exports/png`
- `figure://<name>/audit/visual-clash`
- `figure://<name>/audit/text-boundary`
- `figure://<name>/audit/label-path`
- `figure://<name>/perception/extract`

These patterns should be exposed through MCP resource templates, not as literal
`resources/list` entries with `{name}` embedded in the URI. `resources/list`
should return only concrete fixture resources when the server has a specific
fixture context.

Each concrete resource response should include:

- workspace-relative path,
- stable `figure://...` URI,
- existence state,
- freshness state when available,
- media type when known.

`read_resource` should return small JSON metadata in Phase 1. It should not
stream PDF, PNG, SVG, TIFF, or TeX bytes until the host runtime's binary/image
resource behavior is verified against Claude and Cowork.

Absolute paths may be included only in local CLI/debug fields. Stable MCP result
contracts should prefer workspace-relative paths and resource URIs so outputs do
not depend on one developer's home directory.

The host agent remains responsible for visually reading PNG/PDF/crop artifacts before writing critique.

## Error Model

MCP tools should avoid raw tracebacks in normal failure modes.

Use stable error categories:

- `bundle_missing`
- `workspace_missing`
- `dependency_missing`
- `doctor_failed`
- `export_failed`
- `fixture_missing`
- `invalid_fixture_name`
- `invalid_request`
- `compile_failed`
- `critique_required`
- `reference_input_missing`
- `tracked_golden_protected`
- `human_gate_required`
- `operation_in_progress`
- `status_failed`
- `timeout`
- `unsupported_operation`

Each failure should return:

```json
{
  "success": false,
  "error": {
    "category": "fixture_missing",
    "message": "examples/demo not found",
    "next_action": "Create examples/demo or choose an existing fixture."
  }
}
```

Tool process failures may include bounded stdout/stderr excerpts, but not unlimited logs.

## Concurrency and Timeouts

Read-only calls may run concurrently. Mutating calls must serialize per fixture:

- `figure_agent_compile`
- `figure_agent_export`
- `figure_agent_loop_checkpoint`

If a mutating operation is already running for `examples/<name>`, the next
mutating call should return `operation_in_progress` with the active operation
name and a suggested retry. The lock must live under generated state, not beside
source files, and stale-lock recovery must be conservative.

Every subprocess-backed operation needs an explicit timeout. Timeout failures
must return `timeout` with bounded output excerpts and must not be reported as
successful partial builds.

Because MCP uses stdout for protocol messages, the server itself must not print
diagnostics, warnings, progress logs, or captured subprocess output to stdout.
All non-protocol diagnostics must go to stderr or be returned inside structured
tool responses.

## Security and Workspace Boundaries

The MCP server must preserve the same safety rules as `fig-agent`:

- Validate fixture names before joining paths.
- Never resolve bare fixture names outside `workspace_root/examples`.
- Never read/write generated package paths as user fixture state.
- Never package or upload manuscript fixtures by default.
- Never run arbitrary helper scripts by path.
- Keep mutating tools explicit and named.
- Treat every path coming from a tool argument as untrusted.
- Keep stdout/stderr excerpts bounded so TeX logs cannot flood context.
- Do not expose a tool that returns raw environment variables.
- Do not expose host-provided project paths unless they are needed for local
  debugging output.

The first MCP release should not expose a general shell runner.

## Better Figure Quality Path

MCP improves drawing quality only if it improves the evidence loop. The highest-impact quality features are:

1. structured artifact discovery,
2. structured detector findings,
3. audit crop resources,
4. next-action routing,
5. bounded patch handoff.

The first implementation should prioritize artifact and finding visibility over automatic editing.

## Rollout Plan

### Phase 0: Contract Freeze

- Keep CLI behavior unchanged.
- Document MCP as optional.
- Add tests that CLI still passes without MCP.

### Phase 1: Thin Read/Run Facade

- Add `figure_agent_doctor`.
- Add `figure_agent_status`.
- Add `figure_agent_compile`.
- Add `figure_agent_export`.
- Add `figure_agent_next_action`.
- Add `figure_agent_loop_checkpoint`.

Acceptance:

- Existing full pytest suite passes.
- MCP tools pass against a temp workspace.
- `.mcp.json` uses `${CLAUDE_PLUGIN_ROOT}` and starts the server without `uv`.
- MCP startup, tool listing, and resource listing create no files.
- Mutating calls have per-fixture serialization and timeout coverage.
- Cowork ZIP still validates and excludes user fixtures.

### Phase 2: Artifact Resources

- Add resource listing for build/export/audit/perception artifacts.
- Return deterministic media metadata.
- Add tests with `smoke_trap_demo`.

Acceptance:

- Host agent can discover the correct PNG/PDF/crop paths without guessing.
- Missing artifacts produce structured missing states, not exceptions.

### Phase 3: Bounded Patch Assistance

- Add a patch-validation tool only after loop handoff is stable.
- Accept unified diffs or existing `fig_loop_patch_executor.py` inputs.
- Require exactly one target.
- Preserve human gates.

Acceptance:

- No broad edits.
- No edits to critique, exports, accepted/golden metadata, or unrelated examples.
- Post-patch closeout requires compile/status evidence.

## Testing Plan

Add focused tests:

- `.mcp.json` exists and references only plugin-root server paths.
- `.mcp.json` does not require `uv` for MCP server startup.
- MCP tool schemas return stable JSON.
- invalid fixture names are rejected before path joins.
- temp workspace fixtures are used instead of plugin examples.
- plugin resources are read from plugin root.
- plugin-root `cwd` does not satisfy the workspace contract even if bundled
  smoke fixtures exist.
- MCP server startup and list-tools/list-resources are side-effect-free.
- missing workspace and missing dependency errors are distinct.
- compile/export wrappers preserve current CLI exit behavior.
- compile/export wrappers enforce timeouts.
- concurrent mutating calls against the same fixture return `operation_in_progress`.
- resource reads return metadata without loading artifact bytes in Phase 1.
- server stdout contains only MCP protocol frames under startup, list-tools, and
  tool-call tests.
- resource listing never includes manuscript fixtures from the plugin package.
- Cowork ZIP includes MCP server files only after tests pass.
- Package audit rejects `.mcp.json` configs that execute workspace-relative scripts.

Keep these existing gates:

- `uv run pytest -q`
- `uv run ruff check .`
- `python3 scripts/package_cowork_plugin.py --output dist/cowork`
- `python3 scripts/plugin_package_audit.py <unpacked-package> --max-mib 50`
- `claude plugin validate <unpacked-package> --strict`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`

## Open Decisions

1. MCP runtime choice: plain Python stdio server, official Python SDK, or a small local adapter.
2. Whether resources should stream image bytes or return file references in the first release.
3. Whether `compile` and `export` need an extra confirmation convention beyond clear tool names/descriptions.
4. Whether MCP should be packaged in 0.10.0 as experimental or held until after one more CLI-only release.
5. Which Claude/Cowork versions are the minimum supported MCP-plugin runtimes.

## Recommendation

Build Phase 1 as a thin facade over the proven CLI core. Do not move business logic into MCP. The goal is to make the host agent see figure state and artifacts more accurately, not to create a second implementation of figure-agent.

The first success criterion is simple: an installed Cowork plugin can answer status, compile, export, and next-action through MCP with the same results as `fig-agent`, while still passing the full CLI test suite and package audit.
