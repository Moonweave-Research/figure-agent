# Issue 100BM - SVG Polish Recipe CLI Fixture Path Boundary

Status: implemented

Type: SVG polish starter safety, path-boundary hardening, mutation containment

## Problem

`svg_polish_recipe.py --template` prints a starter recipe for one fixture, and
`--write-template` writes:

- `polish/svg_polish_recipe.yaml`.

Before this issue, the CLI accepted traversal-like relative paths such as
`examples/../outside`. It also accepted an existing single-component relative
directory such as `outside`. If that outside fixture had the required SVG
inputs, `--write-template` wrote a recipe starter outside the declared
`examples/<name>` fixture tree.

## Decision

Harden only the `--template` CLI resolver. Lower-level APIs such as
`svg_polish_recipe_template(Path)` remain path-explicit for tests and internal
callers.

The CLI now accepts:

- `<name>`;
- `examples/<name>`;
- an explicit absolute path.

Fixture names resolve under `examples/<name>`. Existing relative directories
outside `examples/` are rejected unless passed as explicit absolute paths.

It rejects traversal-like relative paths, nested `examples/<name>/...` paths,
existing outside-relative paths, and invalid fixture names before printing or
writing the starter recipe. Invalid input is reported as a controlled
`svg_polish_recipe.py: invalid fixture path...` error with exit code `1`.

## Tests

Covered by:

- `tests/test_svg_polish_recipe.py::test_template_write_rejects_parent_relative_fixture_before_writing`
- `tests/test_svg_polish_recipe.py::test_template_write_rejects_existing_relative_dir_outside_examples`
- `tests/test_svg_polish_recipe.py::test_svg_polish_recipe_template_cli_can_write_canonical_recipe`

The first two tests reproduced pre-fix bugs: `examples/../outside
--write-template` and `outside --write-template` returned exit code `0` and
wrote `polish/svg_polish_recipe.yaml` when the escaped or outside-relative
fixture had the required source SVG.

## Review Notes

- The write-capable `--write-template` path now fails closed before starter
  output path allocation.
- The documented `scripts/svg_polish_recipe.py --template examples/<name>
  --write-template` form remains valid.
- Explicit absolute paths remain available for controlled tests and ad hoc
  direct-path reviews.
- No SVG polish recipe schema, executor, delta, handoff, status, driver,
  accepted, golden, or publication behavior changed.
