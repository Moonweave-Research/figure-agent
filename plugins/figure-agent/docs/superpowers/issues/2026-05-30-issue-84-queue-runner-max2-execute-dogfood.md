# Issue 84 - Queue Runner Max-2 Execute Dogfood

Status: completed

Depends on:

- Issue 82 - queue runner dogfood and operator playbook
- Issue 83 - queue runner execute dogfood

Type: dogfood, operator validation

## Problem

Issue 83 proved that `/fig_queue_run --execute --max-fixtures 1` delegates to
`/fig_run` safely and stops repeated no-progress commands with
`repeated_executable_action`. The next operational question is whether the same
contract remains clear when the batch contains more than one executable
workflow-agent fixture.

## Goal

Dogfood `/fig_queue_run --execute` with `--max-fixtures 2` against the current
real fixture queue.

## Scope

- Re-run queue-run in plan-only mode with `--max-fixtures 2`.
- Run the same queue-run with `--execute`.
- Confirm only workflow-agent executable rows are attempted.
- Confirm closeout-blocked export rows remain blocked.
- Confirm each attempted fixture stops after one no-progress loop command.
- Do not change source, exports, accepted/golden state, publication state, SVG,
  host critique, or fixture specs.

## Dogfood Result

Plan-only:

- attempted: 2
- planned_executable: 2
- planned_blocked: 1
- executable fixtures:
  - `fig3_trapping_concept`
  - `smoke_trap_demo`
- blocked fixture:
  - `fig5_floating_clip_mechanism` / `stop_boundary:closeout_required`

Execute:

- attempted: 2
- executed_commands: 2
- failed: 0
- planned_blocked: 1
- `fig3_trapping_concept`: executed once, then stopped with
  `repeated_executable_action`
- `smoke_trap_demo`: executed once, then stopped with
  `repeated_executable_action`

Both fixture handoffs reported:

```text
same executable action and command was selected again after a successful run;
stopped to avoid no-progress replay
```

No source, export, accepted, golden, publication, SVG, or host-critique state
was mutated.

## Review

1. Batch-boundary review: clean. `--max-fixtures 2` attempted exactly the two
   executable workflow-agent rows and did not attempt the closeout-blocked
   export row.
2. Runner-safety review: clean. The Issue 83 repeated-action guard applies per
   fixture and prevents duplicate loop evidence for both fixtures.
3. Operator-readiness review: clean. The queue summary and per-run result give
   enough evidence to proceed without reading the full JSON payload.

No known Issue 84 blocker remains.
