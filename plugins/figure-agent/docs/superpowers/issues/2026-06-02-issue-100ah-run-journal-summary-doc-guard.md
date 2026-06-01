# Issue 100AH - Run Journal Summary Doc Guard

Status: implemented

Type: operator UX, documentation drift guard, release contract

## Problem

Issue 100J added `scripts/fig_run_journal.py` so interrupted `/fig_run`
sessions can be summarized without replaying stale commands. The detailed
`/fig_run` command doc covered that helper, but the README and agent-facing
SKILL still said only to inspect the prior journal as context.

That left a practical continuation gap: a fresh agent could still dig through
raw `.scratch/fig-run-runs/` JSON instead of using the safe summary command.

## Contract

- README and SKILL continuation guidance must name
  `scripts/fig_run_journal.py`.
- Both documents must also say not to replay commands from a journal.
- The command remains read-only and non-authoritative; live `/fig_status` or
  `/fig_drive` remains the continuation authority.

## Implementation

- Updated README autonomous-run guidance to route interrupted sessions through
  `uv run python3 scripts/fig_run_journal.py <name>`.
- Updated SKILL autonomous-run guidance with the same continuation path.
- Added a release-contract pytest so future edits cannot hide the summary
  helper from the two highest-traffic docs.

## Verification

- `uv run pytest -q tests/test_release_contract.py -q`

