# Fig1 Reference Local Layout Handback v2

## Goal

Move the next layer of visual control from renderer-local offsets into `visual_layout.yaml`, then add a small evidence-plot polish pass.

## What Changed

- Added region-local boxes to `visual_layout.yaml`.
- Added `LayoutBox` and `Column.box()` to the scene model.
- Updated `fig1_l1_scene.py` so local boxes are parsed from the reference layout contract.
- Updated `render_fig1_l1.py` so key local geometry uses named boxes:
  - sulfur origin motif boxes
  - hero band/DOS/callout boxes
  - evidence plot boxes
  - interpretation flow/plot/ISPD/callout boxes
  - probe frame/callout boxes
- Added more reference-like evidence plot details:
  - P-E zero axes
  - larger hysteresis loop
  - current-decay log ticks
  - dashed slope guide
- Updated verification so local boxes are checked against `visual_layout.yaml`.

## Result

The renderer is still not a pixel-traced reconstruction, but the layout authority is now deeper than card bounds. The scene and renderer consume named internal visual boxes, which gives the next polish pass a clearer control surface.

## Remaining Gap

The next pass should focus on the hero and probe:

- Hero deep-state level density and spacing.
- DOS lobe label placement.
- Probe cantilever curve and charge placement.
- Text collision checks for card-edge labels such as `Sx` and `S85`.
