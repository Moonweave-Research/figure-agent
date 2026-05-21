# Issue 15D: Orchestration Boundary Refactor

**Date:** 2026-05-21 KST
**Status:** proposed
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

- [ ] Issue 15A additions do not turn `fig_driver.py` into the owner of
  closeout policy internals.
- [ ] Issue 15C additions do not put patch mutation logic in `fig_loop.py` or
  `status.py`.
- [ ] New helpers have direct unit tests.
- [ ] Existing public JSON contracts remain backward compatible.
- [ ] No broad behavior-preserving refactor lands without a feature slice that
  needs the boundary.

## Verification

```bash
uv run pytest -q tests/test_fig_driver.py tests/test_status.py tests/test_fig_loop.py
uv run pytest -q
uv run ruff check .
git diff --check
```
