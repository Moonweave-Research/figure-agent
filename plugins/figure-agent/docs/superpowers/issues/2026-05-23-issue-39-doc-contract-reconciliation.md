# Issue 39 — Documentation Contract Reconciliation

**Status:** implemented and verified

## Problem

Several completed issue documents still used branch-local status wording or
unchecked acceptance criteria after their implementation had already landed on
`main`. This creates a planning hazard: future agents may treat implemented
contracts as open work and duplicate or destabilize existing behavior.

## Scope

Docs-only reconciliation for recently completed audit, boundary, aesthetic, and
critique-lint issues:

- Issue 23A-C acceptance criteria now reflect implemented contracts.
- Issue 24A-E status lines now cite the landed implementation commits.
- Issue 27-28 status lines now cite the landed implementation commits.
- Issue 30-32 and Issue 34 status lines now cite their landed commits.
- Issue 35-38 status lines now cite their landed implementation commits.

## Non-Goals

- No script, command, schema, fixture, export, accepted, or golden-state
  behavior changes.
- No generated artifact commits.
- No edits to active figure source files.
- No revalidation of old historical planning checklists outside the recently
  completed implementation docs listed above.

## Verification

```bash
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Also run a status-wording scan over `plugins/figure-agent/docs/superpowers/issues`
to confirm no stale branch-local completion phrasing remains outside this
retrospective note.
