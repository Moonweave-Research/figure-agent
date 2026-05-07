# Phase 3 — Pipeline-Level Quality Plan

Branch: `experiment/python-svg-semantic-fig1`
Pre-Phase-3 commit: `a8f0f54` (Phase 1+2 closed, schematic-grade)
Owner: Moon-python

This document is the single source of truth for Phase 3 execution.
The Ralph loop reads this file, picks the next unchecked task, executes it,
runs gates, ticks the box, and stops. Re-firing the prompt advances by one
unit until all five phases close.

## 0. Goal — Nature Communications Publication-Illustration Grade

All eight criteria must hold at end of Phase 3-E:

- [ ] (a) `uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools --with rdkit python plugins/figure-agent-py/scripts/pyfig.py verify-fig1` reports `fig1 gates passed: 8/8`
- [ ] (b) Sulfur chemistry rendered by RDKit (no hand-drawn S atom circles in `top_synthesis`)
- [ ] (c) ISPD g(Et), DOS lobes, and V_s(t) panels rendered by Matplotlib SVG fragments (no hand-drawn bell curves in those three panels)
- [ ] (d) Cantilever beam, electrode, charges, and release wells use SVG `<defs>` gradients/shadows (no flat fills in those primitives)
- [ ] (e) Hero panel `localized_traps` text is visually dominant: hero title size strictly greater than the largest support panel title size
- [ ] (f) `fig1_visual_judgment_report.md` contains zero `text-shape conflict` findings at `0.0px` distance
- [ ] (g) Panel density rebalanced: `localized_traps` ≤ 0.70, `vs_decay_module` ≥ 0.20, `ispd_module` ≥ 0.20 in the visual judgment report's "Panel Bounds And Density" table
- [ ] (h) `uv run --with drawsvg --with matplotlib --with numpy --with shapely --with svgelements --with svgpathtools --with rdkit python -m unittest discover -s experiments/python_svg_semantic_fig1/src -p 'test_fig1_*.py'` reports zero failures, zero errors

Out of scope:
- TikZ / lualatex
- measured-data plot production
- new panels beyond the existing six

## 1. Commit Discipline

- One commit per closed phase (5 commits total).
- Each phase commit message starts with `SEMANTIC.fig1: phase 3-X — <topic>`.
- Baseline-hash is updated only inside that phase's commit, never in a separate commit.
- Never amend `a8f0f54` or any prior commit.
- After each phase commit, the Ralph loop must re-read this plan file before continuing.

## 2. Phase 3-A — WIP Infrastructure Commit

Goal: commit the already-working library-fragment scaffolding, unblock 3-B/3-C.

