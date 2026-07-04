# Architecture v0.11 — Global Quality Search Loop

**Date**: 2026-07-04
**Status**: proposed direction after fig1 v5f loop dogfood

## Decision

Add a global quality-search layer above the existing quality kernel. The layer
does not replace `/fig_compile`, `/fig_critique`, `/fig_loop`, candidate
rendering, adjudication, or release gates. It coordinates them as an explicit
search process:

1. observe current figure state and detector evidence;
2. choose a bounded set of patch hypotheses;
3. render candidates in isolated lanes;
4. score candidates with deterministic metrics, critique evidence, and
   regression gates;
5. apply only the best reviewable patch or stop with a named basin/tool defect;
6. write learning events that improve the next search.

The product goal is not "fully automatic taste." The goal is repeatable
manuscript-figure improvement with visible evidence, rollback boundaries, and a
separate record of tool defects discovered while iterating.

## Why Now

The fig1 v5f dogfood exposed three system facts:

- The kernel can prove freshness, audit accounting, compile/export state, and
  release boundaries.
- Local loop routing can still confuse quality iteration with human acceptance.
- Once a loop repeatedly reports the same high-level aesthetic bottleneck,
  another local micro-patch is usually low value unless the system changes the
  search strategy.

That means the next step is not more manual gate prose. It is a search
algorithm that treats figure improvement as a sequence of controlled
experiments.

## Algorithm: GQSL

GQSL means **Global Quality Search Loop**. It is a repo-local, evidence-driven
optimization loop over editable figure source.

High-level pseudocode:

```text
state = observe(fixture)
while budget remains:
  if hard_gate_missing(state):
    run safe prerequisite or stop at required actor

  actions = propose_patch_hypotheses(state, memory, basin)
  candidates = render_isolated(actions)
  scored = score(candidates, state, memory)
  decision = select(scored, acceptance_policy)

  if decision.kind == apply_patch:
    apply_to_source(decision.patch)
    run compile -> critique scaffold/check -> adjudication -> loop
    memory.record(success/failure/tool_defects)
    state = observe(fixture)
    continue

  if decision.kind == step_out:
    memory.record(basin/tool_gap)
    stop with next experiment recommendation

  stop with no_actionable_improvement
```

This is closer to black-box optimization, evolutionary search, and contextual
bandits than to a single deterministic checker. The figure source is the
environment, patch families are actions, compile/render/critique are the reward
measurement pipeline, and the memory ledger is the learned prior.

## State Vector

The search state is assembled from existing surfaces:

- `/fig_status`: render, critique, adjudication, export, release, and freshness.
- `/fig_loop`: active patch target, basin signal, aesthetic summaries, crop
  uncertainty, top-tier summaries, and detector accounting.
- detector reports: collision, visual clash, text boundary, label-path,
  undeclared geometry, physics grounding, TeX assertions.
- visual metrics: print legibility, density, scaffold load, panel hierarchy,
  stroke rhythm, palette restraint, and changed-pixel ratios.
- candidate history: family success rate, rejected patches, regressions, and
  detector false-positive patterns.

The state must distinguish:

- **progress blockers**: stale render, stale critique, missing adjudication;
- **quality targets**: labels, apparatus credibility, panel hierarchy, density;
- **release blockers**: accepted/golden/final artifact decisions;
- **tool defects**: wrong stop boundary, false detector positives, unstable crop
  IDs, stale scaffold behavior.

## Action Space

Patch hypotheses are typed. The first implementation should support a small
catalog rather than free-form source mutation.

| Family | Typical target | Scope |
| --- | --- | --- |
| `label_reflow` | overlapping, cramped, or low-authority labels | one label cluster |
| `apparatus_strengthen` | weak instrument/device drawing | one apparatus group |
| `hierarchy_rebalance` | weak hero panel or equal-weight panels | one panel or row |
| `density_reduce` | repeated micro-labels or excess rulework | one panel |
| `mechanism_foreground` | result/mechanism hidden by apparatus | one panel |
| `stroke_palette_tune` | thin-stroke rhythm or color overload | bounded style region |
| `layout_macro_shift` | whitespace and panel breathing | declared subregion |

Each action must declare:

- target fixture and source line range;
- expected detector movement;
- expected visual metric movement;
- protected invariants;
- rollback condition;
- forbidden files.

No action may set accepted/golden/final state.

## Candidate Generation

GQSL should generate a small batch per iteration:

- one conservative patch from the current patch handoff;
- one stronger patch in the same family;
- one orthogonal patch family if basin history shows repeated failure;
- one null candidate that keeps the current source for regression comparison.

Candidates render in isolated candidate lanes or sandboxes. Generated build and
export artifacts stay ignored. The source lane is mutated only after the best
candidate passes hard gates and reviewability thresholds.

