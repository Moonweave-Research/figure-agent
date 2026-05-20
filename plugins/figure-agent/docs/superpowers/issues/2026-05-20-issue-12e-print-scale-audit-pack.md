# Issue 12E: Print-Scale Audit Pack

**Date:** 2026-05-20 KST
**Status:** open
**Type:** AFK visual audit evidence
**Parent:** `2026-05-20-issue-12-critical-visual-audit-gaps.md`
**Blocked by:** Issue 12A

## What To Build

Generate reduced-scale audit images so the critique loop checks whether labels,
arrow tips, line weights, and dense sub-regions survive manuscript-scale
reading. This is evidence for `journal_polish`, `reduction_print_readability`,
and `publication_readiness`; it is not an export or acceptance mutation.

## Acceptance Criteria

- [ ] Audit images include a 178 mm equivalent render.
- [ ] Audit images include one conservative thumbnail-scale render.
- [ ] `/fig_critique` brief lists the images and requires inspection before
  setting `journal_polish` or `publication_readiness` to `pass`.
- [ ] The generated files live under `build/audit_crops/` or a similarly
  ephemeral build subdirectory.
- [ ] No export, accepted, golden, final-artifact, or source file is mutated.
- [ ] Tests prove deterministic file naming and brief inclusion.

## Blocked By

- Issue 12A, because the crop/audit-pack plumbing should be shared.

