# Issue 50 - Real Fixture State Sweep

**Status:** implemented on branch `codex/issue50-real-fixture-state-sweep`
**Builds on:** v0.7.1 release docs sync and Issue 48 SVG polish readiness

## Problem

After Issue 48, the plugin had a clear `svg_polish_readiness` object, but the
next risk moved to cross-surface consistency: `/fig_status` and
`/fig_drive --mode authoring|review|polish|release` must agree on the same
conservative next boundary for real fixtures.

A dry-run sweep found one concrete mismatch on
`fig1_overview_v2_pair_001_vault`: review/release mode respected the tracked
golden human gate, but polish mode still offered `polish_handoff_stop` when no
current loop checkpoint routed `ready_for_svg_polish`.

## Goal

Run a real-fixture state sweep and harden polish mode so SVG polish handoff
cannot start unless a current `/fig_loop` checkpoint explicitly routes
`ready_for_svg_polish`.

## Scope

In scope:

- Run dry-run state evidence across representative real fixtures.
- Fix the no-loop-checkpoint polish fallback.
- Update `/fig_drive` documentation to describe the stricter route.
- Add a regression test for the fallback.
- Record dogfood evidence.

Out of scope:

- Running compile/export/critique on fixtures.
- Mutating fixture source, generated exports, accepted/golden state, or
  publication provenance.
- Changing recipe/executor/delta behavior when a valid `ready_for_svg_polish`
  checkpoint already exists.

## Acceptance Criteria

- With fresh exports but no current loop checkpoint, polish mode returns
  `run_fig_loop` with `mode_forbidden_action`.
- With a current `ready_for_svg_polish` loop checkpoint, polish mode still
  reaches the bounded SVG polish route.
- `continue_tikz`, `needs_human_art_direction`, and
  `semantic_backport_required` routes keep their existing conservative
  behavior.
- Representative fixtures produce a documented state sweep with no remaining
  silent SVG-polish handoff route.
- Focused driver tests, full pytest, ruff, diff check, and Claude plugin
  validation pass.
