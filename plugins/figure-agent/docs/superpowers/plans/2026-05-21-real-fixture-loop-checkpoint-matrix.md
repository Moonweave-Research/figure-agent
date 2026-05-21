# Real-Fixture Loop Checkpoint Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lock `/fig_loop --json` checkpoint output against real fixture state
shapes without changing loop behavior.

**Architecture:** Keep `scripts/fig_loop.py` unchanged. Add a data-driven test
that copies real fixtures into `tmp_path`, controls only volatile artifact and
status inputs, runs `fig_loop.run_loop()` with a temp runs root, and asserts
the public checkpoint fields in `run_manifest.json`, `iteration_001.json`, and
`json_stdout_summary()`.

**Tech Stack:** Python 3.12, pytest, PyYAML, existing figure-agent scripts.

---

### Task 1: Add Loop Checkpoint Contract Tests

**Files:**
- Create: `plugins/figure-agent/tests/test_real_fixture_loop_contracts.py`
- Create: `plugins/figure-agent/tests/real_fixture_loop_contracts.yaml`
- Read: `plugins/figure-agent/tests/real_fixture_state_contracts.yaml`

- [x] **Step 1: Write the failing test**

  Create `test_real_fixture_loop_contracts.py` that:

  - loads cases from `real_fixture_loop_contracts.yaml`;
  - loads artifact/export controls from `real_fixture_state_contracts.yaml`;
  - copies each real fixture into `tmp_path/repo/examples/<name>`;
  - ignores checked-in or local `build/` and `exports/`;
  - materializes minimal build/export placeholder artifacts declared by the
    18A state contract;
  - runs `fig_loop.run_loop()` with `runs_root=tmp_path/.scratch/fig-loop-runs`;
  - asserts:
    - `run_manifest.json` schema, fixture, mode, goal, final stop reason;
    - `iteration_001.json` stop reason, escalation level, recommended next
      action, human gate status, patch handoff presence, status subset, and
      adjudication subset;
    - stdout summary public fields from `json_stdout_summary()`.

- [x] **Step 2: Run RED**

  ```bash
  cd plugins/figure-agent
  uv run pytest -q tests/test_real_fixture_loop_contracts.py
  ```

  Expected initial result: collection failure because
  `tests/real_fixture_loop_contracts.yaml` does not exist.

- [x] **Step 3: Add the YAML matrix**

  Add cases for:

  - `stale_critique_blocks_loop`;
  - `reference_missing_preempts_critique`;
  - `human_gate_from_fresh_adjudication`;
  - `single_apply_creates_patch_handoff`;
  - `ambiguous_apply_blocks_handoff`.

- [x] **Step 4: Run GREEN**

  ```bash
  cd plugins/figure-agent
  uv run pytest -q tests/test_real_fixture_loop_contracts.py
  ```

  Expected: all loop contract cases pass.

### Task 2: Document Issue 18B

**Files:**
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-05-21-issue-18-real-fixture-state-contract-matrix.md`
- Create: `plugins/figure-agent/docs/superpowers/plans/2026-05-21-real-fixture-loop-checkpoint-matrix.md`

- [x] **Step 1: Update Issue 18**

  Mark Issue 18B implemented and list the checkpoint states now covered:

  - stale critique;
  - missing reference input;
  - human gate;
  - single patch handoff;
  - ambiguous apply selection.

- [x] **Step 2: Add this implementation plan**

  Save the exact test/design/verification contract in this plan file.

### Task 3: Verify and Publish

**Files:**
- All files above.

- [x] **Step 1: Run focused verification**

  ```bash
  cd plugins/figure-agent
  uv run pytest -q tests/test_real_fixture_loop_contracts.py
  uv run pytest -q tests/test_real_fixture_state_contracts.py tests/test_real_fixture_loop_contracts.py tests/test_fig_loop.py tests/test_fig_driver.py
  ```

- [x] **Step 2: Run CI-equivalent verification**

  ```bash
  cd plugins/figure-agent
  uv run pytest -q -m "not render"
  uv run ruff check .
  cd ../..
  git diff --check
  ```

- [x] **Step 3: Run full local verification before PR update**

  ```bash
  cd plugins/figure-agent
  uv run pytest -q
  claude plugin validate .claude-plugin/plugin.json
  claude plugin validate .
  claude plugin validate ../../.claude-plugin/marketplace.json
  ```

- [x] **Step 4: Commit and open a stacked PR**

  Stack on `codex/real-fixture-state-matrix`, because Issue 18B reuses the
  18A state matrix helpers and fixture controls.

## Self-Review

- Spec coverage: The slice covers checkpoint output only; command behavior is
  unchanged.
- Placeholder scan: No implementation placeholder remains in the test or YAML.
- Type consistency: YAML keys match test assertions and existing fig_loop JSON
  fields.
