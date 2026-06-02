---
description: Read-only multi-fixture driver queue. Aggregates /fig_drive decisions without executing or mutating files.
---

Inspect the driver-selected next action for multiple fixtures.

**Usage**: `/fig_queue --mode <mode> --goal "<goal>" [filters] [<fixture> ...] [--json | --format json]`

Run from the plugin root:

```bash
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>"
uv run python3 scripts/fig_queue.py --mode release --goal "<goal>" --json
uv run python3 scripts/fig_queue.py --mode release --goal "<goal>" --format json
uv run python3 scripts/fig_queue.py --mode final --goal "final readiness" --json
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" fig1_overview_v2_pair_001_vault
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor host_llm
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --action run_fig_loop
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor workflow_agent --command-plan --json
uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor workflow_agent --commands
```

`/fig_queue` is an operator dashboard over `/fig_drive`. It calls the existing
dry-run driver selector once per fixture, copies the selected `action`,
`stop_boundary`, `safe_command`, required actor, blocker source, and
`/fig_status` state fields into a compact row. When the driver emits
mode-scoped `operator_guidance`, the queue preserves it so a row with
`action: complete` still explains the next broader mode to inspect instead of
looking like whole-figure completion. The queue then summarizes counts by
action, stop boundary, first blocker, required actor, and blocking source.

The command is read-only. It never compiles, critiques, adjudicates, loops,
exports, patches, polishes, accepts, stages, commits, or forces golden state.
Use `/fig_run` for bounded deterministic execution of a single fixture after
inspecting the queue.

## Canonical operator sequence

For multi-fixture work, use the queue before running any fixture command:

1. Inspect the whole queue:
   `uv run python3 scripts/fig_queue.py --mode review --goal "<goal>"`.
2. Filter host-vision rows:
   `uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor host_llm`.
3. Refresh those critiques in the host LLM environment, then re-check the
   queue.
4. Inspect deterministic workflow-agent work with
   `--actor workflow_agent --command-plan --json`.
5. Use `/fig_queue_run` in plan-only mode first; add `--execute` only after
   reviewing the plan.
6. Handle `human`, `release_operator`, and `svg_editor` rows as explicit
   non-automatic gates.

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
- `--svg-polish-gate-state ready|blocked|needs_human|semantic_backport|no_current_checkpoint`
- `--can-start-svg-polish true|false`
- `--svg-polish-recommended-path <route>`
- `--svg-polish-next-action <svg-polish-next-action>`
- `--svg-polish-blocking-source <source>`

The SVG-polish filters are meaningful in `--mode polish`. They let operators
ask direct evidence questions such as "which real fixtures can start SVG polish
now?" without hand-filtering JSON:

```bash
uv run python3 scripts/fig_queue.py --mode polish --can-start-svg-polish true
```

Use `--command-plan` to add a read-only `command_plan` object to JSON output.
Use `--commands` to print only executable deterministic workflow commands, one
per line. Neither mode executes anything.

Output is a table by default. `--json` and `--format json` both print the same
JSON contract; `--format table` is accepted as the explicit table form.

The command plan treats a row as executable only when all of these are true:

- `required_actor == workflow_agent`
- `requires_human == false`
- `safe_command` is present
- `stop_boundary` is empty
- `action` is one of `/fig_run`'s deterministic allowlist:
  `run_compile`, `run_adjudicate`, `run_export`, or `run_fig_loop`
- for `run_export`, the row also matches the draft-export safety predicate:
  exact fixture command, `acceptance_state: NOT_DECLARED`,
  `export_state: MISSING | STALE`, and `critique_state: FRESH | NOT_REQUIRED`

Host critique, human review, release/golden approval, SVG polish handoff,
missing commands, non-allowlisted actions, and rows with stop boundaries remain
blocked and visible in the command plan.

## Output JSON contract

`schema: figure-agent.fixture-driver-queue.v1` with these top-level fields:

