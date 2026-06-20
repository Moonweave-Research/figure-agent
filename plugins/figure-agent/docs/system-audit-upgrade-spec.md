# figure-agent System Audit Upgrade Spec

Status: draft for planning
Date: 2026-06-08
Target: figure-agent 0.10.x after the 0.9.3 Cowork/MCP plugin package

## Summary

The next upgrade should make figure-agent easier to trust after installation,
not merely easier to call. The current 0.9.3 work gives the project a Cowork
ZIP, a public `fig-agent` entrypoint, runtime root separation, and a thin MCP
facade. The remaining system gap is end-to-end auditability across four
boundaries:

- development source tree,
- installed plugin cache,
- user workspace,
- host MCP runtime.

This spec defines the next layer: installed-host smoke, audit evidence graph,
MCP resource metadata, release gates, and cache hygiene diagnostics.

## Current State

Implemented and verified locally:

- Plugin resources are resolved separately from user workspaces.
- `bin/fig-agent` is the public CLI entrypoint.
- Cowork packaging excludes generated artifacts, manuscript fixtures, caches,
  virtualenvs, and local backups.
- `.mcp.json` registers `mcp/figure_agent_server.py` as a plugin-bundled MCP
  server.
- MCP startup is dependency-light and does not require `uv`.
- MCP tools expose doctor/status/compile/export/next-action/loop-checkpoint
  through structured envelopes.
- Package audit checks `.mcp.json` for unsafe workspace-relative script paths.
- Local verification has passed: full pytest, ruff, ZIP build, unzip, package
  audit, and MCP protocol smoke.

Still not proven by local tests:

- Claude/Cowork actually forwards `CLAUDE_PROJECT_DIR` to plugin MCP
  subprocesses in every target host.
- Installed plugin cache cannot accumulate hidden `.venv`, generated build,
  export, or manuscript-state drift after repeated real usage.
- MCP resource behavior is limited to templates and status-returned descriptors;
  artifact reads are not implemented.
- Export/compile MCP errors are still coarse compared with existing CLI policy
  branches.
- Audit evidence is spread across status JSON, checker JSON, critique state,
  export freshness, package audit, and install freshness rather than one
  explainable graph.

## Goals

1. Prove installed-host behavior with a repeatable smoke workflow.
2. Make `figure_agent_doctor` report source/cache/workspace boundaries clearly.
3. Add a figure audit evidence graph that explains release readiness from
   hashes, artifact state, checker outputs, critique freshness, export state,
   and human gates.
4. Expose artifact metadata through MCP resources without streaming large binary
   content in the first pass.
5. Turn release validation into one deterministic command that builds,
   unpacks, audits, and validates the plugin package.
6. Improve MCP error categories so host agents can distinguish policy gates from
   generic subprocess failures.

## Non-goals

- Do not make MCP mandatory for CLI operation.
- Do not add external image-generation, paper-search, or vision API calls to
  the plugin core.
- Do not let MCP mutate user source files by default.
- Do not stream PDF/PNG/TIFF/SVG bytes until host behavior is verified.
- Do not treat bundled smoke fixtures as user workspace examples.
- Do not hide human approval gates behind automated readiness labels.

## Public Interfaces

### CLI

Add or extend:

- `fig-agent doctor --json`
- `fig-agent helper plugin_install_freshness.py --json`
- `fig-agent helper plugin_package_audit.py <root> --max-mib 50`
- `fig-agent helper release_gate.py --output dist/cowork --max-mib 50 --json`
- `fig-agent helper audit_evidence_graph.py <name> --json`

`release_gate.py` should be a deterministic wrapper around existing checks, not
a new release policy engine.

Implementation note: adding these helper scripts also requires updating
`bin/fig-agent` helper allowlists, command docs, and command-contract tests so
public docs do not route users back to `python3 scripts/...`.

### MCP

Extend existing tools without renaming them:

- `figure_agent_doctor`
- `figure_agent_status`
- `figure_agent_next`
- `figure_agent_compile`
- `figure_agent_export`
- `figure_agent_loop_checkpoint`

