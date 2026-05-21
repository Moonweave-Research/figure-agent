# Issue 15C: Bounded Auto-Patch Executor Pilot

**Date:** 2026-05-21 KST
**Status:** proposed
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
fail closed.

## Acceptance Criteria

- [ ] Default plugin behavior remains non-mutating.
- [ ] Executor requires an explicit opt-in flag.
- [ ] Executor requires exactly one `apply` decision and one matching
  `patch_handoff`.
- [ ] Executor refuses science, structure, physics, mechanism, reference
  interpretation, target-journal, accepted, golden, export, final-artifact,
  semantic-backport, and multi-target edits.
- [ ] Executor writes only inside `patch_handoff.allowed_edit_scope`.
- [ ] Executor records before/after evidence and a rollback path.
- [ ] Executor requires `/fig_closeout` after mutation and does not claim
  completion while closeout is incomplete.
- [ ] Tests include refusal cases for every forbidden category above.

## Verification

```bash
uv run pytest -q tests/test_fig_loop_auto_patch.py tests/test_fig_loop_handoff.py tests/test_fig_closeout.py tests/test_fig_driver.py
uv run pytest -q
uv run ruff check .
git diff --check
```
