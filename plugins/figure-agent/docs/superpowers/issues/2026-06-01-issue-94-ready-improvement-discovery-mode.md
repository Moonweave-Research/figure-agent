# Issue 94 - Ready Improvement Discovery Mode

Status: completed

Type: operator UX, guided autonomy, non-blocking aesthetic improvement surfacing

Depends on:

- Issue 43 - aesthetic lever grammar
- Issue 70 - operator-grade guided autonomy
- Issue 90 - SVG polish and aesthetic gate hardening
- Issue 93 - content-fresh export status next UX

Design:
`docs/superpowers/specs/2026-06-01-ready-improvement-discovery-design.md`

## Problem

`figure-agent` can now correctly stop at real gates and say a figure is ready
when no in-scope blocker remains. But in real use this creates a confusing
operator experience:

- the plugin may say `complete`;
- the user can still see that the figure could be improved;
- the next improvement must be manually requested;
- optional improvement levers are buried in critique/frontmatter or loop
  checkpoints instead of being surfaced as a clear, non-blocking choice.

The plugin therefore behaves like a quality gate, not a design coach. That is
safe, but it underserves the user's workflow after blocker cleanup.

## Goal

Add a read-only summary that tells the operator whether a ready/safe fixture has
optional improvement candidates.

The summary must be advisory only:

- it never changes release readiness;
- it never permits hidden edits;
- it never bypasses human, host, accepted, golden, export, publication, or SVG
  polish gates;
- it is derived only from structured evidence.

## Expected Behavior

`/fig_driver` JSON may include:

```json
{
  "ready_improvement_summary": {
    "schema": "figure-agent.ready-improvement-summary.v1",
    "state": "ready_but_improvable",
    "safe_to_ship": true,
    "blocks_release": false,
    "auto_patch_allowed": false,
    "candidate_count": 1,
    "candidates": [
      {
        "id": "I001",
        "source": "editorial_art_direction_summary",
        "source_id": "tikz_vs_svg_polish_trigger",
        "type": "tikz_micro_polish",
        "target": "remaining TikZ polish lever",
        "suggested_action": "Review the structured route detail and patch one source-level micro-polish target only if desired.",
        "expected_gain": "low",
        "risk": "low",
        "required_actor": "workflow_agent",
        "allowed_scope": ["examples/<name>/<name>.tex"],
        "reason": "<polish_route_detail>"
      }
    ]
  }
}
```

If no structured optional evidence exists, the summary may say
`ready_no_actionable_improvement`. If blockers exist, it must say `not_ready` or
be omitted.

## Hard Scope

Implement:

- pure extraction helper for ready improvement summaries;
- `/fig_driver` additive output integration;
- tests for ready, improvable, blocked, human-gated, SVG-route, and legacy
  no-op cases;
- docs explaining the contract and non-goals.

Do not implement:

- new slash command;
- automatic source/SVG patching;
- release/accepted/golden mutation;
- changes to `/fig_status` readiness;
- numeric quality gating;
- critique schema changes;
- prose mining from critique body.
- direct findings/adjudication candidate extraction.

## Acceptance Criteria

- Driver output includes a deterministic `ready_improvement_summary` for
  ready/safe review or release states when loop checkpoint evidence is present.
- Optional `continue_tikz` route details become a non-blocking candidate.
- Weak top-tier, aesthetic-lever, and journal-playbook summaries become
  optional candidates when they are non-blocking.
- Human-gated or blocking loop checkpoints do not become optional candidates.
- SVG polish candidates are surfaced only as optional handoff candidates; they
  do not bypass existing SVG polish readiness gates.
- Existing driver action vocabulary and stop boundaries are unchanged.
- Full test suite and lint pass.

## Test Plan

- Unit tests for the helper:
  - complete ready checkpoint with no optional evidence;
  - ready checkpoint with `continue_tikz` route detail;
  - ready checkpoint with weak top-tier slot and no blocker;
  - ready checkpoint with weak aesthetic lever route;
  - human-gated checkpoint returns `not_ready`;
  - no checkpoint returns no summary or no candidates;
  - force-golden status-action checkpoints remain safe manual roll-forward
    states.
- Driver tests:
  - `ACTION_COMPLETE` review result includes advisory candidates when present;
  - release blocked by force-golden can still include `safe_to_ship: true`
    advisory candidates;
  - human gate result does not present optional improvement candidates as next
    work.

## Verification

- `uv run pytest -q tests/test_ready_improvement.py tests/test_fig_driver.py`
- `uv run pytest -q`
- `uv run ruff check .`
- `git diff --check`
- `claude plugin validate .claude-plugin/plugin.json`
- `claude plugin validate .`
- `claude plugin validate ../../.claude-plugin/marketplace.json`

## Review Checklist

1. Contract/schema: additive only, no action vocabulary change, no new blocker.
2. Safety/scope: no hidden edit path, no force-golden/accepted/export mutation.
3. Test readiness: blocked, human-gated, legacy, and optional-improvement paths
   covered.

## Implementation

Implemented a read-only helper in `scripts/ready_improvement.py` and surfaced
its result as additive `/fig_driver` JSON under `ready_improvement_summary`.

The implementation:

- preserves the existing driver action vocabulary and stop boundaries;
- emits no source, SVG, export, accepted, golden, or publication mutation path;
- treats human gates, patch handoff, semantic backport, crop uncertainty,
  top-tier blockers, editorial blockers, and blocked/human aesthetic summaries
  as `not_ready`;
- surfaces optional candidates from current loop checkpoint summaries only:
  editorial route detail, weak top-tier slots, weak aesthetic levers, and weak
  journal-playbook items;
- keeps force-golden/manual roll-forward states safe-to-ship when the latest
  loop checkpoint is otherwise clean.

`fig_driver_checkpoint.py` now preserves
`journal_art_direction_playbook_summary` so the new helper can consume the same
loop evidence that `fig_loop.py` already records.

## Verification Results

- `uv run pytest -q tests/test_ready_improvement.py tests/test_fig_driver.py tests/test_fig_driver_checkpoint.py`
  - Result: 88 passed.
- `uv run pytest -q`
  - Result: 1544 passed, 3 skipped, 1 xfailed, 6 warnings.
- `uv run ruff check .`
  - Result: all checks passed.
- `git diff --check`
  - Result: clean.
- `claude plugin validate .claude-plugin/plugin.json`
  - Result: passed.
- `claude plugin validate .`
  - Result: passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json`
  - Result: passed.

## Review Results

1. Contract/schema review found no action-vocabulary change. One integration
   gap was fixed: release/manual-gate summaries now preserve the loop checkpoint
   when available.
2. Scope/safety review narrowed the design to loop-checkpoint summaries only;
   direct findings/adjudication candidate extraction is deferred to avoid stale
   decision-state ambiguity.
3. Failure-mode review added defensive blocker checks inside the helper itself,
   so malformed or future `complete` summaries with fail/needs_human audit
   evidence return `not_ready` instead of silently reporting no candidates.

No known Issue 94 plugin blocker remains.
