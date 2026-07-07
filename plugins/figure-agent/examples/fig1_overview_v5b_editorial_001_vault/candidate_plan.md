# Fig1 Overview v5b Editorial Candidate Plan

## Purpose

Create a non-golden visual-elevation candidate from `fig1_overview_v4_pair_001_vault`.
This lane tests whether Figure 1 feels more like a final manuscript figure when Row 2
is less boxed and less visibly scaffolded.

## Candidate Scope

v5b is the editorial option:

- remove the enclosing Row 2 outer box
- retain only faint D/E/F column separators
- demote the bridge bracket, central up-arrow, `convergent evidence`, and modality labels
- preserve Panel C's v4 label/path readability fix
- do not change panel roles, scientific labels, force direction, or trap semantics

## Validation Snapshot

- `./bin/fig-agent compile fig1_overview_v5b_editorial_001_vault` exits 0
- collisions: 0
- text-boundary clashes: 0
- label-path proximity candidates: 0
- tex assertions: pass
- physics grounding: grounded
- export generated with `--skip-critique` for visual comparison only
- build PNG SHA-256: `df1490890db7f67c648b9862d61f267bfa7b00c2f7f35a795a7dff21c87ff87a`
- export SVG SHA-256: `4f9d58a3fcf6a367ab8d63243b329f4e989067b3d0a9f2d8ade39ab68853468e`

## Current Judgment

v5b is the stronger direction. Removing the enclosing Row 2 box reduces the tool/UI
feel and lets D/E/F read more like manuscript evidence panels. It still needs a fresh
grounded critique before it can become a formal candidate, but it is the better branch
for the next visual-elevation iteration.

## Human Boundary

This candidate is not accepted and not golden. Before any release/golden decision,
run a fresh grounded critique and compare against v4 and the accepted baseline.
