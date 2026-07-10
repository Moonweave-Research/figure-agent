# figure-agent v2 — SVG Illustrator (hand-craft schematics)

**Status:** Historical evidence — non-authoritative.
**Superseded by:** `docs/product-spec.md` and `docs/execution-plan.md`.

*Design spec. Brainstorm output, 2026-06-21. Builds on and pivots away from the v0.10 TikZ/convention-context-spine line. Design only — no build. Piece #3 detail lives in `ILLUSTRATORS_HAND_design.md` (verified against source); the deep-dive evidence is in `.hand-deepdive-2026-06-21/`.*

## 1. Problem and north star

Produce **publication schematics** — concept / apparatus / mechanism illustrations (e.g. an SC-7-style 4-panel: Polymer / Trap / Force / Actuation) — with **illustrator-grade, hand-touch craft**. NOT data plots; those are owned by Graph Hub and are considered done.

The craft gap, from the user, is three capabilities plus one explicit exclusion:

- **A — aesthetic finish**: depth/shading, line-weight rhythm, color craft, "looks designed, not code-generated."
- **B — organic / freeform curves**: elegant Béziers, controlled hand-jitter, tapered strokes — the things TikZ fights.
- **D — compositional eye**: balance, hero hierarchy, whitespace, grid.
- **C — WYSIWYG drag editing is EXCLUDED.** The goal is *output* quality, not an editing UI. The user wants the agent to be the hand, not to drag boxes himself.

## 2. Philosophy decision — ③ SVG-as-truth

Three candidate philosophies were weighed:

1. **Code-as-truth (evolve current).** Keep TikZ/code as source, upgrade the substrate + add aesthetic/composition critique. Rejected as the *primary* path: code is a precision-CAD medium, not an illustration medium; B (organic feel) is hard to reach deterministically from code.
2. **Intent-as-truth.** Source = a design-intent spec; pixels are generated (incl. AI-assisted). Rejected: AI generation hallucinates topology — fatal for "a schematic must never be scientifically wrong."
3. **SVG-as-truth (CHOSEN).** Source = a *semantic SVG* (named layers/paths, Béziers). The agent manipulates it like an illustrator; the human directs. SVG is the natural illustration medium (native Bézier / gradients / organic form → A + B), it is exact (no hallucinated structure), and it is version-controllable.

**Reproducibility is redefined**: not pixel-lock, but **versioned SVG + a seeded decision log** (what aesthetic/composition choice was made, and why). Same recipe + seed → same bytes; the *judgment* is recorded, not frozen.

**Hard guard, everywhere:** aesthetic freedom is permitted *only on top of structural truth.* A schematic must never become scientifically wrong. (§5 shows the current lock does not yet enforce this for the ops v2 introduces — so the truth guarantee is a thing this design must **build**, not inherit.)

## 3. Architecture — six components

Pipeline: **semantic canvas → intent → Hand → asset library → vision-critique → accuracy lock.**

| # | Component | Status |
|---|-----------|--------|
| 1 | **Semantic SVG canvas** — the source of truth; layers/paths carry meaning (`id=polymer-chain`, `contact-interface`) so human and agent address parts by meaning, **plus a per-path `truth_bearing` flag** (truth vs decoration; gates what the Hand may reshape — §5). | new (model + conventions) |
| 2 | **Intent layer** — thin brief: what the figure shows + what to emphasize + visual language. | reuse figure-agent briefing/spec |
| 3 | **The Hand (illustrator engine)** — agent ops over the SVG: curves/organic form (B), depth/shading (A), color, labels/typography, composition (D). | **the hard core; see `ILLUSTRATORS_HAND_design.md`** |
| 4 | **Asset library** — reusable hand-crafted components (bioicons-style) + SVG token table (ports the Paul Tol palette from the dead `.sty`). | new + reuse style intent |
| 5 | **Vision-critique loop** — render → host-session reads PNG → critique (aesthetic + composition + correctness) → edit → re-render. | **reuse verbatim** (`critique_*.py`, `critique_schema_vocab.py`) |
| 6 | **Accuracy lock** — structural-truth invariant; verified after every edit. | **rebuild — current `svg_semantic_diff` is geometry-blind (§5)** |

