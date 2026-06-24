I now have decisive evidence. Three load-bearing facts confirmed against source:

1. The existing executor supports exactly THREE action types (`translate`, `set_stroke_width`, opacity attrs). No path-`d` rewrite primitive exists. The entire B (organic-curve) library proposes writing new path data, which the existing apply-layer cannot express.

2. `svg_semantic_diff._inventory` tracks `path_count` and `marker_count` as integers only — it compares path geometry by COUNT, not shape. This is the seam the design over-trusts AND under-uses.

3. `tikz_patch`/`continue_tikz` are NOT dead — they're live members of `AESTHETIC_GATE_ROUTES`/`SVG_DELTA_ROUTES` and related sets. The design's "dead enum members" claim is factually wrong.

These are enough for a brutal, evidence-grounded refutation across A/B/D.

---

**Adversarial review — The Illustrator's Hand (piece #3). Verdict: does not yet achieve A/B/D; three load-bearing claims are false against the actual code.**

**B (organic form) — the architecture has no hands.** The entire B library (`smooth`, `roughen`, `jitter`, `taper`, `simplify`) rewrites path `d` data. But the existing apply-layer it claims to "widen," `svg_polish_executor.apply_action`, supports exactly three action types: `translate` (transform attr), `set_stroke_width`, and opacity attrs (lines 119-171). There is no `d`-rewrite primitive and no plan-time geometry validator for one. "Widens the existing contract" is doing enormous unearned work — every B op is a brand-new write path, brand-new bounds, brand-new diff invariant. That is the bulk of the build, hand-waved as a contract extension. **Fix: declare B as a new `path_rewrite` action class with its own validator; do not pretend it's an extension.**

