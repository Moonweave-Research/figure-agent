# Issue 100AJ - External Finding Handoff Gate

Status: completed

Type: external review evidence, loop routing, human-gate safety

## Problem

`external_vision_review.yaml` could contain a fresh external finding without a
matching `conflicts[]` entry. In that shape, `/fig_loop` treated the external
review as `passed` because only explicit host-vs-external conflicts were routed
to human review.

That was too weak for the second-opinion route. A reviewer can find a new
BLOCKER/MAJOR/MINOR issue that is not a conflict with an existing host finding;
the plugin should not silently treat that as clean.

## Decision

Fresh external findings are now first-class unresolved evidence unless their
`suggested_action` is `accept_simplification`.

- Fresh review with active conflicts: `needs_human`.
- Fresh review with active findings: `needs_human`.
- Fresh review with no active conflicts or findings: `passed`.
- Stale, missing-artifact, or invalid review state still takes precedence over
  finding/conflict interpretation.

This keeps the provider-agnostic route local and non-mutating. External findings
do not become automatic truth; they force a human adjudication boundary.

## Implemented Contract

- `external_vision_review_summary()` now emits:
  - `unresolved_finding_count`
  - `active_findings` as stable `EV###:SEVERITY` strings
- `/fig_loop` recommended action names the active external finding when there
  is no explicit conflict.
- Existing conflict behavior is unchanged.

## Tests

Covered in:

- `tests/test_external_vision_review.py`
- `tests/test_fig_loop.py`

The tests verify that a fresh external MAJOR finding with no conflict routes to
`needs_human` and that `/fig_loop` surfaces it as a human gate.
