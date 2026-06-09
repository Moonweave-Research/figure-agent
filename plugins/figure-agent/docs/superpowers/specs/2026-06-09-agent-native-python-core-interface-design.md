# Agent-Native Python Core Interface Design

Date: 2026-06-09
Status: proposed
Target: figure-agent 0.11.x and later

## Summary

figure-agent should remain a UI-less, agent-native tool. The primary product is
not a visual app; it is a deterministic figure-improvement kernel that coding
agents, Claude Cowork, Codex, local shell users, and future MCP clients can call
without guessing what happened.

Python remains the correct core language for the current phase because the
system depends on file orchestration, LaTeX/SVG/PDF tooling, detector adapters,
benchmark runners, and JSON contracts more than low-latency UI rendering. MCP is
valuable as an agent access surface, but it must stay a thin facade over the
same Python/CLI contracts. It must not become a second implementation of figure
logic.

The next design priority is therefore not a rewrite. It is a stronger command
and schema layer: stable JSON envelopes, explicit write boundaries, benchmarked
candidate evidence, safe workspace behavior, and one obvious next action for an
agent to run.

## Current Position

Already available:

- plugin/workspace runtime separation through `FIGURE_AGENT_PLUGIN_ROOT` and
  `FIGURE_AGENT_WORKSPACE`;
- public shell entrypoint through `fig-agent`;
- packaged Cowork plugin flow;
- MCP facade for core read/preview workflows;
- candidate generation, rendering, ranking, review, and gated apply semantics;
- smoke and dogfood benchmark contracts;
- detector-backed benchmark report generation;
- release gate checks for packaging, smoke, MCP, and benchmark behavior.

The remaining architectural risk is interface drift: different commands return
slightly different JSON shapes, some workflows still require an agent to infer
the next step, and MCP can become confusing if it exposes tools without a common
state model.

## Product Stance

### Primary User

The primary user is an agent operating inside a user workspace:

1. inspect a figure fixture;
2. identify the current state;
3. propose safe improvements;
4. render and compare candidates;
5. explain evidence;
6. request explicit human acceptance for source mutation;
7. export publication artifacts only after gates pass.

Human users may run the same CLI, but the interface should be optimized for
machine parsing first and human readability second.

### Non-Goals

- Do not build a frontend or review board in this phase.
- Do not rewrite the core in TypeScript, Rust, or another systems language.
- Do not create a separate MCP implementation of figure logic.
- Do not let MCP mutate source files by default.
- Do not add hidden ML auto-design that bypasses benchmark evidence, detector
  reports, or human acceptance gates.
- Do not write into Google Drive, CloudStorage, sync folders, global caches, or
  user manuscript files during preview operations.

## Architecture Decision

Keep a Python core, expose it through a strict CLI contract, and let MCP call
that same core as a facade.

The durable layering is:

1. Python modules implement figure state, candidate generation, detectors,
   benchmarks, package checks, and apply gates.
2. `fig-agent` is the only public shell entrypoint.
3. MCP tools call the same Python modules or the same command handlers.
4. Agents consume stable JSON responses and artifact paths.
5. Write operations require explicit commands and explicit flags.

This keeps one source of truth while still making the tool installable in
Codex, Claude Desktop, Claude Cowork, and ordinary local terminals.

## Public Interface Contract

Every new machine-facing command should support `--json` unless it is a pure
artifact writer whose output is already a file.

Preferred command names:

```bash
fig-agent doctor --json
fig-agent status <name> --json
fig-agent next <name> --json
fig-agent analyze-panel <name> <panel-id> --json
fig-agent candidates <name> --json
fig-agent render-candidates <name> --candidate-set <path> --json
fig-agent rank-candidates <name> --candidate-set <path> --json
fig-agent review-candidate <name> <candidate-id> --json
fig-agent apply-candidate-ready <name> <candidate-id> --json
fig-agent accept-candidate <name> <candidate-id> --write
fig-agent apply-candidate <name> <candidate-id> --apply
fig-agent benchmark-run --suite smoke --json
fig-agent benchmark-detectors <name> --suite smoke --json
```

`fig-agent next` is the missing high-leverage command. It should not perform
work. It should inspect fixture state and return the single safest next command
plus alternatives and blockers. This reduces agent thrash because the agent can
ask the tool what state machine transition is legal instead of reconstructing
that logic from docs.

