---
description: Bounded workflow runner. Executes only allowlisted deterministic shell steps from /fig_drive and stops at host, human, patch, polish, release, accepted, and golden boundaries.
---

Run a bounded figure workflow until the next non-automatic boundary.

**Usage**: `/fig_run <name> --mode <mode> --goal "<goal>" [--execute] [--json | --format json]`

Run from the plugin root:

```bash
fig-agent run <name> --mode review --goal "<goal>"
fig-agent run <name> --mode review --goal "<goal>" --json
fig-agent run <name> --mode review --goal "<goal>" --format json
fig-agent run <name> --mode review --goal "<goal>" --execute
fig-agent run <name> --mode review --goal "<goal>" --record --runs-root /tmp/fig-run-runs
fig-agent run <name> --mode review --goal "<goal>" --no-record
fig-agent helper fig_run_journal.py <name>
```

### Root attempt admission

For a fresh real render with no canonical attempt, pass exactly one explicit
`--closed-loop-attempt-manifest <manifest.json>` input. The manifest must
hash-bind the fixture, named `authoring_agent`, source and render paths/hashes,
task/model/budget provenance, and `publication_acceptance: not_claimed`.
The runner never discovers a manifest beside a render.

Plan-only validates the manifest and reports the exact proposed
`authored_rendered` state path without writing. `--execute` revalidates under
the shared transition lock and publishes that one root state, then stops.
Admission invokes neither host nor human actor.
Existing current attempts of every disposition are rejected; an identical
concurrent publication is recovered idempotently, while a conflicting one is
rejected. Admission is lifecycle provenance only: it does not create critique,
review, adjudication, attribution, repair, authorization, verdict, accepted or
golden evidence, and never claims visual or publication acceptance.
Admission deliberately does not write a run journal: the canonical state is its
only execute-time publication.

`/fig_run` is a conservative executor over `/fig_drive`. It asks the driver
for one next action, executes only allowlisted deterministic shell actions, then
asks the driver again. It stops when the next action requires host vision,
human judgment, patch handoff, SVG polish handoff, existing adjudication repair,
accepted state, tracked-golden export, golden roll-forward, release approval, or
any unsupported mutation.

The internal `run_workflow` API also accepts an optional paired
`expected_first_action` and `expected_first_safe_command`. `/fig_queue_run`
uses this pair to bind the first admitted live driver step to the queue row it
selected. Both values must be present together and cannot be combined with
explicit closed-loop lifecycle inputs. Direct `/fig_run` calls omit them.

In execute mode, `run_compile`, `run_adjudicate`, and `run_export` each acquire
the shared fixture admission lease independently. The runner identifies a
pre-lock candidate, acquires the lease, re-queries the driver, and revalidates
the exact action, command, absence of a stop boundary, and every action-specific
safety predicate while the lease is held. It holds the lease through subprocess
completion, releases it, and reacquires separately for a later mutation step.
A direct call compares the pre-lock candidate with the under-lock live result.
A queue-bound first step compares the queued expectation with that under-lock
result. Any mismatch or lost safety predicate stops as `stale_plan` before
mutation and records `plan_binding.scope: step_admission`.

If the fixture lease is already held, the runner stops as retryable
`admission_busy`, starts no subprocess, leaves `executed_count` unchanged, and
returns a read-only workflow-agent handoff. Plan-only runs acquire no lease.
If the fixture path or non-busy lock state becomes invalid during acquisition
or under-lock validation, the runner instead stops as non-retryable
`admission_invalid`. It preserves the eligible pre-lock step as
`would_execute: true`, executes nothing, and emits a sanitized
`admission_diagnostic` without filesystem paths.

Direct `run_fig_loop` execution remains on the existing self-leased `fig_loop`
path and is never wrapped in an outer runner lease. A queue-bound first
`run_fig_loop` step temporarily stops without a subprocess as
`run_fig_loop_admission_integration_pending`; integrating that self-leased path
with queue expectations is deferred to the next slice.

