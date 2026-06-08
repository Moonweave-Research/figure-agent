# Quality Memory and Benchmark Engine Design

Status: draft for review

Target: figure-agent 0.12.x after candidate rendering, evidence-gated apply, and
closeout-ready stabilize

## Summary

The current figure-agent can package as a plugin, expose a conservative MCP
facade, generate/render/rank bounded candidates, apply a selected candidate with
explicit evidence, and close out a real manuscript fixture through
`closeout-ready`.

That still does not make the agent consistently better at drawing. The missing
system layer is memory and measurement:

```text
candidate attempt -> rendered evidence -> human/closeout outcome
  -> reusable local quality memory
  -> benchmark score across fixed fixtures
  -> better future candidate generation/ranking
```

This spec defines a local-only quality memory and benchmark engine. Its purpose
is to make figure-agent learn from its own successful and failed candidate
runs without adding model training, external services, hidden global state, or
unsafe source mutation.

The product goal is practical:

> When figure-agent proposes a patch, it should know which kinds of edits have
> actually improved similar figures before, and it should prove improvement on
> a fixed benchmark before claiming progress.

## Current Baseline

Already implemented or available:

- `fig-agent candidates`, `render-candidates`, `rank-candidates`,
  `review-candidate`, `accept-candidate`, `apply-candidate`.
- `fig-agent evidence-sync`, `closeout-ready`, and `closeout-accept`.
- `fig-agent quality-map`, `propose`, `apply-plan`, and `verify-plan`.
- MCP tools for read-only analysis/proposal/ranking and guarded candidate
  workflows.
- Deterministic evidence from compile, status, export freshness,
  visual-clash, text-boundary, label-path, undeclared-geometry, perception
  packs, critique, crop audits, and closeout.
- A real dogfood fixture, `fig1_overview_v2_pair_001_vault`, has reached
  `closeout-ready status=ready`.

Observed limitations:

- `candidate_rank.py` currently gives most soft scores fixed zero or fixed
  review-burden values; ranking is not yet evidence-rich enough to select better
  drawings reliably.
- Candidate runs do not accumulate reusable outcome evidence.
- There is no benchmark command that says whether a new engine change improved
  or regressed figure quality across a fixed fixture set.
- Host vision critique remains a deliberate host boundary. The engine must not
  pretend it can fully automate visual judgment without a human/host review
  artifact.
- Existing local user manuscript files such as `caption.md` may be dirty and
  must not be silently packaged, overwritten, or used as hidden training state.

## Goals

1. Record every candidate attempt, render, rank, acceptance, apply, rollback,
   and closeout outcome as fixture-local structured memory.
2. Build a local quality memory index that summarizes which edit families,
   panels, defect types, and evidence patterns improved or regressed figures.
3. Add a benchmark runner over a fixed local fixture manifest so engine changes
   can be compared by deterministic metrics.
4. Feed memory-derived priors into candidate ranking without overriding hard
   gates or human approval boundaries.
5. Keep all memory local to the workspace or repo-controlled benchmark fixtures.
6. Expose read-only MCP tools for memory summaries and benchmark reports.
7. Preserve explicit CLI apply/acceptance semantics for all mutation.

## Non-Goals

- Do not train a neural model.
- Do not call external vision, embedding, search, or image-generation APIs.
- Do not write anything under Google Drive, CloudStorage, or user home cache
  paths.
- Do not use cross-project manuscript data unless the benchmark manifest
  explicitly lists a fixture under the current workspace.
- Do not make MCP decide accepted/golden/publication state.
- Do not let memory override deterministic hard gates.
- Do not invent scientific claims from captions, references, or prior runs.
- Do not make fig1 mutable as a hidden training corpus. It may be a benchmark
  case only when explicitly listed in the benchmark manifest.

## Product Principle

The engine should improve by remembering evidence, not by becoming bolder.

Useful output:

- "Label-offset candidates in dense Panel C energy diagrams often pass when
  they reduce label-path proximity without changing semantic anchors."
- "SVG polish route for this fixture family has not shown enough repeated gain;
  keep using TikZ source edits."
- "This new ranking function improved 3/5 benchmark cases and regressed 1 case;
  block release until the regression is explained."

Bad output:

- "This looks nicer, apply it."
- "Prior manuscript style suggests changing the science."
- "The model learned from unrelated local files."

