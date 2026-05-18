---
description: Read-only post-patch checklist for compile, critique, adjudication, export, and loop rerun freshness.
---

Inspect whether a patched figure has completed the required closeout steps.

**Usage**: `/fig_closeout <name>`

Run from the plugin root:

```bash
uv run python3 scripts/fig_closeout.py <name>
```

For automation:

```bash
uv run python3 scripts/fig_closeout.py <name> --json
```

The JSON report has schema `figure-agent.closeout.v1` and includes:

- `closeout_complete`
- `next_action`
- `blocking_step_ids`
- `status`
- `steps[]`

Each step has:

- `id`: `compile`, `critique`, `adjudication`, `export`, or `loop_rerun`
- `state`: `passed`, `needs_action`, `blocked`, or `not_required`
- `reason`
- `command`: a copyable slash command when one safe next command exists, otherwise `null`
- `evidence_path`
- `evidence`: structured context such as `blocked_by`, `repair_target`, or
  `approval_command`

The command is read-only. It does not compile, critique, adjudicate, export,
run `/fig_loop`, edit source, mutate `.scratch/`, or change accepted/golden
state. Use it after an outer agent or human patches exactly one target selected
by `/fig_loop`.

The final `loop_rerun` step is blocked until compile, critique, adjudication,
and export prerequisites are closed. If the export state is `TRACKED_GOLDEN`,
the report marks export as blocked with an `approval_command` in evidence
instead of putting `--force-golden` in `next_action`; rolling forward golden
artifacts remains a deliberate manual approval checkpoint.

Exit code is `0` only when `closeout_complete` is true. Incomplete closeout
returns `1` so automation can stop before overclaiming.
