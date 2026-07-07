# Spec: Geometry-vocabulary gaps — closing the not-modeled QA blind spots

Status: DRAFT for agent execution (revised after adversarial technical + history review, 2026-07-07)
Evidence base: 2026-07-07 blind-spot check — 8 human-eye defects on fig1_overview_v5f_art_direction_001_vault
(a figure the auto-loop had declared converged); tool detected 1/8, promoted 0/8. Root-cause split:
7/8 = the relation is computed nowhere ("not-modeled"), 1/8 = detected but killed by the promotion gate
(VC012, the "Energy"-label collision). Zero findings were caused by insufficient resolution (600dpi).

> **Read this first — what the adversarial pass changed (changelog):**
> - G1's "universal declaration-free tier" (U1/U2) is **CUT**. It resurrected the intent-inference the
>   perception spec was rejected for (2026-05-08), and its FP-safety math was inverted (see below). Vector↔vector
>   rules ship **declaration-gated or critique/nitpick-only, never auto-promoted.**
> - **Bézier-hull clearance direction was wrong** in the draft. A curve lies *inside* its control hull, so
>   hull-clearance is a **lower bound** (never misses a real violation, **can false-positive**) — the opposite
>   of what the draft claimed. Curve clearance is therefore conservative-flag-only, human/critique-reviewed.
> - **Circle is the dominant curve** on the benchmark fixture (~60 `circle` ops vs 0 named-coords, 0 arcs,
>   ~23 bézier). G3 now specifies circles explicitly; named-coordinate resolution is **demoted** (≈0 coverage
>   on this corpus) and gated behind a fixture that actually uses named coords.
> - **Declaration drift** (anchor still matches but binds the WRONG element) is now a first-class requirement:
>   every declared selector must fail loud on zero-match AND multi-match, with tests.
> - **Hard ordering dependency**: G4 auto-promotion must land AFTER parent-plan Phase 0.6d, or it promotes
>   still-fail-open detector output into the ledger.
> - G4 triage is not free: visual_clash candidates lack `tex_lines`/`defect_class`, so triage-accept must
>   synthesize them; the queue must show evidence crops inline, not just IDs.

## 1. Purpose

Add the missing measurement vocabularies to the DETERMINISTIC QA stack so the class of defects found by the
2026-07-07 human inspection becomes machine-detectable and machine-actionable, WITHOUT recreating the
false-positive flood the 2026-07-07 auto-loop diagnosis exposed (15 noise candidates from undeclared-geometry
promotion) and WITHOUT re-treading the intent-inference the perception spec was rejected for.

This spec defines WHAT to build, the acceptance bar, and the ordering. It does not fix module layout; the
implementing agent derives a per-phase plan via superpowers:writing-plans. **Each gap is a separate spec/PR
— do not batch.**

## 2. Non-goals (binding — do not re-litigate)

- **No LLM aesthetic judgment in gates.** Rejected repeatedly (figure-quality spec 2026-05-04; N=1 critique
  ≈18%). LLM vision stays advisory (critique), never a pass/fail authority.
- **No topology / intent auto-discovery.** Rejected (perception spec, docs/trials/2026-05-08-perception-spec-review-codex.md:
  "the hidden dependency is semantic judgment"). Every intent-dependent check here is DECLARATION-driven; the
  author states the relation, the checker measures it. **No rule decides on its own whether a geometric
  configuration is "wrong" when the same configuration is legitimately intentional elsewhere** (a fit-line
  through data markers is conventional — that is why U1 is cut).
- **No new subregion-hash scheme** (three already coexist). Reference geometry by declared id + coordinates.
- **No weakening of existing gates.** Fail-closed doctrine stays: a checker that cannot read its evidence
  blocks or fails loud; it never silently passes.
