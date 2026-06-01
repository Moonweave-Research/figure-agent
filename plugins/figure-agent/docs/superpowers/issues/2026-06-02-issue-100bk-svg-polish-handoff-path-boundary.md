# Issue 100BK - SVG Polish Handoff CLI Fixture Path Boundary

Status: implemented

Type: final-artifact safety, path-boundary hardening, mutation containment

## Problem

`svg_polish_handoff.py` is a final-artifact handoff helper. In dry-run mode it
validates a polished SVG, and with `--write` it writes:

- `polish/svg_polish_audit.md`;
- `polish/svg_polish_manifest.yaml`.

Before this issue, the CLI accepted a traversal-like relative path such as
`examples/../outside`. It also accepted an existing single-component relative
directory such as `outside`. If the normalized outside fixture existed,
`--write` treated it as a normal fixture and wrote the audit and manifest
outside the declared `examples/<name>` fixture tree.

## Decision

Harden only the CLI resolver. Lower-level APIs such as
`write_handoff_files(Path)` remain path-explicit for tests and internal callers.

The CLI now accepts:

- `<name>`;
- `examples/<name>`;
- an explicit absolute path.

Fixture names resolve under `examples/<name>`. Existing relative directories
outside `examples/` are rejected unless passed as explicit absolute paths.

It rejects traversal-like relative paths, nested `examples/<name>/...` paths,
existing outside-relative paths, and invalid fixture names before dry-run
validation or `--write` can run.
Invalid input is reported as a controlled `svg_polish_handoff.py: invalid
fixture path...` error with exit code `1`.

## Tests

Covered by:

- `tests/test_svg_polish_handoff.py::test_cli_write_rejects_parent_relative_fixture_before_writing`
- `tests/test_svg_polish_handoff.py::test_cli_write_rejects_existing_relative_dir_outside_examples`
- `tests/test_svg_polish_handoff.py::test_cli_write_accepts_examples_fixture_path`

The first two tests reproduced pre-fix bugs: `examples/../outside --write` and
`outside --write` returned exit code `0` and wrote both handoff files when the
escaped or outside-relative fixture existed.

## Review Notes

- The mutation-capable `--write` path now fails closed before output path
  allocation.
- The documented `scripts/svg_polish_handoff.py examples/<name> ... --write`
  form remains valid.
- Explicit absolute paths remain available for controlled tests and ad hoc
  direct-path reviews.
- No SVG polish schema, manifest freshness, status, driver, accepted, golden,
  or publication behavior changed.
