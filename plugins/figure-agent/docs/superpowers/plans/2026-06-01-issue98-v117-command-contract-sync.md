# Issue 98 v1.17 Command Contract Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align operator-facing command guidance with the shipped v1.17 grounded critique contract.

**Architecture:** This is a command-contract hardening slice. Tests read command markdown as executable contract fixtures, then docs are updated to match the existing v1.17 Python implementation.

**Tech Stack:** Markdown command docs, pytest contract tests, existing Python critique/driver modules.

---

### Task 1: Add Command Contract Drift Tests

**Files:**
- Create: `plugins/figure-agent/tests/test_command_contract_docs.py`
- Read: `plugins/figure-agent/commands/fig_critique.md`
- Read: `plugins/figure-agent/commands/fig_loop.md`
- Read: `plugins/figure-agent/commands/fig_drive.md`

- [ ] **Step 1: Write failing tests**

Add tests that require `/fig_critique` to name the three v1.17 grounded fields,
and require `/fig_loop` plus `/fig_drive` to avoid describing inherited route
detail as v1.14-only.

- [ ] **Step 2: Run targeted tests and confirm failure**

Run:

```bash
uv run pytest -q tests/test_command_contract_docs.py
```

Expected: fails because command docs still omit or narrowly describe v1.17.

### Task 2: Update Command And Skill Docs

**Files:**
- Modify: `plugins/figure-agent/commands/fig_critique.md`
- Modify: `plugins/figure-agent/commands/fig_loop.md`
- Modify: `plugins/figure-agent/commands/fig_drive.md`
- Modify: `plugins/figure-agent/skills/figure-agent/SKILL.md`
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-06-01-issue-98-v117-command-contract-sync.md`

- [ ] **Step 1: Update `/fig_critique`**

Describe grounded v1.17 critique outputs and state that the host should follow
the exact schema printed by the brief rather than pasting an older template.

- [ ] **Step 2: Update `/fig_loop` and `/fig_drive`**

Change v1.14-only route-detail wording to v1.14+ / newer-schema inheritance
wording.

- [ ] **Step 3: Update `SKILL.md`**

Add the v1.17 fields to the L4.5 critique operating contract.

### Task 3: Verify And Review

**Files:**
- Test: `plugins/figure-agent/tests/test_command_contract_docs.py`
- Test: relevant command-doc/readiness suites.

- [ ] **Step 1: Run targeted verification**

```bash
uv run pytest -q tests/test_command_contract_docs.py tests/test_critique_brief.py tests/test_quality_manifest.py tests/test_fig_driver.py tests/test_fig_loop.py
```

- [ ] **Step 2: Run full verification**

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

- [ ] **Step 3: Critical review**

Check that new docs do not imply hidden auto-design, do not weaken legacy
compatibility, and do not change release/accepted/golden behavior.
