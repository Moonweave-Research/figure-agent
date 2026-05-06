# Framework Probe 02 Handback

## Purpose

`fig_probe_02` is the second framework probe after the Fig1 v14 closeout. It corrects the main limitation of `fig_probe_01`: the first probe only proved that the engine could render a small non-Fig1 smoke test, but it did not apply Fig1-level composition pressure.

`fig_probe_02` uses a Fig1-scale canvas and a five-panel scientific schematic structure:

- four support panels
- one central mechanism panel
- support-to-center flow arrows
- material, electrical, trap-spectrum, and device-response cues
- central band/trap/DOS composition using payload-driven trap counts and sampled DOS geometry

It remains a framework probe, not a publication-quality Fig2 draft.

## Added assets

- `src/fig_probe_02_scene.py`
- `src/render_fig_probe_02.py`
- `src/verify_fig_probe_02_contracts.py`
- `fig_probe_02_semantic.svg`
- `fig_probe_02_semantic.png`

## Boundary checks

The probe verifier enforces:

- no imports or source references to `fig1_l1_scene`, `render_fig1_l1`, `verify_fig1_semantics`, or `fig1_visual_policies`
- Fig1-scale canvas: `1595 x 986`
- exactly five panels: one `hero` center plus four `supporting` panels
- required semantic objects for composition, electrical readout, band/trap/DOS, readout flow, and device response
- rendered panel/title/flow/trap/DOS/readout/device roles under `data-probe2-role`
- no Fig1 `data-panel-role` leakage in the SVG
- payload-derived trap role counts and DOS sample exposure

## Result

Initial RED failed because `fig_probe_02_scene.py` did not exist. After adding the scene and renderer, `python experiments/python_svg_semantic_fig1/src/verify_fig_probe_02_contracts.py` passes.

The result is the first meaningful stress test of the v14 boundary split: `engine/` can support a second Fig-scale semantic schematic, while Fig1 visual policies remain isolated.

## Visual interpretation

This probe is not a publication-grade figure and should not be treated as proof that semantic-first layout synthesis works. It increases canvas size, panel count, object count, and role pressure, but its awkward structure shows the remaining gap: count/role correctness is not the same as reference-quality composition.

The useful conclusion is narrower. `fig_probe_02` proves that the engine boundary can carry a larger non-Fig1 scene. It also provides failure evidence that future real figures need an approved reference scaffold before semantic payload binding starts.
