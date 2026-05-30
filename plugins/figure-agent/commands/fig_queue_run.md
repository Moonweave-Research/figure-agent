---
description: Plan or execute bounded workflow-agent work from the filtered fixture queue.
---

Run the executable workflow-agent subset from `/fig_queue`.

**Usage**: `/fig_queue_run --mode <mode> --goal "<goal>" [filters] [<fixture> ...] [--execute]`

Run from the plugin root:

```bash
uv run python3 scripts/fig_queue_run.py --mode review --goal "<goal>" --actor workflow_agent
uv run python3 scripts/fig_queue_run.py --mode review --goal "<goal>" --actor workflow_agent --max-fixtures 2
uv run python3 scripts/fig_queue_run.py --mode review --goal "<goal>" --actor workflow_agent --execute
```

`/fig_queue_run` is plan-only by default. It builds the same
`/fig_queue --command-plan` data, takes only `command_plan.executable`, and
reports which fixture runs would be attempted.

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
and applies the existing deterministic allowlist and safety predicates.

## Filters

The command accepts the same filters as `/fig_queue`:

- `--actor workflow_agent|host_llm|human|release_operator|svg_editor`
- `--action <driver-action>`
- `--stop-boundary <boundary-id>`
- `--first-blocker <status-first-blocker-code>`
- `--blocking-source <next-action-blocking-source>`

In normal use, pass `--actor workflow_agent`; other actors are preserved as
blocked command-plan rows and will not be attempted.

## Safety

- Default mode is plan-only.
- `--execute` delegates to `/fig_run`; this script never calls shell commands
  directly.
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
| `queue` | source queue summary plus command plan |
| `runs` | one record per attempted fixture |
| `summary` | planned executable, planned blocked, attempted, unattempted executable, executed command, failed, and blocked counts |

Run records contain the planned fixture/action/command. In execute mode they
also include the embedded `/fig_run` result so the operator can inspect the live
revalidation stop reason.

Blocked rows remain under `queue.command_plan.blocked`. Each blocked row carries
`operator_handoff`, copied from `/fig_queue`, so the operator can see the next
manual/host/release/closeout action without making that row executable.
