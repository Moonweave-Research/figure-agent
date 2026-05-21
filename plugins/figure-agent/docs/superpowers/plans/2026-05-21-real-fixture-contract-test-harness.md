# Real-Fixture Contract Test Harness Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove duplicate real-fixture setup code from the Issue 18 state and
loop contract tests without changing any public command behavior.

**Architecture:** Add one shared pytest helper module under `tests/` for
fixture copying, controlled placeholder artifact creation, mtime normalization,
YAML loading, and stable style-lock setup. Keep test case assertions in their
existing files so each contract matrix remains easy to read.

**Tech Stack:** Python 3.12, pytest, PyYAML.

---

### Task 1: Extract Shared Fixture Setup Helpers

**Files:**
- Create: `plugins/figure-agent/tests/real_fixture_contract_helpers.py`
- Modify: `plugins/figure-agent/tests/test_real_fixture_state_contracts.py`
- Modify: `plugins/figure-agent/tests/test_real_fixture_loop_contracts.py`

- [x] **Step 1: Add helper module**

  Move the duplicated helper responsibilities into
  `tests/real_fixture_contract_helpers.py`:

  - `load_yaml_mapping(path)`;
  - `copy_fixture_to_repo(tmp_path, fixture_name)`;
  - `materialize_controlled_artifacts(fixture, fixture_name, contract)`;
  - `normalize_fixture_mtimes(fixture, fixture_name)`;
  - `stable_style_lock(tmp_path)`.

- [x] **Step 2: Update state/driver matrix test**

  Replace local helper implementations with imports from the shared helper
  module. Keep assertions unchanged.

- [x] **Step 3: Update loop checkpoint matrix test**

  Replace local helper implementations with imports from the shared helper
  module. Keep checkpoint assertions unchanged.

### Task 2: Verify Refactor

**Files:**
- All files above.

- [x] **Step 1: Run focused contract tests**

  ```bash
  cd plugins/figure-agent
  uv run pytest -q tests/test_real_fixture_state_contracts.py tests/test_real_fixture_loop_contracts.py
  ```

- [x] **Step 2: Run caller regression bundle**

  ```bash
  cd plugins/figure-agent
  uv run pytest -q tests/test_real_fixture_state_contracts.py tests/test_real_fixture_loop_contracts.py tests/test_fig_loop.py tests/test_fig_driver.py
  uv run ruff check .
  cd ../..
  git diff --check
  ```

## Self-Review

- Spec coverage: This is a test-harness-only refactor for Issue 18C.
- Placeholder scan: No TODO/TBD placeholders remain.
- Type consistency: Helper function names used by both tests match the module
  definitions.
