# Issue 100BN - External Vision Review CLI Fixture Path Boundary

Status: implemented

Type: external review evidence safety, path-boundary hardening, mutation containment

## Problem

`external_vision_review.py --template` prints a starter second-opinion review
for one fixture, and `--write-template` writes:

- `external_vision_review.yaml`.

Before this issue, the CLI accepted traversal-like relative paths such as
`examples/../outside`. It also accepted an existing single-component relative
directory such as `outside`. If that outside fixture had the required build
artifact, `--write-template` wrote external review evidence outside the declared
`examples/<name>` fixture tree.

## Decision

Harden only the `--template` CLI resolver. Lower-level APIs such as
`external_vision_review_template(Path)` remain path-explicit for tests and
internal callers.

The CLI now accepts:

- `<name>`;
- `examples/<name>`;
- an explicit absolute path.

Fixture names resolve under `examples/<name>`. Existing relative directories
outside `examples/` are rejected unless passed as explicit absolute paths.

It rejects traversal-like relative paths, nested `examples/<name>/...` paths,
existing outside-relative paths, and invalid fixture names before printing or
writing the starter review. Invalid input is reported as a controlled
`external_vision_review.py: invalid fixture path...` error with exit code `1`.

## Tests

Covered by:

- `tests/test_external_vision_review.py::test_template_write_rejects_parent_relative_fixture_before_writing`
- `tests/test_external_vision_review.py::test_template_write_rejects_existing_relative_dir_outside_examples`
- `tests/test_external_vision_review.py::test_external_vision_review_template_cli_can_write_canonical_file`

The first two tests reproduced pre-fix bugs: `examples/../outside
--write-template` and `outside --write-template` returned exit code `0` and
wrote `external_vision_review.yaml` when the escaped or outside-relative
fixture had the required build artifact.

## Review Notes

- The write-capable `--write-template` path now fails closed before output path
  allocation.
- The documented `scripts/external_vision_review.py --template examples/<name>
  --write-template` form remains valid.
- Explicit absolute paths remain available for controlled tests and ad hoc
  direct-path reviews.
- No external review schema, freshness, loop, status, driver, accepted, golden,
  or publication behavior changed.
