# Causal Readability Handback v18

## Scope

This pass is a readability polish and gate-hardening pass over the v17 visible causal cues. It has no new semantic content, does not create a new scaffold, and does not change the semantic payload model.

## Implemented Boundary

- The original aesthetic reference remains layout/style evidence only.
- The user-provided causal diagram remains semantic/narrative evidence only.
- The renderer still uses drawsvg as the SVG compositor.
- The v18 visual change only repositions and scales existing visible causal cues.
- No absolute min-font-size verifier was added; readability remains human-review territory for this figure.

## Visible Changes

- Origin causal cue labels were enlarged and spaced inside the existing origin relation strip.
- Current-decay `extract n` was enlarged and moved below the fitted decay line.
- Interpretation chain text was split where needed and scaled within the existing flow strip.
- Hero `Converged trap-depth picture` callout was enlarged inside the existing callout box.

## Gate Changes

- `src/run_fig1_gates.py` chains the existing Fig1 gates and summarizes pass/fail.
- `src/verify_fig1_baseline_hash.py` pins the settled v18 SVG baseline hash.

## Hash Record

- previous hash: `26d0e4eaa91b6b6b187d385d9bdcbf0caf7f27c478bae703113eb5e37203d092`
- new hash: `b43c192481c799e895bd616b57fdd3731dfc58b3bf2d5fcee932d204592c207f`

## Review Gate

Human visual review is still required before treating this as publication-grade. The gates check contract, visibility, and baseline drift; they do not judge final aesthetics.
