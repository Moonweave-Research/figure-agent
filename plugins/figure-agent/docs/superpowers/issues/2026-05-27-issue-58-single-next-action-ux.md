# Issue 58 - Single Next Action UX

Status: implemented in branch `codex/issue58-single-next-action-ux`

Depends on: Issue 57 real fixture audit adoption

## Problem

The plugin now exposes many useful states: render freshness, critique
freshness, lint blockers, adjudication, crop audit, aesthetic levers,
journal playbooks, SVG polish readiness, golden gates, publication gates, and
closeout checks. This is correct for auditability, but it makes the operator's
main question harder than it should be:

```text
What is the one next safe action?
```

When that answer is unclear, agents can loop inside compile, skip critique,
request humans too early, or attempt export/polish out of order.

## Goal

Add a compact, read-only next-action summary that makes `/fig_status`,
`/fig_drive`, `/fig_loop`, and `/fig_closeout` agree on the next safe step
without weakening any existing gate.

## Order

Run this after Issue 57 so the UX is tested against real adopted fixture states.
Run it before SVG polish promotion work, because polish routing should consume
the same canonical next-action contract.

## Scope

In scope:

- Define a single compact object, for example `next_action_summary`, with:
  - `action`;
  - `reason`;
  - `blocking_source`;
  - `safe_command`;
  - `requires_human`;
  - `allowed_scope`;
  - `forbidden_scope`;
  - `evidence_refs`.
- Keep existing detailed fields intact.
- Make the summary read-only and deterministic.
- Ensure `/fig_drive --dry-run` remains the canonical action selector.
- Add tests for precedence among compile, critique, adjudication, human gate,
  TikZ patch, SVG polish, export, golden, and publication states.

Out of scope:

- New action vocabulary unless an existing action cannot express a real state.
- Hidden execution.
- Auto-patching.
- Mutating accepted/golden/export state.
- Removing detailed diagnostic fields.

## Acceptance

- For a fixture in every major workflow state, the top-level next action is
  stable, explainable, and points to one command or one human gate.
- Existing status/driver/loop tests continue to pass.
- No existing stop boundary is bypassed or demoted.
- The summary is compact enough to be shown at the top of command output.
- Docs explain that detailed audit fields remain available below the summary.

## Review Questions

1. Does the summary hide any blocker that should remain visible?
2. Does it conflict with `/fig_drive` action selection?
3. Can an agent still choose compile/export/polish out of order?
4. Is human review requested only when the state actually needs human judgment?

## Design Constraint

The summary should compress evidence, not reinterpret it. The source of truth
remains the existing state vector and loop checkpoint contracts.

## Implementation Notes

- Added `scripts/next_action_summary.py` as the shared read-only adapter for
  `/fig_status`, `/fig_drive`, `/fig_loop`, and `/fig_closeout`.
- Added `tests/test_next_action_summary.py` plus integration assertions in
  status, driver, loop-record, and closeout tests.
- Wired `next_action_summary` into existing JSON/status dictionaries without
  changing `/fig_drive` action selection, action vocabulary, stop boundaries,
  or mutation behavior.
- Updated command docs and added
  `docs/milestones/2026-05-28-single-next-action-ux.md`.
- No figure source, export, accepted, golden, or generated build artifact was
  changed.
