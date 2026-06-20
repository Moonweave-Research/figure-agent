# Figure-Agent Quality Improvement Loop Design

Status: ready for implementation

Target: figure-agent 0.10.x after Cowork/MCP packaging and system-audit
hardening

## Summary

The previous upgrade made figure-agent installable, diagnosable, packageable, and
MCP-visible. It did not make the figure authoring engine inherently better at
drawing.

This spec defines the next layer: a quality-improvement loop that turns existing
audit, critique, reference, and status evidence into bounded mechanical patch
plans. The goal is not autonomous taste. The goal is to make the existing
human-led element-iteration loop faster, more explicit, and less error-prone.

The loop must preserve the current contract:

- the user owns scientific meaning and taste;
- deterministic tools own mechanical checks and render evidence;
- host vision can identify and describe defects;
- figure-agent may propose safe mechanical edits;
- no source mutation happens without an explicit apply command and fresh
  verification.

## Current Baseline

Already available:

- deterministic compile checks: collisions, visual clash, text boundary, label
  path proximity, undeclared geometry, warning budgets, perception packs;
- critique schema through v1.17 with grounded observation, aesthetic levers,
  reference learning, and top-tier audit slots;
- `fig_loop_auto_patch.py` classifies auto-patch eligibility but always returns
  `may_edit: false`;
- SVG polish recipe, executor, manifest, and delta machinery exist, but real
  fixture promotion is intentionally conservative;
- `audit_evidence_graph.py` can explain fixture evidence and readiness;
- MCP resource metadata exposes artifact descriptors without streaming binary
  content;
- roadmap policy says fig1 is the frozen reference, taste remains human-led, and
  SVG polish reopens only under proven recurring pressure.

Observed gap:

- The system can say what is wrong, but it does not yet reliably convert narrow
  mechanical defects into patchable, reviewable source operations.

## Goals

1. Build a quality defect ledger that normalizes actionable defects from
   deterministic audits, critique findings, loop decisions, and reference/style
   evidence.
2. Produce safe patch plans for narrow mechanical issues:
   - label offsets;
   - text overlap relief;
   - small whitespace balancing;
   - line-weight/style normalization;
   - repeated style macro adoption;
   - bounded SVG visual polish only when the existing route allows it.
3. Keep all proposed edits reviewable before apply.
4. Require compile/export/status evidence after any apply.
5. Expose the loop through CLI first and MCP as a proposal/status surface.
6. Measure improvement by before/after audit deltas, not by model taste scores.
7. Keep the implementation compatible with existing `fig_loop` patch handoff and
   patch executor evidence instead of creating a second patch ecosystem.

## Non-Goals

- Do not create an autonomous figure designer.
- Do not let MCP mutate source files by default.
- Do not use SVG polish to repair scientific semantics, topology, reaction
  meaning, causal arrows, or manuscript claims.
- Do not decide accepted/golden/publication state.
- Do not rebuild paper-figure-vault supply or reference retrieval in this slice.
- Do not refactor the full command surface.
- Do not generate broad alternate figures off-identity.

## Success Criteria

The upgrade is successful when these are true on fixture-level tests and at
least one real non-fig1 manuscript fixture:

1. `fig-agent quality-map <name> --json` emits a deterministic defect ledger
   with stable ids, evidence links, severity, patchability, and owner.
2. `fig-agent propose <name> --json` emits a patch plan for at least one narrow
   mechanical defect without editing files.
3. Patch plans refuse semantic, taste, publication, accepted/golden, stale, and
   unsupported defects with explicit reasons.
4. Applying a plan requires an explicit command flag and records before/after
   evidence.
5. After apply, compile/status evidence shows either improvement or a precise
   rollback-required state.
6. No generated plan or MCP response contains workspace-escaping paths.
7. The loop reduces manual patch bookkeeping without reopening fig1's frozen
   reference state.
