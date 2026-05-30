# Issue 80 - Fixture Queue Command Plan

Status: completed

Depends on:

- Issue 77 - fixture driver queue
- Issue 78 - fixture queue actor handoff
- Issue 79 - fixture queue filters

Type: operator UX, read-only safety layer

## Problem

`/fig_queue` can now show and filter the whole fixture queue, but operators
still need to copy rows into the next command manually. That is acceptable for
host, human, release, and SVG boundaries, but inefficient for deterministic
workflow-agent actions.

The plugin needs a read-only command plan that extracts only the commands that
are safe candidates for `/fig_run`-style deterministic execution while keeping
all boundaries blocked and visible.

## Goal

Add optional command-plan output to `/fig_queue`.

## Scope

- Add a `command_plan` object to queue output when requested.
- Add `--command-plan` to include the plan in JSON/table output.
- Add `--commands` to print executable commands only, one per line.
- Classify a row as executable only when:
  - `required_actor == workflow_agent`;
  - `requires_human is false`;
  - `safe_command` is present;
  - `stop_boundary is null`;
  - `action` is one of the same deterministic actions allowed by `/fig_run`:
    `run_compile`, `run_adjudicate`, `run_export`, `run_fig_loop`.
- Classify all other rows as blocked with a compact reason.

## Non-Goals

- No execution.
- No batch runner.
- No retry/resume.
- No host critique writing.
- No accepted/golden/publication mutation.
- No generated artifact commits.

## Acceptance

- API can build a command plan from already-filtered rows.
- `--command-plan --json` includes executable and blocked rows.
- `--commands` prints executable commands only.
- Host/human/release/SVG rows are excluded from executable commands.
- Workflow-agent rows with a stop boundary are blocked, not executable.
- Existing queue JSON/table behavior remains backward compatible unless a
  command-plan flag is supplied.
- Full verification passes.

## Implementation

Extended `scripts/fig_queue.py` with:

- `COMMAND_PLAN_SCHEMA = figure-agent.fixture-command-plan.v1`
- `build_command_plan(rows)`
- `include_command_plan=True` API opt-in for `build_queue()`
- `--command-plan` to include `command_plan` in JSON output
- `--commands` to print executable commands only

The executable predicate is intentionally aligned with `/fig_run`'s deterministic
allowlist. A row is executable only when it is assigned to `workflow_agent`, has
no human requirement, has a non-empty `safe_command`, has no stop boundary, and
uses `run_compile`, `run_adjudicate`, `run_export`, or `run_fig_loop`.

All other rows are classified as blocked with a compact reason such as
`required_actor:host_llm`, `stop_boundary:closeout_required`,
`safe_command:missing`, or `action:not_executable:<action>`.

## Tests

Extended `tests/test_fig_queue.py` with coverage for:

- command-plan executable and blocked rows;
- command plan built from filtered rows;
- `--commands` printing executable commands only.

## Review

1. Safety contract: clean. This slice remains read-only and does not execute
   commands.
2. Driver/runner alignment: clean. The command-plan executable action set
   matches `/fig_run`'s deterministic allowlist.
3. Operator UX: clean. Host/human/release/SVG boundaries stay visible as
   blocked rows, while safe workflow-agent commands can be copied directly.

## Verification

- `uv run pytest -q tests/test_fig_queue.py` -> 11 passed.
- `uv run python3 scripts/fig_queue.py --mode review --goal "triage" --actor workflow_agent --command-plan --json` -> command plan with 2 executable rows and 1 blocked closeout row.
- `uv run python3 scripts/fig_queue.py --mode review --goal "triage" --actor workflow_agent --commands` -> printed only 2 executable `fig_loop.py` commands.
- `uv run ruff check scripts/fig_queue.py tests/test_fig_queue.py` -> passed.
- `uv run pytest -q tests/test_fig_queue.py tests/test_driver_actor.py tests/test_fig_run.py` -> 60 passed.
- `uv run pytest -q` -> 1459 passed, 1 skipped, 1 xfailed.
- `uv run ruff check .` -> passed.
- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` -> passed.
- `claude plugin validate .` -> passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> passed.