**Accuracy lock is geometry-blind exactly where B needs it.** `_inventory` records `path_count`/`marker_count` as integers (lines 187-188, 210-219); `_compare` only flags count changes. So a `roughen`/`taper` that keeps the path count but turns a clean curve into garbage passes the diff untouched — the lock cannot see shape corruption, only inventory deltas and the 10px translate / [0.5,2.0] stroke bounds (which don't apply to `d` edits at all). The claim "structural-layer ops must leave the inventory byte-invariant" is true and useless: byte-invariant inventory permits arbitrary geometry destruction. **Open risk: B operating on the structural layer has NO geometric guard; the proposed `relationship_guard` checks bbox relations, not curve fidelity (a Hausdorff/Fréchet bound is missing).**

**Factual error undermining the reuse premise.** The design asserts `tikz_patch`/`continue_tikz` are "dead enum members." They are live in `critique_schema_vocab.py` (`AESTHETIC_GATE_ROUTES` L278, `SVG_DELTA_ROUTES` L213, plus L137/252/303/313). Routing taste verdicts as if those routes don't exist will silently drop or mis-handle real critique outputs. **Fix: either retire them in code first, or handle them — don't design around a false premise.**

**A (aesthetic finish) — the one real differentiator is human-gated into irrelevance.** Soft shadows / blur are the single most recognizable "finished" cue, and they're the ONLY filter op, human-gated, and rasterize on PDF export (the actual delivery format). So in the real output path, A reduces to flat gradient fills + filter-free fake-bevel geometry — which is precisely the "dead_flat_vector_finish" antipattern the loop is supposed to cure. **Open risk: A's headline capability is unavailable in the export target; default output stays flat.**

**D (compositional eye) is the only genuinely sound piece** — `measure→CompositionReport` + kiwisolver `snap_to_grid` is real and the determinism split is coherent. But D moves whole elements via `translate`, capped at `MAX_TRANSLATE_PX=10`. Composition fixes (re-balancing a panel, opening whitespace) routinely need >10px. **Fix: D needs its own larger structural-translate budget under `relationship_guard`, or it can only nudge, never compose.**

Net: D ships, A is export-crippled, B is unbuilt and unguarded. Constants verified; reuse map is wrong on the dead-enum claim.

=== SKEPTIC ===

I have all the evidence I need. The design's own "verified" claims are partly false against the real code, and the lens-specific flaw (determinism/taste bleed) is concrete. Writing the ~450-word adversarial critique.

---

## Adversarial review — deterministic-core vs taste-layer separation

The separation does not hold. It bleeds in both directions, and the design's own grounding claims are contradicted by the actual code.

**Flaw 1 — "deterministic" geometry ops secretly encode taste in their parameter defaults, and the contract has nowhere to put that taste.** Take `hand.simplify(sel, epsilon, algo=rdp|vw)` and `hand.smooth(sel, method, iters)`, both filed as deterministic. They are reproducible *given* `epsilon`/`iters` — but the *choice* of `epsilon` is precisely "how much truth do I erase to look cleaner," which is a taste judgment with scientific stakes (over-simplifying a schematic deletes structure). The design's escape hatch is "a taste op proposes params, a deterministic op executes." But there is no taste op in the library that proposes `epsilon` for `simplify` — `decide_organic_curvature`/`tune_corner_softness` cover roughen/fillet, not RDP tolerance. So `simplify`'s most consequential parameter is taste with no proposing op, executed under a "deterministic, no critique needed" label. Same for `resample(density)` and `taper(width_profile)`. The boundary is drawn at *seeded* vs *unseeded*, but the real fault line is *parametrized-with-a-correct-answer* vs *parametrized-with-a-judgment-call*, and those cross-cut.

**Flaw 2 — a "taste" op is fully mechanizable: `enforce_min_print_size` and `snap_to_grid` routing.** `print_scale_unreadable→enforce_min_print_size` is listed mechanical (correct), but `balance_annotation_density` is taste — yet its trigger `annotation_noise_competes_with_science` plus the PFLP solver (`place_labels`, declared deterministic) means the decision "is it too dense" reduces to a measurable occupancy ratio against `measure()`'s density metric. It is a threshold, not an eye. It's mislabeled taste to justify a human gate it doesn't need.

**Flaw 3 — the grounding is wrong, which collapses the "deterministic core executes+logs" story.** The design asserts the Hand's geometric ops widen the existing `action{type}` contract. The real `ACTION_TYPES` frozenset (`svg_polish_recipe.py:18`) is exactly five **scalar setters**: `translate, set_stroke_width, set_opacity, set_fill_opacity, set_stroke_opacity`. None of `smooth/simplify/taper/roughen/jitter/route_leader` exist as actions. The "deterministic core" the design hands off to *cannot execute or log a single geometric op* — every B-group op requires inventing new action types and new diff invariants. Also `element_inventory_change` is severity **MINOR** (`svg_semantic_diff.py:365`), not the MAJOR the accuracy-lock narrative implies, so the `hand:*` allowlist is load-bearing in a way the design understates.

**Fix / risk to record:** Replace the deterministic/taste binary with a three-axis declaration: `reproducible(seed) × judgment-bearing(params) × truth-affecting(structural-layer)`. An op can be reproducible yet judgment-bearing yet truth-affecting (`simplify`) — that combination is exactly what needs a critique gate, and the current two-way split hides it. **Open risk:** every B/D geometric op is unimplementable until `ACTION_TYPES` and the diff's transform/inventory invariants are extended; treat the "deterministic core already executes+logs" claim as false until those land.

=== SKEPTIC ===

I have enough evidence. The findings are confirmed against the actual code. Here is my adversarial review.

---

**VERDICT: The accuracy lock does NOT hold under the Hand's own ops. It is geometry-blind, and the most important class of "beautify" ops it is supposed to police rewrite exactly the geometry it never reads.**

Evidence is from the real code at `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/scripts/svg_semantic_diff.py` and `svg_polish_executor.py`.

**Flaw 1 — The lock never reads path geometry (`d`). This is the central break.**
`_inventory()` (lines 172-255) collects text, ids, classes, frame, transforms, colors-by-id, and *counts* of paths/markers. It never parses the `d` attribute, and `svgpathtools`/`parse_path` appear zero times in the file. So every B-group op — `smooth`, `roughen`, `jitter`, `simplify(epsilon)`, `taper`, `soften_corners`, `open_loop` — rewrites control points in place and the diff sees a byte-identical inventory: same path_count, same id, same fill. It returns `pass`.

Concrete schematic + op where this is scientifically WRONG: a phase-boundary line on a binary phase diagram (or a band-bending diagram in a semiconductor junction). `hand.smooth(method=catmull_rom)` rounds a eutectic cusp into a smooth minimum; `hand.simplify(epsilon=2)` on a step-function (e.g. a quantized energy level, a square-wave drive signal, a sharp absorption edge) deletes vertices and turns a discontinuity into a ramp. The line count is unchanged, the label "T_eutectic" is untouched, the `id` survives — `svg_semantic_diff` passes it clean. The schematic now asserts a physical falsehood (a smooth invariant point that does not exist, a first-order transition redrawn as second-order). The lock catches nothing.

This is not an edge case; it is the design's flagship value prop ("organic/freeform curves -> B") landing precisely in the lock's blind spot. The `marker_or_path_change` finding (lines 344-358) is **count-only and MINOR** — it fires if you add/remove a path, never if you reshape one.

**Flaw 2 — `relationship_guard` and `bbox_inventory_native` do not exist and are load-bearing.** Grep returns zero hits in the scripts dir. The design leans on them to reject a `snap_to_grid` that reverses A-left-of-B *before* the diff — but they are vaporware in this writeup. Worse, even the proposed relationship guard only checks *declared* relations. The eutectic-cusp falsehood above is not a spatial relation between two named nodes; it is intra-path curvature. No bbox/relation guard catches it either. The guard family is scoped to inter-element topology and is blind to within-element shape semantics — the same blind spot, one layer up.

**Flaw 3 — color/shade ops escape the only color check.** `OPTICAL_ATTRS` compare (line 189, 371-388) is an exact-string match on `fill`/`stroke`. `derive_shade`, `apply_role_gradient`, `add_volume_shading` set `fill="url(#grad)"`; the diff stores the literal string and never resolves the gradient stops. A `crameri_map` gradient that re-orders perceptual lightness (making a "low" region read as "high" on a sequential-encoded field) passes `semantic_color_remap`, because the string changed in a *whitelisted* `hand:*` def and the on-canvas id's fill string may be unchanged. The structural-layer `verify_*` gates are asserted in prose but absent from the diff path.

**Proposed fix (record as required, not optional):**
1. Add a geometry invariant to `svg_semantic_diff`: for every structural-layer path, parse `d` with `svgpathtools` and assert a **monotonicity/curvature-sign/vertex-count-and-corner signature** is preserved (Fréchet/Hausdorff distance bound + sign-of-curvature run-length). Structural B-ops must be BLOCKED outright, not bounds-checked — there is no safe "10px" for reshaping a phase boundary. The two-layer split only helps if B-ops are confined to `hand:*` overlay; but `smooth`/`simplify`/`taper` are explicitly listed as operating on the structural schematic line, which contradicts the lock.
2. Resolve `url()` fills to actual stops before the optical compare.

**Open risk if unfixed:** the lock's guarantee ("cannot be scientifically wrong") is false for the entire curve/shape op family and for gradient recolor. The two-layer model is sound *only* if structural-layer ops are restricted to the 3 currently-implemented actions (translate/opacity/stroke-width); every new geometry-mutating op the Hand adds to the structural layer is unguarded by construction. The design's self-assessment ("structurally confined") is contradicted by its own op list.

=== SKEPTIC ===

I now have decisive evidence. The inventory tracks `path_count` as a bare integer count — but crucially, the design's geometry ops (smooth, roughen, taper centerline→outline, double_stroke, simplify) all *rewrite path `d` data or change the number of paths*. `taper` and `double_stroke` and `roughen`-into-filled-outline literally change `path_count`, which fires `element_inventory_change` (MAJOR → whole-commit reject). This is a structural contradiction in the design's own "structural-layer ops must leave inventory byte-invariant" claim vs. what B-craft ops do.

I have more than enough verified evidence. Writing the refutation.

---

# Adversarial review — The Illustrator's Hand (figure-agent piece #3)

**Verdict: the design's load-bearing premise ("All constants and the contract shape are confirmed... Every op widens the existing recipe contract") is partly false, and the falsity is fatal to the plan-as-written.** Constants check out (`MAX_TRANSLATE_PX=10.0`, `0.5/2.0`, three selector kinds — `svg_polish_executor.py:20-23`, `svg_polish_recipe.py:17`). The contract does not.

**Flaw 1 — the contract you claim to "widen" doesn't have the fields you build on.** The real op (`svg_polish_recipe.py:135-157`) is `{id, class, selector, action, rationale, semantic_guard{allowed,reason}}`. There is **no `layer`, no `determinism`, no `driven_by`, no `action.params`, no `seed`.** Actions are flat (`dx/dy/unit` or `value`), and `ACTION_TYPES` is a frozen set of exactly **four** (`translate, set_stroke_width, set_opacity, set_stroke_opacity`/`set_fill_opacity` — `:18-26`), not "5 sanctioned actions." Your entire §2 deterministic/taste split is declared "in `determinism`" — a field that does not exist. *Fix:* state plainly that piece #3 requires a **new recipe schema (v2)**, not a widening; enumerate the added fields as net-new. Right now the design rests on a contract that would reject every Hand op.

**Flaw 2 — the edit-class whitelist hard-blocks the whole op library.** `ALLOWED_EDIT_CLASSES` (`svg_polish_manifest.py:39-50`) is a frozen 8-member set of *micro-corrections* (`label_micro_position`, `stroke_polish`, `typography_cleanup`…). `smooth`, `roughen`, `taper`, `add_volume_shading` map to **none** of them, so `_validate_operation` raises before any diff runs. The Hand needs a parallel op taxonomy, not a reuse.

**Flaw 3 — B-craft ops violate the accuracy lock you say protects them.** `_inventory` (`svg_semantic_diff.py:172-255`) counts `path_count` and fires `element_inventory_change=MAJOR` (whole-commit reject, all-or-nothing) on any change. But `taper` (centerline→filled outline), `double_stroke` (passes→extra paths), and `roughen`/`simplify` **change path count and rewrite `d`**. Your text even concedes structural-layer ops "must leave the inventory byte-invariant" — which these cannot. The `hand:*` overlay escape hatch doesn't save B: smoothing/tapering the *schematic's own strokes* is a structural-layer edit by definition. *Open risk to record:* either B ops are overlay-only (you redraw a stylized copy on top and hide the original — doubling inventory, breaking `text/marker` relationships) or the inventory invariant must become geometry-aware (per-path topological identity, not a count). Neither exists today.

**Flaw 4 — `relationship_guard`, `bbox_inventory_native`, `hand:*` allowlist, and `color-interpolation` gating are presented as "new" but are vaporware with no spec.** Grep confirms **zero** occurrences. The critique vocab you cite (`MICRO_DEFECT_KINDS`, `AESTHETIC_*`, `SVG_DELTA_ROUTES`) is real (`critique_schema_vocab.py`), so §3's routing is plausible — but §4's three core guards are asserted, not designed. The "Design complete... all paths verified" framing overstates readiness: the guards that make freedom safe are exactly the unbuilt parts.

**Is SVG-native the right substrate? Mostly yes — but steelman the recorder.** SVG-as-truth is correctly chosen over **raster+vectorize** (vectorization hallucinates topology — fatal for "cannot be scientifically wrong") and **AI image-gen** (same). Over **TikZ**: SVG genuinely wins on organic B (native Bézier/gradients) and version-control. **3D** is overkill for 2D schematics. The real contender is **"a real illustrator with a recorder"** (capture an expert's Illustrator/Inkscape edit ops as a replayable, parameterized macro library). Steelman: it sidesteps the hardest unsolved problem here — *taste*. Your §2 punts taste to "a critique signal" but never says where competent taste comes from; a recorded human-derived op library encodes real craft priors instead of hoping the vision-critique loop converges. It would also yield the exact param ranges (corner radius, jitter correlation) you currently hand-pick. **SVG-native is right for the *substrate*; the recorder is the better *source of the op parameters*.** Open risk: with no taste oracle, the loop may oscillate (`childish_shape_language` ↔ `dead_flat_vector_finish`) with no fixed point.

**Single biggest weakness:** the design claims reuse of a contract and guard set that, as verified in-tree, **cannot represent or admit the ops it proposes** — and the accuracy lock that is its whole safety story actively rejects its own B-craft geometry. This is a from-scratch schema + geometry-aware diff, mislabeled as a "widening."