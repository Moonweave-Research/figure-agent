# Issue 15D: Orchestration Boundary Refactor

**Date:** 2026-05-21 KST
**Status:** completed as no-code boundary review
**Parent:** Issue 15
**Blocked by:** Issue 15A

## Problem

`fig_driver.py` and `status.py` already own large state-machine surfaces. They
are tested, but adding closeout and auto-patch policy directly into those files
would make the orchestration layer harder to reason about.

## What to Build

Keep future loop automation modular. New closeout selection, patch execution
eligibility, and audit-completeness policy should live in focused helper
modules with narrow public functions. `fig_driver.py` should remain the CLI and
controller; `status.py` should remain the canonical state reader.

## Acceptance Criteria

- [x] Issue 15A additions do not turn `fig_driver.py` into the owner of
  closeout policy internals.
- [x] Issue 15C additions do not put patch mutation logic in `fig_loop.py` or
  `status.py`.
- [x] New helpers have direct unit tests.
- [x] Existing public JSON contracts remain backward compatible.
- [x] No broad behavior-preserving refactor lands without a feature slice that
  needs the boundary.

## Boundary Review Result

No additional refactor is needed after Issues 15A and 15C.

- Issue 15A closeout routing lives in `scripts/fig_driver_closeout.py`; the
  driver remains the controller that maps a compact closeout recommendation to
  an action.
- Issue 15C mutation policy lives in `scripts/fig_loop_patch_executor.py`;
  `/fig_loop` remains verify-only, and `status.py` remains the canonical state
  reader.
- Direct tests cover both helpers:
  `tests/test_fig_driver.py` for closeout-driven driver decisions and
  `tests/test_fig_loop_patch_executor.py` for executor safety/refusal paths.
- The public driver and loop contracts remain additive: existing fields keep
  their meaning, while closeout and patch-apply evidence are opt-in/additive.

Given those boundaries, a behavior-preserving extraction would add risk without
removing current coupling. Revisit this issue only if future work starts adding
more policy branches directly to `fig_driver.py`, `fig_loop.py`, or `status.py`.

## Verification

```bash
uv run pytest -q tests/test_fig_driver.py tests/test_status.py tests/test_fig_loop.py
uv run pytest -q
uv run ruff check .
git diff --check
```
