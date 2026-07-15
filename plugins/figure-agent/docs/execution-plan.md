<!-- FIGURE_AGENT:EXECUTION_AUTHORITY -->
# Figure Agent Failure-First Implementation Plan

> **For agentic workers:** Execute this plan in order with tests first. Do not open another renderer, grammar, roadmap, or fixture-specific polish lane.

**Goal:** Prove on two materially different complex figure families that the same LLM plus Figure Agent detects and safely reduces recurring scientific and visual failures better than the same LLM alone.

**Architecture:** Keep TikZ as the current default publication-authoring path. Use the existing Python control plane for reviewed failure evidence, multi-scale observation, exact attribution, bounded repair, rollback, provenance, and human review. SVG remains a derived export or bounded diagnostic surface and is not an active backend-development target.

**Tech stack:** Python 3.11+, pytest, PyYAML, existing Figure Agent CLI and quality modules, TikZ/LuaLaTeX, PDF/PNG review evidence, existing dvisvgm export. Add no dependency.

---

## Current QA stop state — 2026-07-14

The reviewed baseline `09cd206a` was 32 commits ahead of `main` and had no
commits to merge from `main`. A detached clean-worktree run collected 3,778 tests and
finished with `3740 passed, 4 failed, 29 skipped, 5 xfailed`. The four failures
are release blockers, not publication findings:

1. a layout test requires an ignored historical v64 PDF that is absent from a
   clean checkout;
2. this active plan exceeded its authority-test size limit;
3. the Fig1 evidence verifier requires an ignored `review/states/build/raw.png`;
4. the historical hybrid Fig3 attribution test resolves `unbound`, not `exact`.

This update closes item 2; Q0 owns the remaining clean-checkout failures and
the destructive-test boundary found during review.

Q0–Q3 are complete on the active Fig3 source. The strict compile is green and
its status keeps render freshness separate from detector evidence. The geometry
report attributes 16/20 operations (five transfer paths, two analytic plots),
resolves five rendered curved arrows, and records non-zero layout clearances.

This is a bounded machine result, not publication acceptance: four operations
remain outside typed parsing, and the hash-bound current-render scaffold still
awaits a named human verdict. Critique and export evidence are present. Q4 is
next; keep historical sources read-only.

## 0. Authority and execution rules

This is the only active forward plan. `docs/product-spec.md` is the only active product specification. Completed tasks, superseded plans, experiment designs, and generated review packets remain evidence in Git history and their existing artifact directories; they do not set the next action.

Before editing any implementation, the integration target is `main`:

1. verify the active worktree, branch, common Git directory, and clean state;
2. compare the branch delta against `main` using the exact read-only preflight below;
3. preserve accepted, historical, and user-owned artifacts;
4. resolve integration in a dedicated clean worktree without force, reset, checkout-discard, or clean;
5. run commands from `plugins/figure-agent` unless stated otherwise;
6. write the smallest failing test before behavior changes;
7. keep each implementation commit bounded to one slice;
8. do not modify `scripts/quality/quality_search.py` or add fixture names and coordinates to reusable modules;
9. do not create another active specification, roadmap, or execution plan; and
10. never equate machine-valid or review-ready with publication acceptance.

```bash
git status --short
git branch --show-current
git rev-parse --git-common-dir
git rev-list --left-right --count main...HEAD
git diff --stat main...HEAD
```

If `main` cannot be resolved locally, stop as `integration_base_missing`; do not silently substitute another branch. Integration conflict resolution belongs in a separate clean worktree and is not part of the figure-evidence slices below.

Every A/B/C manifest must bind at least `model_id`, `input_packet_sha256`, `budget_contract`, `source_commit`, `starting_artifact_sha256`, selectors or declared regions, toolchain versions, and an aggregate `review_input_hash`. Generated outputs must carry their own hashes and provenance. A manifest without an actual generation receipt is staged evidence, not a comparable model run.

Existing implementation surfaces to reuse:

