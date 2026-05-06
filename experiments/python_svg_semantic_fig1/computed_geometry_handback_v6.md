# Fig1 Computed Scientific Geometry Handback v6

## Goal

Move the current renderer one level beyond semantic annotation and manual coordinate drawing: DOS lobes, P-E hysteresis, and I(t) decay should be generated from typed semantic payload parameters through reusable geometry functions.

## What Changed

- Added `src/engine/scientific_geometry.py`.
- Added computed geometry functions for:
  - Gaussian-mixture DOS lobes.
  - Parametric P-E hysteresis loops.
  - Log-log power-law current decay.
- Extended typed payloads in `src/engine/domain_primitives.py` so curve models and sampling parameters live in scene data:
  - `DOSLobes.model`, sigma pairs, and sample count.
  - `PEHysteresisPlot.model` and branch sample count.
  - `PowerLawDecayPlot.model`, log-axis range, and sample count.
  - `ISPDPlot.model`, sigma pairs, and sample count.
- Updated `src/render_fig1_l1.py` so renderer output is driven by those payload values rather than renderer-local curve constants.
- Updated `src/engine/primitives.py` so DOS lobe paths are built from sampled geometry points.
- Reused the power-law decay primitive in both the electrical evidence card and the interpretation card.

## Verifier Upgrade

`src/verify_fig1_semantics.py` now checks:

- The expected computed model IDs are present in typed payloads and rendered SVG semantic metadata.
- Computed deep DOS extent and approximate sampled area dominate shallow DOS.
- The computed P-E loop has branch separation consistent with remanence.
- The computed power-law decay is monotonic in log-time and decays for negative slope.
- Mutating trap, DOS, P-E, and decay payloads changes the visible SVG geometry even after `data-payload-geometry` attributes are stripped.

## Result

This is now stronger than a comment-annotated SVG redraw. The scene model carries the scientific curve model choice and parameters, and the renderer dispatches from semantic object kind to reusable geometry functions.

The important improvement is not just visual quality. The renderer now has a mechanical contract: if a semantic payload changes, the generated path geometry changes and the verifier can catch a detached hard-coded drawing.

## Remaining Gap

This is still schematic scientific geometry, not a calibrated measurement reconstruction.

- DOS lobe shape is plausible and parameterized, but not fitted to ISPD data.
- P-E hysteresis is a compact parametric schematic, not a ferroelectric/material model.
- I(t) is mathematically log-log power-law, but tick placement and typography still need publication polish.
- The visual grammar is still hand-tuned by card-local boxes; there is no automatic label/collision optimizer yet.

## Next Goal

The next useful pass is visual-scientific polish on top of computed geometry:

- Add reusable axis/tick primitives with consistent scientific typography.
- Improve tick labels and minor ticks for log plots.
- Make DOS/band alignment more publication-like.
- Add label collision checks for curve labels, Et labels, and probe arrows.
- Keep the semantic payload and verifier checks as the non-negotiable base layer.
