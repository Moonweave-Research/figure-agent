# Figure Quality System Roadmap

**Status:** Historical evidence — non-authoritative.
**Superseded by:** `docs/product-spec.md` and `docs/execution-plan.md`.

Date: 2026-07-03
Status at the time: execution roadmap after fig1 v5 visual dogfood

Implementation update:

- 2026-07-03: P1 initial `compare-fixtures` CLI shipped in commit `757acc2d`.
- 2026-07-03: P2 initial `critique-scaffold` CLI shipped in commit `b6c4b661`.
- 2026-07-03: P3 initial `fork-fixture` CLI shipped in commit `20bf44fe`.
- 2026-07-03: P4 initial `visual-metrics` CLI shipped in commit `b01f12c3`.
- 2026-07-03: P5 initial queue operator-report buckets shipped in commit `41080dd2`.

## Purpose

This document turns the current Figure 1 quality problem into a system roadmap.
The immediate question is not only whether `fig1_overview_v5c_quiet_001_vault`
is better than v5b or v4. The larger question is how `figure-agent` should make
the next such choice easier, more repeatable, and less dependent on memory.

The target product identity remains the active quality-kernel direction:
deterministic quality gates, authoring context, reproducibility, and honest
human review boundaries for paper figures. The plugin should not become an
autonomous taste judge or a hidden image-generation orchestrator.

## Current Diagnosis

The current tool can prove many hard facts:

- build and export freshness;
- geometric collision and boundary checks;
- label/path proximity;
- semantic assertions and convention receipts;
- critique freshness and publication gate state;
- candidate generation, rendering, ranking, review, acceptance, and apply flows;
- quality defect ledger and patch planning surfaces;
- style benchmark packs, comparison packets, and design-direction packets.

The weak point is the visual-quality decision interface between those facts.
During the v4 -> v5a -> v5b -> v5c loop, the most important decisions were still
made by manual side-by-side judgment:

- v5a was safe but visually small;
- v5b was a real improvement because it removed the Row 2 outer box;
- v5c was the current best branch, but only modestly stronger than v5b;
- the next branch should be either fresh critique plus minor TikZ polish, or a
  deliberate ground-up redraw.

The system can render candidates, but it does not yet make "which candidate
should become the next serious lane?" feel like a first-class operation. The
result is that aesthetic iteration works, but the operator has to assemble the
decision packet manually.

## Product Direction

The next phase should deepen the figure-quality kernel in four modules:

1. Candidate decision packets.
   A read-only interface that compares complete fixture lanes such as v5b and
   v5c, summarizes hard gates, artifact hashes, critique state, aesthetic intent,
   and known human judgment, then recommends the next action.

2. Critique readiness scaffolding.
   A helper that reduces the cost of writing a fresh grounded critique without
   fabricating human judgment. It may prefill evidence, source hashes, crop
   manifests, and empty accounting fields, but it must leave the actual visual
   finding decisions for the human/host critic.

3. Candidate lane hygiene.
   A safer way to fork and track visual lanes so metadata, `aesthetic_intent`,
   `briefing.md`, and fixture identity do not drift when creating a v5b/v5c-style
   branch by hand.

4. Non-model visual-quality metrics.
   Print-scale readability, hierarchy, density, line-weight rhythm, scaffold
   load, and reference-class deltas should become advisory evidence. These are
   not "AI taste"; they are deterministic signals that help decide whether a
   redraw is worth the cost.

## Architecture Opportunities

### P0: Current Figure 1 Decision Path

Goal: get from v5c to a justified next art-direction choice.

Tasks:

- Run fresh critique for `fig1_overview_v5c_quiet_001_vault`.
- Compare v5c against v5b at full render and print-scale proxy.
- Decide one of:
  - keep v5c and do bounded TikZ micro-polish;
  - fall back to v5b if v5c made the convergence cue too quiet;
  - start a ground-up redraw if neither candidate crosses the desired journal
    finish threshold.

Stop condition:

- A decision packet records the chosen branch, why it beat the alternatives, and
  the next bounded action.