## Public Interfaces

### CLI

Add these commands to `plugins/figure-agent/bin/fig-agent`:

```text
fig-agent memory-log <name> --json
fig-agent memory-index (--fixture <name> | --suite <suite>) [--write] --json
fig-agent benchmark-list --json
fig-agent benchmark-run --suite <suite> [--limit N] [--render] [--write] --json
fig-agent benchmark-compare <baseline-run> <candidate-run> --json
fig-agent rank-candidates <name> --candidate-set <path> --use-memory --json
```

Rules:

- `memory-log` is read-only. It scans one fixture and emits normalized event
  records from existing candidate and closeout artifacts in the first slice.
  Evidence-index and loop-checkpoint ingestion are planned extensions under the
  same schema and must remain read-only.
- `memory-index` requires exactly one scope: `--fixture <name>` or
  `--suite <suite>`. There is no implicit "all fixture" mode.
- `memory-index --fixture <name> --write` writes only
  `examples/<name>/build/memory/quality_memory_index.json` for a selected
  fixture.
- `memory-index --suite <suite> --write` writes only
  `.scratch/figure-agent-memory/<suite>/quality_memory_index.json`. Suite
  indexing skips missing fixtures with diagnostics and never creates fixtures.
- `benchmark-run --write` writes only under
  `.scratch/figure-agent-benchmarks/<run_id>/`.
- `benchmark-run` is lightweight by default. It runs status, candidate
  generation, and ranking. It renders candidates only when `--render` is
  explicitly passed.
- `rank-candidates --use-memory` may adjust soft ranking only. It must never
  upgrade rejected or review-only candidates to apply-eligible.
- Commands must use `runtime_paths` and existing fixture path validation.

### MCP

Expose only read-only memory and benchmark surfaces first:

- `figure_agent_memory_summary`
- `figure_agent_benchmark_list`
- `figure_agent_benchmark_run_preview`
- `figure_agent_benchmark_compare`

MCP must not expose `memory-index --write` or `benchmark-run --write` until the
CLI path has dogfood evidence and a separate opt-in flag is designed.

## Data Model

### Memory Event

Schema: `figure-agent.quality-memory-event.v1`

Each event is derived from an existing artifact. The memory layer must not
invent events.

```json
{
  "schema": "figure-agent.quality-memory-event.v1",
  "fixture": "fig1",
  "event_id": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "event_type": "candidate_rendered",
  "created_at": "2026-06-08T00:00:00Z",
  "source_artifact": "build/candidates/CAND001/render_manifest.json",
  "candidate_id": "CAND001",
  "edit_family": "label_offset",
  "target": {"panel": "C", "subregion": "energy_diagram"},
  "pre_state": {
    "render_state": "FRESH",
    "critique_state": "FRESH",
    "export_state": "TRACKED_GOLDEN"
  },
  "post_state": {
    "compile": "success",
    "export": "success",
    "status": "success"
  },
  "outcome": {
    "state": "reviewed_not_applied",
    "reason": "human preferred baseline",
    "evidence_paths": [
      "build/candidates/CAND001/candidate_manifest.json",
      "build/candidates/CAND001/render_manifest.json"
    ]
  },
  "metrics": {
    "new_visual_clash_count": 0,
    "new_text_boundary_count": 0,
    "candidate_rank_score": 0.75
  }
}
```

Allowed `event_type` values:

- `candidate_generated`
- `candidate_rendered`
- `candidate_ranked`
- `candidate_accepted`
- `candidate_applied`
- `candidate_rejected`
- `candidate_rolled_back`
- `closeout_accepted`
- `closeout_ready`
- `loop_checkpoint`

Allowed `outcome.state` values:

- `improved`
- `neutral`
- `regressed`
- `reviewed_not_applied`
- `blocked_by_hard_gate`
- `blocked_by_human_gate`
- `unknown`

Unknown is allowed only when the source artifact lacks outcome evidence. Unknown
events may be indexed for counting but must not influence ranking priors.

### Quality Memory Index

Schema: `figure-agent.quality-memory-index.v1`

