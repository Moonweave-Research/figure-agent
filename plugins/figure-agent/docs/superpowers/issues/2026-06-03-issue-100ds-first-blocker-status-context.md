# Issue 100DS - First-Blocker Status Context

Status: implemented in this slice

Type: operator workflow, queue documentation guard

## Problem

After Issues 100DP-100DR, complete rows were correctly separated from true
blocked rows in queue summaries, command-plan JSON, and queue-run summaries.
However, `/fig_queue` still reports `by_first_blocker`, which is copied from
global `/fig_status` context. Live authoring dogfood showed complete rows with
first blockers such as `critique_stale` and `acceptance_not_declared`.

That signal is useful for broader workflow routing, but it is not a current-mode
blocker. Without explicit wording, operators could still read
`by_first_blocker` as a blocked-row distribution.

## Scope

- Clarify `/fig_queue` command documentation.
- Preserve existing JSON/table fields for backward compatibility.
- Do not change row filtering, command-plan construction, driver decisions,
  queue-run behavior, or fixture artifacts.

## Implemented Behavior

- `commands/fig_queue.md` now states that `by_first_blocker` is status context
  from `/fig_status`, can include mode-scoped complete rows, and should not be
  treated as proof of selected-mode blockage.
- It directs operators to `by_blocking_source` and
  `command_plan.blocked_count` for true current-mode blockers.
- A release-contract test guards the wording.

## Tests

- `tests/test_release_contract.py::test_fig_queue_docs_explain_first_blocker_is_status_context_not_mode_blocker`

## Review Notes

- Contract: docs-only clarification; no JSON field rename or removal.
- Safety: complete rows remain non-executable and non-blocked.
- UX: table/global status context remains visible without recreating the
  earlier "complete equals blocked" confusion.