Extend `figure_agent_doctor` output with boundary fields:

```json
{
  "schema": "figure-agent.mcp.doctor.v1",
  "success": false,
  "bundle": {
    "state": "ok",
    "plugin_root": "/Users/example/.claude/plugins/cache/figure-agent",
    "plugin_root_kind": "installed_cache",
    "unexpected_cache_state": []
  },
  "workspace": {
    "state": "missing",
    "workspace_root": null,
    "workspace_source": "missing"
  },
  "dependencies": {}
}
```

`plugin_root_kind` values:

- `source_tree`
- `installed_cache`
- `unpacked_zip`
- `unknown`

`workspace_source` values:

- `FIGURE_AGENT_WORKSPACE`
- `CLAUDE_PROJECT_DIR`
- `cwd`
- `missing`

Add Phase 2 tools only after CLI contracts exist:

- `figure_agent_release_gate`
- `figure_agent_audit_graph`

`figure_agent_release_gate` is a developer/release tool, not a normal Cowork
project tool. It must be disabled by default in installed user workflows and
enabled only when `FIGURE_AGENT_ENABLE_RELEASE_TOOLS=1` is present. When
disabled, the MCP response must use `unsupported_operation` and must not run
tests, build packages, create `dist/`, or inspect unrelated workspaces.

Add MCP resource template reads:

- `figure://<name>/build/png`
- `figure://<name>/build/pdf`
- `figure://<name>/exports/svg`
- `figure://<name>/exports/png`
- `figure://<name>/audit/visual-clash`
- `figure://<name>/audit/text-boundary`
- `figure://<name>/audit/label-path`
- `figure://<name>/perception/extract`
- `figure://<name>/audit/evidence-graph`

Phase 2 `resources/read` returns JSON metadata only:

```json
{
  "schema": "figure-agent.mcp.resource-metadata.v1",
  "success": true,
  "uri": "figure://smoke_trap_demo/build/png",
  "path": "examples/smoke_trap_demo/build/smoke_trap_demo.png",
  "exists": true,
  "media_type": "image/png",
  "size_bytes": 12345,
  "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "freshness": "fresh"
}
```

## Architecture

Use five layers:

1. **Runtime Boundary Layer**
   `runtime_paths.py` remains the only resolver for plugin resources and user
   workspace paths. MCP may add stricter plugin-root `cwd` handling, but should
   not create a second general path system.
   All graph/resource readers must resolve candidate paths and reject path
   escapes outside `workspace_root/examples/<name>` or the plugin style
   allowlist.

2. **CLI Evidence Layer**
   Existing scripts produce status, checker outputs, critique freshness, export
   freshness, and package/install diagnostics.

3. **Audit Graph Layer**
   A new helper normalizes evidence into one graph-shaped JSON payload. It reads
   files and hashes artifacts but does not compile, export, or edit.

4. **MCP Facade Layer**
   MCP exposes evidence and safe operations through structured envelopes and
   metadata resources. It does not become a second workflow engine.

5. **Release Gate Layer**
   A deterministic command builds the ZIP, unpacks it, runs package audit,
   checks MCP config, and optionally calls `claude plugin validate` when the
   host CLI is available.

## Audit Evidence Graph

Add a JSON schema:

```json
{
  "schema": "figure-agent.audit-evidence-graph.v1",
  "name": "smoke_trap_demo",
  "workspace_root": "/Users/example/project",
  "nodes": [],
  "edges": [],
  "readiness": {
    "workflow_ready": false,
    "final_ready": false,
    "release_ready": false,
    "human_gate_required": true
  },
  "first_blocker": {
    "category": "human_gate",
    "code": "acceptance_required",
    "message": "Human acceptance is required before release."
  }
}
```

Required node classes:

