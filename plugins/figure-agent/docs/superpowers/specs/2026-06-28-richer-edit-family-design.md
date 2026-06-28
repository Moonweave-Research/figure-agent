# Richer Edit Family for Tight Layouts (Slice 5 — proposer edit vocabulary)

Status: DESIGN (approved in brainstorm 2026-06-28; no code yet). Branch:
work/review-auto-fixes-2026-06-25 @ HEAD 84e40e5. Backs memory
`project_slice5_fig2_settles_clean_2026_06_25` and the canonical
`project_techstack_direction_2026_06_21` (tool = iteration-amplifier).

## Problem (dogfood-grounded, not assumed)

The anchored fix-mode (Inc1–4b) can move a label by a bounded coordinate offset,
but a **single coordinate offset is the proposer's ENTIRE edit vocabulary**. The
Slice-5 dogfood arc proved that is the real autonomy ceiling — not the verifier
(the geometric-verifier next-step was built, dogfooded, and reverted: its premise
was falsified and a geometric line-crossing FILTER weakens the verifier; see the
memory topic file).

fig2_trap_design_space finding **C001** is the canonical case a coordinate offset
cannot fix. Grounded from `fig2.tex`:

- x-axis: `\draw[axisArr] (6.10,3.90)--(17.25,3.90)` (horizontal at y=3.90).
- caption (lines 95-96): `\node[labelMute, anchor=north, text width=2.6cm,
  align=center] at (7.60,4.12) {PI, PDMS, PET (shallow, leaky)}` — anchor=north@4.12
  flows DOWN, wraps to 2 lines, crosses the axis at 3.90.
- blocked UP by the conventional-cluster box `(6.45,4.15) rectangle (8.75,5.45)`
  (bottom 4.15, only 0.03cm above the caption) + 3 canonNode dots.
- blocked DOWN by the panel-c title `\node[labelStrong, anchor=west] at (5.55,3.15)
  {Kinetic charge-trapping signature (schematic)}`. The axis(3.90)↔title(3.15) gap
  is **0.75cm — too tight for a 2-line caption.**

A pure reposition has no clean solution: moving down hits the title, moving up hits
the cluster. The defect needs a **shape** change, not just a position change.

## Feasibility VERIFIED on real fig2 (the fix the family must author)

Widen `text width=2.6cm → 5.6cm` (collapses the 2-line wrap to 1 line) **+**
reposition `y 4.12 → 3.84` (top below the axis, into the 0.75cm gap; a 1-line 7pt
caption is ~0.3cm tall → spans 3.84→3.54, clears the title 3.15 by 0.39cm).

Compiled both variants (engine = **lualatex**; fig2 preamble uses fontspec;
`TEXINPUTS=styles/`). Real `check_visual_clash`:

- orig: 10 candidates incl PI,/PDMS,/PET (the C001 crossing).
- widen+reposition: **7 candidates = orig MINUS exactly PI,/PDMS,/PET, with ZERO
  new crossing** (Origin/of/S–S/S85/S60/trap-distribution/I(t) are stable baseline
  false-positives, unchanged).

The caption text is **identical** → the value-preservation gate `labels_unchanged`
passes. The single-offset family could never author this (widen alone keeps top@4.12
→ 1 line down to ~3.82, still crosses 3.90). The fix is a **COMBINED text-width +
reposition refit** — exactly the edit this family adds.

## Scope boundary (autonomy vs escalation)

User delegated the boundary; chosen rule:

- **AUTONOMOUS = value-preserving footprint edits only.** An edit may change a
  label's rendered FOOTPRINT (text-width, position, later anchor/font-size) but must
  NOT change its rendered text. Every such edit rides the existing fail-loud verifier
  unchanged (it passes `labels_unchanged`).
- **ESCALATE = text-changing + structural edits.** Caption-shorten (e.g. dropping
  "(shallow, leaky)") changes meaning — an autonomous tool cannot verify semantic
  equivalence, and `candidate_apply._run_class_verifiers` HARD-iterates
  `CLASS_VERIFIERS["_default"]=("labels_unchanged","palette_locked")` for every edit
  (it ignores `_verifier_keys(edit_class)`), so any text change auto-rolls-back.
  Panel relayout is structural. Both fall through to the existing refusal /
  review_only path (no new escalation machinery — YAGNI).

Invariant: **every autonomous edit changes shape/position only and rides the
existing fail-loud verifier. The verifier is never weakened** (the opposite of the
reverted geometric filter).

## Design (Approach 1: eye-supplied refit, existing verifier)

### Components (each independently testable)

1. **Proposal vocabulary.** A critique finding may carry an optional structured
   `proposed_edit` (alongside the existing `proposed_offset`):
   ```yaml
   proposed_edit:
     edit_class: label_refit
     text_width_cm: 5.6                 # absolute target text-width
     reposition: {axis: y, dx_cm: -0.28}   # reuse the existing reposition
   ```
   The eye/host diagnoses the refit (widen-to-one-line + drop-below-axis), exactly as
   Inc2's `proposed_offset` carries the eye's diagnosed magnitude.

2. **Primitive** `bounded_text_width.set_text_width(line, *, target_cm) -> str | None`
   — replaces the node's `text width=Xcm` with a bounded new value; returns None when
   the line has no `text width` key or the change exceeds a delta cap
   `MAX_TEXT_WIDTH_DELTA_CM = 4.0` (stops an absurd whole-figure-width blow-up; the
   real safety is the verifier, mirroring MAX_REPOSITION_CM). Pure, TDD.

