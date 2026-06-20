# THE ILLUSTRATOR'S HAND — Engine Design (figure-agent piece #3)

*Design only. Read-only. No build. Verified against in-tree source on 2026-06-21.*

## 1. Purpose and scope

The Hand is **how an agent manipulates SVG like an illustrator** — piece #3 of the six-piece figure-agent v2 architecture (semantic canvas → intent → **Hand** → asset library → vision-critique → accuracy lock). Northstar: an illustrator-grade, hand-touch **schematic** generator (concept / apparatus / mechanism illustrations, e.g. an SC-7-style 4-panel), **not** data plots — those stay in Graph Hub.

It closes three gaps and excludes one:

- **A — aesthetic finish** (depth, line-weight rhythm, color craft).
- **B — organic / freeform curves** (Bézier authoring, controlled hand-jitter, tapered strokes).
- **D — compositional eye** (balance, hero hierarchy, whitespace, grid).
- **C — WYSIWYG-drag is EXCLUDED.** The goal is *output* quality, not an editing UI. C has zero footprint here, which costs nothing because nothing in the existing pipeline is an editor.

**Hard guard, repeated everywhere below:** aesthetic freedom is permitted **only on top of structural truth.** A schematic must never become scientifically wrong. As §6 shows with verified evidence, the existing accuracy lock does *not* yet enforce this for the very ops the Hand introduces — so the truth guarantee is a *thing this design must build*, not a thing it inherits.

## 2. What is reused from figure-agent (and what the brief got wrong)

Honest accounting against source — three "confirmed" reuse claims in the brief are false:

**Genuinely reusable:**
- **The whole vision-critique loop** (`critique_*.py`, `critique_schema_vocab.py`) — schema, signal vocabulary, host-session review. This *is* piece #5; the Hand consumes its routes verbatim. Solid.
- **`svg_semantic_diff.py` inventory+finding engine** — already pure-SVG. It is the *seed* of piece #6, but it is **geometry-blind** (see §6) and must be extended, not merely "gated through."
- **The op *contract shape* as inspiration** — `{id, class, selector, action, rationale, semantic_guard{allowed,reason}}`. Reuse the *spirit*; the fields the Hand needs do not exist yet (below).
- **Manifest provenance ledger** (`svg_polish_manifest.py`) → becomes the version-controlled decision log. Reproducibility = versioned SVG + seeded decision log, **not** pixel-lock. Reuse.

**Brief errors corrected (verified):**
1. **"Every op widens the existing recipe contract."** False. The real op (`svg_polish_recipe.py:135-157`) has **no** `layer`, `determinism`, `driven_by`, `action.params`, or `seed`. The Hand requires a **new recipe schema (v2)**, declared as net-new fields — not a widening.
2. **"5 sanctioned actions" the Hand extends.** `ACTION_TYPES` lists 5 (`:18-26`) but the executor dispatches **3 families** (`translate`, opacity-attrs, `set_stroke_width`; `svg_polish_executor.py:118-147`). There is **no path-`d` write primitive and no geometry validator.** Every B-craft op is a brand-new write path, not an extension.
3. **`tikz_patch`/`continue_tikz` are "dead enum members."** False — they are **live** in `AESTHETIC_GATE_ROUTES` and `SVG_DELTA_ROUTES` (`critique_schema_vocab.py:137, 252, 278, 303, 313`). The Hand must either retire them in code first or handle them; it may **not** design around their absence.
4. **`ALLOWED_EDIT_CLASSES`** (`svg_polish_manifest.py:39-50`) is a frozen 8-member *micro-correction* set. `smooth`/`roughen`/`taper`/`add_volume_shading` map to none, so `_validate_operation` rejects them before any diff runs. The Hand needs a **parallel op taxonomy**, not a reuse of the 8 classes.

