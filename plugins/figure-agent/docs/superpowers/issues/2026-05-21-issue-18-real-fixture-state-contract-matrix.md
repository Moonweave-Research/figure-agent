# Issue 18: Real-Fixture State Contract Matrix

**Date:** 2026-05-21 KST
**Status:** implemented through Issue 18C
**Type:** public contract hardening / regression coverage

## Problem

The driver/status refactor in Issue 17 made the command-facing policies easier
to review, but most coverage still exercises focused helper modules or narrow
synthetic fixture states. That is useful for policy clarity, but it does not
prove that real fixture shapes still route through the same public
state-machine contract.

The risky gap is drift between:

- `/fig_status` state-vector fields;
- `/fig_drive --dry-run` action/stop-boundary choices;
- real fixture metadata combinations such as accepted false, no critique
  required, stale reference-grounded critique, missing export, tracked golden,
  and no golden contract.

## Design Direction

Add a deterministic real-fixture contract matrix that copies existing fixtures
into a temporary repo, controls only the volatile inputs, and asserts a stable
public subset of `/fig_status` and `/fig_drive`.

The matrix should be a regression net, not a new workflow implementation. It
must not compile, export, mutate examples, fabricate critique, force golden
state, or depend on previous `.scratch` loop checkpoints.

## Issue Breakdown

### Issue 18A: `/fig_status` + `/fig_drive` Real-Fixture Matrix

**Status:** implemented

Add a data-driven pytest fixture matrix for representative real fixtures:

- `golden_trap_depth_picture`: tracked golden + accepted false + stale
  reference-grounded critique;
- `smoke_trap_demo`: critique not required + fresh generated exports + no
  accepted declaration;
- `fig5_floating_clip_mechanism`: critique not required + missing exports +
  accepted false;
- `n3_trial_01_trap_depth`: stale reference-grounded critique + missing
  exports + no accepted declaration.

Acceptance criteria:

- [x] Contract cases live in `tests/real_fixture_state_contracts.yaml`.
- [x] Test copies fixtures into `tmp_path` and does not mutate checked-in
  examples.
- [x] Test materializes minimal build/export placeholders in `tmp_path` so the
  contract does not depend on local untracked artifacts.
- [x] Test normalizes mtimes and stubs export freshness/checkpoint/closeout
  volatility.
- [x] Public `/fig_status` fields are asserted for each case.
- [x] Public `/fig_drive` action, `safe_command`, and `stop_boundary` are
  asserted for representative modes.
- [x] No behavior changes to production command code.

### Issue 18B: `/fig_loop` Checkpoint Matrix

**Status:** implemented

Add a separate real-fixture matrix for checkpoint JSON contracts. This remains
separate from 18A because `/fig_loop --json` writes `.scratch/fig-loop-runs`
and has a wider contract surface than status/driver dry-run.

Representative checkpoint states:

- stale critique blocks the loop before adjudication or export;
- missing reference input preempts critique refresh;
- fresh `needs_human` adjudication routes to `human_gate_required`;
- one `apply` decision creates one patch handoff;
- multiple `apply` decisions route to `ambiguous_patch_selection`.

Acceptance criteria:

- [x] Contract cases live in `tests/real_fixture_loop_contracts.yaml`.
- [x] Test copies fixtures into `tmp_path` and writes checkpoints only under
  `tmp_path/.scratch/fig-loop-runs`.
- [x] Test reuses the 18A artifact controls and does not depend on local
  untracked build/export artifacts.
- [x] `run_manifest.json`, `iteration_001.json`, and stdout summary public
  fields are asserted.
- [x] Patch handoff presence is asserted without applying patches.
- [x] No behavior changes to production loop code.

Non-goals for 18B:

- No host-vision critique run.
- No source patching.
- No golden or accepted mutation.

### Issue 18C: Shared Real-Fixture Test Harness

**Status:** implemented

Issue 18A and 18B initially duplicated fixture-copy, artifact placeholder, mtime
normalization, YAML loading, and style-lock setup helpers. That duplication
created a future drift risk: the same CI clean-checkout artifact bug could be
fixed in one matrix and missed in the other.

Acceptance criteria:

- [x] Shared helper module lives in
  `tests/real_fixture_contract_helpers.py`.
- [x] State/driver and loop checkpoint matrix tests both use the helper.
- [x] Helper keeps real fixture copies isolated under `tmp_path`.
- [x] Helper ignores local `build/` and `exports/` artifacts, then materializes
  only YAML-declared placeholders.
- [x] No production behavior changes.

## Non-Goals

- No changes to `/fig_status`, `/fig_drive`, `/fig_loop`, compile, export, or
  critique behavior.
- No fixture migration.
- No new dependencies.
- No broad golden/accepted state changes.

## Verification Floor

For Issue 18A:

- `uv run pytest -q tests/test_real_fixture_state_contracts.py`
- `uv run pytest -q tests/test_real_fixture_state_contracts.py tests/test_status.py tests/test_fig_driver.py`
- `uv run pytest -q -m "not render"`
- `uv run ruff check .`
- `git diff --check`

For Issue 18B:

- `uv run pytest -q tests/test_real_fixture_loop_contracts.py`
- `uv run pytest -q tests/test_real_fixture_state_contracts.py tests/test_real_fixture_loop_contracts.py tests/test_fig_loop.py tests/test_fig_driver.py`
- `uv run pytest -q -m "not render"`
- `uv run ruff check .`
- `git diff --check`

For Issue 18C:

- `uv run pytest -q tests/test_real_fixture_state_contracts.py tests/test_real_fixture_loop_contracts.py`
- `uv run pytest -q tests/test_real_fixture_state_contracts.py tests/test_real_fixture_loop_contracts.py tests/test_fig_loop.py tests/test_fig_driver.py`
- `uv run ruff check .`
- `git diff --check`
