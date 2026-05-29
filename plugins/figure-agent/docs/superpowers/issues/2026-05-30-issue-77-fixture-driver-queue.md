# Issue 77 - Fixture Driver Queue

Status: completed

Depends on:

- Issue 70 - guided autonomy
- Issue 76 - release not-declared gate explanation

Type: operator UX, read-only

## Problem

The plugin now gives precise next-action information for one fixture through
`/fig_status <name>` and `/fig_drive <name> --mode <mode> --dry-run`. But when
the operator wants to understand the whole corpus, they still have to run the
driver fixture by fixture and manually compare action, stop boundary, first
blocker, and safe command.

This slows down real operation and makes stale host critique queues, release
gates, and human blockers harder to triage.

## Goal

Add a read-only fixture queue surface that runs the existing driver selector
over multiple fixtures and prints a compact matrix. This must be an aggregation
layer only: it cannot invent new policy or mutate files.

## Scope

Create `scripts/fig_queue.py` and document `/fig_queue`.

The queue should:

- list fixture directories under `examples/` that contain `spec.yaml`;
- support `--mode authoring|review|release|polish`;
- support `--goal <text>`;
- support `--json` for machine-readable output;
- support optional fixture names to restrict the queue;
- include per row: fixture, action, stop_boundary, first_blocker, safe_command,
  render_state, critique_state, export_state, acceptance_state,
  publication_gate_state, release_ready;
- summarize counts by action, stop boundary, and first blocker;
- continue on per-fixture controlled errors by recording an `error` row.

## Non-Goals

- No execution; use `fig_run.py` for bounded execution.
- No host critique writing.
- No accepted/golden/publication mutation.
- No changes to driver state-selection policy.
- No generated artifact commits.

## Acceptance

- JSON output has schema `figure-agent.fixture-driver-queue.v1`.
- Table output has one line per fixture plus a summary.
- Optional fixture args restrict the queue.
- Missing fixture args produce controlled error rows, not tracebacks.
- Tests cover JSON, table, filtering, summaries, and controlled errors.
- Full verification passes.

## Implementation

Added `scripts/fig_queue.py` as a read-only aggregation layer over
`fig_driver.build_driver_summary()`. The queue scans `examples/*/spec.yaml`
when no fixtures are supplied, supports fixture filters, emits table or JSON
output, and records controlled per-fixture error rows for missing fixtures or
driver filesystem/value errors.

Added `/fig_queue` command documentation with the explicit non-execution
contract and JSON row schema. The command delegates policy to `/fig_drive`;
it does not compile, critique, adjudicate, loop, export, patch, polish, accept,
stage, commit, or force golden state.

## Tests

Added `tests/test_fig_queue.py` covering:

- JSON rows and summary counts by action, stop boundary, and first blocker;
- fixture filtering;
- missing fixture controlled error rows;
- table output;
- CLI `--json` output.

## Review

1. Contract/schema/freshness: clean. The queue does not introduce a second
   selector and copies the compact driver/status fields only.
2. Backward compatibility/scope: clean. Existing `/fig_drive`, `/fig_run`,
   `/fig_status`, compile/export/release behavior is unchanged.
3. Test/failure modes: clean after removing unused implementation scaffolding
   and constraining driver exception handling to controlled filesystem/value
   errors.

## Verification

- `uv run pytest -q tests/test_fig_queue.py` -> 5 passed.
- `uv run python3 scripts/fig_queue.py --mode review --goal "triage" fig1_overview_v2_pair_001_vault --json` -> valid queue JSON with one row.
- `uv run pytest -q tests/test_fig_queue.py tests/test_fig_driver.py tests/test_status.py` -> 217 passed.
- `uv run ruff check scripts/fig_queue.py tests/test_fig_queue.py` -> passed.
- `uv run pytest -q` -> 1446 passed, 1 skipped, 1 xfailed.
- `uv run ruff check .` -> passed.
- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` -> passed.
- `claude plugin validate .` -> passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> passed.
