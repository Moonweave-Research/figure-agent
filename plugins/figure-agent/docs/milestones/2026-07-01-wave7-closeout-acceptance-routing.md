# Wave 7 Closeout And Acceptance Routing

Date: 2026-07-01

## Outcome

`fig_queue` now preserves closeout completion as queue evidence without treating it as release acceptance.

This protects the important state:

- closeout can be complete;
- the generated export can still be `acceptance_not_declared`;
- release still requires an explicit human release decision.

## Contract

When driver summary includes `closeout`:

- queue row preserves `closeout_complete`;
- queue row preserves `closeout_next_action`;
- queue row preserves `closeout_blocking_step_ids` when present;
- release decision packet `current_state` includes closeout fields only when they exist;
- release decision packet evidence refs include `closeout:complete_not_acceptance` when closeout is complete.

No source, export, accepted, golden, final-artifact, or publication state is mutated.

## Validation

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_queue.py tests/test_fig_driver.py tests/test_fig_closeout.py
# 186 passed

uv run ruff check scripts/fig_queue.py scripts/fig_driver.py scripts/fig_closeout.py \
  scripts/driver/fig_driver_closeout.py tests/test_fig_queue.py \
  tests/test_fig_driver.py tests/test_fig_closeout.py
# All checks passed
```
