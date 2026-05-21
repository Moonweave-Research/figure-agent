# Driver Command Adapter Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract `/fig_drive` safe-command string construction from `scripts/fig_driver.py` into a focused adapter module without changing public JSON behavior.

**Architecture:** `fig_driver.py` remains the state/action selector. New module `scripts/fig_driver_commands.py` owns the small command string vocabulary used by `safe_command`, including the existing shell quoting behavior for `/fig_loop --goal`.

**Tech Stack:** Python 3.12, pytest, existing dry-run JSON contract.

---

## File Structure

- Create `plugins/figure-agent/scripts/fig_driver_commands.py`
  - Public functions: `compile_command()`, `critique_command()`, `adjudicate_command()`, `fig_loop_command()`, `export_command()`.
- Create `plugins/figure-agent/tests/test_fig_driver_commands.py`
  - Focused tests for every command string and goal shell quoting.
- Modify `plugins/figure-agent/scripts/fig_driver.py`
  - Import `fig_driver_commands as command_mod`.
  - Replace private command helper calls with `command_mod.*`.
  - Delete private command helpers from `fig_driver.py`.

## Task 1: Add Focused Command Adapter Tests

- [x] **Step 1: Write failing tests**

Create `plugins/figure-agent/tests/test_fig_driver_commands.py` that imports
the five public functions from `fig_driver_commands` and asserts the exact
existing strings:

- compile: `bash scripts/compile.sh examples/driver_demo/driver_demo.tex`
- critique: `/fig_critique driver_demo`
- adjudicate: `uv run python3 scripts/critique_adjudication.py scaffold driver_demo`
- loop: `uv run python3 scripts/fig_loop.py driver_demo --goal review --json`
- loop with apostrophe: `uv run python3 scripts/fig_loop.py driver_demo --goal 'it'"'"'s a goal' --json`
- export: `uv run python3 scripts/run_export.py driver_demo`

- [x] **Step 2: Run RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_driver_commands.py
```

Expected: import error because `fig_driver_commands.py` does not exist yet.

## Task 2: Implement Adapter Module

- [x] **Step 1: Create `scripts/fig_driver_commands.py`**

Move command string construction into the new module. Keep behavior identical
to the existing private helpers in `fig_driver.py`, including `shlex.quote()`
for the `goal` argument in `fig_loop_command()`.

- [x] **Step 2: Run GREEN**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_driver_commands.py
```

Expected: all command adapter tests pass.

## Task 3: Wire `fig_driver.py`

- [x] **Step 1: Replace private command helpers**

Import `fig_driver_commands as command_mod`, update callsites to
`command_mod.compile_command(name)`, `command_mod.critique_command(name)`,
`command_mod.adjudicate_command(name)`, `command_mod.fig_loop_command(name,
goal)`, and `command_mod.export_command(name)`.

- [x] **Step 2: Run caller tests**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_driver_commands.py tests/test_fig_driver.py
```

Expected: all pass with no public `safe_command` changes.

## Task 4: Verify and Commit

- [x] **Step 1: Run verification**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_fig_driver_commands.py tests/test_fig_driver.py
uv run pytest -q -m "not render"
uv run ruff check .
cd ../..
git diff --check
```

- [x] **Step 2: Commit**

Stage only Issue 17B docs/code/tests:

```bash
git add \
  plugins/figure-agent/docs/superpowers/issues/2026-05-21-issue-17-driver-status-state-machine-refactor.md \
  plugins/figure-agent/docs/superpowers/plans/2026-05-21-driver-command-adapter-extraction.md \
  plugins/figure-agent/scripts/fig_driver.py \
  plugins/figure-agent/scripts/fig_driver_commands.py \
  plugins/figure-agent/tests/test_fig_driver_commands.py
git commit -m "Extract fig driver command adapter"
```

## Self-Review

- Spec coverage: Issue 17B only extracts safe-command text construction.
- Placeholder scan: no TODO or open-ended implementation steps.
- Type consistency: command functions all return `str`; `fig_loop_command()` accepts `(name: str, goal: str)`.
