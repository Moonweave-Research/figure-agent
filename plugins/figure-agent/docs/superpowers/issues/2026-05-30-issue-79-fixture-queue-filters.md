# Issue 79 - Fixture Queue Filters

Status: completed

Depends on:

- Issue 77 - fixture driver queue
- Issue 78 - fixture queue actor handoff

Type: operator UX, read-only

## Problem

`/fig_queue` now shows actor/action/blocker context for the whole fixture set,
but a real operator often needs one subset at a time:

- host-vision work only;
- workflow-agent runnable work only;
- release/golden approval blockers only;
- one action or stop boundary class only.

Without filters, the operator must visually scan the full queue and copy rows
manually.

## Goal

Add read-only queue filters that operate on already-built queue rows. Filtering
must not change driver selection, mutate artifacts, or hide the unfiltered
queue size.

## Scope

Add CLI/API filters for:

- `required_actor`
- `action`
- `stop_boundary`
- `first_blocker`
- `blocking_source`

Filtered output should include:

- top-level `filters` object;
- top-level `unfiltered_total`;
- rows and summary computed after filtering.

## Non-Goals

- No execution.
- No priority scheduler.
- No retry/resume.
- No hidden host critique.
- No mutation of source/export/golden/accepted/publication state.

## Acceptance

- API supports filters without requiring CLI parsing.
- CLI supports `--actor`, `--action`, `--stop-boundary`,
  `--first-blocker`, and `--blocking-source`.
- Filters compose with fixture arguments.
- Summary counts are computed from filtered rows.
- `unfiltered_total` preserves the original scanned row count.
- Table and JSON output remain deterministic.
- Full verification passes.

## Implementation

Extended `scripts/fig_queue.py` with row-level filters applied after all
requested driver rows are built:

- `required_actor`
- `action`
- `stop_boundary`
- `first_blocker`
- `blocking_source`

The public JSON now includes `filters` and `unfiltered_total`. `rows` and
`summary` are computed after filtering, so operator counts match the visible
subset while preserving the original scanned count.

Updated `/fig_queue` command documentation with filter usage and examples.

## Tests

Extended `tests/test_fig_queue.py` with coverage for:

- filtering by actor while preserving `unfiltered_total`;
- composing filters with explicit fixture args;
- CLI filter flags in JSON mode.

## Review

1. Contract correctness: clean. Filtering is post-driver and cannot alter
   action selection.
2. Scope containment: clean. No execution or mutation was added.
3. Operator usability: clean. Filters cover the fields operators already scan:
   actor, action, stop boundary, first blocker, and blocking source.

## Verification

- `uv run pytest -q tests/test_fig_queue.py` -> 8 passed.
- `uv run python3 scripts/fig_queue.py --mode review --goal "triage" --actor host_llm --json` -> 2 host rows, `unfiltered_total: 8`.
- `uv run python3 scripts/fig_queue.py --mode review --goal "triage" --actor workflow_agent` -> filtered table with 3 workflow rows.
- `uv run ruff check scripts/fig_queue.py tests/test_fig_queue.py` -> passed.
- `uv run pytest -q tests/test_fig_queue.py tests/test_driver_actor.py tests/test_fig_run.py` -> 57 passed.
- `uv run pytest -q` -> 1456 passed, 1 skipped, 1 xfailed.
- `uv run ruff check .` -> passed.
- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` -> passed.
- `claude plugin validate .` -> passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> passed.
