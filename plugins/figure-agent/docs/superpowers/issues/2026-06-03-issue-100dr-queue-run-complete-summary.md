# Issue 100DR - Queue-Run Complete Summary

Status: implemented in this slice

Type: operator workflow, queue runner JSON contract, documentation guard

## Problem

Issue 100DQ split mode-scoped `complete` rows out of
`command_plan.blocked`. `/fig_queue_run` embeds that full command plan, but its
top-level `summary` still only exposed `planned_executable`,
`planned_blocked`, and execution counters.

That meant a plan-only batch run could preserve `queue.command_plan.complete`
deep in the payload while the operator-facing summary made mode-scoped complete
rows effectively disappear.

## Scope

- Add an additive `summary.planned_complete` count to `/fig_queue_run`.
- Keep complete rows non-executable.
- Keep blocked rows and blocked counts reserved for true host/human/release,
  closeout, or unsafe workflow boundaries.
- Do not change queue selection, driver decisions, execution allowlists,
  accepted/golden state, exports, source files, or fixture artifacts.

## Implemented Behavior

- `scripts/fig_queue_run.py` copies `command_plan.complete_count` into
  `summary.planned_complete`.
- `commands/fig_queue_run.md` documents that complete rows live under
  `queue.command_plan.complete`, count as `summary.planned_complete`, and do
  not count toward `summary.blocked`.
- Release-contract docs tests guard the wording.

## Tests

- `tests/test_fig_queue_run.py::test_plan_only_reports_planned_runs_without_executing`
  covers the additive summary count.
- `tests/test_release_contract.py::test_fig_queue_run_docs_separate_complete_rows_from_blocked_summary`
  guards the command documentation.

## Review Notes

- Contract: additive JSON field; existing consumers that ignore unknown fields
  remain compatible.
- Safety: no row becomes executable because it is complete; only the summary
  count changes.
- UX: queue, command-plan, and queue-run summaries now use the same blocked vs
  complete distinction.
