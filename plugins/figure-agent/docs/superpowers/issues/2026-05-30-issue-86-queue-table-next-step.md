# Issue 86 - Queue Table Next Step

Status: completed

Depends on:

- Issue 85 - blocked row operator handoff

Type: operator UX

## Problem

Issue 85 added `operator_handoff` to blocked JSON rows, but the default
human-readable `/fig_queue` table still showed only the driver-selected
`safe_command`. For blocked rows such as `closeout_required`, that could show a
blocked `run_export` command even though the correct operator action is a
read-only closeout inspection.

## Goal

Make the default `/fig_queue` table show the actual next operator step.

## Scope

- Add `next_step` and `next_command` columns to the table output.
- Use handoff policy for blocked rows.
- Use the driver safe command for executable workflow-agent rows.
- Do not change JSON schema or execution eligibility.
- Do not change `/fig_queue_run --execute` behavior.

## Implementation

- `scripts/fig_queue.py`
  - Adds `_table_next_step()`.
  - Adds `_table_next_command()`.
  - Updates `print_table()` header and row rendering.
- `tests/test_fig_queue.py`
  - Covers host LLM next-step table output.
  - Covers closeout-blocked rows showing `fig_closeout.py`, not the blocked
    `run_export.py` command.
- `commands/fig_queue.md`
  - Documents the table behavior.

## Dogfood Result

```bash
uv run python3 scripts/fig_queue.py --mode review \
  --goal "Issue 86 queue table next-step dogfood" \
  --actor workflow_agent
```

The `fig5_floating_clip_mechanism` row now shows:

- `next_step`: run read-only closeout inspection before continuing automation.
- `next_command`:
  `uv run python3 scripts/fig_closeout.py fig5_floating_clip_mechanism --json`

The blocked `run_export.py` command is no longer shown as the copyable table
command.

## Review

1. Contract review: clean. JSON output remains unchanged except for existing
   Issue 85 handoff support.
2. Safety review: clean. The table now hides blocked driver commands from the
   copyable next-command position.
3. Operator review: clean. The default table is useful without requiring
   `--json`.

No known Issue 86 blocker remains.
