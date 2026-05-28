---
description: Bounded workflow runner. Executes only allowlisted deterministic shell steps from /fig_drive and stops at host, human, patch, polish, release, accepted, and golden boundaries.
---

Run a bounded figure workflow until the next non-automatic boundary.

**Usage**: `/fig_run <name> --mode <mode> --goal "<goal>" [--execute]`

Run from the plugin root:

```bash
uv run python3 scripts/fig_run.py <name> --mode review --goal "<goal>"
uv run python3 scripts/fig_run.py <name> --mode review --goal "<goal>" --execute
```

`/fig_run` is a conservative executor over `/fig_drive`. It asks the driver
for one next action, executes only allowlisted deterministic shell actions, then
asks the driver again. It stops when the next action requires host vision,
human judgment, patch handoff, SVG polish handoff, export/adjudication policy,
accepted state, golden roll-forward, release approval, or any unsupported
mutation.

Default mode is plan-only. Without `--execute`, the command emits what would be
run and does not mutate anything.

## Execution Policy

The executable actions are allowed only when the driver attaches no
`stop_boundary`:

- `run_compile` -> `bash scripts/compile.sh examples/<name>/<name>.tex`
- `run_fig_loop` -> `uv run python3 scripts/fig_loop.py <name> --goal ... --json`

The runner intentionally stops on these actions even when they have shell
commands:

- `run_adjudicate`
- `run_export`

Those commands mutate review/export evidence and need separate policy hardening
before they can be safely automated. `/fig_loop` is allowed because it is
verify-only and writes bounded run evidence under `.scratch/fig-loop-runs/`.
The runner always stops on `/fig_critique`
because that is a host-vision operation, not a shell command.

## Output JSON contract

`schema: figure-agent.run.v1` with these fields:

| Field | Type | Notes |
|---|---|---|
| `schema` | string | `figure-agent.run.v1` |
| `fixture` | string | figure name |
| `mode` | string | driver mode |
| `goal` | string | passthrough goal |
| `execute` | bool | whether allowed shell commands were executed |
| `max_steps` | int | safety cap |
| `executable_actions` | list | current allowlist: `run_compile`, `run_fig_loop` |
| `steps` | list | driver action plus execution result for each iteration |
| `final_action` | string | last driver action |
| `final_safe_command` | string or null | last command selected by driver |
| `final_stop_boundary` | string or null | last driver stop boundary |
| `final_stop_reason` | string | runner reason for stopping |
| `executed_count` | int | number of shell commands actually run |

Step entries include the embedded `/fig_drive` JSON under `driver` so an outer
agent can inspect the exact status, blocker, and next-action evidence used for
the decision. A successful executed step may have `stop_reason: null`; the
runner then re-queries the driver for the next action.

## Stop Reasons

- `plan_only` — command would be executable, but `--execute` was not passed.
- `host_boundary` — host vision or slash command required.
- `not_executable_action` — driver selected an action outside the Issue 66A
  allowlist.
- `command_failed` — an executed command returned non-zero.
- `complete` — driver selected `complete`.
- `max_steps_exceeded` — the runner hit the safety cap before state advanced to
  a boundary.

## When To Use

Use `/fig_run` when the user wants the plugin to proceed through safe mechanical
steps without asking for each compile. Use `/fig_drive --dry-run` when you only
need a recommendation. Use the lower-level slash commands directly when the
user is intentionally operating one specific stage.

`/fig_run` does not remove human gates. It only removes unnecessary manual
copy-paste for deterministic shell work the driver already selected.