Default mode is plan-only. Without `--execute`, the command emits what would be
run and does not mutate fixture source, exports, accepted state, or golden
state. Plan-only runs do not write a journal unless `--record` is passed.
Output is JSON by default; `--json` and `--format json` are accepted as
explicit output compatibility spellings.

## Execution Policy

The executable actions are allowed only when the driver attaches no
`stop_boundary`. The runner also revalidates that each shell command matches
the current fixture before executing; an allowlisted action with a mismatched
or malformed command stops as `not_executable_action`.

- `run_compile` -> `fig-agent compile <name>`
- `run_adjudicate` -> `fig-agent adjudicate <name>`
  only when `critique_adjudication.yaml` is missing
- `run_export` -> `fig-agent export <name>` only for
  that exact fixture command and only for draft generated exports where
  `acceptance_state: NOT_DECLARED`, `export_state: MISSING | STALE`, and
  `critique_state: FRESH | NOT_REQUIRED`
- `run_fig_loop` -> `fig-agent loop <name> --goal ... --json`

`run_adjudicate` is allowed only for initial scaffold; existing adjudication
files, including stale or invalid files, still require manual repair.
`run_export` is allowed only for draft fixtures whose acceptance has not yet
been declared (`acceptance_state: NOT_DECLARED`) and whose generated exports
are missing or stale. Accepted fixtures, explicitly not-accepted fixtures,
tracked-golden export state, closeout boundaries, `--force-golden`, and
`--skip-critique` remain explicit manual actions.
`/fig_loop` is allowed because it is verify-only and writes bounded run evidence
under `.scratch/fig-loop-runs/`. The runner always stops on `/fig_critique`
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
| `executable_actions` | list | current allowlist: `run_adjudicate`, `run_compile`, `run_export`, `run_fig_loop` |
| `steps` | list | driver action plus execution result for each iteration |
| `final_action` | string | last driver action |
| `final_safe_command` | string or null | last command selected by driver |
| `final_stop_boundary` | string or null | last driver stop boundary |
| `final_stop_reason` | string | runner reason for stopping |
| `executed_count` | int | number of shell commands actually run |
| `plan_binding` | object, optional | step-admission comparison with `basis: queue_first_step | live_prelock`, planned/live action and command evidence, and `matched`, `stale`, or `admission_pending` state |
| `admission_diagnostic` | object, optional | sanitized non-retryable fixture/lock diagnostic for `admission_invalid`; no filesystem paths |
| `boundary_handoff` | object, optional | present for non-`complete` stops; explanatory only |
| `journal` | object, optional | reference to the non-authoritative `.scratch/fig-run-runs/` record unless `--no-record` is used |
| `journal_error` | object, optional | recording failure details; run payload remains usable |

Step entries include the embedded `/fig_drive` JSON under `driver` so an outer
agent can inspect the exact status, blocker, and next-action evidence used for
the decision. A successful executed step may have `stop_reason: null`; the
runner then re-queries the driver for the next action.

### Run Journal

When `--execute` is passed, the CLI records each `/fig_run` payload under:

```text
.scratch/fig-run-runs/<timestamp>-<name>/
├── run_manifest.json
├── run.json
├── steps/
│   └── step_001.json
└── stop.md
```

Use `--record` to record a plan-only run. Use `--runs-root <path>` to redirect
journals in tests or dogfood runs. Use `--no-record` for stdout-only behavior,
including execute mode.

The journal is non-authoritative evidence. It exists so a later session can
inspect what the runner saw and why it stopped. It preserves the public payload,
so `safe_command` fields may appear inside `run.json` and step JSON as evidence
of what the live driver selected. Those strings are not resume commands and are
not permission to execute stale state; rerun live `/fig_status` and
`/fig_drive` before continuing.

If recording fails after a run, the CLI still prints the public run payload with
`journal_error` instead of hiding the result behind a traceback.

There is no executable `--resume` or `--resume-latest` flag. To continue after
an interruption, inspect `stop.md` only as context, or run:

```bash
fig-agent helper fig_run_journal.py <name>
```

