# Issue 76 - Release Not-Declared Gate Explanation

Status: completed

Depends on:

- Issue 23E - Fixture Freshness UX Cleanup
- Issue 71E - Release, Golden, And Publication Gate Rehearsal
- Issue 75 - SVG Polish Readiness Source-Gate Clarity

Type: small UX/contract bugfix

## Problem

`/fig_driver <name> --mode release --dry-run` correctly blocks release when
`release_ready` is false and the fixture has no accepted/final-ready release
state. But for fixtures whose `acceptance_state` is `NOT_DECLARED` and whose
exports are otherwise fresh, `status_explanation.first_blocker` currently
returns `code: none`.

Observed on 2026-05-30:

- `fig3_trapping_concept`
- `smoke_trap_demo`

Both returned `action: release_blocked` /
`stop_boundary: accepted_or_final_ready_required`, but their first blocker was
`none`. That is internally inconsistent: the driver knows release is blocked,
while the shared explanation layer says no blocker is visible.

## Goal

Surface `acceptance_state: NOT_DECLARED` as an explicit release/final readiness
human blocker once a fixture is otherwise at a release-evaluation stage. The
operator should see that release is blocked because the fixture has not been
declared accepted or final-ready, not because of a hidden plugin defect.

## Non-Goals

- Do not change release readiness booleans.
- Do not set `accepted: true`.
- Do not mutate publication, golden, export, SVG, or source files.
- Do not make support/smoke fixtures production-ready.
- Do not add a safe command that performs acceptance.

## Contract

When status has:

- `stage >= 4`
- `release_ready: false`
- `final_ready: false`
- `acceptance_state: NOT_DECLARED`
- no earlier freshness blocker

then `status_explanation.first_blocker` should be:

```yaml
code: acceptance_not_declared
category: human_blocker
manual: true
next_command: null
```

`/fig_driver --mode release --dry-run` should include this first-blocker code in
the reason through the existing shared `_summary()` behavior.

## Acceptance

- `status_explanation` reports `acceptance_not_declared` for a stage-4 fresh
  draft fixture with no acceptance/final-ready declaration.
- `critique_not_required` remains a non-blocking plugin-state note.
- Existing `NOT_ACCEPTED` behavior remains `not_accepted`.
- Release driver dry-run includes `first blocker acceptance_not_declared`.
- Full verification passes.

## Root Cause

`status_explanation.py` treated `acceptance_state: NOT_ACCEPTED` as a human
blocker, but left `acceptance_state: NOT_DECLARED` as non-blocking. That was
reasonable for ordinary status browsing, but inconsistent in release mode once
the fixture had reached stage 4 with fresh exports: `/fig_driver` correctly
blocked on `accepted_or_final_ready_required`, while the shared explanation
reported no visible blocker.

## Implementation

- Added `acceptance_not_declared` as a human blocker when a fixture is stage 4,
  `release_ready: false`, `final_ready: false`, and
  `acceptance_state: NOT_DECLARED`.
- Kept `critique_not_required` as a non-blocking plugin-state note.
- Kept existing `not_accepted`, tracked-golden, publication, and freshness
  blocker behavior unchanged.
- Because `/fig_driver` already appends non-`none` first blocker codes through
  `_summary()`, release dry-runs now include
  `first blocker acceptance_not_declared` automatically.

## Verification

- TDD red:
  `uv run pytest -q tests/test_status.py::test_status_explanation_surfaces_acceptance_not_declared_release_gate tests/test_fig_driver.py::test_release_mode_surfaces_acceptance_not_declared_first_blocker`
  -> failed before implementation with `first_blocker.code == "none"`.
- TDD green:
  same command -> 2 passed.
- Real fixture spot-check:
  `uv run python3 scripts/fig_driver.py fig3_trapping_concept --mode release --goal "Issue 76 release blocker explanation" --dry-run`
  and the same command for `smoke_trap_demo`
  -> both report `first_blocker.code: acceptance_not_declared`.
- Targeted tests:
  `uv run pytest -q tests/test_status.py tests/test_fig_driver.py`
  -> 212 passed.
- Targeted ruff:
  `uv run ruff check scripts/status_explanation.py tests/test_status.py tests/test_fig_driver.py`
  -> All checks passed.
- Full test suite:
  `uv run pytest -q`
  -> 1441 passed, 1 skipped, 1 xfailed.
- Full ruff:
  `uv run ruff check .`
  -> All checks passed.
- Diff check:
  `git diff --check`
  -> clean.
- Plugin validation:
  `claude plugin validate .claude-plugin/plugin.json`, `claude plugin validate .`,
  and `claude plugin validate ../../.claude-plugin/marketplace.json`
  -> all Validation passed.

## Review

1. **Contract correctness** - PASS. Release readiness semantics did not change;
   only the shared explanation now matches the existing release stop.
2. **Scope containment** - PASS. No fixture source, critique, export, accepted,
   golden, publication, or SVG state is mutated.
3. **Operator UX** - PASS. Stage-4 draft/support fixtures no longer appear to
   have `first_blocker: none` while release is blocked.

No known Issue 76 blocker remains.
