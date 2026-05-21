# Issue 21A: Visual Clash Candidate Accounting

**Date:** 2026-05-21 KST
**Status:** completed
**Type:** critique lint hardening
**Depends on:** Issue 20 visual clash evidence integration

## Problem

Issue 20 made `check_visual_clash.py` WARN candidates machine-readable and
visible in `/fig_critique`, but a host critique can still silently ignore one
or more candidates. That recreates the original failure mode: the evidence is
available, but the loop does not prove that the critic accounted for it.

## Goal

Make every visual-clash candidate auditable in `critique.md`.

For schema v1.7 critiques, if `examples/<name>/build/visual_clash.json`
contains candidates, each candidate must be referenced by a `micro_defects`
item through `visual_clash_ref`. The item may be an open defect or
`accept_simplification`, but it must be explicit.

## Scope

- Add stable visual-clash candidate ids, e.g. `VC001`.
- Teach the critique brief to show those ids.
- Extend the critique output schema to include `micro_defects[].visual_clash_ref`.
- Bump critique schema/rubric to v1.7.
- Teach `critique_lint.py` to reject v1.7 critiques that leave candidates
  unaccounted.

## Non-Goals

- No auto-classification of visual-clash candidates into final micro-defect kind.
- No hard failure for legacy v1.6 critiques.
- No source `.tex` edits.
- No attempt to reduce existing visual-clash counts.

## Acceptance Criteria

- [x] `check_visual_clash.py --json-output` writes candidate ids.
- [x] `/fig_critique` brief includes candidate ids and the `visual_clash_ref` field.
- [x] `critique_lint.py` rejects a v1.7 critique when a visual-clash candidate is
  not referenced by any `micro_defects` item.
- [x] `critique_lint.py` accepts a v1.7 critique when all candidates are referenced,
  including candidates explicitly marked `accept_simplification`.
- [x] Duplicate `micro_defects[].visual_clash_ref` entries are rejected so each
  candidate has one explicit accounting decision.
- [x] Unknown `micro_defects[].visual_clash_ref` entries are rejected so typo ids
  cannot satisfy accounting.
- [x] Existing v1.6 critiques remain legacy-compatible.