8. Existing `fig_loop` outputs that include `auto_patch_eligibility` can be
   consumed without changing their current schema or meaning.

## Scope Boundary

This release is the first implementation slice of a larger quality-improvement
system. It must deliver one reliable vertical path:

```text
defect evidence -> quality-map -> safe proposal -> explicit apply -> verify
```

It must not attempt to solve all visual quality classes. A narrow successful
label/style patch with full provenance is more valuable than a broad planner
that edits many constructs with weak guarantees.

Implementation must stop after Phase 3 unless a real dogfood fixture proves that
the path is useful without increasing review burden.

## Agent Execution Contract

Implement this spec in order. Do not skip ahead to source mutation before the
read-only and proposal contracts are proven.

### Required Order

1. Runtime contracts:
   - fixture/workspace path resolution;
   - generated artifact allowlist;
   - schema/module map update;
   - release inventory update.
2. Phase 1 read-only ledger:
   - `quality_defect_ledger.py`;
   - `fig-agent quality-map`;
   - MCP `figure_agent_quality_map`;
   - deterministic and path-safety tests.
3. Phase 2 proposal-only planner:
   - `quality_patch_policy.py`;
   - `quality_patch_plan.py`;
   - `fig-agent propose`;
   - MCP `figure_agent_propose_patch`;
   - synthetic safe/refused plan tests.
4. Phase 3 explicit apply and verify:
   - `quality_patch_apply.py`;
   - `fig-agent apply-plan`;
   - `fig-agent verify-plan`;
   - mutation lock, rollback, stale-plan, and verification tests.
5. Phase 4 dogfood:
   - synthetic manuscript-like fixture;
   - one non-fig1 real fixture;
   - written before/after evidence.

### Parallel Work Split

These workstreams can be assigned to separate agents if their write sets stay
disjoint:

- Ledger agent: `quality_defect_ledger.py`, ledger tests, MCP read-only wrapper.
- Policy/planner agent: `quality_patch_policy.py`, `quality_patch_plan.py`,
  planner tests.
- Apply/verify agent: `quality_patch_apply.py`, lock/rollback/apply tests.
- Release/docs agent: command docs, schema-module map, release gate/package
  tests.

Do not let multiple agents edit `bin/fig-agent` or `mcp/figure_agent_server.py`
at the same time. Integrate those files serially after each phase passes.

### Done Gate Per Phase

Each phase is done only when all are true:

- focused unit tests pass;
- `uv run ruff check` passes for touched Python files;
- relevant CLI contract tests pass;
- `git diff --check` is clean;
- generated artifacts remain under `examples/<name>/build/quality/`;
- Cowork-facing commands use `fig-agent ...`;
- user fixture work such as existing manuscript `caption.md` remains untouched.

Before declaring the full feature done, run:

```text
uv run pytest -q
uv run ruff check .
python3 scripts/release_gate.py --output dist/cowork --json
```

If full release gate time is too high during inner-loop work, targeted release
gate may be used temporarily, but the final claim requires the full gate.

### Safe Mechanical Patch Definition

A patch is safe-mechanical only when all conditions are true:

- it changes at most one fixture-local source or SVG-polish recipe file;
- it has a deterministic selector that matches exactly one intended target, or a
  bounded line range with an original text hash;
- it changes layout/style mechanics only, not scientific meaning;
- it can be verified by compile/status/audit evidence;
- it has a reverse patch or equivalent rollback artifact;
- it does not require the agent to decide whether the figure is tasteful,
  publishable, accepted, or scientifically correct.

Any failed condition routes the defect to `assisted_only`, `human_required`, or
`unsupported`.

### File Ownership

Expected new files:

