# Issue 100G - Run-History Basin And Repeated-Defect Detector

Status: implemented on branch `codex/issue100g-basin-detector`; verified and
pending commit

Depends on:

- Issue 95 - loop improve orchestrator
- Issue 97D - marginal-return stop signal
- Issue 100B - guided entrypoint and explanation UX
- Issue 100F - advisory-vs-blocking decision boundaries

## Problem

`fig_loop_basin.py` already detects repeated local-loop signals such as repeated
patch targets, aesthetic bottlenecks, and severe reference-aesthetic metric
items. The remaining gap is operator surfacing: once a loop checkpoint records
`basin_detected`, the driver/runner should not flatten that into a generic
human gate.

If the plugin only says "human review required", the operator can continue the
same local patch loop and waste more iterations. The system needs to name the
repeated signal and recommend a step-out review.

## Goal

Make run-history basin detection visible through the normal `/fig_drive` and
`/fig_run` handoff path without changing deterministic execution or adding
hidden auto-patching.

## Contract

- Latest loop checkpoints preserve `basin_summary` when present.
- `/fig_drive` treats `final_stop_reason: basin_detected` as a human review
  boundary, but its reason must explicitly name the repeated signal class/value
  and history count.
- `/fig_run` boundary handoff for a basin must expose closeout checks that guide
  the operator out of the local loop: second opinion, human art-direction/domain
  review, possible reference-learning or briefing revision, then live status and
  driver re-query.
- Existing basin detection remains read-only and history-based. It does not edit
  source, critique, adjudication, SVG, accepted, golden, export, or publication
  state.

## Non-Goals

- No new auto-patch executor.
- No new external model integration.
- No change to threshold defaults.
- No resume command; that remains Issue 100J.
- No attempt to make subjective taste a release gate.

## Review Questions

1. Does the operator see that the problem is repeated-loop basin, not a normal
   single human gate?
2. Does the handoff recommend a step-out path instead of another blind local
   patch?
3. Does the feature preserve existing `fig_loop_basin.py` history filters and
   freshness checks?
4. Does it stay additive for existing driver/run consumers?

## Implementation Notes

- `scripts/fig_driver_checkpoint.py` preserves loop `basin_summary` in latest
  checkpoint snapshots.
- `scripts/fig_driver.py` gives `basin_detected` a specific
  `human_gate_stop` reason naming the repeated signal class/value and history
  count.
- `scripts/fig_run.py` copies `basin_summary` into `boundary_handoff` and uses
  the basin's `recommended_step_out_actions` as the first closeout checks.
- Command docs now state that basin stops are step-out review boundaries, not
  another blind local patch instruction.

## Review / Verification Log

Review 1 - contract and boundary safety:

- Confirmed the change is additive. It preserves the existing
  `human_gate_stop` / `human_gate_required` public boundary and does not add a
  new executable action or mutate source/export/accepted/golden/publication
  state.

Review 2 - operator flow:

- Confirmed `/fig_drive` no longer flattens basin stops into generic human-gate
  prose. The repeated signal and count are visible before an operator decides
  whether to seek second opinion, human art-direction review, or contract
  revision.

Review 3 - test coverage:

- Added regression coverage for driver checkpoint basin surfacing and runner
  handoff closeout checks.

Targeted verification:

- `uv run pytest -q tests/test_fig_driver.py::test_review_mode_surfaces_latest_basin_checkpoint_as_step_out_handoff tests/test_fig_run.py::test_basin_detected_handoff_preserves_step_out_actions`
  - `2 passed`
- `uv run pytest -q tests/test_fig_driver.py tests/test_fig_run.py tests/test_fig_loop.py tests/test_fig_improve.py`
  - `222 passed`
- `uv run ruff check scripts/fig_driver.py scripts/fig_driver_checkpoint.py scripts/fig_run.py tests/test_fig_driver.py tests/test_fig_run.py`
  - passed
- `git diff --check`
  - clean

Final verification:

- `uv run pytest -q`
  - `1616 passed, 3 skipped, 1 xfailed, 6 warnings`
- `uv run ruff check .`
  - passed
- `git diff --check`
  - clean
- `claude plugin validate .claude-plugin/plugin.json`
  - passed
- `claude plugin validate .`
  - passed
- `claude plugin validate ../../.claude-plugin/marketplace.json`
  - passed
