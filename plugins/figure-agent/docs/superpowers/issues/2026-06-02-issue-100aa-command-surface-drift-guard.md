# Issue 100AA - Command Surface Drift Guard

Status: implemented

Type: documentation contract, operator UX, release guard

## Problem

The plugin had command docs for `/fig_closeout` and `/fig_e2e_smoke`, but the
README Core commands list did not name them. `/fig_closeout` was especially
confusing because the same README later tells operators to use it after each
patch target.

This kind of drift makes the plugin feel less coherent: a user can read the
main command list and still miss a command that is part of the actual workflow.

## Goal

Keep the README Core commands list aligned with every `commands/fig_*.md`
slash-command document. If a new command doc is added, release-contract tests
should fail until the command is either documented in the core list or the
contract is deliberately revised.

## Implemented

- Added `/fig_closeout` and `/fig_e2e_smoke` to README Core commands.
- Added `test_readme_core_commands_cover_command_docs()` to
  `tests/test_release_contract.py`.

## Non-Goals

- No command behavior changes.
- No new slash command.
- No runner, status, loop, export, or critique contract changes.
- No generated fixture artifact changes.

## Verification

- Red test failed first with missing `/fig_closeout` and `/fig_e2e_smoke`.
- After README update, the focused release-contract test passed.

## Review Results

1. Operator UX: the main command list now matches the command docs and no longer
   hides post-patch closeout or deterministic smoke testing.
2. Scope containment: docs and release-contract tests only.
3. Future protection: new command docs now force README command-surface review.