- **No auto-promotion of pixel-heuristic findings.** The visual_clash human-adjudication gate
  (docs/superpowers/specs/2026-05-21-visual-clash-evidence-integration-design.md; 2026-05-20-auto-adjudication-policy-design.md)
  is deliberate FP control. G4 makes it FASTER to work, not bypassable.

## 3. Design principles

P1. **Declaration over discovery.** Intent-dependent relations are author-declared once, checker-verified
    forever. Declaration-free rules are permitted ONLY where precision is structurally near-1.0 AND the
    codebase already models the structure the rule needs. (The draft's U1 failed this second clause — there
    is no plot-grouping structure in the stack, so "exclude a plot's own line" is not structurally decidable.
    Hence no declaration-free vector rules ship in this spec.)

P2. **Precision first, recall second — measured, not asserted.** Before any new rule is declared "ship-ready,"
    the implementing agent runs it across the real-fixture corpus (fig1 v5f, fig2, fig3, v5a–e) and the user
    verdicts the raw findings once. Budget: ≤2 human-rejected findings per fixture. A rule that misses the
    budget ships declaration-gated (author opts in per figure) rather than universal. This verdict pass
    doubles as the first review-queue dogfood.

P3. **Promotion-or-nothing, with the right trust tier.** A detector nobody reads is a WARN-graveyard (the
    reach=0 pattern; confirmed: quality_defect_ledger reads 3 of the ~10 `check_*` outputs). Every capability
    ships as a triple: (detector) + (ledger/queue rule with a trust tier) + (edit-family mapping the improve
    loop can act on). A PR adding only the detector is incomplete. BUT trust tier matters: deterministic-evidence
    detectors auto-promote; pixel-heuristic detectors go to the human review queue (§G4).

P4. **Deterministic evidence.** Each finding carries: rule id, measured quantity (cm at figure scale), tex
    anchor(s) (file:line or matched text), the declared threshold violated. No finding without a number.

P5. **Declaration integrity is enforced, not assumed.** Every declared selector resolves to EXACTLY one
    target. Zero matches → fail loud (anchor vanished — drift). Two+ matches → fail loud (ambiguous bind —
    the anchor text now also matches a different element; this is the silent-false-pass drift mode and is the
    single most dangerous failure of a declaration-driven stack). Both are acceptance-tested, not implied.

## 4. The four gaps

Coordinate-space note (applies throughout): the source-side extractor emits **tex-source cm**; existing
declared-path checkers (label_path_proximity, text_boundary) use **rendered pdf_cm**. Any rule that mixes a
source-extracted element with a pdf_cm declaration MUST convert explicitly and state which space each side is
in. Do not assume they are the same space.

### G4 — Promotion wiring (build FIRST; smallest, no new detection, no new FP risk) — finding #2 / VC012

**Problem.** quality_defect_ledger reads 3 of ~10 detector outputs. tex_assertions (reversed physics arrows),
semantic_assertions, label_path_proximity, layout_drift, hyphenation, physics_grounding never become
actionable — console WARN only. visual_clash (44 candidates on v5f incl. the real VC012 "Energy" collision)
requires a human to hand-copy findings into critique.md before the ledger looks.

**Hard dependency (do not start G4 auto-promotion before this):** parent-plan Phase 0.6d fail-closed
semantic_assertions on missing spec but left `anchor_missing` a possible silent pass. Auto-promoting a
detector that can still fail open injects garbage into the ledger. **G4 auto-promote tier may only include a
detector once that detector is confirmed fail-closed AND satisfies P5 (zero/multi-match loud).** Verify per
detector before wiring it.

**Capability — three tiers, not "promote everything":**
1. **Auto-promote tier** — deterministic-evidence, fail-closed detectors only: `tex_assertions` (a reversed
   declared arrow is never an FP) and `semantic_assertions`/alignment (declared, numeric). Promote with the
   measured delta. Precondition: the detector passes P5 and is fail-closed (see dependency above).
