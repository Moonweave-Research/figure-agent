# Issue 100AI - Gap Inventory Freshness Guard

Status: implemented

Type: roadmap hygiene, documentation drift guard, release contract

## Problem

The Issue 100 gap inventory is the active whole-plugin review ledger. After
Issues 100AG and 100AH, the inventory body listed the new slices but its status
header still said the roadmap was current only through Issue 100AF. The same
document also carried stale code-surface counts.

That makes the roadmap less trustworthy as the source of truth for deciding the
next whole-plugin review target.

## Contract

- The Issue 100 inventory header must name the latest `Issue 100*` suffix
  referenced in the document body.
- The code-surface inventory count must match the current number of top-level
  Python scripts, pytest modules, and slash command docs.
- The guard is intentionally limited to freshness metadata. It does not judge
  whether every roadmap item is complete.

## Implementation

- Updated the Issue 100 status header through Issue 100AI.
- Updated the code-surface count to the current tree.
- Added a release-contract pytest that derives both values from the current
  repository and fails if the inventory drifts again.

## Verification

- `uv run pytest -q tests/test_release_contract.py -q`
- `uv run pytest -q`
