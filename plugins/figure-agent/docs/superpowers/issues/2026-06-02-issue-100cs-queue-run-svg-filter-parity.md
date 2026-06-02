# Issue 100CS - Queue-Run SVG Filter Parity

Status: implemented

Type: operator workflow, queue runner, SVG polish readiness

## Problem

Issues 100CQ and 100CR made `/fig_queue --mode polish` useful for direct SVG
polish evidence queries:

- `--can-start-svg-polish true|false`
- `--svg-polish-gate-state <state>`
- `--svg-polish-recommended-path <route>`
- `--svg-polish-next-action <action>`
- `--svg-polish-blocking-source <source>`

`/fig_queue_run` claimed to accept the same filters as `/fig_queue`, but its CLI
only accepted the older actor/action/status filters. The next natural operator
step after queue triage is plan-only queue execution, so this mismatch pushed
SVG promotion evidence back into manual JSON filtering.

## Scope

Keep the slice narrow:

- add the SVG-polish filters to `scripts/fig_queue_run.py`;
- pass those filters through unchanged to `fig_queue.build_queue()`;
- update `/fig_queue_run` command documentation;
- add a focused regression test.

Do not change execution safety. SVG polish handoff rows remain blocked unless
the underlying `/fig_run` and `/fig_drive` contracts already make a deterministic
workflow-agent command executable.

## Implementation

`fig_queue_run.py` now accepts and forwards:

- `--svg-polish-gate-state`
- `--can-start-svg-polish true|false`
- `--svg-polish-recommended-path`
- `--svg-polish-next-action`
- `--svg-polish-blocking-source`

The implementation reuses the existing queue filter keys. It does not add any
new action vocabulary and does not execute SVG editing.

## Tests

`tests/test_fig_queue_run.py` covers the CLI path and asserts that every SVG
filter is forwarded to `fig_queue.build_queue()` and appears in the output
payload's active `filters`.

## Review

1. **Contract parity**
   `/fig_queue_run` now matches the SVG filter surface already exposed by
   `/fig_queue`.

2. **Safety**
   The change only narrows the queue rows used for a plan or execution attempt.
   Existing command-plan executable predicates still decide what can run.

3. **Operator fit**
   Real-fixture SVG polish evidence can now use the same filters through the
   dashboard and the bounded runner, avoiding a return to manual JSON
   post-processing.
