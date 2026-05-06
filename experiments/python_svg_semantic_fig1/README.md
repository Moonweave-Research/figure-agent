# Fig1 Python SVG Semantic Experiment

This folder contains two generations of the Fig1 redraw experiment.

## Current Reference-Based Pilot

Use these files for the current semantic-driven reference-layout renderer:

- `src/engine/scene.py`
- `src/engine/style.py`
- `src/engine/primitives.py`
- `src/engine/domain_primitives.py`
- `src/engine/scaffold.py`
- `src/fig1_l1_scene.py`
- `src/render_fig1_l1.py`
- `src/verify_fig1_semantics.py`
- `src/verify_fig1_scaffold_contract.py`
- `src/verify_fig1_causal_binding.py`
- `src/verify_fig1_causal_visibility.py`
- `src/verify_fig1_physics_sanity.py`
- `src/fig1_visual_policies.py`
- `src/run_fig1_gates.py`
- `src/verify_fig1_baseline_hash.py`
- `src/test_fig1_physics_sanity.py`
- `src/check_fig1_docs_manifest.py`
- `src/fig_probe_01_scene.py`
- `src/render_fig_probe_01.py`
- `src/verify_fig_probe_01_contracts.py`
- `src/fig_probe_02_scene.py`
- `src/render_fig_probe_02.py`
- `src/verify_fig_probe_02_contracts.py`
- `src/engine/scientific_plots.py`
- `visual_layout.yaml`
- `scaffold_contract_v1.md`
- `causal_reference_binding_v16.md`
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
- `scaffold_contract_handback_v15.md`
- `causal_reference_handback_v16.md`
- `causal_visibility_handback_v17.md`
- `causal_readability_handback_v18.md`
- `reference_fidelity_execution_prompt_v19.md`
- `reference_fidelity_audit_v19.md`
- `reference_fidelity_handback_v19.md`
- `physics_sanity_inventory_v20.md`
- `physics_sanity_contract_v20.md`
- `physics_sanity_gate_handback_v20.md`
- `framework_probe_01_handback.md`
- `framework_probe_02_handback.md`
- `reference_scaffold_first_pivot_plan.md`

The current renderer is scaffold-contract-driven for layout and semantic-driven for scientific payloads: `src/engine/scaffold.py` normalizes `visual_layout.yaml` into `ScaffoldContract.schema_version == "scaffold_contract_v1"`, scene objects keep typed payloads, rendering dispatches by object kind, and the SVG contains semantic IDs plus payload-derived geometry tokens. The v6 layer also computes DOS, P-E, and power-law decay path geometry from semantic payload model parameters instead of renderer-local curve constants.

The v7b layer keeps `drawsvg` as the semantic SVG compositor, but uses Matplotlib only as a scientific schematic calculator for log spacing, curve sampling, and payload-scaled placement. P-E, I(t), and ISPD are rendered as reference-style measurement glyphs, not literal mini publication plots: no plot frames, numeric tick labels, dense minor ticks, or grids. The v8 layer starts the broader reference-scaffold redraw by adding explicit hero band/trap/DOS mark roles and payload-count trap-state markers. The v9 layer replaces the generic Gaussian-looking DOS lobes with a reusable reference-style DOS schematic primitive shared by the hero DOS and interpretation mini-DOS. The v10 layer changes that primitive from fixed Bezier glyphs to payload-sampled asymmetric density profiles, so `deep_sigma`, `shallow_sigma`, and `samples` affect the visible DOS silhouette. The v11 layer adds a schematic polish pass over the sampled DOS paths: the hero deep lobe silhouette is remapped for a cleaner shoulder/tail, the trap-depth label is separated from the red lobe, and the mini-DOS keeps the shallow/deep lobe roles while reducing label clutter. The v12 layer starts a whole-figure cohesion pass from the panel-by-panel audit: hero typography is restrained, interpretation flow is no longer four boxed UI steps, and the electrical panel now has a compact conclusion cue tying the P-E and current-decay evidence together. The v13 layer continues that audit into the support panels: the origin panel is changed from a checklist into a compact composition relation, and the probe panel loses the boxed footer and heavy inset-shadow treatment while keeping the same force semantics. The v14 layer adds global composition roles for panel titles, support-to-hero flow arrows, and panel conclusions, then documents which parts are reusable asset candidates versus Fig1-only layout boundaries. The verifier uses Shapely and svgelements through `uv` to check schematic label containment while also rejecting over-real plot roles and enforcing DOS lobe separation, local DOS bounds, threshold guides, sampled DOS profile paths, low-density DOS tails, DOS-owned trap-depth annotation, hero DOS label/lobe clearance, mini-DOS label composition, v12 panel-composition constraints, v13 support-panel cohesion constraints, and v14 global composition/asset-boundary constraints.