Verification:

- `./bin/fig-agent status fig1_overview_v5c_quiet_001_vault --json`
- `./bin/fig-agent helper critique_brief.py examples/fig1_overview_v5c_quiet_001_vault`
- `python scripts/checks/check_golden_artifacts.py examples/fig1_overview_v5c_quiet_001_vault --no-require-accepted`

### P1: Candidate Lane Decision Packets

Goal: make side-by-side candidate-lane comparison a first-class read-only
module.

Proposed interface:

```bash
./bin/fig-agent compare-fixtures \
  fig1_overview_v5b_editorial_001_vault \
  fig1_overview_v5c_quiet_001_vault \
  --baseline fig1_overview_v4_pair_001_vault \
  --json
```

Expected payload:

- schema and candidate fixture list;
- source, build PNG, export SVG/PDF/PNG/TIFF hashes;
- compile/export/status freshness;
- deterministic audit counts;
- critique state and acceptance state;
- aesthetic-intent and paper-context availability;
- advisory visual metrics where available;
- human-readable recommendation bucket:
  - `needs_human_critique`;
  - `candidate_beats_baseline`;
  - `candidate_tie`;
  - `fallback_to_previous`;
  - `redraw_recommended`;
  - `blocked_stale_evidence`.

Implementation notes:

- Reuse `status.py`, `quality_manifest`, `reference_aesthetic_metrics.py`, and
  existing checker outputs rather than creating a second policy engine.
- Keep the module read-only. Do not compile, export, edit, accept, or mark
  golden state.
- The recommendation must be advisory unless a hard gate is stale or failed.

Verification:

- unit tests with two tiny fixture directories and synthetic build/export files;
- CLI smoke on v5b/v5c;
- `python -m compileall -q scripts tests`;
- targeted pytest for the new module.

### P2: Critique Readiness Scaffold

Goal: reduce the host/human cost of a fresh `/fig_critique` while keeping the
human-attestation boundary honest.

Proposed interface:

```bash
./bin/fig-agent critique-scaffold fig1_overview_v5c_quiet_001_vault --json
```

Expected behavior:

- require fresh render inputs;
- summarize the critique input hash and artifact hashes;
- list required crop-accounting sections;
- emit a fillable `build/critique_scaffold.md` or JSON packet;
- never write `critique.md`;
- never mark findings as absent;
- never set acceptance or publication readiness.

Why this matters:

- `critique_brief.py` already creates rich evidence, but the actual critique
  write is high-friction. The scaffold should make "write the fresh critique"
  easier without pretending the machine performed the visual judgment.

Verification:

- scaffold output is deterministic for unchanged inputs;
- output changes when `.tex`, `briefing.md`, `spec.yaml`, or style lock changes;
- malformed/non-fresh inputs fail closed with controlled errors.

### P3: Candidate Lane Hygiene

Goal: make visual lane forking safer than manual copy/edit.

Proposed interface:

```bash
./bin/fig-agent fork-fixture \
  fig1_overview_v5b_editorial_001_vault \
  fig1_overview_v5d_redraw_001_vault \
  --reason "ground-up editorial redraw candidate"
```

Expected behavior:

- copy only source-side files needed for a new fixture lane;
- rewrite fixture-local identity in `spec.yaml`, `.tex`, and known metadata
  files;
- clear stale build/export/critique/acceptance files;
- record a fixture-local fork receipt;
- preserve acceptance/golden state as not declared unless explicitly created by
  a separate human gate.

Non-goals:

- no automatic science changes;
- no source mutation of the original fixture;
- no hidden final-artifact promotion.

Verification:

- forked fixture status starts blocked on missing render/critique, not falsely
  ready;
- source paths and fixture names are internally consistent;
- stale artifacts are absent;
- symlink/path escape checks match existing candidate sandbox style.

### P4: Deterministic Visual Quality Metrics

Goal: add advisory visual evidence that correlates with journal finish quality.

Metric families:

