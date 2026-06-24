# Fig Drive Dogfood Evidence Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove whether `/fig_drive --dry-run` gives correct next-action guidance on real fixtures before any executor mode is designed.

**Architecture:** Run the dry-run driver across a fixed fixture/mode matrix, write the results to a milestone document, and only patch `fig_driver.py` if a real defect is found. This is an evidence slice, not a new automation slice.

**Tech Stack:** Python 3.12, existing `scripts/fig_driver.py`, pytest, markdown milestone docs.

---

## Source Of Truth

Read first:

- `docs/superpowers/issues/2026-05-19-issue-8c-fig-drive-dogfood-evidence.md`
- `docs/superpowers/issues/2026-05-19-issue-8b-dry-run-figure-driver.md`
- `scripts/fig_driver.py`
- `commands/fig_drive.md`
- `tests/test_fig_driver.py`

## Task 1: Run The Dogfood Matrix

**Files:**
- Create or update: `docs/milestones-archive/2026-05-19-fig-drive-dogfood-evidence.md`

- [ ] **Step 1: Create an empty evidence doc**

Create `docs/milestones-archive/2026-05-19-fig-drive-dogfood-evidence.md` with:

```markdown
# Fig Drive Dogfood Evidence

**Date:** 2026-05-19
**Scope:** Issue 8C dry-run driver dogfood
**Status:** in progress

## Purpose

This evidence matrix checks whether `/fig_drive --dry-run` gives correct
next-action guidance on real fixtures. It does not approve executor mode,
auto-patching, auto-export, auto-critique, SVG editing, or accepted/golden
mutation.

## Method

Commands were run from `plugins/figure-agent`. For each fixture and mode, the
driver output was captured and reviewed against current `/fig_status` state.

## Evidence Matrix

| Fixture | Mode | Action | Stop boundary | Render | Critique | Export | Final artifact | Workflow ready | Release ready | Verdict | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|

## Findings

## Readiness Judgment

## Follow-Ups
```

- [ ] **Step 2: Run the matrix**

Run these commands for each fixture that exists:

```bash
for name in fig1_overview_v2_pair_001_vault golden_trap_depth_picture smoke_trap_demo fig3_trapping_concept fig5_floating_clip_mechanism; do
  for mode in authoring review release polish; do
    uv run python3 scripts/fig_driver.py "$name" --mode "$mode" --goal "dogfood driver" --dry-run
  done
done
```

If a command fails, record the fixture, mode, exit code, stdout, and stderr in
the milestone. Do not hide failures.

- [ ] **Step 3: Fill the evidence table**

For each JSON output, record:

- `fixture`
- `mode`
- `action`
- `stop_boundary`
- `status.render_state`
- `status.critique_state`
- `status.export_state`
- `status.final_artifact_state`
- `status.workflow_ready`
- `status.release_ready`
- verdict: `correct`, `questionable`, or `defect`
- one-line note explaining the verdict

Use `missing_fixture` rows if any target fixture does not exist.

## Task 2: Review The Driver Decisions

**Files:**
- Modify: `docs/milestones-archive/2026-05-19-fig-drive-dogfood-evidence.md`
- Optional Modify: `scripts/fig_driver.py`
- Optional Modify: `tests/test_fig_driver.py`
- Optional Modify: `commands/fig_drive.md`

- [ ] **Step 1: Apply the verdict rubric**

Use this rubric:

- `correct`: action follows status vector and selected mode.
- `questionable`: action is defensible but reason, safe command, or forbidden
  actions may confuse a future executor.
- `defect`: action violates Issue 8B contract, suggests a forbidden command, or
  fails to stop at a required boundary.

- [ ] **Step 2: Fix real defects only**

If any row is `defect`, first add or update a regression test in
`tests/test_fig_driver.py`, confirm it fails, then patch `scripts/fig_driver.py`
minimally.

