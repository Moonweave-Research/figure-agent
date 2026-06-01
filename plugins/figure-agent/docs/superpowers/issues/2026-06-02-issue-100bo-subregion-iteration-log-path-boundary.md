# Issue 100BO - Subregion Iteration Log CLI Fixture Path Boundary

Status: implemented

Type: subregion workflow safety, path-boundary hardening, mutation containment

## Problem

`subregion_iteration_log.py` writes or appends a fixture-local
`subregion_iteration_log.md` used by critique briefs and loop handoff context.

Before this issue, the CLI accepted traversal-like relative paths such as
`examples/../outside`. It also accepted an existing single-component relative
directory such as `outside`. If that outside fixture existed:

- `--template ... --write-template` wrote `subregion_iteration_log.md` there;
- `--append ...` appended a new iteration row there.

Both paths could create or mutate subregion workflow state outside the declared
`examples/<name>` fixture tree.

## Decision

Harden only the CLI resolver. Lower-level APIs such as
`subregion_iteration_log_template(Path)`,
`write_subregion_iteration_log(Path, text)`, and
`append_iteration_row(Path, ...)` remain path-explicit for tests and internal
callers.

The CLI now accepts:

- `<name>`;
- `examples/<name>`;
- an explicit absolute path.

Fixture names resolve under `examples/<name>`. Existing relative directories
outside `examples/` are rejected unless passed as explicit absolute paths.

It rejects traversal-like relative paths, nested `examples/<name>/...` paths,
existing outside-relative paths, and invalid fixture names before writing or
appending the log. Invalid input is reported as a controlled
`subregion_iteration_log.py: invalid fixture path...` error with exit code `2`.

## Tests

Covered by:

- `tests/test_subregion_iteration_log.py::test_cli_template_rejects_parent_relative_fixture_before_writing`
- `tests/test_subregion_iteration_log.py::test_cli_append_rejects_existing_relative_dir_outside_examples`
- `tests/test_subregion_iteration_log.py::test_cli_write_template_and_append_are_reloadable`

The first two tests reproduced pre-fix bugs: `examples/../outside
--write-template` returned exit code `0` and wrote a log, while `--append
outside` appended a row to an outside-relative log.

## Review Notes

- Both write-capable CLI modes fail closed before output path allocation.
- The documented `scripts/subregion_iteration_log.py --template
  examples/<name> --write-template` and `--append examples/<name>` forms remain
  valid.
- Explicit absolute paths remain available for controlled tests and ad hoc
  direct-path reviews.
- No subregion parser, critique brief, loop, status, driver, accepted, golden,
  or publication behavior changed.