- print-scale text legibility proxy;
- label density and label-to-mark clearance;
- panel hierarchy and scaffold load;
- line-weight tier consistency;
- color count and palette restraint;
- edge density / ink density / coarse occupancy deltas;
- repeated-panel rhythm across rows.

Rules:

- metrics are advisory unless tied to an explicit hard invariant;
- do not call a model or external API;
- report uncertainty and missing evidence clearly;
- use existing reference packs and aesthetic intent where available.

Verification:

- fixtures with known dense labels should score worse than clear controls;
- metrics remain stable across repeated renders in the same environment;
- no metric alone can mark a figure accepted or release-ready.

### P5: Queue and Operator Reporting

Goal: make "what blocks publication?" and "what improves visual quality next?"
different questions in the queue/report surface.

Current issue:

- release readiness, critique freshness, candidate comparison, and aesthetic
  direction are related but not identical.

Desired reporting buckets:

- hard publication blocker;
- human critique blocker;
- reproducibility blocker;
- visual-quality improvement opportunity;
- optional editorial polish;
- deferred/redraw decision.

Verification:

- `fig-agent queue --json` keeps existing blockers stable;
- new fields are additive;
- no existing release gate silently weakens.

Initial shipped behavior:

- each queue row may now include `operator_report_bucket`;
- queue `summary` includes `by_operator_report_bucket`;
- `bottleneck_report` includes `by_operator_report_bucket` and
  `operator_report_buckets`;
- command-plan item shapes stay unchanged so executable/blocked automation
  contracts remain stable.

Buckets:

- `hard_publication_blocker`;
- `human_critique_blocker`;
- `reproducibility_blocker`;
- `visual_quality_improvement_opportunity`;
- `optional_editorial_polish`;
- `deferred_redraw_decision`.

Current v5c smoke result:

```bash
./bin/fig-agent queue --mode review --goal "P5 operator report smoke" \
  fig1_overview_v5c_quiet_001_vault --json
```

The row reports `operator_report_bucket: human_critique_blocker`. This is
intentional: the row also carries release-blocker context, but the current
operator action is a missing/freshness critique boundary, so it should not be
misreported as the publication blocker that comes later.

## Execution Order

1. Finish the v5c decision path.
   This is the live dogfood case and should drive the first implementation
   details.

2. Implement P1 compare-fixtures.
   This is the highest-leverage missing interface. It converts manual
   side-by-side judgment into a repeatable packet without crossing the human
   visual-judgment boundary.

3. Implement P2 critique-scaffold.
   This shortens the slowest part of the loop while preserving honest critique
   ownership.

4. Implement P3 fork-fixture.
   This prevents future lane metadata drift once comparison and critique
   scaffolding define what metadata must stay coherent.

5. Add P4 metrics one family at a time.
   Start with print-scale readability and scaffold load because they connect
   directly to the v5b/v5c Figure 1 question.

6. Update queue/report fields.
   Do this after P1/P2/P4 payloads exist so queue reporting can summarize real
   evidence rather than inventing state names.

## Agent Work Packets

### Work Packet A: v5c Decision Packet

Owner: one implementation agent plus human/host critique.

Inputs:

- `docs/decision-packets/2026-07-03-fig1-v5-visual-elevation.md`
- `examples/fig1_overview_v5b_editorial_001_vault`
- `examples/fig1_overview_v5c_quiet_001_vault`

Deliverable:

- updated decision packet with fresh critique result and branch choice.

Stop:

- branch choice is explicit; no acceptance/golden mutation.

### Work Packet B: compare-fixtures Read-Only CLI

Owner: implementation agent.

Deliverable:

- module under `scripts/`;
- CLI entry in `bin/fig-agent`;
- targeted tests;
- smoke output on v5b/v5c.

Stop:

- no mutation; stale evidence blocks recommendation; tests pass.

Initial shipped interface:

```bash
./bin/fig-agent compare-fixtures <candidate-a> <candidate-b> --baseline <baseline> --json
```

