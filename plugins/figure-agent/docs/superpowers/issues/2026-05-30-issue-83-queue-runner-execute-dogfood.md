# Issue 83 - Queue Runner Execute Dogfood

Status: completed

Depends on:

- Issue 81 - queue batch runner
- Issue 82 - queue runner dogfood and operator playbook

Type: dogfood, runner hardening

## Problem

Issue 82 froze the plan-only queue path, but the actual
`/fig_queue_run --execute` path still needed a live dogfood pass. During the
pass, `/fig_queue_run` delegated correctly to `/fig_run`, but `/fig_run`
repeated the same `run_fig_loop` command until `max_steps_exceeded` because
the driver state did not advance after a verify-only loop checkpoint.

That behavior was safe but noisy: it created duplicate loop evidence and made
the stop reason look like a generic safety-cap failure instead of a no-progress
repeat.

## Goal

Dogfood `/fig_queue_run --execute` with a bounded real fixture run and harden
`/fig_run` so repeated executable actions stop after one successful execution.

## Scope

- Run current real queue and workflow-agent command plan.
- Execute at most one workflow-agent fixture through `/fig_queue_run`.
- Add a runner stop reason for repeated executable action/command pairs.
- Document the live dogfood outcome.
- Do not execute host critique, release/golden approval, SVG polish, source
  patches, or generated export mutation.

## Implementation

Code:

- `scripts/fig_run.py`
  - Adds `repeated_executable_action`.
  - Tracks executed `(action, safe_command)` signatures within one run.
  - If the live driver returns the same executable signature again, records a
    non-executed final step and emits a boundary handoff instead of replaying
    the command.

Docs:

- `commands/fig_run.md`
  - Documents `repeated_executable_action`.
- `docs/milestones/2026-05-30-queue-runner-execute-dogfood.md`
  - Records plan-only, failed pre-fix dogfood, fixed dogfood, and verification.

Tests:

- `tests/test_fig_run.py`
  - Covers repeated `run_fig_loop` stopping after one execution.

## Dogfood Result

Current queue still has two executable workflow-agent rows:

- `fig3_trapping_concept` -> `run_fig_loop`
- `smoke_trap_demo` -> `run_fig_loop`

`fig5_floating_clip_mechanism` remains blocked by
`stop_boundary: closeout_required` and is not attempted.

The fixed execute dogfood:

```bash
uv run python3 scripts/fig_queue_run.py --mode review \
  --goal "Issue 83 queue-run execute dogfood" \
  --actor workflow_agent --max-fixtures 1 --execute
```

Result:

- attempted: 1
- executed_commands: 1
- failed: 0
- planned_blocked: 1
- final fixture: `fig3_trapping_concept`
- final stop reason: `repeated_executable_action`

No source, export, accepted, golden, publication, or SVG state was mutated.

## Review

1. Root-cause review: clean. The bug was not in queue filtering; it was in
   `/fig_run` replaying a state-preserving command when the driver selected the
   same command again.
2. Safety review: clean. The new stop is stricter than the prior behavior and
   prevents duplicate execution while preserving live driver revalidation.
3. Integration review: clean. `/fig_queue_run` still delegates to `/fig_run`;
   the public run schema remains additive because `final_stop_reason` is an
   open string field in existing consumers.

No known Issue 83 blocker remains.