- `source`: `spec.yaml`, `<name>.tex`, `briefing.md`, `critique.md`
- `style`: bundled style lock files
- `build_artifact`: build PDF/PNG/checker outputs
- `export_artifact`: exported PDF/SVG/PNG/TIFF
- `checker`: visual clash, text boundary, label path, undeclared geometry
- `critique`: critique freshness and lint state
- `human_gate`: acceptance/publication gate state
- `package`: installed package/cache hygiene when available

Readiness definitions:

- `workflow_ready`: compile/status loop can proceed without missing deterministic
  prerequisites.
- `final_ready`: final artifact exists, is fresh, and has no deterministic
  plugin blocker.
- `release_ready`: `final_ready` plus acceptance/publication gates are satisfied.
- `human_gate_required`: true whenever acceptance, external review, unresolved
  critique judgment, or publication disclosure requires a person.
- `first_blocker`: the highest-priority blocker according to the existing status
  explanation policy; the graph must not invent a separate priority system.

Required edge classes:

- `derived_from`
- `fresh_against`
- `blocks`
- `satisfies`
- `requires_human`

Hash policy:

- Use SHA-256 for source and artifact files.
- Hash only files under `workspace_root/examples/<name>` and plugin style files.
- Never hash arbitrary absolute paths supplied by model/tool input.
- Hash files by streaming chunks; never load full PDFs, PNGs, TIFFs, or SVGs
  into memory only to compute identity.
- Refuse or mark unresolved any symlink that resolves outside the fixture
  directory or plugin style allowlist.
- Stable graph output should prefer workspace-relative and plugin-relative paths.
  Absolute paths may appear only in explicit debug fields.
- Sort nodes and edges deterministically by id so repeated runs produce stable
  JSON except for elapsed-time/debug fields.
- Missing files are explicit nodes with `exists: false`, not exceptions.

Node id policy:

- Node ids must be deterministic strings such as
  `source:spec.yaml`, `build:smoke_trap_demo.pdf`, or
  `checker:visual_clash`.
- Edge ids are derived from `from`, `to`, and edge class.
- Duplicate node ids are test failures.
- Graph payloads must include `schema_version` or versioned `schema` and may
  only add optional fields without a schema bump.

## Installed Host Smoke

Create a repeatable smoke that can be followed manually first and automated
later.

Required checks:

1. Installed plugin appears in plugin list.
2. `/mcp` shows `figure-agent`.
3. `figure_agent_doctor` reports:
   - plugin bundle root,
   - workspace root,
   - whether workspace came from `FIGURE_AGENT_WORKSPACE`,
     `CLAUDE_PROJECT_DIR`, or non-plugin `cwd`,
   - host dependencies.
4. With host project missing `examples/`, doctor reports `workspace_missing`
   but not `bundle_missing`.
5. With host project containing `examples/smoke_trap_demo`, MCP status reads
   that workspace fixture and returns plugin style/artifact metadata.
6. Installed plugin cache does not gain `.venv`, `build/`, `exports/`,
   manuscript fixtures, or local backup files after doctor/status.

Cache hygiene allowlist:

- expected: `.claude-plugin/`, `.mcp.json`, `mcp/`, `bin/`, `commands/`,
  `skills/`, `scripts/`, `styles/`, selected docs, `README.md`,
  `CHANGELOG.md`, `pyproject.toml`, `uv.lock`, and bundled smoke fixture source
  files.
