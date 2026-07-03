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
- redraw slice 1 has modified the figure composition by removing the Row 1 to
  Row 2 bracket/up-arrow connector scaffold;
- slice 1 keeps v5c as fallback and should be treated as an incremental
  editorial cleanup, not a promotion-quality redraw by itself.

## Redraw Slice 1 -- Connector Typography

Change:

- removed the faint bracket, vertical tick marks, and center up-arrow between
  Row 1 and Row 2;
- kept `convergent evidence` as a typographic row-level cue;
- kept `kinetic`, `ISPD`, and `mechanical` labels inside the existing Row 2
  text-boundary contract.

Validation:

- `./bin/fig-agent compile fig1_overview_v5d_redraw_001_vault` exits `0`;
- text-boundary detector reports `0` candidates;
- label-path detector reports `0` candidates;
- visual metrics report `visual_clash=39`, `undeclared_geometry=91`,
  `scaffold_load.score=130`, `ink_density=0.1059`, `edge_density=0.016184`.

Interpretation:

- this improves the row transition by removing a tool-like construction layer;
- it does not yet prove v5d is visually better than v5c overall;
- the next slice should target a larger perceptual quality lever, such as Panel
  C label hierarchy, Row 2 apparatus density, or print-scale crop review.

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