| Surface | Responsibility |
| --- | --- |
| `scripts/quality/failure_corpus.py` | Reviewed failure taxonomy and provenance |
| `scripts/quality/failure_ablation.py` | Comparable raw/verified/repaired evaluation |
| `scripts/visual_finding_attribution.py` | Geometry-first render-to-region attribution |
| `scripts/finding_source_attribution.py` | Token-first text-to-source attribution |
| `scripts/visual_finding_artifacts.py` | Deterministic overlays and crops |
| `scripts/quality/quality_patch_policy.py` | Human-required versus patchable boundary |
| `scripts/quality/quality_patch_plan.py` | Protected, budgeted repair plan |
| `scripts/quality/quality_patch_apply.py` | Preflight, application, receipt, rollback |
| `styles/snippets/panel-f-floating-cantilever.tex` | Reviewed same-family TikZ motif evidence |
| `bin/fig-agent` | Existing corpus, ablation, compile, export, and review surfaces |
The direct Panel F SVG renderer is retained only as non-promoted experiment evidence. Do not polish, generalize, import, or delete it during these slices.

## Slice 1: Panel F review closure

### Purpose

Close the evidence boundary of the first real failure-first figure without
silently upgrading its current development-baseline verdict.

### Current state

- the pre-extraction Panel F packet has a named development-baseline approval;
- clean-checkout reproduction exposed that shared-primitive extraction had
  removed three visible labels and left the tracked review evidence stale;
- the labels are restored and the current source, render, evidence manifest,
  and generated receipt now reproduce together;
- the primitive-derived packet has a small pixel delta from the historically
  reviewed packet, so all four current views are `pending_revalidation`;
- normal compilation passes;
- strict compilation remains non-accepting because inherited whole-figure
  collision and undeclared-geometry findings remain outside the bounded repair;
- correction minutes are still null; and
- publication acceptance is not claimed.

### Files

- Verify: `examples/fig1_failure_first_panel_f_pilot/`
- Modify only review state when evidence is current:
  `examples/fig1_failure_first_panel_f_pilot/review/human_verdict.yaml`
- Modify only reviewed findings when a named reviewer confirms them:
  `examples/fig1_failure_first_panel_f_pilot/review/human_findings.yaml`
- Test: `tests/test_fig1_failure_first_panel_f_pilot.py`
- Test: `tests/test_failure_first_vertical_slice.py`

### Steps

- [x] Reproduce the tracked figure and review packet from a clean checkout.
- [x] Bind the current render, source, semantic contract, selector state, and
  review-input hashes, then compare them with the packet presented to the
  reviewer; record any mismatch instead of transferring the verdict.
- [ ] Present and record the current whole, panel, object/relation, and zoom
  views as separate human decisions; preserve the existing panel verdict as
  historical evidence, but do not transfer it because the bound panel hash changed.
- [x] Record correction minutes and intervention count; do not infer either from
  commit count or elapsed agent time.
- [x] Retrospective correction time must not be estimated. For the existing Fig1
  work, record `unavailable` plus a reason; measure Fig3 prospectively.
- [x] Keep strict inherited findings visible instead of suppressing them to
  obtain a green state.
- [x] Admit only named confirmed defects or accepted false positives to the
  reviewed failure corpus.

### Verification

```bash
bash scripts/compile.sh \
  examples/fig1_failure_first_panel_f_pilot/fig1_failure_first_panel_f_pilot.tex
set +e
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh \
  examples/fig1_failure_first_panel_f_pilot/fig1_failure_first_panel_f_pilot.tex
strict_exit=$?
set -e
test "$strict_exit" -ne 0
uv run pytest tests/test_fig1_failure_first_panel_f_pilot.py \
  tests/test_failure_first_vertical_slice.py \
  tests/test_failure_corpus.py -q
uv run ruff check tests/test_fig1_failure_first_panel_f_pilot.py
git diff --check
```

Strict mode may remain non-zero only when the receipt names the unchanged
inherited findings. That state is evidence, not completion.

