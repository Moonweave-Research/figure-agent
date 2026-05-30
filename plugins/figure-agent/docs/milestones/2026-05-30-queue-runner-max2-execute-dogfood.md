# Queue Runner Max-2 Execute Dogfood - Issue 84

Status: completed

Issue:

- `docs/superpowers/issues/2026-05-30-issue-84-queue-runner-max2-execute-dogfood.md`

## Purpose

Validate the queue runner beyond a single fixture by executing the current
workflow-agent batch with `--max-fixtures 2`.

This milestone checks that the operator stack remains bounded after Issue 83's
repeated-action hardening:

- `/fig_queue_run` only attempts rows from the executable command plan;
- blocked closeout rows remain blocked;
- each fixture delegates to `/fig_run`;
- no fixture replays the same no-progress loop command.

## Commands

Plan-only:

```bash
uv run python3 scripts/fig_queue_run.py --mode review \
  --goal "Issue 84 queue-run execute max2 dogfood" \
  --actor workflow_agent --max-fixtures 2
```

Execute:

```bash
uv run python3 scripts/fig_queue_run.py --mode review \
  --goal "Issue 84 queue-run execute max2 dogfood" \
  --actor workflow_agent --max-fixtures 2 --execute
```

## Evidence

Plan-only result:

| Field | Value |
|---|---:|
| attempted | 2 |
| blocked | 1 |
| planned_executable | 2 |
| planned_blocked | 1 |
| executed_commands | 0 |
| failed | 0 |

Executable rows:

| Fixture | Action |
|---|---|
| `fig3_trapping_concept` | `run_fig_loop` |
| `smoke_trap_demo` | `run_fig_loop` |

Blocked row:

| Fixture | Action | Reason |
|---|---|---|
| `fig5_floating_clip_mechanism` | `run_export` | `stop_boundary:closeout_required` |

Execute result:

| Field | Value |
|---|---:|
| attempted | 2 |
| blocked | 1 |
| planned_executable | 2 |
| planned_blocked | 1 |
| executed_commands | 2 |
| failed | 0 |

Per fixture:

| Fixture | Executed count | Final stop reason |
|---|---:|---|
| `fig3_trapping_concept` | 1 | `repeated_executable_action` |
| `smoke_trap_demo` | 1 | `repeated_executable_action` |

Both boundary handoffs explained that the same executable action and command
was selected again after a successful run, so the runner stopped to avoid
no-progress replay.

## Verification

```bash
uv run python3 scripts/fig_queue_run.py --mode review --goal "Issue 84 queue-run execute max2 dogfood" --actor workflow_agent --max-fixtures 2
# attempted: 2, planned_executable: 2, planned_blocked: 1, failed: 0

uv run python3 scripts/fig_queue_run.py --mode review --goal "Issue 84 queue-run execute max2 dogfood" --actor workflow_agent --max-fixtures 2 --execute
# attempted: 2, executed_commands: 2, failed: 0
# both runs final_stop_reason: repeated_executable_action
```

Final verification:

```bash
uv run pytest -q tests/test_fig_run.py tests/test_fig_queue_run.py tests/test_fig_queue.py
# 57 passed

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

1. Scope containment: clean. No source/export/accepted/golden/publication/SVG
   files were changed.
2. Safety: clean. The closeout-blocked export row stayed blocked.
3. Operator usability: clean. The compact result makes the batch outcome clear
   without requiring manual inspection of every nested JSON field.

No known Issue 84 blocker remains.
