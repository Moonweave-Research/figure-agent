# Issue 17: Driver and Status State-Machine Refactor

**Date:** 2026-05-21 KST
**Status:** in progress through Issue 17B
**Type:** parent issue / architecture hardening

## Problem

`figure-agent` now has enough loop, critique, polish, and release gates that
the command-facing state machines are becoming the next source of risk.

Current size snapshot:

- `scripts/fig_driver.py`: 816 lines
- `scripts/status.py`: 898 lines
- `tests/test_fig_driver.py`: 1186 lines
- `tests/test_status.py`: 2851 lines

The issue is not line count alone. The risk is that unrelated policies now sit
next to each other: CLI JSON shape, safe command text, loop checkpoint parsing,
publication gate release blocking, closeout routing, polish routing, and status
next-hint selection. New slices such as editorial routing should not keep
adding policy directly to `fig_driver.py` or `status.py`.

## Design Direction

Keep public slash-command behavior stable. Extract focused helper modules
behind small interfaces, each with targeted tests, so the top-level scripts stay
command-facing controllers.

Do not rewrite the whole state machine at once. This is a series of
behavior-preserving slices.

## Issue Breakdown

### Issue 17A: Driver Loop Checkpoint Adapter Extraction

**Status:** implemented

Extract `.scratch/fig-loop-runs` checkpoint parsing/currentness selection from
`fig_driver.py` into `scripts/fig_driver_checkpoint.py`.

Why first:

- It is self-contained and read-only.
- It already has a clear concept: latest current `/fig_loop` checkpoint.
- It is used by both review and polish mode.
- It is easy to regression-test without changing public JSON behavior.

Acceptance criteria:

- [x] New module exposes `latest_loop_checkpoint(repo_root, name, example_dir)`.
- [x] Malformed JSON, wrong fixture, missing stop reason, stale checkpoint, and
  latest-current selection are covered by focused tests.
- [x] `fig_driver.py` delegates checkpoint discovery to the module.
- [x] Existing `tests/test_fig_driver.py` still pass.
- [x] No public driver action, stop-boundary, or JSON field changes.

### Issue 17B: Driver Command Text Adapter

**Status:** implemented

Move safe command construction (`/fig_critique`, compile, adjudicate,
`/fig_loop`, export) into a tiny helper module. This reduces duplicated command
format knowledge and keeps shell quoting tests local to that module.

Acceptance criteria:

- [x] New module exposes command string helpers for compile, critique,
  adjudication scaffold, fig_loop, and export.
- [x] `fig_loop` goal shell quoting is covered by focused tests.
- [x] `fig_driver.py` delegates safe-command text construction to the module.
- [x] Existing `tests/test_fig_driver.py` still pass.
- [x] No public driver action, stop-boundary, or JSON field changes.

### Issue 17C: Status Next-Hint Policy Extraction

**Status:** future

Extract the stage-specific `next` selection logic from `status.py` into a
helper module that accepts the already-computed state vector plus freshness
substates. This is higher-risk than 17A because it touches many stage branches,
so it should happen only after adding focused regression tests for next-hint
precedence.

### Issue 17D: Status Final/Publication Gate Adapter Boundary Review

**Status:** future

Review whether final-artifact and publication-gate computations should stay as
adapters called by `status.py`, or whether the status vector builder needs a
smaller interface for these release surfaces.

## Non-Goals

- No behavior changes to `/fig_status`, `/fig_drive`, `/fig_loop`, export,
  accepted state, golden state, or final artifacts.
- No rewrite of `status.py` in one large diff.
- No broad test fixture migration.
- No new dependencies.

## Verification Floor

Each slice must run:

- targeted tests for the extracted module;
- relevant existing caller tests;
- `uv run ruff check .`;
- `git diff --check`;
- local CI fast path: `uv run pytest -q -m "not render"`;
- full `uv run pytest -q` before push or merge.
