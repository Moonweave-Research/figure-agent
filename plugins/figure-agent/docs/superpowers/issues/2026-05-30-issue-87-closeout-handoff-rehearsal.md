# Issue 87 - Closeout Handoff Rehearsal

Status: completed

Depends on:

- Issue 85 - blocked row operator handoff
- Issue 86 - queue table next step

Type: operator rehearsal, UX hardening

## Problem

The queue table now recommends `fig_closeout.py <name> --json` for
`closeout_required` rows. That command is read-only, but it intentionally exits
with code `1` when closeout is incomplete. Without saying that in the queue
handoff, an operator can mistake the expected incomplete-closeout signal for a
tool failure.

## Goal

Rehearse the closeout handoff on the current real blocked fixture and make the
handoff explicit about how to interpret `fig_closeout.py` output.

## Scope

- Run the current workflow-agent queue.
- Run the read-only closeout handoff command for
  `fig5_floating_clip_mechanism`.
- Add closeout handoff checks that tell operators to read JSON even when exit
  code is `1`, follow `closeout.next_action`, and rerun `/fig_queue`.
- Do not run export, mutate generated artifacts, accept/golden state,
  publication state, SVG, source, or critique files.

## Result

The handoff now includes:

```yaml
closeout_checks:
  - read JSON output even when exit code is 1
  - follow closeout.next_action
  - rerun /fig_queue after resolving the blocked row
```

The live rehearsal command:

```bash
uv run python3 scripts/fig_closeout.py fig5_floating_clip_mechanism --json
```

returned exit `1` with controlled JSON:

- `closeout_complete: false`
- `blocking_step_ids: ["export", "loop_rerun"]`
- `next_action: /fig_export fig5_floating_clip_mechanism`
- export step state: `needs_action`
- loop rerun step state: `blocked`

That means the handoff command worked: it did not mutate anything, and it
explained the next non-read-only action instead of trying to execute it.

## Review

1. Contract review: clean. Handoff remains advisory and does not make
   closeout-blocked rows executable.
2. Safety review: clean. The rehearsal stopped before export and did not touch
   protected states.
3. Operator review: clean. The expected non-zero closeout exit is now called
   out in the queue handoff.

No known Issue 87 blocker remains.
