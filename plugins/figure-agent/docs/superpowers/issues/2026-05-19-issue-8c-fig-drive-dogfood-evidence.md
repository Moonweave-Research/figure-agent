# Issue 8C: Fig Drive Dogfood Evidence

**Status:** completed in commits `b1fce92`, `fbb57b0`.
**Predecessor:** `docs/superpowers/issues/2026-05-19-issue-8b-dry-run-figure-driver.md`
**Evidence:** `docs/milestones/2026-05-19-fig-drive-dogfood-evidence.md`

## Problem

Issue 8B added the dry-run driver, but passing unit tests is not enough to prove
that it reduces real agent confusion. The driver must be exercised against real
fixtures with different readiness states so we know whether it recommends the
right next action before designing any executor mode.

## What to build

Create a dogfood evidence matrix for `/fig_drive --dry-run`.

Required output:

- `docs/milestones/2026-05-19-fig-drive-dogfood-evidence.md`

Optional fixes, only if dogfood finds a real defect:

- `scripts/fig_driver.py`
- `tests/test_fig_driver.py`
- `commands/fig_drive.md`

Also update issue status where appropriate:

- mark Issue 8A completed if its acceptance criteria are already satisfied
- mark Issue 8B completed if dogfood finds no blocker or after defects are fixed

## Fixtures to check

Run the matrix on at least these fixtures when present:

- `fig1_overview_v2_pair_001_vault`
- `golden_trap_depth_picture`
- `smoke_trap_demo`
- `fig3_trapping_concept`
- `fig5_floating_clip_mechanism`

If a fixture is missing, record it as `missing_fixture` rather than replacing
it silently.

## Modes to check

For each fixture, run:

```bash
uv run python3 scripts/fig_driver.py <name> --mode authoring --goal "dogfood driver" --dry-run
uv run python3 scripts/fig_driver.py <name> --mode review --goal "dogfood driver" --dry-run
uv run python3 scripts/fig_driver.py <name> --mode release --goal "dogfood driver" --dry-run
uv run python3 scripts/fig_driver.py <name> --mode polish --goal "dogfood driver" --dry-run
```

Capture:

- action
- stop_boundary
- safe_command
- render_state
- critique_state
- export_state
- final_artifact_state
- workflow_ready
- release_ready
- reason

## Acceptance criteria

- [ ] Evidence matrix includes at least five real fixtures or records why fewer
  are available.
- [ ] Each tested fixture has all four modes recorded.
- [ ] Every row has a reviewer verdict: `correct`, `questionable`, or `defect`.
- [ ] Every `defect` row either has a code/test fix or a follow-up issue.
- [ ] No dogfood run mutates source, build, exports, polish, accepted/golden,
  `.scratch`, or git state.
- [ ] If driver code changes, targeted and full verification pass.
- [ ] Issue 8A/8B statuses are updated truthfully.

## Out of scope

- Adding executor mode.
- Running compile/export/critique from the driver.
- Patching figures.
- SVG polish implementation.
- Changing accepted/golden semantics.
