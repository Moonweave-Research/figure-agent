# Issue 100CN - Inventory Next-Analysis Freshness Guard

Status: implemented
Type: roadmap hygiene, release contract, operator UX
Priority: P3

## Problem

Issue 100 inventory freshness guards already kept the header, branch baseline,
issue-file suffix, completion summaries, and issue-status headers aligned.

After Issue 100CM, the inventory still had a stale `Additional Update Analysis`
section saying the next urgent work was Issue 100A and Issue 100B/C. Those
slices had long since been implemented. The stale prose was not a code failure,
but it was an operator-routing failure: future agents could read the inventory
as the live roadmap and restart already-completed work.

## Contract

Extend release-contract coverage so the `Additional Update Analysis` section
must stay current with the latest Issue 100 suffix on disk:

- compute the latest Issue 100 suffix from issue files;
- require the update-analysis section to mention that suffix;
- reject stale "next candidate" wording that points back to Issue 100A or
  Issue 100B/C as future work.

## Acceptance

- TDD reproduces the stale inventory passing older freshness guards while the
  update-analysis section omits Issue 100CM and still names Issue 100A-C as
  next work.
- The inventory is rewritten to describe the current post-100CM candidates:
  real-fixture SVG polish promotion evidence, operator completion explanation,
  and installed-cache refresh after dirty figure work is resolved.
- The new release-contract test passes with the updated inventory.

## Verification

- `uv run pytest -q tests/test_release_contract.py`
- `uv run pytest -q`
- `uv run ruff check tests/test_release_contract.py`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`
