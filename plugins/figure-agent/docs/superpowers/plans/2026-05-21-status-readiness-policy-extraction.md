# Status Readiness Policy Extraction Plan

**Date:** 2026-05-21 KST
**Parent issue:** `2026-05-21-issue-17-driver-status-state-machine-refactor.md`
**Slice:** Issue 17D

## Goal

Make `/fig_status` release/final readiness easier to review by moving boolean
readiness policy out of `scripts/status.py` and into a pure helper.

This is behavior-preserving. `status.py` remains the filesystem/spec state
controller. It still calls the final-artifact and publication adapters, but no
longer owns the readiness truth table.

## Review Finding

The final-artifact and publication gate implementations were already
reasonable adapter boundaries:

- `scripts/svg_polish_manifest.py` owns polished-SVG manifest validation and
  final-artifact state.
- `scripts/publication_gate.py` owns QUALITY_AUDIT provenance/compliance
  checks.

The remaining mixed policy was inside `status.py`:

- `workflow_ready`;
- `golden_ready`;
- `release_ready`;
- `final_ready`;
- `acceptance_state`;
- publication-gate field merge.

That mix made release readiness harder to test without a fixture filesystem.

## Implementation

- Add `scripts/status_readiness_policy.py`.
- Expose `build_status_vector(...)` as a pure function.
- Keep the following policy there:
  - coordinate-hint and final-artifact notes are workflow-nonblocking;
  - spec/reference/export/critique blocking notes still block workflow;
  - tracked golden can be workflow/golden ready but not release ready;
  - polished SVG release requires `final_artifact.state == FRESH`;
  - publication gate fields are preserved in the status vector.
- Make `status.py` pass its computed state into the policy module.

## TDD Coverage

Add `tests/test_status_readiness_policy.py` before implementation.

Focused cases:

- coordinate/final-artifact notes do not block `workflow_ready`;
- malformed spec notes block workflow and release readiness;
- tracked golden is golden-ready but not release-ready;
- stale polished SVG blocks final release, fresh polished SVG permits it;
- publication gate fields survive vector construction.

## Verification

- `uv run pytest -q tests/test_status_readiness_policy.py tests/test_status.py`
- `uv run pytest -q tests/test_status_readiness_policy.py tests/test_status.py tests/test_status_next_policy.py tests/test_fig_loop.py`
- `uv run pytest -q -m "not render"`
- `uv run pytest -q`
- `uv run ruff check .`
- `git diff --check`

## Non-Goals

- No change to final-artifact schema, publication provenance rules, or release
  gate semantics.
- No change to `/fig_status` output fields.
- No fixture migration.
- No new dependencies.
