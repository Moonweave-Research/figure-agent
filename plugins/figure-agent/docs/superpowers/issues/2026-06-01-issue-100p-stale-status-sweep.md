# Issue 100P - Stale Issue Status Sweep

Status: completed

Type: documentation hygiene, operator safety

## Problem

Some Issue 100 documents still described already-merged work as branch-local or
pending commit work. That stale wording is risky because future operators and
agents can treat completed capabilities as unresolved backlog, especially in a
large plugin where issue headers are often used as the first routing signal.

## Scope

This issue is docs-only. It does not change runtime behavior, schemas, command
contracts, tests, fixture sources, accepted state, golden state, exports, SVG
polish state, or publication state.

## Implemented Behavior

- Cleared stale `verified and pending commit` headers from:
  - Issue 100F - advisory-vs-blocking aesthetic language;
  - Issue 100G - run-history basin and repeated-defect detector.
- Normalized already-mainline Issue 100 headers from branch-only wording to
  main commit references:
  - Issue 100E - reference-learning template;
  - Issue 100R - diagnostic artifact provenance rule;
  - Issue 100J - resumable guided run checkpoint;
  - Issue 100H/I - schema and module maps;
  - Issue 100N/O - freshness diagnostics and detector feedback.
- Updated the comprehensive Issue 100 inventory so G100-16 and the Track D
  execution order describe the current cleanup rather than older historical
  sweeps.

## Non-Goals

- No branch deletion or worktree cleanup beyond this feature branch.
- No status changes for unrelated legacy issues outside the current Issue 100
  roadmap.
- No runtime or fixture mutation.

## Review Notes

Review 1 - stale marker coverage:

- `pending commit` now only appears in historical milestone prose, not active
  Issue 100 headers.
- Current Issue 100 completed work uses main commit references where available.

Review 2 - scope containment:

- The diff is documentation-only.
- No generated artifacts, fixture source, accepted/golden/export, SVG, or
  publication files are touched.

Review 3 - integration readiness:

- The comprehensive inventory now points future operators at completed work
  correctly and keeps remaining open backlog separate from already-merged
  capabilities.

## Verification

Run before closing:

```bash
uv run pytest -q tests/test_release_contract.py tests/test_command_contract_docs.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```
