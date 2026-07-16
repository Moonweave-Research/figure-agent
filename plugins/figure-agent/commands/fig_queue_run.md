---
description: Plan or execute bounded workflow-agent work from the filtered fixture queue.
---

Run the executable workflow-agent subset from `/fig_queue`.

**Usage**: `/fig_queue_run --mode <mode> --goal "<goal>" [filters] [<fixture> ...] [--dry-run] [--json | --format json] [--execute]`

Run from the plugin root:

```bash
fig-agent queue-run --mode review --goal "<goal>" --actor workflow_agent
fig-agent queue-run --mode review --goal "<goal>" --actor workflow_agent --max-fixtures 2
fig-agent queue-run --mode review --goal "<goal>" --actor workflow_agent --execute
fig-agent queue-run --mode review --goal "<goal>" --actor workflow_agent --format json
fig-agent queue-run --mode polish --goal "<goal>" --can-start-svg-polish true
```

`/fig_queue_run` is plan-only by default. It builds the same
`/fig_queue --command-plan` data, takes only `command_plan.executable`, and
reports which fixture runs would be attempted.

Output is JSON by default. `--json`, `--format json`, and `--dry-run` are
accepted as compatibility no-ops: `--dry-run` does not change behavior because
plan-only is already the default, and only `--execute` opts into bounded
execution. `--execute --dry-run` is rejected as an ambiguous safety conflict;
choose one mode explicitly.

Use it after inspecting `/fig_queue --actor workflow_agent --command-plan`.
The normal order is:

1. run `/fig_queue` for the whole fixture set;
2. close host LLM critique rows first;
3. inspect the workflow-agent command plan;
4. run `/fig_queue_run` without `--execute`;
5. add `--execute` only after the plan shows the intended fixtures and no
   unexpected blocked rows.

With `--execute`, it still does not execute queue commands directly. For each
planned fixture it calls `/fig_run` logic, which re-queries live driver state
and applies the existing deterministic allowlist and safety predicates. It
also passes the exact queued `action` and `safe_command` as a first-step
expectation. Compile, adjudication-scaffold, and export candidates are re-queried
and revalidated under the shared fixture admission lease, which remains held
through subprocess completion. A mismatch or lost safety predicate returns
`stale_plan`; a busy lease returns `admission_busy`. Neither starts a
subprocess. A matched first step is consumed after its successful command;
later steps remain free to follow fresh live driver decisions and reacquire the
lease independently.

Queue-bound `run_fig_loop` is temporarily non-executing and returns
`run_fig_loop_admission_integration_pending`. Direct single-fixture `fig_run`
retains the existing self-leased `fig_loop` path; queue-run does not add an
outer lease around it.

## Exit status

The complete JSON payload is written before `queue-run` exits. Direct
`fig_queue_run.py` and `fig-agent queue-run` use the same exit matrix:

| Exit | Condition |
|---|---|
| `0` | Plan-only/dry-run, or an execute batch with no nested `/fig_run` `command_failed`, `stale_plan`, `admission_busy`, or `run_fig_loop_admission_integration_pending` final stop. This includes complete, host/human boundaries, repeated-action, max-step, blocked, unattempted, and pre-delegation fixture-row errors. |
| `1` | `--execute` delegated at least one selected fixture to `/fig_run` and that nested run ended with canonical `final_stop_reason: command_failed`, `stale_plan`, `admission_busy`, or `run_fig_loop_admission_integration_pending`. Remaining selected fixtures are still attempted and remain in `runs`. |
| `2` | Existing argument/value errors or workspace diagnostics, including missing `examples/` and an implicit symlinked `examples/` directory. These diagnostics take precedence over delegated command failures. |

`summary.failed` counts only delegated command failures. `summary.stale`,
`summary.busy`, and `summary.admission_pending` count their corresponding
admission stops separately. Exit status is based only on those actual nested
`/fig_run` stop contracts, so a pre-delegation fixture/path error row does not
make shell or CI treat the batch as a delegated execution error.

## Filters

The command accepts the same filters as `/fig_queue`:

- `--actor workflow_agent|host_llm|human|release_operator|svg_editor`
- `--action <driver-action>`
- `--stop-boundary <boundary-id>`
- `--first-blocker <status-first-blocker-code>`
- `--blocking-source <next-action-blocking-source>`
- `--svg-polish-gate-state ready|blocked|needs_human|semantic_backport|no_current_checkpoint`
- `--can-start-svg-polish true|false`
- `--svg-polish-recommended-path <route>`
- `--svg-polish-next-action <svg-polish-next-action>`
- `--svg-polish-blocking-source <source>`

In normal use, pass `--actor workflow_agent`; other actors are preserved as
blocked command-plan rows and will not be attempted.

The SVG-polish filters match `/fig_queue`. They are useful for plan-only
promotion evidence, for example checking that no real fixture can enter bounded
SVG polish yet, or planning only fixtures whose SVG gate is ready. They do not
make SVG polish handoff executable; `svg_editor` rows remain blocked.

## Safety

- Default mode is plan-only.
- `--execute` delegates to `/fig_run`; this script never calls shell commands
  directly.
- Compile, adjudication-scaffold, and export subprocesses run only after
  under-lease live revalidation.
- Queue-bound `run_fig_loop` remains non-executing until its queue admission
  integration is implemented.
- `--max-fixtures` bounds the number of fixture attempts.
- Host critique, human review, release/golden approval, SVG polish handoff,
  and rows with stop boundaries are not attempted.
- Accepted/golden/publication state is never mutated by this command.

## Output JSON contract

`schema: figure-agent.queue-run.v1` with:

| Field | Notes |
|---|---|
| `mode`, `goal`, `execute`, `max_steps`, `max_fixtures` | selected run settings |
| `fixtures` | explicit fixture args, or empty list when scanning the queue |
| `filters` | active queue filters |
| `queue` | source queue summary, `bottleneck_report`, and command plan |
| `runs` | one record per attempted fixture |
| `summary` | planned executable, planned blocked, planned complete, attempted, unattempted executable, executed command, failed, stale, busy, admission-pending, and blocked counts |

Run records contain the planned fixture/action/command. In execute mode they
also include the embedded `/fig_run` result, including additive `plan_binding`
evidence, so the operator can inspect the live revalidation stop reason.

Blocked rows remain under `queue.command_plan.blocked`. Each blocked row carries
`operator_handoff`, copied from `/fig_queue`, so the operator can see the next
manual/host/release/closeout action without making that row executable.

Mode-scoped complete rows remain under `queue.command_plan.complete` and are
counted as `summary.planned_complete`. They are non-executable, but they are not
blocked and do not count toward `summary.blocked`.

Admission and machine-gate outcomes never claim visual, human-development,
release, or publication acceptance.
