# Issue 12C: Drawing-Order and Arrow-Tip Lints

**Date:** 2026-05-20 KST
**Status:** completed in commit `f551bc3`
**Type:** AFK report-only lint slice
**Parent:** `2026-05-20-issue-12-critical-visual-audit-gaps.md`

## What To Build

Add deterministic report-only lints for two dogfood failure modes:

1. label/background fills that do not protect text because later draw commands
   render over them;
2. short double-headed arrow segments whose arrow tips can visually fuse at
   manuscript scale.

## Acceptance Criteria

- [x] A source-order lint reports suspicious filled label/node lines followed
  by local drawing commands that may overpaint the protected label.
- [x] A short-arrow lint reports double-headed arrow segments below a
  conservative threshold.
- [x] Both lints are report-only by default.
- [x] `/fig_compile` may surface the warnings, but existing fixtures are not
  blocked in this slice.
- [x] Tests include true positives and false positives.
- [x] The lint output includes file path, line number, lint code, and one-line
  remediation guidance.

## Implementation Notes

- Implemented as WARN-tier `lint_tex.py` checks so `/fig_compile` surfaces the
  warnings without changing compile exit behavior.
- `label_fill_source_order` warns when a filled non-empty node is followed by a
  local draw/path command within a conservative lookahead window.
- `short_double_arrow` warns when a straight `<->`, `<=>`, `Stealth-Stealth`,
  or `Latex-Latex` segment is shorter than the conservative threshold.

## Blocked By

None - can start immediately.
