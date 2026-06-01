# Issue 100AK - Inventory Baseline Freshness Guard

Status: completed

Type: roadmap hygiene, release-contract guard

## Problem

Issue 100AI guarded the inventory status header and code-surface counts, but
the same document still described the branch baseline as `main` after Issue 99.
After many completed Issue 100 slices, that stale baseline could mislead future
review loops into treating already-mainline work as out-of-date context.

## Decision

Extend the release-contract guard so the Issue 100 inventory baseline line must
track the same latest Issue 100 suffix as the status header.

## Implemented Contract

- The Issue 100 inventory now says the branch baseline is `main` after the
  latest Issue 100 slice.
- `tests/test_release_contract.py` fails if the baseline line drifts behind the
  latest `Issue 100*` suffix named in the inventory.

## Tests

Covered by:

- `tests/test_release_contract.py::test_issue_100_inventory_header_and_surface_counts_match_current_tree`
