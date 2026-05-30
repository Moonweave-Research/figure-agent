# Export Driver And Runner Contract Alignment

Date: 2026-05-29

Related issue:
`docs/superpowers/issues/2026-05-29-issue-72-align-export-driver-runner-contract.md`

Status: completed

## Problem

Issue 71C found that `fig5_floating_clip_mechanism` produced contradictory
operator signals:

- `/fig_drive --mode release --dry-run` returned `action: run_export`,
  `safe_command: uv run python3 scripts/run_export.py fig5_floating_clip_mechanism`,
  and `stop_boundary: null`.
- `/fig_run --execute` refused to execute the same command because the fixture
  had `acceptance_state: NOT_ACCEPTED`.

The runner was following the Issue 69 safety policy: draft export execution is
allowed only for `acceptance_state: NOT_DECLARED`, `critique_state: FRESH |
NOT_REQUIRED`, and `export_state: MISSING | STALE`.

## Fix

`fig_driver.py` now mirrors the runner's draft-export executability policy
before surfacing a runnable export command in release or polish mode.

If export is missing/stale but the state is outside the runner policy:

- release mode returns `release_blocked`;
- polish mode returns `polish_handoff_stop`;
- both use `stop_boundary: accepted_or_final_ready_required`;
- `safe_command` is `null`;
- the reason states that `/fig_run` auto-export is limited to draft fixtures
  whose `acceptance_state` is `NOT_DECLARED`.

Review-mode closeout export behavior is unchanged: closeout-bound export still
surfaces with `stop_boundary: closeout_required`, so `/fig_run` will not execute
it directly.

## Tests Added

- `test_release_mode_does_not_surface_not_accepted_export_as_executable`
- `test_polish_mode_does_not_surface_not_accepted_export_as_executable`

An existing status-explanation test now explicitly uses
`acceptance_state: NOT_DECLARED` so it continues to test first-blocker reason
propagation rather than accepted-state export policy.

## Real Fixture Check

After the fix:

- `fig_driver.py fig5_floating_clip_mechanism --mode release ... --dry-run`
  returns `release_blocked`, `safe_command: null`, and
  `stop_boundary: accepted_or_final_ready_required`.
- `fig_driver.py fig5_floating_clip_mechanism --mode polish ... --dry-run`
  returns `polish_handoff_stop`, `safe_command: null`, and
  `stop_boundary: accepted_or_final_ready_required`.
- `fig_run.py fig5_floating_clip_mechanism --mode release --execute ...`
  stops without attempting export and emits a release-operator handoff.

## Verification

- Red test: `uv run pytest -q tests/test_fig_driver.py -k not_accepted_export`
  failed before implementation with `run_export` returned in both modes.
- Green test: same command passed after implementation.
- `uv run pytest -q tests/test_fig_driver.py tests/test_fig_run.py`
  -> 111 passed.
- `uv run pytest -q tests/test_real_fixture_state_contracts.py tests/test_fig_driver.py tests/test_fig_run.py`
  -> 115 passed.
- `git diff --check` -> clean.
- `uv run pytest -q tests/test_fig_driver.py tests/test_fig_run.py tests/test_fig_closeout.py`
  -> 128 passed.
- `uv run ruff check .` -> passed.
- `uv run pytest -q` -> 1427 passed, 1 skipped, 1 xfailed, 6 warnings.
- `claude plugin validate .claude-plugin/plugin.json` -> passed.
- `claude plugin validate .` -> passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> passed.

No known Issue 72 blocker remains.
