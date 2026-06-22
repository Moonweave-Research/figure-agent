# Queue Runner Execute Dogfood - Issue 83

Status: completed

Issue:

- `docs/superpowers/issues/2026-05-30-issue-83-queue-runner-execute-dogfood.md`

## Purpose

Exercise the actual `/fig_queue_run --execute` path after Issue 82 documented
the plan-only operator playbook.

The goal was to verify that multi-fixture automation remains bounded:

- only workflow-agent rows are attempted;
- `--max-fixtures` limits the batch;
- blocked closeout rows stay blocked;
- `/fig_queue_run` delegates to `/fig_run`;
- repeated no-progress commands do not produce unbounded duplicate evidence.

## Pre-Fix Dogfood

Plan-only command:

```bash
uv run python3 scripts/fig_queue_run.py --mode review \
  --goal "Issue 83 queue-run execute dogfood" \
  --actor workflow_agent --max-fixtures 1
```

Result:

- planned executable: 2 (`fig3_trapping_concept`, `smoke_trap_demo`)
- planned blocked: 1 (`fig5_floating_clip_mechanism`,
  `stop_boundary:closeout_required`)
- attempted: 1 (`fig3_trapping_concept`)
- executed: false

Initial execute command:

```bash
uv run python3 scripts/fig_queue_run.py --mode review \
  --goal "Issue 83 queue-run execute dogfood" \
  --actor workflow_agent --max-fixtures 1 --execute
```

Observed defect:

- `/fig_queue_run` selected only `fig3_trapping_concept`, as intended.
- `/fig_run` executed `run_fig_loop` five times.
- Final stop reason was `max_steps_exceeded`.
- This was safe but noisy because `run_fig_loop` wrote repeated verify-only
  evidence while driver state remained the same.

## Fix

`scripts/fig_run.py` now tracks executed `(action, safe_command)` pairs during
one run. If the driver returns the same executable pair again, the runner
records a final non-executed step and stops with:

```text
repeated_executable_action
```

The boundary handoff asks the operator to inspect the repeated action and rerun
live `/fig_status` and `/fig_drive`.

## Post-Fix Dogfood

Command:

```bash
uv run python3 scripts/fig_queue_run.py --mode review \
  --goal "Issue 83 queue-run execute dogfood" \
  --actor workflow_agent --max-fixtures 1 --execute
```

Result:

| Field | Value |
|---|---|
| attempted | 1 |
| planned_executable | 2 |
| planned_blocked | 1 |
| blocked row | `fig5_floating_clip_mechanism` / `closeout_required` |
| executed_commands | 1 |
| failed | 0 |
| fixture | `fig3_trapping_concept` |
| first command | `run_fig_loop` |
| final stop reason | `repeated_executable_action` |

The final run contains two steps:

1. executed `run_fig_loop` once;
2. detected the same `run_fig_loop` command again and stopped without
   executing it.

## Verification

```bash
uv run pytest -q tests/test_fig_run.py::test_stops_after_repeated_executable_command_without_progress
# 1 passed

uv run python3 scripts/fig_queue_run.py --mode review --goal "Issue 83 queue-run execute dogfood" --actor workflow_agent --max-fixtures 1 --execute
# executed_commands: 1, failed: 0, final_stop_reason: repeated_executable_action
```

Final full verification is recorded with the commit.

```bash
uv run pytest -q tests/test_fig_run.py tests/test_fig_queue_run.py tests/test_fig_queue.py
# 57 passed

uv run ruff check scripts/fig_run.py tests/test_fig_run.py
# All checks passed

uv run pytest -q
# 1463 passed, 1 skipped, 1 xfailed, 6 warnings

git diff --check
# clean

claude plugin validate .claude-plugin/plugin.json
# passed

claude plugin validate .
# passed

claude plugin validate ../../.claude-plugin/marketplace.json
# passed
```

## Review Notes

1. Contract review: clean. `final_stop_reason` gained one additive value and
   `commands/fig_run.md` documents it.
2. Scope review: clean. The runner still refuses host, human, release,
   tracked-golden, patch, polish, and blocked closeout rows.
3. Operator review: clean. A repeated no-progress command now surfaces as a
   specific boundary instead of a generic max-step failure.

No known Issue 83 blocker remains.