| Field | Type | Notes |
|---|---|---|
| `schema` | string | `figure-agent.fixture-driver-queue.v1` |
| `mode` | string | driver mode: `authoring`, `review`, `release`, `polish`, or `final` |
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
| `blocking_source` | compact source from `next_action_summary.blocking_source`, stop boundary, or driver action; mode-scoped `complete` rows use `null` so completion is not counted as a blocker |
| `requires_human` | copied from `next_action_summary.requires_human` when available |
| `render_state` | compact status field |
| `critique_state` | compact status field |
| `export_state` | compact status field |
| `acceptance_state` | compact status field |
| `publication_gate_state` | compact status field |
| `release_ready` | compact status field |
| `operator_guidance` | copied from `/fig_drive` when present; complete rows use its `next_step` to avoid hiding mode-scoped follow-up |
| `error` | present only for controlled error rows |

In `--mode polish`, rows also include SVG-polish gate fields when the underlying
driver has a current loop checkpoint or gate explanation:

| Field | Notes |
|---|---|
| `svg_polish_gate_state` | compact `svg_polish_gate.state` copied from `/fig_drive` |
| `can_start_svg_polish` | whether the current gate permits bounded SVG polish |
| `svg_polish_recommended_path` | latest loop editorial route, such as `continue_tikz` or `ready_for_svg_polish` |
| `svg_polish_next_action` | next action from the SVG polish gate/readiness summary |
| `svg_polish_blocking_sources` | unique blocker sources copied from `svg_polish_gate.blocking_items` and `svg_polish_readiness.blocking_items`, for example `driver_prerequisite`, `driver_blocker`, or `tikz_vs_svg_polish_trigger` |

`summary` includes:

- `total`
- `errors`
- `by_action`
- `by_stop_boundary`
- `by_first_blocker`
- `by_required_actor`
- `by_blocking_source`
- `by_svg_polish_gate_state` when polish rows expose SVG gate state
- `by_svg_polish_recommended_path` when polish rows expose readiness route
- `by_svg_polish_next_action` when polish rows expose SVG next-action guidance
- `by_svg_polish_blocking_source` when polish gate/readiness reports blocker sources

The human-readable table prints `summary total=... errors=...` followed by
deterministically sorted grouped summary lines such as
`summary by_action=run_critique:4,run_fig_loop:2` and, in polish mode,
`summary by_svg_polish_next_action=run_fig_critique:4,rerun_fig_loop:2`.
Those lines mirror the JSON `summary` object so operators can see the corpus
dominant actor/action/blocker distribution without switching to JSON.

`command_plan` includes:

| Field | Notes |
|---|---|
| `schema` | `figure-agent.fixture-command-plan.v1` |
| `executable_count` | number of rows with safe deterministic commands |
| `blocked_count` | number of rows blocked by host/human/release/closeout/unsafe workflow boundaries |
| `complete_count` | number of mode-scoped complete rows that are non-executable but not blocked |
| `executable` | fixture/action/safe_command/required_actor records |
| `blocked` | fixture/action/actor/blocking_source/stop_boundary/reason records |
| `complete` | fixture/action/actor plus mode-scoped `operator_handoff` records |

The human-readable table prints tab-separated `next_step` and `next_command`
columns. When any row contains SVG-polish gate fields, the table also prints
`svg_gate`, `can_svg`, `polish_path`, `polish_next`, and `polish_blockers`
columns so a polish-mode queue does not hide why a fixture can or cannot enter
the bounded SVG handoff. For complete rows, `next_step` uses the driver's
mode-scoped `operator_guidance.next_step` when available. For blocked rows, the
next-step fields come from the same handoff policy used by
`command_plan.blocked[].operator_handoff`, so the table does not show a blocked
driver command as the next command to run.

Blocked command-plan rows include an additive
`schema: figure-agent.queue-operator-handoff.v1` object under
`operator_handoff`. The handoff states the required actor, next step, optional
command, allowed scope, forbidden scope, and closeout checks. It is guidance for
the operator; it does not make blocked rows executable. Complete rows are
non-executable but not blocked; they live under `command_plan.complete`, count
toward `complete_count`, and use preserved driver `operator_guidance.next_step`
when available so mode-local completion remains visible in JSON as well as the
table.

The queue does not reinterpret driver policy. If a row looks surprising, inspect
the corresponding single-fixture `/fig_drive <name> --mode <mode> --goal
"<goal>" --dry-run` output for full evidence.
