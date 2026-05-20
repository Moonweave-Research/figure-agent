# Issue 12D: Critique Metadata Sync Helper

**Date:** 2026-05-20 KST
**Status:** open
**Type:** AFK workflow ergonomics
**Parent:** `2026-05-20-issue-12-critical-visual-audit-gaps.md`

## What To Build

Add a safe one-shot helper for critique/adjudication freshness maintenance. The
helper must reduce manual hash work without weakening the core rule: a stale
host-vision critique cannot be declared fresh by metadata edits alone.

## Acceptance Criteria

- [ ] The helper refreshes `critique_adjudication.yaml` against the current
  `critique.md` content hash when `critique.md` is already fresh.
- [ ] The helper refuses metadata-only freshness if `critique_input_hash`,
  `generator_version`, or `rubric_version` mismatch current expectations.
- [ ] The helper prints the exact stale reason and the required next command,
  usually `/fig_critique <name>`.
- [ ] The helper never rewrites `critique.md` findings or host-authored
  judgments.
- [ ] Tests cover fresh, stale-generator, stale-input, missing critique, and
  malformed adjudication cases.

## Blocked By

None - can start immediately.

