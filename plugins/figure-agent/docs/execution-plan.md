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
  same model, input packet, budget, and starting artifact; do not treat manually
  staged manifests as actual LLM runs without generation receipts. A receipt is
  `transcript_bound` only when its adjacent non-symlink transcript and both
  declared starting/generated artifacts match their SHA-256 hashes and shared
  contract; use `scripts/quality/generation_receipt.py` to write this record.
  The writer refuses packet/budget hash drift and transcript overwrite. This is
  an auditable execution claim, not provider authentication.
  The additive `comparable-v1/` run is transcript-bound and equal-input, but all
  three arms fail before render because the abstract `polymer-paper` style
  profile was not converted into an executable preamble and palette contract.
  Its reproduction gate failed and no product or publication claim is allowed.
  The additive `comparable-v2/` run closes that integration gap: `raw` remains
  free authoring, `verified` receives the executable preamble/palette/type
  contract, and `repaired` receives the same contract plus one declared Panel A
  layout lane. In a clean committed worktree, raw reproducibly stops at 20
  Style Lock blockers while verified and repaired render with zero blockers.
  Confirmed defect occurrences fall from 26 to 6 and 3 respectively. This is
  not acceptance: both rendered arms still fail the declared layout lane
  (`0.000 < 0.015`), verified has one detected collision and four label-order
  risks, repaired has two detected collisions, and scaffold inspection exposes
  unfinished label placement. The result proves that pre-authoring style
  injection removes a broad class of avoidable source defects; it also proves
  that prompt-only layout injection is not enforcement or repair.
  Moon subsequently rejected both rendered arms. The verified arm remains the
  repair seed because the repaired arm made the Panel B band-energy shapes
  worse. The rejection names major label/path collisions, unnatural arrows and
  endpoints, insufficient sample rendering, and unresolved physical or
  mathematical authority for the band-energy curves; color and aesthetic
  polish are explicitly deferred. The ablation product gate now requires an
  `accepted` named decision, so a named rejection cannot authorize a product
  claim.
  Historical evidence for this unchecked comparison remains under
  `review/failure-first/` and is non-prescriptive:

  - `raw.yaml`, `style_control.yaml`, `verified.yaml`, and their receipts show a
    bound raw run, a deterministic non-LLM style control, one preamble failure,
    and one feedback-guided run that is not equal-input.
  - The `region_guided_*` artifacts show narrow containment gains but continuing
    strict collisions, a clipped label, weak hierarchy, and Moon's rejection of
    the shapes, palette, proportion, grammar consistency, and prose density.
    The bound inventory records `75 > 45`, `33 > 22`, and `42 > 23` words plus
    missing-label and zero-clearance findings; these are fixture evidence, not
    universal publication rules.
  - `execution-binding-v3/`, `execution-binding-v4/`, and
    `execution-binding-v6/` preserve respectively a non-renderable preamble
    failure, undeclared treatment reads, and a timed-out treatment proof with
    continuing strict findings. All pairs remain comparison-ineligible.
  - `execution-repair-v1/` onward preserves every accepted and rejected bounded
    attempt. The sequence established exact replacement, transactional
    materialization, blocker-identity regression checks, multi-neighbor layout
    checks, source-scoped transfer assertions, rendered semantic-path recovery,
    and threshold-free path metrics. The detailed attempt history belongs to
    those immutable artifact directories and Git history, not this forward plan.
    V64 is the current verified-derived baseline; v66 is the preserved
    transferred-collision counterexample. Neither is publication-accepted.
  - Commits `771c339d`, `a30ff450`, `3d16305e`, and `5a2e895f` bind the v12
    renderer-neutral semantic packet, fail-closed authority and selector checks,
    transactional version publishing, and authenticated page evidence at
    `semantic-review-v12/packet/packet.json`.
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

**Current next executable step:** complete Q0 before changing the figure.

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

Q0–Q4 are sequential. A failed earlier gate blocks later figure polishing.
After Q4 and the Slice 1 exit condition both pass, execute Slice 3 exactly once;
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

- [ ] Verify identical model, input, budget, and starting-artifact contracts
  within each family.
- [ ] Report scientific failures, visual defects by class, actionable attribution
  rate, repair success, regression rate, human interventions, correction
  minutes, reproduction, editability, and provenance as separate metrics.
- [ ] Reject any result in which visual improvement compensates for a semantic or
  relation failure.
- [ ] Compare which detector and repair families transferred without fixture
  names, coordinates, or weakened thresholds.
- [ ] Classify each capability as `promote`, `retain_experimental`, `human_only`,
  or `retire` with evidence links.
- [ ] Update `docs/product-spec.md` only if the two-family evidence changes a
  durable product rule. Remove completed work from this plan rather than
  appending another historical task log.

### Verification

```bash
uv run python bin/fig-agent failure-corpus --json
uv run python bin/fig-agent failure-ablation \
  --raw examples/fig1_failure_first_panel_f_pilot/review/ablation/raw.yaml \
  --verified examples/fig1_failure_first_panel_f_pilot/review/ablation/verified.yaml \
  --repaired examples/fig1_failure_first_panel_f_pilot/review/ablation/repaired.yaml \
  --json
uv run python bin/fig-agent failure-ablation \
  --raw examples/fig3_resistance_mechanism/review/failure-first/raw.yaml \
  --verified examples/fig3_resistance_mechanism/review/failure-first/verified.yaml \
  --repaired examples/fig3_resistance_mechanism/review/failure-first/repaired.yaml \
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
