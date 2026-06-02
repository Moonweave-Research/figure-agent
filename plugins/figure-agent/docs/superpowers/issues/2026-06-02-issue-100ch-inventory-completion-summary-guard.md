# Issue 100CH - Inventory Completion-Summary Guard

Status: implemented in branch `codex/issue-100ch-inventory-completion-summary`
Type: roadmap hygiene, release-contract documentation guard
Priority: P3

## Problem

Issue 100CC made the Issue 100 inventory header and baseline track the latest
Issue 100 file suffix. Later work showed another stale-document surface: the
inventory header and gap table tracked through Issue 100CG, but the
`Recommended Execution Order` completion summaries stopped at Issue 100BS.

That made the inventory look current at the top while its operator-facing
status briefing omitted completed work from Issue 100BT onward.

## Contract

The Issue 100 inventory must keep three status surfaces synchronized with the
latest Issue 100 file suffix on disk:

- status header;
- branch baseline line;
- `Recommended Execution Order` completion summary.

## Acceptance

- The release-contract test fails when a new Issue 100 file exists but the
  completion-summary section omits that suffix.
- The inventory completion-summary section is updated through Issue 100CH.
- Header and branch baseline remain guarded by the existing tests.

## Verification

- `uv run pytest -q tests/test_release_contract.py`
- `uv run pytest -q tests/test_plugin_install_freshness.py tests/test_release_contract.py`
- `uv run ruff check tests/test_release_contract.py`
- `git diff --check`
