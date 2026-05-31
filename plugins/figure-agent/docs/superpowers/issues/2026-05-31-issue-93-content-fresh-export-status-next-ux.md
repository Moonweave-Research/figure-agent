# Issue 93 - Content-Fresh Export Status Next UX

Status: completed

Type: status UX defect, export freshness, operator routing

Discovered by:

- Issue 92 - Post-Issue91 real-fixture migration dogfood

## Problem

During the post-Issue91 queue sweep, `fig3_trapping_concept` and
`smoke_trap_demo` reported:

- `export_state: FRESH`
- `notes: stale_export`
- `next: exports are stale or incomplete — re-run /fig_export ...`

The status explanation already identified the real blocker as
`acceptance_not_declared`. The top-level next hint was therefore misleading:
it routed the operator toward export work when content-hash export freshness was
already fresh.

## Root Cause

`status.py` combined two freshness signals:

1. content freshness from `export_freshness.compute_export_state()`;
2. legacy mtime freshness between source files and export artifacts.

When content freshness returned `FRESH`, mtime drift could still add
`stale_export`. For non-accepted fixtures this obscured the real human
acceptance gate.

## Fix

- `status.py` now trusts content-hash `EXPORT_FRESH` for stage-4 export staleness
  and suppresses mtime-only `stale_export` in that case.
- `status_next_policy.py` now has a dedicated acceptance-not-declared next hint
  instead of falling through to the generic `done` hint.
- Added a regression test covering content-fresh exports older than source
  mtimes with an acceptance-not-declared human gate.

## Verification

- `uv run pytest -q tests/test_status.py::test_status_does_not_call_content_fresh_exports_stale_for_acceptance_gate tests/test_status.py::test_stage_4_stale_export_when_source_newer tests/test_status.py::test_stage_4_export_substate_stale_redirects_to_fig_export tests/test_status.py::test_status_explanation_surfaces_acceptance_not_declared_release_gate tests/test_status_next_policy.py`
  - Result: 17 passed.
- `uv run pytest -q tests/test_status.py tests/test_fig_driver.py tests/test_fig_queue.py tests/test_fig_loop.py tests/test_status_next_policy.py`
  - Result: 330 passed.
- `uv run pytest -q`
  - Result: 1530 passed, 1 skipped, 1 xfailed.
- `uv run ruff check .`
  - Result: all checks passed.
- `git diff --check`
  - Result: clean.

## Review

- Contract correctness: content-hash export freshness is more authoritative
  than export mtime when the generated build and export PDF match.
- Backward compatibility: tracked-golden and explicit `EXPORT_STALE` routes
  remain stale/export-blocking.
- Operator UX: acceptance-not-declared now points to loop/human acceptance
  decision instead of unnecessary export reruns.
