# Sub-Region Iteration Tool — Issue / Pre-Spec

**Status:** ISSUE + narrow parser prototype. No schema, cropper, or auto-segmentation committed.
**Filed:** 2026-05-15
**Drives from:** `feedback_element_iteration_workflow.md`, `feedback_subregion_iteration_unit.md`.
**Predecessor work:** `architecture-v0.5-per-panel-reference-workflow.md` lifted granularity from figure → panel. This issue asks whether to lift granularity panel → sub-region.

---

## 1. Problem

`/fig_critique` v0.5 compares each panel against its per-panel reference image. Granularity stops at panel.

Real iteration unit (memory: `feedback_subregion_iteration_unit.md`) is **sub-region within a panel**. Concrete case on file: `fig1_overview` center hub panel has ~8 distinct sub-regions (left polymer chain, right polymer chain, top/bottom arrow groups, central node, etc). Author edits one sub-region per iteration — e.g., "Row 3 polymer chain: add S markers, second chain wider, 1pt bolder" — and re-compiles.

Current `/fig_critique` collapses all 8 sub-regions into one panel-level verdict. This either dilutes the feedback (vague panel-wide comments) or drifts toward generic style commentary, which is the N=1 dogfood failure mode (`session_dogfood_n1_critique_failure.md`: 2/11 = 18% accuracy).

## 2. Why this matters

`feedback_element_iteration_workflow.md` records the falsified-then-locked workflow: 5–10 iterations × 1-line patch = Nature-grade figure. The tool does not yet surface this primitive. Author has been doing the partitioning in their head; the tool can structure it for both author and LLM.

This is also a **prerequisite for the SVG-polish-pipeline issue** (`svg-polish-pipeline.md`): without sub-region iteration data, we cannot tell *which* specific polish operations TikZ fails to cover.

## 3. Sketch (not committed)

Three candidate shapes, listed so design discussion has anchors. Do not read as recommendations.

1. **Schema extension** — `spec.yaml.panels[i].subregions[j]` with id + optional reference_image + optional bbox. Author declares sub-regions. Cost: spec.yaml grows.
2. **Auto-partition from reference** — `/fig_critique` segments reference image into sub-regions. Walks back into rejected family (`feedback_perception_spec_rejected.md`: no PDF-geometry invariant). Likely a dead end, but listed for completeness.
3. **Reference-driven, no schema** — author drops `reference/panel_A_polymer_chain.png`, `reference/panel_A_arrow_group.png` files; tool enumerates by filename convention. Cheap; preserves v0.5 architecture cleanly.

Option 3 inherits v0.5 cleanly; option 2 re-enters falsified territory.

