# Issue 100AV - Driver Fixture Name Boundary

Status: implemented

Type: driver safety, runner safety, path-boundary hardening

## Problem

Issue 100AU made `/fig_queue` reject explicit fixture arguments containing
path components before calling the driver. The direct single-fixture entrypoints
still needed the same boundary at the canonical next-action selector.

Before this issue, `fig_driver.build_driver_summary("../outside", ...)` built
`examples/../outside` and reached status inference if that escaped path existed.
`/fig_run` wraps the driver, so it inherited the same direct-entrypoint risk.

The driver is read-only, but it is the canonical command planner for `/fig_drive`
and `/fig_run`; it should never let traversal syntax become a fixture identity.

## Decision

Validate fixture names at the top of `fig_driver.build_driver_summary()`:

- fixture name must be a non-empty single relative path component;
- absolute paths, `..`, and multi-component paths are rejected before status
  inference, loop checkpoint lookup, closeout inspection, or command planning;
- the CLI surfaces the existing controlled `ValueError` path as exit code 2;
- `/fig_run` inherits the same controlled error through its driver wrapper.

`/fig_queue` reuses the same driver-side fixture-name policy, so queue and
direct entrypoints cannot drift into different path-boundary rules. This keeps
the direct entrypoints aligned with the queue boundary without changing valid
fixture names or driver mode behavior.

## Tests

Covered by:

- `tests/test_fig_driver.py::test_build_driver_summary_rejects_unsafe_fixture_name_before_status`
- `tests/test_fig_driver.py::test_main_rejects_unsafe_fixture_name_cleanly`
- `tests/test_fig_run.py::test_main_rejects_unsafe_fixture_name_cleanly`
- `tests/test_fig_queue.py::test_build_queue_rejects_unsafe_fixture_name_before_driver`
