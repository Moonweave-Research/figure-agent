# Fig1 Overview v5a Polish Candidate Plan

## Purpose

Create a non-golden visual-elevation candidate from `fig1_overview_v4_pair_001_vault`.
This lane preserves the v4 scientific structure while reducing the visual weight of the
Row 2 frame and bridge annotations.

## Candidate Scope

v5a is the conservative option:

- keep the Row 2 outer frame, but reduce it to a very light editorial hairline
- keep the D/E/F separators, but shorten and lighten them
- demote the bridge bracket, central up-arrow, `convergent evidence`, and modality labels
- do not change panel roles, scientific labels, force direction, or Panel C trap geometry

## Validation Snapshot

- `./bin/fig-agent compile fig1_overview_v5a_polish_001_vault` exits 0
- collisions: 0
- text-boundary clashes: 0
- label-path proximity candidates: 0
- tex assertions: pass
- physics grounding: grounded
- export generated with `--skip-critique` for visual comparison only
- build PNG SHA-256: `e5a3c734546aacd01ba42d3eb9a26bec16ac8bb72fa536216d5d1856a67a4cdb`
- export SVG SHA-256: `730296c1aa3707917590bf27a173c6d9f7398a6d77ea43d443f45a2f054079a2`

## Current Judgment

v5a is safer than v5b but less transformative. It improves the heavy boxed feel
without changing the figure's first-read logic. It is useful as a low-risk fallback,
not as the strongest answer to the “final Nature Communications polish” concern.

## Human Boundary

This candidate is not accepted and not golden. Before any release/golden decision,
run a fresh grounded critique and compare against v4 and the accepted baseline.
