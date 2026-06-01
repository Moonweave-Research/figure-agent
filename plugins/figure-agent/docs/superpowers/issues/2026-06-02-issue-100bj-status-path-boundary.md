# Issue 100BJ - Status CLI Fixture Path Boundary

Status: implemented

Type: canonical workflow safety, path-boundary hardening, operator trust

## Problem

`/fig_status` is the canonical first workflow check. Its CLI implementation in
`status.py` computes the state vector, next action, explanation, and audit
evidence summary that other tools and operators use to decide what should run
next.

Before this issue, `status.py examples/../outside` normalized to an outside
directory and printed a normal stage summary such as `outside — stage 1/4`.
That made an escaped path look like ordinary fixture state.

## Decision

Harden only the single-figure CLI resolver. The lower-level `infer_stage(Path)`
API remains path-explicit for tests and internal callers.

The CLI now accepts:

- `<name>`;
- `examples/<name>`;
- an explicit absolute path.

It rejects traversal-like relative paths, nested `examples/<name>/...` paths,
and invalid fixture names before computing the status vector. Invalid input is
reported to stderr as `invalid fixture path...` with exit code `1`.

## Tests

Covered by:

- `tests/test_status.py::test_main_resolves_single_name_under_examples`
- `tests/test_status.py::test_main_accepts_examples_fixture_path`
- `tests/test_status.py::test_main_rejects_parent_relative_example_path`
- `tests/test_status.py::test_main_reports_controlled_error_for_invalid_fixture_name`

## Review Notes

- No-argument all-fixture summary behavior is unchanged.
- `infer_stage(Path)` behavior is unchanged.
- The documented `/fig_status <name>` and `scripts/status.py examples/<name>`
  forms are preserved.
- The command now fails closed before an escaped path can be presented as the
  authoritative next-action state.
