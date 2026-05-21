# Issue 20: Visual Clash Evidence Integration

**Date:** 2026-05-21 KST
**Status:** completed on main through Issues 20A-D and follow-up Issues 21A-C
**Type:** QA evidence pipeline hardening
**Spec:** `../specs/2026-05-21-visual-clash-evidence-integration-design.md`

## Problem

Dogfood on `fig1_overview_v2_pair_001_vault` showed that small
intra-instrument label defects can survive many authoring loops even when
`check_visual_clash.py` emits relevant WARN candidates. The pipeline treated
those candidates as compile-log noise instead of structured critique input.

This issue fixes the evidence plumbing: visual clash candidates must become
machine-readable, high-zoom crops must be fine enough for small instrument
boxes, and critique schema vocabulary must name the observed defect classes.

## Issue Breakdown

### Issue 20A: Micro-Defect Kind Extension

**Status:** implemented

Add critique schema v1.6 and extend `micro_defects[].kind` with:

- `label_backdrop_overflows_outline`;
- `label_glyph_overlaps_internal_drawing`.

Acceptance criteria:

- [x] Schema vocabulary exposes v1.6 and both new kinds.
- [x] Validator accepts the new kinds under v1.6.
- [x] Validator/lint still rejects unknown kinds.
- [x] `BLOCKER`/`MAJOR` new-kind micro-defects require a linked finding or
  `accept_simplification`.
- [x] `/fig_critique` command and brief rubric describe concrete examples.

### Issue 20B: Instrument/Sub-Quadrant Audit Crops

**Status:** implemented

Add a second high-zoom crop layer:

- `panels[].instruments[]` -> deterministic instrument crops;
- no instruments -> 4x4 panel sub-quadrant fallback.

Acceptance criteria:

- [x] Crop pack preserves existing full-render quadrants and print-scale images.
- [x] Instrument crop paths are deterministic and fixture-relative.
- [x] 4x4 fallback paths are deterministic.
- [x] Brief lists the new crops in High-Zoom Visual Audit Crops.

### Issue 20C: Visual Clash JSON + Brief Ingestion

**Status:** implemented

Serialize `check_visual_clash.py` candidates into
`build/visual_clash.json` and require `/fig_critique` to account for them.

Acceptance criteria:

- [x] `check_visual_clash.py --json-output <path>` writes the documented JSON.
- [x] `compile.sh` writes `build/visual_clash.json` on every successful
  visual-clash check.
- [x] `critique_brief.py` emits
  `## Visual Clash Candidates (from check_visual_clash.py)` when JSON exists.
- [x] Candidate ordering is deterministic.

### Issue 20D: Visual Clash Budget Guardrail

**Status:** implemented

Add CI-facing enforcement for `spec.yaml.visual_clash_cap`, defaulting to 0.

Acceptance criteria:

- [x] Budget checker reads `build/visual_clash.json`.
- [x] Missing `visual_clash_cap` defaults to 0.
- [x] Cap exceedance fails with a controlled message.
- [x] Local authoring remains report-only unless strict/budget mode is invoked.

## Non-Goals

- No source edits to `fig1_overview_v2_pair_001_vault`.
- No hidden auto-patching.
- No external vision API.
- No heuristic instrument detection in this slice.
- No removal or rename of existing micro-defect kinds.
