# Issue 41 — Canonical Usage Docs Sync

**Status:** implemented and verified

## Problem

Issue 40 fixed command behavior so stale or missing render state takes priority
over stale critique in `/fig_loop`. The user-facing command docs and skill
entrypoint also need to pin that same workflow order; otherwise agents may
still choose `/fig_critique` before `/fig_compile` from memory.

## Scope

Docs-only synchronization of the canonical usage order:

1. `/fig_status` or `/fig_drive --dry-run` is the first check.
2. Stale/missing render routes to `/fig_compile` before critique.
3. Fresh render plus stale/missing/reference-missing critique routes to
   `/fig_critique` or reference repair.
4. Fresh critique plus missing/stale/invalid adjudication routes to
   `/fig_adjudicate` or adjudication repair.
5. `/fig_loop` records verify-only evidence after those prerequisites.
6. Export, release, and polish happen only when status/driver routes there.

## Files

- `skills/figure-agent/SKILL.md`
- `commands/fig_loop.md`
- `commands/fig_drive.md`

## Non-Goals

- No command behavior changes.
- No schema, fixture, export, accepted, or golden-state changes.
- No generated artifact commits.

## Verification

```bash
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```
