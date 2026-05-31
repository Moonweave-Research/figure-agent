# Plan - Issue 94 Ready Improvement Discovery Mode

## Scope Decision

Implement a pure read-only summary and attach it to `/fig_driver` output. Do not
add a new command or alter existing readiness gates.

## Steps

1. Inspect
   - Read `fig_driver.py`, `fig_driver_editorial.py`,
     `fig_loop_assessments.py`, and driver tests.
   - Confirm where latest loop checkpoint summaries enter driver output.

2. TDD red
   - Add `tests/test_ready_improvement.py` for the pure helper.
   - Add focused `tests/test_fig_driver.py` coverage for driver integration.
   - Run targeted tests and confirm expected missing-module/field failures.

3. Implement helper
   - Add `scripts/ready_improvement.py`.
   - Produce stable summary ids and conservative candidate extraction.
   - Return non-blocking states only; blockers produce `not_ready`.
   - Limit first-slice extraction to summaries already preserved in the loop
     checkpoint: editorial, top-tier, aesthetic-lever, and journal-playbook.

4. Integrate driver
   - Add optional `ready_improvement_summary` in `_summary`.
   - Keep action/stop-boundary logic unchanged.

5. Verify
   - Run targeted tests.
   - Run full tests, ruff, diff-check, and plugin validations.

6. Review/fix
   - Contract review: no release blocker or action vocabulary change.
   - Safety review: no mutation route or hidden patch path.
   - Integration review: output useful for "why complete?" and stable for
     downstream clients.

## Non-Regression Rules

- Existing complete/release behavior must still pass.
- `ready_improvement_summary.blocks_release` must always be false.
- `ready_improvement_summary.auto_patch_allowed` must always be false.
- Human gates must keep existing `human_gate_stop` and stop boundary.
- SVG polish candidate text must not imply SVG edit permission unless the
  existing SVG polish gate is ready.
