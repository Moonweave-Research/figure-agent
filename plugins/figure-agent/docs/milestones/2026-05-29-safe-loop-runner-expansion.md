# Safe Loop Runner Expansion

Date: 2026-05-29

## Summary

Issue 67 expands `/fig_run --execute` from compile-only automation to compile
plus verify-only loop checkpoints. `/fig_drive` remains the selector; `/fig_run`
executes an allowlisted action only when the driver reports `stop_boundary:
null`.

This reduces another repetitive manual step without automating host critique,
adjudication, export, patching, SVG polish, accepted state, or golden
roll-forward.

## Behavior

- `run_compile` remains executable when it has no stop boundary.
- `run_fig_loop` is executable when it has no stop boundary.
- `run_fig_loop` with a boundary such as `mode_forbidden_action` is not
  executed.
- `run_adjudicate` and `run_export` remain non-executable.
- Any failed compile or loop command stops with `command_failed`.
- Successful loop execution triggers a driver re-query.

## Review Notes

1. Contract/schema review: clean after adding the `stop_boundary: null`
   execution precondition.
2. Scope containment review: clean. The only newly executable action writes
   verify-only `.scratch/fig-loop-runs/` evidence.
3. Test/integration review: clean. New tests cover loop execution, loop failure,
   and boundary-protected loop non-execution.

## Verification

- `uv run pytest -q tests/test_fig_run.py` — 12 passed
- `uv run pytest -q tests/test_fig_run.py tests/test_fig_driver.py` — 79 passed
- `uv run ruff check scripts/fig_run.py tests/test_fig_run.py` — passed
- `git diff --check` — passed

No known Issue 67 plugin blocker remains.