```json
{
  "schema": "figure-agent.quality-memory-index.v1",
  "generated_at": "2026-06-08T00:00:00Z",
  "scope": {"kind": "fixture", "fixture": "fig1"},
  "event_count": 12,
  "eligible_prior_count": 5,
  "families": {
    "label_offset": {
      "attempts": 4,
      "improved": 2,
      "regressed": 0,
      "blocked": 1,
      "median_rank_delta": 0.12,
      "recommended_prior": 0.65
    }
  },
  "panel_patterns": {
    "C:energy_diagram:label_offset": {
      "attempts": 2,
      "improved": 1,
      "regressed": 0,
      "notes": ["low regression in dense diagram labels"]
    }
  },
  "disallowed_priors": [
    {
      "key": "semantic_rewrite",
      "reason": "semantic edit families cannot receive apply priors"
    }
  ]
}
```

The index must include enough raw counts that a reviewer can see why a prior was
computed. No opaque score-only memory is allowed.

### Benchmark Suite Manifest

Create:

```text
plugins/figure-agent/benchmarks/quality_suites.yaml
```

Initial content:

```yaml
schema: figure-agent.quality-benchmark-suites.v1
suites:
  smoke:
    description: Fast synthetic fixtures for ranking and safety contracts.
    fixtures:
      - smoke_trap_demo
  dogfood:
    description: Local dogfood fixtures with real manuscript complexity.
    fixtures:
      - fig1_overview_v2_pair_001_vault
```

The benchmark runner must skip missing fixtures with a structured diagnostic
instead of creating fixtures or searching outside `workspace_root/examples/`.

### Benchmark Run

Schema: `figure-agent.quality-benchmark-run.v1`

```json
{
  "schema": "figure-agent.quality-benchmark-run.v1",
  "run_id": "20260608T000000Z-smoke",
  "suite": "smoke",
  "fixture_count": 1,
  "results": [
    {
      "fixture": "smoke_trap_demo",
      "status": "completed",
      "candidate_count": 3,
      "rendered_count": 0,
      "ranked_count": 3,
      "render_mode": "none",
      "hard_gate_failures": [],
      "best_candidate": "CAND001",
      "memory_prior_used": false,
      "metrics": {
        "compile_success_rate": 1.0,
        "render_success_rate": 1.0,
        "new_blocker_count": 0,
        "mean_rank_score": 0.58
      }
    }
  ],
  "summary": {
    "completed": 1,
    "skipped": 0,
    "failed": 0,
    "regression_count": 0
  }
}
```

## Ranking Memory Rules

Memory may change only these fields in `figure-agent.candidate-score.v1`:

- `scores.memory_prior`
- `scores.review_burden`
- `rank_score`
- `evidence.positive`
- `evidence.negative`

Memory must not change:

- `hard_gate_state`
- `hard_gate_failures`
- `effective_apply_authority`
- `verdict` when hard gate is rejected
- any candidate operation

Ranking adjustment:

```text
memory_prior = clamp((improved + 0.5 * neutral - regressed) / attempts, -0.25, 0.25)
rank_score = base_rank_score + memory_prior - review_burden_penalty
```

Minimum evidence:

- At least 3 eligible prior events are required before memory affects ranking.
- Regressed events count even if later rolled back.
- Events with `outcome.state=unknown` are ignored for priors.
- Events from a different fixture may contribute only if the same
  `edit_family`, `panel role`, and `defect class` are present.

## Safety Requirements

- All paths must resolve inside either:
  - `workspace_root/examples/<name>/`; or
  - repo-local `.scratch/figure-agent-benchmarks/`; or
  - repo-local `.scratch/figure-agent-memory/`.
- No command writes under `~/Library/CloudStorage`, Google Drive, home-level
  caches, or plugin installed cache.
- Symlinked `build`, `build/memory`, benchmark run directories, event source
  artifacts, and output files are rejected.
- Benchmark runs are append-only by `run_id`; rerunning the same `run_id`
  requires `--overwrite` and is not exposed in MCP.
- Dirty user fixture files are never staged or packaged by benchmark commands.
- Memory index generation is deterministic except `generated_at`; tests should
  normalize timestamps or pass an injected clock.

## Implementation Plan

### Task 1: Memory Event Extractor

Files:

- Create `plugins/figure-agent/scripts/quality_memory_events.py`
- Test `plugins/figure-agent/tests/test_quality_memory_events.py`
- Modify `plugins/figure-agent/bin/fig-agent`