Touched paths:
- `experiments/python_svg_semantic_fig1/src/engine/svg_fragments.py` (new, tracked)
- `experiments/python_svg_semantic_fig1/src/engine/matplotlib_subrenderers.py` (new, tracked, edited)
- `experiments/python_svg_semantic_fig1/src/engine/rdkit_subrenderers.py` (new, tracked)
- `experiments/python_svg_semantic_fig1/src/test_fig1_svg_fragments.py` (new, tracked)
- `experiments/python_svg_semantic_fig1/src/test_fig1_library_subrenderers.py` (new, tracked)
- `experiments/python_svg_semantic_fig1/src/test_fig1_visual_constraints.py` (new, tracked)
- `experiments/python_svg_semantic_fig1/src/preview_fig1_library_subrenderers.py` (new, tracked)
- `experiments/python_svg_semantic_fig1/src/preview_fig1_electrical_style_adapter.py` (new, tracked)
- `experiments/python_svg_semantic_fig1/src/test_fig1_electrical_style_adapter_integration.py` (DELETE — file is entirely about removed `pe_hysteresis`)
- `experiments/python_svg_semantic_fig1/src/test_fig1_physics_sanity.py` (edit — remove `test_rejects_invalid_pe_hysteresis_parameters`)
- `experiments/python_svg_semantic_fig1/src/test_fig1_svg_fragments.py` (edit — replace string literals `"pe_hysteresis"` / `"PEHysteresisPlot"` / `"electrical-pe-plot"` with surviving tokens, e.g. `"power_law_decay"` / `"PowerLawDecayPlot"` / `"electrical-decay-plot"`; this file tests the wrapper API generically)
- `experiments/python_svg_semantic_fig1/src/engine/matplotlib_subrenderers.py` (edit — delete `pe_hysteresis_fragment` + `_pe_points` + `MatplotlibPlotStyle.pe_label*` fields + pe-related branches in `fig1_electrical_style()` and `_default_plot_style()`; KEEP `PEHysteresisPlot` import only if Fig probe 02 codepath needs it transitively — currently it does not, this module imports it directly so the import line goes when pe_hysteresis_fragment goes)
- `experiments/python_svg_semantic_fig1/src/engine/domain_primitives.py` (NO EDIT — `PEHysteresisPlot` is consumed by Fig probe 02 in `fig_probe_02_scene.py`, `render_fig_probe_02.py`, `verify_fig_probe_02_contracts.py`, `engine/scientific_plots.py:pe_hysteresis_plan`, and `engine/scientific_geometry.py:pe_hysteresis_points`. Out of Phase 3 scope.)
- `experiments/python_svg_semantic_fig1/src/test_fig1_library_subrenderers.py` (edit — drop the four `pe_hysteresis_fragment` test methods; keep RDKit + power_law_decay tests)
- `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py` (edit — drop `PEHysteresisPlot` import, drop `pe_hysteresis_fragment` import, remove `"PEHysteresisPlot": _draw_pe_hysteresis` dispatch entry, delete `_draw_pe_hysteresis` body; this is dead code since the scene no longer creates a PEHysteresisPlot SemanticObject)
- `experiments/python_svg_semantic_fig1/src/preview_fig1_electrical_style_adapter.py` (edit — delete pe-specific imports, payload, and three `pe_hysteresis_fragment` calls; keep power_law_decay preview blocks. If the file becomes mostly empty, DELETE it instead.)
- `experiments/python_svg_semantic_fig1/src/preview_fig1_library_subrenderers.py` (edit — same disposition as above: delete pe-specific imports/payload/calls; keep power_law_decay preview. If empty, DELETE.)
- `plugins/figure-agent-py/scripts/pyfig.py` (edit — add `"rdkit"` to `RENDER_DEPS`)

