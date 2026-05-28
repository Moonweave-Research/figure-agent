# Safe Draft Export Runner Expansion

Date: 2026-05-29

## Summary

Issue 69 expands `/fig_run --execute` to run draft generated exports when
`/fig_drive` selects `run_export` with no stop boundary. This removes another
manual copy-paste step for non-golden fixtures while preserving accepted,
tracked-golden, release, and closeout boundaries.

## Behavior

- `run_export` is executable only when:
  - `stop_boundary` is null,
  - the command is exactly `uv run python3 scripts/run_export.py <name>`,
  - the command does not include `--force-golden` or `--skip-critique`,
  - `acceptance_state` is `NOT_DECLARED`,
  - `export_state` is `MISSING` or `STALE`,
  - `critique_state` is `FRESH` or `NOT_REQUIRED`.
- Accepted fixtures and `TRACKED_GOLDEN` export state block runner execution.
- Export commands targeting any other fixture block runner execution.
- Closeout, force-golden, human, patch, polish, and host-vision boundaries still
  stop execution.
- Failed export execution stops with `command_failed`.
- Successful export execution triggers a driver re-query.

## Reviews

1. Contract/schema review: clean. The runner uses compact driver status and
   does not bypass `run_export.py` freshness/lint gates.
2. Scope containment review: clean. No accepted/golden roll-forward,
   `--force-golden`, `--skip-critique`, release approval, or source patching is
   automated; explicit tests guard the two forbidden export flags.
3. Test/integration review: clean. New tests cover draft execution, unsafe
   boundaries, accepted/tracked-golden state, unclosed critique state, and
   command failure.

## Verification

- `uv run pytest -q tests/test_fig_run.py` — 24 passed
- `uv run pytest -q tests/test_fig_run.py tests/test_fig_driver.py tests/test_run_export.py` — 98 passed
- `uv run pytest -q` — 1400 passed, 1 skipped, 1 xfailed, 6 warnings
- `uv run ruff check .` — passed
- `git diff --check` — passed
- `claude plugin validate .claude-plugin/plugin.json` — passed
- `claude plugin validate .` — passed
- `claude plugin validate ../../.claude-plugin/marketplace.json` — passed

No known Issue 69 plugin blocker remains.
