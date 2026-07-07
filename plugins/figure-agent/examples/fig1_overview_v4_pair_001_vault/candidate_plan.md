# Fig1 Overview v4 Candidate Plan

## Purpose

Create a non-golden candidate lane for improving the figure-1 overview without
mutating the accepted `fig1_overview_v2_pair_001_vault` fixture, the current v3
baseline, generated exports, release state, or tracked golden artifacts.

The `reference` entry is a symlink to the v3 fixture reference pack to avoid
committing duplicate binary reference assets for this temporary candidate.

## Candidate Scope

This candidate is a restrained TikZ refinement focused on Panel C. It preserves
panel roles, labels, semantic colors, force meanings, and the real-space plus
energy-diagram story.

Implemented source-level changes:

- right-align and slightly demote `mobility edge` so it no longer extends into
  the escape-arrow / Delta-E_t optical lane
- keep `shallow` above the deep-escape polyline bbox while moving it into clear
  whitespace between the trap levels and Delta-E_t caliper
- pull the deep escape curve terminus slightly left/down to reduce optical
  crowding around the shallow band label
- update `spec.yaml` label-path-proximity coordinates for the moved deep escape
  curve so detector evidence tracks current geometry

Validation snapshot:

- `./bin/fig-agent compile fig1_overview_v4_pair_001_vault` exits 0
- collisions: 0
- text-boundary clashes: 0
- label-path proximity candidates: 0
- tex assertions: pass
- physics grounding: grounded
- status render state: fresh
- remaining detector debt: visual/undeclared geometry candidates remain
  unadjudicated because no formal `critique.md` has been written for this
  candidate

## Human Boundary

This candidate is not accepted and not golden. It must be compared against the
accepted v2 benchmark before any acceptance, export, publication, or golden
roll-forward decision.

Allowed next agent action:

```bash
./bin/fig-agent compile fig1_overview_v4_pair_001_vault
./bin/fig-agent status fig1_overview_v4_pair_001_vault --json
./bin/fig-agent drive fig1_overview_v4_pair_001_vault --mode review --goal fig1-v4-candidate --dry-run --json
```

Forbidden without explicit human approval:

- copy v4 outputs over v2
- mark v4 accepted
- run `--force-golden`
- edit generated SVG/PDF/PNG/TIF by hand
