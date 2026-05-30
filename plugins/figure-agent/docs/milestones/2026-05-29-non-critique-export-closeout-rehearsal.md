# Non-Critique Export And Closeout Rehearsal

Date: 2026-05-29

Related issue:
`docs/superpowers/issues/2026-05-29-issue-71c-non-critique-export-and-closeout-rehearsal.md`

Status: completed

## Goal

Exercise the real non-critique fixtures from Issue 71A and verify where the
guided workflow can proceed without host critique, and where it must stop at
runner, closeout, or human-owned gates.

No source drawing, host critique, accepted/golden roll-forward, force-golden,
publication provenance edit, or SVG polish edit was performed.

## Fixtures

| Fixture | Initial state | Action taken | Result | Remaining owner |
| --- | --- | --- | --- | --- |
| `fig3_trapping_concept` | render FRESH, critique NOT_REQUIRED, export FRESH, closeout needed loop rerun | `/fig_run --execute` refused closeout-bound loop, then explicit verify-only `fig_loop.py --json` was run | `fig_closeout.py --json` reports `closeout_complete: true` | none for 71C; release remains not final-ready |
| `smoke_trap_demo` | render FRESH, critique NOT_REQUIRED, export FRESH, closeout needed loop rerun | `/fig_run --execute` refused closeout-bound loop, then explicit verify-only `fig_loop.py --json` was run | `fig_closeout.py --json` reports `closeout_complete: true` | none for 71C; release remains not final-ready |
| `fig5_floating_clip_mechanism` | render FRESH, critique NOT_REQUIRED, export MISSING, acceptance NOT_ACCEPTED | `/fig_run --execute` in release mode refused execution even though driver selected `run_export` with no stop boundary | closeout remains blocked on `export`, then `loop_rerun` | Issue 72 contract alignment, then 71E human gate rehearsal |

## Commands

From `plugins/figure-agent`:

```bash
uv run python3 scripts/fig_run.py fig3_trapping_concept --mode review --goal issue-71c-non-critique-closeout --execute --max-steps 2 --no-record
uv run python3 scripts/fig_loop.py fig3_trapping_concept --goal issue-71c-non-critique-closeout --json
uv run python3 scripts/fig_closeout.py fig3_trapping_concept --json

uv run python3 scripts/fig_run.py smoke_trap_demo --mode review --goal issue-71c-non-critique-closeout --execute --max-steps 2 --no-record
uv run python3 scripts/fig_loop.py smoke_trap_demo --goal issue-71c-non-critique-closeout --json
uv run python3 scripts/fig_closeout.py smoke_trap_demo --json

uv run python3 scripts/fig_run.py fig5_floating_clip_mechanism --mode release --goal issue-71c-non-critique-closeout --execute --max-steps 2 --no-record
uv run python3 scripts/fig_closeout.py fig5_floating_clip_mechanism --json
```

## Findings

### Confirmed Safe Behavior

- `/fig_run` did not cross `closeout_required` for `fig3_trapping_concept` or
  `smoke_trap_demo`.
- Explicit `/fig_loop` reruns are verify-only and produced ignored
  `.scratch/fig-loop-runs/` evidence.
- `fig_closeout.py` correctly recognized the new loop evidence and closed both
  non-critique fixtures.
- No tracked fixture source, critique, accepted/golden state, publication file,
  or export artifact was staged.

### Contract Gap

`fig5_floating_clip_mechanism` exposed a driver/runner contract mismatch:

- `fig_driver.py --mode release` returns `action: run_export`,
  `stop_boundary: null`, and safe command
  `uv run python3 scripts/run_export.py fig5_floating_clip_mechanism`.
- `/fig_run --execute` refuses to execute it with `not_executable_action`
  because Issue 69 runner policy permits draft export only when
  `acceptance_state: NOT_DECLARED`.
- The fixture is `acceptance_state: NOT_ACCEPTED`, so the runner is following
  the conservative policy, but the driver output makes the action look runnable.

This was split into and fixed by:
`docs/superpowers/issues/2026-05-29-issue-72-align-export-driver-runner-contract.md`.

## Review Notes

- `/fig_run` reduced copy-paste only for states that are already within its
  execution policy. Closeout-bound loop handoffs still require explicit
  `/fig_loop` execution.
- Closeout cleanly distinguishes mechanical loop evidence from human
  release/publication state.
- `fig5_floating_clip_mechanism` proves the next code-level improvement should
  align driver and runner export semantics before more export autonomy is
  added.
- Generated `.scratch/` loop evidence stayed ignored.

## Verification

- `git diff --check` -> clean.
- `uv run pytest -q tests/test_fig_run.py tests/test_fig_driver.py tests/test_status.py`
  -> 249 passed.
- `claude plugin validate .claude-plugin/plugin.json` -> passed.
- `claude plugin validate .` -> passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> passed.

No known Issue 71C fixture-closeout blocker remains.
