# Fig1 Overview v5e Aggressive Editorial Candidate Plan

## Purpose

Create a non-golden aggressive redraw lane from
`fig1_overview_v5d_redraw_001_vault`. v5d is now a stable fallback with fresh
critique/export evidence, but its improvement was mostly local and conservative.
v5e exists to test a larger visual jump: stronger hero hierarchy, less
tool-scaffold feel, and a more editorial Panel F mechanism scene.

## Candidate Scope

v5e is an experiment lane, not an acceptance lane:

- preserve v5d as fallback;
- preserve the A/B/C/D/E/F story and the physics invariants;
- allow larger composition and hierarchy edits than v5d;
- prefer a better first-glance figure over detector appeasement during the first
  pass, then repair detector/accounting regressions afterward;
- do not mutate accepted, golden, export, release, or human-decision state;
- stop or revert if the result is merely different rather than clearly stronger.

## Aggressive Design Moves

The first pass targets visible quality, not tiny cleanup:

- strengthen Panel C as the model hero by making the right energy-diagram lane
  feel less like a label stack and more like a single composed trap scene;
- make Row 2 read as three evidence modes rather than three tool panels by
  reducing secondary apparatus dominance and tightening graph/result hierarchy;
- redesign Panel F's charge/force story so `q_{tr}`, Coulomb repulsion, electrode,
  and air gap read as one polished mechanism rather than scattered labels;
- keep the figure white, restrained, and journal-like; do not add decorative
  gradients, cover-scene effects, or unsupported visual metaphors.

## First Pass Success Criteria

After the first compile, v5e should be judged visually before promotion:

- the full render should look materially more finished than v5d at first glance;
- Panel F should no longer have the weak `q_{tr}` print-scale issue identified
  in v5d critique finding C001;
- Panel D `high n` should no longer feel like a soft afterthought;
- Panel C should still preserve mobility-edge, shallow/deep, and Delta-E_t
  semantics without recreating the earlier top-right overlap;
- detector regressions are acceptable only if they are explainable and repairable.

## Initial Gate State

Expected immediately after fork:

- `build/` and `exports/` are absent;
- `critique.md` and `critique_adjudication.yaml` are absent;
- `acceptance_state=NOT_DECLARED`;
- `release_ready=false`;
- the next valid step is source redraw, compile, visual inspection, then fresh
  critique/export if the result is worth keeping.

## Slice 1 Result -- Panel F Charge Story + Panel D High-n Authority

Completed first source pass:

- Panel F charge markers were enlarged and given restrained red halos so the
  trapped-charge family reads at print scale.
- Panel F `q_{tr}` was replaced by a compact two-leader callout reading
  `trapped charge` plus `q_{\mathrm{tr}}`; this directly targets v5d critique
  C001 without changing the Coulomb-only physics story.
- Panel D `high n` was promoted into a white-backed, larger print-scale tag near
  the red sulfur trace endpoint; this targets v5d critique C002.
- `spec.yaml` row-2 text allowlists were updated for the new `trapped` and
  `charge` callout words.

Validation after Slice 1:

- `./bin/fig-agent compile fig1_overview_v5e_aggressive_001_vault` exits 0.
- Collision check: pass.
- Text-boundary check: pass after narrowing the Panel F callout.
- Label-path proximity check: pass.
- Tex assertion: pass.
- Physics grounding: grounded.
- Layout drift: OK for covered anchors; expected skips remain for uncovered
  anchors such as `qtr`.
- Remaining detector candidates are unadjudicated because this lane intentionally
  has no fresh `critique.md` yet.

Current next gate:

- `status` reports `critique_missing`; run a fresh reference-grounded critique
  before export or any comparison/promotion decision.

## Human Boundary

This lane is not accepted and not golden. Creating, compiling, or exporting v5e
does not authorize publication or replace v5d. Promotion requires explicit
comparison against v5d, v5c, and the accepted v4 baseline.
