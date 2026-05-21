# Issue 15C: Bounded Auto-Patch Executor Pilot

**Date:** 2026-05-21 KST
**Status:** implemented and verified
**Parent:** Issue 15
**Blocked by:** Issue 15A and Issue 15B

## Problem

The plugin can identify an `auto_patch_candidate`, but it cannot execute even
the safest local patch. That is intentional today. A mutating executor should
only exist after the driver can keep closeout coherent and the critique linter
can prove the target is fully evidenced.

## What to Build

Add an opt-in pilot executor for exactly one local low-risk patch target. The
executor must be narrower than the existing patch handoff contract and must
fail closed. The executor applies an externally prepared unified diff; it does
not infer or generate code edits from critique prose.

## Acceptance Criteria

- [x] Default plugin behavior remains non-mutating.
- [x] Executor requires an explicit opt-in flag.
- [x] Executor requires exactly one `apply` decision and one matching
  `patch_handoff`.
- [x] Executor refuses science, structure, physics, mechanism, reference
  interpretation, target-journal, accepted, golden, export, final-artifact,
  semantic-backport, and multi-target edits.
- [x] Executor writes only inside `patch_handoff.allowed_edit_scope`.
- [x] Executor records before/after evidence and a rollback path.
- [x] Executor requires `/fig_closeout` after mutation and does not claim
  completion while closeout is incomplete.
- [x] Tests include refusal cases for every forbidden category above.

## Implementation Notes

Implemented as `scripts/fig_loop_patch_executor.py`, a separate module so
`fig_loop.py`, `fig_driver.py`, and `status.py` do not absorb mutation policy.
The CLI requires `--apply`; without it, the command refuses before reading the
patch into mutation flow. The executor validates the latest loop checkpoint,
fresh adjudication, one `apply` decision, one finding target, eligibility
classification, changed path count, allowed scope, and forbidden path classes
before running `/usr/bin/patch --dry-run`. Only after dry-run succeeds does it
apply the patch and write `patch_apply_001.json` evidence into the latest loop
run directory.

Post-review hardening added git-style diff compatibility for `a/`/`b/`
headers and new-file patches such as `/dev/null` to
`b/examples/<name>/subregion_iteration_log.md`, while preserving the same
single-path allowed-scope and forbidden-path checks.

## Verification

```bash
uv run pytest -q tests/test_fig_loop_patch_executor.py tests/test_fig_loop_auto_patch.py tests/test_fig_loop_handoff.py tests/test_fig_closeout.py tests/test_fig_driver.py
uv run pytest -q
uv run ruff check scripts/fig_loop_patch_executor.py tests/test_fig_loop_patch_executor.py
git diff --check
```