## Scoring

Scoring is multi-objective and advisory. A candidate is never accepted by score
alone.

Primary score components:

- hard gate: compile success, no source escape, no stale critique dependency;
- defect movement: target detector count improves without new blocker defects;
- visual metric movement: legibility, density, hierarchy, stroke rhythm;
- semantic preservation: physics grounding, TeX assertions, protected labels;
- regression budget: changed-pixel ratio enough for intended patch, not broad
  accidental churn;
- memory prior: patch-family success/failure history on similar fixtures;
- review burden: how much human/host review remains.

Selection policy:

```text
reject if hard gate fails
reject if semantic preservation regresses
prefer highest target improvement under regression budget
prefer lower review burden when scores tie
if all scores are marginal or basin repeats, step out
```

## Search Policy

Use a staged policy before adding anything more complex:

1. **Rule-based triage** for hard gates and obvious detector-linked defects.
2. **Contextual bandit** over patch families, using fixture type, panel type,
   detector signals, and prior family outcomes.
3. **Beam search** over 2-4 candidates per iteration for visible layout changes.
4. **Annealing/step-out** when the same bottleneck repeats: expand edit radius,
   switch family, or stop with a tool/critique defect.

This keeps the system practical. We do not need gradient descent; the render
pipeline is non-differentiable and expensive. We need disciplined proposal,
measurement, and learning.

## Tool-Defect Mining

Every loop iteration should emit a `tool_defect_candidates` section when the
workflow behaves suspiciously. Examples:

- a route marked `tikz_patch` becomes `human_gate_required`;
- a verify-only safe command is not executed by an executor that claims execute
  mode;
- crop IDs churn after a local label edit and invalidate unrelated critique
  accounting;
- detector candidates are fully accounted but status still reports an
  ungrounded blocker;
- repeated basin history is caused by stale or misclassified prior checkpoints.

Tool defects are not figure defects. They should be written to a separate
ledger with:

- symptom;
- command that exposed it;
- expected behavior;
- actual behavior;
- affected fixture;
- minimal reproduction;
- recommended fix or test.

## Proposed Interfaces

Initial read-only planner:

```bash
fig-agent quality-search <fixture> --goal "<goal>" --plan --json
```

Bounded executor:

```bash
fig-agent quality-search <fixture> --goal "<goal>" --execute --max-iterations 3
```

Learning digest:

```bash
fig-agent quality-memory <fixture> --json
```

The first implementation should make `--plan` useful before `--execute` exists.
It can reuse `fig_run`, `fig_loop`, `candidate_generator`, `candidate_render`,
`candidate_rank`, `quality_defect_ledger`, and `quality_memory_events`.

## Evidence Artifacts

Each run writes under `.scratch/quality-search-runs/<timestamp>-<fixture>/`:

- `state_000.json`;
- `patch_hypotheses.json`;
- `candidate_scores.json`;
- `decision.json`;
- `tool_defect_candidates.json`;
- `run_manifest.json`.

These are evidence, not authority. The authoritative source remains the figure
folder plus committed code/docs.

## Safety Boundaries

GQSL may:

- run status, compile, loop, non-golden draft export, candidate render, and
  read-only comparison commands;
- create candidate lanes or scratch evidence;
- apply one bounded source patch only after a passing candidate decision.

GQSL may not:

- set `accepted: true`;
- force golden exports;
- edit generated `exports/` as source of truth;
- hide unresolved critique findings;
- rewrite broad fixture metadata to make the status green;
- cross into unrelated examples.

## First Milestone

Build GQSL v0 as a planner only:

1. collect the state vector for one fixture;
2. classify current stop reason into progress blocker, quality target, release
   blocker, or tool defect;
3. propose 1-3 patch families with target line ranges when source mutation is
   appropriate;
4. propose a step-out experiment when basin repeats;
5. emit tool-defect candidates separately from figure defects.

Dogfood target: `fig1_overview_v5f_art_direction_001_vault`.

Success criteria:

- `quality-search --plan` does not say "human gate" when the issue is actually
  basin/tool-routing;
- it recommends a stronger family switch when typography authority repeats;
- it records the fig1 v5f route/execute/basin issues as tool-defect candidates;
- it leaves release blocked on explicit acceptance only.

## Later Milestones

v1:

- candidate batch generation for `label_reflow` and `apparatus_strengthen`;
- render and score isolated candidates;
- rank candidates with detector and visual metrics.

v2:

- bounded apply of one selected source patch;
- automatic post-apply compile/critique/adjudication/loop closeout;
- regression-aware rollback recommendation.

v3:

- learned patch-family priors across fixtures;
- benchmark suite integration;
- dashboard/queue reporting that separates quality improvement, release
  readiness, and tool-defect work.
