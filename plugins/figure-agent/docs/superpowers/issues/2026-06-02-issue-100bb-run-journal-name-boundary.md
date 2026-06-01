# Issue 100BB - Fig Run Journal Fixture Name Boundary

Status: implemented

Type: continuation safety, path-boundary hardening, fixture identity consistency

## Problem

`fig_run_journal.py` summarizes previous `/fig_run` journals and prints live
continuation commands such as:

- `/fig_status <name>`;
- `/fig_drive <name> --mode ... --dry-run`.

Before this issue, the helper did not validate that `name` was a single fixture
identity. Calling it with `../outside` produced a normal missing-journal JSON
summary and embedded unsafe live commands in `next_live_commands`.

The journal helper is read-only, but it is an operator-facing continuation
surface. It must not generate follow-up commands for traversal syntax.

## Decision

Reuse `fixture_identity.validate_fixture_name()` at the start of
`latest_journal_summary()`, before journal lookup, stale-evidence checks, or
`next_live_commands` generation.

The CLI catches that controlled `ValueError`, prints
`fig_run_journal.py: ...`, and exits with status `2`.

## Tests

Covered by:

- `tests/test_fig_run_journal.py::test_latest_journal_summary_rejects_unsafe_fixture_name_before_live_commands`
- `tests/test_fig_run_journal.py::test_cli_rejects_unsafe_fixture_name_cleanly`
- `tests/test_fig_run_journal.py::test_cli_does_not_mask_later_value_errors`
