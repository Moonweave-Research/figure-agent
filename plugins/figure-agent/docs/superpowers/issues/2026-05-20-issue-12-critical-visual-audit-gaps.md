# Issue 12: Critical Visual Audit Gaps From Real Dogfood

**Date:** 2026-05-20 KST
**Status:** open
**Type:** parent issue / implementation backlog

## Problem

Real figure dogfood on `fig1_overview_v2_pair_001_vault` exposed a gap between
the plugin's current audit contract and the defects that decide whether a
figure is actually publication-ready. The v1.3 critique contract now asks for
journal-grade axes, top-tier audit slots, and numeric advisory scoring, but the
vision input is still too coarse for micro-defects such as line-through-label,
arrow-tip fusion, floating semantic arrows, source-order layering mistakes, and
print-scale readability failures.

This means a loop can look contract-complete while the user still has to catch
critical defects from screenshots. That is the wrong boundary for a figure
agent.

## Evidence From Dogfood

| Area | Observed defect | Current repo truth |
|---|---|---|
| Host vision zoom | Standard full-render and panel-crop reads missed sub-mm line crossings and arrow artifacts. | `/fig_critique` reads `build/<name>.png` and optional panel crops, but no high-zoom sub-region crop pack exists. |
| Visual clash | `check_visual_clash.py` produced many report-only candidates while missing actual line-through-label cases. | The detector is text-bbox plus local pixel statistics; it is not a semantic micro-defect detector. |
| Drawing order | Adding a white fill did not help when later `\draw` paths rendered over the label. | No source-order lint exists for label-background protection. |
| Arrow-tip print behavior | Short `<->` arrow segments fused into diamond-like marks at print scale. | No print-scale arrow-tip recognizability gate exists. |
| Semantic anchoring | Vibration arrows could float away from the oscillating element. | Existing quality axes ask for label/arrow semantics, but no sub-region crop or closed-set micro-defect enum forces this check. |
| Hash/sync overhead | Generator/rubric/input/adjudication hashes require repeated manual refresh during active plugin development. | Freshness is correct but ergonomically expensive; no one-shot sync command exists. |
| Iteration logging | Sub-region loop progress was easy to omit or name inconsistently. | `subregion_iteration_log.md` is parsed when present, but no closeout helper appends or normalizes iteration rows. |

## Current Architecture Boundary

The current plugin has:

- v1.3 critique prompt/schema/rubric surfaces.
- `/fig_loop` ingestion of quality axes and top-tier summary.
- `subregion_iteration_log.md` active-target parsing.
- panel-level reference crop generation when `panels[].reference_image` and
  `panels[].bbox_pdf_cm` are both declared.

The current plugin does not have:

- automatic high-zoom crop generation;
- sub-region image crops as first-class critique inputs;
- micro-defect categories below panel/top-level findings;
- drawing-order or arrow-tip lint;
- print-scale audit images;
- one-shot critique/adjudication metadata sync;
- conflict mediation for concurrent Codex/Claude edits.

## Issue Breakdown

### Issue 12A: High-Zoom Subregion Audit Pack

**Type:** AFK
**Blocked by:** None

Create a deterministic crop pack for `/fig_critique` that generates high-zoom
2x2 quadrant crops for the full render and for every panel crop already produced
by `critique_brief.py`. The brief must list these crops and instruct the host
LLM to inspect them for micro-defects before declaring a critique ready.

Acceptance criteria:

- [ ] A new script/helper creates deterministic high-zoom crop files under
  `examples/<name>/build/audit_crops/`.
- [ ] `/fig_critique` brief lists the crop paths in a dedicated section.
- [ ] The section contains closed-set checks for line-through-label,
  arrow-tip-fusion, floating-arrow, label-target-detachment, and source-order
  suspicion.
- [ ] Existing fixtures without panel references still receive full-render
  quadrant crops.
- [ ] No source, export, accepted, golden, or critique files are mutated.
- [ ] Tests prove crop file creation, brief inclusion, and backwards-compatible
  behavior.

### Issue 12B: Micro-Defect Schema v1.4

**Type:** AFK
**Blocked by:** Issue 12A

Advance the critique schema so micro-defects have an explicit home instead of
being squeezed into broad categories such as `label_placement` or `style`.

Acceptance criteria:

- [ ] Brief output advances to `figure-agent.critique.v1.4` only after 12A
  produces stable crop inputs.
- [ ] `micro_defects` contains closed-set defect kinds:
  `line_crosses_label`, `wire_crosses_label`, `arrow_tip_fused`,
  `label_target_detached`, `floating_semantic_cue`, `drawing_order_suspect`,
  `print_scale_unreadable`.
- [ ] Validator rejects missing or malformed v1.4 micro-defect blocks.
- [ ] Any open `BLOCKER` or `MAJOR` micro-defect must link to a normal finding
  or explicit `accept_simplification`.
- [ ] v1.3 critiques remain scaffoldable as legacy.

### Issue 12C: Drawing-Order and Arrow-Tip Lints

**Type:** AFK
**Blocked by:** None

Add report-only static checks that catch two dogfood classes before the host
vision pass: protected labels drawn before later paths, and short double-headed
arrow segments whose tips can fuse at print scale.

Acceptance criteria:

- [ ] A lint detects suspicious `fill=white` or `fill=<color>` label/node lines
  followed by nearby drawing commands in the same local block.
- [ ] A lint detects short `<->`, `Stealth-Stealth`, or equivalent
  double-headed arrow segments below a conservative length threshold when the
  line has visible arrow tips.
- [ ] Lints are report-only by default and can be surfaced in `/fig_compile`
  output without blocking existing fixtures.
- [ ] Tests include true-positive and false-positive examples.

### Issue 12D: Critique Metadata Sync Helper

**Type:** AFK
**Blocked by:** None

Reduce manual hash churn without weakening freshness semantics.

Acceptance criteria:

- [ ] A one-shot command refreshes `critique_adjudication.yaml` from the current
  `critique.md` hash.
- [ ] The command refuses to mark a stale `critique.md` fresh when
  `critique_input_hash`, `generator_version`, or `rubric_version` mismatch.
- [ ] The command prints the exact reason when a host re-critique is required.
- [ ] No command silently edits `critique.md` content or invents host-vision
  judgments.

### Issue 12E: Print-Scale Audit Pack

**Type:** AFK
**Blocked by:** Issue 12A

Generate reduced-width audit images so labels, arrow tips, and dense sub-regions
are assessed at manuscript scale rather than only at screen scale.

Acceptance criteria:

- [ ] Render-derived audit images include at least 178 mm equivalent and one
  conservative thumbnail scale.
- [ ] The brief requires the host LLM to inspect print-scale crops before
  setting `journal_polish` or `publication_readiness` to `pass`.
- [ ] Report-only metadata records the audit image paths and scale labels.
- [ ] No export or accepted artifact is mutated.

## Priority

1. Issue 12A first. It addresses the largest observed failure mode and gives
   later schema/lint work real image evidence.
2. Issue 12C second if E14/E15-style failures keep recurring during TikZ work.
3. Issue 12B after 12A produces stable crop inputs.
4. Issue 12D can run in parallel with 12A when workflow friction becomes the
   bottleneck.
5. Issue 12E after high-zoom crop plumbing exists.

## Out of Scope

- Hidden auto-editing.
- Replacing host-LLM critique with an external paid vision API.
- Automatic accepted/golden/export mutation.
- SVG polish implementation.
- Declaring a figure publication-ready from deterministic checks alone.

