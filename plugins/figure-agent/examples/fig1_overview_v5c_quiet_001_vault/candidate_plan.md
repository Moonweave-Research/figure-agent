# Fig1 Overview v5c Quiet-Editorial Candidate Plan

## Purpose

Create a non-golden visual-elevation candidate from `fig1_overview_v5b_editorial_001_vault`.
This lane tests whether Figure 1 feels more like a final manuscript figure when the Row 2
bridge layer is treated as a quiet editorial cue rather than an explicit schematic scaffold.

## Candidate Scope

v5c is the quieter editorial option:

- keep v5b's unboxed Row 2
- retain only faint D/E/F column separators
- further demote the bridge bracket, central up-arrow, `convergent evidence`, and modality labels
- do not remove the convergence cue entirely; keep enough structure for the three evidence columns to read as linked to Panel C
- preserve Panel C's v4 label/path readability fix
- do not change panel roles, scientific labels, force direction, or trap semantics

## Validation Snapshot

- `./bin/fig-agent compile fig1_overview_v5c_quiet_001_vault` exits 0
- collisions: 0
- text-boundary clashes: 0
- label-path proximity candidates: 0
- tex assertions: pass
- physics grounding: grounded
- export generated with `--skip-critique` for visual comparison only
- critique brief generation succeeds and creates print-scale audit crops
- build PNG SHA-256: `76835d132f70db41d008829ef1c06a18ffc07d44c06e10eeea05871814f83b82`
- export SVG SHA-256: `a208379611507eec68a0353799b6ff5b9e678fc7253996d8f7d6fe1e880a3b6c`

## Current Judgment

v5c is a modest improvement over v5b, not a transformative redraw. The bridge tier is quieter,
so Row 2 reads slightly less like a tool-generated scaffold and slightly more like manuscript
evidence panels. Use v5c as the current main visual-elevation branch; keep v5b as fallback if a
human reviewer decides the convergence relationship has become too weak.

## Human Boundary

This candidate is not accepted and not golden. Before any release/golden decision,
run a fresh grounded critique and compare against v5b, v4, and the accepted baseline.