### Exit condition

All four required review scales have explicit named outcomes, correction time is
recorded or explicitly unavailable with a reason, corpus admission is
hash-bound, and publication acceptance remains separate. If human review is not
available, Slice 1 stops as `pending_human_review`.

## Slice 2: Fig3 cross-family proof

### Purpose

Test the same failure-first control loop on the current main-text Fig3
mechanism schematic rather than extending the successful Fig1 fixture or
reviving an older abandoned Fig3 composition.

### Target and boundaries

The target is `examples/fig3_resistance_mechanism/`: the current main-text Fig3
schematic that connects Fig2's material design space to Fig4's quantified trap
spectra. It has a maintained editable TikZ source, briefing, specification,
authoring contract, panel goals, critique history, and current render. Its two
dense panels test a different failure profile from Fig1: repeated,
sign-agnostic trap/release transport in panel A and the separate fitted-`n`,
distribution-breadth, and `rho_60s = magnitude` cues in panel B.

`fig3_trap_schematic_v97` and its derivative
`examples/fig3_trap_schematic_slice3_semantic/` are historical rejected/raw
evidence. Preserve them exactly and do not use them as the active target,
baseline, or acceptance candidate. `fig3_trapping_concept` is an older reset
fixture. `fig3_floating_clip_protocol` is a distinct SI/methods protocol
fixture; it remains useful later only after its experiment-specific physics
authority is reopened. Neither is part of this slice.

New failure-first evidence is additive under
`examples/fig3_resistance_mechanism/review/failure-first/`. It must not alter
the existing source figure or reinterpret its prior critique artifacts.

Fig1-specific snippets, coordinates, selectors, detector thresholds, labels,
and repair templates are forbidden. Reuse only renderer-neutral schemas and the
generic failure, attribution, artifact, policy, plan, apply, and rollback
modules listed in Section 0.

### Files

- Read authority: `examples/fig3_resistance_mechanism/{briefing.md,spec.yaml,authoring_contract.md,panel_goals.md,critique.md,critique_adjudication.yaml}`
- Verify source: `examples/fig3_resistance_mechanism/fig3_resistance_mechanism.tex`
- Create: `examples/fig3_resistance_mechanism/review/failure-first/`
- Modify only when one bounded exact repair is authorized: the current TikZ
  source plus its hash-bound receipt, with the maintained briefing, semantic
  boundary, and historical Fig3 artifacts protected
- Create: `tests/test_fig3_resistance_failure_first.py`
- Modify when reviewed evidence is added: `benchmarks/llm_failure_sources.yaml`
- Regenerate: `benchmarks/llm_failure_corpus.yaml`

### Steps

- [x] Create `tests/test_fig3_resistance_failure_first.py` as the first RED
  change. Do not reuse a test, packet, selector, coordinate hint, or verdict
  from the retired Fig3 target.
- [x] Bind the maintained briefing, specification, authoring contract, panel
  goals, editable source, render, and critique history to explicit hashes and
  authority roles.
- [x] Declare the two-panel narrative, required objects and relations,
  forbidden implications, and stable source selectors without importing Fig1
  declarations. In particular, preserve sign-agnostic repeated trapping in A,
  discrete-to-continuous distribution evolution in B, and the distinction
  between `n` (breadth) and `rho_60s` (magnitude).
- [x] Produce comparable `raw`, `verified`, and `repaired` manifests using the
  same model, input packet, budget, and starting artifact. `comparable-v1/`
  records a reproducible preamble integration failure. `comparable-v2/` proves
  that executable Style Lock injection removes broad source blockers, but its
  prompt-only layout treatment is not enforcement or repair. Moon rejected both
  rendered arms for collisions, unnatural paths, weak sample rendering, and
  unresolved band-energy authority; the repaired arm also regressed the band
  shapes. The verified arm remains the repair seed. All detailed intermediate
  attempts, receipts, exact counts, and counterexamples remain immutable under
  `review/failure-first/` and Git history rather than in this forward plan.
  Generation receipts are auditable execution evidence, not provider
  authentication, and no rejected or comparison-ineligible run authorizes a
  product or publication claim.