**Dead (TikZ-era):** the `.sty` style lock (→ SVG token table in piece #4), `check_collisions.py`/`check_undeclared_geometry.py` operating on `pdftotext` bboxes (logic reuses, PDF/TikZ I/O dies), and the whole `lualatex`/PDF chain.

## 3. Operation library

Build on `svgpathtools` + `lxml` + `ColorAide` (OKLCH) + `kiwisolver` + `fonttools` + `rough-py`. Avoid unmaintained `svgwrite`. Every op declares `action_class ∈ {transform, path_rewrite, paint, defs_add, text_layout, overlay}` — the **`path_rewrite` class is net-new** and carries its own plan-time validator (§6).

**B — curves & organic form** (`path_rewrite`): `smooth(sel, method=chaikin|catmull_rom, iters)`, `soften_corners(sel, radius, min_angle)`, `simplify(sel, epsilon, algo=rdp|vw)`, `resample(sel, density)`, `roughen(sel, roughness, bowing, seed)`, `jitter(sel, magnitude, correlation, source=fir|perlin, seed)` (normal-direction, FIR/Perlin-smoothed — isotropic per-point noise is the amateur "corrupted-file" failure), `double_stroke(sel, passes, jitter, seed)`, `taper(sel, width_profile)` (centerline→filled outline; SVG has no native variable stroke width), `open_loop(sel, gap_fraction)`.

**A — depth/shading** (`paint`/`defs_add`): `set_document_light(vector, key, ambient)` (one locked rig), `add_volume_shading(sel, form=sphere|cylinder|plane, light=@doc)` (Lambert 5-stop gradient, fill-only), `add_contact_shadow`, `add_long_shadow(angle, length)`, `add_bevel(depth)` (all filter-FREE decor geometry), `cel_quantize(bands)`, and the **only** filter op `add_soft_shadow_filter(...)` (human-gated; see §7 risk — it rasterizes on PDF export).

**A — color** (`paint`): `resolve_token(role)→hex` (frozen SVG token table porting the Paul Tol Muted bindings from the dead `.sty`), `derive_shade(hex, ΔL,ΔC,ΔH)` (OKLCH), `set_fill/set_stroke`, `apply_role_gradient(crameri_map)`, `generate_harmony(anchor, scheme)`, gates `verify_cvd/verify_grayscale/verify_contrast`.

**Labels/typography** (`text_layout`): `measure_text` (fonttools, no render), `place_labels(anchors, specs, obstacles, strategy=greedy|annealing, seed)` (PFLP), `route_leader(kind=s|po|opo)` (boundary labeling), `align_labels`, `render_math(latex)` (MathJax→paths), `format_units`, `enforce_min_print_size(min_pt=5)`, `add_text_halo`.

**D — composition** (`transform`/`overlay`): `measure(svg)→CompositionReport` (Ngo balance/equilibrium/density + saliency + grid candidates, read-only), `snap_to_grid(sel, grid, max_delta)` (kiwisolver), `equalize_gutters`, `set_emphasis(hero, strength)`, `deemphasize`, `reorder_paint`, `draw_overlay(layer=hand:*, ops=[halo|vignette|background_field|group_bracket|common_region|counterweight])`.

## 4. Deterministic core vs taste layer (defended against the separation skeptic)

The skeptic is right that a 2-way `deterministic|taste` split bleeds. `simplify(epsilon)` is reproducible *given* `epsilon`, yet the *choice* of `epsilon` is "how much truth do I erase to look cleaner" — a judgment with scientific stakes, and no taste op proposes it. The split must be **three independent axes**, declared per op:

- **`reproducible(seed)`** — same recipe+seed → same bytes. Seeded ops (`roughen`, `jitter`, `place_labels` annealing) qualify; the seed is frozen in the decision log.
- **`judgment_bearing(params)`** — does a parameter have a *correct answer* (e.g. `min_print_size`, grid pitch) or a *taste answer* (`epsilon`, roughness, light direction, hero strength)? Judgment-bearing params **must** be proposed by a critique signal, never defaulted silently.
- **`truth_affecting(layer)`** — does the op mutate a structural-layer node (the schematic's own geometry) or only a `hand:*` overlay?

The combination that the old binary *hid* — **reproducible × judgment-bearing × truth-affecting** (exactly `simplify`/`smooth`/`taper` on a real schematic stroke) — is precisely the cell that **requires a critique gate AND a geometry guard**. A taste op only *proposes* `{params, seed}`; a deterministic executor then applies and logs. So the eye can be wrong about taste without ever producing unreproducible or unverifiable geometry — but only if the third axis routes truth-affecting ops to §6's guard.

## 5. Critique-to-edit drive (reuses figure-agent vocabulary)

Piece #5 runs in the host Claude session and emits the existing signals; each routes to an op — **no new enum invented, and the live `tikz_patch`/`continue_tikz` routes are handled, not ignored** (mapped to `svg_polish` or `needs_human_art_direction` by a thin shim until retired in code).

- **Mechanical routes** (`MICRO_DEFECT_KIND` → op): `line_crosses_label`/`wire_crosses_label`→`route_leader`; `label_target_detached`/`floating_semantic_cue`→`route_leader` reconnect; `label_path_near_miss`→bounded `place_labels` nudge; `print_scale_unreadable`→`enforce_min_print_size`; new `edge_misalignment_off_grid`→`snap_to_grid`.
- **Taste routes** (`AESTHETIC_ANTIPATTERN_ID`/`LEVER_DIMENSION` → taste op): `weak_hero_anchor`+`visual_hierarchy`→`designate_hero`/`set_emphasis`; `dead_flat_vector_finish`+`uniform_line_weight_monotony`+`handcrafted_finish`→`add_volume_shading`/`taper`/`derive_shade`; `childish_shape_language`→**reduce** roughness/revert (the "too sketchy" brake); `cramped_or_dead_whitespace`→`shape_whitespace`/`equalize_gutters`; `annotation_noise_competes_with_science`→`balance_annotation_density`; `overdecorated_or_cartoonish`+`maturity_restraint`→`decide_decoration_restraint` (often REJECT).

After write, `rasterize_preview`→re-critique closes the loop via `SVG_DELTA_EVALUATION_STATES {improved|no_meaningful_change|regressed|needs_human_art_direction}`; a `regressed→overdecorated/label_readability` verdict reverts the edit or lowers the sketchiness scalar. **Open loop-stability risk:** with no taste oracle, the pair `childish_shape_language ↔ dead_flat_vector_finish` can oscillate; the design caps iterations and requires monotone-improvement on the chosen axis or it routes to `needs_human_art_direction`.

## 6. Accuracy lock / immutable guard (skeptic 3's break case is real)

**Confirmed break case.** `_inventory` (`svg_semantic_diff.py:183-205, 247-248`) records `path_count`/`marker_count` as bare integers and **never parses `d`.** `_compare` flags count deltas only (`:345-346`), and `element_inventory_change`/`marker_or_path_change` are **MINOR** (`:366, :351`), not MAJOR. Therefore:

> `hand.smooth(method=catmull_rom)` rounds a eutectic cusp on a phase diagram into a smooth minimum; `hand.simplify(epsilon=2)` deletes vertices on a step-function (quantized energy level, sharp absorption edge), turning a first-order discontinuity into a ramp. Path count unchanged, `id` and label `"T_eutectic"` untouched → **`svg_semantic_diff` returns `pass`.** The schematic now asserts a physical falsehood and the lock catches nothing.

This is the design's flagship value prop (organic curves → B) landing in the lock's blind spot. "Inventory byte-invariant" is **true and useless** — byte-invariant inventory permits arbitrary geometry destruction. The two-layer model is sound *only if* structural-layer ops are restricted to the 3 implemented actions; every geometry-mutating op is unguarded by construction.

**Required mitigation (not optional):**
1. **Structural-layer `path_rewrite` is BLOCKED outright**, not bounds-checked. There is no safe "10px" for reshaping a phase boundary. B-craft ops may run **only** in `hand:*` overlay, where they restyle a copy that sits above truth.
2. **Add a geometry invariant to the diff:** for every structural path, parse `d` with `svgpathtools` and assert a topological signature survives — vertex/corner count, **sign-of-curvature run-length**, and a **Fréchet/Hausdorff distance bound**. This is the guard the proposed `relationship_guard` does *not* provide (it checks inter-element bbox topology; the cusp falsehood is intra-path curvature).
3. **Resolve `url(#grad)` fills to actual stops before the optical compare.** `OPTICAL_ATTRS` is an exact-string match (`:189`); a `crameri_map` gradient that re-orders perceptual lightness passes `semantic_color_remap` today. Color edits additionally pass `verify_cvd/grayscale/contrast`.
4. **Two new guards must be specified, not asserted** (both are currently vaporware — zero hits in tree): `relationship_guard` (declared spatial relations: A-left-of-B, A-inside-B, A-connected-by-leader, from a native `bbox_inventory_native` replacing the dead `pdftotext` path) and an **occlusion/detachment guard** for overlays (reusing `label_backdrop_overflows_outline`/`label_target_detached`/`floating_semantic_cue` against *locked* bboxes).
5. **`hand:*` allowlist** whitelists decor `defs`/groups so added gradients don't trip `unsupported_svg_feature`/`element_inventory_change`. `commit()` stays all-or-nothing: any BLOCKER/MAJOR rejects the whole write.

With these, beautifying is structurally confined: the critique can misjudge taste, but cannot make the schematic scientifically wrong. **Without them, the lock's "cannot be wrong" guarantee is false** — record as the single highest-priority open risk.

## 7. Honest A/B/D achievability verdict (skeptic 1)

- **D ships.** `measure→CompositionReport` + kiwisolver `snap_to_grid` + the 3-axis determinism split are sound and grounded in real signals. **Caveat:** D moves elements via `translate` capped at `MAX_TRANSLATE_PX=10`; real composition fixes routinely exceed 10px. D needs its **own larger structural-translate budget gated by `relationship_guard`**, or it can only nudge, never compose.
- **B is unbuilt and unguarded** as-designed. It requires the net-new `path_rewrite` action class, a plan-time geometry validator, and the §6 curvature invariant. It is the bulk of the build, not a contract extension. Honest status: **largest single work item; do not ship as "reuse."**
- **A is export-crippled by default.** Soft shadow / blur is the single most recognizable "finished" cue, yet it is the **only** filter op, human-gated, and **rasterizes at ~200 DPI on PDF export** (the delivery format) with `color-interpolation-filters` divergence across renderers. In the real output path A reduces to flat gradient fills + filter-free fake-bevel geometry — precisely the `dead_flat_vector_finish` antipattern the loop is meant to cure. **Mitigation:** make filter-free volume shading (Lambert gradients, cel bands, long-shadow geometry) the *default* A path and treat blur as an opt-in screen-only enhancement; accept that print-A is gradient-and-geometry, not blur.

## 8. Substrate decision vs alternatives

SVG-native (SVG-as-truth) is the **right substrate**: it beats raster+vectorize and AI image-gen (both hallucinate topology — fatal for "cannot be scientifically wrong"), beats TikZ on organic B (native Bézier/gradients) and version control, and 3D is overkill for 2D schematics. **Steelmanned contender — "a real illustrator with a recorder":** capture an expert's Inkscape/Illustrator edit ops as a replayable, parameterized macro library. It sidesteps the unsolved problem this design punts — *where competent taste comes from* — and would yield the exact param ranges (corner radius, jitter correlation, `epsilon`) currently hand-picked. **Resolution:** SVG-native is correct for the *substrate*; a recorded human-op corpus is the better *source of taste-op parameter priors*. Adopt SVG-native now; treat a recorded-op param corpus as the eventual taste oracle that breaks the §5 oscillation.

## 9. Open risks (must be tracked, not buried)

1. **Accuracy lock is geometry-blind** — top priority; §6 mitigation is a hard precondition for any B op touching truth.
2. **`path_rewrite` action class, v2 recipe schema, and parallel op taxonomy do not exist** — this is a from-scratch schema + geometry-aware diff, mislabeled in the brief as a "widening."
3. **A's blur is unavailable in the export target** — default print output stays flat unless filter-free shading is the default.
4. **D's 10px translate ceiling** prevents real composition without a new budget.
5. **`tikz_patch`/`continue_tikz` are live** — must be retired-in-code or shimmed; cannot be ignored.
6. **Loop oscillation** with no taste oracle (`childish ↔ dead_flat`).
7. **Vaporware guards** (`relationship_guard`, `bbox_inventory_native`, `hand:*` allowlist, `color-interpolation` gating) are load-bearing and unspecified — zero in-tree presence.

## 10. Smallest first buildable slice (still design; names the first piece)

**Slice 0 — the geometry-aware accuracy lock, overlay-only.** Before any drawing op, build:
1. A `path_geometry_inventory()` extension to `svg_semantic_diff.py` that parses `d` with `svgpathtools` and computes the per-path topological signature (vertex/corner count, curvature-sign run-length, Fréchet bound).
2. The `hand:*` overlay namespace + allowlist in the diff, so overlay `defs`/groups don't trip inventory findings.
3. One end-to-end op proving the contract: **`add_volume_shading` (overlay, filter-free, deterministic, paint/defs_add)** — it never touches a structural path, exercises the v2 recipe fields (`layer=hand:*`, `action_class=defs_add`, `determinism` axes), the `hand:*` allowlist, the occlusion guard, and the color gates — and delivers a visible A-gap win with **zero** structural risk.

This slice proves the two-layer safety model and the v2 schema before a single `path_rewrite` op (the risky B work) is written. It is the correct wedge: lock first, draw second.

---

**Return-value notes for the caller:** This is design-only; no files created or modified. All four adversarial findings are **confirmed against source** at `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/scripts/` — the brief's "verified" claims were wrong on (a) "5 actions extended" (executor dispatches 3; `svg_polish_executor.py:118-147`), (b) "widens the contract" (recipe op lacks `layer`/`determinism`/`seed`; `svg_polish_recipe.py:135-157`), (c) "dead enum" (`tikz_patch`/`continue_tikz` live; `critique_schema_vocab.py:137,252,278,303,313`), and (d) inventory geometry-blindness (`path_count` integer-only, `d` never parsed; `svg_semantic_diff.py:183-205,247-248`; `element_inventory_change` is MINOR at `:366`). The document folds all of this in honestly: D ships, A is export-crippled, B is unbuilt-and-unguarded, and the accuracy lock must become geometry-aware (Slice 0) before any structural curve op.
