# Issue 78 - Fixture Queue Actor Handoff

Status: completed

Depends on:

- Issue 70 - operator-grade guided autonomy
- Issue 77 - fixture driver queue

Type: operator UX, read-only contract hardening

## Problem

`/fig_queue` now shows the selected driver action for every fixture, but the
operator still has to infer who should act next. This is easy to misread when a
queue mixes host-vision critique, human judgment, release/golden approval,
workflow-agent shell actions, and SVG polish handoff.

`/fig_run` already emits `boundary_handoff.required_actor`, but the actor
classification is private to `fig_run.py`. If `/fig_queue` reimplements it
separately, the two surfaces can drift.

## Goal

Add a shared actor-classification helper for driver summaries and surface its
result in `/fig_queue` rows and summaries.

## Scope

- Create a focused helper module for driver-summary actor classification.
- Make `/fig_run` use the shared helper for boundary handoff.
- Extend `/fig_queue` rows with:
  - `required_actor`
  - `blocking_source`
  - `requires_human`
- Extend queue summary with counts by required actor and blocking source.
- Update `/fig_queue` command docs.

## Non-Goals

- No action execution.
- No change to driver action selection.
- No change to `/fig_run` execution policy.
- No accepted/golden/publication mutation.
- No host critique writing.
- No generated artifact commits.

## Acceptance

- `/fig_run` and `/fig_queue` use one shared actor classifier.
- Host critique rows classify as `host_llm`.
- Human gates classify as `human`.
- Golden/release blocks classify as `release_operator`.
- SVG polish handoff classifies as `svg_editor`.
- Normal runnable shell/workflow rows classify as `workflow_agent`.
- Queue JSON includes `required_actor`, `blocking_source`, and
  `requires_human`.
- Queue summary includes `by_required_actor` and `by_blocking_source`.
- Existing `/fig_run` boundary handoff tests still pass.
- Full verification passes.

## Implementation

Created `scripts/driver_actor.py` as the shared classifier for driver-summary
handoffs. It exposes:

- `required_actor_for_driver_summary()`
- `blocking_source_for_driver_summary()`
- `requires_human_for_driver_summary()`

`fig_run.py` now delegates its boundary handoff actor field to this shared
classifier. `fig_queue.py` uses the same classifier to add actor/blocker fields
to every queue row and grouped counts to the queue summary.

## Tests

Added `tests/test_driver_actor.py` for the actor and blocker-source classifier.
Extended `tests/test_fig_queue.py` to assert:

- host critique rows classify as `host_llm`;
- release rows classify as `release_operator`;
- missing fixture errors remain controlled workflow-agent rows;
- table output shows the actor column;
- summary includes `by_required_actor` and `by_blocking_source`.

Existing `tests/test_fig_run.py` verifies the refactored `/fig_run`
boundary-handoff actor contract still holds.

## Review

1. Contract correctness: clean. Actor classification is shared and additive;
   driver action selection is untouched.
2. Scope containment: clean. Queue remains read-only and `/fig_run` execution
   policy is unchanged.
3. Integration readiness: clean. The queue now separates host, human, release,
   SVG, and workflow-agent work without inventing a second router.

## Verification

- `uv run pytest -q tests/test_driver_actor.py tests/test_fig_queue.py tests/test_fig_run.py` -> 54 passed.
- `uv run python3 scripts/fig_queue.py --mode review --goal "triage" --json` -> valid queue JSON with actor/blocker fields.
- `uv run python3 scripts/fig_queue.py --mode review --goal "triage"` -> table includes actor column.
- `uv run ruff check scripts/driver_actor.py scripts/fig_queue.py scripts/fig_run.py tests/test_driver_actor.py tests/test_fig_queue.py` -> passed.
- `uv run pytest -q tests/test_driver_actor.py tests/test_fig_queue.py tests/test_fig_run.py tests/test_fig_driver.py tests/test_next_action_summary.py` -> 129 passed.
- `uv run pytest -q` -> 1453 passed, 1 skipped, 1 xfailed.
- `uv run ruff check .` -> passed.
- `git diff --check` -> clean.
- `claude plugin validate .claude-plugin/plugin.json` -> passed.
- `claude plugin validate .` -> passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` -> passed.
