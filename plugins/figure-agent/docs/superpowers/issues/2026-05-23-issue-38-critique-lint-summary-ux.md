# Issue 38 — Critique Lint Summary UX

**Status:** implemented in branch `codex/issue38-critique-lint-summary`

## Problem

Issue 37 surfaces `critique_lint_blocked` in `/fig_status`, but the JSON does
not yet include the lint violation details that explain why the critique is
blocked. Users can run `critique_lint.py` manually, but status/driver consumers
need a compact read-only summary for diagnostics and UI routing.

## Goal

Add a compact `critique_lint_summary` to status output when lint is actually
evaluated. Preserve the existing first-blocker ordering: stale or missing
critique still routes to `/fig_critique` before lint details are treated as
actionable.

## Scope

In scope:

- Add `critique_lint_summary` to `/fig_status` result when `critique_state ==
  FRESH`.
- Forward the summary through `/fig_driver` compact status.
- Keep stale/missing critique behavior unchanged.
- Tests for blocked summary and driver propagation.

Out of scope:

- Running critique lint for stale/missing critiques.
- Changing public critique freshness enum.
- Changing `critique_lint.py` contracts.
- Mutating critique, adjudication, exports, accepted state, or golden state.

## Summary Shape

```yaml
critique_lint_summary:
  state: passed | blocked
  violation_count: <int>
  first_category: <string or null>
  first_message: <string or null>
```

## Acceptance Criteria

- Fresh invalid critique produces `critique_lint_summary.state: blocked`,
  violation count, first category, and first message.
- Fresh clean critique produces `critique_lint_summary.state: passed`.
- `/fig_driver` includes the same summary inside compact `status`.
- Stale/missing critique does not run lint and does not add the summary.

## Implementation Notes

- `/fig_status` now attaches `critique_lint_summary` only when the critique is
  already hash-fresh.
- The summary is intentionally absent for stale or missing critique so the
  first action remains `/fig_critique <name>`.
- `/fig_driver` forwards the summary through its compact status whitelist.

## Verification

- `tests/test_status.py` covers blocked summaries, clean summaries, stale
  omission, and exported-stage propagation.
- `tests/test_fig_driver.py` covers compact driver forwarding.
- Full local verification passed with `uv run pytest -q`, `uv run ruff check
  .`, `git diff --check`, and the three Claude plugin validation commands.
