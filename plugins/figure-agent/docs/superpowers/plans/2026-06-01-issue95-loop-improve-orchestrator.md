# Loop Improve Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/fig_improve` as a loop-centered one-fixture workflow entry point over existing safe `/fig_run` behavior.

**Architecture:** Keep `fig_driver.py` and `fig_run.py` authoritative. Add a focused `fig_improve.py` wrapper that calls `fig_run.run_workflow()` per cycle, classifies the final boundary, and emits one JSON summary. The wrapper does not execute any command that `/fig_run` would not already execute. It may continue to another internal cycle only after `max_steps_exceeded`; all host, human, patch, SVG, release, and optional-improvement boundaries stop the command and require the operator to act before rerunning.

**Tech Stack:** Python 3.12, pytest, existing figure-agent scripts and command docs.

---

### Task 1: Add Improve Runner Core

**Files:**
- Create: `scripts/fig_improve.py`
- Test: `tests/test_fig_improve.py`

- [x] Write failing tests for host boundary, complete, optional improvement,
  plan-only, and repeated boundary behavior.
- [x] Run `uv run pytest -q tests/test_fig_improve.py` and confirm it fails
  because `fig_improve` is missing.
- [x] Implement `fig_improve.run_improvement()` using `fig_run.run_workflow()`.
- [x] Run `uv run pytest -q tests/test_fig_improve.py` and confirm pass.

### Task 2: Add CLI And Command Docs

**Files:**
- Modify: `scripts/fig_improve.py`
- Create: `commands/fig_improve.md`
- Modify: `skills/figure-agent/SKILL.md`

- [x] Write failing CLI test for JSON output and `max_loops < 1` error.
- [x] Implement argparse CLI.
- [x] Document `/fig_improve` as the loop-centered entry point.
- [x] Run targeted tests.

### Task 3: Verification And Review

**Files:**
- Modify: `docs/superpowers/issues/2026-06-01-issue-95-loop-improve-orchestrator.md`

- [x] Run `uv run pytest -q tests/test_fig_improve.py tests/test_fig_run.py tests/test_fig_driver.py`.
- [x] Run `uv run pytest -q`.
- [x] Run `uv run ruff check .`.
- [x] Run `git diff --check`.
- [x] Run plugin validation commands.
- [x] Review contract, safety, and integration edge cases.
- [x] Update Issue 95 status and verification notes.