## JSON Envelope

New JSON outputs should converge on this envelope:

```json
{
  "schema": "figure-agent.<domain>.v1",
  "success": true,
  "state": "ready",
  "name": "smoke_trap_demo",
  "workspace_root": null,
  "plugin_root": null,
  "artifacts": [],
  "diagnostics": [],
  "writes": [],
  "next": {
    "command": "fig-agent status smoke_trap_demo --json",
    "reason": "Fixture exists and no compile artifact is fresh."
  },
  "duration_ms": 0
}
```

Rules:

- `schema` is required.
- `success` is required and must represent command success, not figure quality.
- `state` is required when the command inspects workflow state.
- `diagnostics` is always a list.
- `writes` is always a list and must be empty for read-only commands.
- Stable fields must not expose absolute local paths.
- Absolute paths are allowed only in explicitly local diagnostic fields or
  human-readable debug sections.
- Artifact paths should be fixture-relative where possible.
- Error responses should use the same envelope shape with `success: false`.

## Write-Safety Contract

Default behavior must be preview/read-only. Mutation requires an explicit command
and an explicit write/apply flag.

Read-only commands must not write source or durable review state. Commands that
produce derived artifacts must make the write explicit in the command name,
flag, or output contract, such as candidate sandbox rendering, detector report
generation with `--write`, or benchmark report generation.

Source mutation is allowed only through acceptance/apply commands:

- `accept-candidate` records human approval evidence;
- `apply-candidate` mutates fixture source only after acceptance hashes match;
- apply must create rollback metadata before mutation;
- MCP apply remains refused unless a future spec explicitly enables an
  operator-gated write mode.

Preview commands must not edit:

- `caption.md`;
- manuscript text;
- accepted exports;
- golden exports;
- files outside the active fixture;
- files under Google Drive, CloudStorage, or other sync roots.

## Workspace Safety

The plugin has two roots:

- plugin root: installed bundle containing `scripts/`, `styles/`, `skills/`,
  `commands/`, `bin/`, and metadata;
- workspace root: user project containing `examples/<name>`.

All command implementations must use runtime path resolution rather than
assuming the current working directory is the plugin root.

Safety checks:

- reject workspace paths that resolve outside `FIGURE_AGENT_WORKSPACE`;
- reject plugin resource paths that resolve outside `FIGURE_AGENT_PLUGIN_ROOT`;
- avoid global caches for figure outputs;
- keep test kernels and candidate sandboxes inside local repo temp fixtures or
  `/tmp`, not sync folders;
- record refused write attempts as diagnostics instead of silently falling back
  to unsafe locations.

## MCP Boundary

MCP is an access layer for agents, not the core product.

MCP tools should:

- expose tool descriptions that mirror `fig-agent` commands;
- return the same JSON envelope fields where practical;
- refuse source mutation by default;
- return structured refusal codes instead of free-text-only errors;
- avoid arbitrary absolute path arguments;
- operate on fixture names and candidate IDs, not uncontrolled local paths;
- report exact equivalent CLI commands in `next.command` or diagnostics.

MCP tools should not:

- implement detector logic separately from Python modules;
- maintain separate workflow state;
- silently call write commands;
- hide benchmark or human-gate failures.

## Benchmark Meaning

Benchmark cases are not random generated figures and not arbitrary external
paper figures. They are fixed local fixtures with explicit contracts.

Two benchmark tiers are useful:

1. smoke benchmarks: small controlled fixtures that isolate known failure
   families such as label overlap, leader-line ambiguity, panel spacing,
   contrast, and annotation box collisions;
2. dogfood benchmarks: real project figures, such as
   `fig1_overview_v2_pair_001_vault`, promoted only when they have detector
   reports and clear metrics.

The benchmark goal is not to claim aesthetic superiority from one scalar score.
It is to prevent regressions and measure whether a candidate reduces known,
observable defects under fixed contracts.

## Next Implementation Targets

### Target 1: Unified Output Envelope

Normalize the highest-value CLI/MCP responses first:

- `doctor`;
- `status`;
- `next`;
- `benchmark-run`;
- `benchmark-detectors`;
- candidate readiness/review commands.

Acceptance:

