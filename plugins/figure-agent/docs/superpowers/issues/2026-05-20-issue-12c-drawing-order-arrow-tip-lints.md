# Issue 12C: Drawing-Order and Arrow-Tip Lints

**Date:** 2026-05-20 KST
**Status:** open
**Type:** AFK report-only lint slice
**Parent:** `2026-05-20-issue-12-critical-visual-audit-gaps.md`

## What To Build

Add deterministic report-only lints for two dogfood failure modes:

1. label/background fills that do not protect text because later draw commands
   render over them;
2. short double-headed arrow segments whose arrow tips can visually fuse at
   manuscript scale.

## Acceptance Criteria

- [ ] A source-order lint reports suspicious filled label/node lines followed
  by local drawing commands that may overpaint the protected label.
- [ ] A short-arrow lint reports double-headed arrow segments below a
  conservative threshold.
- [ ] Both lints are report-only by default.
- [ ] `/fig_compile` may surface the warnings, but existing fixtures are not
  blocked in this slice.
- [ ] Tests include true positives and false positives.
- [ ] The lint output includes file path, line number, lint code, and one-line
  remediation guidance.

## Blocked By

None - can start immediately.

