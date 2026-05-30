# Queue Table Next Step - Issue 86

Status: completed

Issue:

- `docs/superpowers/issues/2026-05-30-issue-86-queue-table-next-step.md`

## Purpose

Make the default `/fig_queue` table actionable for operators who are not
reading JSON.

After Issue 85, blocked rows had good `operator_handoff` objects in JSON, but
the plain table could still display the blocked driver `safe_command` as the
last column. This slice changes the table to display `next_step` and
`next_command` instead.

## Contract

Table columns are now:

```text
fixture actor action stop_boundary first_blocker next_step next_command
```

Rules:

- Executable workflow-agent rows show `Executable workflow-agent command.` and
  the driver `safe_command`.
- Blocked rows show the handoff `next_step`.
- Blocked rows show the handoff `command`, if any.
- Blocked rows without a safe handoff command show `-`.

## Dogfood

```bash
uv run python3 scripts/fig_queue.py --mode review \
  --goal "Issue 86 queue table next-step dogfood" \
  --actor workflow_agent
```

Observed:

- `fig3_trapping_concept` and `smoke_trap_demo` remain executable
  `run_fig_loop` rows.
- `fig5_floating_clip_mechanism` remains blocked by `closeout_required`.
- The blocked row's `next_command` is now:
  `uv run python3 scripts/fig_closeout.py fig5_floating_clip_mechanism --json`
- The blocked row no longer exposes `run_export.py` as the table command.

## Verification

```bash
uv run pytest -q tests/test_fig_queue.py::test_print_table_outputs_rows_and_summary tests/test_fig_queue.py::test_print_table_uses_handoff_command_for_blocked_rows
# 2 passed

uv run pytest -q tests/test_fig_queue.py tests/test_fig_queue_run.py tests/test_fig_run.py
# 59 passed

uv run pytest -q
# 1465 passed, 1 skipped, 1 xfailed, 6 warnings

uv run ruff check .
# All checks passed

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

1. Scope: clean. This is table output only; queue JSON and execution policy are
   unchanged.
2. Safety: clean. The table reduces accidental execution of blocked commands.
3. Usability: clean. Operators can see the next action without adding
   `--command-plan --json`.

No known Issue 86 blocker remains.
