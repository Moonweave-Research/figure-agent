# Issue 68: Safe Adjudication Runner Expansion

Status: completed

Depends on: Issue 67 safe loop runner expansion

## Problem

`/fig_run --execute` can now close compile and verify-only loop steps, but it
still stops on `run_adjudicate`. That is correct for stale or invalid existing
adjudication files because automatic rewrite could overwrite human decisions.
It is unnecessarily manual when the adjudication file is simply missing.

`critique_adjudication.py scaffold` already refuses to overwrite existing files
without `--force`, so the safe automation slice is narrow: execute initial
scaffold only when `examples/<name>/critique_adjudication.yaml` does not exist.

## Decision

Add `run_adjudicate` to `/fig_run` executable actions only under this extra
precondition:

- driver action is `run_adjudicate`
- `stop_boundary` is null
- selected command is a shell command
- `examples/<name>/critique_adjudication.yaml` is missing

If the file exists, even if stale or invalid, `/fig_run` stops with
`not_executable_action`. Manual repair or explicit force remains required.

## Scope

Implement:

- Runner-side safety predicate for `run_adjudicate`.
- Tests for missing-file execution, existing-file non-execution, and failure.
- Docs update for `/fig_run`, README, SKILL, issue, and milestone.

Do not implement:

- automatic `--force`
- automatic `sync`
- stale adjudication repair
- invalid adjudication repair
- critique mutation
- export/release/accepted/golden automation

## Acceptance

- Missing `critique_adjudication.yaml` permits `run_adjudicate` execution.
- Existing `critique_adjudication.yaml` blocks `run_adjudicate` execution.
- A failed scaffold command stops with `command_failed`.
- `executable_actions` includes `run_compile`, `run_fig_loop`, and
  `run_adjudicate`.
- `run_export` remains non-executable.

## Verification

- `uv run pytest -q tests/test_fig_run.py tests/test_fig_driver.py tests/test_critique_adjudication.py` — 194 passed
- `uv run ruff check scripts/fig_run.py tests/test_fig_run.py` — passed
- `git diff --check` — passed

## Review Notes

1. Contract review: clean. `run_adjudicate` only executes when
   `critique_adjudication.yaml` is missing and `stop_boundary` is null.
2. Scope review: clean. Existing adjudication files, stale files, invalid files,
   `--force`, and `sync` remain manual.
3. Test review: clean. Tests cover missing scaffold execution, existing-file
   stop, failure stop, and continued `run_export` non-execution.
