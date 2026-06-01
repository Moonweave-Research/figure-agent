# Issue 100BD - Fig Run Evidence Helper Fixture Name Boundary

Status: implemented

Type: continuation safety, path-boundary hardening, fixture identity consistency

## Problem

Issue 100BB protected the read-only journal summary helper, and Issue 100BC
protected the write-capable journal recorder. Both call into
`fig_run_evidence.py`, which owns the shared evidence source set and hash
snapshot logic for run journals.

Before this issue, the evidence helper itself still accepted raw fixture names
and resolved them as:

- `<repo-root>/examples/<name>`.

A direct helper caller could therefore call `evidence_snapshot(repo_root,
"../outside")` and read files outside `examples/` if the normalized paths
existed. The normal operator paths already validate names, but the shared helper
should not rely on every caller remembering that precondition.

## Decision

Reuse `fixture_identity.validate_fixture_name()` inside the shared helper
boundary:

- `fixture_evidence_paths()`;
- `snapshot_stale_paths()`.

`evidence_snapshot()` inherits the validation through `fixture_evidence_paths()`.
`snapshot_stale_paths()` validates fixture identity even when the stored
snapshot is `None`, because the function contract still names a fixture.

## Tests

Covered by:

- `tests/test_fig_run_evidence.py::test_fixture_evidence_paths_rejects_unsafe_fixture_name`
- `tests/test_fig_run_evidence.py::test_evidence_snapshot_rejects_unsafe_fixture_name_before_reading_outside_root`
- `tests/test_fig_run_evidence.py::test_snapshot_stale_paths_rejects_unsafe_fixture_name_even_without_snapshot`
- existing `/fig_run` and `fig_run_journal.py` tests for safe fixture names.
