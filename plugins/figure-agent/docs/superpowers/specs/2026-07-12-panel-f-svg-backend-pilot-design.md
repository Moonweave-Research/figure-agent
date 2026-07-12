# Panel F SVG Backend Pilot Design

**Status:** Approved experiment design; not product authority

## Goal

Determine whether an editable semantic SVG implementation of the approved Panel
F apparatus motif can approach the current TikZ primitive without weakening its
scientific topology, finish checks, reproducibility, or human-review boundary.

## Architecture

The existing `panel-f-floating-cantilever.contract.yaml` remains the shared
semantic authority. The TikZ snippet remains the visual baseline. A new focused
Python renderer reads that contract and emits only the apparatus fragment as
editable SVG groups with stable instance-prefixed semantic IDs.

The renderer is intentionally independent of the rejected sulfur-trap grammar
and its generic backend profiles. It supports only the existing Panel F motif.
It does not compose the whole Fig1, draw force annotations, or decide that SVG
is superior.

## Evidence

The pilot produces a deterministic SVG, a rasterized PNG, a TikZ-baseline crop,
an equal-boundary comparison sheet, and a hash-bound receipt. Machine checks
cover semantic group coverage, electrical and mechanical relation bindings,
visible contours, deterministic replay, artifact freshness, and absence of
fixture-local labels or force arrows.

The receipt records machine evidence separately from two pending human fields:

- `semantic_legibility_verdict`
- `visual_quality_vs_tikz`

Neither field has an accepted default. SVG promotion remains unauthorized until
a named human judges the bound comparison.

## Boundaries

- Do not modify or replace the approved TikZ primitive.
- Do not edit the historical sulfur-trap grammar or backends.
- Do not render the whole Fig1 through SVG.
- Do not add a general illustration language or style DSL.
- Do not treat pixel similarity as publication quality.
- Keep SVG editable and free of embedded raster images, scripts, filters, and
  external URLs.

## Success condition

The experiment is review-ready when clean replay produces byte-identical SVG,
the semantic topology and visible-object gates pass, and the bound comparison
packet exists. It becomes a reusable SVG backend candidate only after the human
verdict says it is semantically legible and not materially worse than TikZ.