The command is read-only, aggregates status/artifact hashes/audit counts, and
returns `blocked_stale_evidence`, `needs_human_critique`, or `candidate_tie`
without declaring an automated aesthetic winner.

### Work Packet C: critique-scaffold

Owner: implementation agent.

Deliverable:

- scaffold module and CLI;
- tests proving it never writes `critique.md` or acceptance state;
- deterministic output for unchanged inputs.

Stop:

- host/human still owns critique decisions.

Initial shipped interface:

```bash
./bin/fig-agent critique-scaffold <fixture> --json
./bin/fig-agent critique-scaffold <fixture> --no-write --json
```

The command requires fresh render state, writes only
`build/critique_scaffold.md` unless `--no-write` is supplied, and explicitly
forbids `critique.md`, human attestation, or accepted/golden-state mutation.

### Work Packet D: fork-fixture

Owner: implementation agent.

Deliverable:

- safe fixture fork helper;
- metadata rewrite tests;
- stale artifact clearing tests.

Stop:

- new fixture is internally coherent and starts non-accepted.

Initial shipped interface:

```bash
./bin/fig-agent fork-fixture <source> <target> --reason "<why>" --json
./bin/fig-agent fork-fixture <source> <target> --reason "<why>" --dry-run --json
```

The command copies source-side entries only, rewrites fixture-local identity,
renames `<source>.tex` to `<target>.tex`, records `fork_receipt.json`, skips
generated/state entries, and skips source symlinks rather than copying link
targets into the new lane.

### Work Packet E: Visual Metrics v1

Owner: implementation or analysis agent.

Deliverable:

- print-scale readability and scaffold-load advisory metrics;
- fixture examples that demonstrate useful signal;
- documentation that metrics do not accept/reject figures alone.

Stop:

- metrics are stable, explainable, and advisory.

Initial shipped interface:

```bash
./bin/fig-agent visual-metrics <fixture> --json
./bin/fig-agent visual-metrics <fixture> --no-write --json
```

The command reads `build/<fixture>.png`, existing detector outputs, and
`build/audit_crops/manifest.json`, then reports image density, edge density,
quantized color count, detector candidate counts, required crop counts, and
print-scale crop evidence. It writes only
`build/visual_quality_metrics.json` unless `--no-write` is supplied and reports
`policy: advisory_only`; it never changes acceptance, publication readiness, or
golden state.

Current v5c smoke result:

- fixture: `fig1_overview_v5c_quiet_001_vault`;
- image: `4272 x 2897`, ink density `0.105872`, edge density `0.016187`;
- detectors: `39` visual-clash candidates, `93` undeclared-geometry candidates,
  `0` text-boundary candidates, `0` label-path candidates;
- crops: `105` required crop ids with `print_178mm` and `print_thumbnail`
  present;
- scaffold load: `high` with score `237`.

Interpretation: v5c has useful print-scale evidence and no current text/path
proximity findings, but the detector/crop burden is still high enough that
human critique and editorial simplification remain live concerns.

## Risks

- Over-automation risk: the tool may start pretending it can judge taste. Keep
  recommendations advisory unless evidence is deterministic and explicitly
  policy-bound.
- Interface sprawl: there are already candidate, quality, benchmark, direction,
  and critique modules. Prefer thin aggregators over new engines.
- Fixture churn: visual lanes can multiply quickly. Fork receipts and comparison
  packets should identify which lane is active and which lanes are archived.
- False confidence: clean geometry checks do not imply journal-level finish.
  Report deterministic pass/fail separately from aesthetic recommendation.

## Success Criteria

The next successful phase should make this true:

- An operator can ask, "Is v5c better than v5b, and what should we do next?"
  and get a grounded packet rather than reconstructing the answer from logs.
- A fresh critique remains human-owned but takes less setup work.
- New visual lanes are created with coherent metadata and no stale artifacts.
- Deterministic metrics help identify print-scale and scaffold problems without
  becoming a hidden aesthetic gate.
- The Figure 1 loop produces a documented branch decision: bounded TikZ polish,
  fallback, or ground-up redraw.
