# Real-Fixture State Contract Matrix Plan

**Date:** 2026-05-21 KST
**Parent issue:** `2026-05-21-issue-18-real-fixture-state-contract-matrix.md`
**Slice:** Issue 18A

## Goal

Lock the public `/fig_status` and `/fig_drive --dry-run` state-machine
contract against real fixture shapes, without changing command behavior.

This is a regression net after Issue 17's state-machine refactor. It answers:
when the repo contains real fixture metadata, stale critique, no-reference
critique, accepted false, missing exports, or tracked golden state, does the
driver still select the expected public next action?

## Architecture

- Keep `scripts/status.py` and `scripts/fig_driver.py` unchanged.
- Add a data file, `tests/real_fixture_state_contracts.yaml`, for public
  contract expectations.
- Add `tests/test_real_fixture_state_contracts.py` to:
  - copy each real fixture into a temporary repo;
  - normalize mtimes so source/build/export freshness is deterministic;
  - stub only volatile external state:
    - export freshness substate;
    - workspace dirty warnings;
    - latest loop checkpoint;
    - closeout report;
  - assert public fields from `status.infer_stage()`;
  - assert public `fig_driver.build_driver_summary()` action,
    `safe_command`, and `stop_boundary`.

## TDD Record

1. Write the matrix test first.
2. Run RED:

   ```bash
   cd plugins/figure-agent
   uv run pytest -q tests/test_real_fixture_state_contracts.py
   ```

   Expected initial failure: `tests/real_fixture_state_contracts.yaml` missing.

3. Add the YAML contract matrix.
4. Run GREEN with the same command.
5. Refactor only if the test is noisy or over-coupled.

## Contract Cases

- `golden_trap_depth_picture`
  - controlled export: `TRACKED_GOLDEN`
  - expected routing: stale critique blocks review/release before golden
    release handling.

- `smoke_trap_demo`
  - controlled export: `FRESH`
  - expected routing: critique not required; review runs `/fig_loop`; release
    blocks on accepted/final readiness; polish can hand off.

- `fig5_floating_clip_mechanism`
  - controlled export: `MISSING`
  - expected routing: critique not required; release/polish ask for export.

- `n3_trial_01_trap_depth`
  - controlled export: `MISSING`
  - expected routing: stale reference-grounded critique blocks all non-authoring
    modes before export or polish.

## Verification

Run from `plugins/figure-agent` unless noted:

```bash
uv run pytest -q tests/test_real_fixture_state_contracts.py
uv run pytest -q tests/test_real_fixture_state_contracts.py tests/test_status.py tests/test_fig_driver.py
uv run pytest -q -m "not render"
uv run ruff check .
cd ../..
git diff --check
```

Before push or PR update, also run:

```bash
uv run pytest -q
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Non-Goals

- No production behavior changes.
- No `/fig_loop --json` checkpoint contract in this slice.
- No compile/export invocation.
- No host-vision `/fig_critique`.
- No mutation of checked-in fixtures, accepted state, golden state, exports, or
  `.scratch`.
