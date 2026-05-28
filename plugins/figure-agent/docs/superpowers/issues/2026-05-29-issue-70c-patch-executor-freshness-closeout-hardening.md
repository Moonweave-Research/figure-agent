# Issue 70C: Patch Executor Freshness And Pending-Closeout Hardening

Status: proposed

Depends on: Issue 70A guided autonomy readiness matrix

Type: AFK

## Problem

The patch executor is the only existing source-mutating path in the plugin. It
is deliberately opt-in and diff-driven, but it currently selects the latest
loop run by manifest mtime. Driver checkpoint reading has stronger protections:
it ignores loop checkpoints older than fixture evidence. Patch execution should
not be weaker than read-only driver routing.

Before any guided-autonomy work exposes patch execution more prominently, the
executor needs checkpoint freshness and pending-closeout hardening.

## What To Build

Harden `fig_loop_patch_executor.py` so it refuses to apply a patch when the
selected loop run is stale relative to fixture evidence or when a prior patch
apply record in that run still requires closeout.

The freshness rule should align with `fig_driver_checkpoint.py` where possible:

- ignore or reject loop runs older than relevant fixture evidence;
- require the loop run fixture to match the requested fixture;
- reject malformed or missing iteration records;
- reject a run if a prior `patch_apply_*.json` says `closeout_required: true`
  and no newer closeout/loop evidence proves closure.

## Scope

In scope:

- Patch executor freshness check.
- Pending-closeout refusal.
- Tests for stale loop run, newer adjudication/critique/source evidence,
  malformed run, pending closeout, and clean current run.

Out of scope:

- Adding patch execution to `/fig_run`.
- LLM-generated patches.
- Multi-target patches.
- Expanding auto-patch eligibility.
- Changing patch handoff schema.

## Acceptance

- The executor refuses stale loop checkpoints.
- The executor refuses when a previous patch apply still requires closeout.
- Existing safe patch executor tests remain green.
- Error messages name the blocking evidence path.
- No source mutation occurs in failure cases.

## Verification

- `uv run pytest -q tests/test_fig_loop_patch_executor.py tests/test_fig_driver_checkpoint.py`
- `uv run ruff check scripts/fig_loop_patch_executor.py tests/test_fig_loop_patch_executor.py tests/test_fig_driver_checkpoint.py`
- `git diff --check`

## Review Questions

1. Is source mutation at least as freshness-safe as read-only driver routing?
2. Can stale loop evidence trigger a patch?
3. Can a second patch start before closeout is complete?
4. Are refusal messages actionable?