| File | Owner | Responsibility |
|---|---|---|
| `scripts/quality_defect_ledger.py` | Phase 1 | Build read-only defect ledger from existing evidence |
| `scripts/quality_patch_policy.py` | Phase 2 | Classify patchability and blocked reasons |
| `scripts/quality_patch_plan.py` | Phase 2 | Build deterministic patch plans |
| `scripts/quality_patch_apply.py` | Phase 3 | Validate, apply, verify, and rollback plans |
| `tests/test_quality_defect_ledger.py` | Phase 1 | Ledger contract tests |
| `tests/test_quality_patch_policy.py` | Phase 2 | Patchability policy tests |
| `tests/test_quality_patch_plan.py` | Phase 2 | Plan generation and safety tests |
| `tests/test_quality_patch_apply.py` | Phase 3 | Apply, lock, rollback, verify tests |

Expected modified files:

| File | Change |
|---|---|
| `bin/fig-agent` | Add public command routing serially after script tests pass |
| `mcp/figure_agent_server.py` | Add read/propose/verify tools only |
| `scripts/release_gate.py` | Add new targeted tests and package exclusions |
| `docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md` | Add new schemas and module ownership |
| `docs/superpowers/issues/2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md` | Update inventory counts |
| command docs | Add user-facing `fig-agent ...` command text only if public command docs are added |

Do not modify manuscript fixture source during implementation except inside
explicit synthetic or dogfood test fixtures created for this feature.

## Public Interfaces

### CLI

Add these public commands behind `bin/fig-agent`:

```text
fig-agent quality-map <name> [--json | --format json]
fig-agent propose <name> [--json | --format json] [--scope safe-mechanics]
  [--output build/quality/patch_plan.yaml]
fig-agent apply-plan <name> --plan <fixture-relative-plan> --dry-run
fig-agent apply-plan <name> --plan <fixture-relative-plan> --apply
fig-agent verify-plan <name> --plan <fixture-relative-plan> [--json | --format json]
```

Command behavior:

- `quality-map` is read-only.
- `propose` is read-only by default and prints the plan to stdout.
- `propose --output` may write only a generated fixture-local plan under
  `build/`; it must not edit source.
- `apply-plan --dry-run` is read-only.
- `apply-plan --apply` is the only source-mutating command and must refuse stale
  plans.
- `verify-plan` reruns the required checks and reports whether the patch
  improved, regressed, or needs rollback.

Existing commands must keep working:

- `fig-agent status`
- `fig-agent compile`
- `fig-agent export`
- `fig-agent doctor`

### Artifact Layout

Generated quality-loop artifacts live under:

```text
examples/<name>/build/quality/
  defect_ledger.json
  patch_plan.yaml
  patch_result.json
  rollback/
    <plan-id>.patch
```

Rules:

- `quality-map` may only write `defect_ledger.json` when an explicit future
  `--output` option is implemented; the Phase 1 default is stdout only.
- `propose --output build/quality/patch_plan.yaml` may create parent
  directories under `build/quality/`.
- rollback artifacts are generated only by `apply-plan --apply`.
- generated quality artifacts are package-excluded and must never be included in
  Cowork ZIPs.

### MCP

Add proposal/status tools only in the first MCP phase:

```text
figure_agent_quality_map
figure_agent_propose_patch
figure_agent_verify_plan
```

MCP mutation remains disabled by default. If a future write-capable MCP apply
tool is added, it must require both:

- a server environment opt-in, for example `FIGURE_AGENT_MCP_ENABLE_WRITES=1`;
- an explicit per-call `allow_write: true`.

MCP resource templates may add:

```text
figure://{name}/quality/defect-ledger
figure://{name}/quality/patch-plan
figure://{name}/quality/patch-result
```

Resource reads return metadata or JSON text descriptors only. They must not
stream PDF, PNG, TIFF, or arbitrary source file bytes.

MCP tools must preserve the existing envelope shape used by
`figure_agent_status`, including `schema`, `success`, `artifacts`,
`duration_ms`, and structured `error` when applicable.

## Data Contracts

### Defect Ledger

Schema: `figure-agent.quality-defect-ledger.v1`

Each ledger entry:

