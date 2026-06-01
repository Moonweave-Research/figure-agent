# Issue 100BL - SVG Polish Executor CLI Fixture Path Boundary

Status: implemented

Type: SVG polish safety, path-boundary hardening, mutation containment

## Problem

`svg_polish_executor.py` is the direct SVG polish recipe executor. In dry-run
mode it resolves recipe operations, and with `--write` it writes:

- `polish/<name>.polished.svg`.

Before this issue, the CLI accepted traversal-like relative paths such as
`examples/../outside`. It also accepted an existing single-component relative
directory such as `outside`. If that outside fixture contained a fresh recipe,
`--write` applied the recipe and wrote the polished SVG outside the declared
`examples/<name>` fixture tree.

## Decision

Harden only the CLI resolver. Lower-level APIs such as
`plan_svg_polish(Path, example_dir=Path)` and
`apply_svg_polish(Path, example_dir=Path)` remain path-explicit for tests and
internal callers.

The CLI now accepts:

- `<name>`;
- `examples/<name>`;
- an explicit absolute path.

Fixture names resolve under `examples/<name>`. Existing relative directories
outside `examples/` are rejected unless passed as explicit absolute paths.

It rejects traversal-like relative paths, nested `examples/<name>/...` paths,
existing outside-relative paths, and invalid fixture names before recipe
loading, dry-run planning, or `--write` can run. Invalid input is reported as a
controlled `svg_polish_executor.py: invalid fixture path...` error with exit
code `1`.

## Tests

Covered by:

- `tests/test_svg_polish_executor.py::test_cli_write_rejects_parent_relative_fixture_before_writing`
- `tests/test_svg_polish_executor.py::test_cli_write_rejects_existing_relative_dir_outside_examples`
- `tests/test_svg_polish_executor.py::test_cli_write_accepts_relative_example_dir`

The first two tests reproduced pre-fix bugs: `examples/../outside --write` and
`outside --write` returned exit code `0` and wrote
`polish/outside.polished.svg` when the escaped or outside-relative fixture
contained a fresh recipe.

## Review Notes

- The mutation-capable `--write` path now fails closed before recipe loading or
  output path allocation.
- The documented `scripts/svg_polish_executor.py examples/<name> --write` form
  remains valid.
- Explicit absolute paths remain available for controlled tests and ad hoc
  direct-path reviews.
- No SVG polish recipe schema, delta generation, handoff manifest, status,
  driver, accepted, golden, or publication behavior changed.
