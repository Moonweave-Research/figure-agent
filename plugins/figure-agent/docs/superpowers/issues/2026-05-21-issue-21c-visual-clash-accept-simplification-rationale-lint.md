# Issue 21C: Visual Clash Accept-Simplification Rationale Lint

**Date:** 2026-05-21 KST
**Status:** implemented
**Type:** critique lint hardening
**Depends on:** Issue 21A visual clash candidate accounting; Issue 21B historical regression dogfood

## Problem

Issue 21A made every `build/visual_clash.json` candidate visible and required
one-to-one `VC### -> micro_defects[].visual_clash_ref` accounting for schema
v1.7 critiques. Issue 21B proved the host critique can catch the historical
`HV+` backdrop overflow and `$V_s$` same-box glyph/internal-drawing interaction.

The remaining loophole is weaker: a critique can still account for every
candidate while marking real or ambiguous warnings as `status:
accept_simplification` with a vague observation such as "acceptable after
review". That preserves accounting but weakens audit value.

## Goal

For schema v1.7 critiques, require visual-clash-linked
`accept_simplification` micro-defects to include a concrete observation that
names the `VC###` candidate and explains why the candidate is not a defect.

## Hard Scope

- Do not change the v1.7 schema string.
- Do not alter the one-to-one candidate accounting rule from Issue 21A.
- Do not promote visual clash WARN candidates to compile blockers.
- Do not add an automated vision classifier.
- Keep legacy v1.6 and older critiques compatible.

## Implemented Contract

When `schema: figure-agent.critique.v1.7` and `build/visual_clash.json` exists:

- each candidate must still be accounted exactly once via
  `micro_defects[].visual_clash_ref`;
- if a linked micro-defect uses `status: accept_simplification`, its
  `observation` must:
  - name the candidate id, e.g. `VC026`;
  - be long enough to carry a concrete reason;
  - include a non-defect rationale marker such as `false positive`,
    `intentional`, `not`, `separate`, `outside`, `axis`, `legend`,
    `background`, `decorative`, or `convention`.

This is intentionally a lint guardrail, not semantic proof. Its job is to
reject empty or hand-wavy acceptances and force the host critique to leave
reviewable evidence.

## Acceptance Criteria

- [x] `critique_lint.py` rejects a visual-clash-linked
  `accept_simplification` with a vague observation.
- [x] `critique_lint.py` accepts a visual-clash-linked
  `accept_simplification` with concrete candidate-specific rationale.
- [x] `/fig_critique` brief tells the host LLM not to use vague
  `accept_simplification` prose for visual clash candidates.
- [x] Existing v1.7 visual clash accounting behavior remains intact.

## Verification

- `uv run pytest -q tests/test_critique_lint.py -k visual_clash`
- `uv run pytest -q tests/test_critique_brief.py -k v1_7_editorial`

## Follow-Up Boundary

If this heuristic proves too loose, the next slice should introduce a structured
`accept_simplification_reason` field in a future schema version instead of
expanding natural-language keyword checks.
