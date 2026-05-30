---
description: Read-only multi-fixture driver queue. Aggregates /fig_drive decisions without executing or mutating files.
---

Inspect the driver-selected next action for multiple fixtures.

**Usage**: `/fig_queue --mode <mode> --goal "<goal>" [filters] [<fixture> ...] [--json]`

Run from the plugin root:

```bash
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>"
uv run python3 scripts/fig_queue.py --mode release --goal "<goal>" --json
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" fig1_overview_v2_pair_001_vault
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor host_llm
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --action run_fig_loop
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor workflow_agent --command-plan --json
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor workflow_agent --commands
```

`/fig_queue` is an operator dashboard over `/fig_drive`. It calls the existing
dry-run driver selector once per fixture, copies the selected `action`,
`stop_boundary`, `safe_command`, required actor, blocker source, and
`/fig_status` state fields into a compact row, then summarizes counts by
action, stop boundary, first blocker, required actor, and blocking source.

The command is read-only. It never compiles, critiques, adjudicates, loops,
exports, patches, polishes, accepts, stages, commits, or forces golden state.
Use `/fig_run` for bounded deterministic execution of a single fixture after
inspecting the queue.

With no fixture arguments, the queue scans `examples/*/spec.yaml` and sorts
fixtures by directory name. With fixture arguments, only those fixtures are
checked. Missing fixtures are reported as controlled `error` rows instead of
tracebacks.

Filters are applied after driver rows are built, so they do not change driver
selection or fixture scanning. Supported filters:

- `--actor workflow_agent|host_llm|human|release_operator|svg_editor`
- `--action <driver-action>`
- `--stop-boundary <boundary-id>`
- `--first-blocker <status-first-blocker-code>`
- `--blocking-source <next-action-blocking-source>`

Use `--command-plan` to add a read-only `command_plan` object to JSON output.
Use `--commands` to print only executable deterministic workflow commands, one
per line. Neither mode executes anything.

The command plan treats a row as executable only when all of these are true:

- `required_actor == workflow_agent`
- `requires_human == false`
- `safe_command` is present
- `stop_boundary` is empty
- `action` is one of `/fig_run`'s deterministic allowlist:
  `run_compile`, `run_adjudicate`, `run_export`, or `run_fig_loop`

Host critique, human review, release/golden approval, SVG polish handoff,
missing commands, non-allowlisted actions, and rows with stop boundaries remain
blocked and visible in the command plan.

## Output JSON contract

`schema: figure-agent.fixture-driver-queue.v1` with these top-level fields:

| Field | Type | Notes |
|---|---|---|
| `schema` | string | `figure-agent.fixture-driver-queue.v1` |
| `mode` | string | driver mode: `authoring`, `review`, `release`, or `polish` |
| `goal` | string | passthrough goal used for driver recommendations |
| `filters` | object | active filters only; empty object when no filters were supplied |
| `unfiltered_total` | int | row count before filters are applied |
| `rows` | list | one compact row per fixture or controlled error |
| `summary` | object | total/error counts plus grouped counts |
| `command_plan` | object | present only with `--command-plan`, `--commands`, or API opt-in |

Each row includes:

| Field | Notes |
|---|---|
| `fixture` | fixture name |
| `mode` | selected driver mode |
| `action` | copied from `/fig_drive`, or `error` |
| `stop_boundary` | copied from `/fig_drive`, or a controlled error boundary |
| `first_blocker` | `status_explanation.first_blocker.code` when available |
| `safe_command` | copied from `/fig_drive`; still advisory, not executed |
| `required_actor` | `workflow_agent`, `host_llm`, `human`, `release_operator`, or `svg_editor` |
| `blocking_source` | compact source from `next_action_summary.blocking_source`, stop boundary, or driver action |
| `requires_human` | copied from `next_action_summary.requires_human` when available |
| `render_state` | compact status field |
| `critique_state` | compact status field |
| `export_state` | compact status field |
| `acceptance_state` | compact status field |
| `publication_gate_state` | compact status field |
| `release_ready` | compact status field |
| `error` | present only for controlled error rows |

`summary` includes:

- `total`
- `errors`
- `by_action`
- `by_stop_boundary`
- `by_first_blocker`
- `by_required_actor`
- `by_blocking_source`

`command_plan` includes:

| Field | Notes |
|---|---|
| `schema` | `figure-agent.fixture-command-plan.v1` |
| `executable_count` | number of rows with safe deterministic commands |
| `blocked_count` | number of rows excluded from executable commands |
| `executable` | fixture/action/safe_command/required_actor records |
| `blocked` | fixture/action/actor/blocking_source/stop_boundary/reason records |

The queue does not reinterpret driver policy. If a row looks surprising, inspect
the corresponding single-fixture `/fig_drive <name> --mode <mode> --goal
"<goal>" --dry-run` output for full evidence.
