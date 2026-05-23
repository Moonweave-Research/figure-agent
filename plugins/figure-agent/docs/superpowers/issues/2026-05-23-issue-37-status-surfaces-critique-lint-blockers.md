# Issue 37 — Status Surfaces Critique Lint Blockers

**Status:** implemented in branch `codex/issue36-fig1-critique-refresh`

## Problem

`critique_lint.py` now enforces audit accountability contracts such as crop
reads, visual-clash accounting, text-boundary accounting, and aesthetic-intent
anchor usage. However `/fig_status` currently reports only critique freshness.

That leaves a workflow gap: a hash-fresh `critique.md` can still be invalid
under current lint rules, while status/driver may appear ready to proceed to
adjudication or export. The command docs tell users to run lint before
adjudication, but the canonical status surface should expose this blocker
directly.

## Goal

When `critique_state == FRESH`, `/fig_status` should run critique lint as a
read-only check. If lint returns blocker violations, status should add a
`critique_lint_blocked` note and point the user back to `/fig_critique <name>`.

## Scope

In scope:

- Status-only surfacing of critique lint blockers.
- Status explanation and next-action hint integration.
- Tests for blocker and clean legacy behavior.

Out of scope:

- Changing the public critique freshness enum.
- Running lint when critique is missing or stale.
- Auto-mutating critique, adjudication, export, accepted, or golden state.
- Changing `critique_lint.py` contracts.

## Acceptance Criteria

- A fresh critique that fails lint causes `/fig_status` to include
  `critique_lint_blocked`.
- The first blocker explanation points to `/fig_critique <name>` and is marked
  manual.
- The next hint routes to `/fig_critique <name>` before export/adjudication.
- Fixtures without lint blockers preserve existing status behavior.

## Implementation Notes

- `/fig_status` runs `critique_lint.py` only when `critique_state == FRESH`.
- Lint failures add `critique_lint_blocked` while preserving the existing public
  critique freshness enum.
- The status explanation surfaces the blocker as fixture freshness with
  `/fig_critique <name>` as the manual next command.
- The next-action policy routes `critique_lint_blocked` back through
  `/fig_critique <name>` before export/adjudication continuation.
