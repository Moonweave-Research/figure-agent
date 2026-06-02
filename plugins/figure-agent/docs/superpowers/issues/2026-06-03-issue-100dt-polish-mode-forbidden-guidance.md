# Issue 100DT - Polish Mode-Forbidden Guidance

Status: implemented in this slice

Type: operator workflow, driver guidance, SVG polish routing

## Problem

Live `/fig_driver --mode polish` dogfood on fixtures without a current SVG-polish
checkpoint showed a contradictory JSON contract:

- `stop_boundary: mode_forbidden_action`
- `action: run_fig_loop`
- `safe_command: uv run python3 scripts/fig_loop.py ...`
- `operator_guidance.next_step: Run the selected command: ...`

The stop boundary correctly says the selected action is not executable in polish
mode, but the operator guidance still told the user to run it.

## Scope

- Fix operator-facing guidance for `mode_forbidden_action`.
- Preserve existing `action`, `safe_command`, `stop_boundary`, and
  `svg_polish_gate` compatibility.
- Do not change SVG polish gate decisions, loop execution, queue filtering,
  fixture source, exports, accepted/golden state, or generated artifacts.

## Implemented Behavior

- `fig_driver_guidance.py` now detects `stop_boundary: mode_forbidden_action`
  before the generic safe-command branch.
- In polish mode it tells the operator that the selected next action is not
  executable in polish mode and to rerun `/fig_drive <fixture> --mode review`
  to close the TikZ/loop prerequisite.
- The guidance no longer says "Run the selected command" for polish
  mode-forbidden rows.

## Tests

- `tests/test_fig_driver.py::test_polish_mode_requires_loop_checkpoint_before_svg_handoff`
- `tests/test_fig_driver.py::test_polish_mode_routes_editorial_continue_tikz_back_to_loop`

## Review Notes

- Contract: this is a guidance-only fix; downstream tools that inspect
  `action`, `safe_command`, `stop_boundary`, or `svg_polish_gate` are unchanged.
- Safety: mode-forbidden rows remain non-executable in queue and queue-run.
- UX: single-fixture `/fig_drive` output now matches the safety semantics that
  queue handoff already enforced.