```yaml
id: QD001
source: deterministic_audit | critique | loop | style_foundation | reference
evidence:
  - uri: figure://<name>/audit/text-boundary
  - node_id: checker:text_boundary
severity: blocker | action | advisory
owner: tool | host_vision | human
defect_class: label_offset | text_overlap | whitespace_balance | line_weight_style |
  svg_visual_polish | semantic_meaning | taste_decision | publication_gate
patchability:
  state: safe_candidate | assisted_only | human_required | unsupported
  reasons:
    - narrow label offset
affected_files:
  - examples/<name>/<name>.tex
freshness:
  status_input_hash: sha256:<hex>
  critique_input_hash: sha256:<hex>
  audit_evidence_graph_hash: sha256:<hex>
policy:
  version: figure-agent.quality-patch-policy.v1
  blocked_codes: []
```

Rules:

- ids must be deterministic for the same input set;
- one defect may cite many evidence nodes;
- `semantic_meaning`, `taste_decision`, and `publication_gate` are never
  `safe_candidate`;
- `safe_candidate` requires at least one concrete evidence pointer and one
  fixture-local affected file;
- ledger generation is read-only.

Severity semantics:

- `blocker`: prevents workflow/final/release progress in existing status policy;
- `action`: visible or mechanical issue that can be worked before release;
- `advisory`: useful information that must not block release by itself.

Owner semantics:

- `tool`: deterministic evidence can identify and verify the issue;
- `host_vision`: critique can identify the issue, but verification still needs
  rendered evidence or human review;
- `human`: taste, science, publication, or acceptance decision.

### Patch Plan

Schema: `figure-agent.quality-patch-plan.v1`

Patch plan fields:

```yaml
schema: figure-agent.quality-patch-plan.v1
fixture: <name>
plan_id: sha256:<hex>
created_from:
  defect_ledger_hash: sha256:<hex>
  audit_evidence_graph_hash: sha256:<hex>
  source_hashes:
    examples/<name>/<name>.tex: sha256:<hex>
operations:
  - id: OP001
    defect_id: QD001
    file: examples/<name>/<name>.tex
    operation_type: tikz_coordinate_adjust | tikz_style_replace |
      tikz_macro_adoption | svg_polish_recipe
    selector:
      kind: line_range | command_id | node_name | svg_selector
      value: <stable selector>
      confidence: exact | bounded | ambiguous
    proposed_change:
      summary: <short human-readable change>
      patch: <unified diff or structured operation>
    bounds:
      max_translate_px: 10
      allowed_style_names:
        - <style>
    semantic_guard:
      allowed: true
      reason: <why this is mechanical only>
verification:
  required_commands:
    - fig-agent compile <name> --strict
    - fig-agent status <name> --json
  success_metrics:
    - resolved_defect_ids:
        - QD001
    - no_new_blockers: true
rollback:
  strategy: reverse_patch
```

Rules:

- plans must be fixture-local;
- source hashes must match before apply;
- operation selectors must be stable enough to fail closed;
- broad regex rewriting is forbidden;
- every operation must include a semantic guard;
- plans may include at most one source file in Phase 1;
- plans include both structured operations and human-readable unified diffs, but
  structured operations are authoritative.
- `selector.confidence: ambiguous` blocks apply;
- `plan_id` is computed from canonical JSON of fixture, operations, source
  hashes, policy version, and verification commands.

Allowed plan targets in Phase 1:

- `examples/<name>/<name>.tex`
- `examples/<name>/polish/svg_polish_recipe.yaml` only when the existing SVG
  polish route is already active and fresh

Forbidden plan targets:

- `critique.md`
- `accepted.*`
- `QUALITY_AUDIT.md`
- `exports/`
- `build/`
- `publication*`
- files outside the fixture

### Patch Result

Schema: `figure-agent.quality-patch-result.v1`

Patch result fields:

