# Architecture v0.12 - Quality Search Execution Plan

**Status:** Historical evidence — non-authoritative.
**Superseded by:** `docs/product-spec.md` and `docs/execution-plan.md`.

**Date**: 2026-07-04
**Status at the time**: planning document after broad fig-agent analysis
**Fixture used for dogfood evidence**: `fig1_overview_v5f_art_direction_001_vault`

## Executive Decision

Do not create a separate figure agent.

Build a global quality-search executor inside the existing fig-agent. The
executor should reuse the current status, driver, loop, candidate, render,
rank, apply, memory, and defect-ledger modules as the pipeline stages of one
quality-improvement algorithm.

The missing part is not another local Panel F patch. The missing part is an
execution algorithm that can:

1. observe the whole fixture state;
2. classify release blockers separately from quality-search targets;
3. generate multiple candidate families at once;
4. render and score candidates in sandboxes;
5. apply only one bounded, evidence-backed source patch when gates pass;
6. record tool defects discovered during the loop.

This keeps fig-agent as the authority. The new work is orchestration plus
family adapters, not a replacement system.

## Current Evidence

The repo already has most of the safety and evidence surfaces needed for the
loop.

| Surface | Evidence | Current role |
| --- | --- | --- |
| Verify-only loop | `scripts/fig_loop.py:1` to `scripts/fig_loop.py:5` | Runs a read-only loop iteration and writes checkpoint evidence without source/export/acceptance mutation. |
| Basin separation | `scripts/fig_loop.py:202` to `scripts/fig_loop.py:214` | Repeated local failures can stop as `basin_detected` without requiring human acceptance. |
| Dry-run driver | `scripts/fig_driver.py:1` to `scripts/fig_driver.py:6` | Selects next action without mutating protected source/export/release surfaces. |
| Planner-only quality search | `scripts/quality/quality_search.py:1` to `scripts/quality/quality_search.py:6` | Observes status, loop, ledger, and memory, then separates blockers, targets, and tool defects. |
| Candidate generator | `scripts/candidates/candidate_generator.py:1` to `scripts/candidates/candidate_generator.py:40` | Generates deterministic improvement candidates, but currently the supported family is narrow. |
| Candidate sandbox render | `scripts/candidates/candidate_render.py:1` to `scripts/candidates/candidate_render.py:2` | Creates candidate sandbox manifests without touching source exports. |
| Candidate ranking | `scripts/candidates/candidate_rank.py:117` to `scripts/candidates/candidate_rank.py:176` | Scores hard-gated candidate manifests with render, detector, and memory priors. |
| Candidate apply | `scripts/candidates/candidate_apply.py:1` to `scripts/candidates/candidate_apply.py:2` | Applies one evidence-gated candidate source patch, with drift, render, and semantic checks. |
| Prior architecture | `docs/architecture-v0.11-global-quality-search-loop.md:40` to `docs/architecture-v0.11-global-quality-search-loop.md:76` | Defines GQSL as controlled experiments over figure source. |

Live dogfood evidence from:

```bash
./bin/fig-agent quality-search fig1_overview_v5f_art_direction_001_vault \
  --goal "global art-direction improvement and tool-defect discovery" \
  --plan --json
```

Current result:

- `workflow_ready=true`, `release_ready=false`.
- Release blocker is `acceptance_not_declared`, and `blocks_search=false`.
- Search is blocked by neither release nor workflow gates.
- Quality basin is `print_typography_authority`, `history_count=5`.
- Detector-safe candidate count is `15`.
- Detector clusters are `B=1`, `C=7`, `E=7`, `unknown=3`.
- Recommended operation is `step_out_experiment`.
- Candidate families are `hierarchy_rebalance`, `apparatus_strengthen`, and
  `density_reduce`.
- Tool-defect candidates already surfaced:
  - local `tikz_patch` routing ended in basin instead of stronger family switch;
  - safe detector candidates lack full panel/selector binding;
  - unlinked micro defect `M_PANEL_F_DENSITY` is not part of the current map.

## Gap Analysis

### 1. Planner Exists, Executor Does Not

`quality-search --plan` now gives the correct high-level answer: do not stop at
human acceptance, step out from local typography polish, and try larger family
changes.

The missing command is:

```bash
./bin/fig-agent quality-search <fixture> --execute --max-iterations N
```

At first this must be a dry executor that writes only scratch evidence. Source
mutation comes later, after candidate gates exist.

### 2. Candidate Generation Is Too Local

The current deterministic generator is mostly built around
`bounded_coordinate_offset` and coordinate/text-boundary style defects. That is
useful for local repair, but it cannot solve the current v5f problem:

- Panel C needs stronger hero hierarchy.
- Row 2 needs to read as three evidence modes, not three equal tool boxes.
- Panel F apparatus needs structural redrawing, not bigger labels.
- D/E/F need results/mechanism foregrounded over apparatus decoration.

