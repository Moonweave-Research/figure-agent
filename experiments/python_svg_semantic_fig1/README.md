# Fig1 Python SVG Semantic Experiment

This folder contains two generations of the Fig1 redraw experiment.

## Current Reference-Based Pilot

Use these files for the current semantic-driven reference-layout renderer:

- `src/engine/scene.py`
- `src/engine/style.py`
- `src/engine/primitives.py`
- `src/engine/domain_primitives.py`
- `src/fig1_l1_scene.py`
- `src/render_fig1_l1.py`
- `src/verify_fig1_semantics.py`
- `src/fig1_visual_policies.py`
- `src/check_fig1_docs_manifest.py`
- `src/engine/scientific_plots.py`
- `visual_layout.yaml`
- `reference_layout_spec_v1.md`
- `fig1_reference_semantic.svg`
- `fig1_reference_semantic.png`
- `reference_vs_fig1_reference_semantic.png`
- `feasibility_handback_v2.md`
- `visual_polish_handback_v1.md`
- `visual_polish_handback_v2.md`
- `visual_polish_handback_v3.md`
- `visual_grammar_handback_v4.md`
- `visual_constraint_handback_v5.md`
- `computed_geometry_handback_v6.md`
- `hybrid_scientific_plot_grammar_v7.md`
- `scientific_plot_grammar_handback_v7.md`
- `reference_scaffold_handback_v8.md`
- `dos_reference_schematic_handback_v9.md`
- `dos_density_profile_handback_v10.md`
- `dos_schematic_polish_handback_v11.md`
- `visual_cohesion_handback_v12.md`
- `support_panel_cohesion_handback_v13.md`
- `global_composition_asset_boundary_handback_v14.md`

The current renderer is semantic-driven: scene objects have typed payloads, rendering dispatches by object kind, and the SVG contains semantic IDs plus payload-derived geometry tokens. The v6 layer also computes DOS, P-E, and power-law decay path geometry from semantic payload model parameters instead of renderer-local curve constants.

The v7b layer keeps `drawsvg` as the semantic SVG compositor, but uses Matplotlib only as a scientific schematic calculator for log spacing, curve sampling, and payload-scaled placement. P-E, I(t), and ISPD are rendered as reference-style measurement glyphs, not literal mini publication plots: no plot frames, numeric tick labels, dense minor ticks, or grids. The v8 layer starts the broader reference-scaffold redraw by adding explicit hero band/trap/DOS mark roles and payload-count trap-state markers. The v9 layer replaces the generic Gaussian-looking DOS lobes with a reusable reference-style DOS schematic primitive shared by the hero DOS and interpretation mini-DOS. The v10 layer changes that primitive from fixed Bezier glyphs to payload-sampled asymmetric density profiles, so `deep_sigma`, `shallow_sigma`, and `samples` affect the visible DOS silhouette. The v11 layer adds a schematic polish pass over the sampled DOS paths: the hero deep lobe silhouette is remapped for a cleaner shoulder/tail, the trap-depth label is separated from the red lobe, and the mini-DOS keeps the shallow/deep lobe roles while reducing label clutter. The v12 layer starts a whole-figure cohesion pass from the panel-by-panel audit: hero typography is restrained, interpretation flow is no longer four boxed UI steps, and the electrical panel now has a compact conclusion cue tying the P-E and current-decay evidence together. The v13 layer continues that audit into the support panels: the origin panel is changed from a checklist into a compact composition relation, and the probe panel loses the boxed footer and heavy inset-shadow treatment while keeping the same force semantics. The v14 layer adds global composition roles for panel titles, support-to-hero flow arrows, and panel conclusions, then documents which parts are reusable asset candidates versus Fig1-only layout boundaries. The verifier uses Shapely and svgelements through `uv` to check schematic label containment while also rejecting over-real plot roles and enforcing DOS lobe separation, local DOS bounds, threshold guides, sampled DOS profile paths, low-density DOS tails, DOS-owned trap-depth annotation, hero DOS label/lobe clearance, mini-DOS label composition, v12 panel-composition constraints, v13 support-panel cohesion constraints, and v14 global composition/asset-boundary constraints.

The reference PNG is layout/style evidence only for this pilot. It is not ground truth and not a pixel-tracing target: `visual_layout.yaml` converts the reference into explicit card bounds, local card boxes, object assignments, and flow anchors, then the scene payload drives the rendered geometry inside those regions.

## Legacy Annotated Redraw

These files are the legacy annotated redraw from the earlier pass:

- `src/semantic_scene.py`
- `src/fig1_scene.py`
- `src/render_semantic_fig1.py`
- `src/verify_semantic_scene.py`
- `semantic_fig1.svg`
- `semantic_fig1.png`
- `reference_vs_semantic_fig1.png`
- `feasibility_handback.md`
- `capability_log.md`

The legacy annotated redraw is kept for provenance and comparison. It is not the current Fig1 L1 semantic engine target.

## Verification

Run the current pilot with:

```bash
uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools python experiments/python_svg_semantic_fig1/src/render_fig1_l1.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_semantics.py
python experiments/python_svg_semantic_fig1/src/check_fig1_docs_manifest.py
python -m xml.etree.ElementTree experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg
rsvg-convert -w 1595 -h 986 experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg -o /tmp/fig1_reference_semantic_check.png
```

`verify_fig1_semantics.py` checks the required object kinds, trap/DOS dominance, trap energy ordering, computed curve-model sanity, reference card bounds and local boxes from `visual_layout.yaml`, center hero placement, support-to-hero flow arrows, reference probe force cues, evidence modalities, hero reference-scaffold roles, hero DOS morphology, sampled DOS density paths, hero DOS label/lobe clearance, mini-DOS label count and lobe avoidance, semantic SVG bboxes, schematic plot roles, rejection of over-real plot frames/tick labels/dense ticks, schematic label containment, forbidden actuator/force-balance framing terms, generated artifacts, and visible-geometry payload mutation behavior. Fig1-specific visual policy caps from v12-v14 live in `fig1_visual_policies.py`, while README/handback governance lives in `check_fig1_docs_manifest.py`.
