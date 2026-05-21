# Driver Checkpoint Adapter Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract latest `/fig_loop` checkpoint discovery from `scripts/fig_driver.py` into a focused read-only adapter module.

**Status:** completed in Issue 17A.

**Architecture:** `fig_driver.py` remains the command-facing controller. New module `scripts/fig_driver_checkpoint.py` owns reading `.scratch/fig-loop-runs`, validating checkpoint JSON, checking currentness against fixture evidence, and selecting the newest current checkpoint.

**Tech Stack:** Python 3.12, pytest, existing JSON file records under `.scratch/fig-loop-runs`.

---

## File Structure

- Create `plugins/figure-agent/scripts/fig_driver_checkpoint.py`
  - Public interface: `latest_loop_checkpoint(repo_root: Path, name: str, example_dir: Path) -> dict[str, Any] | None`
  - Private helpers: `_read_loop_checkpoint()`, `_loop_checkpoint_is_current()`
- Create `plugins/figure-agent/tests/test_fig_driver_checkpoint.py`
  - Focused tests for malformed runs, wrong fixture, stale evidence, and latest-current selection.
- Modify `plugins/figure-agent/scripts/fig_driver.py`
  - Import `fig_driver_checkpoint as checkpoint_mod`
  - Replace `_latest_loop_checkpoint(...)` call with `checkpoint_mod.latest_loop_checkpoint(...)`
  - Delete checkpoint helper implementation from `fig_driver.py`
- Keep `plugins/figure-agent/tests/test_fig_driver.py`
  - Existing integration tests must still pass without public JSON changes.

## Task 1: Add Focused Checkpoint Adapter Tests

- [x] **Step 1: Write the failing tests**

Create `plugins/figure-agent/tests/test_fig_driver_checkpoint.py` with tests that import `latest_loop_checkpoint` from `fig_driver_checkpoint`.

Test cases:

- malformed `run_manifest.json` is ignored;
- wrong fixture run is ignored;
- checkpoint older than `critique_adjudication.yaml` is ignored;
- newest current checkpoint is returned;
- optional `top_tier_audit_summary` and `editorial_art_direction_summary` are preserved.

- [x] **Step 2: Run RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_driver_checkpoint.py
```

Expected: import error because `fig_driver_checkpoint.py` does not exist yet.

## Task 2: Implement Adapter Module

- [x] **Step 1: Create `scripts/fig_driver_checkpoint.py`**

Move the existing checkpoint helper logic from `fig_driver.py` into the new
module. Keep behavior identical:

- return `None` on file, Unicode, or JSON errors;
- require manifest schema `figure-agent.fig-loop-run.v1`;
- require matching fixture name;
- require non-empty final stop reason;
- preserve top-tier and editorial summaries only when they are mappings;
- consider spec, briefing, authoring context, source `.tex`, critique,
  adjudication, quality audit, theory guard, subregion log, and build PDF as
  freshness evidence.

- [x] **Step 2: Run GREEN**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_driver_checkpoint.py
```

Expected: all new tests pass.

## Task 3: Wire `fig_driver.py`

- [x] **Step 1: Modify driver import and callsite**

Import `fig_driver_checkpoint as checkpoint_mod` and replace:

```python
_latest_loop_checkpoint(repo_root, name, example_dir)
```

with:

```python
checkpoint_mod.latest_loop_checkpoint(repo_root, name, example_dir)
```

Delete `_read_loop_checkpoint`, `_loop_checkpoint_is_current`, and
`_latest_loop_checkpoint` from `fig_driver.py`.

- [x] **Step 2: Run caller tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_driver_checkpoint.py tests/test_fig_driver.py
```

Expected: all pass.

## Task 4: Verify and Commit

- [x] **Step 1: Run verification**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_driver_checkpoint.py tests/test_fig_driver.py
uv run pytest -q -m "not render"
uv run ruff check .
cd ../..
git diff --check
```

- [x] **Step 2: Commit**

Stage only Issue 17A docs/code/tests:

```bash
git add \
  plugins/figure-agent/docs/superpowers/issues/2026-05-21-issue-17-driver-status-state-machine-refactor.md \
  plugins/figure-agent/docs/superpowers/plans/2026-05-21-driver-checkpoint-adapter-extraction.md \
  plugins/figure-agent/scripts/fig_driver.py \
  plugins/figure-agent/scripts/fig_driver_checkpoint.py \
  plugins/figure-agent/tests/test_fig_driver_checkpoint.py
git commit -m "Extract fig driver checkpoint adapter"
```

## Self-Review

- Spec coverage: Issue 17A targets only checkpoint adapter extraction.
- Placeholder scan: no placeholder implementation steps; all commands and files are explicit.
- Type consistency: public adapter signature is stable across tasks:
  `latest_loop_checkpoint(repo_root: Path, name: str, example_dir: Path) -> dict[str, Any] | None`.
