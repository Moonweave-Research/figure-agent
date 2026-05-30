# Issue 85 - Blocked Row Operator Handoff

Status: completed

Depends on:

- Issue 82 - queue runner dogfood and operator playbook
- Issue 83 - queue runner execute dogfood
- Issue 84 - queue runner max-2 execute dogfood

Type: operator UX, queue contract hardening

## Problem

The queue runner now executes the deterministic workflow-agent subset safely,
but blocked rows still require the operator to infer the next action from
`required_actor`, `blocking_source`, `stop_boundary`, and `reason`.

That is workable for developers, but not a good operating surface. The queue
should make blocked work explicit without making it executable.

## Goal

Add a compact operator handoff to every blocked command-plan row.

## Scope

- Add `operator_handoff` to `command_plan.blocked[]`.
- Keep `/fig_queue` read-only.
- Keep `/fig_queue_run` execution limited to `command_plan.executable[]`.
- Do not add a new command.
- Do not execute host critique, release/golden approval, human decisions,
  source patches, SVG polish, or closeout-blocked exports.

## Public Contract

Blocked rows now include:

```yaml
operator_handoff:
  schema: figure-agent.queue-operator-handoff.v1
  fixture: <name>
  required_actor: workflow_agent | host_llm | human | release_operator | svg_editor
  next_step: "<operator-facing next action>"
  command: "<optional command or slash command>"
  reason: "<blocked reason>"
  allowed_scope: [...]
  forbidden_scope: [...]
  closeout_checks: [...]
```

The object is advisory. It does not change execution eligibility.

## Implemented Handoffs

- `host_llm`: run `/fig_critique <name>`, then lint and sync/scaffold
  adjudication.
- `workflow_agent` with `stop_boundary:closeout_required`: run read-only
  `fig_closeout.py <name> --json` before trying export again.
- `human`: record the required human decision.
- `release_operator`: perform explicit release/golden review; never force
  golden implicitly.
- `svg_editor`: complete SVG polish handoff outside queue automation.
- fallback: inspect the blocked row and rerun live driver state.

## Dogfood Result

Current workflow-agent command plan includes one blocked row:

- `fig5_floating_clip_mechanism` / `run_export` /
  `stop_boundary:closeout_required`

Its handoff recommends:

```bash
uv run python3 scripts/fig_closeout.py fig5_floating_clip_mechanism --json
```

Current host-LLM command plan includes two blocked critique rows:

- `n3_trial_01_trap_depth`
- `n3_trial_02_actuation_sequence`

Their handoffs recommend `/fig_critique <name>` and list critique/adjudication
closeout checks.

## Review

1. Contract review: clean. The handoff is additive to blocked rows and does
   not alter executable rows.
2. Safety review: clean. Blocked rows still remain blocked; no handoff command
   is executed by `/fig_queue_run`.
3. Operator review: clean. The queue now tells the next actor what to do and
   what not to touch.

No known Issue 85 blocker remains.