Tasks (Ralph executes top-to-bottom):
- [x] 3-A.1 Audit `pe_hysteresis` usage: `grep -rn "pe_hysteresis\|PEHysteresisPlot\|pe_hysteresis_fragment" experiments/python_svg_semantic_fig1/src plugins/figure-agent-py`. Record results in this file under section 7 before deleting.
- [x] 3-A.2 In `render_fig1_l1.py`: drop `PEHysteresisPlot` import (line 28), drop `pe_hysteresis_fragment` import (line 37), remove the `"PEHysteresisPlot": _draw_pe_hysteresis` line from the renderer dispatch table (~line 102), delete the `_draw_pe_hysteresis` function body (starting line 1752).
- [x] 3-A.3 In `engine/matplotlib_subrenderers.py`: delete `pe_hysteresis_fragment` and `_pe_points`. Drop pe-specific fields from `MatplotlibPlotStyle` (`pe_label`, `pe_label_x`, `pe_label_y`). Drop pe-specific lines in `fig1_electrical_style()` and `_default_plot_style()`. Drop the `PEHysteresisPlot` name from the `engine.domain_primitives` import.
- [x] 3-A.4 In `preview_fig1_electrical_style_adapter.py` and `preview_fig1_library_subrenderers.py`: delete pe-related imports, payloads, and `pe_hysteresis_fragment` calls. If a file becomes degenerate (empty `main`, no remaining preview blocks), `git rm` it.
- [x] 3-A.5 Delete `test_fig1_electrical_style_adapter_integration.py` (`git rm`). Remove `test_rejects_invalid_pe_hysteresis_parameters` from `test_fig1_physics_sanity.py`. Drop the four pe-specific test methods from `test_fig1_library_subrenderers.py`. In `test_fig1_svg_fragments.py`, replace `"pe_hysteresis"` / `"PEHysteresisPlot"` / `"electrical-pe-plot"` string literals with `"power_law_decay"` / `"PowerLawDecayPlot"` / `"electrical-decay-plot"` so the wrapper-API test stays meaningful.
- [x] 3-A.6 Add `"rdkit"` to `RENDER_DEPS` tuple in `plugins/figure-agent-py/scripts/pyfig.py`.
- [x] 3-A.7 Re-grep `pe_hysteresis|PEHysteresisPlot|pe_hysteresis_fragment` under `experiments/python_svg_semantic_fig1/src/` ONLY (excluding fig_probe_02_*, render_fig_probe_02.py, verify_fig_probe_02_contracts.py, engine/scientific_plots.py:pe_hysteresis_plan, engine/scientific_geometry.py:pe_hysteresis_points which are scope-protected). Required: zero matches in fig1-named files and engine/matplotlib_subrenderers.py.
- [x] 3-A.8 Render fig1 via dispatcher and confirm baseline-hash unchanged (no semantic change). If hash drifts, investigate before continuing.
- [x] 3-A.9 Run all `test_fig1_*.py` with full deps (incl. rdkit). Required: zero failures, zero errors.
- [x] 3-A.10 Run gate suite via dispatcher. Required: 8/8.
- [x] 3-A.11 Stage only the in-scope paths above (use `git add` per path; for deletions use `git rm` or `git add -u <path>`). Skip `.agents/`, `.claude/`, `docs/` at repo root.
- [x] 3-A.12 Commit: `SEMANTIC.fig1: phase 3-A — commit library-fragment scaffolding + drop dead pe_hysteresis`.

Exit criteria for 3-A:
- All `pe_hysteresis*` symbols removed from src and tests.
- `git status --short` shows only `.agents/`, `.claude/`, `docs/` (root-level) as untracked.
- 8/8 gates pass via dispatcher.
- All `test_fig1_*.py` tests pass.
- Baseline-hash equals pre-Phase-3-A value.

## 3. Phase 3-B — Wire RDKit S8 Ring Into top_synthesis

Goal: replace hand-drawn S atom row with `s8_ring_fragment`. Single-panel, low-risk validation of library-fragment wiring pattern.

Touched paths:
- `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py` (edit `_draw_sulfur_polymer_origin` and import)
- `experiments/python_svg_semantic_fig1/visual_layout.yaml` (verify `s8_ring` local box matches fragment dimensions)
- `experiments/python_svg_semantic_fig1/src/verify_fig1_baseline_hash.py` (hash update only)
- `experiments/python_svg_semantic_fig1/fig1_reference_semantic.svg` + `.png` + comparison png + judgment report (artifact regen)

Tasks:
- [x] 3-B.1 Read `_draw_sulfur_polymer_origin` in render_fig1_l1.py end-to-end. Identify exact code block that draws the S8 ring shape (the eight `draw.Circle` ring) and the chain-S atom row.
- [x] 3-B.2 Replace the S8 ring block with `s8_ring_fragment(width=W, height=H)` where W,H come from `visual_layout.yaml.regions[top_synthesis].local_boxes.s8_ring`. Wrap with `wrapped_fragment_svg` and `draw.Raw`. Preserve `p.begin_semantic_group` / `end_semantic_group` boundaries and the `data-causal-role` attributes that downstream verifiers rely on.
- [x] 3-B.3 Verify the chain-S row stays hand-drawn for now (chain is a polymer, not a ring; deferred to a future phase). Document this in section 7.
- [x] 3-B.4 Render fig1, regenerate visual judgment report, recompute hash, update `EXPECTED_HASH` in `verify_fig1_baseline_hash.py`.
- [x] 3-B.5 Run gate suite. Required: 8/8. Fix causal-binding/causal-visibility immediately if RDKit-injected ids conflict with semantic data attributes.
- [x] 3-B.6 Commit: `SEMANTIC.fig1: phase 3-B — RDKit S8 ring in top_synthesis`.

