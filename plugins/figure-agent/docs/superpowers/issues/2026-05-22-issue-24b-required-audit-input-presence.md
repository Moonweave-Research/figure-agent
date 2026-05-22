# Issue 24B: Required Audit Input Presence

**Date:** 2026-05-22 KST
**Status:** implemented in branch
**Type:** audit-input contract hardening
**Parent:** `2026-05-22-issue-24-audit-gate-hardening-roadmap.md`

## What to build

For critique schemas that require visual-clash accounting, make a missing
`build/visual_clash.json` a controlled lint blocker instead of treating it like
there are zero candidates to account for.

## Current Problem

`critique_lint.py` validates `micro_defects[].visual_clash_ref` against
`build/visual_clash.json` for v1.7+ critique schemas. Before this issue, if the
JSON report was missing, `_visual_clash_candidate_ids()` returned an empty
candidate list and no violation. The accounting check then exited early, which
allowed the critique to pass without proving that the visual-clash detector ran.

Crop audit accounting already has the stricter behavior for v1.8+:
`build/audit_crops/manifest.json` missing is a blocker. Visual-clash accounting
should follow the same pattern.

## Acceptance Criteria

- [x] v1.7, v1.8, and v1.9 critiques fail lint when
  `build/visual_clash.json` is missing.
- [x] The failure category remains `visual_clash_accounting`.
- [x] The failure message names `missing build/visual_clash.json`.
- [x] Existing malformed-report and invalid-candidate checks continue to work.
- [x] v1.6 and older critiques remain legacy-compatible and do not require the
  visual-clash report.
- [x] A present report with an empty `candidates: []` remains valid and means
  there were no visual-clash candidates to account for.

## Implementation Notes

- `_visual_clash_candidate_ids()` now returns a blocker violation when the
  report is missing.
- Existing v1.8/v1.9 crop-accounting tests now write an explicit empty
  `visual_clash.json` when the test is not about visual-clash accounting.
- v1.6 legacy tests still pass without the report.

## Implementation Contract

Change `_visual_clash_candidate_ids(report_path)` in `scripts/critique_lint.py`
so a missing file returns one blocker violation:

```text
BLOCKER: visual_clash_accounting: missing build/visual_clash.json for visual_clash_ref validation
```

Do not change the public schema version. This is enforcement of an existing
v1.7+ accounting contract, not a new critique output shape.

Do not require `visual_clash.json` for v1.6 or older critiques, because those
schemas did not carry first-class visual-clash accounting.

## Suggested Files

- `scripts/critique_lint.py`
- `tests/test_critique_lint.py`
- `docs/superpowers/issues/2026-05-22-issue-24-audit-gate-hardening-roadmap.md`
- `docs/superpowers/issues/2026-05-22-issue-24b-required-audit-input-presence.md`

## TDD Plan

1. Add a failing v1.7 test with no `build/visual_clash.json`.
2. Assert lint returns one `visual_clash_accounting` violation that names the
   missing report.
3. Add a v1.6 legacy test with no report and confirm it still passes.
4. Add a v1.7 empty-report test and confirm it passes when `candidates: []`.
5. Implement the missing-file violation in `_visual_clash_candidate_ids()`.
6. Run focused lint tests and the broader critique lint suite.

## Verification

```bash
uv run pytest -q tests/test_critique_lint.py
uv run ruff check scripts/critique_lint.py tests/test_critique_lint.py
git diff --check
```

## Non-Goals

- No status or driver behavior changes in this slice.
- No crop content hashing; that is Issue 24C.
- No change to `compile.sh` or `check_visual_clash.py`.
- No migration of existing critique files.