```yaml
schema: figure-agent.quality-patch-result.v1
fixture: <name>
plan_id: sha256:<hex>
applied: true | false
changed_files:
  - examples/<name>/<name>.tex
before:
  status_hash: sha256:<hex>
  audit_summary_hash: sha256:<hex>
after:
  status_hash: sha256:<hex>
  audit_summary_hash: sha256:<hex>
outcome: improved | unchanged | regressed | verification_failed |
  rollback_required
rollback_patch: <fixture-local path>
verification_commands:
  - command: fig-agent compile <name> --strict
    returncode: 0
  - command: fig-agent status <name> --json
    returncode: 0
```

Outcome semantics:

- `improved`: at least one targeted defect resolved, no new blocker introduced,
  and status freshness did not regress;
- `unchanged`: patch applied and verification ran, but targeted defects remain;
- `regressed`: new blocker or worse audit state appears;
- `verification_failed`: required command failed before outcome comparison;
- `rollback_required`: regression or source/apply inconsistency requires
  operator rollback.

## Architecture

### Layer 1: Defect Normalization

New module:

- `scripts/quality_defect_ledger.py`

Inputs:

- `status.infer_stage(example_dir)`;
- `audit_evidence_summary.summarize_audit_evidence(example_dir)`;
- `audit_evidence_graph.build_audit_evidence_graph(name, ...)`;
- critique findings and adjudication output when present;
- optional `aesthetic_intent.yaml` and `figure-design-philosophy.md` references.

Output:

- normalized read-only defect ledger.

This layer should not decide patches. It only says what evidence exists and how
the defect is classified.

The ledger should ingest current `auto_patch_eligibility` data from `fig_loop`
when available, but it must not change `fig_loop`'s existing output contract in
Phase 1.

### Layer 2: Patchability Policy

New module:

- `scripts/quality_patch_policy.py`

Responsibilities:

- wrap and gradually replace keyword-only eligibility in `fig_loop_auto_patch.py`
  with a structured policy that still defaults to no edit;
- classify defects into `safe_candidate`, `assisted_only`, `human_required`, or
  `unsupported`;
- explain blocked reasons in stable machine-readable codes.

Safe candidates in Phase 1:

- one-label coordinate nudges;
- style token replacement from inline TikZ values to known style names;
- small whitespace moves where only non-semantic decoration shifts;
- SVG visual polish only through the existing recipe/executor route.

Always blocked:

- chemistry topology;
- mechanism arrows or causal direction;
- data values;
- legend/category meaning;
- paper claim alignment;
- accepted/golden/publication state;
- critique/adjudication mutation.

### Layer 3: Patch Planning

New module:

- `scripts/quality_patch_plan.py`

Responsibilities:

- convert safe ledger entries into patch plans;
- include source hashes, selectors, semantic guards, and verification commands;
- fail closed when selector confidence is low;
- produce structured operations instead of broad free-form edits.

The planner may emit unified diffs, but the source of truth should be the
structured operation. Unified diffs are for human review and apply mechanics.

Selector requirements:

- `line_range` selectors must include the original text hash for the selected
  range;
- `command_id` and `node_name` selectors must match exactly one target;
- `svg_selector` must reuse the existing SVG polish selector constraints;
- ambiguous or zero-match selectors must produce `selector_ambiguous`, not a
  best-effort patch.

### Layer 4: Apply And Verify

New module:

- `scripts/quality_patch_apply.py`

Responsibilities:

- dry-run plan validation;
- explicit apply with source hash checks;
- write rollback patch;
- run required verification;
- emit patch result.

This module may mutate source only under `--apply`. It must never write accepted,
golden, export, publication, or critique decision files.

Apply must use a fixture-local mutation lock under:

```text
examples/<name>/build/.quality-locks/mutation.lock
```

If another compile/export/MCP mutation lock exists, apply must fail with
`operation_in_progress`.

Integration requirement:

- reuse or share policy with existing `fig_loop_patch_executor.py` where possible;
- do not create a second rollback format when the existing patch evidence format
  can represent the same information;
