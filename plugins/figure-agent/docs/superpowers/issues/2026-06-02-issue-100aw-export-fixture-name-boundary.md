# Issue 100AW - Export Fixture Name Boundary

Status: implemented

Type: export safety, path-boundary hardening, shared fixture identity

## Problem

Issue 100AV added fixture-name validation to the dry-run driver and runner
surfaces. `/fig_export` still accepted the raw fixture argument and resolved it
as `examples/<name>` before export-state checks and regeneration decisions.

That made export safety depend on incidental downstream path failures. For
example, `../outside` could be resolved as an existing path outside
`examples/`, then proceed into critique/export checks instead of being rejected
as an invalid fixture identity.

Because `/fig_export` can write export artifacts and, with explicit approval,
roll tracked golden artifacts forward, it needs the same boundary as the driver
and queue.

## Decision

Add a small shared `fixture_identity.py` helper:

- `is_safe_fixture_name(name)` returns true only for non-empty single relative
  path components;
- `validate_fixture_name(name)` raises the shared fixture-name error for
  absolute paths, `..`, empty strings, and multi-component paths;
- `/fig_drive`, `/fig_queue`, and `/fig_export` use the same policy.

`/fig_export` now rejects unsafe names before checking `examples/<name>/`,
critique freshness, export freshness, build PDFs, or regeneration.

## Tests

Covered by:

- `tests/test_run_export.py::test_run_export_rejects_unsafe_fixture_name_before_regenerate`
- `tests/test_fig_driver.py::test_build_driver_summary_rejects_unsafe_fixture_name_before_status`
- `tests/test_fig_queue.py::test_build_queue_rejects_unsafe_fixture_name_before_driver`
