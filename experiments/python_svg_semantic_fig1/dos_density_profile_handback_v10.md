# Fig1 DOS Density Profile Handback v10

## Goal

Fix the v9 limitation where DOS lobes no longer overlapped but still read as fixed schematic blobs instead of density-of-states profiles.

## Root Cause

The v9 primitive prevented overlap with a fixed reference-style Bezier glyph. It used payload width and center values for placement, but it did not use `shallow_sigma`, `deep_sigma`, or `samples` to construct the visible lobe outline. The result was a clean icon, not a payload-sampled DOS density silhouette.

## What Changed

- Replaced the fixed deep/shallow Bezier lobe paths with sampled asymmetric density profiles.
- The shared DOS primitive now uses:
  - `shallow_sigma`
  - `deep_sigma`
  - `samples`
  - lobe center
  - lobe width and height
- Added SVG markers on DOS lobe paths:
  - `data-dos-profile="payload-sampled-asymmetric"`
  - `data-dos-samples="..."`
- Tuned the deep DOS payload sigma from broad capsule-like values to narrower asymmetric tail values:
  - hero `deep_sigma=(0.24, 0.28)`
  - interpretation mini-DOS `deep_sigma=(0.24, 0.28)`

## Verifier Changes

`src/verify_fig1_semantics.py` now rejects DOS lobes that are only role-tagged Bezier blobs.

The v10 checks require:

- sampled DOS profile markers,
- enough visible sampled path segments,
- low-density tails near the threshold and band-edge side of the deep lobe,
- the existing v9 DOS bounds, threshold, depth-guide, and label containment checks.

The RED checks before implementation failed with:

```text
hero dos-lobe-shallow is not a sampled DOS density profile
hero deep DOS lobe lacks a clear low-density tail at the threshold or band edge
```

## Remaining Gap

This pass makes the DOS morphology payload-sampled and more density-like. It is still a schematic overview element, not a quantitative ISPD/DOS fit. The next visual pass should tune label spacing and the whole figure's card density.
