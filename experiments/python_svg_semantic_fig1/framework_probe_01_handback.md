# Framework Probe 01 Handback

## Purpose

`fig_probe_01` is a second semantic figure used to test the framework boundary after the Fig1 v14 closeout. It is not a publication-quality Fig2 draft and does not use a reference PNG.

The probe asks one narrow question: can the shared semantic scene model and engine primitives render a non-Fig1 figure without importing Fig1-specific policy modules?

## Added assets

- `src/fig_probe_01_scene.py`
- `src/render_fig_probe_01.py`
- `src/verify_fig_probe_01_contracts.py`
- `fig_probe_01_semantic.svg`
- `fig_probe_01_semantic.png`

## Boundary checks

The probe verifier enforces these constraints:

- probe source files must not reference `fig1_l1_scene`, `verify_fig1_semantics`, or `fig1_visual_policies`
- the scene id must be `fig_probe_01`
- the layout must use exactly three non-hero columns
- the probe must include `BandDiagram`, `TrapLevelSet`, `DOSLobes`, and `LayoutFlow`
- rendered trap state roles must be derived from the payload counts
- rendered DOS paths must expose the payload sample count
- rendered SVG must not leak Fig1 `data-panel-role` attributes

## Result

Initial RED failed because `fig_probe_01_scene.py` did not exist. After adding the minimal scene and renderer, `python experiments/python_svg_semantic_fig1/src/verify_fig_probe_01_contracts.py` passes.

The visible result is intentionally modest. Its value is architectural: it confirms that the v14 split left a reusable engine path for a second semantic figure while keeping Fig1 policy caps isolated.

## Visual interpretation

This probe must not be used as visual-quality evidence. It only checks that a non-Fig1 scene can render through the shared engine without importing Fig1-specific policy modules.

The probe is too small and too compositionally simple to test whether the framework can produce a publication-grade scientific schematic. Its result supports engine-boundary reuse, not semantic-first layout generation.