The executor therefore needs a family registry for broader, still-bounded
candidate families.

### 3. Ranking Is Safe But Weak

Candidate ranking already includes hard gate, render evidence, detector prior,
and memory prior. The weak points are:

- `legibility` is currently placeholder-like;
- `reference_faithfulness` is placeholder-like;
- review burden is coarse;
- changed-pixel ratio is not yet a first-class score component;
- panel hierarchy and apparatus credibility are not yet measured directly.

This is acceptable for v0 execution if every candidate stays review-only. It is
not enough for automatic source apply.

### 4. Tool Defects Are Detected But Not Yet a First-Class Work Queue

The planner can emit tool-defect candidates, but they need a stable ledger and
regression path. Tool defects should not be mixed with figure defects. They need
their own reproduction, expected behavior, actual behavior, and recommended
test.

### 5. Local Loop Output Is Not Yet a Search Policy

`fig_loop` can say a basin exists. `quality_search` can say which family should
be tried. The missing layer is a policy that decides:

- keep doing local detector-linked fixes;
- step out to a broader family;
- render a candidate batch;
- mark a tool defect;
- stop because no safe search remains.

## Proposed Algorithm

Name: **Quality Search Executor**.

It is a staged, evidence-driven search loop. It is not a free-form LLM editor.

```text
state = observe(fixture)
for iteration in budget:
  classification = classify(state)

  if classification.progress_blocker:
    run safe prerequisite or stop with blocker
    continue

  if classification.release_blocker_only:
    keep searching if blocks_search == false

  policy = choose_policy(state, memory, basin_history)

  candidate_specs = generate_batch(policy, state)
  render_results = render_sandboxes(candidate_specs)
  scores = rank_candidates(render_results, state, memory)
  decision = select(scores)

  write scratch evidence

  if decision.kind == "apply_ready":
    require apply gate
    apply one candidate
    compile -> export -> critique/adjudicate/loop/status
    record memory/tool defects
    continue

  if decision.kind in {"step_out", "tool_defect", "no_actionable_candidate"}:
    stop with evidence
```

The initial policy should be simple and deterministic:

1. **Rule gate** for missing compile, stale critique, stale export, source drift,
   and release blockers that do not block search.
2. **Detector-local policy** when safe candidates point to one clear selector
   and the family is supported.
3. **Basin step-out policy** when repeated local loop history shows the same
   aesthetic bottleneck.
4. **Beam batch** of 2-4 candidates plus one null candidate.
5. **Anneal/expand** only after repeated marginal scores, by widening the
   family from label to panel to row.

Do not add an opaque machine-learning dependency. The useful algorithmic shape
is contextual bandit plus beam search plus annealing, implemented as explicit
JSON decisions over existing render evidence.

## Candidate Families

Candidate families are typed adapters. Each family must declare target, source
range, protected labels, expected movement, scoring hooks, and rollback.

| Family | First implementation | Initial apply authority |
| --- | --- | --- |
| `bounded_coordinate_offset` | Existing local label/spacing movement | apply-gated when render and semantic checks pass |
| `density_reduce` | Remove or merge repeated micro-labels in one panel or row | review-only |
| `apparatus_strengthen` | Redraw one apparatus group with clearer physical relation | review-only |
| `hierarchy_rebalance` | Reweight one panel or row so the scientific result reads first | review-only |
| `mechanism_foreground` | Put result curve/mechanism above apparatus scaffolding | review-only |
| `layout_macro_shift` | Adjust panel/row whitespace and breathing room | review-only |

Review-only means the executor may render and rank candidates, but source apply
requires an explicit apply gate until metrics mature.

## Evidence Artifacts

Every execution run writes under:

```text
.scratch/quality-search-runs/<timestamp>-<fixture>/
```

Required files:

- `run_manifest.json`
- `state_000.json`
- `classification_000.json`
- `policy_000.json`
- `family_registry_000.json`
- `candidate_set_000.json`
- `candidate_specs_000.json`
- `render_results_000.json`
- `candidate_scores_000.json`
- `candidate_rankings_000.json`
- `decision_000.json`
- `depone_plan_000.json`
- `depone_evidence_000/evidence-contract.json`
- `depone_evidence_000/quality-search-verdict.json`
- `tool_defect_candidates_000.json`
- `memory_events_000.json`

These files are evidence, not authority. They do not replace source files,
fixture metadata, critique files, adjudication files, or acceptance files.
The Depone evidence pack is a verifier bridge for the run folder: it must prove
the run stayed review-only, materialized candidates, preserved source/release
mutation boundaries, and produced rankable sandbox evidence.

## Implementation Slices

### Slice 0 - Freeze Analysis

Status: this document.

Deliverable:

- Document the total system analysis and execution plan.
- Confirm the current plan command still identifies v5f as a searchable basin,
  not a human-acceptance stop.

Verification:

