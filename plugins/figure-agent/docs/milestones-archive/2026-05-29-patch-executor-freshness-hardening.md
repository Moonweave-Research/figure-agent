# Patch Executor Freshness Hardening

Date: 2026-05-29

Related issue:
`docs/superpowers/issues/2026-05-29-issue-70c-patch-executor-freshness-closeout-hardening.md`

Status: implemented

## Goal

Make the source-mutating patch executor at least as currentness-safe as the
read-only driver checkpoint path before any future handoff or runner UX makes
patch application more prominent.

## Implemented Behavior

`scripts/fig_loop_patch_executor.py` now refuses to apply a patch when:

- the latest selected `/fig_loop` run is stale relative to fixture evidence;
- an `allowed_edit_scope` file from the selected patch handoff is newer than
  the loop checkpoint;
- the iteration record declares a mismatched fixture;
- a prior `patch_apply_*.json` record in the same loop run still has
  `closeout_required: true`;
- patch-apply evidence itself declares a mismatched fixture.

The latest loop run is selected by loop checkpoint evidence mtime
(`run_manifest.json` / `iteration_001.json`), not directory mtime, so an older
run with pending patch evidence cannot mask a newer clean loop rerun.

The stale-evidence check uses the same fixture evidence family as the driver
checkpoint reader:

- `spec.yaml`;
- `briefing.md`;
- `authoring_plan.md`;
- `authoring_contract.md`;
- `subregion_iteration_log.md`;
- `theory_guard.md`;
- `QUALITY_AUDIT.md`;
- source `.tex`;
- `critique.md`;
- `critique_adjudication.yaml`;
- compiled build PDF.

Failure happens before `patch --dry-run` and before source mutation.

## Tests Added

`tests/test_fig_loop_patch_executor.py` now covers:

- source `.tex` newer than loop checkpoint -> refusal without mutation;
- `critique.md` newer than loop checkpoint -> refusal without mutation;
- `critique_adjudication.yaml` newer than loop checkpoint -> refusal without
  mutation;
- handoff `allowed_edit_scope` path newer than loop checkpoint -> refusal
  without mutation;
- iteration fixture mismatch -> refusal without mutation;
- pending patch closeout evidence -> refusal without mutation.
- newer clean loop run superseding an older pending-closeout run -> patch may
  proceed against the newer run.

The existing patch scope, forbidden path, explicit `--apply`, unified-diff, and
closeout evidence tests remain in place.

## Verification

- Red test first:
  `uv run pytest -q tests/test_fig_loop_patch_executor.py -k "stale_loop_run or fixture_mismatch or pending_patch_closeout"`
  failed with five expected failures before implementation.
- Targeted green:
  `uv run pytest -q tests/test_fig_loop_patch_executor.py -k "stale_loop_run or fixture_mismatch or pending_patch_closeout"`
  -> 5 passed.
- Regression target:
  `uv run pytest -q tests/test_fig_loop_patch_executor.py tests/test_fig_driver_checkpoint.py`
  -> 41 passed.
- Expanded regression after review fixes:
  `uv run pytest -q tests/test_fig_loop_patch_executor.py tests/test_fig_driver_checkpoint.py tests/test_fig_closeout.py tests/test_fig_driver.py`
  -> 127 passed.
- Lint:
  `uv run ruff check scripts/fig_loop_patch_executor.py tests/test_fig_loop_patch_executor.py tests/test_fig_driver_checkpoint.py`
  -> passed.

## Review Notes

- The executor still does not integrate with `/fig_run`.
- The executor still does not generate patches.
- The executor still requires explicit `--apply` for source mutation.
- Pending closeout is conservative: any same-run patch apply record with
  `closeout_required: true` blocks another patch.
- Review fix 1: newer clean loop checkpoints now supersede older pending runs.
- Review fix 2: handoff-specific `allowed_edit_scope` files participate in
  stale-loop refusal.
