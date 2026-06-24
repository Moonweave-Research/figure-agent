# Issue 100CR - SVG Polish Gate Blocker-Source Filters

Status: implemented

Type: operator workflow, SVG polish evidence, queue UX

Milestone:

- `docs/milestones-archive/2026-06-02-svg-polish-readiness-filter-evidence.md`

## Problem

Issue 100CQ added SVG polish readiness filters to `/fig_queue --mode polish`,
including `--svg-polish-blocking-source`. The first real-fixture evidence pass
found a contract hole: rows blocked by `svg_polish_gate.blocking_items` did not
populate `svg_polish_blocking_sources` unless they also had a
`svg_polish_readiness` object.

Concretely, after a mechanical compile/export pass:

- three fixtures reported `svg_polish_gate_state: no_current_checkpoint`;
- their gate blocker source was `driver_blocker`;
- `--svg-polish-blocking-source driver_blocker` returned zero rows.

That made the new evidence filter incomplete for exactly the polish-gate rows
operators need to inspect.

## Scope

Fix queue evidence projection only. Do not change:

- `ready_for_svg_polish` thresholds;
- driver action selection;
- SVG recipe/executor/delta/manifest behavior;
- source, export, accepted, golden, SVG, or publication mutation boundaries.

## Implemented Contract

`fig_queue.py` now builds `svg_polish_blocking_sources` from both:

- `svg_polish_gate.blocking_items[].source`;
- `svg_polish_readiness.blocking_items[].source`.

Sources are merged in order and deduplicated. Existing readiness-only rows keep
their previous behavior; gate-only rows are now filterable.

## Tests

- `tests/test_fig_queue.py` covers readiness blocking-source filtering.
- `tests/test_fig_queue.py` now also covers gate blocking-source filtering.

## Real-Fixture Evidence

The evidence pass used the new filters after mechanical prerequisites were
advanced in an isolated worktree:

```text
--can-start-svg-polish true -> 0 rows
--svg-polish-blocking-source driver_prerequisite -> 5 critique-refresh rows
--svg-polish-blocking-source driver_blocker -> 3 no-current-checkpoint rows
```

This confirms that real positive SVG polish promotion is still not established,
but the no-ready result is now inspectable without manual JSON traversal.

## Review

1. **Contract correctness** - PASS. Queue rows now expose the blocker sources
   from the same gate object whose state and next action they already expose.
2. **Scope containment** - PASS. The fix is a read-only projection/filter
   correction and does not change SVG polish readiness decisions.
3. **Integration readiness** - PASS. The real-fixture pass now has a repeatable
   blocker breakdown for the next host-vision critique refresh queue.