Exit criteria for 3-B:
- top_synthesis panel renders S8 ring via RDKit (visible in PNG).
- 8/8 gates pass.
- All `test_fig1_*.py` pass.
- judgment report regenerated.

## 4. Phase 3-C — Matplotlib Fragments for ISPD / DOS / V_s(t)

Goal: replace three hand-drawn schematic plots with matplotlib SVG fragments. Promote orphan `vs_decay_module` to a real scene object.

Touched paths:
- `experiments/python_svg_semantic_fig1/src/engine/domain_primitives.py` (add `VsDecayPlot`)
- `experiments/python_svg_semantic_fig1/src/engine/matplotlib_subrenderers.py` (add `ispd_dos_fragment`, `dos_lobes_fragment`, `vs_decay_fragment`)
- `experiments/python_svg_semantic_fig1/src/fig1_l1_scene.py` (add `vs_decay_plot` SemanticObject, attach to `vs_decay_module` column)
- `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py` (rewrite `_draw_ispd_plot`, `_draw_dos_lobes`, `_draw_vs_decay_curve` to use fragments)
- `experiments/python_svg_semantic_fig1/visual_layout.yaml` (`vs_decay_module.objects` from `[]` to `["vs_decay_plot"]`)
- `experiments/python_svg_semantic_fig1/src/verify_fig1_scaffold_contract.py` (verify it accepts the new object; expect no edit needed)
- `experiments/python_svg_semantic_fig1/src/verify_fig1_baseline_hash.py` (hash update)
- artifacts (regen)

Tasks:
- [x] 3-C.1 Add `VsDecayPlot` dataclass to `engine/domain_primitives.py` with fields: `model`, `decay_form` ("non-debye-power-law"), `t_min`, `t_max`, `samples`, `color`, `label`, `axis_label_t`, `axis_label_v`.
- [x] 3-C.2 Add `vs_decay_fragment(payload, *, width, height, style)` in `matplotlib_subrenderers.py` mirroring `power_law_decay_fragment` shape (rc_context, log/lin axes, role tags). Use `subrenderer="matplotlib"`, `role="vs-decay-plot"`.
- [x] 3-C.3 Add `ispd_dos_fragment(payload, *, width, height, style)` and `dos_lobes_fragment(payload, *, width, height, style)`. Both render Gaussian-mixture lobes from the existing `ISPDPlot` / `DOSLobes` payloads. Roles `ispd-dos-plot` / `dos-lobes-plot`. Respect `MINI_DOS_MAX_LABELS=3` constraint by suppressing extra ticks.
- [x] 3-C.4 Add `vs_decay_plot` SemanticObject in `fig1_l1_scene.py`, column `col_vs_decay`. Update `Scene.objects` tuple. Update `visual_layout.yaml.regions[vs_decay_module].objects` to `["vs_decay_plot"]`.
- [x] 3-C.5 Rewrite `_draw_ispd_plot`, `_draw_dos_lobes`, `_draw_vs_decay_curve` to call the fragments via `wrapped_fragment_svg` + `draw.Raw`. Preserve all `data-causal-role`, semantic-group boundaries, and label text expected by verifiers.
- [x] 3-C.6 Render + regen judgment + run gates + update hash.
- [x] 3-C.7 Confirm density goal (g): `vs_decay_module ≥ 0.20`, `ispd_module ≥ 0.20`, `localized_traps ≤ 0.70`. If not met, adjust fragment width/height in scene before locking the hash.
- [ ] 3-C.8 Commit: `SEMANTIC.fig1: phase 3-C — matplotlib fragments for ISPD/DOS/Vs(t)`.

