# Fig1 Overview v3 Candidate Plan

## Purpose

Create a non-golden candidate lane for improving the figure-1 overview without
mutating the accepted `fig1_overview_v2_pair_001_vault` fixture, generated
exports, release state, or tracked golden artifacts.

## Candidate Scope

This first candidate is a restrained TikZ refinement focused on Panel C. It
preserves panel roles, labels, semantic colors, force meanings, and the
real-space plus energy-diagram story.

Implemented source-level changes:

- add minimal white backplates to `mobility edge` and `shallow` labels
- pull the deep escape curve terminus slightly left/down to reduce optical
  crowding around the shallow band label

## Human Boundary

This candidate is not accepted and not golden. It must be compared against the
accepted v2 benchmark before any acceptance, export, publication, or golden
roll-forward decision.

Allowed next agent action:

```bash
./bin/fig-agent compile fig1_overview_v3_pair_001_vault
./bin/fig-agent status fig1_overview_v3_pair_001_vault --json
./bin/fig-agent drive fig1_overview_v3_pair_001_vault --mode review --goal fig1-v3-candidate --dry-run --json
```

Forbidden without explicit human approval:

- copy v3 outputs over v2
- mark v3 accepted
- run `--force-golden`
- edit generated SVG/PDF/PNG/TIF by hand
