# Issue 100CI - Stale Issue-Status Recurrence Guard

Status: implemented
Type: roadmap hygiene, release-contract documentation guard
Priority: P3

## Problem

Issue 100P and Issue 100AB previously swept stale issue-status headers, but the
release-contract guard only rejected a narrow phrase set:

- `implemented on branch`
- `implemented in working tree`

Later merged Issue 100 documents used `implemented in branch ...` instead. That
wording survived after merge even though git history and the Issue 100 inventory
already treated the work as mainline-complete.

This is an operations leak, not just a prose nit: agents can read a merged issue
as branch-only work, reopen completed slices, or distrust the plugin release
state even when the code and tests are current.

## Contract

Completed issue headers must not claim branch-only, worktree-only, or pending
state after the work is represented as mainline-complete.

The release-contract guard must reject these stale header forms:

- `implemented in branch`
- `implemented on branch`
- `implemented in working tree`
- `implemented in worktree`
- `pending commit`
- `pending merge`

## Acceptance

- The existing stale-status release-contract test fails against the old guard
  while Issue 100BV-100CH headers still contain `implemented in branch`.
- The test is widened to reject the full stale phrase set.
- Current Issue 100BV-100CH headers are normalized to main merge-commit truth.
- The Issue 100 inventory tracks this recurrence as Issue 100CI and keeps its
  header, branch baseline, gap table, and completion summary synchronized.

## Verification

- `uv run pytest -q tests/test_release_contract.py::test_completed_issue_headers_do_not_claim_branch_or_worktree_only`
- `uv run pytest -q tests/test_release_contract.py`
- `uv run ruff check tests/test_release_contract.py`
- `git diff --check`
