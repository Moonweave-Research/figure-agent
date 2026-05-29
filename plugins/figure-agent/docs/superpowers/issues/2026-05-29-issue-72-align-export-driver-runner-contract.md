# Issue 72 - Align Export Driver And Runner Contract

Status: proposed

Discovered during: Issue 71C non-critique export and closeout rehearsal

## Problem

`fig5_floating_clip_mechanism` exposed a mismatch between `/fig_drive` and
`/fig_run`:

- `/fig_drive --mode release --dry-run` selects `run_export`, emits
  `stop_boundary: null`, and provides the safe command
  `uv run python3 scripts/run_export.py fig5_floating_clip_mechanism`.
- `/fig_run --execute` refuses to run that command and reports
  `not_executable_action`.

The refusal is conservative and consistent with Issue 69: `/fig_run` only
executes draft export when `acceptance_state: NOT_DECLARED`. The fixture is
`NOT_ACCEPTED`, which means human acceptance/publication work is still visible.

The defect is not that the runner refused. The defect is that the driver made a
non-executable export look executable by returning no stop boundary.

## Goal

Make driver output and runner execution policy agree for draft export states.
An operator should be able to tell from `/fig_drive` whether `/fig_run` can
actually execute the selected export command.

## Candidate Fixes

Choose one after reviewing the current Issue 69 policy:

1. Keep runner policy strict and change `fig_driver.py` so
   `acceptance_state: NOT_ACCEPTED` export states surface an explicit stop
   boundary, likely `accepted_or_final_ready_required` or a narrower export
   approval boundary.
2. Broaden runner policy to allow non-golden draft export for `NOT_ACCEPTED`
   when `--force-golden`, accepted state, publication files, and tracked golden
   artifacts are not touched.

Option 1 is safer unless there is a strong operator need to export
`NOT_ACCEPTED` fixtures automatically.

## Scope

In scope:

- `scripts/fig_driver.py`
- `scripts/fig_run.py` only if the chosen policy requires it
- `tests/test_fig_driver.py`
- `tests/test_fig_run.py`
- command docs if public behavior changes

Out of scope:

- `--force-golden`
- accepted/golden roll-forward
- publication provenance edits
- source drawing edits
- host critique generation

## Acceptance

- A regression test covers a fixture-like state with
  `action: run_export`, `export_state: MISSING`, `critique_state:
  NOT_REQUIRED`, and `acceptance_state: NOT_ACCEPTED`.
- `/fig_drive` and `/fig_run` no longer disagree about whether the export
  command is executable.
- Existing `NOT_DECLARED` draft export execution still works.
- Accepted or tracked-golden export remains non-executable without explicit
  human approval.
- Verification includes:
  `uv run pytest -q tests/test_fig_driver.py tests/test_fig_run.py tests/test_fig_closeout.py`
  and `uv run pytest -q`.

## Review Questions

1. Does the chosen policy preserve the Issue 69 safety contract?
2. Does the driver expose a stop boundary whenever `/fig_run` would refuse?
3. Is `NOT_ACCEPTED` being treated as a human publication/acceptance state, not
   as a generic draft fixture?
4. Is the next action wording clear enough for an operator to continue without
   guessing?
