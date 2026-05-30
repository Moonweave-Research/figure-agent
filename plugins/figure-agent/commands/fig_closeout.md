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
- `next_action_summary`
- `blocking_step_ids`
- `status`
- `steps[]`

`next_action_summary` follows the same shared compact shape as `/fig_status`,
`/fig_drive`, and `/fig_loop`. It points at the first `needs_action` step, or
the first blocked step when no copyable command is safe. It is read-only
compression of the detailed `steps[]` list; `steps[]` remains the debugging
surface.

Each step has:

- `id`: `text_boundary_checks`, `compile`, `critique`, `adjudication`,
  `export`, or `loop_rerun`
- `state`: `passed`, `needs_action`, `blocked`, or `not_required`
- `reason`
- `command`: a copyable slash command when one safe next command exists, otherwise `null`
- `evidence_path`
- `evidence`: structured context such as `blocked_by`, `repair_target`, or
  `approval_command`

The command is read-only. It does not run `text_boundary_spec_helper.py`,
compile, critique, adjudicate, export, run `/fig_loop`, edit source, mutate
`.scratch/`, or change accepted/golden state. Use it after an outer agent or
human patches exactly one target selected by `/fig_loop`.

If `spec.yaml.text_boundary_layout` exists, the `text_boundary_checks` step
verifies that generated `text_boundary_checks` are present and current. When
they are missing or stale, the report emits:

```bash
uv run python3 scripts/text_boundary_spec_helper.py examples/<name> --write
```

Run that helper, inspect the spec diff, then continue to `/fig_compile`.

The final `loop_rerun` step is blocked until text-boundary sync, compile,
critique, adjudication, and export prerequisites are closed. If the export
state is `TRACKED_GOLDEN`, the report marks export as blocked with an
`approval_command` in evidence instead of putting `--force-golden` in
`next_action`; rolling forward golden artifacts remains a deliberate manual
approval checkpoint.

`/fig_closeout` does not resume `.scratch/fig-run-runs/` journals. After a
runner interruption, use the journal only to understand the previous stop, then
rerun live `/fig_status`, `/fig_drive`, or `/fig_closeout` as appropriate.

Exit code is `0` only when `closeout_complete` is true. Incomplete closeout
returns `1` so automation can stop before overclaiming.
