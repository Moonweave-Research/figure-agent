# Issue 100DN - Queue Table Summary Counts

Status: implemented in this slice

Type: operator UX, queue contract, documentation guard

## Problem

Issues 100DL and 100DM made `/fig_queue --mode polish` compute and document
rich SVG-polish summary fields in JSON. A live polish queue still showed only
`summary total=8 errors=0` in the default human-readable table.

That meant the plugin had already computed the dominant corpus state, such as
`run_fig_critique: 4`, `run_fig_compile: 1`, `rerun_fig_loop: 2`, and
`resolve_release_boundary: 1`, but the operator still had to switch to JSON or
scan rows manually to see what to do first.

## Scope

Add grouped summary count lines to the default table output only. Do not change
queue JSON, driver selection, filters, command-plan execution, fixture state,
or SVG polish gate policy.

## Implemented Behavior

- `print_table()` now prints deterministic grouped summary lines after
  `summary total=... errors=...`.
- The table mirrors existing JSON `summary` count dictionaries:
  - `by_action`
  - `by_stop_boundary`
  - `by_first_blocker`
  - `by_required_actor`
  - `by_blocking_source`
  - SVG polish summary keys when present
- Empty or malformed summary dictionaries are skipped instead of producing
  noisy placeholder lines.
- `/fig_queue` docs now state that human-readable table summaries mirror the
  JSON summary object.

## Tests

- `tests/test_fig_queue.py::test_print_table_outputs_grouped_summary_counts`
  covers deterministic table rendering for grouped counts.
- `tests/test_release_contract.py::test_fig_queue_docs_describe_table_grouped_summary_counts`
  guards the operator-facing command documentation.

## Review Notes

- Safety: read-only output formatting only; no mutation path changed.
- Contract: JSON remains unchanged; table output becomes a more complete view
  of the existing contract.
- Operator fit: the default queue view now shows corpus-level dominant actions
  without requiring JSON post-processing.
