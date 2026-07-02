# Issue 95 - Figure #2 Candidate Selection

Status: validation checkpoint complete; north-star reduction is capped for this
candidate because fig2 was already post-refit before the context-pack-backed
measurement window started.

## Selected Candidate

`fig2_trap_design_space`

## Rationale

`fig2_trap_design_space` is the best candidate for validating the authoring
context pack's north-star metric because it is already framed as the real
same-paper Figure 2:

- `briefing.md` calls it a Nature Communications main-text Figure 2.
- `spec.yaml` notes it as the "figure-agent figure #2" and "first end-to-end
  dogfood".
- The content is the same sulfur-polymer paper family as fig1: sulfur-rich
  polymer charge traps, S60-S85 composition tuning, conventional dielectric
  comparison, and charge-retention schematic logic.
- It is not accepted/golden yet, so it can still serve as a validation target.
- It has current render/export artifacts, critique/adjudication evidence, and a
  compact 144-line TikZ source, making iteration tracking practical.
- Its briefing already has explicit physics invariants and must-depict /
  must-avoid language that can be converted into semantic claims before the
  next major refit.

## Non-Candidates

- `fig1_overview_v2_pair_001_vault`: baseline, already accepted/golden; cannot
  validate figure #2.
- `fig3_*`, `fig4_*`, `fig5_*`: useful later, but they are downstream figure
  slots and less literal for the "figure #2 after fig1" validation.
- smoke fixtures: synthetic detector fixtures, not paper figures.

## Candidate Setup

`fig2_trap_design_space/spec.yaml` now declares `paper_id: pair001`, so the
context pack resolves the same source-anchored pair001 paper catalog that fig1
uses. This is selection metadata, not acceptance or release state.

## Context-Pack Evidence

Command:

```bash
cd plugins/figure-agent
bin/fig-agent context-pack fig2_trap_design_space --json
```

Expected evidence after `paper_id: pair001`:

- schema: `figure-agent.authoring-context-pack.v1`
- read_only: `true`
- rule_catalog: `docs/authoring-rules-pair001.md`
- project_rule_catalog: `docs/authoring-rules-project.md`

The pack should be rerun immediately before the next source-authoring or major
refit pass, because future edits to spec, briefing, rules, or style lock should
be part of the measured authoring context.

## Current Status Precondition

Adding `paper_id: pair001` changes `spec.yaml`, so `/fig_status` correctly
marks the current render and critique as stale. Before using fig2 as a
validation run, refresh compile/critique from this metadata-bearing source set;
do not compare iteration counts against pre-`paper_id` outputs.

## Measurement Plan

Use the fig1 baseline from #82: 241 iteration comments.

For fig2, count either:

1. explicit rows in `subregion_iteration_log.md` if the next refit creates one;
2. otherwise, a documented proxy: critique/adjudication loop count plus patch
   commits from first context-pack-backed refit to accepted/golden-ready state.

Stop condition for #95:

- material reduction versus fig1 baseline: direction remains promising;
- no meaningful reduction: record the context-pack direction as falsified or
  capped for this paper.

## Validation Checkpoint - 2026-07-02

Commands run after selecting `fig2_trap_design_space`:

```bash
cd plugins/figure-agent
bin/fig-agent context-pack fig2_trap_design_space --json
bin/fig-agent compile fig2_trap_design_space
bin/fig-agent helper critique_brief.py examples/fig2_trap_design_space
bin/fig-agent helper critique_lint.py fig2_trap_design_space
PYTHONPATH=scripts:scripts/quality uv run python scripts/critique_adjudication.py sync fig2_trap_design_space --preview
PYTHONPATH=scripts:scripts/quality uv run python scripts/critique_adjudication.py sync fig2_trap_design_space
bin/fig-agent loop fig2_trap_design_space --goal 'validate authoring context pack reduces figure 2 iterations to golden' --json
bin/fig-agent closeout fig2_trap_design_space --json
```

Evidence:

- context-pack resolved `docs/authoring-rules-pair001.md` and
  `docs/authoring-rules-project.md`; `read_only: true`.
- `/fig_compile` refreshed the render under the `paper_id: pair001` source set.
  It reported no text collisions, no text-boundary clashes, no label-path
  proximity candidates, and 4 passing semantic assertions.
- The host critique was refreshed to
  `critique_input_hash:
  sha256:982194dd21a583bcfd404c1a4fac4f5d12a336aa2ffd972cfed5357619a1a892`.
- `critique_lint.py` passed.
- adjudication sync preview was `normal_sync_safe: true`; decision `C001` was
  preserved with no added, dropped, or shape-changed decisions.
- latest loop evidence:
  `.scratch/fig-loop-runs/20260702-131410-888337-fig2_trap_design_space/iteration_001.json`.
- loop summaries: top-tier audit 10 pass / 0 weak / 0 fail / 0 needs_human;
  editorial art direction 10 pass / 0 weak / 0 fail / 0 needs_human; crop audit
  16 no_defect / 0 defect / 0 uncertain.
- closeout result: `closeout_complete: true`, render fresh, critique fresh,
  adjudication fresh, export fresh, loop rerun passed.

Measured proxy:

- New context-pack-backed source patch iterations in this validation window: 0.
- Mechanical refresh steps: 1 compile, 1 host critique refresh, 1 adjudication
  hash sync, 1 loop checkpoint.
- Current release blocker is not a plugin-quality blocker; it is the explicit
  human/release boundary: `acceptance_not_declared`.

Interpretation:

This candidate cannot prove a material reduction from first draft to
accepted/golden-ready because the figure was already post-refit before the
context-pack-backed measurement window began. Treat the north-star claim as
capped for this paper/fixture, not validated. The useful result is narrower:
after `paper_id: pair001`, the context-pack-backed refresh reached
workflow-ready with no additional TikZ patch needed, and the remaining
acceptance decision is human/release authority rather than deterministic
quality-kernel work.