That summary is also non-authoritative: it names the latest journal stop,
required actor, stale fixture evidence, and closeout checks, but it never emits
a replay command. Continue by rerunning live `/fig_status <name>` and
`/fig_drive <name> --mode <mode> --goal "<goal>" --dry-run`. Use
`/fig_run --execute` again only for the fresh driver-selected action.

### `boundary_handoff`

When the runner stops before `complete`, it emits an additive
`schema: figure-agent.boundary-handoff.v1` object. This object is a compact
explanation of the stop, not a second router and not permission to bypass a
boundary.

Fields:

| Field | Notes |
|---|---|
| `action` | copied from the final `/fig_drive` action |
| `stop_boundary` | copied from the final `/fig_drive` stop boundary |
| `required_actor` | one of `host_llm`, `human`, `svg_editor`, `release_operator`, `workflow_agent` |
| `blocking_reason` | compact driver/runner reason; command failures include `stderr_tail` |
| `evidence_refs` | copied from `next_action_summary` or fallback driver/runner evidence |
| `allowed_scope` | copied from `next_action_summary`, except deferred patch/source boundaries |
| `forbidden_scope` | copied from `next_action_summary`, except deferred patch/source boundaries |
| `closeout_checks` | checks to perform after the required actor acts |
| `continuation_guidance` | always says to rerun live status and driver state first |

When the final driver summary came from a `/fig_loop` `basin_detected`
checkpoint, `boundary_handoff` also includes `basin_summary` and its
`closeout_checks` begin with the basin's `recommended_step_out_actions`. Treat
this as a signal to leave the local patch loop for second-opinion review,
human art-direction/domain review, or reference/briefing contract repair before
rerunning live `/fig_loop` and `/fig_drive`.

`boundary_handoff.continuation_guidance` intentionally does not contain an
executable resume command. Resume/replay behavior is out of scope for
`/fig_run`.

Patch/source-mutation boundaries are explicitly deferred. If the final driver
action is `patch_handoff_stop`, the handoff reports
`deferred_boundary: patch_source_mutation_deferred_until_70c`, uses
`allowed_scope: ["read-only"]`, and does not surface patch edit scope.

## Stop Reasons

- `plan_only` — command would be executable, but `--execute` was not passed.
- `host_boundary` — host vision or slash command required.
- `not_executable_action` — driver selected an unsupported action, or an
  allowlisted action failed its extra safety predicate.
- `command_failed` — an executed command returned non-zero.
- `stale_plan` — the under-lock live driver action/command or safety state no
  longer matches the queued first step or direct pre-lock candidate; no mutation
  is attempted.
- `admission_busy` — the fixture admission lease is held; no subprocess starts
  and the read-only handoff may be retried from fresh live state.
- `admission_invalid` — the fixture path, lock state, or under-lock validation
  became unsafe; no subprocess starts and the boundary must be repaired before
  a new live run.
- `run_fig_loop_admission_integration_pending` — a queue-bound `run_fig_loop`
  first step is deliberately not delegated yet; direct `fig_run` keeps the
  existing self-leased path.
- `complete` — driver selected `complete`.
- `repeated_executable_action` — a successful command was followed by the same
  driver action and shell command again, so the runner stopped instead of
  repeating a no-progress loop.
- `max_steps_exceeded` — the runner hit the safety cap before state advanced to
  a boundary.

## When To Use

Use `/fig_run` when the user wants the plugin to proceed through safe mechanical
steps without asking for each compile. Use `/fig_drive --dry-run` when you only
need a recommendation. Use the lower-level slash commands directly when the
user is intentionally operating one specific stage.

`/fig_run` does not remove human gates. It only removes unnecessary manual
copy-paste for deterministic shell work the driver already selected.
`/fig_drive --mode final --dry-run` is intentionally driver-only; `/fig_run`
does not execute final mode because final readiness is an explanatory
human/release preset, not a new automation lane.
Admission success is a machine safety result only and never claims visual,
human-development, release, or publication acceptance.