The reference PNG is layout/style evidence only for this pilot. It is not ground truth and not a pixel-tracing target: `visual_layout.yaml` converts the reference into explicit card bounds, local card boxes, object assignments, and flow anchors, then `src/engine/scaffold.py` exposes those facts as the scaffold contract. The scene payload drives the rendered scientific geometry inside those regions.

The v16 causal binding layer keeps that visual scaffold authority unchanged while treating the user-provided causal diagram as a semantic reference only. It binds the narrative chain `I(t) ~ t^-n -> n -> Debye exp(-t/tau) -> tau_d -> g(Et)`, S-rich segments, localized traps, chemical/physical origin cues, and the converged trap-depth picture into typed payload fields and a separate verifier. The causal diagram is not ground_truth and is not a pixel-tracing target.

The v17 causal visibility layer makes selected v16 bindings visible without replacing the scaffold: origin labels show `S-rich segments` and `localized traps`, the current-decay plot shows `extract n`, the interpretation flow shows `I(t) ~ t^-n -> n -> Debye exp(-t/tau) -> tau_d -> g(Et)`, and the hero callout names the `Converged trap-depth picture`. This is an intentional visual semantic update and still requires human visual review before publication-grade approval.

The v18 readability polish keeps the v17 semantic content unchanged while repositioning and scaling those existing visible causal cues. It also adds `src/run_fig1_gates.py` as a thin runner for the existing Fig1 gates and `src/verify_fig1_baseline_hash.py` to pin the settled v18 baseline hash. No absolute min-font-size verifier is added; readability remains human-review territory, and human visual review remains required before publication-grade approval.

The v19 reference-fidelity pass starts from `reference_fidelity_execution_prompt_v19.md` and `reference_fidelity_audit_v19.md`. It keeps the existing scaffold and semantics, then strengthens only the interpretation and electrical evidence panels: the interpretation chain regains lightweight step hierarchy, the Debye bridge/conclusion band read more deliberately, and the electrical schematic plots gain stronger axis/curve/label hierarchy without adding real plot frames or dense numeric ticks. Human visual review remains required before publication-grade approval.

The v20 physics sanity layer starts from the v20 physics sanity inventory and adds a separate basic-academic correctness gate. It audits energy ordering, trap ordering, decay notation, Debye-to-`g(Et)` causal semantics, reference authority, claim overreach, and probe charge/electrode consistency. `physics_sanity_contract_v20.md` defines hard-fail, deferred-fail, and document-only boundaries; `src/verify_fig1_physics_sanity.py` implements the current hard failures; and `src/test_fig1_physics_sanity.py` mutates payloads to prove the gate rejects known bad states. The unresolved `ForceArrow` `force_target` ambiguity remains a warning until the payload can state which object the force acts on; if that field appears, the gate immediately applies target-specific vector checks rather than silently passing. This is not publication-grade theory validation; it is a guard against clearly wrong sign, direction, ordering, model-chain, and claim errors.

## Second-Figure Framework Probe

`fig_probe_01` is a deliberately small second semantic figure. It is not a publication-quality Fig2 draft; it exists to test whether the shared `engine/` scene model, style tokens, semantic grouping, trap-state rendering, and payload-sampled DOS primitive can render a non-Fig1 composition without importing Fig1-specific policy modules.

Important interpretation: this probe is architecture-only evidence. It is not visual-quality evidence and should not be used to argue that semantic-first layout synthesis is sufficient.

Run it with:

```bash
uv run --with drawsvg python experiments/python_svg_semantic_fig1/src/render_fig_probe_01.py
python experiments/python_svg_semantic_fig1/src/verify_fig_probe_01_contracts.py
```

The probe writes `fig_probe_01_semantic.svg` and `fig_probe_01_semantic.png`. Its verifier checks source boundary isolation from Fig1 policy modules, payload-derived trap role counts, DOS sample exposure, and absence of Fig1 `data-panel-role` attributes.