- unexpected: `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `.scratch/`, `dist/`,
  generated `build/`, generated `exports/`, manuscript fixtures other than the
  smoke fixture, local backup directories, and package manager caches.

Host env fallback:

- If the host does not forward `CLAUDE_PROJECT_DIR` and the MCP process starts
  with plugin-root `cwd`, workspace tools must fail with `workspace_missing`.
- This is an explicit unsupported host/workspace state, not a reason to read
  plugin-bundled examples as user figures.
- The smoke report must record the host name, app/version if visible, exact date,
  and whether the workspace source was `FIGURE_AGENT_WORKSPACE`,
  `CLAUDE_PROJECT_DIR`, non-plugin `cwd`, or missing.

## Release Gate

Add `scripts/release_gate.py` after the lower-level audit functions are stable.

Required steps:

1. Run targeted contract tests.
2. Run full pytest when not explicitly skipped.
3. Run ruff.
4. Build Cowork ZIP.
5. Unpack to a temp directory.
6. Run package audit with `--max-mib 50`.
7. Verify required package paths:
   - `.claude-plugin/plugin.json`
   - `.mcp.json`
   - `mcp/figure_agent_server.py`
   - `bin/fig-agent`
   - `scripts/`
   - `styles/`
   - `commands/`
   - `skills/`
8. Verify excluded paths:
   - generated `build/`
   - generated `exports/`
   - `.venv`
   - plugin cache backups
   - dirty manuscript fixtures
9. If `claude` is available, run:
   - `claude plugin validate <unpacked-package> --strict`
   - from plugin root: `claude plugin validate .`
   - from repository root: `claude plugin validate .claude-plugin/marketplace.json`
10. Emit one JSON report with pass/fail, artifact path, package size, and
    failure categories.

Release gate output and side effects:

- Default output must be a caller-selected temp/output directory, not the
  installed plugin cache.
- The command may create package artifacts only under the requested output path
  and temporary unpack directories.
- The command must never run `--clean` automatically.
- Missing optional host tools such as `claude` are `skipped`, not `passed`.

## MCP Error Improvements

Phase 2 should map existing CLI policy branches into stable categories.

Export wrapper mapping:

- critique missing or stale -> `critique_required`
- declared reference missing -> `reference_input_missing`
- tracked golden protected -> `tracked_golden_protected`
- missing build PDF -> `compile_failed`
- unsupported CLI failure -> `export_failed`

MCP success semantics:

- Fresh no-op export is `success: true`.
- Successful regenerate is `success: true`.
- Tracked-golden protection without `force_golden` is `success: false` with
  `tracked_golden_protected`, even if the CLI preserves exit code 0 for shell
  compatibility.
- Missing/stale critique and missing reference inputs are `success: false`
  policy gates, not generic subprocess failures.
- Text parsing of human-readable CLI output is allowed only as a compatibility
  bridge. Preferred implementation is to refactor shared helpers to return
  structured branch outcomes and have CLI/MCP render from that shared result.

Compile wrapper mapping:

- TeX engine missing -> `dependency_missing`
- source missing -> `fixture_missing` or `compile_failed` depending on fixture
  existence
- timeout -> `timeout`
- checker failure -> `compile_failed` with checker summaries

Doctor mapping:

- bundle files missing -> `bundle_missing`
- workspace missing -> `workspace_missing`
- host binary/module missing -> `dependency_missing`
- aggregate failure envelope may still use `doctor_failed` only as summary;
  individual diagnostics must carry specific categories.

## Security and Boundary Rules

- Tool inputs may name fixtures only, never arbitrary workspace roots.
- Fixture names must remain single path components under `examples/`.
- Plugin root is never a user workspace.
- Resource URIs must be parsed against a fixed allowlist of resource kinds; URI
  path segments must not be used as filesystem paths directly.
- Symlink escapes from fixture directories are rejected or reported as blocked
  evidence nodes.
- MCP startup, list-tools, list-resources, and list-templates create no files.
- Resource reads return metadata only in Phase 2.
- Resource freshness must reuse existing status/export/critique freshness
  helpers where available. Do not invent independent mtime-only freshness rules
  for MCP resource metadata.
- Mutating tools serialize per fixture.
- stdout is reserved for MCP protocol frames.
- Package/release audits must not delete files unless a command explicitly says
  `--clean`.
- Developer/release MCP tools are disabled unless
  `FIGURE_AGENT_ENABLE_RELEASE_TOOLS=1` is set.

## Test Plan

Add tests in small slices:

- `tests/test_installed_host_smoke_contract.py`
  - simulate plugin-root `cwd` with no workspace env,
  - simulate temp workspace with `examples/smoke_trap_demo`,
  - assert plugin bundled examples never satisfy user workspace.
  - assert `plugin_root_kind` and `workspace_source` values are one of the
    documented enums.
  - assert cache hygiene allowlist violations are reported without deleting.

- `tests/test_audit_evidence_graph.py`
  - missing fixture returns explicit missing graph,
  - minimal stage-1 fixture returns source nodes and first blocker,
  - existing build/export artifacts include size/hash metadata,
  - graph never reads outside plugin root or workspace examples.
  - symlink escapes are blocked or represented as blocked evidence nodes,
  - node and edge order is deterministic across repeated runs.

- `tests/test_mcp_resource_metadata.py`
  - `resources/templates/list` exposes templates,
  - `resources/read` returns JSON metadata for existing artifact,
  - missing artifact returns `exists: false`,
  - binary bytes are not streamed.
  - malicious URIs such as `figure://../outside/build/png` are rejected,
  - fixture symlink escapes do not expose outside files.

