# Fig1 v5 Visual Elevation Packet

Date: 2026-07-03

## Objective

Test whether the v4 Figure 1 overview can move closer to a Nature Communications
final-figure impression without changing the scientific story or mutating accepted/golden state.

## Baseline

`fig1_overview_v4_pair_001_vault` is the safe baseline. It has fresh render, fresh critique,
fresh export, and detector readiness, but visually still reads slightly boxed/instrumented in
Row 2.

## Candidates

### v5a polish

Fixture: `examples/fig1_overview_v5a_polish_001_vault`

Scope:

- preserve v4 structure
- lighten Row 2 outer frame and internal separators
- demote bridge/caption/modality annotation weight

Validation:

- compile: pass
- collisions: 0
- text-boundary clashes: 0
- label-path proximity candidates: 0
- tex assertions: pass
- physics grounding: grounded
- build PNG SHA-256: `e5a3c734546aacd01ba42d3eb9a26bec16ac8bb72fa536216d5d1856a67a4cdb`
- export SVG SHA-256: `730296c1aa3707917590bf27a173c6d9f7398a6d77ea43d443f45a2f054079a2`

Judgment:

Low-risk improvement. It keeps the v4 reading logic but does not substantially change the
first impression.

### v5b editorial

Fixture: `examples/fig1_overview_v5b_editorial_001_vault`

Scope:

- remove the enclosing Row 2 outer box
- retain only faint column separators
- demote bridge/caption/modality annotation weight
- preserve v4 Panel C readability fix

Validation:

- compile: pass
- collisions: 0
- text-boundary clashes: 0
- label-path proximity candidates: 0
- tex assertions: pass
- physics grounding: grounded
- build PNG SHA-256: `df1490890db7f67c648b9862d61f267bfa7b00c2f7f35a795a7dff21c87ff87a`
- export SVG SHA-256: `4f9d58a3fcf6a367ab8d63243b329f4e989067b3d0a9f2d8ade39ab68853468e`

Judgment:

Stronger direction. Removing the enclosing Row 2 box reduces the tool/UI impression and makes
D/E/F read more like manuscript evidence panels. It became the source branch for v5c.

### v5c quiet editorial

Fixture: `examples/fig1_overview_v5c_quiet_001_vault`

Scope:

- preserve v5b's unboxed Row 2
- keep the convergence cue, but reduce the bridge bracket/up-arrow/caption/modality tier
- keep the scientific panel roles and v4 Panel C readability fix unchanged

Validation:

- compile: pass
- collisions: 0
- text-boundary clashes: 0
- label-path proximity candidates: 0
- tex assertions: pass
- physics grounding: grounded
- critique brief generation: pass
- build PNG SHA-256: `76835d132f70db41d008829ef1c06a18ffc07d44c06e10eeea05871814f83b82`
- export SVG SHA-256: `a208379611507eec68a0353799b6ff5b9e678fc7253996d8f7d6fe1e880a3b6c`

Judgment:

Current best branch, but only by a modest margin. v5c is slightly less scaffolded than v5b and
therefore closer to the desired manuscript-panel feel. It is not a full visual reset and should
not be described as final without fresh grounded critique.

## Boundary

All v5 lanes are non-golden and `acceptance=NOT_DECLARED`. Exports were generated with
`--skip-critique` for comparison only. Neither lane should be treated as final until a fresh
grounded critique/adjudication pass is written.

## Recommended Next Step

Continue to use `fig1_overview_v5c_quiet_001_vault` as the current best v5
fallback candidate, but do not treat it as the final Figure 1 art direction.
The next useful iteration is a deliberate v5d redraw lane, not another blind
micro-polish pass on v5c.

- keep v5c as the current fallback/current candidate;
- open `fig1_overview_v5d_redraw_001_vault` as a non-accepted source-side lane;
- require a fresh `/fig_critique fig1_overview_v5c_quiet_001_vault` before any
  acceptance or release step;
- compare any v5d redraw against v5c and v5b before promotion;
- fall back to v5b only if the v5c convergence cue is judged too quiet.

## P0 Decision Update

Date: 2026-07-03

Decision: start a v5d ground-up redraw candidate lane while preserving v5c as
the current fallback. Do not accept, golden-promote, or release any v5 lane yet.

Evidence:

- `compare-fixtures v5b v5c --baseline v4` reports `needs_human_critique` for
  both candidates because fresh critique is missing.
- v5b visual metrics: ink density `0.106532`, edge density `0.016345`,
  visual-clash candidates `39`, undeclared-geometry candidates `96`, scaffold
  load `high` with score `240`.
- v5c visual metrics: ink density `0.105872`, edge density `0.016187`,
  visual-clash candidates `39`, undeclared-geometry candidates `93`, scaffold
  load `high` with score `237`.
- v5c is therefore measurably a little lighter than v5b, but not enough to
  justify calling the figure final.
- `fig-agent queue --mode review` classifies v5c's current operator bucket as
  `human_critique_blocker`, not `hard_publication_blocker`; the immediate block
  is critique freshness, while acceptance/release is a later protected boundary.

Stop condition for this packet:

- v5c remains the current non-accepted fallback;
- v5d may be created as a source-side fork;
- no release, golden, attestation, or accepted state is mutated by this
  decision.

## v5d Bootstrap Result

Date: 2026-07-03

Created fixture: `examples/fig1_overview_v5d_redraw_001_vault`.

Bootstrap evidence:

- created with `fig-agent fork-fixture fig1_overview_v5c_quiet_001_vault
  fig1_overview_v5d_redraw_001_vault --reason "ground-up editorial redraw
  candidate after v5b/v5c comparison"`;
- stale `build/` and `exports/` artifacts were not copied;
- reference context was explicitly relinked to the same tracked reference pack
  used by v5b/v5c;
- `fig-agent compile fig1_overview_v5d_redraw_001_vault` exits `0`;
- post-compile status: `render_state=FRESH`, `critique_state=MISSING`,
  `export_state=MISSING`, `acceptance_state=NOT_DECLARED`;
- advisory visual metrics currently match v5c because the redraw content has
  not been changed yet: ink density `0.105872`, edge density `0.016187`,
  visual-clash candidates `39`, undeclared-geometry candidates `93`;
- next safe command is `/fig_critique fig1_overview_v5d_redraw_001_vault`.

Interpretation: v5d is now a working redraw lane, but not yet an improved
redraw. The next implementation slice must change the actual figure composition
before any comparison can claim visual improvement.
