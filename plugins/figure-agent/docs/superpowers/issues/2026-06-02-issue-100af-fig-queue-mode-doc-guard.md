# Issue 100AF - Fig Queue Mode Documentation Guard

Status: implemented

Type: command contract, documentation drift guard, release contract

## Problem

`/fig_queue` delegates mode selection to `fig_driver.MODES`, which currently
includes `authoring`, `review`, `release`, `polish`, and `final`. The command
documentation listed only `authoring`, `review`, `release`, and `polish`.

That made the final-readiness queue path discoverable from code but not from
the operator-facing command contract.

## Goal

Keep `/fig_queue` command documentation synchronized with the driver mode
vocabulary so future mode additions cannot silently drift out of the docs.

## Scope

In scope:

- add `final` to `/fig_queue` examples and mode contract;
- add a release-contract test that every `fig_driver.MODES` entry appears in
  `commands/fig_queue.md`.

Out of scope:

- changing driver modes;
- changing final-mode policy;
- changing queue execution behavior;
- mutating source figures, exports, accepted/golden, publication, or SVG state.

## Implemented Behavior

`commands/fig_queue.md` now documents `--mode final`, and
`tests/test_release_contract.py` fails when a mode in `fig_driver.MODES` is not
named in the command doc.

## Review Cycles

1. **Contract correctness** - PASS. The test imports the actual mode tuple from
   `fig_driver`, so it tracks code truth rather than duplicating a stale list.
2. **Scope containment** - PASS. This is a docs/test guard only; no runtime
   queue behavior changes.
3. **Operator readiness** - PASS. Operators can now discover corpus-level final
   readiness triage from the queue docs.

## Verification

- `uv run pytest -q tests/test_release_contract.py`
- `uv run ruff check tests/test_release_contract.py`
- `git diff --check`
