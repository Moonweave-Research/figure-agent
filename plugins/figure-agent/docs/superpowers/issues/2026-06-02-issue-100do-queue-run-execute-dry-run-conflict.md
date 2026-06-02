# Issue 100DO - Queue-Run Execute/Dry-Run Conflict

Status: implemented in this slice

Type: execution safety, CLI contract, operator workflow

## Problem

`/fig_queue_run` is plan-only by default and mutates only when `--execute` is
supplied. It also accepted `--dry-run` as an explicit compatibility spelling.
Before this slice, passing both `--execute --dry-run` silently chose execute
mode.

For a bounded runner that can compile/export/loop through `/fig_run`, that
combination is an ambiguous safety conflict. A user or agent intending a dry
run could accidentally trigger execution.

## Scope

Reject only the conflicting flag combination. Do not change plan-only default
behavior, JSON output, queue filters, command-plan construction, `/fig_run`
delegation, or execution safety predicates.

## Implemented Behavior

- `fig_queue_run.py --execute --dry-run` exits 2 before building/running the
  queue.
- No fixture workflow is attempted when the conflict is present.
- `--dry-run` alone remains a plan-only no-op.
- `--execute` alone still delegates each executable row to `/fig_run`.
- `/fig_queue_run` docs now name the conflict explicitly.

## Tests

- `tests/test_fig_queue_run.py::test_main_rejects_execute_with_dry_run_without_running`
  covers the regression and proves no workflow call is made.
- Existing plan-only and execute-path tests continue to pass.
- `tests/test_release_contract.py::test_fig_queue_run_docs_describe_execute_dry_run_conflict`
  guards the command documentation.

## Review Notes

- Safety: execution now requires an unambiguous `--execute`.
- Compatibility: existing no-flag and `--dry-run` plan-only calls are unchanged.
- Scope: no source, export, accepted, golden, SVG polish, or publication state
  is touched by this change.
