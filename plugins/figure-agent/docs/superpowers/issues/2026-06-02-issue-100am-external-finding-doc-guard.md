# Issue 100AM - External Finding Documentation Guard

Status: completed

Type: operator documentation, release-contract guard

## Problem

Issues 100AJ and 100AL made external second-opinion evidence stricter:
unresolved external findings and crop-set drift now stop the loop instead of
silently passing. The highest-traffic docs still described only stale or
conflicting second opinions, which left the new-finding handoff contract easy to
miss.

## Decision

Document that external-review unresolved findings become human-gate evidence,
not automatic truth, in both the README command-surface summary and
`/fig_critique` command instructions.

## Implemented Contract

- README external-vision row names `unresolved findings` and `human gate`.
- `/fig_critique` external-review instruction says fresh unresolved findings or
  explicit conflicts become a `/fig_loop` human gate.
- Release-contract tests fail if either high-traffic doc stops naming that
  boundary.

## Tests

Covered by:

- `tests/test_release_contract.py::test_docs_explain_external_review_findings_are_human_gates`