*Note (2026-05-15):* The §8 case study added a fourth candidate de facto — **Option 4: briefing.md text-form, no spec.yaml schema** — and partially falsified Option 1 via cross-panel tier discovery (§8.3 #1). The sketch is left intact as historical record; the live answer to "which shape" now lives in §8.2 + §8.3.

## 4. Open questions

- How does author declare sub-regions without spec.yaml boilerplate explosion?
- Does `/fig_critique` iterate sub-regions sequentially or aggregate at the end?
- Does sub-region need PDF-bbox (like v0.5 panel bbox), or is reference-image-only sufficient?
- What is the minimum useful prototype? (Likely: 1 sub-region per panel on `fig1_overview_v2`, no bbox, just to validate workflow shape.)

## 5. Non-goals

- ❌ Auto-detecting sub-region boundaries from PDF or reference image. Same falsification family as v0.4 perception.
- ❌ Sub-region-level patch synthesis. Tool surfaces the iteration unit; author still writes the 1-line patch.
- ❌ Replacing panel-level critique. Sub-region is additive.

## 6. Dependencies / prerequisites

- v0.5 per-panel reference workflow shipped (`81aa08b`).
- v0.5 dogfood on `fig1_overview_v2` complete — supplies the empirical sub-region examples that should drive design (see `session_handoff_2026_05_09.md`).

## 7. Decision gate

**Status (2026-05-15): PARTIALLY MET — design remains BLOCKED, but enumeration prerequisite is closed.**

Original gate split into two:

| Prerequisite | State | Evidence |
|---|---|---|
| Enumeration (≥1 concrete panel sub-region list) | ✅ MET | §8 case study — 46 sub-regions across `fig1_overview_v2_pair_001_vault` 7 panels + Row 2 cover-binding. Source: `examples/fig1_overview_v2_pair_001_vault/briefing.md` §13. |
| Iteration log (which sub-regions actually received 1-line patches over multiple cycles) | 🟡 LIVE EVIDENCE STARTED | `examples/fig1_overview_v2_pair_001_vault/subregion_iteration_log.md` records the v5-v7 active/stable split and concrete patch units. More cycles and at least one cross-fixture comparison are still required before tool design unblocks. |
| Cross-fixture generalization | ❌ PENDING | §8.4 requests enumeration for at least one other fixture (`fig1_overview_v2` no-vault arm or `golden_trap_depth_picture`). Single-fixture form might not generalize. |

**Design remains blocked** until the live iteration log has enough cycles and
cross-fixture comparison surfaces. The enumeration alone tells us *what*
sub-regions exist; the iteration log tells us *which ones are real iteration
units vs. named-but-stable catalog entries* (§8.3 #2). Without enough of the
latter, schema design optimizes for the wrong dimension.

Tool shape must come from observed iteration, not from this issue.

**Narrow parser prototype (2026-05-16):** `scripts/subregion_active_set.py`
parses `subregion_iteration_log.md` Markdown tables and emits the current active
target IDs plus observed patch-unit IDs. `scripts/critique_brief.py` includes
that summary in the reference-conditioned authoring context when the log exists.
This is not a schema commitment: it reads the live evidence file, keeps an empty
active set empty, and does not infer boundaries, crop sub-regions, or modify
TikZ.

---

## 8. Case study — fig1_overview_v2_pair_001_vault (2026-05-15 dogfood)

First sub-region enumeration completed as text-form in `examples/fig1_overview_v2_pair_001_vault/briefing.md` §13 (this fixture is the active dogfood target driving Row 2 cover-feel redesign per Cover-scene + M2 + P-A branching).

### 8.1 Observed sub-region counts

| Panel | Sub-regions | Notes |
|---|---|---|
| A (sulfur polymer chemistry) | 8 | Includes background wash + inset + dashed arrow as distinct iteration units |
| B (chain length scaffold) | 3 | Simplest panel — single chemistry concept |
| C (HERO trap landscape) | 11 | LEFT 5 + RIGHT 6 — split-half drives higher count |
| Row 2 cover-binding | 3 | shared background + branching root + 3-spoke (figure-level, NOT panel) |
| D (kinetic icon) | 5 | iconic plot panel post M2 axis-frame removal |
| E (ISPD raw icon) | 4 | E↔F paired ISPD arrow counted under E |
| F (g(E_t) icon) | 5 | Two Gaussian bands + τ_d arrow + 2 labels + axis |
| G (mechanical scene) | 7 | Isometric scene — many distinct elements (clip, electrode, strip, markers, leader, Coulomb arrow, air-gap label) |
| **Total** | **46** | A:8 + B:3 + C:11 + Row2:3 + D:5 + E:4 + F:5 + G:7 |

Range per panel: **3 (B) to 11 (C HERO)**. Average ~5.5. Matches `feedback_subregion_iteration_unit.md` memory ("5-8 per panel") with hero panels exceeding upper bound.

**Row 2 cover-binding** introduces a new sub-region tier: *cross-panel structural elements* (shared background + branching root + spokes) that are neither figure-level nor panel-level. Tool design must accommodate this tier.

### 8.2 Answers to §4 open questions (preliminary, from this case)

**Q: How does author declare sub-regions without spec.yaml boilerplate explosion?**
A: Text-form in `briefing.md` works. 46 sub-regions × ~1 line each = ~50 lines added; survivable. No `spec.yaml` boilerplate. Form: `**ID** description` markdown bullet, grouped by panel headers (§13.1 ... §13.8).

**Q: Does `/fig_critique` iterate sub-regions sequentially or aggregate at the end?**
A: **Active subset, not all 46.** This case marked ~10 sub-regions as "active iteration target" (Row 2 newly authored + Panel C LEFT medium-limit) and ~36 as "stable / minimum iteration". A useful critique iterates active subset only. Aggregation at panel/figure level remains via existing v0.5 critique.

**Q: Does sub-region need PDF-bbox (like v0.5 panel bbox), or is reference-image-only sufficient?**
A: **Neither bbox nor reference image was needed for the enumeration itself.** ID + 1-line description suffices to *name* the iteration unit. Whether tooling (e.g., crop generation, panel-style reference grounding) requires bbox is a separate question; for design input it does not.

**Q: What is the minimum useful prototype?**
A: From this case: text-form sub-region list in `briefing.md` is sufficient *as design input*. A useful tool would (1) parse the briefing list, (2) let author tag active subset, (3) feed active subset to `/fig_critique` as scoped sub-prompts. No new schema needed.

### 8.3 New findings beyond §3 sketch

1. **Cross-panel structural tier**: Option 1's `spec.yaml.panels[i].subregions[j]` shape does not accommodate "Row 2 cover-binding" sub-regions (shared background + branching arrow spanning multiple panels). Schema must allow figure-level sub-regions OR cross-panel grouping.
2. **Iteration target vs stable distinction is itself a data field**: Active/stable tag changes per session and is the actual primary filter for tool output. Treating sub-regions as static catalog misses this dynamism.
3. **Panel A's "background wash" (A-7) and Panel G's "air gap label" (G-7) are sub-regions by author intuition** even though they're not *visually prominent*. The boundary is "could I patch this in one line?" — yes for both. Confirms iteration-unit > visual-prominence as the partitioning criterion.

### 8.4 Next dogfood inputs requested

- Iteration log: which sub-regions actually got 1-line patches over the next 5-10 cycles, and which were "named but never touched"? — informs whether enumeration density is correct.
- Pilot live log: `examples/fig1_overview_v2_pair_001_vault/subregion_iteration_log.md` is now the current evidence surface for the v5-v7 loop. Treat it as live evidence, not as a finalized schema.
- Cross-fixture comparison: enumerate sub-regions for at least one other fixture (`fig1_overview_v2` no-vault arm or `golden_trap_depth_picture`) to test whether the form generalizes.
