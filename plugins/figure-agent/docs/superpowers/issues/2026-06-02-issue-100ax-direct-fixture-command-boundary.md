# Issue 100AX - Direct Fixture Command Boundary

Status: implemented

Type: command safety, path-boundary hardening, fixture identity consistency

## Problem

Issues 100AU-100AW hardened `/fig_queue`, `/fig_drive`, `/fig_run`, and
`/fig_export` against fixture names containing path components. Several direct
fixture commands still resolved `examples/<name>` before validating that
`name` was actually a fixture identity.

The affected surfaces were:

- `/fig_loop`, which writes verify-only records under `.scratch/fig-loop-runs`;
- `/fig_closeout`, which computes closeout status from fixture artifacts;
- `/fig_e2e_smoke`, which can run compile, export, status, and loop commands;
- `fig_loop_patch_executor.py`, which is an explicit opt-in mutation path.

These commands should not rely on downstream missing-file errors or loop lookup
failures to avoid interpreting traversal syntax as a fixture.

## Decision

Reuse `fixture_identity.validate_fixture_name()` at the top of each direct
command's public workflow function:

- `fig_loop.run_loop()`;
- `fig_closeout.compute_closeout()`;
- `fig_e2e_smoke.run_smoke()`;
- `fig_loop_patch_executor.apply_patch_file()`.

Each command translates the shared `ValueError` into its existing user-facing
error type so CLI behavior remains controlled and backward-compatible for valid
fixture names.

`perception_pack.py` is intentionally not changed in this slice because it has
a cwd-based mode that can build a pack from the current figure directory. It
needs a separate design if the project decides to distinguish cwd-mode from
examples fixture-mode.

## Tests

Covered by:

- `tests/test_fig_loop.py::test_loop_rejects_unsafe_fixture_name_before_writing_run`
- `tests/test_fig_closeout.py::test_closeout_rejects_unsafe_fixture_name_before_status`
- `tests/test_fig_e2e_smoke.py::test_run_smoke_rejects_unsafe_fixture_name_before_commands`
- `tests/test_fig_loop_patch_executor.py::test_executor_rejects_unsafe_fixture_name_before_loop_lookup`
