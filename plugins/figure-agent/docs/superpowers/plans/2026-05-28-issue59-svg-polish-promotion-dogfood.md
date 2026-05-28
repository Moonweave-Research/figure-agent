# Issue 59 SVG Polish Promotion Dogfood Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dogfood SVG polish promotion routing on real fixtures and record whether the current policy is predictable, conservative, and actionable.

**Architecture:** Do not change SVG polish execution or edit figures unless a concrete routing defect is found. Use `/fig_drive --mode polish --dry-run`, compile-only preflight when render artifacts are absent, and existing `/fig_loop` records to determine whether route blockers are correct. Store evidence in a milestone and close Issue 59 if no code change is needed.

**Tech Stack:** Python 3.12, shell compile script, fig_driver, fig_loop, pytest, markdown milestone docs.

---

### Task 1: Select Fixtures And Capture Preflight

**Files:**
- Create: `plugins/figure-agent/docs/milestones/2026-05-28-svg-polish-promotion-dogfood.md`

- [x] **Step 1: Select fixtures**

Use five real fixtures:

- `fig1_overview_v2_pair_001_vault`
- `fig1_overview_v2`
- `golden_trap_depth_picture`
- `n3_trial_01_trap_depth`
- `n3_trial_02_actuation_sequence`

- [x] **Step 2: Run initial polish driver preflight**

Run:

```bash
cd plugins/figure-agent
uv run python3 scripts/fig_driver.py <fixture> --mode polish --goal "issue59 svg polish promotion dogfood" --dry-run
```

Expected in a clean worktree: most or all fixtures first return
`action: run_compile` because build artifacts are absent or stale.

Actual result: all five fixtures had `render_state: FRESH` and selected
`action: run_critique` because `critique_state: STALE`.

### Task 2: Close Render Gate Without Editing Sources

- [x] **Step 1: Compile selected fixtures only**

Run:

```bash
bash scripts/compile.sh examples/<fixture>/<fixture>.tex
```

Do not stage generated `build/`, `exports/`, `.scratch/`, or preview artifacts.

Not rerun. Render state was already fresh for all selected fixtures, and compile
would not resolve the active stale-critique blocker.

- [x] **Step 2: Re-run polish driver**

Run:

```bash
uv run python3 scripts/fig_driver.py <fixture> --mode polish --goal "issue59 svg polish promotion dogfood" --dry-run
```

Record `action`, `stop_boundary`, `next_action_summary`, and any
`svg_polish_readiness`.

Post-preflight driver state remained `run_critique` for all five fixtures. No
`svg_polish_readiness` route could be validly evaluated without host-vision
critique refresh.

### Task 3: Run Loop Only Where Preconditions Permit

- [x] **Step 1: Check whether critique/adjudication prerequisites are closed**

If driver returns `run_critique`, `run_adjudicate`, or `run_export`, record the
blocker and do not fabricate host-vision or export evidence.

- [x] **Step 2: Run `/fig_loop` only when driver policy indicates it is safe**

Run:

```bash
uv run python3 scripts/fig_loop.py <fixture> --goal "issue59 svg polish promotion dogfood" --json
```

Only use this when render/critique/adjudication prerequisites are already
closed enough for a meaningful checkpoint.

Not run. Driver policy selected `run_critique` for every fixture.

### Task 4: Review Policy And Document Judgment

- [x] **Step 1: Create the milestone**

Record:

- fixture;
- preflight action;
- post-compile action;
- route verdict;
- whether recommendation was useful;
- whether `ready_for_svg_polish` was correctly withheld when blockers remain.

- [x] **Step 2: Update Issue 59**

Change status to implemented or blocked, depending on whether enough real
fixture evidence was collected. If no code defect is found, say no code change
was required.

### Task 5: Verification

- [x] **Step 1: Verify docs-only or code path**

If docs-only:

```bash
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Docs-only verification passed:

- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`

If code changes occur:

```bash
uv run pytest -q tests/test_fig_driver.py tests/test_fig_loop.py tests/test_next_action_summary.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

- [x] **Step 2: Critical review**

Check:

- no source/export/accepted/golden/polish artifact was staged;
- no host-vision result was fabricated;
- `ready_for_svg_polish` did not bypass compile, critique, export, human, crop,
  semantic, aesthetic, accepted, golden, or publication gates;
- Issue 60 can use the evidence for style-pack catalog work.

Review result: clean for negative dogfood. The evidence does not claim positive
SVG polish readiness; it only closes Issue 59 as a safe-withholding check under
stale critique conditions.
