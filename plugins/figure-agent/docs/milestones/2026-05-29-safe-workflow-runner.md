# Safe Workflow Runner

Date: 2026-05-29

## Summary

Issue 66 adds `/fig_run`, a bounded executor over `/fig_drive`. The driver
remains the canonical selector; the runner only executes allowlisted
deterministic shell work and stops at the next boundary that requires host,
human, review-state, export, release, patch, polish, accepted, or golden
authority.

Issue 66A intentionally allowed only `run_compile`. Issues 67, 68, and 69 later
expand the same bounded model to verify-only `/fig_loop` checkpoints, missing
adjudication scaffold, and non-golden draft export.

## Files Changed

- `scripts/fig_run.py`
- `commands/fig_run.md`
- `tests/test_fig_run.py`
- `README.md`
- `skills/figure-agent/SKILL.md`
- `docs/superpowers/issues/2026-05-29-issue-66-safe-workflow-runner.md`

## Behavior

- Plan-only by default.
- `--execute` runs `run_compile` only.
- Re-queries `/fig_drive` after each executed command.
- Stops on `/fig_critique` host boundary.
- Stops on non-allowlisted shell actions such as `run_adjudicate` and
  `run_export`.
- Stops on command failure and records stdout/stderr tails.
- Stops on `--max-steps` if state does not advance.
- Emits `figure-agent.run.v1` JSON evidence.

## Reviews

1. Contract/schema/freshness: clean after documenting `stop_reason: null` for
   successful intermediate executed steps.
2. Scope containment: clean. No source, critique, adjudication, loop, export,
   accepted, golden, SVG, or git mutation is automated by Issue 66A.
3. Test/integration readiness: clean after adding CLI `--execute` and invalid
   `--max-steps` tests.

## Verification

- `uv run pytest -q tests/test_fig_run.py tests/test_fig_driver.py` — 76 passed
- `uv run ruff check scripts/fig_run.py tests/test_fig_run.py` — passed
- `git diff --check` — passed
- `uv run python3 scripts/fig_run.py n3_trial_02_actuation_sequence --mode review --goal 'safe runner smoke'` — emitted `figure-agent.run.v1`, stopped at `run_critique` / `host_boundary`, executed 0 commands
- `uv run pytest -q` — 1385 passed, 1 skipped, 1 xfailed, 6 legacy critique deprecation warnings
- `uv run ruff check .` — passed
- `claude plugin validate .claude-plugin/plugin.json` — passed
- `claude plugin validate .` — passed
- `claude plugin validate ../../.claude-plugin/marketplace.json` — passed

## Remaining Risk

The runner is deliberately conservative. It still does not automate host
critique, existing adjudication repair, closeout overrides, accepted/golden
roll-forward, SVG polish editing, release approval, source patching, or git
mutation. Those require separate explicit policies because they cross human,
publication, or source-edit boundaries.

No known Issue 66 plugin blocker remains.