- [x] Generate whole, panel, object/relation, and zoom crops and overlays.
- [x] Keep ambiguous and unbound findings review-only. The renderer-neutral
  `figure-agent.semantic-legibility-evidence.v1` packet binds full/page rasters,
  geometry, crops, declarations, authenticated selectors, and the aggregate
  review hash. Missing, stale, duplicate, hash-drifted, conflicting, or
  cross-semantic bindings fail closed; versioned transactional publishing
  preserves human-owned files.
- [x] Apply one bounded Panel B hierarchy repair: remove the cross-plot
  transition arrow, attach concise labels to the two distributions, and keep
  `n` breadth and `rho_60s` magnitude orthogonal. The source and render receipt
  are hash-bound; its visual outcome remains review-ready, not accepted.
- [x] Compile v12 semantic review evidence: five subjects are exact and the S60
  distribution is blocked by an authority conflict. Exactly three questions are
  pending: trap-site versus capture-event distinction, breadth versus magnitude,
  and voltage connection to both electrodes. The S60 authority question is
  blocked. This is machine evidence only; semantic preservation and publication
  acceptance are not claimed.
- [x] Obtain a named human scaffold review. Both rendered v2 arms are rejected;
  this does not transfer to a publication verdict or authorize a product claim.
- [ ] Record prospectively measured correction minutes. A machine result is
  never a publication verdict.

### Ordered next execution

**Current next executable step:** complete Q4 for the maintained Fig3 evidence.
Before any further authoring experiment, complete Q5's constraint-diet gate; do
not add another generator, renderer, candidate family, or workflow shell.

- [x] **Q0 — Make QA non-destructive and clean-checkout complete.** Copy every
  historical TeX input and its required local dependencies to `tmp_path` before
  compilation; never write beside a historical source. Mark every TeX/render
  test `render`, prove `pytest -m 'not render'` invokes no TeX tool, and make the
  three remaining detached-worktree failures pass without relying on ignored
  build files.
- [x] **Q1 — Close semantic source-gate bypasses.** Match exact comma-delimited
  TikZ option keys so `xfer-helper` cannot satisfy `xfer`; resolve arrowheads
  declared through named TikZ styles; make missing or bidirectional heads fail a
  unidirectional assertion; validate tex-assertion evidence schema, source hash,
  and checked counts; compare scope against the declared merge base as well as
  the pending worktree surface.
- [x] **Q2 — Make status and strict orchestration truthful.** Run every detector
  through deferred strict aggregation, including vector clearance. Surface
  strict outcome, critique/export freshness, and geometry coverage separately;
  `FRESH` must mean freshness only. Reconcile `layout_lanes.yaml` with current
  rendered labels without weakening the intended breadth/energy/magnitude
  relations.
- [x] **Q3 — Cover the geometry users actually reject.** Parse and attribute the
  five curved transfer paths and two band plots, then require explicit coverage
  floors before zero findings may be called clean. Establish rendered semantic
  paths and non-zero vector-clearance checks. Do not invent aesthetic or
  physical thresholds from v64 alone; band-energy shape authority remains a
  human/scientific decision. Evidence: 16/20 source operations (including five
  `to_curve` paths and two `analytic_plot` records) map to five rendered arrows;
  this bounds detector coverage only, not physical band-energy shape.
- [ ] **Q4 — Refresh evidence and close human review.** Regenerate critique,
  audit crops, compile/export receipts, and review hashes in a clean environment.
  A named development-baseline scaffold verdict is now recorded; prospective
  correction minutes were not captured and must not be reconstructed after the
  fact. The critique/adjudication refresh remains open after any source repair.
  Machine-valid or review-ready remains distinct from publication acceptance.
