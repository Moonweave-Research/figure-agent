# Fig1 DOS Schematic Polish and Label Composition Handback v11

## Goal

Polish the v10 payload-sampled DOS schematic without changing the semantic scene model or replacing the sampled DOS profiles with traced artwork.

The reference PNG remains layout/style evidence only. It is not ground truth and not a pixel-tracing target.

## What Changed

- Added verifier checks for DOS label composition:
  - hero shallow/deep labels must keep clear of their lobe bodies,
  - hero trap-depth label and guide must keep readable clearance from the deep lobe,
  - mini-DOS label count is capped for the small interpretation-card box,
  - mini-DOS labels must remain inside local bounds and avoid the lobe bodies.
- Kept `drawsvg` as compositor and kept the v10 payload-sampled asymmetric DOS paths.
- Added a v11 schematic polish marker to sampled DOS paths:
  - `data-dos-profile="payload-sampled-asymmetric"`
  - `data-dos-polish="schematic-v11"`
  - `data-dos-samples="..."`
- Tuned the visible DOS silhouette mapping so the hero deep lobe is less mechanically broad, with a cleaner shoulder and lower tail while still responding to `deep_sigma`, `shallow_sigma`, and `samples`.
- Split the hero trap-depth annotation into two short lines and moved it into clear space to the right of the red lobe.
- Moved the hero `deep` label off the red contour.
- Simplified the interpretation-card mini-DOS by removing the small shallow/deep text labels and reducing the trap-depth cue to compact `Et`.

## RED Check

The new verifier checks failed against the existing v10 artifact before the rendering changes:

```text
hero DOS depth label collides with the deep lobe body
```

## Generated Artifacts

- `fig1_reference_semantic.svg`
- `fig1_reference_semantic.png`
- `reference_vs_fig1_reference_semantic.png`

## Verification

The implementation keeps the sampled DOS profile contract and passed the semantic verifier after regeneration:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py
python -m xml.etree.ElementTree experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg
python -m py_compile experiments/python_svg_semantic_fig1/src/engine/primitives.py experiments/python_svg_semantic_fig1/src/render_fig1_l1.py experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py experiments/python_svg_semantic_fig1/src/fig1_l1_scene.py
rsvg-convert -w 1595 -h 986 experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg -o /tmp/fig1_reference_semantic_check.png
```

Two consecutive SVG regenerations produced the same hash:

```text
868e85df036168976e14075b067cda35f373b3522742bc8a7cdfafaba019b335
```