Exit criteria for 3-C:
- `vs_decay_module` no longer orphan (objects has 1 entry).
- Three plot panels rendered via matplotlib fragments.
- 8/8 gates pass; all tests pass.
- Density bands met per goal (g).

## 5. Phase 3-D — SVG `<defs>` Gradients + Shadows

Goal: depth/material illusion on hand-drawn primitives that remain after 3-B/3-C. No content change, only visual richness.

Touched paths:
- `experiments/python_svg_semantic_fig1/src/engine/primitives.py` or new `engine/svg_defs.py` (centralized gradient + filter builders)
- `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py` (call sites: `_cantilever_frame`, `_draw_polymer_cantilever`, `_draw_electrode`, `_draw_release_wells`, hero panel rect, charges)
- `experiments/python_svg_semantic_fig1/src/verify_fig1_baseline_hash.py` (hash update)
- artifacts (regen)

Tasks:
- [ ] 3-D.1 Create or extend `engine/svg_defs.py` (or add to `primitives.py`) with deterministic `id`-stable builders: `metallic_beam_gradient(id_, axis="vertical")`, `sphere_radial_gradient(id_, base_color)`, `well_depth_gradient(id_, well_color)`, `panel_drop_shadow_filter(id_, blur, offset)`. Each returns a `draw.Raw` defs string with stable id per call site.
- [ ] 3-D.2 Inject all four `<defs>` once at the top of `build_drawing` after the white background rect, before any panel renders.
- [ ] 3-D.3 Apply `metallic_beam_gradient` to cantilever beam fill in `_cantilever_frame`.
- [ ] 3-D.4 Apply `sphere_radial_gradient` to electrode body and the five trapped-charge circles.
- [ ] 3-D.5 Apply `well_depth_gradient` to the four release wells in `_draw_release_wells` (deeper well = darker base).
- [ ] 3-D.6 Apply `panel_drop_shadow_filter` to the hero panel rectangle only (per goal e — visual hierarchy hint).
- [ ] 3-D.7 Render + regen + gates + hash. Confirm causal-visibility still passes (gradient ids must not collide with semantic ids).
- [ ] 3-D.8 Commit: `SEMANTIC.fig1: phase 3-D — SVG defs gradients + hero shadow`.

Exit criteria for 3-D:
- `<defs>` block contains four gradient/filter elements.
- Cantilever, electrode, charges, wells, hero panel use those defs (visible in SVG source).
- 8/8 gates pass.
- Goal (d) satisfied.

## 6. Phase 3-E — Hierarchy + Text-Conflict Polish

Goal: close goals (e), (f), (g) — hero dominance, zero text-shape collisions, density bands held.

Touched paths:
- `experiments/python_svg_semantic_fig1/src/engine/style.py` (raise `hero_title_size`)
- `experiments/python_svg_semantic_fig1/src/render_fig1_l1.py` (label re-anchor: '−' on dos lobe, '+' on electrode, '(+) electrode' offset, panel-label 'a' offset, 'Maxwell attraction' / '+' separation, 'Coulomb F' offset from charge)
- `experiments/python_svg_semantic_fig1/src/verify_fig1_baseline_hash.py` (hash update)
- artifacts (regen, judgment regen)