- [ ] **Q5 — Reduce the active product surface before composition v2.** Preserve
  historical artifacts and compatibility schema readers, but inventory every
  top-level command and classify it as core, internal compatibility, or retired
  from the default path. Freeze direct-SVG generation, SVG-polish, deterministic
  composition-family templates, numeric taste ranking, and autonomous quality
  search. Select one canonical orchestration path and one bounded-repair path;
  do not delete code until import, CLI, fixture, and receipt dependencies are
  proven absent. Composition v2 may add only: generated-source semantic coverage
  eligibility, non-coordinate canvas containment, label-capacity/local-clearance
  requirements, complete per-arm QA receipts, and independent cold-run receipts.
  It may not prescribe coordinates, panel rectangles, primitive geometry,
  palette choices, or a fixed reading path.
  The first Q5 slice classifies all 81 callable CLI names behind
  `fig-agent doctor --commands --json`, makes `status -> run` the canonical
  public route, and removes autonomous quality-search activation from the
  `improve` compatibility adapter. The second Q5 slice establishes one shared
  source-mutation authorization validator and hardens the internal-compatibility
  `apply-plan` executor: apply now requires a decision bound to the fixture and
  exact quality-plan schema/path/recommendation and SHA-256 `plan_id`, rejects a
  plan whose mutation-critical content no longer matches that ID, and persists
  the authorization-record hash. It now derives a tested reverse patch from the
  pre/post source pair, writes rollback plus a recovery-required receipt before
  source mutation, and uses atomic replacement for source and final receipt.
  Existing bounded-TikZ apply now consumes the same validator while preserving
  its historical diagnostic codes and packet/result schemas. This is a
  safety-kernel extraction, not selection of `apply-plan` as a second public
  repair route. The third Q5 slice connects that kernel to the canonical
  additive `authoring-repair-packet -> authoring-repair-materialize` route.
  Materialization now has a read-only preview that exposes the packet/output
  hashes, requires a named decision bound to the exact packet, full preview,
  output path, and output hash, owns the adjacent v2 receipt, rejects
  lock/replay conflicts, and writes a recovery-required receipt before
  atomically creating the candidate. Atomic replacement fsyncs the containing
  directory before advancing the transaction, and additive rollback is defined
  as deletion only when the new output still matches its approved hash.
  Quality-patch and authoring-repair now share the same low-level exclusive-lock
  and atomic-write implementation; historical packet v3 and v1 receipts remain
  untouched. The bounded-repair transaction remains open only at the
  verification boundary: clean strict compile/status evidence still needs a
  fail-closed post-render finalizer. `bounded_repair_transaction_state`
  therefore remains `incomplete`.

Q0–Q4 are sequential. Q5 is an architecture gate and may proceed without
altering the figure while Q4 awaits human evidence. After Q4, Q5, and the Slice
1 exit condition pass, execute Slice 3 exactly once;
do not start another renderer or fixture.

### Verification

```bash
# Fast lane: after Q0 this must invoke no TeX/render tool.
uv run pytest -q -m 'not render'
# Run the complete suite in a disposable detached worktree.
uv run pytest -q
uv run pytest -q tests/test_check_tex_assertions.py tests/test_run_export.py tests/test_compile_contract.py tests/test_undeclared_geometry.py tests/test_check_layout_drift.py tests/test_document_authority.py
bash scripts/compile.sh examples/fig3_resistance_mechanism/fig3_resistance_mechanism.tex
set +e
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh examples/fig3_resistance_mechanism/fig3_resistance_mechanism.tex
strict_exit=$?
set -e
test "$strict_exit" -eq 0
uv run ruff check tests/test_fig3_resistance_failure_first.py
git diff --check
```

### Exit condition

This cross-family proof advances only after all three ablation manifests and
their bound generation receipts exist. The Fig3 packet is cleanly reproducible,
contains no Fig1-specific dependency, reports exact/ambiguous/unbound
attribution honestly, preserves scientific relations across any repair, and has
a named human outcome. A passing machine gate is not publication acceptance.

