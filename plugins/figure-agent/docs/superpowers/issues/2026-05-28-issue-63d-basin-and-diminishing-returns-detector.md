# Issue 63D - Basin And Diminishing-Returns Detector

Status: implemented on branch `codex/issue63-reference-learning-roadmap`

Depends on: Issue 63C aesthetic metric surfacing

## Problem

The loop can keep returning similar stop reasons, similar bottlenecks, or
similar critique defects across many iterations. That is a sign that the figure
is stuck in a local basin and needs a step-out action: external audit, human art
direction, reference-contract revision, or a broader redesign.

Today the escalation layer maps the current stop reason to a level, but it does
not reason over history. A repeated failure can look like a normal single-step
patch opportunity forever.

## Goal

Teach `/fig_loop` to detect repeated loop basins and route to a step-out action
instead of endlessly recommending the same local polish path.

## Scope

In scope:

- Read recent loop history from existing run records or an explicit compact
  history file.
- Detect repeated classes such as:
  - same critique finding kind across N runs;
  - same aesthetic bottleneck across N runs;
  - same severe metric divergence across N runs;
  - repeated human phrase or route class if represented structurally.
- Add a conservative stop reason such as `basin_detected`.
- Recommend step-out actions:
  - run external second-opinion review;
  - request human art direction;
  - revise reference-learning contract;
  - revise briefing if the reference and intent conflict.
- Keep detection read-only.

Out of scope:

- Guessing fixes automatically.
- Editing source or briefing.
- Using unstructured chat history as the sole source of truth.
- Treating one repeated NIT as a blocker.

## Acceptance

- [x] Repeated bottlenecks route to a basin/step-out state.
- [x] Non-repeated findings preserve current behavior.
- [x] Basin detection includes evidence paths and counted history.
- [x] Human/agent recommendations are concrete and bounded.
- [x] Tests cover repeated, non-repeated, stale-history, and mixed-severity
  cases.

## Implementation Notes

- Added `scripts/fig_loop_basin.py`, a read-only detector over existing
  `.scratch/fig-loop-runs/*/iteration_001.json` records.
- The detector currently recognizes repeated active patch targets, repeated
  aesthetic lever bottlenecks, and repeated severe reference-aesthetic metric
  divergence.
- History is considered only when prior iteration `render_state` and
  `critique_state` match the current run, preventing stale run records from
  forcing a basin verdict.
- Threshold defaults to three occurrences, counting the current run plus
  matching historical iterations.
- `/fig_loop` emits `basin_summary` and routes detected basins to
  `stop_reason: basin_detected` with `escalation_level:
  human_review_required`.
- The detector does not edit source, briefing, critique, adjudication,
  accepted/golden/export state, or generated artifacts.

## Verification

- `uv run pytest -q tests/test_fig_loop.py::test_loop_detects_repeated_reference_aesthetic_metric_basin tests/test_fig_loop.py::test_loop_does_not_detect_basin_without_repeated_history tests/test_fig_loop.py::test_loop_ignores_stale_history_for_basin_detection tests/test_fig_loop.py::test_loop_does_not_count_warning_metrics_as_severe_basin_history`
  - 4 passed.
- `uv run pytest -q tests/test_fig_loop.py tests/test_reference_aesthetic_metrics.py tests/test_status.py`
  - 230 passed.
- `uv run ruff check scripts/fig_loop.py scripts/fig_loop_basin.py scripts/fig_loop_escalation.py scripts/fig_loop_records.py tests/test_fig_loop.py`
  - All checks passed.

## Review Questions

1. Does this catch stuck loops without punishing normal iteration?
2. Is the history source reliable and repo-local?
3. Can the user understand why the loop says "step out"?
4. Does the detector avoid hidden state that cannot be reproduced?
