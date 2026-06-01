# Issue 100BG - Critique Adjudication CLI Fixture Path Boundary

Status: implemented

Type: mutation-surface safety, path-boundary hardening, human-decision integrity

## Problem

`critique_adjudication.py` is a write-capable helper. `scaffold` creates
`critique_adjudication.yaml`, and `sync` can refresh or recreate that file after
a fresh critique.

Before this issue, the CLI accepted fixture-like path input such as
`examples/../outside`. If the normalized outside directory contained a
`critique.md`, `scaffold --force` could write `critique_adjudication.yaml`
outside the declared `examples/<name>` fixture boundary. `sync --force` could
also enter the escaped path before failing on incidental freshness checks.

That is the wrong failure mode for a human-decision artifact. The CLI should
reject invalid fixture identity before any scaffold/sync read or write path is
constructed.

## Decision

Harden only the CLI fixture resolver. The public low-level APIs remain
path-explicit for tests and internal code that already has an authoritative
`Path`.

The CLI now accepts only:

- `<name>`;
- `examples/<name>`;
- an absolute path whose resolved target is exactly one direct child of
  `<repo-root>/examples`.

It rejects traversal-like relative paths, nested `examples/<name>/...` paths,
and absolute paths outside `<repo-root>/examples` with a controlled
`CritiqueAdjudicationError` surfaced as exit code `1`.

Invalid fixture-name validation errors are also wrapped into the same controlled
CLI error path so malformed user input cannot escape as a Python traceback.

## Tests

Covered by:

- `tests/test_critique_adjudication.py::test_cli_rejects_parent_relative_example_path_before_write[scaffold]`
- `tests/test_critique_adjudication.py::test_cli_rejects_parent_relative_example_path_before_write[sync]`
- `tests/test_critique_adjudication.py::test_cli_reports_controlled_error_for_invalid_fixture_name[scaffold]`
- `tests/test_critique_adjudication.py::test_cli_reports_controlled_error_for_invalid_fixture_name[sync]`
- existing CLI fixture-name scaffold/sync tests.

## Review Notes

- The change preserves normal fixture-name and `examples/<name>` usage.
- The change preserves absolute direct-child fixture paths for explicit local
  invocation.
- The change does not alter `build_adjudication_scaffold()`,
  `scaffold_adjudication()`, or `sync_adjudication()` path-explicit behavior.
- The guard runs before writes, so invalid fixture syntax cannot create or
  refresh adjudication state outside the fixture tree.
