# Issue 95 - Figure #2 Candidate Selection

Status: candidate selected; validation not yet started

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