- if a new rollback artifact is required, document how it maps to existing
  `patch-evidence` and `patch-apply` schemas.

### Layer 5: CLI/MCP Facade

CLI:

- `bin/fig-agent` routes public commands to scripts.

MCP:

- `mcp/figure_agent_server.py` exposes quality-map/propose/verify as structured
  envelopes.
- MCP apply is out of scope for Phase 1.

All operator-facing command strings emitted by driver/docs must prefer
`fig-agent ...`. Workspace-relative `uv run python3 scripts/...` and
`bash scripts/...` strings remain forbidden for Cowork-facing paths.

### Layer 6: Governance

Any implementation that adds these schemas must also update the Issue 100 schema
module map and release-contract tests:

- `figure-agent.quality-defect-ledger.v1`
- `figure-agent.quality-patch-policy.v1`
- `figure-agent.quality-patch-plan.v1`
- `figure-agent.quality-patch-result.v1`

The release inventory count must be updated in the same change that adds new
script or test files.

## Improvement Strategy

### Phase 1: Read-Only Quality Map

Implement:

- `quality_defect_ledger.py`;
- CLI `quality-map`;
- MCP `figure_agent_quality_map`;
- tests for deterministic ids, fixture-local paths, and blocked semantic
  classes.

Acceptance:

- no file writes;
- ledger explains at least deterministic audit findings and first blocker;
- output references audit evidence graph nodes;
- existing fixtures without critique still produce a valid ledger with explicit
  missing/stale evidence entries rather than raising.

### Phase 2: Proposal-Only Patch Plans

Implement:

- `quality_patch_policy.py`;
- `quality_patch_plan.py`;
- CLI `propose`;
- MCP `figure_agent_propose_patch`.

Acceptance:

- at least one synthetic fixture produces a safe coordinate/style patch plan;
- semantic and taste defects produce explicit refusal;
- plans include source hashes and verification commands;
- no source edits;
- plan output is deterministic under repeated runs with unchanged inputs.

### Phase 3: Explicit Apply And Verification

Implement:

- `quality_patch_apply.py`;
- CLI `apply-plan --dry-run`;
- CLI `apply-plan --apply`;
- CLI/MCP `verify-plan`.

Acceptance:

- stale source hash refuses apply;
- apply writes only fixture source and rollback artifact;
- strict compile/status run after apply;
- result classifies improvement/regression;
- concurrent apply attempts fail rather than interleave.

### Phase 4: Real-Manuscript Dogfood

Run one synthetic manuscript-like fixture first, then use the next non-fig1
manuscript fixture.

Procedure:

1. run quality-map;
2. run propose;
3. user reviews plan;
4. apply one safe mechanical patch;
5. compile/status;
6. record whether manual bookkeeping decreased.

Acceptance:

- no fig1 source changes;
- no accepted/golden/publication changes;
- improvement measured by resolved deterministic/audit defect or clearer
  next-action state.

## Error Model

Stable error categories:

- `fixture_missing`
- `workspace_missing`
- `stale_plan`
- `unsupported_defect`
- `unsafe_patch`
- `selector_ambiguous`
- `source_hash_mismatch`
- `verification_failed`
- `rollback_required`
- `dependency_missing`
- `operation_in_progress`
- `invalid_plan`
- `plan_target_forbidden`
- `plan_output_forbidden`

All CLI and MCP errors should include:

- category;
- human-readable message;
- next action;
- fixture-relative path if applicable.

## Safety Rules

1. Read-only commands must not create files.
2. Apply requires explicit `--apply`.
3. MCP apply is disabled in Phase 1.
4. Plans must stay inside `FIGURE_AGENT_WORKSPACE/examples/<name>`.
5. Symlinks that resolve outside the fixture are blocked.
6. Every mutation must have a rollback path.
7. Source hash mismatch blocks apply.
8. Critique, accepted, golden, publication, export, and build artifacts are not
   source-patch targets.
