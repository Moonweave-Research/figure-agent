# Issue 21B: Historical Visual Clash Regression Dogfood

**Date:** 2026-05-21 KST
**Status:** preflight captured; host-vision dogfood pending
**Type:** dogfood evidence / regression protocol
**Depends on:** Issue 20 visual clash evidence integration; Issue 21A visual clash candidate accounting

## Problem

Issue 20 made visual-clash WARNs visible to `/fig_critique`, and Issue 21A
made schema v1.7 critiques account for each `VC###` candidate exactly once.
That still proves only *accounting*, not that the host critique classifies the
historical failure mode correctly.

The motivating dogfood failure was specific:

- an `HV+` label backdrop protruded outside its enclosing instrument box;
- a `$V_s$ meter` label/glyph interacted with same-box internal drawing;
- `check_visual_clash.py` emitted relevant WARN candidates, but the compile
  footer made them look like low-priority noise;
- panel-level and quadrant crops were too coarse for the human/host loop to
  reliably catch the defect.

## Goal

Create a reproducible dogfood protocol that proves the v1.7 critique loop can
surface those historical intra-instrument label failures when they are present,
without mutating the canonical figure source or accepted/golden state.

## Hard Scope

- Use a disposable regression copy, snapshot, or generated temporary fixture.
- Do not edit `examples/fig1_overview_v2_pair_001_vault/*.tex` in-place.
- Do not change accepted/golden/export state.
- Do not invent an automated vision classifier for label overflows.
- Do not require external vision APIs.

## Protocol

1. Prepare a temporary regression artifact.
   - Preferred: copy the target fixture to a scratch directory and apply a
     minimal source patch that recreates the historical label overflow geometry.
   - Acceptable: use a committed tiny synthetic fixture only if it preserves the
     same failure shape: label/backdrop inside an instrument box plus
     same-box internal drawing.
2. Run compile on the temporary artifact.
   - Confirm `build/visual_clash.json` exists.
   - Confirm relevant candidates have stable `VC###` ids.
   - Confirm the brief includes `## Visual Clash Candidates` and the relevant
     high-zoom crops.
3. Run `/fig_critique` with host vision against the temporary artifact.
   - The host must read the high-zoom crops and visual-clash candidate list.
   - The resulting `critique.md` must be schema v1.7 or newer.
4. Run `critique_lint.py`.
   - The critique must account for every visual-clash candidate exactly once.
   - Historical `HV+`-style overflow must be represented as
     `label_backdrop_overflows_outline`, unless explicitly justified as not
     present in the regressed artifact.
   - Historical same-box display/glyph collision must be represented as
     `label_glyph_overlaps_internal_drawing`, unless explicitly justified as
     not present in the regressed artifact.
5. Record the result in a milestone evidence document.

## Acceptance Criteria

- [x] A disposable regression artifact or protocol is documented with exact
  commands and no canonical source mutation.
- [x] The compile step produces `build/visual_clash.json` with relevant
  candidate ids.
- [x] The generated brief lists the candidate ids and high-zoom crops required
  for host review.
- [ ] A dogfood `/fig_critique` pass produces schema v1.7+ critique output.
- [ ] `critique_lint.py` passes only when all candidates are accounted.
- [ ] The historical overflow shape is either classified with the intended new
  micro-defect kind or explicitly justified as absent from the artifact.
- [ ] The evidence document states whether the plugin contract is sufficient or
  whether another code slice is needed.

## Review Questions

- Does the protocol test the original failure mode, or only a simplified toy?
- Are the candidate ids stable enough for the evidence claim being made?
- Does the host critique have enough crop/context resolution to classify the
  defect without user screenshots?
- Can a bad critique still pass by marking everything `accept_simplification`
  with weak rationale?
- If yes, should the next issue lint `accept_simplification` rationale quality
  for visual-clash-linked micro-defects?

## Expected Outcome

This issue is evidence-first. If the dogfood pass succeeds, no code change is
required. If it fails, the follow-up should be a narrow code slice, likely one
of:

- stronger `accept_simplification` rationale lint for visual-clash-linked
  micro-defects;
- richer visual-clash candidate context in the brief;
- deterministic temporary regression fixture support for CI/reporting.
