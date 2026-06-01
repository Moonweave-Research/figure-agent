# Issue 100BH - Critique Lint CLI Fixture Path Boundary

Status: implemented

Type: read-only gate safety, path-boundary hardening, operator trust

## Problem

`critique_lint.py` is read-only, but it is an authority surface: operators and
other commands use its result to decide whether `critique.md` is contract-valid.

Before this issue, the CLI accepted traversal-like input such as
`examples/../outside`. If the normalized outside directory contained a valid
`critique.md`, the command could print `OK: critique lint passed for outside`.
That made an escaped path look like normal fixture truth instead of an invalid
fixture identity.

## Decision

Harden only the CLI fixture resolver. The low-level `lint_critique(Path)` API
remains path-explicit for focused tests and internal reuse.

The CLI now accepts only:

- `<name>`;
- `examples/<name>`;
- an explicit absolute path, preserved for read-only linting of ad hoc test
  fixtures.

It rejects traversal-like relative paths, nested `examples/<name>/...` paths,
and invalid fixture names before running lint. Invalid CLI input is surfaced as a normal
`BLOCKER: critique_contract: invalid fixture path...` result with exit code `1`.

## Tests

Covered by:

- `tests/test_critique_lint.py::test_lint_critique_cli_accepts_examples_fixture_path`
- `tests/test_critique_lint.py::test_lint_critique_cli_rejects_parent_relative_example_path`
- `tests/test_critique_lint.py::test_lint_critique_cli_reports_controlled_error_for_invalid_fixture_name`
- existing CLI nonzero and malformed-finding tests.

## Review Notes

- This does not change critique schema validation.
- This does not change `lint_critique(Path)` behavior.
- The normal fixture-name, `examples/<name>`, and explicit absolute-path CLI
  forms are preserved.
- The command now fails closed before an escaped critique can be reported as
  passing plugin lint.
