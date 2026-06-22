# Issue 71C - Non-Critique Export And Closeout Rehearsal

Status: completed

Depends on: Issue 71A

Type: AFK/HITL mixed

## Problem

Some fixtures do not require reference-grounded critique, but still have stale
or missing exports and loop closeout gaps. These are the best candidates for
proving that `/fig_run` can safely close mechanical workflow work without
touching host/human boundaries.

## Goal

Use `/fig_drive`, `/fig_run`, `/fig_closeout`, and `/fig_loop` to rehearse the
non-critique closeout path on real fixtures, while stopping at publication or
accepted/golden gates.

## Scope

In scope:

- Run `/fig_drive --mode review --dry-run` and `/fig_run --execute` only when
  the driver selects allowlisted mechanical actions.
- Run draft export only for non-accepted fixtures where `/fig_run` deems export
  safe.
- Run `/fig_closeout <name>` after mechanical work to confirm remaining steps.
- Record where `/fig_run` refuses execution because closeout or publication
  gates are human-owned.

Out of scope:

- Host critique generation.
- Accepted/golden roll-forward.
- `--force-golden`.
- Publication provenance edits.
- Source drawing edits.

## Acceptance

- A milestone records every non-critique fixture attempted, driver action,
  runner action, closeout result, and final remaining owner.
- `/fig_run` executes only allowlisted commands whose command shape matches the
  current fixture.
- Any generated exports remain ignored unless an explicitly authorized
  accepted/golden update is part of a later issue.
- `tests/test_fig_run.py`, `tests/test_fig_driver.py`, `tests/test_fig_closeout.py`,
  and full pytest pass.

## Review Questions

1. Did `/fig_run` remove copy-paste friction without crossing manual gates?
2. Did closeout distinguish mechanical stale export from human publication
   work?
3. Did any safe mechanical state still require manual command chaining?
4. Are generated artifacts excluded from the final diff?

## Completion

Completed in milestone:
`docs/milestones-archive/2026-05-29-non-critique-export-closeout-rehearsal.md`.

The rehearsal found one driver/runner contract gap and split it into
`docs/superpowers/issues/2026-05-29-issue-72-align-export-driver-runner-contract.md`.