Responsibilities:

- Extract memory events from:
  - `build/candidates/*/candidate_manifest.json`
  - `build/candidates/*/render_manifest.json`
  - `build/candidates/*/acceptance.json`
  - `build/candidates/*/apply_result.json`
  - `build/closeout/golden_acceptance.json`
- Defer these artifact classes until after candidate/closeout memory is stable:
  - `build/evidence/evidence_index.json`
  - latest `.scratch/fig-loop-runs/*-<name>/iteration_001.json`
- Validate source artifact paths and reject symlink escapes.
- Emit `figure-agent.quality-memory-event.v1`.
- Add `fig-agent memory-log <name> --json`.

Tests:

- Missing optional artifacts produce an empty event list, not a failure.
- Symlinked candidate sandbox is rejected.
- Applied candidate with successful post-apply produces `candidate_applied`.
- Stale apply result produces `blocked_by_hard_gate`.
- Closeout-ready fixture produces `closeout_ready`.

### Task 2: Memory Index Builder

Files:

- Create `plugins/figure-agent/scripts/quality_memory_index.py`
- Test `plugins/figure-agent/tests/test_quality_memory_index.py`
- Modify `plugins/figure-agent/bin/fig-agent`

Responsibilities:

- Consume event lists and aggregate by edit family, panel role, defect class,
  and fixture.
- Count raw `event_count` separately from outcome `attempts`; generated events
  and fixture-level closeout events must not inflate candidate-family attempts.
- Compute conservative priors only when minimum evidence is met.
- Add `fig-agent memory-index (--fixture <name> | --suite <suite>) [--write] --json`.
- Write fixture-local index only to
  `examples/<name>/build/memory/quality_memory_index.json`.
- Add `--suite <suite>` as the only non-fixture indexing scope.
- Write suite index only to
  `.scratch/figure-agent-memory/<suite>/quality_memory_index.json`.
- Reject invocations that omit both scope flags or pass both scope flags.

Tests:

- Fewer than 3 eligible events yields `eligible_prior_count=0`.
- Regressed event reduces prior.
- Unknown outcomes do not affect prior.
- Symlinked `build/memory` output is rejected.
- `--write` writes only the index file.

### Task 3: Memory-Aware Candidate Ranking

Files:

- Modify `plugins/figure-agent/scripts/candidate_rank.py`
- Test `plugins/figure-agent/tests/test_candidate_rank.py`
- Modify `plugins/figure-agent/bin/fig-agent`

Responsibilities:

- Add `--use-memory` to `fig-agent rank-candidates`.
- Load memory index when present.
- Add `scores.memory_prior`.
- Adjust `rank_score` only for reviewable candidates.
- Preserve hard gate and effective apply authority exactly.

Tests:

- Memory prior changes rank order for two passing candidates.
- Rejected candidate remains rejected even with positive prior.
- Missing memory index leaves existing score unchanged.
- Negative prior lowers score and adds negative evidence.

### Task 4: Benchmark Suite Runner

Files:

- Create `plugins/figure-agent/benchmarks/quality_suites.yaml`
- Create `plugins/figure-agent/scripts/quality_benchmark.py`
- Test `plugins/figure-agent/tests/test_quality_benchmark.py`
- Modify `plugins/figure-agent/bin/fig-agent`

Responsibilities:

- Add `fig-agent benchmark-list --json`.
- Add `fig-agent benchmark-run --suite <suite> [--limit N] [--render] [--write] --json`.
- For each fixture:
  - run status;
  - build candidate set;
  - render candidates only when `--render` is passed;
  - rank candidates with and without memory;
  - collect deterministic metrics.
- In preview mode, do not write benchmark run artifacts.
- In write mode, write only under `.scratch/figure-agent-benchmarks/<run_id>/`.

Tests:

- Missing fixture is skipped with `status=skipped`.
- Preview mode is read-only.
- Default preview and write modes do not render candidates unless `--render` is
  passed.
- Write mode refuses symlinked benchmark run directory.
- `--limit 1` runs exactly one fixture.
- Benchmark output schema is stable.

### Task 5: Benchmark Compare

Files:

- Extend `plugins/figure-agent/scripts/quality_benchmark.py`
- Test `plugins/figure-agent/tests/test_quality_benchmark_compare.py`
- Modify `plugins/figure-agent/bin/fig-agent`

