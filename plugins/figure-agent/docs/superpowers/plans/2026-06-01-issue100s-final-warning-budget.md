# Issue 100S Final Warning Budget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/fig_drive --mode final` honor explicit detector warning budgets instead of treating raw strict compile as the whole final readiness story.

**Architecture:** Reuse the existing `visual_clash_cap` contract. Add a structured summary helper to `check_visual_clash_budget.py`, pass it into `fig_driver_guidance.final_readiness_profile()`, and add final-mode routing in `fig_driver.py` for missing and over-budget states.

**Tech Stack:** Python stdlib, existing `fig_driver.py`, `fig_driver_guidance.py`, `check_visual_clash_budget.py`, pytest.

---

### Task 1: Budget Summary API

**Files:**
- Modify: `plugins/figure-agent/scripts/check_visual_clash_budget.py`
- Modify: `plugins/figure-agent/tests/test_visual_clash_budget.py`

- [x] **Step 1: Write failing tests**

Add tests for pass, over-budget, and missing-report summaries.

- [x] **Step 2: Implement `summarize_fixture()`**

Return `figure-agent.warning-budget.v1` with a `visual_clash` object carrying
`present`, `total`, `cap`, `over_by`, and `status`.

- [x] **Step 3: Preserve old CLI/check contract**

Keep `check_fixture()` raising `VisualClashBudgetError` for missing input,
invalid input, and over-budget state.

### Task 2: Final Driver Routing

**Files:**
- Modify: `plugins/figure-agent/scripts/fig_driver.py`
- Modify: `plugins/figure-agent/scripts/fig_driver_guidance.py`
- Modify: `plugins/figure-agent/tests/test_fig_driver.py`

- [x] **Step 1: Write failing final-mode tests**

Cover:

- missing `build/visual_clash.json` routes to strict compile;
- over-budget total routes to `human_gate_stop`;
- within-budget total allows complete final mode.

- [x] **Step 2: Implement final warning budget routing**

Evaluate the warning budget only in final mode once render is fresh. Missing
input routes to strict compile. Over-budget/invalid input routes to human gate.

- [x] **Step 3: Attach final profile field**

Expose `final_readiness_profile.warning_budget` with both profile `state` and
raw `budget_state`.

### Task 3: Docs And Verification

**Files:**
- Create: `plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100s-final-warning-budget.md`
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-100-comprehensive-plugin-gap-inventory.md`

- [x] **Step 1: Document behavior and non-goals**

Record that this is read-only final-mode routing and does not mutate warning
caps, critique, accepted/golden, export, SVG, or publication state.

- [x] **Step 2: Run verification**

```bash
uv run pytest -q tests/test_visual_clash_budget.py tests/test_fig_driver.py tests/test_release_contract.py tests/test_command_contract_docs.py
uv run ruff check scripts/check_visual_clash_budget.py scripts/fig_driver.py scripts/fig_driver_guidance.py tests/test_visual_clash_budget.py tests/test_fig_driver.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```
