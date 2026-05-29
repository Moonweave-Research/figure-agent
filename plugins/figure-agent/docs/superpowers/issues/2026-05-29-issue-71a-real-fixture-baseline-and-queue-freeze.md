# Issue 71A - Real Fixture Baseline And Queue Freeze

Status: proposed

Depends on: Issue 71 roadmap

Type: AFK

## Problem

The fixture corpus contains production candidates, smoke fixtures, support
folders, accepted/golden fixtures, and stale dogfood outputs. A generic
`status.py` sweep is useful, but not enough for later agents to know which
fixtures are supposed to be worked on and which are intentionally not
production targets.

## Goal

Create a current fixture queue that separates production targets from
support/smoke fixtures and freezes the starting state for Issue 71 dogfood.

## Scope

In scope:

- Run `uv run python3 scripts/status.py` from `plugins/figure-agent`.
- Run `/fig_drive --dry-run` equivalents for all production candidate fixtures
  in review, release, and polish modes.
- Create a milestone matrix that records state, next action, owner, and whether
  the fixture belongs to 71B, 71C, 71D, 71E, or deferred support.
- Record support/smoke folders explicitly so they do not look like failed
  production targets.
- Keep generated artifacts untracked.

Out of scope:

- Host critique writing.
- Source edits.
- Export or force-golden mutation.
- Accepted/publication state changes.
- New code behavior.

## Acceptance

- A milestone under `docs/milestones/` records the fixture matrix and current
  queue.
- Every `examples/*/spec.yaml` fixture is classified.
- The milestone names the exact child issue that owns each non-clean state.
- `git status --short --untracked-files=no` shows no tracked fixture source,
  critique, accepted/golden, publication, or generated artifact mutation.
- Verification includes `git diff --check`, `uv run pytest -q tests/test_fig_run.py
  tests/test_fig_driver.py tests/test_status.py`, and plugin validation.

## Review Questions

1. Are support folders separated from real production fixtures?
2. Are stale critiques assigned to HITL 71B rather than Codex-only work?
3. Are accepted/golden/publication states assigned to 71E rather than automatic
   work?
4. Is the queue specific enough for a fresh agent to continue without another
   broad sweep?
