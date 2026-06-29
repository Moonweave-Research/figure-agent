# Wave 0 Queue Bottleneck Plan

Date: 2026-06-29

## Scope

Wave 0 is a repo-local, read-only planning slice for the current figure-agent
fixture corpus. It does not compile, export, patch, accept, force golden state,
or edit figure sources. Its purpose is to make the next bottleneck visible from
live `/fig_queue` and `/fig_status`-derived driver state before any operator
chooses an execution wave.

## Live command

Run from `plugins/figure-agent`:

```bash
fig-agent queue --mode review --goal "Wave 0 bottleneck scan" --json
```

The JSON output includes `bottleneck_report` with schema
`figure-agent.queue-bottleneck-report.v1`. The report is derived from the
filtered queue rows, which are themselves produced by `/fig_drive` over live
status inference. It summarizes:

- total row and error counts;
- dominant actions;
- dominant first status blockers;
- dominant required actors;
- dominant blocking sources;
- command-plan counts for executable, blocked, and mode-complete rows.

## Current Wave 0 reading

At the time this plan was written, the review-mode queue reported 14 rows:
13 rows at `run_compile` / `render_missing` and 1 row at
`create_or_fix_source` / `source_not_authored`. That makes the first wave a
render-freshness wave, not a critique, export, accepted-state, or golden-state
wave.

## Execution boundary

Allowed next step: inspect `bottleneck_report`, then decide whether to run a
bounded `/fig_queue_run` plan for deterministic `workflow_agent` rows.

Forbidden in Wave 0: accepted/golden mutation, source edits, unreviewed export
mutation, TeX execution as part of this plan document, or plugin-side model/API
calls.
