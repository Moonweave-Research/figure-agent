# Issue 100CB - Layout Drift CLI Usage Doc Sync

Status: implemented in branch `codex/issue-100cb-layout-drift-usage-doc`
Type: operator UX, command contract documentation
Priority: P3

## Problem

Issue 100CA hardened `scripts/check_layout_drift.py` so the public CLI no
longer accepts arbitrary fixture-like directories. The script docstring and
argparse positional name still said `<example_dir>`, which implied the old
contract.

That stale help text could make operators think `examples/../outside` or an
ad-hoc sibling directory is an accepted target shape even though the hardened
CLI now rejects it.

## Decision

Update the script-local usage and help text to name the actual accepted forms:

- `<fixture-name>`;
- `examples/<fixture-name>`;
- `.` when invoked from inside a fixture directory by `compile.sh`.

No behavior changes are included.

## Acceptance

- `python3 scripts/check_layout_drift.py --help` shows the narrowed fixture
  target contract.
- Existing layout-drift behavior and tests remain unchanged.

## Verification

- `uv run pytest -q tests/test_check_layout_drift.py`
- `uv run ruff check scripts/check_layout_drift.py`
- `git diff --check`