Tasks:
- [ ] 3-E.1 Raise `Typography.hero_title_size` from 16.0 to ≥ 19.0 (must strictly exceed `support_title_size=13.5` and any other support-panel title used). Bump `subtitle_size` proportionally if needed for hero only.
- [ ] 3-E.2 Re-anchor every '−' label in `_draw_band_diagram` and `_draw_dos_lobes` to leave ≥ 4px from any path mark.
- [ ] 3-E.3 Re-anchor probe panel labels: '+' inside electrode kept ≥ 4px from electrode stroke; '(+) electrode' caption moved below the electrode, not on top of it; 'Maxwell attraction' separated from '+' by ≥ 8px; 'Coulomb F' moved away from charge circles.
- [ ] 3-E.4 Re-position panel-label letters ('a'..'f') so none overlap any path or shape (top_synthesis 'a' currently 0px from path).
- [ ] 3-E.5 Render + regen judgment report.
- [ ] 3-E.6 Verify goal (f): `grep -E "is 0\.0px from" experiments/python_svg_semantic_fig1/fig1_visual_judgment_report.md` returns no matches.
- [ ] 3-E.7 Verify goal (g): density columns within bands.
- [ ] 3-E.8 Verify goal (e): in style.py, `hero_title_size > support_title_size`. Spot-check: search rendered SVG for the hero title text and confirm its `font-size` attribute is the largest in the document.
- [ ] 3-E.9 Run gate suite + tests.
- [ ] 3-E.10 Commit: `SEMANTIC.fig1: phase 3-E — hierarchy + text-conflict polish`.

Exit criteria for 3-E:
- All eight goals (a)-(h) checked at top of this file.
- 8/8 gates, zero test failures.
- Five Phase-3 commits on `experiment/python-svg-semantic-fig1`.

## 7. Audit Notes (filled by Ralph as it executes)

### 3-C.7 — density readings + ispd resize attempt (2026-05-08)

After 3-C wiring, density readings:
- `vs_decay_module`: 0.024 → **0.253** ✓ goal ≥ 0.20 met (panel was orphan, now hosts a real plot)
- `ispd_module`: 0.090 → 0.148 ✗ goal ≥ 0.20 not met (matplotlib fragment is wired but plot-box still small)
- `localized_traps`: 0.749 → 0.764 ✗ goal ≤ 0.70 slightly over (DOS lobes now visible adds area)

Attempted to enlarge `ispd_plot` local box from `[195, 100, 130, 280]` to `[50, 80, 420, 320]` then `[120, 70, 280, 340]`. Both broke the `_deep_dos_lobe_has_tails` semantic check — the hidden schematic helper renders Gaussians whose tail aspect-ratio depends on the bounding box, and a wider box pushes the deep-lobe top-band beyond the 62%-of-peak threshold.

Decision: roll back to `[195, 100, 130, 280]`. Density rebalance for goals (g) ispd ≥ 0.20 and localized_traps ≤ 0.70 is **deferred to Phase 3-E**, where typography and label re-anchoring is allowed to expand visible content without touching the hidden schematic geometry.

### 3-B.3 — chain-S row deferral (2026-05-07)

The chain-S row at `_draw_sulfur_polymer_origin:847-885` and the four mini polymer chains in the composition ramp at `_draw_sulfur_polymer_origin:887-948` remain hand-drawn after 3-B. Reasons:

- They render an open polymer chain `(-S-)ₓ`, not the closed S8 ring; RDKit would render them as straight `S-S-S-...` paths without the staggered y-offset visual cue used here, losing the schematic shorthand.
- The composition ramp varies atom counts per S60/S70/S80/S85 cell (4/6/8/10 atoms); a future RDKit polymer-chain primitive that accepts variable repeat-units would be the right wiring point.
- Deferred until a `polymer_chain_fragment(repeat_units, ...)` exists in `engine/rdkit_subrenderers.py`. Tracked as a future phase, not Phase 3.

### 3-B.1 — S8 ring code locations (2026-05-07)

`_draw_sulfur_polymer_origin` (lines 764-1007 in render_fig1_l1.py) contains three sulfur drawings:

- **lines 779-823** — S8 ring (target for 3-B.2): `column.box("s8_ring")` → bounds `[40, 80, 110, 124]`, computes `ring_center` + `ring_radius=min(w,h)*0.41`, draws 8 `draw.Line` segments + 8 `draw.Circle` atoms (radius 4.5), then a "S8" text label at `ring_center + (0, 82)`.
- **lines 847-885** — chain-S row (preserved per 3-B.3): `column.box("sulfur_chain")` with 7 atoms, hand-drawn polymer chain, not a ring.
- **lines 887-948** — composition ramp (preserved): four library entries S60/S70/S80/S85 with mini polymer chains, also not a ring.