9. Any semantic uncertainty routes to human review.
10. Aesthetic score changes are advisory and cannot prove success alone.
11. Generated plan files must be under `build/quality/`.
12. Patch operations must be idempotence-checked: applying the same plan twice
    must refuse on source hash mismatch or already-applied detection.
13. The apply command must fail closed if verification cannot run.

## Threat Model

The quality loop handles user-authored figure source. It must defend against:

- fixture names that escape `examples/<name>`;
- symlinks from fixture files to external paths;
- plan files that point at arbitrary workspace paths;
- stale plans generated before source or critique changed;
- ambiguous selectors that edit the wrong TikZ/SVG element;
- MCP hosts invoking tools from plugin root instead of user workspace;
- generated build/export/cache artifacts being packaged into Cowork ZIPs.

Every threat above needs a contract test before the feature is considered
releaseable.

## Testing Plan

### Unit Tests

- ledger id determinism;
- evidence graph node references;
- semantic/taste/publication defects blocked;
- allowed mechanical defect classified as `safe_candidate`;
- path escape and symlink escape blocked;
- patch plan hash changes when source changes;
- stale plan refuses apply;
- rollback patch is generated;
- plan target allowlist rejects `critique.md`, `exports/`, `build/`, and
  external paths;
- applying the same plan twice fails closed;
- mutation lock rejects concurrent apply.

### CLI Contract Tests

- `fig-agent quality-map smoke_trap_demo --json`;
- `fig-agent propose smoke_trap_demo --json`;
- `fig-agent apply-plan smoke_trap_demo --plan ... --dry-run`;
- `fig-agent apply-plan smoke_trap_demo --plan ... --apply` only mutates the
  expected fixture source;
- safe commands emitted by docs and drivers prefer `fig-agent ...`;
- `propose --output ../outside.yaml` is rejected;
- `apply-plan --plan build/quality/patch_plan.yaml --apply` refuses stale source
  hashes.

### MCP Tests

- startup/list-tools remains side-effect-free;
- quality-map/propose return structured envelopes;
- MCP proposal is read-only;
- malformed fixture names rejected before path join;
- resource metadata does not stream binary artifact bytes;
- MCP quality tools preserve structured envelope fields;
- MCP cannot apply source mutations in this release.

### Dogfood Tests

- synthetic fixture with known label overlap produces a plan and verifies clean;
- real non-fig1 fixture dogfood records before/after audit delta;
- fig1 remains unchanged.

## Release Gate Additions

Extend `release_gate.py` targeted tests with:

- `tests/test_quality_defect_ledger.py`;
- `tests/test_quality_patch_policy.py`;
- `tests/test_quality_patch_plan.py`;
- `tests/test_quality_patch_apply.py`;
- MCP quality facade tests.

Package audit must include new scripts and exclude generated patch artifacts
under examples.

`release_gate.py` must fail if generated quality artifacts or rollback patches
appear inside the Cowork ZIP.

## Design Decisions

1. Patch plans include both structured operations and human-readable unified
   diffs. Structured operations are authoritative.
2. Dogfood order is synthetic manuscript-like fixture first, then the next
   non-fig1 manuscript fixture.
3. MCP write opt-in is not implemented in this release. MCP remains
   read/propose/verify-only until CLI apply has real dogfood evidence.
4. Phase 1 does not change critique schema. It consumes existing critique and
   loop evidence.
5. Phase 1 does not change `/fig_improve`; it may later call `quality-map` and
   `propose` after the CLI contracts are proven.

## Review Checklist

- No autonomous taste decision is introduced.
- No MCP default mutation is introduced.
- Every source mutation has explicit apply, source hash check, verification, and
  rollback.
- Quality improvement is measured by resolved defects or clearer readiness
  state, not by aesthetic score alone.
- Existing Cowork/plugin install behavior remains unchanged.
- Fig1 frozen reference is not modified by the dogfood phase.
