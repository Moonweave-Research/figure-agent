# Issue 22: Post-Closeout Critical Contract Hardening

**Date:** 2026-05-21 KST
**Status:** implemented through Issue 22E
**Type:** critical review follow-up

## Problem

The three-agent post-closeout review found that the latest critique producer
contract was stronger than several consumers and gates:

- `/fig_loop` consumed critique schemas only through v1.5 while `/fig_critique`
  now emits v1.7.
- `/fig_export` checked critique freshness but not critique lint/schema
  validity.
- `build/visual_clash.json` was a mandatory critique input but was not included
  in the critique freshness hash.
- print-scale evidence lint applied only to v1.4/v1.5 even though v1.7 still
  requires journal-polish and publication-readiness evidence.
- release readiness needed a separate binding so unresolved loop checkpoint
  blockers could not be bypassed by accepted/golden/export-ready state.

## Issue 22A: v1.7 Loop Consumer Wiring

**Status:** implemented

`fig_loop_assessments.py` now treats v1.6/v1.7 as schemas with quality axes,
top-tier audit, editorial art direction, and journal-grade assessment surfaces.

Acceptance:

- [x] v1.7 `journal_grade_assessment` is consumed.
- [x] v1.7 `top_tier_audit` is consumed.
- [x] v1.7 `editorial_art_direction` is consumed.

## Issue 22B: Export Critique Validity Gate

**Status:** implemented

`/fig_export` now runs `critique_lint.py` before regeneration when critique is
required and `--skip-critique` is not set. A hash-fresh but malformed
`critique.md` no longer passes export by freshness alone.

Acceptance:

- [x] malformed hash-fresh v1.7 critique blocks `/fig_export`.
- [x] existing `--skip-critique` stale-critique override remains explicit.
- [x] missing reference inputs still cannot be bypassed by `--skip-critique`.

## Issue 22C: Visual Clash Freshness Input

**Status:** implemented

`build/visual_clash.json` is now part of the critique input manifest when it
exists. Changing the visual-clash candidate set makes a hash-fresh critique
stale.

Acceptance:

- [x] critique state is `FRESH` when the stored hash matches the current visual
  clash report.
- [x] critique state becomes `STALE` when `build/visual_clash.json` changes.

## Issue 22D: v1.7 Print-Scale Evidence Lint

**Status:** implemented

Print-scale evidence lint now applies to v1.6/v1.7 in addition to v1.4/v1.5.

Acceptance:

- [x] v1.7 critiques with `journal_polish: pass` and generic evidence are
  rejected.
- [x] v1.7 critiques with `publication_readiness: pass` and generic evidence
  are rejected.

## Issue 22E: Release Gate Binding

**Status:** implemented

Release mode now loads the latest current `/fig_loop` checkpoint and applies
the same loop-blocker interpretation used by review/polish before declaring a
release loop complete. A release-ready fixture is still stopped when the latest
checkpoint requires human review, top-tier/editorial art-direction resolution,
ambiguous patch selection, or a single patch handoff.

Acceptance:

- [x] release mode stops on a latest human-gated loop checkpoint even when
  `release_ready` is already true.
- [x] release mode stops on a latest patch-handoff loop checkpoint even when
  `release_ready` is already true.
- [x] release mode requires fresh adjudication before completion when
  `critique_state` is `FRESH`.
- [x] release mode still completes when the latest checkpoint is clean and
  includes that checkpoint in the JSON evidence.
- [x] export freshness remains the first release prerequisite; missing/stale
  exports still route to `/fig_export` before release blockers are evaluated.

Non-goals for Issue 22:

- Do not change accepted/golden semantics.
- Do not make `--skip-critique` disappear.
- Do not add hidden auto-patching.
- Do not redesign release readiness inside the v1.7 consumer/freshness patch.
