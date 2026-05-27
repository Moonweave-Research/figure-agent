# Issue 58 Single Next Action UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one compact `next_action_summary` object across status, driver, loop, and closeout outputs without changing the existing action selector or gates.

**Architecture:** Keep `/fig_drive --dry-run` as the canonical selector. Add a small read-only `next_action_summary.py` adapter module that compresses existing status/driver/loop/closeout evidence into the same schema. Integrate the adapter into existing outputs without removing detailed fields.

**Tech Stack:** Python 3.12, pytest, existing figure-agent scripts and command docs.

---

### Task 1: Add The Summary Contract Tests

**Files:**
- Create: `plugins/figure-agent/tests/test_next_action_summary.py`
- Create later: `plugins/figure-agent/scripts/next_action_summary.py`

- [ ] **Step 1: Write tests for status, driver, loop, and closeout summary shape**

Add tests that require every summary to expose:

```python
{
    "schema": "figure-agent.next-action-summary.v1",
    "action": "...",
    "reason": "...",
    "blocking_source": "...",
    "safe_command": "...",
    "requires_human": False,
    "allowed_scope": [...],
    "forbidden_scope": [...],
    "evidence_refs": [...],
}
```

Cover these cases:

- status render missing -> `run_compile`;
- driver human gate -> `human_gate_stop` with `requires_human: true`;
- loop patch recommendation -> `patch_handoff_stop`;
- closeout compile need -> `run_compile`.

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_next_action_summary.py
```

Expected: FAIL because `next_action_summary.py` does not exist.

### Task 2: Implement The Adapter Module

**Files:**
- Create: `plugins/figure-agent/scripts/next_action_summary.py`

- [ ] **Step 1: Add read-only summary builders**

Implement:

- `status_next_action_summary(status: Mapping[str, Any]) -> dict[str, Any]`
- `driver_next_action_summary(driver_summary: Mapping[str, Any]) -> dict[str, Any]`
- `loop_next_action_summary(loop_decision: Mapping[str, Any], status: Mapping[str, Any], patch_handoff: Mapping[str, Any] | None) -> dict[str, Any]`
- `closeout_next_action_summary(report: Mapping[str, Any]) -> dict[str, Any]`

Do not select a new workflow action. Only compress fields already selected by
the caller.

- [ ] **Step 2: Verify GREEN**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_next_action_summary.py
```

Expected: PASS.

### Task 3: Integrate The Summary Into Existing Outputs

**Files:**
- Modify: `plugins/figure-agent/scripts/status.py`
- Modify: `plugins/figure-agent/scripts/fig_driver.py`
- Modify: `plugins/figure-agent/scripts/fig_loop.py`
- Modify: `plugins/figure-agent/scripts/fig_loop_records.py`
- Modify: `plugins/figure-agent/scripts/fig_closeout.py`
- Modify tests where the public JSON shape is asserted.

- [ ] **Step 1: Add failing integration assertions**

Update existing tests so:

- `/fig_status` inferred dict includes `next_action_summary`;
- `/fig_drive --dry-run` JSON includes `next_action_summary` matching top-level `action` and `safe_command`;
- `/fig_loop --json` includes the iteration's `next_action_summary`;
- `/fig_closeout --json` includes `next_action_summary`.

- [ ] **Step 2: Run targeted tests and verify RED**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop_records.py tests/test_fig_closeout.py
```

Expected: FAIL on missing `next_action_summary`.

- [ ] **Step 3: Wire adapter calls into existing outputs**

Add summary construction after existing decisions are already computed. Preserve
all existing fields and action vocabulary.

- [ ] **Step 4: Run targeted tests and verify GREEN**

Run:

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_next_action_summary.py tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop_records.py tests/test_fig_closeout.py
```

Expected: PASS.

### Task 4: Documentation And Issue Closeout

**Files:**
- Modify: `plugins/figure-agent/commands/fig_status.md`
- Modify: `plugins/figure-agent/commands/fig_drive.md`
- Modify: `plugins/figure-agent/commands/fig_loop.md`
- Modify: `plugins/figure-agent/docs/superpowers/issues/2026-05-27-issue-58-single-next-action-ux.md`
- Create: `plugins/figure-agent/docs/milestones/2026-05-28-single-next-action-ux.md`

- [ ] **Step 1: Document the summary contract**

Explain that `next_action_summary` is read-only compression, not a new selector.
State that `/fig_drive --dry-run` remains canonical for action selection.

- [ ] **Step 2: Update Issue 58 status**

Record implementation paths, verification commands, and scope containment.

### Task 5: Final Verification And Review

- [ ] **Step 1: Run targeted verification**

```bash
cd plugins/figure-agent
uv run pytest -q tests/test_next_action_summary.py tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop_records.py tests/test_fig_closeout.py tests/test_real_fixture_audit_adoption.py
uv run ruff check scripts/next_action_summary.py scripts/status.py scripts/fig_driver.py scripts/fig_loop.py scripts/fig_loop_records.py scripts/fig_closeout.py tests/test_next_action_summary.py tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop_records.py tests/test_fig_closeout.py
git diff --check
```

- [ ] **Step 2: Run full verification**

```bash
cd plugins/figure-agent
uv run pytest -q
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

- [ ] **Step 3: Critical review**

Check:

- summary does not hide detailed blockers;
- driver action and summary action agree;
- human gates remain human gates;
- no source/export/accepted/golden mutation was introduced;
- Issue 59 can consume the summary for SVG polish promotion routing.