- `tests/test_release_gate.py`
  - release gate builds ZIP to temp output,
  - unpacked ZIP passes package audit,
  - required paths are present,
  - excluded paths are absent,
  - missing `claude` CLI is reported as skipped, not failed.
  - output is confined to the requested output/temp directory,
  - release gate never runs package audit with `--clean`.

- Extend `tests/test_mcp_facade.py`
  - export policy errors map to stable categories,
  - compile timeout path returns `timeout`,
  - package/cache root does not get `.venv` from MCP tool calls.
  - `figure_agent_release_gate` is unavailable without
    `FIGURE_AGENT_ENABLE_RELEASE_TOOLS=1`.
  - tracked-golden protection is reported as `success: false` with
    `tracked_golden_protected` even when the CLI command exits 0.

## Rollout Plan

### Phase 0: Host Smoke Checklist

- Write manual installed-host smoke doc.
- Run it once in Claude Code and once in Cowork/Desktop if available.
- Record host-specific environment observations.

Acceptance:

- Known host env behavior is documented with exact dates.
- Any missing `CLAUDE_PROJECT_DIR` behavior has a fallback plan.

### Phase 1: Release Gate

- Add `scripts/release_gate.py`.
- Add package/validate/audit JSON output.
- Wire into docs and README.

Acceptance:

- One command can produce a verified ZIP report.
- Existing package tests still pass.

### Phase 2: Audit Evidence Graph

- Add `scripts/audit_evidence_graph.py`.
- Expose `figure_agent_audit_graph`.
- Include graph metadata in status where useful.

Acceptance:

- A user can ask why a figure is not release-ready and get a structured first
  blocker with evidence references.

### Phase 3: MCP Resource Metadata

- Implement `resources/read` for metadata responses.
- Add artifact size/hash/freshness.
- Keep binary streaming disabled.

Acceptance:

- Host can inspect artifact identity without path guessing or reading raw bytes.

### Phase 4: Fine-Grained MCP Errors

- Parse existing CLI outputs or refactor helpers to return structured branch
  outcomes.
- Replace generic `export_failed` and coarse `compile_failed` where policy
  branches are known.

Acceptance:

- Host agent can distinguish missing critique, reference input errors, tracked
  golden protection, dependency failures, and generic subprocess failures.

## Open Decisions

1. Whether installed-host smoke should be a purely documented checklist or a
   script that emits a prompt for Claude/Cowork to run.
2. Whether audit graph nodes should use compact flat arrays or nested sections
   optimized for human readability.
3. Whether `figure_agent_status` should embed audit graph summaries by default
   or keep graph retrieval as a separate tool.
4. Whether package cache hygiene should warn on `.venv` only, or any directory
   outside the expected installed package allowlist.

## Recommendation

Build the next increment in this order:

1. host smoke checklist,
2. release gate,
3. audit evidence graph,
4. MCP resource metadata,
5. fine-grained MCP error mapping.

This order keeps the system honest: prove installation behavior first, make
release verification repeatable second, then deepen figure-quality evidence.
