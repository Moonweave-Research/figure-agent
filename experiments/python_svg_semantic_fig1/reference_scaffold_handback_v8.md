# Fig1 Reference Scaffold Semantic Redraw Handback v8

## Goal

Re-align the Python SVG semantic renderer with the reference PNG as a visual scaffold rather than inventing new plot or layout language.

This pass starts with the highest-risk area: the center hero band/trap/DOS module.

## What Changed

- Added verifier checks for hero reference-scaffold anatomy.
- Added explicit hero mark roles in the SVG:
  - `band-edge`
  - `energy-axis`
  - `shallow-trap-state`
  - `deep-trap-state`
  - `trap-track`
  - `depth-guide`
  - `depth-label`
  - `dos-axis`
  - `dos-lobe-shallow`
  - `dos-lobe-deep`
  - `dos-label`
- Changed shallow/deep trap rendering from plain stacked lines to dashed energy-state tracks with discrete payload-count markers.
- Kept deep trap count and shallow trap count driven by `TrapLevelSet` payload values.
- Kept DOS lobe geometry driven by `DOSLobes` payload values.
- Removed the literal `bandgap` text from the hero and replaced it with a dashed guide line.
- Kept the reference PNG as visual scaffold only, not `ground_truth`.

## Why

The previous v7/v7b plot grammar work fixed the over-real mini-plot issue, but the hero still lacked explicit reference-scaffold structure. The renderer now records whether the hero is actually made from the intended schematic marks instead of only relying on object-level semantic groups.

## Verification

Fresh checks for this pass:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py
python -m py_compile experiments/python_svg_semantic_fig1/src/engine/primitives.py experiments/python_svg_semantic_fig1/src/render_fig1_l1.py experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py
```

The full closeout verification is recorded in the session final answer.

## Remaining Gap

This is not final figure art. The next likely pass should tune whole-card composition and text hierarchy against the reference scaffold:

- hero title/subtitle density,
- electrical evidence glyph size and balance,
- interpretation card density,
- probe card framing and labels.
