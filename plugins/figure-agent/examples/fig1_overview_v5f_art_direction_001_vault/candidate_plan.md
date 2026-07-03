# Fig1 Overview v5f Art-Direction Candidate Plan

## Purpose

Create a new non-golden art-direction lane from
`fig1_overview_v5e_aggressive_001_vault` after v5e proved too local. v5d and
v5e remain fallback candidates. v5f tests a larger composition redesign aimed at
a first-glance Nature / Nature Materials overview: stronger whitespace, clearer
panel hierarchy, more breathable Row 2 evidence, and a more heroic Panel C.

This lane is not an acceptance lane. It must not mutate accepted, golden,
release, export-decision, or human-decision state.

## Failure Criteria

Discard or redesign the first v5f pass if any of these are true:

- the full render changed-pixel ratio is below 2 percent versus v5d;
- Panel C still reads as one of several equal panels rather than the hero;
- Row 2 still reads as three apparatus/tool panels instead of three evidence
  modes;
- Panel F improves only by enlarging labels while preserving the same crowded
  charge/force/electrode/air-gap composition;
- print-thumbnail text loses `mobility edge`, `shallow/deep`, `high n`, or
  `q_tr` / `trapped charge`;
- the redesign breaks the locked physics invariants in `briefing.md`,
  `design.md`, `authoring_contract.md`, or `theory_guard.md`.

## Tool Gate

The required gate order for this candidate is fixed:

1. `./bin/fig-agent status fig1_overview_v5f_art_direction_001_vault --json`
2. `./bin/fig-agent context-pack fig1_overview_v5f_art_direction_001_vault`
3. source redesign
4. `./bin/fig-agent compile fig1_overview_v5f_art_direction_001_vault`
5. v5d/v5e/v5f contact sheets: full render, print thumbnail, and Panel C/D/E/F
   crops
6. pixel-diff versus v5d and human visual-comparison notes
7. fresh `critique.md` and `critique_lint.py` pass
8. `./bin/fig-agent adjudicate fig1_overview_v5f_art_direction_001_vault`
9. `./bin/fig-agent export fig1_overview_v5f_art_direction_001_vault`
10. final `status --json` with `workflow_ready=true`, `release_ready=false`,
    and human acceptance as the remaining blocker

## Art-Direction Moves

- Recompose Panel C as the unmistakable hero: more visual mass, cleaner right
  energy-diagram lane, stronger model/result hierarchy, and preserved
  mobility-edge / shallow / deep / Delta-E_t semantics.
- Reframe Row 2 D/E/F as three evidence modes. Apparatus should support the
  result claims rather than dominate them.
- Redesign Panel F around charge, force, electrode, and air gap as one coherent
  mechanism scene. Do not treat label enlargement alone as a solution.
- Make Panel D/E/F result curves and mechanisms read before equipment boxes.
- Remove unnecessary micro-labels, repeated decoration, and same-weight line
  clutter so the full page feels more editorial and less tool-generated.

## Human Gate

v5f can become a promotion candidate only after direct comparison against v5d and
v5e using the contact sheets and pixel-diff evidence. Compile, critique,
adjudication, and export success do not authorize accepted/golden/final status.

## Initial Gate Record

- Fork created from `fig1_overview_v5e_aggressive_001_vault`.
- `build/` and `exports/` were not copied.
- `critique.md` was not copied.
- v5f starts with `acceptance_state=NOT_DECLARED` and `release_ready=false`.
- Fresh critique/adjudication/export evidence must be created after the source
  redesign.
