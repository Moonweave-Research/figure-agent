# Issue 97E - Operator-Facing Aesthetic Integration

Status: implemented for `/fig_driver.next_action_summary`

Type: `/fig_driver` UX integration; future loop-improve integration

Parent:

- Issue 97 - Top-Tier Aesthetic Edge-Case Audit Roadmap

## Problem

The plugin has many audit surfaces, but the operator still needs one clear
answer after each loop:

- keep patching in TikZ;
- run host critique;
- adjudicate;
- start SVG polish;
- ask human art direction;
- force golden;
- stop.

Issue 94 improved `/fig_driver` ready-improvement surfacing. A separate
loop-improve orchestrator may later become the long-loop entrypoint, but this
branch should not assume that command exists. New aesthetic edge-case signals
from Issues 97A-D must be surfaced without adding another confusing command.

## Goal

Wire aesthetic anti-patterns, weakest-panel summaries, reference-learning
accountability, and marginal-return summaries into existing driver outputs, and
future loop-improve outputs if that command is merged, as readable bounded
next-action guidance.

## Implementation

`scripts/next_action_summary.py` now copies the already-computed
`ready_improvement_summary` state into `/fig_driver.next_action_summary`:

```yaml
next_action_summary:
  ready_improvement_state: not_ready | ready_no_actionable_improvement | ready_but_improvable
  ready_improvement_safe_to_ship: true | false
  optional_candidate_count: <int>
  marginal_return_state: continue | stop_recommended | needs_human_art_direction | not_ready
  marginal_return_reason: "<reason when available>"
```

This is additive. It does not change driver action vocabulary, stop
boundaries, safe commands, release readiness, or hidden edit behavior.

## Acceptance

- [x] `/fig_driver` action vocabulary and stop boundaries remain backward
  compatible.
- [x] If a loop-improve command exists in the target branch, it remains a bounded
  orchestrator and does not become a hidden designer.
- [x] Optional aesthetic improvements are explicitly optional.
- [x] Human art-direction cases stop at the human boundary.
- [x] SVG polish cases still require the existing SVG polish readiness gate.
- [x] Release/golden/accepted/publication gates remain authoritative.

## Verification

- `uv run pytest -q tests/test_fig_driver.py::test_review_complete_surfaces_ready_improvement_candidates tests/test_fig_driver.py::test_human_gate_driver_result_does_not_offer_optional_improvement_candidates`
  - Result: 2 passed.

## Review Questions

1. Does this make the plugin easier to use, or just more verbose?
2. Can a user understand why the plugin says "complete"?
3. Can the output distinguish "safe to ship" from "still improvable"?
4. Does any output imply hidden auto-design? It must not.