## Slice 3: Two-family A/B/C decision

### Purpose

Decide what Figure Agent has actually earned the right to promote based on Fig1
and Fig3 evidence, rather than starting another implementation lane.

### Files

- Verify: `benchmarks/llm_failure_corpus.yaml`
- Verify: the Fig1 and Fig3 raw/verified/repaired manifests
- Create or update the machine-readable decision artifact:
  `benchmarks/failure_first_capability_decision.yaml`; do not create a roadmap
- Test: `tests/test_failure_ablation.py`
- Test: `tests/test_failure_first_cli.py`
- Test: `tests/test_document_authority.py`

### Steps

- [x] `benchmarks/failure_first_capability_decision.yaml` records separate
  contract, defect, attribution, reproduction, provenance, human-outcome, and
  correction-minute evidence. Its decision is `insufficient_evidence`: visual
  improvement cannot offset semantic/relation failures, no capability promotes,
  and `docs/product-spec.md` remains unchanged.

- [ ] **Next evidence — additive Fig1 three-arm replay.** Preserve historical `review/ablation/` evidence and create only `review/failure-first/comparable-v1/`; before model invocation, run `./bin/fig-agent authoring-preflight-triplet --raw examples/fig1_failure_first_panel_f_pilot/review/failure-first/comparable-v1/raw_packet.json --verified examples/fig1_failure_first_panel_f_pilot/review/failure-first/comparable-v1/verified_packet.json --repaired examples/fig1_failure_first_panel_f_pilot/review/failure-first/comparable-v1/repaired_packet.json --json`.
  A pass proves only equal-input packet binding and disjoint outputs—not execution, a receipt, review, correction time, product claim, or publication acceptance; real clean-environment runs and named human outcomes remain required.

Runtime review surfaces use `figure-agent.current-render-review-scaffold.v1`
and `figure-agent.strict-status.v1`; neither schema is a publication verdict.

### Verification

```bash
uv run python bin/fig-agent failure-corpus --json
uv run python bin/fig-agent failure-ablation \
  --raw examples/fig1_failure_first_panel_f_pilot/review/ablation/raw.yaml \
  --verified examples/fig1_failure_first_panel_f_pilot/review/ablation/verified.yaml \
  --repaired examples/fig1_failure_first_panel_f_pilot/review/ablation/repaired.yaml \
  --json
uv run python bin/fig-agent failure-ablation \
  --raw examples/fig3_resistance_mechanism/review/failure-first/comparable-v2/raw.yaml \
  --verified examples/fig3_resistance_mechanism/review/failure-first/comparable-v2/verified.yaml \
  --repaired examples/fig3_resistance_mechanism/review/failure-first/comparable-v2/repaired.yaml \
  --json
uv run pytest tests/test_failure_ablation.py \
  tests/test_failure_first_cli.py \
  tests/test_document_authority.py \
  tests/test_release_contract.py -q
uv run ruff check scripts/quality tests/test_failure_ablation.py \
  tests/test_failure_first_cli.py tests/test_document_authority.py
git diff --check
```

### Exit condition

The decision names transferred capabilities and non-transferred experiments,
records the two named human outcomes, and leaves publication acceptance outside
the machine report. If either family lacks comparable evidence, the decision is
`insufficient_evidence`, not success.

## Completion boundary

This plan is complete only when:

1. Panel F has all required review scales and a recorded human-effort status;
2. Fig3 proves the same control loop without Fig1-specific imports;
3. both families have comparable raw, verified, and repaired evidence;
4. at least one recurring failure is exactly attributable and safely reduced
   without scientific regression;
5. rollback and clean reproduction are proven;
6. capability promotion is based on two-family evidence and named human review;
7. direct SVG remains non-promoted unless separate future evidence changes that
   fact; and
8. machine output never claims publication acceptance.

Until all conditions hold, Figure Agent remains a substantial quality-control system with promising bounded-repair evidence, not a proven autonomous publication-figure finisher.
