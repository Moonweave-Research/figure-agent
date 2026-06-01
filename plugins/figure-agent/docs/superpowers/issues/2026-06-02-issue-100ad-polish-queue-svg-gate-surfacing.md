# Issue 100AD - Polish Queue SVG Gate Surfacing

Status: implemented

Type: operator workflow, SVG polish triage, queue UX

## Problem

`/fig_drive --mode polish` already computes `svg_polish_gate` and
`svg_polish_readiness` from the latest loop checkpoint. `/fig_queue --mode
polish` copied only the generic action, stop boundary, blocker, actor, and
status fields.

That meant a corpus-level polish queue could say `run_fig_loop` or
`mode_forbidden_action` without showing whether the fixture lacked a current
checkpoint, was still `continue_tikz`, had crop/human/top-tier blockers, or was
actually ready for the bounded SVG polish handoff.

## Goal

Surface the existing SVG polish gate/readiness fields in polish-mode queue
rows and table output without changing driver policy, loosening SVG readiness,
or making blocked rows executable.

## Scope

In scope:

- copy selected `svg_polish_gate` and `svg_polish_readiness` fields from
  `/fig_drive` into `/fig_queue --mode polish` rows;
- expose compact SVG columns in the human-readable table only when rows contain
  SVG polish gate data;
- document the additive row fields.

Out of scope:

- changing `ready_for_svg_polish` rules;
- creating positive real-fixture SVG polish evidence;
- writing recipes, SVG files, exports, accepted state, golden state, or source
  figures;
- making SVG polish a queue-executable action.

## Implemented Behavior

When `mode == polish`, queue rows may include:

- `svg_polish_gate_state`
- `can_start_svg_polish`
- `svg_polish_recommended_path`
- `svg_polish_next_action`
- `svg_polish_blocking_sources`

The table view adds:

- `svg_gate`
- `can_svg`
- `polish_path`
- `polish_next`
- `polish_blockers`

only when at least one row contains these fields. Non-polish modes keep the
same table shape.

## Review Cycles

1. **Contract correctness** - The queue copies existing driver-derived SVG
   fields and does not reinterpret readiness.
2. **Scope containment** - No source, export, SVG, accepted, golden, or
   publication mutation path is added.
3. **Operator readiness** - Corpus-level polish triage now shows why SVG polish
   is blocked or ready without opening one driver JSON per fixture.

## Verification

- `uv run pytest -q tests/test_fig_queue.py`
- `uv run ruff check scripts/fig_queue.py tests/test_fig_queue.py`
- `git diff --check`