```bash
./bin/fig-agent quality-search fig1_overview_v5f_art_direction_001_vault \
  --goal "global art-direction improvement and tool-defect discovery" \
  --plan --json
```

### Slice 1 - Dry Executor

Add:

```bash
./bin/fig-agent quality-search <fixture> --execute --max-iterations N --json
```

Initial behavior:

- read state with the same surfaces as `--plan`;
- write `.scratch/quality-search-runs/...`;
- choose a policy and candidate batch;
- do not mutate source;
- do not set accepted/golden/final;
- return a machine-readable decision.

Stop condition:

- executor can produce a complete run folder and decision without source writes.

### Slice 2 - Family Registry

Add a small registry that maps quality-search family names to candidate-spec
builders.

Initial builders:

- `density_reduce`: target panels from detector clusters and unlinked micro
  defects.
- `apparatus_strengthen`: target Panel F apparatus group and require physical
  relation fields such as charge, force, electrode, and air gap.
- `hierarchy_rebalance`: target Panel C plus Row 2 D/E/F hierarchy.

Stop condition:

- each builder emits candidate specs with source selectors, protected labels,
  expected visual movement, and rollback conditions.

### Slice 3 - Batch Render And Rank

Wire generated candidate specs into existing sandbox rendering and ranking.

Add:

- null candidate baseline;
- contact sheet for baseline versus candidates;
- full-render changed-pixel ratio;
- panel C/D/E/F crop evidence;
- minimum 2 percent v5d-to-current or baseline-to-candidate change threshold
  for declared large redesign experiments.

Stop condition:

- executor can render and rank a candidate batch without touching source.

### Slice 4 - Apply Gate

Allow one selected candidate to become apply-ready only if:

- compile/export/crop/evaluate gates pass;
- no source drift;
- semantic review passes;
- detector target improves or broad-family metric improves;
- no equal-or-higher new defect appears;
- candidate acceptance or configured local apply gate is present;
- release state remains not accepted unless a human explicitly accepts.

Stop condition:

- one bounded patch can be applied, verified, and rolled back if needed.

### Slice 5 - Tool Defect Ledger

Create a separate tool-defect ledger for search-loop failures.

Each record includes:

- symptom;
- fixture;
- command;
- expected behavior;
- actual behavior;
- minimal reproduction;
- suspected module;
- recommended test;
- status.

Stop condition:

- v5f tool defects from the current plan output are recorded as actionable,
  testable repo work, separate from figure quality defects.

### Slice 6 - Cross-Fixture Benchmark

Run the dry executor across multiple fixtures to learn whether families and
policies generalize.

Stop condition:

- benchmark report separates figure improvement, tool defects, and release
  blockers.

## v5f First Execution Target

Use v5f as the first dogfood fixture:

```text
fig1_overview_v5f_art_direction_001_vault
```

Initial candidate batch:

1. `hierarchy_rebalance`: Panel C becomes the clear hero; Row 2 reads as three
   evidence modes.
2. `apparatus_strengthen`: Panel F redraws charge/force/electrode/air-gap
   geometry instead of enlarging labels.
3. `density_reduce`: Panels C/E/F remove repeated micro-label load at print
   scale.
4. `null`: current v5f source as baseline.

Required comparison:

- v5d/v5e/v5f full render contact sheet;
- print thumbnail;
- Panel C/D/E/F crops;
- full render changed-pixel ratio;
- detector movement;
- tool-defect candidates.

Do not promote v5f. Do not set accepted/golden/final. The goal is search-loop
evidence and candidate quality, not release declaration.

## Safety Boundaries

Forbidden without explicit human approval:

- setting accepted/golden/final state;
- overwriting release exports;
- treating generated export pixels as source;
- broad free-form source rewrite with no selectors;
- mutating unrelated fixtures;
- hiding critique findings to make status green.

Allowed in dry executor:

- status, driver, loop, quality-map, memory, and planner reads;
- compile/export into ordinary ignored build/export paths when already allowed
  by the existing commands;
- candidate sandbox writes;
- scratch evidence writes.

Allowed in apply executor only after gates:

- one bounded source patch inside the target fixture;
- post-apply compile/export/status/loop verification;
- rollback patch generation.

## Success Criteria

The next meaningful milestone is not a prettier single manual patch. It is:

- `quality-search --execute` exists;
- it runs the v5f loop as a candidate batch;
- it records evidence under `.scratch/quality-search-runs`;
- it separates release blocker from search blocker;
- it proposes or renders stronger family changes when basin repeats;
- it records tool defects as separate work items;
- source mutation remains impossible until apply gates pass.

## Stop Conditions

Stop and report, rather than patching blindly, when:

- all candidates fail compile/render gates;
- candidate specs cannot bind to stable source selectors;
- detector evidence is stale;
- the best candidate only changes pixels locally when the goal is global
  art-direction improvement;
- tool behavior prevents a valid search decision;
- release readiness is the only remaining blocker.
