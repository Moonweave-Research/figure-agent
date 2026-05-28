# Issue 69: Safe Draft Export Runner Expansion

Status: completed

Depends on: Issue 68 safe adjudication runner expansion

## Problem

`/fig_run --execute` can close compile, initial adjudication scaffold, and
verify-only loop checkpoints, but it still stops on every `run_export`. That is
correct for accepted/golden/release state because export can become a
publication artifact boundary. It is unnecessarily manual for draft fixtures
where `/fig_drive` selected `run_export` only because generated exports are
missing or stale.

`run_export.py` already owns critique freshness, critique lint, and export
freshness checks. The runner still needs an extra policy guard so a successful
no-op on tracked golden exports or a closeout/golden boundary is not hidden as
"automatic progress."

## Decision

Add `run_export` to `/fig_run` executable actions only under these preconditions:

- driver action is `run_export`
- `stop_boundary` is null
- selected command is exactly `uv run python3 scripts/run_export.py <name>`
- selected command does not include `--force-golden` or `--skip-critique`
- compact status says `acceptance_state: NOT_DECLARED`
- compact status says `export_state: MISSING | STALE`
- compact status says `critique_state: FRESH | NOT_REQUIRED`

If any of those checks fail, `/fig_run` stops with `not_executable_action`.

## Scope

Implement:

- Runner-side safety predicate for draft generated exports.
- Tests for draft export execution, stop-boundary non-execution,
  accepted/tracked-golden non-execution, unclosed critique non-execution, and
  export failure.
- Docs update for `/fig_run`, README, SKILL, issue, and milestone.

Do not implement:

- automatic `--force-golden`
- automatic `--skip-critique`
- accepted/golden roll-forward
- release approval
- command-level `--force-golden` or `--skip-critique`
- closeout-boundary override
- source patching
- critique or adjudication mutation beyond Issue 68 missing-file scaffold

## Acceptance

- Draft `run_export` with missing/stale exports executes when critique is fresh
  or not required.
- A driver stop boundary blocks export execution.
- Accepted fixtures and `TRACKED_GOLDEN` export state block execution.
- `--force-golden` and `--skip-critique` export commands block execution.
- Export commands targeting any fixture other than `<name>` block execution.
- Stale/missing critique blocks runner-side export execution even if a malformed
  driver summary selected export.
- Failed export command stops with `command_failed` and does not re-query.
- `executable_actions` includes `run_compile`, `run_adjudicate`,
  `run_export`, and `run_fig_loop`.

## Verification

- `uv run pytest -q tests/test_fig_run.py` — 24 passed
- `uv run pytest -q tests/test_fig_run.py tests/test_fig_driver.py tests/test_run_export.py` — 98 passed
- `uv run pytest -q` — 1400 passed, 1 skipped, 1 xfailed, 6 warnings
- `uv run ruff check .` — passed
- `git diff --check` — passed
- `claude plugin validate .claude-plugin/plugin.json` — passed
- `claude plugin validate .` — passed
- `claude plugin validate ../../.claude-plugin/marketplace.json` — passed

## Review Notes

1. Contract review: clean. `run_export` requires both `stop_boundary: null` and
   draft/non-golden compact status.
2. Scope review: clean. Accepted, tracked-golden, closeout, release, force, and
   skip-critique paths remain manual.
3. Test review: clean. Targeted and full verification passed.