Do not change behavior for merely `questionable` rows unless the note identifies
an actual contract violation.

- [ ] **Step 3: Re-run matrix after fixes**

If code changed, rerun the affected fixture/mode rows and update the milestone
with before/after notes.

## Task 3: Update Issue Statuses

**Files:**
- Modify: `docs/superpowers/issues/2026-05-19-issue-8a-figure-driver-protocol.md`
- Modify: `docs/superpowers/issues/2026-05-19-issue-8b-dry-run-figure-driver.md`
- Modify: `docs/superpowers/issues/2026-05-19-issue-8c-fig-drive-dogfood-evidence.md`

- [ ] **Step 1: Mark 8A completed if accurate**

Change:

```markdown
**Status:** open
```

to:

```markdown
**Status:** completed in commits `5a6d65b`, `9a01b99`.
```

Only do this if the current file still matches the completed docs-first scope.

- [ ] **Step 2: Mark 8B completed if accurate**

Change:

```markdown
**Status:** open
```

to:

```markdown
**Status:** completed in commits `c0453aa`, `38f3b89`.
```

Only do this if the dogfood evidence does not reveal an unfixed blocker.

- [ ] **Step 3: Mark 8C completed after evidence is final**

Change Issue 8C status to:

```markdown
**Status:** completed in commit `<commit>`.
```

Use the actual commit hash after committing, or leave it as `implemented; pending final commit` before commit.

## Task 4: Verification And Review

**Files:**
- Review all changed files.

- [ ] **Step 1: Run required verification**

If docs-only plus dogfood evidence:

```bash
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

If `fig_driver.py` or tests changed:

```bash
uv run pytest -q tests/test_fig_driver.py tests/test_status.py tests/test_fig_loop.py tests/test_run_export.py
uv run pytest
uv run ruff check scripts/fig_driver.py tests/test_fig_driver.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

- [ ] **Step 2: Run three clean reviews**

Review 1: matrix completeness.

- At least five fixtures or explicit missing rows?
- Four modes per available fixture?
- Every row has a verdict and note?

Review 2: decision correctness.

- Does each action follow the status vector?
- Are stop boundaries used where required?
- Are questionable rows documented honestly?

Review 3: mutation containment and next-step readiness.

- Did dogfood avoid mutating fixtures?
- Are 8A/8B statuses truthful?
- Is the next recommended issue clear?

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/milestones-archive/2026-05-19-fig-drive-dogfood-evidence.md docs/superpowers/issues/2026-05-19-issue-8a-figure-driver-protocol.md docs/superpowers/issues/2026-05-19-issue-8b-dry-run-figure-driver.md docs/superpowers/issues/2026-05-19-issue-8c-fig-drive-dogfood-evidence.md
git commit -m "Record fig drive dogfood evidence"
```

If code changed, include `scripts/fig_driver.py`, `tests/test_fig_driver.py`,
and `commands/fig_drive.md` in the same commit or a preceding fix commit.

## Completion Report Template

```markdown
Issue 8C completion report

Files changed:
- `docs/milestones-archive/2026-05-19-fig-drive-dogfood-evidence.md`
- `docs/superpowers/issues/2026-05-19-issue-8a-figure-driver-protocol.md`
- `docs/superpowers/issues/2026-05-19-issue-8b-dry-run-figure-driver.md`
- `docs/superpowers/issues/2026-05-19-issue-8c-fig-drive-dogfood-evidence.md`
- optional if defects are found: `scripts/fig_driver.py`, `tests/test_fig_driver.py`, `commands/fig_drive.md`

Dogfood coverage:
- fixtures:
- rows:
- defects fixed:

Verification:
- command -> result

Review passes:
- Review 1:
- Review 2:
- Review 3:

Next recommended issue:
- Issue 7E final-artifact loop surfacing, unless 8C finds a driver blocker that requires 8D.

Remaining risks:
- No known Issue 8C blocker remains.
```
