# Issue 100CC - Inventory Issue-File Freshness Guard

Status: completed on main in merge commit `58a6343`
Type: roadmap documentation guard, release contract
Priority: P3

## Problem

Issue 100AI and Issue 100AK made the comprehensive gap inventory check its own
header and baseline against the latest `Issue 100*` suffix mentioned inside the
inventory document.

That was not enough once later slices were added as separate issue files. After
Issues 100CA and 100CB landed, the inventory could still pass the release
contract while saying it was current only through Issue 100BZ, because the guard
never compared the inventory against the actual issue files on disk.

## Contract

The release contract must compute the latest Issue 100 suffix from the issue
files themselves, not only from the inventory text, and require the inventory to
name that suffix in both:

- the status header;
- the branch-baseline line.

Combined historical files such as `Issue 100H/I` and `Issue 100N/O` count as
their individual single-letter issues, not as synthetic suffixes `100HI` or
`100NO`.

## Acceptance

- A stale inventory header fails when a newer `docs/superpowers/issues/*issue-100*.md`
  file exists.
- Combined issue files do not force impossible synthetic suffixes.
- The comprehensive inventory records Issues 100CA, 100CB, and this guard.

## Verification

- `uv run pytest -q tests/test_release_contract.py::test_issue_100_inventory_tracks_latest_issue_file_suffix`
- `uv run pytest -q tests/test_release_contract.py`
- `uv run ruff check tests/test_release_contract.py`
- `git diff --check`
