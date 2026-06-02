# Issue 100CT - Inventory Version Consistency Guard

Status: implemented

Type: roadmap metadata, release contract, documentation hygiene

## Problem

The live release metadata had advanced to v0.9.2:

- `.claude-plugin/plugin.json`
- `pyproject.toml`
- `README.md` current-state heading

But the Issue 100 inventory's Documentation Consistency Check still claimed
the current plugin was v0.9.1. Existing release-contract tests verified the
README, manifest, and pyproject versions, but did not verify the inventory's
own version sentence.

## Impact

The Issue 100 inventory is the active whole-plugin review ledger. If its
metadata can drift while release metadata is correct, future operators can use
the roadmap as stale evidence and misjudge whether they are reviewing the
current plugin state.

## Implementation

- Updated the inventory status and branch baseline through Issue 100CT.
- Updated the Documentation Consistency Check to name v0.9.2.
- Added a release-contract test that reads `.claude-plugin/plugin.json` and
  requires the Issue 100 inventory consistency section to mention the same
  live plugin version.

## Tests

`tests/test_release_contract.py` now includes
`test_issue_100_inventory_consistency_check_matches_plugin_version`.

The test was first observed failing against the stale v0.9.1 inventory text,
then passed after the inventory update.

## Review

1. **Contract correctness**
   The guard ties the roadmap's version statement to the manifest instead of a
   hard-coded remembered version.

2. **Scope containment**
   No command behavior, fixture source, export, accepted/golden, or plugin
   manifest changed.

3. **Future maintainability**
   Future version bumps already update README/manifest/pyproject through
   release-contract tests; this slice adds the inventory to that same drift
   surface.
