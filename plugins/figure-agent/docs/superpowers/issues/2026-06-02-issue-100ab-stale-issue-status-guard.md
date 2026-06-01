# Issue 100AB - Stale Issue Status Guard

Status: implemented

Type: documentation contract, roadmap hygiene, release guard

## Problem

Some completed issue docs still had branch-only or working-tree-only status
headers after the implementation had already landed on `main`.

The stale headers were:

- Issue 16A: `implemented in working tree`;
- Issue 44: `implemented on branch`;
- Issue 49: `implemented on branch`;
- Issue 50: `implemented on branch`.

This matters because future operators and agents use issue headers as routing
signals. A stale branch status can make already-merged work look unfinished.

## Goal

Prevent completed issue headers from claiming that implementation exists only
in a branch or working tree. Historical branch names may remain in body prose
when useful, but the top status header must express current mainline truth.

## Implemented

- Normalized the four stale status headers to `completed on main`.
- Added
  `test_completed_issue_headers_do_not_claim_branch_or_worktree_only()` to
  `tests/test_release_contract.py`.

## Non-Goals

- No runtime behavior changes.
- No release version bump.
- No rewrite of historical issue bodies.
- No fixture/source/export/golden mutation.

## Verification

- Red test failed first on the four stale headers.
- After header updates, the focused release-contract test passed.

## Review Results

1. Documentation truth: completed issue headers no longer imply branch-only or
   working-tree-only state.
2. Scope containment: only issue headers and release-contract coverage changed.
3. Future protection: any new stale branch-only completed header now fails the
   release contract.
