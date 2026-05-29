---
description: Read-only multi-fixture driver queue. Aggregates /fig_drive decisions without executing or mutating files.
---

Inspect the driver-selected next action for multiple fixtures.

**Usage**: `/fig_queue --mode <mode> --goal "<goal>" [<fixture> ...] [--json]`

Run from the plugin root:

```bash
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>"
uv run python3 scripts/fig_queue.py --mode release --goal "<goal>" --json
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" fig1_overview_v2_pair_001_vault
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

## Output JSON contract

`schema: figure-agent.fixture-driver-queue.v1` with these top-level fields:

| Field | Type | Notes |
|---|---|---|
| `schema` | string | `figure-agent.fixture-driver-queue.v1` |
| `mode` | string | driver mode: `authoring`, `review`, `release`, or `polish` |
| `goal` | string | passthrough goal used for driver recommendations |
| `rows` | list | one compact row per fixture or controlled error |
| `summary` | object | total/error counts plus grouped counts |

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

The queue does not reinterpret driver policy. If a row looks surprising, inspect
the corresponding single-fixture `/fig_drive <name> --mode <mode> --goal
"<goal>" --dry-run` output for full evidence.
