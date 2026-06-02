# Issue 100CU - Queue-Run Filter Surface Guard

Status: implemented

Type: operator workflow, queue runner, regression guard

## Problem

Issue 100CS copied the current SVG polish readiness filters from `/fig_queue`
into `/fig_queue_run`, but that fix was point-in-time. If `/fig_queue` gains
another filter later, `/fig_queue_run` could silently fall behind again while
the command documentation still says it accepts the same filters as `/fig_queue`.

## Impact

The queue runner is the plan-only/bounded execution wrapper after queue
inspection. Filter drift here forces operators back into manual JSON filtering
at the exact step where the workflow should become safer and more repeatable.

## Implementation

- Added `QUEUE_FILTER_KEYS` to `scripts/fig_queue_run.py`, tied to
  `fig_queue._FILTER_KEYS`.
- Added `_queue_filters_from_args()` so the CLI filter payload is assembled in
  one place.
- Added a defensive runtime check that fails if the queue-run filter payload is
  missing a queue filter key or contains an extra key.
- Added a regression test that compares `fig_queue_run.QUEUE_FILTER_KEYS`
  against `fig_queue._FILTER_KEYS`.

## Tests

`tests/test_fig_queue_run.py` now includes
`test_queue_run_filter_surface_matches_fig_queue`.

The test first failed because `fig_queue_run` had no declared filter-surface
constant, then passed after the guard was added.

## Review

1. **Contract correctness**
   `/fig_queue_run` now has an explicit parity contract with `/fig_queue`.

2. **Scope containment**
   No driver policy, command-plan safety predicate, SVG handoff authority, or
   fixture source behavior changed.

3. **Future maintainability**
   Future queue filters must be mirrored in queue-run or the test/runtime guard
   will make the drift visible immediately.
