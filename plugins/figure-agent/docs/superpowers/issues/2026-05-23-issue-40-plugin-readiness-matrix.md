# Issue 40 — Plugin Readiness Matrix

**Status:** implemented and verified

## Problem

The plugin now has many audit, freshness, driver, loop, and lint gates. The
remaining usability question is whether the commands agree on the next action
for real fixtures, especially when multiple blockers are present.

Without a real-fixture readiness matrix, a user can still see apparently
conflicting guidance from `/fig_status`, `/fig_drive`, and `/fig_loop`.

## Scope

Run a read-only readiness pass over real fixtures and document the current
state vector:

- `/fig_status` via `status.infer_stage()`
- `/fig_driver --dry-run` review-mode action selection
- `/fig_loop` verify-only output using a temporary `--runs-root` outside the
  repo

If a command-priority defect is found, fix it with a focused regression test.

## Implemented Fix

The readiness pass found one real UX defect: when both render and critique were
stale, `/fig_driver` correctly recommended compile first, while `/fig_loop`
recommended critique refresh first.

`fig_loop_decision.loop_decision()` now forwards the canonical `/fig_status`
next action when `render_state` is `MISSING` or `STALE`, even if
`critique_state` is also `MISSING` or `STALE`. This keeps compile/export
freshness ahead of host-LLM critique when the rendered artifact is not current.

## Acceptance Criteria

- [x] At least five real fixtures are inspected.
- [x] The matrix records render, critique, export, audit, driver, and loop
  state.
- [x] `/fig_loop` writes only to a temporary runs-root outside the repo.
- [x] Any command-priority defect found during the matrix pass has a focused
  regression test.
- [x] The readiness evidence is captured in a milestone document.

## Verification

```bash
uv run pytest -q tests/test_fig_loop_decision.py
uv run pytest -q tests/test_fig_loop_decision.py tests/test_fig_driver.py tests/test_status.py
uv run ruff check scripts/fig_loop_decision.py tests/test_fig_loop_decision.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```
