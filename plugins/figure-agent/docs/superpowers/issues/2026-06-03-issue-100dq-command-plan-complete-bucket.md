# Issue 100DQ - Command-Plan Complete Bucket

Status: implemented in this slice

Type: queue command-plan UX, mode-scoped completion, operator workflow

## Problem

Issue 100DP removed `complete` rows from blocker-source summaries, but
`/fig_queue --command-plan` still placed mode-scoped `complete` rows under
`command_plan.blocked` with reasons such as `required_actor:none`.

A live authoring queue had seven mode-scoped complete rows and one compile row.
The table was clear, but command-plan JSON still reported `blocked_count: 7`.
That made local completion look like blocked automation.

## Scope

Keep command execution safety unchanged. Complete rows remain non-executable.
Do not execute broader-mode follow-up commands, mutate fixtures, change driver
selection, or reinterpret release/host/human boundaries.

## Implemented Behavior

- `build_command_plan()` now separates mode-scoped complete rows into
  `command_plan.complete`.
- `command_plan.complete_count` counts those rows.
- `command_plan.blocked_count` now counts only truly blocked rows.
- Complete records preserve the existing `operator_handoff` with the driver's
  broader-mode `operator_guidance.next_step`.
- Existing `executable` and `blocked` records remain unchanged for actionable
  workflow-agent rows and blocked host/human/release/closeout rows.

## Tests

- `tests/test_fig_queue.py::test_queue_command_plan_uses_operator_guidance_for_complete_rows`
  now asserts complete rows land under `command_plan.complete`.
- Existing command-plan and queue-run tests prove executable/blocked handling
  still works.
- `tests/test_release_contract.py::test_fig_queue_docs_separate_complete_rows_from_command_plan_blockers`
  guards the operator-facing docs.

## Review Notes

- Safety: complete rows are still not executable.
- Contract: additive `complete_count` and `complete` fields clarify command-plan
  meaning without removing existing `executable` or `blocked`.
- Operator fit: command-plan JSON now matches the table's "mode-local complete,
  inspect broader mode next" wording.