3. **Generator.** `candidate_generator._finding_offset(finding, line)` gains a
   `proposed_edit` branch BEFORE the `proposed_offset` branch: when `edit_class ==
   label_refit`, apply `set_text_width(line, target_cm=…)` then
   `reposition_coordinate(line, axis, dx_cm)` (independent substring edits on the
   same line) and return `(replacement, "label_refit", variant_id, dx_cm)`. The
   candidate rewrites the node line with BOTH attributes changed.

4. **Verifier — UNCHANGED.** A `label_refit` is value-preserving → `labels_unchanged`
   passes. If widening pushes the label onto a neighbor, the finding-recheck
   new-crossing arm (4a) flags `finding_new_crossing_introduced` and 4b auto-rolls
   back. No new verifier, no relaxation.

5. **Escalation — existing path.** When no value-preserving `proposed_edit` /
   `proposed_offset` can be formed, the generator's existing refusal (and the
   review_only authority floor) already serve as escalation. No new machinery.

### Data flow

critique finding (`proposed_edit`) → `_finding_offset` → `label_refit` candidate
(node line rewritten: text-width set + reposition) → `apply_candidate` →
`labels_unchanged` (text identical) + recompile + finding-recheck (target crossing
gone AND no new crossing) → SUCCESS, else auto-rollback.

## TDD increments

- **A — primitive.** `bounded_text_width.set_text_width`: sets the width, respects
  `MAX_TEXT_WIDTH_DELTA_CM`, returns None on missing key / over-cap. (RED→GREEN, pure.)
- **B — generator wiring.** A finding carrying `proposed_edit{label_refit}` emits a
  `label_refit` candidate whose replacement line has BOTH the new text-width and the
  repositioned coordinate, text unchanged. (RED→GREEN.)
- **C — fig2 C001 e2e dogfood.** Author C001's `proposed_edit` (5.6cm, y -0.28),
  build the candidate, drive the real apply path, confirm `labels_unchanged` passes
  and the finding-recheck reports SUCCESS (PI,/PDMS,/PET crossing cleared, 0 new
  crossing). Throwaway; do NOT commit a fig2 mutation.

## Approach 2 — geometry-derived refit (SHIPPED, TDD)

Removes the eye-supplied magnitudes: a finding carrying ONLY its `tex_lines` (no
`proposed_edit`/`proposed_offset`) gets a `label_refit` derived from the figure
itself. New module `scripts/label_refit_derive.py`:

- `parse_node` (coord + text-width) · `nearest_crossed_hline(node_x, node_y,
  tex_lines)` = the closest horizontal `\draw (..,Y)--(..,Y)` BELOW the node whose
  x-span contains it (within `MAX_CROSS_DISTANCE_CM`) · `count_lines`/`node_line_count`
  (wrap count from the rendered words, a height RATIO so pt-vs-px cancels) ·
  `derive_refit` → `{label_refit, text_width_cm = lines × current_width × WIDTH_MARGIN,
  reposition{y, dx = (Y − CLEAR_MARGIN_CM) − node_y}}`.
- `candidate_generator._finding_with_derived_edit` runs this as a FALLBACK in
  `_adjudicated_apply_candidates` when the finding has no eye diagnosis; it feeds the
  Inc B `_finding_refit` path. Words come from the build PDF (`_load_build_words`).

**Crossed-line source = tex-scan, NOT pixel detection (dogfood reversal).** First
tried detector-derived line location (max autonomy); 4 heuristics all mis-located
the axis (label sits ON the line → broken by glyphs where measured; same fragility
as the reverted geometric verifier), and px→tikz scale is underdetermined under
\resizebox. The line's tikz-y is EXACT in the figure's own `\draw`, so tex-scan is
both robust and still eye-free.

**Two dogfooded constants (fig2):** `WIDTH_MARGIN = 1.10` — `lines × current_width`
≈ the natural 1-line width, but AT that width the text wraps back on kerning (5.20cm
still wrapped); 10% headroom guarantees one line. `CLEAR_MARGIN_CM = 0.12` — 0.05cm
sits in the dark-ratio detector's noise band at the line (still flagged), 0.20cm
drifts toward the next element below (re-flags); 0.10–0.15cm clears robustly.

e2e (ZERO eye input) on real fig2 C001: derived `text width 5.72cm` + `y 4.12→3.78`
→ PI,/PDMS,/PET crossing cleared, 0 new crossing, `labels_unchanged` True,
finding-recheck `success`. TDD D1–D4. YAGNI: horizontal reference line +
label-crosses-from-above only; a too-far/too-wide derivation is caught by 4a/4b.

Next refinement: destination-aware margin (derive the gap to the next element below
instead of a fixed CLEAR_MARGIN) so the drop adapts per figure.

## Alternatives considered
- **Approach 3 — generic multi-attribute edit engine** (rewrite any node attribute:
  text-width/anchor/align/font-size/position from a flexible proposal). Over-built for
  the one defect class we have. Rejected (YAGNI). Add attributes when a real finding
  needs them.

## Out of scope

- Text-changing edits (caption-shorten) and structural relayout — ESCALATE.
- New verifiers or any verifier relaxation — none needed.
- Destination-aware margin (derive the gap to the next element below) — next refinement.
