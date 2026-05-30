# Issue 81 - Queue Batch Runner

Status: completed

Depends on:

- Issue 80 - fixture queue command plan

Type: bounded execution UX

## Problem

`/fig_queue --commands` can print deterministic workflow commands, but the
operator still has to copy them one by one. The plugin needs a bounded batch
runner that can take the filtered queue's executable subset and hand each
fixture to `/fig_run` for live revalidation and execution.

## Goal

Add a queue-driven batch runner that is plan-only by default and delegates all
execution to `fig_run.run_workflow()`.

## Scope

- Create `scripts/fig_queue_run.py`.
- Document `/fig_queue_run`.
- Reuse `fig_queue.build_queue(..., include_command_plan=True)`.
- Reuse existing queue filters.
- In plan-only mode, report which fixture runs would be attempted.
- In `--execute` mode, call `fig_run.run_workflow()` for each planned fixture.
- Bound the number of attempted fixtures with `--max-fixtures`.
- Preserve blocked queue rows in output.

## Safety Rules

- Default is plan-only.
- The batch runner never executes shell commands directly.
- It never executes host/human/release/SVG rows because those are absent from
  `command_plan.executable`.
- `fig_run.run_workflow()` performs live driver revalidation per fixture before
  any command execution.
- No accepted/golden/publication mutation is added.
- No generated artifact commits.

## Output Contract

`schema: figure-agent.queue-run.v1`

Top-level fields:

- `mode`, `goal`, `execute`, `max_steps`, `max_fixtures`
- `queue` with the source queue summary and command plan
- `runs` with one row per attempted fixture
- `summary` with planned, attempted, executed, failed, and blocked counts

## Acceptance

- API supports plan-only batch runs without calling `fig_run.run_workflow()`.
- API supports execute mode by calling `fig_run.run_workflow()` once per planned
  fixture, up to `--max-fixtures`.
- Host/human/release/SVG rows remain blocked through the command plan.
- CLI supports queue filters and prints JSON.
- Tests cover plan-only, execute, max-fixtures, and blocked rows.
- Full verification passes.

## Implementation

Added `scripts/fig_queue_run.py` with schema `figure-agent.queue-run.v1`.

The runner:

- builds `fig_queue.build_queue(..., include_command_plan=True)`;
- uses only `command_plan.executable`;
- is plan-only by default;
- bounds attempted fixtures with `--max-fixtures`;
- in `--execute` mode calls `fig_run.run_workflow()` per fixture, so existing
  live driver revalidation and execution safety predicates remain authoritative;
- includes the source queue summary and command plan in output.

Added `/fig_queue_run` command documentation.

## Tests

Added `tests/test_fig_queue_run.py` covering:

- plan-only output without calling `fig_run.run_workflow()`;
- execute mode delegation to `fig_run.run_workflow()`;
- `--max-fixtures` limiting;
- CLI JSON output and filter passthrough.

## Review

1. Safety: clean. The batch runner does not execute shell directly and defaults
   to plan-only.
2. Boundary containment: clean. Host/human/release/SVG rows never enter
   `command_plan.executable` and therefore are not attempted.
3. Integration: clean. Execution semantics are delegated to `/fig_run`, avoiding
   a second execution policy.

## Verification

- `uv run pytest -q tests/test_fig_queue_run.py` -> 4 passed.
- `uv run python3 scripts/fig_queue_run.py --mode review --goal "triage" --actor workflow_agent --max-fixtures 2` -> plan-only JSON with 2 planned runs and 1 blocked closeout row.
- `uv run ruff check scripts/fig_queue_run.py tests/test_fig_queue_run.py` -> passed.
- `uv run pytest -q tests/test_fig_queue_run.py tests/test_fig_queue.py tests/test_fig_run.py` -> 57 passed.
- `uv run pytest -q` -> 1463 passed, 1 skipped, 1 xfailed.
- `uv run ruff check .` -> passed.
- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` -> passed.
- `claude plugin validate .` -> passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> passed.
