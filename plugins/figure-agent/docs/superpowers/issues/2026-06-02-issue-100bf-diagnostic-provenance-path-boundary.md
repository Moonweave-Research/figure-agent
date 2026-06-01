# Issue 100BF - Diagnostic Provenance Fixture Path Boundary

Status: implemented

Type: evidence-provenance safety, path-boundary hardening, operator trust

## Problem

`diagnostic_artifact_provenance.py` is read-only, but it answers a high-impact
workflow question: whether a supplied screenshot/crop/artifact should count as
authoritative plugin evidence.

The intended CLI accepts:

- a fixture name, or
- an `examples/<name>` path.

Before this issue, the CLI also accepted traversal-like path input such as
`examples/../outside` and still emitted a normal provenance report. Even if that
usually classified the artifact as missing or diagnostic-only, it let an invalid
fixture identity masquerade as a normal report instead of an operator error.

Because this tool can influence whether a host/human trusts an image as current
evidence, fixture path interpretation must be explicit and narrow.

## Decision

Add a CLI-only resolver that accepts only:

- `<name>`;
- `examples/<name>`;
- an absolute path whose resolved target is exactly one direct child of
  `<repo-root>/examples`.

Reject relative paths containing `..`, nested `examples/<name>/...` paths, and
absolute paths outside `<repo-root>/examples` with a controlled exit code `2`.

The low-level `classify_artifact()` and `provenance_report()` functions remain
path-explicit for focused tests and internal reuse.

## Tests

Covered by:

- `tests/test_diagnostic_artifact_provenance.py::test_cli_accepts_examples_fixture_path`
- `tests/test_diagnostic_artifact_provenance.py::test_cli_rejects_parent_relative_fixture_path`
- existing manifest-bound, build-render, stale/mismatched, diagnostic-only, and
  summary tests.
