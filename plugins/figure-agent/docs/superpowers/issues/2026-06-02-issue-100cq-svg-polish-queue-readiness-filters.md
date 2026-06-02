# Issue 100CQ - SVG Polish Queue Readiness Filters

Status: implemented

Type: operator workflow, SVG polish evidence, queue UX

## Problem

Issue 100CP aligned SVG polish gate messaging with compile/export
prerequisites, but the real-fixture SVG polish promotion question still
required manual JSON filtering. `/fig_queue --mode polish` surfaced
`can_start_svg_polish`, `svg_polish_gate_state`, route, next action, and
blocking sources, but operators could not directly ask for "only fixtures that
can start SVG polish" or "only fixtures blocked by the TikZ-vs-SVG trigger".

That made positive real-fixture evidence harder to gather and repeat. The data
existed, but the command surface did not expose the evidence query.

## Scope

Add read-only filters over existing queue row fields. Do not change:

- driver action selection;
- `ready_for_svg_polish` thresholds;
- SVG recipe/executor/delta behavior;
- source, export, accepted, golden, SVG, or publication state.

## Implemented Contract

`scripts/fig_queue.py --mode polish` now accepts:

- `--svg-polish-gate-state <state>`;
- `--can-start-svg-polish true|false`;
- `--svg-polish-recommended-path <route>`;
- `--svg-polish-next-action <action>`;
- `--svg-polish-blocking-source <source>`.

The filters run after driver rows are built, like the existing actor/action
filters. Boolean matching is explicit for `can_start_svg_polish`; list matching
uses containment for `svg_polish_blocking_sources`.

## Tests

- `tests/test_fig_queue.py` verifies `--can-start-svg-polish true` keeps only
  ready SVG polish candidates.
- `tests/test_fig_queue.py` verifies `--svg-polish-blocking-source` matches
  rows whose blocking-source list contains the requested source.

## Review

1. **Contract correctness** - PASS. The filter surface queries existing row
   evidence only; it does not infer readiness independently.
2. **Scope containment** - PASS. No mutation path, recipe path, route threshold,
   or release gate changed.
3. **Integration readiness** - PASS. The command docs now provide a direct
   real-fixture promotion evidence query:
   `uv run python3 scripts/fig_queue.py --mode polish --can-start-svg-polish true`.
