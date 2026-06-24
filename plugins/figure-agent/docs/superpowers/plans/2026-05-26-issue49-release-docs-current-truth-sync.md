# Issue 49 Release Docs Current-Truth Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align release metadata, README, changelog, closeout status, and Issue 48 docs after the post-v0.7.0 SVG polish readiness work.

**Architecture:** This is a metadata/documentation patch slice. Runtime behavior stays unchanged; release-contract tests guard the current-truth wording so stale branch or Issue 33 priority text cannot silently return.

**Tech Stack:** Markdown docs, JSON plugin manifest, Python project metadata, uv lockfile, pytest release-contract tests.

---

### Task 1: Add Release-Contract Regression Coverage

**Files:**
- Modify: `tests/test_release_contract.py`

- [x] **Step 1: Add a failing test**

Add `test_closeout_status_matches_current_release_truth()` that reads
`.claude-plugin/plugin.json`, the plugin-development closeout milestone, and
the Issue 48 doc. The test asserts:

- closeout contains `current main truth through v{plugin["version"]}`;
- closeout no longer contains `after Issue 33 / PR #47`;
- closeout no longer says `start with Issue 34`;
- closeout mentions `Issue 48`;
- Issue 48 says `implemented on main`;
- Issue 48 no longer says `implemented on branch`.

- [x] **Step 2: Run the focused test and confirm red**

Run:

```bash
uv run pytest -q tests/test_release_contract.py::test_closeout_status_matches_current_release_truth
```

Expected before the docs sync: fail because the closeout milestone still says
`current main truth after Issue 33 / PR #47`.

### Task 2: Sync Release Metadata and Current-Truth Docs

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/milestones-archive/2026-05-21-plugin-development-closeout-status.md`
- Modify: `docs/superpowers/issues/2026-05-26-issue-48-svg-polish-promotion-readiness.md`
- Create: `docs/superpowers/issues/2026-05-26-issue-49-release-docs-current-truth-sync.md`
- Create: `docs/superpowers/plans/2026-05-26-issue49-release-docs-current-truth-sync.md`

- [x] **Step 1: Bump patch version**

Set `.claude-plugin/plugin.json` and `pyproject.toml` from `0.7.0` to `0.7.1`.
Run `uv lock` from the plugin root so `uv.lock` records the same package
version.

- [x] **Step 2: Add changelog entry**

Add `## [0.7.1] - 2026-05-26` above v0.7.0. Document Issue 48 readiness,
closeout/doc reconciliation, and the release-contract guard.

- [x] **Step 3: Update README current-state header**

Change `Current state (v0.7.0)` to `Current state (v0.7.1)` and fold
`svg_polish_readiness` into the SVG polish handoff description.

- [x] **Step 4: Update closeout milestone**

Make the milestone describe current main truth through v0.7.1 / Issue 48,
replace stale verification counts, add Issue 34-48 closed-track coverage, and
replace the old Issue 34 priority list with the current next work list.

- [x] **Step 5: Update Issue 48 status**

Change the status line to `implemented on main in commit ef1fda9` so future
agents do not treat the issue as branch-local work.

### Task 3: Verify and Commit

**Files:**
- All files changed by Task 1 and Task 2.

- [x] **Step 1: Run focused release contract test**

Run:

```bash
uv run pytest -q tests/test_release_contract.py
```

Expected: all release-contract tests pass.

- [x] **Step 2: Run full verification**

Run from `plugins/figure-agent`:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: pytest passes, ruff clean, diff whitespace clean, and all three
Claude plugin validation commands pass.

- [x] **Step 3: Review the diff**

Confirm the diff is restricted to release metadata, documentation, and the
release-contract test. Confirm no generated build/export artifacts, fixture
source, accepted/golden state, or publication provenance files are staged.

- [x] **Step 4: Commit**

Commit the release/docs sync with:

```bash
git add plugins/figure-agent/.claude-plugin/plugin.json \
  plugins/figure-agent/pyproject.toml \
  plugins/figure-agent/uv.lock \
  plugins/figure-agent/README.md \
  plugins/figure-agent/CHANGELOG.md \
  plugins/figure-agent/tests/test_release_contract.py \
  plugins/figure-agent/docs/milestones-archive/2026-05-21-plugin-development-closeout-status.md \
  plugins/figure-agent/docs/superpowers/issues/2026-05-26-issue-48-svg-polish-promotion-readiness.md \
  plugins/figure-agent/docs/superpowers/issues/2026-05-26-issue-49-release-docs-current-truth-sync.md \
  plugins/figure-agent/docs/superpowers/plans/2026-05-26-issue49-release-docs-current-truth-sync.md
git commit -m "Sync v0.7.1 release docs"
```
