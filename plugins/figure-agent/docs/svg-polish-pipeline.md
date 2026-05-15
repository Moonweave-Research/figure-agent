# SVG Polish Pipeline (TikZ Skeleton → SVG Mastering) — Issue / Pre-Spec

**Status:** ISSUE (pre-design). No implementation committed.
**Filed:** 2026-05-15
**Drives from:** `session_learnings_2026_05_04_eod_l3_ceiling.md` (Gap 2 = next big lever), `session_strategic_direction_2026_05_04.md` (Gap 2 deferred — timing now under review).
**Sibling issue:** `subregion-iteration-tool.md` (must precede; supplies prerequisite data).
**Predecessor evidence:** `session_handoff_2026_05_08_python_svg_close.md`, `feedback_python_svg_ceiling.md` — Python+SVG-from-scratch already falsified; this issue is *not* that direction.

---

## 1. Problem

TikZ delivers ~90% of paper-grade quality deterministically. The remaining 5–10% — label de-collision, optical alignment, panel-rhythm whitespace, edge breathing room — is what separates "compiled" from "Nature-quality". Memory `session_learnings_2026_05_04_eod_l3_ceiling.md`: TikZ/pgfplots auto-avoidance gap proved at golden figure with label-on-line collisions at 3 sites. L3 snippet ceiling reached.

Author currently bridges this gap manually in Inkscape per figure. Repeated, non-reproducible, lost on every spec change.

## 2. Why this matters

`figure-agent`'s core identity (`plugins/figure-agent/CLAUDE.md`) is **reproducibility**: `.tex` source → identical PDF. A naïve "open in Inkscape, save SVG" loop violates that contract — once author hand-nudges, TikZ source ceases to be authoritative.

Two paths exist (settled in conversation 2026-05-15):

- **Path A — SVG becomes authoritative.** One-shot Inkscape pass per figure, save polished SVG, ship that. Fast. **Cost: reproducibility surrendered.** Any spec revision restarts the manual polish. This is a regression of v0.2's whole point.
- **Path B — Polish-as-layer.** TikZ produces vector. Polish operations are declared (e.g., "nudge `label_E_t` by `[+2pt, -1pt]`") in a sidecar artifact and re-applied at every build. Reproducibility preserved. **Cost: polish DSL must be invented + maintained, and replay must survive TikZ re-compile.**

Path B aligns with kernel identity. Path A does not. Path B's feasibility is the open question.

## 3. Sketch (not committed)

Candidate shape for Path B, listed as anchor for discussion. Do not read as design.

1. TikZ → SVG export already exists (`/fig_export svg`).
2. New artifact `polish.yaml` per figure: list of operations (`element_id`, `op_type`, `params`).
3. Build hook: SVG → apply `polish.yaml` ops → polished SVG. Re-applied on every build.
4. Author tool: capture an Inkscape session as `polish.yaml` ops (instead of saving the polished SVG directly).

**Critical unknown.** Which polish-operation set is simultaneously:
- (a) **common** across figures (worth abstracting),
- (b) **deterministically replayable** on a re-built SVG (element IDs and coordinates must be stable across re-compile), and
- (c) **expressible** without re-inventing Inkscape.

Without (a)+(b)+(c), Path B collapses into "ad-hoc per-figure scripts" — worse than Path A.

## 4. Open questions

- Are SVG element IDs stable across TikZ re-compiles? (If element coordinates shift even one pixel between builds, `polish.yaml`'s positional ops re-apply to the wrong target.)
- Is the polish operation set small (10–20 ops covering ≥80% of cases), or does it grow unbounded?
- Does scripted Inkscape (CLI) cover the needed operations, or do they require GUI semantics?
- What is the minimum prototype that validates Path B feasibility? Suggested: **one operation** ("nudge label") applied to **one golden fixture**, surviving **three rebuild cycles** with bit-stable polished output.
- Is "polish capture" feasible — i.e., can an Inkscape session export an op-list rather than a flattened SVG?

## 5. Non-goals

- ❌ Auto-generating polish operations from LLM critique. Re-enters falsified family (`project_v0_3_figure_quality_spec_rejected.md`, `feedback_perception_spec_rejected.md`).
- ❌ Replacing TikZ as primary author surface.
- ❌ General-purpose Inkscape automation. Scope is bounded to operations that close the 5–10% paper-grade gap.
- ❌ Path A (one-shot polish, no replay). Identified and consciously rejected for reproducibility violation.

## 6. Dependencies / prerequisites

- **Sub-region iteration tool data** (`subregion-iteration-tool.md`). Sub-region dogfood will surface *which specific operations* TikZ cannot reach. Without that empirical list, polish-DSL design is speculation — and speculation was the failure mode of v0.3/v0.4 specs.
- v0.5 per-panel reference workflow stable (✓).

## 7. Decision gate

Do **not** enter design until:

1. Sub-region tool produces ≥ 1 working dogfood with iteration log on a real figure.
2. Iteration log surfaces a concrete "TikZ cannot do X" pattern with ≥ 3 occurrences across distinct figures or panels.
3. SVG element-ID stability across re-compile is verified (independent check, single golden fixture, three rebuild cycles).

Path A vs Path B is **decision-deferred** until (1)–(3) are met. Even after that, only enter Path B if (3) passes; if SVG IDs are unstable, Path B is infeasible regardless of other arguments.
