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
- redraw slice 2 has separated the Panel C `shallow` label, red escape curve,
  and Delta-E_t caliper lanes;
- these slices keep v5c as fallback and should be treated as incremental
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
- the next slice should target a larger perceptual quality lever, such as Row 2
  apparatus density, crop review, or global panel hierarchy.

## Redraw Slice 2 -- Panel C Right-Lane Separation

Change:

- moved `shallow` out of the far-right Delta-E_t caliper lane and into a
  clearer mid-right label lane;
- re-routed the red deep-escape curve so it stays left of the blue label;
- preserved the mobility-edge reference, shallow/deep semantics, and the
  vertical Delta-E_t scale.

Validation:

- `./bin/fig-agent compile fig1_overview_v5d_redraw_001_vault` exits `0`;
- text-boundary detector reports `0` candidates;
- label-path detector reports `0` candidates;
- visual metrics report `visual_clash=39`, `undeclared_geometry=91`,
  `scaffold_load.score=130`, `ink_density=0.105884`,
  `edge_density=0.016174`.

Interpretation:

- this directly addresses the prior top-right Panel C crowding concern around
  `mobility edge`, `shallow`, and escape arrows;
- it is a local readability improvement, not yet a full aesthetic reset.

## Redraw Slice 3 -- Panel D High-n Label Lane

Change:

- replaced the path-attached `high n` label with a smaller fixed right-lane
  label;
- moved the label away from the Debye dashed cliff so the reference curve and
  red power-law label do not read as one mark at print scale;
- preserved the red/blue power-law geometry and the Debye reference geometry.

Validation:

- `./bin/fig-agent compile fig1_overview_v5d_redraw_001_vault` exits `0`;
- text-boundary detector reports `0` candidates;
- label-path detector reports `0` candidates;
- visual metrics report `visual_clash=38`, `undeclared_geometry=91`,
  `scaffold_load.score=234`, `ink_density=0.105806`,
  `edge_density=0.016141`.

Interpretation:

- this is a targeted print-scale readability fix for Panel D, not a global
  redesign;
- the crop and 178 mm print-scale evidence now separate `high n` from the
  Debye reference well enough to keep iterating elsewhere.

## Redraw Slice 4 -- Panel E Derive Label Demotion

Change:

- reduced the `derive` transformation label size in Panel E;
- moved the label slightly right/up so it reads as a small inter-plot cue
  rather than a dominant annotation over the Deep peak;
- preserved the vertical derive arrow, V_s(t) trace, g(E_t) distribution, and
  tau_d interval.

Validation:

- `./bin/fig-agent compile fig1_overview_v5d_redraw_001_vault` exits `0`;
- text-boundary detector reports `0` candidates;
- label-path detector reports `0` candidates;
- visual metrics report `visual_clash=38`, `undeclared_geometry=91`,
  `scaffold_load.score=234`, `ink_density=0.105714`,
  `edge_density=0.01612`.

Interpretation:

- this reduces Panel E's annotation weight without changing the scientific
  reading path;
- it is still a local polish pass, not enough by itself to promote v5d.

## Redraw Slice 5 -- Panel F qtr Notation Probe

Attempted but not landed:

- tested replacing the Panel F `$q_{tr}$` label with longer roman-subscript
  forms to improve print-scale readability;
- the longer label did not improve the crop-level read and triggered a layout
  drift warning for the `qtr` reference lane;
- the attempted source edit was reverted, and no commit was made for this
  probe.

Interpretation:

- Panel F notation readability remains a candidate concern, but a longer inline
  math label is not the safe next lever;
- any future Panel F work should first decide whether to keep `q_{tr}`, change
  the semantic notation globally, or move the label into a dedicated legend
  lane rather than stretching the current local label.

## Current Gate -- Host Vision Critique Required

Current status after Slice 4:

- `render_state=FRESH`;
- `critique_state=MISSING`;
- `export_state=MISSING`;
- first blocker is `critique_missing`;
- safe next command from status is
  `/fig_critique fig1_overview_v5d_redraw_001_vault`.

The generated critique brief for the current render is schema
`figure-agent.critique.v1.17` with critique input hash
`sha256:7887edcc6606fa885befabc9532a0407f87d377a75556640cecf949840ff6700`.
It requires full-render review, high-zoom crop review, print-scale review, and
complete accounting of 38 visual-clash candidates plus 91 undeclared-geometry
candidates before `critique.md` can be treated as valid.

Do not hand-write a shortcut critique or promote/export this fixture before
that host vision critique exists. The local polish pass has reached the point
where further edits should be driven by grounded critique findings, not by
one-off taste adjustments.

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
