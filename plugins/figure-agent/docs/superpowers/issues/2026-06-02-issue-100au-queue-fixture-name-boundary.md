# Issue 100AU - Queue Fixture Name Boundary

Status: implemented

Type: queue safety, operator workflow, path-boundary hardening

## Problem

`/fig_queue` accepts explicit fixture arguments and then resolves each as
`examples/<name>`. Before this issue, the queue did not reject names containing
path components such as `../outside`.

If the escaped path existed, the queue could call the driver with an unsafe
fixture name instead of stopping at a queue-level error row. The driver remains
read-only, but the queue is a batch automation entrypoint and should never let
path traversal syntax become a fixture identity.

## Decision

Treat explicit queue fixture arguments as fixture names, not paths:

- fixture name must be a non-empty single relative path component;
- absolute paths, `..`, and multi-component paths are rejected before driver
  invocation;
- rejected rows surface as `unsafe_fixture_name` with `workflow_agent` as the
  required actor and are included in the command-plan blocked list.

This keeps queue behavior aligned with the documented `examples/<name>` command
surface without changing real fixture discovery.

## Tests

Covered by:

- `tests/test_fig_queue.py::test_build_queue_rejects_unsafe_fixture_name_before_driver`
