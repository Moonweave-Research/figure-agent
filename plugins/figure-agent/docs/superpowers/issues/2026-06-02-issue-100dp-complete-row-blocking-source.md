# Issue 100DP - Complete Row Blocking-Source Noise

Status: implemented in this slice

Type: queue UX, mode-scoped completion, summary contract

## Problem

After Issues 100DJ-100DN, `/fig_queue` correctly preserved mode-scoped
completion guidance. A live authoring queue still showed complete rows with
`blocking_source: driver.action`, which made the summary print
`by_blocking_source=driver.action:8`.

That was misleading: a mode-scoped `complete` row is not a blocking source. It
may still carry a broader-mode `first_blocker` such as `critique_stale`, but the
queue already explains that through `operator_guidance.next_step`.

## Scope

Do not change driver action selection, first-blocker reporting,
operator-guidance text, command-plan safety, or broader-mode routing. Only
remove complete rows from blocker-source attribution.

## Implemented Behavior

- `driver_actor.blocking_source_for_driver_summary()` now returns `None` for
  `action: complete`.
- `/fig_queue` rows keep `blocking_source: null` for mode-scoped complete rows.
- `summary.by_blocking_source` no longer counts complete rows as
  `driver.action`.
- Actionable workflow-agent rows, host boundaries, release boundaries, and stop
  boundaries still keep their existing blocker-source attribution.

## Tests

- `tests/test_driver_actor.py::test_blocking_source_omits_mode_scoped_complete_rows`
  covers the helper contract.
- `tests/test_fig_queue.py::test_queue_rows_preserve_driver_operator_guidance_for_complete_modes`
  covers queue row and summary behavior.
- `tests/test_release_contract.py::test_fig_queue_docs_exclude_complete_rows_from_blocking_source`
  guards the command documentation.

## Review Notes

- Safety: read-only attribution only; no mutation path changed.
- Contract: complete rows still expose `action`, `first_blocker`, and
  `operator_guidance`; only blocker-source counting changes.
- Operator fit: authoring/review completion summaries no longer make local
  completion look like a blocker cluster.
