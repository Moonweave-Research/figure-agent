# Issue 70D: Fig Run Journal Contract

Status: implemented

Depends on: Issues 70A and 70B

Type: AFK, conditional

## Problem

`/fig_run` emits stdout JSON only. That may be enough if 70A shows stop/resume
confusion is rare. If 70A and 70B show repeated multi-session continuity
problems, the runner needs a gitignored journal similar to `/fig_loop`.

## What To Build

Add a runner journal under `.scratch/fig-run-runs/<timestamp>-<name>/`.
70B dogfood justified this as continuity evidence: the handoff packet is useful,
but a later session still needs a stable record of what `/fig_run` saw and why
it stopped. The journal persists the public `/fig_run` payload and boundary
handoff output without becoming authoritative workflow state.

Suggested files:

- `run_manifest.json`
- `run.json`
- `steps/step_001.json`
- `stop.md`

Implementation should live in a helper module so `fig_run.py` remains a
controller.

## Required Currentness Rule

The journal is evidence, not authority:

- fresh `/fig_drive` state always decides next action;
- old journals cannot replay commands;
- recorded `safe_command` fields are evidence-only because the journal
  preserves the public payload;
- any future resume feature must revalidate current status and driver output;
- journal currentness must be explicit before any `--resume` flag exists.

## Scope

In scope:

- Journal writer.
- `--runs-root <path>` for tests.
- `--record` to opt into plan-mode recording.
- `--no-record` to preserve stdout-only behavior for execute callers that do
  not want journal writes.
- `.scratch/fig-run-runs/` gitignore coverage.

Out of scope:

- `--resume` or command replay.
- Reading chat history.
- Storing images or generated exports.
- Changing `/fig_loop` journal schema.

## Acceptance

- A run journal can be written and inspected.
- Tests can redirect the journal to a temp directory.
- Existing stdout JSON remains backward compatible.
- Journals cannot be used to skip a fresh driver re-query.
- Generated journals are not committed.
- Plan-only remains no-write by default unless `--record` is explicit.
- Recording failure must not hide the public run payload after execution.

## Verification

- `uv run pytest -q tests/test_fig_run.py`
- `uv run ruff check scripts/fig_run.py tests/test_fig_run.py`
- `git diff --check`

## Review Questions

1. Did 70A/70B prove this is needed?
2. Does the journal create hidden state?
3. Are old journals clearly non-authoritative?
4. Is the helper module boundary clean?
