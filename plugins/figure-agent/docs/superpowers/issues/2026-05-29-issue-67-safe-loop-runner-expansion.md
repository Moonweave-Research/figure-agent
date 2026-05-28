# Issue 67: Safe Loop Runner Expansion

Status: completed

Depends on: Issue 66 safe workflow runner

## Problem

Issue 66 removed manual copy-paste for stale render compilation, but the runner
still stops on `run_fig_loop`. That leaves another repetitive safe step manual:
after compile/critique/adjudication prerequisites are closed, an agent still
has to copy the verify-only loop checkpoint command even though `/fig_drive`
already selected it.

`/fig_loop` is not a source patch, host critique, export, acceptance, golden, or
polish mutation. It writes review evidence under `.scratch/fig-loop-runs/` and
then the driver can re-read that checkpoint. This makes it a good next
automation candidate.

## Decision

Expand `/fig_run --execute` allowlist from:

- `run_compile`

to:

- `run_compile`
- `run_fig_loop`

The runner still stops on `run_adjudicate`, `run_export`, `run_critique`,
patch/polish/human/release boundaries, accepted/golden state, and all unknown
actions. Even allowlisted actions are executable only when the driver reports
`stop_boundary: null`.

## Scope

Implement:

- Add `run_fig_loop` to `scripts/fig_run.py` executable action allowlist.
- Add tests proving compile -> loop -> boundary execution.
- Update `/fig_run` docs, README, SKILL, and Issue 66/67 milestone notes.

Do not implement:

- automatic adjudication
- automatic export
- automatic host critique
- automatic patching
- accepted/golden mutation
- SVG polish editing

## Acceptance

- `fig_run.run_workflow(..., execute=True)` executes a driver-selected
  `run_fig_loop` shell command when `stop_boundary` is null.
- The runner re-queries the driver after loop execution.
- If loop execution fails, the runner stops with `command_failed`.
- If driver selects `run_fig_loop` with a stop boundary, the runner stops
  without executing.
- `run_adjudicate` and `run_export` remain non-executable.
- JSON `executable_actions` includes `run_compile` and `run_fig_loop`.

## Verification

- `uv run pytest -q tests/test_fig_run.py tests/test_fig_driver.py` — 79 passed
- `uv run ruff check scripts/fig_run.py tests/test_fig_run.py` — passed
- `git diff --check` — passed

## Review Notes

1. Contract review found that allowlisted actions must not run when the driver
   attaches a stop boundary. Added test coverage and enforced
   `stop_boundary: null` before execution.
2. Scope review: clean. `run_adjudicate`, `run_export`, host critique, patch,
   polish, accepted, and golden state remain non-executable.
3. Integration review: clean. Existing driver tests still pass and `fig_run`
   JSON remains schema-compatible.