Responsibilities:

- Add `fig-agent benchmark-compare <baseline-run> <candidate-run> --json`.
- Compare:
  - fixture completion;
  - candidate count;
  - render success rate;
  - hard gate failures;
  - new blocker count;
  - rank score movement;
  - regression count.
- Emit `figure-agent.quality-benchmark-comparison.v1`.

Tests:

- Candidate run with new hard gate failure reports regression.
- Missing run path is rejected.
- Run paths outside `.scratch/figure-agent-benchmarks/` are rejected.
- Identical runs report zero regression.

### Task 6: MCP Read-Only Surfaces

Files:

- Modify `plugins/figure-agent/mcp/figure_agent_server.py`
- Test `plugins/figure-agent/tests/test_mcp_facade.py`

Responsibilities:

- Add:
  - `figure_agent_memory_summary`
  - `figure_agent_benchmark_list`
  - `figure_agent_benchmark_run_preview`
  - `figure_agent_benchmark_compare`
- Do not expose write flags.
- Return existing MCP envelopes with stable error categories.

Tests:

- `tools/list` exposes read-only tools.
- Schemas do not include `write`, `overwrite`, or arbitrary path fields.
- Startup/list-tools remains side-effect free.
- Preview benchmark call does not create `.scratch/figure-agent-benchmarks`.

### Task 7: Release Gate and Dogfood

Files:

- Modify `plugins/figure-agent/scripts/release_gate.py`
- Modify or add release contract tests as needed.
- Update command docs only if the public surface is stable.

Responsibilities:

- Add targeted tests to release gate.
- Run dogfood:
  - `fig-agent memory-log fig1_overview_v2_pair_001_vault --json`
  - `fig-agent memory-index --fixture fig1_overview_v2_pair_001_vault --write --json`
  - `fig-agent benchmark-run --suite smoke --write --json`
  - `fig-agent benchmark-run --suite smoke --render --write --json`
  - `fig-agent benchmark-compare <run> <run> --json`
- Verify no writes outside allowed directories.

Done condition:

- Focused pytest passes.
- Ruff passes.
- `git diff --check` passes.
- Dogfood commands complete.
- `git status --short` shows no unintended user fixture files staged.

## Acceptance Criteria

The feature is complete when:

1. `fig-agent memory-log <name> --json` returns event records for a fixture with
   candidate/closeout evidence.
2. `fig-agent memory-index --fixture <name> --write --json` writes only
   `build/memory/quality_memory_index.json`.
3. `fig-agent rank-candidates <name> --candidate-set <path> --use-memory --json`
   includes memory evidence without changing hard gates.
4. `fig-agent benchmark-run --suite smoke --write --json` writes a lightweight
   non-rendering benchmark run under `.scratch/figure-agent-benchmarks/`.
5. `fig-agent benchmark-compare <run> <run> --json` reports no regression for
   identical runs.
6. MCP exposes only read-only memory/benchmark tools.
7. Symlink/path escape tests cover fixture memory writes and benchmark writes.
8. Dogfood on `fig1_overview_v2_pair_001_vault` produces a memory summary
   without modifying `caption.md` or accepted source files.

## Review Checklist

- Does every write path use `runtime_paths` or fixture-local helpers?
- Can a dirty user file become memory input without an explicit artifact path?
- Can memory ever upgrade `effective_apply_authority`?
- Can MCP trigger a write?
- Can benchmark paths escape through symlinks?
- Are unknown outcomes excluded from priors?
- Does benchmark compare catch regressions rather than only reporting averages?
- Does dogfood prove usefulness without reopening frozen fig1 source edits?

## Open Questions

1. Should the dogfood suite include only fixtures already present in the plugin
   repo, or should it support user-provided suite manifests later?
2. Should memory indices be checked into git for synthetic fixtures, or always
   treated as generated artifacts?
3. What threshold should block release: any regression, or only regression in a
   required fixture?

Default answers for first implementation:

- Use only repo-local suite manifests.
- Treat memory indices and benchmark runs as generated artifacts.
- Block release on any hard-gate regression in the smoke suite; report but do
  not block on dogfood fixture optional polish metrics until enough evidence
  accumulates.
