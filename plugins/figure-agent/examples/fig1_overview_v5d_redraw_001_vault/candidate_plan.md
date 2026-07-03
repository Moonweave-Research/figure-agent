# Fig1 Overview v5d Redraw Candidate Plan

## Purpose

Create a non-golden redraw lane from `fig1_overview_v5c_quiet_001_vault`.
The v5b/v5c comparison showed v5c is the current safer fallback, but the
improvement over v5b is modest and both candidates still carry high scaffold
load. v5d exists to test a stronger editorial composition without mutating
accepted, golden, export, or release state.

## Candidate Scope

v5d is a redraw lane, not an acceptance lane:

- keep the same scientific story and A/B/C/D/E/F panel roles;
- keep v5c as fallback until v5d beats it in render, critique, and comparison;
- preserve the unboxed Row 2 direction unless the redraw creates a clearly
  stronger hierarchy;
- reduce the feeling of tool-scaffold construction, especially around Row 2
  connection logic and dense crop burden;
- improve Nature Communications-level finish through layout, hierarchy, stroke,
  whitespace, and print-scale readability;
- do not change force direction, trap semantics, material identity, or
  mechanistic labels without a separate semantic decision.

## Initial State

- source fork created by `fig-agent fork-fixture`;
- stale `build/` and `exports/` artifacts intentionally absent;
- `acceptance_state: NOT_DECLARED`;
- reference context is linked to the same reference pack used by v5b/v5c;
- `./bin/fig-agent compile fig1_overview_v5d_redraw_001_vault` exits `0`;
- post-compile state is `render_state=FRESH`, `critique_state=MISSING`,
  `export_state=MISSING`;
- current visual metrics still match v5c because no redraw content has been
  changed yet.

The next implementation slice must modify the figure composition itself before
claiming v5d is visually better than v5c.

## Comparison Requirements

Before promotion, v5d must be compared against:

- `fig1_overview_v5c_quiet_001_vault` as the current fallback;
- `fig1_overview_v5b_editorial_001_vault` as the louder editorial fallback;
- `fig1_overview_v4_pair_001_vault` as the accepted safe baseline.

Required evidence:

- fresh render and exports;
- detector reports and audit crops;
- advisory visual metrics;
- fresh grounded critique;
- explicit comparison packet showing whether v5d beats v5c strongly enough to
  justify leaving the current fallback.

## Human Boundary

This lane is not accepted and not golden. No release, final-artifact, human
attestation, or golden mutation is authorized by creating this fixture.
