# Issue 42B — SVG Polish Handoff Routing UX

**Status:** implemented on main through Issue 45 SVG polish route UX
**Builds on:** Issue 42 SVG polish handoff scaffolder

## Problem

Issue 42 added `scripts/svg_polish_handoff.py`, but the existing operator
surfaces still used generic phrasing such as "recreate the polish manifest" or
"see /fig_loop SVG Polish Handoff." That left the new helper discoverable only
through docs, not through the normal `/fig_status` and `/fig_drive --mode
polish` routing loop.

## Scope

Wire the new scaffolder into existing read-only UX:

- `/fig_status` next-action hints for missing, stale, and blocked polished-SVG
  final artifacts should name `scripts/svg_polish_handoff.py`.
- `/fig_drive --mode polish` reasons for visual-only SVG handoff should name the
  same helper once `polish/<name>.polished.svg` exists.

## Non-Goals

- No new action vocabulary.
- No automatic SVG editing.
- No automatic manifest execution by the driver.
- No accepted/golden mutation.

## Acceptance Criteria

- Status next-policy tests prove missing/stale/blocked final-artifact hints
  route through `scripts/svg_polish_handoff.py`.
- Driver polish-mode tests prove visual-only handoff reasons mention
  `scripts/svg_polish_handoff.py`.
- Existing driver action/stop-boundary contracts remain unchanged.