`fig_probe_02` is the stronger composition-pressure probe. It keeps the full Fig1 canvas scale and a five-panel structure with one central mechanism panel, four support panels, support-to-center flow arrows, electrical readouts, trap-spectrum readout, and a device-response cue. It still avoids Fig1-specific verifier/policy imports and writes only `data-probe2-role` composition roles.

Important interpretation: this probe increases object and panel pressure, but its awkward visual structure shows that count/role correctness is not enough. It is visual failure evidence for pure semantic-first composition, not proof of publication-grade framework quality.

Run it with:

```bash
uv run --with drawsvg --with matplotlib --with numpy python experiments/python_svg_semantic_fig1/src/render_fig_probe_02.py
python experiments/python_svg_semantic_fig1/src/verify_fig_probe_02_contracts.py
```

The probe writes `fig_probe_02_semantic.svg` and `fig_probe_02_semantic.png`. Its verifier checks Fig1-scale canvas pressure, one-center-plus-four-support layout, source boundary isolation from Fig1 modules, payload-derived trap role counts, DOS sample exposure, and absence of Fig1 `data-panel-role` leakage.

## Reference-Scaffold-First Pivot

The experiment now treats `reference_scaffold_first_pivot_plan.md` as the next direction document. The key decision is to stop treating the semantic scene as a layout generator. A good reference, sketch, or human-authored scaffold should define panel bounds, local boxes, object-to-slot mapping, flow anchors, and visual hierarchy first; semantic payloads then control scientific meaning, computed geometry, roles, and mutation safety inside that scaffold.

Fig1 v14 remains the byte-identity baseline for structure-only work:

```text
8291c26721d83444d5232108ad692c1baafa9651652a04cdb08eb6b900bdf879
```

Future real figures should not start from blank semantic synthesis. They should start from an approved scaffold, then bind semantic objects into it.

The Fig1 scaffold contract is locked in `scaffold_contract_v1.md`: the source file is `visual_layout.yaml`, the source file format is JSON, and the normalized schema version is `scaffold_contract_v1`. An approved scaffold requires panel roles, panel-to-panel flow anchors, hero identification, and a one-line human sign-off that the scaffold is composition-grade. This scaffold step makes the reference dependency explicit; it does not remove the need for a good reference, sketch, or human composition pass.

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
python experiments/python_svg_semantic_fig1/src/verify_fig1_scaffold_contract.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_causal_binding.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_causal_visibility.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_physics_sanity.py
python experiments/python_svg_semantic_fig1/src/run_fig1_gates.py
python experiments/python_svg_semantic_fig1/src/verify_fig1_baseline_hash.py
PYTHONPATH=experiments/python_svg_semantic_fig1/src python -m unittest discover -s experiments/python_svg_semantic_fig1/src -p 'test_fig1_physics_sanity.py' -v
python -m xml.etree.ElementTree experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg
rsvg-convert -w 1595 -h 986 experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg -o /tmp/fig1_reference_semantic_check.png
```

`verify_fig1_semantics.py` checks the required object kinds, trap/DOS dominance, trap energy ordering, computed curve-model sanity, historical reference card bounds and local boxes from `visual_layout.yaml`, center hero placement, support-to-hero flow arrows, reference probe force cues, evidence modalities, hero reference-scaffold roles, hero DOS morphology, sampled DOS density paths, hero DOS label/lobe clearance, mini-DOS label count and lobe avoidance, semantic SVG bboxes, schematic plot roles, rejection of over-real plot frames/tick labels/dense ticks, schematic label containment, forbidden actuator/force-balance framing terms, generated artifacts, and visible-geometry payload mutation behavior. `verify_fig1_scaffold_contract.py` is the explicit scaffold verifier for panel loading, local box containment, object-slot binding, flow-anchor binding, and reference provenance. `verify_fig1_causal_binding.py` checks that the v16 causal diagram stays semantic-only while binding the experiment-to-Debye-to-`g(Et)` chain and molecular-origin cues into payloads. `verify_fig1_causal_visibility.py` checks that those causal bindings are visible as role-tagged SVG text. `verify_fig1_physics_sanity.py` checks basic academic/physics invariants and reports the deferred probe `force_target` ambiguity as a warning. `run_fig1_gates.py` chains the Fig1 gates including the pinned baseline hash check. Fig1-specific visual policy caps from v12-v14 live in `fig1_visual_policies.py`, README/handback governance lives in `check_fig1_docs_manifest.py`, and physics-sanity gate design starts from `physics_sanity_inventory_v20.md`.