Human role: provide intent → spot-direction in natural language ("emphasize the chain", "this curve too sharp") → final confirm. No WYSIWYG UI.

## 4. Execution model

Intent → agent drafts initial SVG (asset components + generated paths) → vision-critique loop (taste + composition + correctness signals route to Hand ops) → human spot-direction → converge → export (PDF/TIFF/PNG for journals). The host Claude session is the eye; the Hand ops are the deterministic executors that a critique signal drives. Determinism is declared per op on **three axes** (not the old binary): `reproducible(seed)` × `judgment_bearing(params)` × `truth_affecting(layer)` — see hand design §4. Judgment-bearing params (e.g. `epsilon`, roughness, light direction, hero strength) must be *proposed by a critique signal*, never silently defaulted.

## 5. Safety and verification gates (the load-bearing risk)

**Verified finding (independently re-confirmed against source):** the current accuracy lock is **geometry-blind**. `svg_semantic_diff._inventory` records `path_count`/`marker_count` as integers and never parses `d`; `_compare` flags count deltas only, severity MINOR. So a `smooth`/`simplify`/`roughen` that preserves path count but corrupts the curve (rounding a eutectic cusp into a smooth minimum; turning a step-function into a ramp) **passes the lock clean** — asserting a physical falsehood undetected. Also: `ACTION_TYPES` is 5 scalar setters with no path-`d` write primitive (B is unbuilt, not reusable); `tikz_patch`/`continue_tikz` are *live* routes (the brief's "dead enum" claim was false).

**Safety-model reframe (adversarial review, 2026-06-21).** The layer-based model ("structural layer = truth, `hand:*` overlay = free") is the **wrong abstraction**. Truth is a property of **specific paths** and of the **rendered composite** and of the **shipped artifact** — not of layers:

- **Truth is per-path, not per-layer (H2).** A device outline is a structural path whose *curvature is decorative*; a phase boundary is a structural path whose *curvature is truth*. The layer model cannot tell them apart, so it either over-blocks legitimate aesthetic edits or silently permits falsehoods. The canvas (#1) must carry a per-path **`truth_bearing: bool`** (default `true`; set `false` only by explicit author intent). The curvature invariant applies to `truth_bearing` paths only.
- **B splits by what it touches (H1, resolved 2026-06-21).** Hand-feel is two distinct capabilities, gated differently — the user gets **both**, not a choice:
  - **(a) centerline-preserving stroke treatment** — `taper`, texture, weight/opacity variation, `double_stroke` that follow the exact `d`. Changes how a line *looks*, not *where it is* → **truth-safe on any path, including `truth_bearing` ones.**
  - **(b) centerline-altering geometry rewrite** — `smooth`, `simplify`, `roughen`, `jitter`, `soften_corners` that move `d`/control points. This *is* a truth claim → permitted **only on `truth_bearing:false` (decorative) paths.**
  The single red line: a **centerline-altering op on a `truth_bearing` path is forbidden outright** — overlay is *not* an escape, because a reshaped curve rendered above truth is still the picture the reader believes. The reader-visible image must never contradict a truth path. (Net: the only thing given up is silently restating a meaningful curve — i.e. scientific fraud.)

**Required gates (hard preconditions):**
1. **Per-path op gate.** Centerline-preserving stroke ops allowed on any path; centerline-altering `path_rewrite` allowed iff target is `truth_bearing:false`; else rejected at plan time.
2. **Geometry-aware diff for truth paths.** Parse `d` (`svgpathtools`); assert vertex/corner count, sign-of-curvature run-length, and a Fréchet/Hausdorff bound. **The bound is itself judgment-bearing (H4)** — it scales with figure units and must be *declared per figure* (or proposed by a critique signal), never a silent global constant. **Canonicalize `d` segmentation before comparing** so a pure `resample` that preserves shape is not false-flagged (and so vertex-count games cannot hide drift).
3. **Composite-color check (H6).** Run `verify_cvd/grayscale/contrast` on the **rendered, composited raster** (gradient × shadow × fill as the eye sees it), not per-fill SVG colors. Resolve `url(#grad)` to stops first.
4. **Shipped-artifact gate (H3).** The lock checks SVG, critique reads PNG, but the journal prints a **PDF in CMYK**. A terminal gate renders the *actual export* (PDF at target DPI), converts to print color space (CMYK), and re-runs critique + composite-color check **there** — catching filter rasterization, renderer divergence, and RGB→CMYK color shift. The figure you verify must be the figure you ship.
5. **`relationship_guard` + occlusion guard** (specified, not asserted; zero in-tree today): declared spatial relations (A-left-of-B, A-inside-B, A-connected-by-leader) from a native bbox inventory replacing the dead `pdftotext` path — **plus the new rule that no overlay may visually replace a truth path.**
6. **`commit()` is all-or-nothing**: any BLOCKER/MAJOR rejects the whole write.

With these, the critique can misjudge *taste* but cannot make the schematic *wrong — in the data, in the composite, or in the shipped PDF.* The layer model alone promised none of that.

## 6. Evaluation fixtures

- **Cusp-falsehood test:** `smooth(catmull_rom)` / `simplify(epsilon=2)` on a phase-boundary cusp and a step-function (quantized level, sharp absorption edge) **must be rejected** by the geometry-aware diff. (Today: passes — the regression target.)
- **Overlay-safe test:** an overlay `add_volume_shading` / added gradient `defs` must NOT trip `element_inventory_change` (needs the `hand:*` allowlist).
- **Color-correctness:** a `crameri_map` gradient that re-orders perceptual lightness must fail until CVD/grayscale/contrast pass.
- **Export-A test:** confirm soft-shadow filters rasterize on PDF export; confirm filter-free volume shading (Lambert gradients / cel bands / long-shadow geometry) survives vector export.
- **Composition test:** a panel needing >10px rebalancing must be expressible (D's translate budget).
- **Overlay-lie test (H1):** an overlay path that visually replaces/contradicts a `truth_bearing` path beneath it **must be rejected** (overlay-confinement is not a truth escape).
- **Resample-invariance test (H4):** a pure `resample` of a `truth_bearing` path (same shape, different point count) must **pass** after `d` canonicalization (no false-positive); a sub-Fréchet-but-meaningful drift must still fail.
- **Composite-CVD test (H6):** individually CVD-safe fills that, composited with a gradient+shadow, fail CVD must be **caught** on the rendered raster.
- **Shipped-PDF/CMYK test (H3):** a figure passing the SVG lock + PNG critique but diverging on PDF export (filter raster / renderer / RGB→CMYK shift) must be **blocked by the terminal ship gate**.

## 7. Honest scope and build order (release plan)

**Scope honesty (corrects the brainstorm's optimism):** B is **from-scratch** (new `path_rewrite` action class + plan-time geometry validator + curvature invariant) — the single largest work item, *not* a contract "widening." Component #6 (accuracy lock) is a **rebuild**, not a reuse. A is **export-crippled by default** (blur rasterizes on PDF) → default A must be filter-free shading. D **ships** but needs its own >10px structural-translate budget under `relationship_guard`. `tikz_patch`/`continue_tikz` must be shimmed or retired-in-code, not ignored.

**Build order — "lock first, draw second"** (note: this is safety-correct but desire-inverted — B, the user's #1 want, is last and riskiest):

- **Slice 0 — geometry-aware accuracy lock + truth model.** (1) `path_geometry_inventory()` extension to `svg_semantic_diff` (parse `d`, canonicalize segmentation, topological signature, declared Fréchet bound). (2) per-path **`truth_bearing`** field on the canvas + the per-path gate. (3) `hand:*` overlay namespace + allowlist + occlusion/no-truth-replacement guard. (4) **shipped-artifact gate** (PDF→CMYK re-render + composite-color check). (5) one end-to-end op — **`add_volume_shading`** — as a *true non-occluding overlay* (NOT recoloring the object's own fill, which would be structural paint — H9); proves the v2 recipe fields + the path/composite/ship safety model with a visible A win and no truth-path mutation.
- **Slice 1 — v2 recipe schema + `path_rewrite` action class** (net-new fields: `layer`, `action_class`, `determinism` axes, `driven_by`, `seed`) and the plan-time geometry validator.
- **Slice 2 — D composition** (`measure→CompositionReport`, `snap_to_grid`, larger translate budget gated by `relationship_guard`).
- **Slice 3 — B organic curves**, split (user-confirmed 2026-06-21: both classes wanted). **Precondition: per-path `truth_bearing` (Slice 0).** **(a)** centerline-preserving stroke ops (`taper`, texture, weight variation, `double_stroke`) ship for **any** path including truth-bearing — truth-safe, the higher-value/lower-risk half; build first. **(b)** centerline-altering rewrites (`smooth`/`simplify`/`roughen`/`jitter`) are **`truth_bearing:false`-only** and run behind the geometry guard. The single forbidden op = centerline-altering on a truth path (no overlay escape — H1).

## 8. Non-goals

- WYSIWYG / drag editing UI (C — explicitly excluded).
- AI image generation as a renderer (hallucinated topology breaks the truth guarantee). Permitted only as ideation/reference, never as the factual artifact.
- Data plots (Graph Hub).
- 3D (overkill for 2D schematics; `vedo`/MolecularNodes remain optional adjuncts, out of scope here).

## 9. Open risks (track, do not bury)

1. Accuracy lock geometry-blind — top priority; §5 is a hard precondition for any B op on truth.
2. `path_rewrite` class + v2 schema + parallel op taxonomy do not exist (from-scratch).
3. A's blur unavailable in the export target — default print stays flat unless filter-free shading is default.
4. D's 10px translate ceiling blocks real composition.
5. `tikz_patch`/`continue_tikz` live — shim or retire.
6. Loop oscillation with no taste oracle (`childish ↔ dead_flat`); cap iterations, route to `needs_human_art_direction`.
7. Vaporware guards (`relationship_guard`, native bbox inventory, `hand:*` allowlist) are load-bearing and unspecified.
8. **Unsolved core — where competent taste comes from.** This design delivers the *safety + operations scaffold*, not the taste engine. The proposed future oracle is a **recorded human-op corpus** (capture an expert's Inkscape/Illustrator edits as parameterized macros, yielding priors for `epsilon`/roughness/corner-radius). The "illustrator-grade" north star ultimately hinges on this; it is deferred, not solved.

**Adversarial-review additions (2026-06-21) — structural ones folded into §5; tracked here:**
9. **B scope (H1 — RESOLVED 2026-06-21).** B splits into centerline-preserving stroke treatment (truth-safe, any path) and centerline-altering rewrite (decorative-only). Hand-feel on meaningful lines IS reachable via (a); only the geometry-lie (centerline-altering on a truth path) is given up. Residual risk: the (a)/(b) boundary must be enforced per op in the taxonomy, and `taper` must be checked to preserve the centerline (filled-outline taper that drifts the centerline would sneak into (b)).
10. **Per-path `truth_bearing` annotation is a new burden that can rot (H2+H7).** Who sets it, how it survives path-creating/merging ops, and a semantic-integrity check are unspecified; drift silently breaks both the lock and "emphasize the chain" addressing.
11. **Reproducibility is replay-only (H5).** Ops are seeded-deterministic, but the op *sequence* comes from a non-deterministic LLM critique; re-running the same intent yields a different figure. State this limit; do not claim generation-reproducibility.
12. **Geometry-guard threshold is itself judgment-bearing (H4)** — declared per figure, never a silent global constant.
13. **Composited color ≠ per-fill color (H6); verified artifact ≠ shipped artifact (H3)** — both gated in §5; the two checks most likely to be skipped under time pressure.
14. **Concurrent-session SVG conflicts (H10).** Parallel agents on one semantic SVG → XML merge hell + decision-log divergence; needs an ownership/lock model.
15. **Taste-corpus is narrow (H8).** Priors only for *seen* figure types and *one* illustrator's taste; novel schematics are out-of-distribution.

## References

- `ILLUSTRATORS_HAND_design.md` — full piece #3 design (verified against source 2026-06-21).
- `.hand-deepdive-2026-06-21/` — craft-findings (P1), synthesis (P2), skeptics (P3 adversarial), reuse-map (P0).
- Memory: `project_figure_agent_northstar.md`.
