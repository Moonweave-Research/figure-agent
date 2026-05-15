# Sub-Region Iteration Tool — Issue / Pre-Spec

**Status:** ISSUE (pre-design). No implementation committed.
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

Do **not** start design until v0.5 dogfood produces at least one concrete `fig1_overview_v2` panel with a real sub-region iteration log. Tool shape must come from observed iteration, not from this issue.