2. **Review-queue tier** — pixel-heuristic (`visual_clash`): candidates land in `build/promotion_queue.json`,
   surfaced by `fig-agent status`/`next` as a count + top-N. A human bulk-triages
   (`fig-agent triage <fixture> --accept VC012,… --reject-rest` or equivalent). **The queue view MUST render
   each candidate's evidence crop inline (reuse critique_zoom_crops), not just IDs** — bulk-accept on IDs
   alone degrades adjudication to rubber-stamp and destroys the FP control the gate exists for.
   **Triage-accept is not a no-op copy:** visual_clash candidates carry `{id,kind,bbox_px,metric,text}` with
   `tex_lines:null` and no `defect_class`. Accept MUST synthesize the fields the ledger requires — derive the
   `tex_lines` range from `bbox_px`→source mapping (or require the human to supply it) and assign a bounded
   `defect_class` — then route through the EXISTING critique_finding_gate path (same gate, faster front-end).
   Budget this synthesis; it is the real cost of the "1-minute sweep."
3. **Non-promoting tier** (recorded so the next audit doesn't re-flag as accidental reach=0): layout_drift
   (reference-relative), hyphenation (cosmetic), physics_grounding (doc meta-check). Stay advisory.
4. Provenance: promoted findings carry `promoted_by: auto|triage` + source detector, so experience-log rows
   record which trust tier produced each defect.

### G2 — Alignment vocabulary, TEXT-ONLY (build SECOND; cheap, declaration-driven, near-zero FP) — finding #1

**Problem.** Relational vocabulary is above/below/left_of/right_of/distance — no "equals." No way to assert two
elements share a baseline/edge/center. Finding #1 (ISPD subtitle floating ~8pt above its row siblings'
baseline) is invisible in principle.

**Capability.**
1. Extend `semantic_assertions` (word-bbox centroid based, wired at compile.sh:122) with alignment kinds:
   `{kind: baseline_aligned|top_aligned|left_aligned|right_aligned|center_aligned_x|center_aligned_y,
   targets: [label_a, label_b, …] (2+), tolerance_cm (default 0.05)}`. Word boxes give baselines directly;
   N-way = all pairwise deltas within tolerance. Enforce P5 (each target label resolves to exactly one box;
   zero/multi → fail loud).
