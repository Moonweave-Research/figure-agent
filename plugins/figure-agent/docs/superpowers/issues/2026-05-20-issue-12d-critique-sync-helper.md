# Issue 12D: Critique Metadata Sync Helper

**Date:** 2026-05-20 KST
**Status:** completed in commit `3b7ae13`; policy sync extended in `52481fb`
**Type:** AFK workflow ergonomics
**Parent:** `2026-05-20-issue-12-critical-visual-audit-gaps.md`

## What To Build

Add a safe one-shot helper for critique/adjudication freshness maintenance. The
helper must reduce manual hash work without weakening the core rule: a stale
host-vision critique cannot be declared fresh by metadata edits alone.

## Acceptance Criteria

- [x] The helper refreshes `critique_adjudication.yaml` against the current
  `critique.md` content hash when `critique.md` is already fresh.
- [x] The helper refuses metadata-only freshness if `critique_input_hash`,
  `generator_version`, or `rubric_version` mismatch current expectations.
- [x] The helper prints the exact stale reason and the required next command,
  usually `/fig_critique <name>`.
- [x] The helper never rewrites `critique.md` findings or host-authored
  judgments.
- [x] Tests cover fresh, stale-generator, stale-input, missing critique, and
  malformed adjudication cases.

## Implementation Notes

- Implemented as `uv run python3 scripts/critique_adjudication.py sync <name>`.
- `sync` preserves existing adjudication decisions when finding ids match the
  current critique and updates only `source_critique_hash`. Plain sync also
  refuses resolved-state changes that would alter the scaffold meaning.
- If finding ids or resolved-state scaffold shape differ, `sync` refuses to
  guess and requires an explicit `scaffold <name> --force` decision.
- `--force` recreates the adjudication scaffold after freshness checks pass.

## Verification

- `uv run pytest -q tests/test_sync_critique_adjudication.py tests/test_critique_adjudication.py tests/test_status.py tests/test_run_export.py tests/test_fig_driver.py` — 255 passed.
- `uv run pytest -q` — 742 passed, 1 skipped, 1 xfailed.
- `uv run ruff check scripts/critique_adjudication.py tests/test_sync_critique_adjudication.py` — all checks passed.
- `git diff --check` — clean.
- `claude plugin validate .claude-plugin/plugin.json` — passed.
- `claude plugin validate .` — passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` — passed.

## Blocked By

None - can start immediately.
