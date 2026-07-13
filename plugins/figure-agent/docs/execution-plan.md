<!-- FIGURE_AGENT:EXECUTION_AUTHORITY -->
# Figure Agent Failure-First Implementation Plan

> **For agentic workers:** Execute this plan in order with tests first. Do not
> open another renderer, grammar, roadmap, or fixture-specific polish lane.

**Goal:** Prove on two materially different complex figure families that the
same LLM plus Figure Agent detects and safely reduces recurring scientific and
visual failures better than the same LLM alone.

**Architecture:** Keep TikZ as the current default publication-authoring path.
Use the existing Python control plane for reviewed failure evidence, multi-scale
observation, exact attribution, bounded repair, rollback, provenance, and human
review. SVG remains a derived export or bounded diagnostic surface and is not an
active backend-development target.

**Tech stack:** Python 3.11+, pytest, PyYAML, existing Figure Agent CLI and
quality modules, TikZ/LuaLaTeX, PDF/PNG review evidence, existing dvisvgm export.
Add no dependency.

---

## 0. Authority and execution rules

This is the only active forward plan. `docs/product-spec.md` is the only active
product specification. Completed tasks, superseded plans, experiment designs,
and generated review packets remain evidence in Git history and their existing
artifact directories; they do not set the next action.

Before editing any implementation, the integration target is `main`:

1. verify the active worktree, branch, common Git directory, and clean state;
2. compare `main` and this branch because they have diverged, using the exact
   read-only preflight below;
3. preserve accepted, historical, and user-owned artifacts;
4. resolve integration in a dedicated clean worktree without force, reset,
   checkout-discard, or clean;
5. run commands from `plugins/figure-agent` unless stated otherwise;
6. write the smallest failing test before behavior changes;
7. keep each implementation commit bounded to one slice;
8. do not modify `scripts/quality/quality_search.py` or add fixture names and
   coordinates to reusable modules;
9. do not create another active specification, roadmap, or execution plan; and
10. never equate machine-valid or review-ready with publication acceptance.

```bash
git status --short
git branch --show-current
git rev-parse --git-common-dir
git rev-list --left-right --count main...HEAD
git diff --stat main...HEAD
```

If `main` cannot be resolved locally, stop as `integration_base_missing`; do not
silently substitute another branch. Integration conflict resolution belongs in
a separate clean worktree and is not part of the figure-evidence slices below.

Every A/B/C manifest must bind at least `model_id`, `input_packet_sha256`,
`budget_contract`, `source_commit`, `starting_artifact_sha256`, selectors or
declared regions, toolchain versions, and an aggregate `review_input_hash`.
Generated outputs must carry their own hashes and provenance. A manifest without
an actual generation receipt is staged evidence, not a comparable model run.

Existing implementation surfaces to reuse:

| Surface | Responsibility |
| --- | --- |
| `scripts/quality/failure_corpus.py` | Reviewed failure taxonomy and provenance |
| `scripts/quality/failure_ablation.py` | Comparable raw/verified/repaired evaluation |
| `scripts/visual_finding_attribution.py` | Render-to-panel/object/source attribution |
| `scripts/visual_finding_artifacts.py` | Deterministic overlays and crops |
| `scripts/quality/quality_patch_policy.py` | Human-required versus patchable boundary |
| `scripts/quality/quality_patch_plan.py` | Protected, budgeted repair plan |
| `scripts/quality/quality_patch_apply.py` | Preflight, application, receipt, rollback |
| `styles/snippets/panel-f-floating-cantilever.tex` | Reviewed same-family TikZ motif evidence |
| `bin/fig-agent` | Existing corpus, ablation, compile, export, and review surfaces |

The direct Panel F SVG renderer is retained only as non-promoted experiment
evidence. Do not polish, generalize, import, or delete it during these slices.

## Slice 1: Panel F review closure

### Purpose

Close the evidence boundary of the first real failure-first figure without
silently upgrading its current development-baseline verdict.

### Current state

- the Panel F panel view has a named development-baseline approval;
- whole, object/relation, and zoom views remain unreviewed;
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

- [ ] Reproduce the tracked figure and review packet from a clean checkout.
- [ ] Prove that the current render, semantic contract, selector state, and
  review-input hashes match the packet presented to the reviewer.
- [ ] Present and record the still-pending whole, object/relation, and zoom views
  as separate human decisions; preserve the existing panel verdict unless its
  bound `review_input_hash` changes.
- [ ] Record correction minutes and intervention count; do not infer either from
  commit count or elapsed agent time.
- [ ] Retrospective correction time must not be estimated. For the existing Fig1
  work, record `unavailable` plus a reason; measure Fig3 prospectively.
- [ ] Keep strict inherited findings visible instead of suppressing them to
  obtain a green state.
- [ ] Admit only named confirmed defects or accepted false positives to the
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
sign-agnostic trap/release transport in panel A and the separate `n = breadth`
and `rho_60s = magnitude` relations in panel B.

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
- [ ] Produce comparable `raw`, `verified`, and `repaired` manifests using the
  same model, input packet, budget, and starting artifact; do not treat manually
  staged manifests as actual LLM runs without generation receipts. A receipt is
  `transcript_bound` only when its adjacent non-symlink transcript and both
  declared starting/generated artifacts match their SHA-256 hashes and shared
  contract; use `scripts/quality/generation_receipt.py` to write this record.
  The writer refuses packet/budget hash drift and transcript overwrite. This is
  an auditable execution claim, not provider authentication.
  Current evidence is deliberately not yet eligible for this checkbox: the raw
  run is receipt-bound; the deterministic `style_control` isolates style-token
  injection but is not an LLM run; verified attempt 1 is preserved as a nested
  preamble-path failure; verified attempt 2 is receipt-bound but explicitly
  marked `feedback_guided_not_equal_input`. None may be presented as a fair
  raw/verified/repaired comparison or publication acceptance.
- [x] Generate whole, panel, object/relation, and zoom crops and overlays.
- [ ] Keep ambiguous and unbound findings review-only.
- [x] Apply one bounded Panel B hierarchy repair: remove the cross-plot
  transition arrow, attach concise labels to the two distributions, and keep
  `n` breadth and `rho_60s` magnitude orthogonal. The source and render receipt
  are hash-bound; its visual outcome remains review-ready, not accepted.
- [ ] Obtain a named human review and record prospectively measured correction
  minutes. A machine result is never a publication verdict.

### Verification

```bash
bash scripts/compile.sh \
  examples/fig3_resistance_mechanism/fig3_resistance_mechanism.tex
uv run pytest tests/test_fig3_resistance_failure_first.py \
  tests/test_failure_ablation.py \
  tests/test_quality_patch_policy.py \
  tests/test_quality_patch_plan.py \
  tests/test_quality_patch_apply.py -q
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

1. Panel F has all required review scales and measured human effort;
2. Fig3 proves the same control loop without Fig1-specific imports;
3. both families have comparable raw, verified, and repaired evidence;
4. at least one recurring failure is exactly attributable and safely reduced
   without scientific regression;
5. rollback and clean reproduction are proven;
6. capability promotion is based on two-family evidence and named human review;
7. direct SVG remains non-promoted unless separate future evidence changes that
   fact; and
8. machine output never claims publication acceptance.

Until all conditions hold, Figure Agent remains a substantial quality-control
system with promising bounded-repair evidence, not a proven autonomous
publication-figure finisher.
