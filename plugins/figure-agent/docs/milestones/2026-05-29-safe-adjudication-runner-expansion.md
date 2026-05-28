# Safe Adjudication Runner Expansion

Date: 2026-05-29

## Summary

Issue 68 expands `/fig_run --execute` to run initial adjudication scaffolding
only when `critique_adjudication.yaml` is missing. This removes another manual
copy-paste step while preserving the human-decision safety boundary.

The runner still refuses to repair or overwrite existing adjudication files.
Stale, invalid, or shape-changed adjudication remains a manual review action.

## Behavior

- `run_adjudicate` is executable only when:
  - `stop_boundary` is null,
  - the command is a shell command,
  - `examples/<name>/critique_adjudication.yaml` does not exist.
- Existing adjudication files block execution even if the driver selected
  `run_adjudicate`.
- Failed scaffold execution stops with `command_failed`.
- Successful scaffold execution triggers a driver re-query.
- `run_export` remains non-executable.

## Review Notes

1. Contract/schema review: clean. The runner does not call `--force` or `sync`.
2. Scope containment review: clean. Existing human decisions cannot be
   overwritten by the runner.
3. Test/integration review: clean. New tests cover missing-file execution,
   existing-file stop, scaffold failure, and export non-execution.

## Verification

- `uv run pytest -q tests/test_fig_run.py tests/test_fig_driver.py tests/test_critique_adjudication.py` — 194 passed
- `uv run ruff check scripts/fig_run.py tests/test_fig_run.py` — passed
- `git diff --check` — passed

No known Issue 68 plugin blocker remains.