- contract tests assert required envelope fields;
- error cases use the same envelope;
- release-contract docs list schema names.

### Target 2: `fig-agent next`

Add a read-only state-router command for agents.

It should return:

- current fixture state;
- one recommended next command;
- blocked reasons;
- alternative safe commands;
- whether human acceptance is required;
- whether writes would occur.

Acceptance:

- missing fixture returns workspace diagnostic;
- stale build returns compile/export recommendation;
- candidate-ready fixture returns review/accept recommendation;
- accepted candidate returns apply recommendation;
- publication-gated fixture returns human gate diagnostic.

### Target 3: MCP Schema Tightening

Align MCP tools with the CLI envelope and add schema tests.

Acceptance:

- each MCP response includes `schema`, `success`, `diagnostics`, and `writes`;
- read-only tools return `writes: []`;
- refused apply uses a stable refusal code;
- MCP docs show equivalent `fig-agent` commands.

### Target 4: Evidence-First Candidate Loop

Improve candidate workflows only where detector or benchmark evidence can
compare before/after outputs.

Acceptance:

- rendered candidates produce detector reports;
- ranking cites detector deltas;
- review packets include evidence links;
- apply readiness refuses candidates without fresh render evidence.

### Target 5: Dogfood Promotion Rules

Make real fixture promotion explicit.

Acceptance:

- dogfood fixtures must have `benchmark_contract.yaml`;
- dogfood metrics must be detector-derived or manually justified;
- benchmark reports must be reproducible from fixture artifacts;
- generated build/export artifacts stay out of package ZIPs and unrelated git
  commits.

## Testing Strategy

Focused tests:

```bash
uv run pytest -q plugins/figure-agent/tests/test_command_contract_docs.py \
  plugins/figure-agent/tests/test_fig_driver_commands.py \
  plugins/figure-agent/tests/test_release_contract.py

uv run pytest -q plugins/figure-agent/tests/test_mcp_facade.py \
  plugins/figure-agent/tests/test_benchmark_contracts.py \
  plugins/figure-agent/tests/test_quality_benchmark.py

uv run ruff check plugins/figure-agent
```

Package/release checks:

```bash
python3 scripts/package_cowork_plugin.py --output dist/cowork
python3 scripts/plugin_package_audit.py plugins/figure-agent --max-mib 50
plugins/figure-agent/bin/fig-agent release-gate --dry-run --json
```

Dogfood checks:

```bash
FIGURE_AGENT_WORKSPACE=plugins/figure-agent \
  plugins/figure-agent/bin/fig-agent benchmark-detectors \
  fig1_overview_v2_pair_001_vault --suite dogfood --json

FIGURE_AGENT_WORKSPACE=plugins/figure-agent \
  plugins/figure-agent/bin/fig-agent benchmark-run --suite dogfood --json
```

## Review Checklist

- Does any new command return JSON without `schema` or `success`?
- Does any preview command mutate source?
- Does any MCP tool implement logic separately from CLI/Python modules?
- Does any command require cwd-relative plugin paths?
- Does any stable JSON field leak absolute local paths?
- Does any workflow write into CloudStorage, Google Drive, or global caches?
- Does any candidate claim improvement without detector or benchmark evidence?
- Does any apply path bypass human acceptance hashes?
- Does package output include manuscript fixtures, build artifacts, exports, or
  local install backups?

## Acceptance Criteria

This direction is complete when:

1. Python remains the single core implementation for figure logic.
2. `fig-agent` remains the public command surface.
3. MCP is documented and tested as a facade, not a second engine.
4. Machine-facing outputs use stable envelopes with explicit diagnostics and
   writes.
5. `fig-agent next` gives agents one safe next action.
6. All mutation paths require explicit write/apply commands.
7. Benchmarks distinguish smoke fixtures from real dogfood fixtures.
8. Release gates catch schema drift, package pollution, and benchmark
   regressions.

## Rationale

The tool becomes better at drawing figures when agents can safely run more
closed-loop experiments with less ambiguity. A UI would mainly help humans
inspect results. The current bottleneck is different: agents need deterministic
state, stable schemas, precise diagnostics, evidence-backed ranking, and safe
mutation gates. Strengthening the Python core and its CLI/MCP contracts attacks
that bottleneck directly without splitting the implementation.