Plan: replace only lines 779-823 (ring + "S8" label) with `s8_ring_fragment(width=ring_box.width, height=ring_box.height)` wrapped via `wrapped_fragment_svg` and `draw.Raw`. The "S8" text caption is preserved as a separate `p.text` call below the fragment. Chain row + composition ramp untouched.

### 3-A.1 — pe_hysteresis full-tree grep (2026-05-07)

Grep target: `pe_hysteresis|PEHysteresisPlot|pe_hysteresis_fragment` under `experiments/python_svg_semantic_fig1/src` and `plugins/figure-agent-py`.

Three categories of hits surfaced:

1. **Fig1 dead code (must remove in 3-A)**
   - `engine/matplotlib_subrenderers.py:14,107,152` — direct definitions, fully removable.
   - `render_fig1_l1.py:28,37,102,1752,1755,1769` — import + dispatch entry + function body for a SemanticObject the scene no longer emits.
   - `preview_fig1_electrical_style_adapter.py:9,10,19,20,62,65,67,70,72,74` — preview file consumes pe path.
   - `preview_fig1_library_subrenderers.py:9,10,25,48,55` — same.
   - `test_fig1_library_subrenderers.py:6,11,13,23,58,60,70,71,78,80,90,123,125,136,137` — four pe-specific test methods.
   - `test_fig1_electrical_style_adapter_integration.py:32` — entire file is pe-only.
   - `test_fig1_physics_sanity.py:73,75,79,80` — single test method `test_rejects_invalid_pe_hysteresis_parameters`.
   - `test_fig1_svg_fragments.py:56,58,59` — STRING LITERALS only, not real dependency. Update tokens, do not remove the test.

2. **Fig probe 02 live consumers (out of Phase 3 scope, must preserve)**
   - `fig_probe_02_scene.py:14,159,167,170` — Scene actively constructs `PEHysteresisPlot` payloads.
   - `render_fig_probe_02.py:17,25,53,199,201` — separate Fig probe 02 renderer dispatch.
   - `verify_fig_probe_02_contracts.py:64` — contract test references the kind name.
   - `engine/scientific_plots.py:119` — `pe_hysteresis_plan` is the legacy non-fragment plot grammar used by Fig probe 02.
   - `engine/scientific_geometry.py:31` — `pe_hysteresis_points` geometry helper used by the plan above.

   **Implication**: the Phase 3-A plan was wrong to schedule a delete of `PEHysteresisPlot` from `engine/domain_primitives.py`. That class is load-bearing for Fig probe 02. Section 2 of this plan has been amended to mark that file `NO EDIT`.

3. **Plugin wrapper**
   - `plugins/figure-agent-py/scripts/pyfig.py` — no pe references, but missing `"rdkit"` in `RENDER_DEPS`. Tracked under 3-A.6.

Decision: Fig1 surface and Fig1-only test files are cleansed in this phase; Fig probe 02 chain (separate renderer) is untouched and continues to depend on `PEHysteresisPlot`. The `forbidden_framing` constraint in `visual_layout.yaml` is Fig1-scoped and not violated by leaving Fig probe 02 alone.

## 8. Status Summary

Phase 3-A: complete (commit `a5ab492`, 12 files, 8/8 gates, 52 tests pass, hash unchanged at `6d0a37ba…`)
Phase 3-B: complete (commit `ea1695d`, 7 files, 8/8 gates, 52 tests pass, hash `03e51b77…`, RDKit S8 ring rendered in top_synthesis)
Phase 3-C: in progress
Phase 3-D: blocked on 3-C
Phase 3-E: blocked on 3-D