2. Vector-element alignment is **explicitly deferred** (needs G1's extractor). This gap is text-only.
3. Promotion: alignment violations are text-position defects → auto-promote tier (unambiguous cm delta),
   edit family `label_reposition`/`bounded_coordinate_offset` (adequate for text; see G-edit note).
4. Seed declarations (the acceptance vehicle): add row-subtitle baseline assertions for fig1 v5f
   (kinetic/ISPD/mechanical) and panel-letter row alignment for fixtures with coordinate-stable letters.

### G3 — Shape/coordinate parsing vocabulary (build THIRD; a multiplier, only earns its keep if G1 ships)

**Problem.** check_undeclared_geometry (`_POINT_RE`, line 36) and check_tex_assertions parse only
literal-numeric straight 2-point `\draw`s (check_tex_assertions parses no rects at all). Curves and
non-literal coordinates are invisible, capping source-side recall.

**Measured reality on the benchmark fixture (fig1 v5f) — the implementing agent MUST re-measure and record
baselines before building, but the draft's premise was corrected here:** the dominant unparsed geometry is
`circle` (~60 ops), then bézier `controls` (~23); **named-coordinate draws ≈0, `arc` ≈0, `\coordinate` defs ≈0**.
Consequences:
1. **Circles are the priority, and the draft omitted them.** Add circle handling: a circle is center±r → a
   bbox/disc, no control points. G3 clearance rules operate on the disc.
2. **Bézier / `to[out,in]`: convex-hull envelope, used correctly.** A cubic Bézier lies INSIDE its control
   hull (curve ⊆ hull). Therefore hull-based clearance is a **conservative lower bound**: it never misses a
   true violation but CAN over-flag (false-positive) when the true curve is further from the element than its
   hull suggests. **This means curve clearance results are NOT auto-promotable** — they are declaration-gated
   or critique/nitpick-only until true-curve flattening exists. (This reverses the draft's inverted claim.)
   Exact flattening is a future extension, not this spec.
3. **Named-coordinate resolution (`\coordinate (n) at (x,y)` substitution) is DEMOTED.** It buys ≈0 coverage
   on this corpus. Build it only when a target fixture actually uses named coords; until then it is
   out-of-scope, and unresolvable coordinates emit a coverage WARN naming the path (fail-loud-not-block:
   unresolvable TikZ — `calc`, intersections — is legitimate).
4. **pdfplumber curves already exist — do not rebuild.** `page.curves` is read at perception_pack.py:89.
   check_undeclared_geometry reads only `page.lines`/`page.rects`; extend it to consume the existing curve
   reader, don't write a new one.
5. **Measure the win.** Report parse coverage (% of `\draw/\fill/\shade` yielding typed geometry vs UNKNOWN)
   per fixture, before/after. Do NOT hardcode a target number in this spec — the draft's ≥70% was unfounded;
   the agent measures the real baseline, sets an honest post-build number, and records what remains UNKNOWN
   and why.

### G1 — Vector↔vector relations, DECLARATION-GATED ONLY (build LAST; highest value, highest risk) — findings #7, #8

**Problem.** No checker computes any relation between two vector elements: path-through-marker (#7),
element crowding (#8), path-path clearance.

**Capability — declared-tier only; the draft's universal tier is cut.**
1. Vector-element extractor: typed list from tex parse + the existing pdfplumber readers (lines/rects +
   curves per G3.4), per G3's vocabulary: `{kind: line|polyline|curve|rect|circle|marker|arrowhead,
   geometry (cm, tex-source space), style:{width,dash,color}, tex_anchor}`. Marker/arrowhead ID via
   structural style heuristics (small filled disc = marker; TikZ arrow-tip construct = arrowhead).
2. `vector_clearance_checks` in spec.yaml:
   `{id, element_a: <selector>, element_b: <selector>, min_clearance_cm | must_touch | must_not_cross}`.
   **Selector grammar (the draft's "reuse label_path_proximity grammar" was wrong — it has coordinates but
   NO tex-anchor selector):** selectors reference elements by (a) declared coordinates in a stated space, or
   (b) a tex-anchor — which requires a NEW small selector grammar this spec authorizes (matched-text or
   file:line range → element). Enforce P5 on every selector (zero/multi-match fail loud). Curve elements make
   the clearance conservative (G3.2) → such a check is flagged non-auto-promotable in its result.
3. Promotion: declared vector_clearance violations promote at the text_boundary tier — EXCEPT any check whose
   `element_a`/`element_b` resolves to a curve/circle envelope, which is review-queue tier (conservative
   geometry, may over-flag).
4. `element_crowding` (#8) is **critique/nitpick-only, never promoted** — surfaced into the crop set to draw
   human/LLM attention, not turned into an edit. (This is the old U2, kept, but explicitly non-promoting.)
5. **Cut:** the universal declaration-free `path_through_marker` (old U1). Precision cannot be made near-1.0
   structurally (no plot-grouping in the stack; "same-plot line" is undecidable; a fit-line through markers is
   often intended). Finding #7 is addressed ONLY when an author declares `must_not_cross` for that specific
   line/marker pair. If unattended detection of #7 is later wanted, it needs a declared plot-group structure
   first — a separate spec.

**G-edit note (D7):** `bounded_coordinate_offset` mutates the FIRST literal coordinate on a source line. That
is adequate for text labels (G2) and single-literal straight segments, but INADEQUATE for curves/circles
(deforms shape / no single first-literal to move) and multi-coordinate paths. Any G1/G3 edit that must
translate a whole vector element requires **translate-whole-element semantics** (offset every coordinate, or
a canvas transform) — specify or add an edit family; do not assume first-coordinate offset relocates a curve.
G1 findings without a valid edit mapping are detect-and-report only (still valuable), not loop-actionable.

## 5. Priority & phasing (value ÷ risk; each independently shippable — do NOT batch)

1. **G4** — smallest, immediate value (already-detected findings become actionable; VC012-class stops dying).
   No new detection ⇒ no new FP. **Gated on parent-plan Phase 0.6d for the auto-promote tier.**
2. **G2 (text-only)** — cheap, declaration-driven, near-zero FP, kills finding-#1-class defects.
3. **G3** — no user-visible checks of its own; multiplies G1 and existing source-side checkers. Only worth
   building if G1 will follow.
4. **G1 (declared-only)** — highest value, highest risk; lands after G3 so it starts with the full shape
   vocabulary and after G4 so its findings have a promotion path.

## 6. Acceptance criteria — the 8-finding benchmark (+ anti-overfit)

Benchmark: the 2026-07-07 human inspection of fig1 v5f (build at main a2fb2e75). After the phases land (with
seed declarations from G2.4 and ≤5 new spec.yaml declarations on fig1 v5f):

| Finding | Must become | Via |
|---|---|---|
| #1 ISPD baseline float | detected + auto-promoted | G2 baseline_aligned |
| #2 connector through "Energy" | promoted (already detected) | G4 review-queue triage (with synthesized tex_lines/defect_class) |
| #7 Debye line through markers | detected ONLY IF declared `must_not_cross` (not auto) | G1 declared + G3 curves; result marked non-auto (conservative curve geometry) |
| #8 peak crowding | surfaced in critique crops, NOT promoted | G1 element_crowding (critique/nitpick tier) |
| #6 field-line offset | **DEFERRED** — needs vector-alignment (G2.2, deferred). Removed from this benchmark. | — |
| #3 arrow-short / #4 caliper-anchor / #5 halo-consistency | OUT of deterministic scope (intent-heavy) — recorded in the coverage doc as known human/critique-only classes | — |

**Anti-overfit (P2 + cross-figure recall):** passing 4 known instances generalizes to nothing on its own.
Two additional bars:
- **FP budget** measured corpus-wide (fig1/fig2/fig3/v5a-e), user-verdicted once: ≤2 rejected findings/fixture.
- **Cross-figure recall:** seed a KNOWN defect of the #1 class (a deliberate baseline float) on a NON-v5f
  fixture (e.g. fig2 or fig3) and require G2 to detect it. Precision-without-recall proves "doesn't flood"
  but not "catches the analogous defect elsewhere"; this bar closes that gap.

Plus: full suite green; every new checker has missing/corrupt/wrong-schema fail-loud tests AND P5
zero/multi-match tests; parse-coverage report (G3.5) committed for fig1 v5f + fig2 + fig3; an acceptance test
greps the ledger/queue for each new detector's output key (enforces P3 — no orphan detector).

## 7. Explicitly deferred (record, don't build)

- Vector-element alignment assertions (G2 vector half) — after G1+G3 stabilize; unblocks finding #6.
- Exact Bézier/arc flattening for tight-clearance curves — hull/disc envelope first; revisit only if the
  conservative envelope over-flags or misses a real defect in practice.
- Named-coordinate resolution (G3.1 full) — until a target fixture actually uses named coords.
- Unattended `path_through_marker` (old U1) — needs a declared plot-group structure; separate spec, only if
  a measured precision case emerges.
- Arrowhead-target contact as a declared assertion (`terminates_near`, finding #3) — a plausible tex_assertions
  extension, but needs G3 named-coord resolution to bind targets; write it only after G3's coverage numbers.
- Same-role glyph style consistency (finding #5) — needs declared glyph groups; intent-heavy; keep human.
- Auto-promotion of any pixel-tier or curve-envelope finding — never, absent a measured precision case.
