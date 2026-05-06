# Python SVG Semantic Engine v0 Handback

## Verdict

Semantic-driven rendering worked better than the annotated renderer once the visual target was also made explicit scene data.

The first semantic pass proved typed payload dispatch, but the L1 1:2:1:1 strip did not encode the visual grammar of the supplied reference. This pass promotes the reference composition into `visual_layout.yaml`: canvas size, five card regions, local card boxes, center hero, object assignments, and support-to-hero arrows are now data consumed by both scene construction and verification.

This is a better foundation than the annotated redraw because meaning and layout are now separable payloads rather than comments around hard-coded drawing. It is still not manuscript-final; the renderer needs another visual-polish pass before it can replace a human reference redraw.

## What Changed

- Added reusable engine modules under `src/engine/`.
- Added `visual_layout.yaml` as the machine-readable reference layout contract.
- Added `reference_layout_spec_v1.md` as the human-readable visual target.
- Updated `src/fig1_l1_scene.py` so scene regions, local boxes, canvas size, flow arrows, evidence colors, probe cues, and panel assignments come from the reference contract.
- Updated `src/render_fig1_l1.py` so renderer dispatch consumes typed semantic payloads plus reference-layout regions.
- Updated `src/verify_fig1_semantics.py` to check semantic object coverage, trap/DOS dominance, reference card bounds, local boxes, center hero placement, support-to-hero flow, secondary Maxwell cue treatment, artifact generation, and payload-mutation response.

Generated current outputs:

- `fig1_reference_semantic.svg`
- `fig1_reference_semantic.png`
- `reference_vs_fig1_reference_semantic.png`

## Reusable Object Kinds

Most reusable:

- `LayoutFlow`
- `BandDiagram`
- `TrapLevelSet`
- `DOSLobes`
- `EvidenceTrio`
- `PEHysteresisPlot`
- `PowerLawDecayPlot`
- `ISPDPlot`
- `MacroscopicProbe`
- `PolymerCantilever`
- `Electrode`
- `ForceArrow`

Reusable with paper-specific constraints:

- `SulfurPolymerOrigin`
- `DeepTrapHero`
- `TrapModelFlow`
- `MaxwellAttractionCue`

`MaxwellAttractionCue` is reusable only as a secondary reference/probe cue. It should not become a generic force-balance panel primitive.

## Remaining Visual Polish

- The center hero now follows the reference placement, but its band/DOS typography and label spacing still need manual tightening.
- The electrical evidence card has the correct two-plot structure, but axes and tick density remain schematic.
- The interpretation card now matches the reference role, but the Debye/tau and ISPD inset need finer spacing.
- The macroscopic probe follows the reference composition with dominant red repulsion and secondary blue Maxwell cue, but cantilever curvature, charge placement, and electrode rendering still need Illustrator/TikZ-level refinement.
- The renderer does not trace the PNG, so it will not automatically recover the LMM reference's organic curve tension or micro-layout.

## Main Engine Readiness

This is strong enough to become a candidate Python-first figure engine layer, not yet the main default layer.

Promotion gates:

- Add serialized scene fixtures for at least two more figures.
- Define a stable object-kind registry and versioned payload schemas.
- Split visual layout contracts from domain semantic payloads cleanly.
- Add overlap/layout regression checks beyond semantic assertions.
- Add a TikZ backend prototype that consumes the same scene model.

## TikZ Backend Needs

A later TikZ backend should consume the scene model and visual layout contract, not the SVG output.

It would need:

- Canvas and region bounds from `visual_layout.yaml`.
- Renderer-neutral coordinates and normalized panel-local anchors.
- Stable semantic IDs, object kinds, and z-order phases.
- Typed physical payloads for traps, DOS lobes, charge signs, electrodes, and force cues.
- Style tokens instead of raw SVG-specific filters and gradients.
- Text labels separated from geometry so TikZ can choose math mode, line breaks, and font sizing.
- Backend capability flags for shadows, gradients, rounded panels, path fills, and texture approximations.

## Non-Goals Preserved

- No SVG-to-TikZ conversion.
- No plugin command integration.
- No new slash command.
- No automatic image tracing.
- No generic chemistry renderer.
- No mutation of the main `plugins/figure-agent/examples/fig1_overview` files.
