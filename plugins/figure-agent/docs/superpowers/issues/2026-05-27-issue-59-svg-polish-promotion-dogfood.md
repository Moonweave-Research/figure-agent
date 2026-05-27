# Issue 59 - SVG Polish Promotion Dogfood

Status: evidence closed - polish route withheld behind stale critique gates

Depends on: Issue 58 single next-action UX

## Problem

The SVG polish route exists and is bounded, but the production promotion policy
is still conservative. The plugin can say `continue_tikz`,
`ready_for_svg_polish`, `semantic_backport_required`, or
`needs_human_art_direction`, but the real-fixture evidence is not yet broad
enough to treat SVG polish as a routine stage.

The risk is two-sided:

- promoting too early hides semantic/source problems behind SVG edits;
- promoting too late traps optical finish work in TikZ when SVG is the right
  handoff layer.

## Goal

Dogfood SVG polish readiness across real fixtures and tighten the promotion
policy until the route is predictable, explainable, and safe.

## Order

Run this after Issue 58 so the route is surfaced through the same single
next-action contract.

## Scope

In scope:

- Select three to five real fixtures with different states:
  - a clean semantic figure that may be ready for SVG polish;
  - a figure that should remain `continue_tikz`;
  - a figure that should trigger `semantic_backport_required`;
  - a figure with human art-direction uncertainty if available.
- Run `/fig_drive --mode polish --dry-run`, `/fig_loop`, and relevant closeout
  checks.
- Record whether the route matched the real evidence.
- Tighten docs/tests if a route is ambiguous.
- Keep SVG polish as explicit handoff or bounded recipe execution.

Out of scope:

- Inventing new SVG polish edits.
- Editing figure source.
- Promoting accepted/golden artifacts.
- Treating SVG polish as a journal-acceptance guarantee.
- External vision integration.

## Acceptance

- A dogfood milestone records all selected fixtures, route verdicts, blocker
  sources, and whether the recommendation was useful.
- `ready_for_svg_polish` is not emitted when human, semantic, crop, aesthetic,
  publication, or freshness blockers remain.
- `semantic_backport_required` is distinguishable from optical-only polish.
- Any policy change is covered by focused tests.
- No generated polish/export artifacts are committed unless explicitly part of
  a later release artifact policy.

## Review Questions

1. Is the route evidence strong enough to let an outer agent stop TikZ work?
2. Does `ready_for_svg_polish` remain subordinate to all safety gates?
3. Is SVG polish being used for optical finish only, not semantic repair?
4. Does the route help the user decide when to stop source-level iteration?

## Evidence Notes

- Added `docs/milestones/2026-05-28-svg-polish-promotion-dogfood.md`.
- Ran `/fig_drive --mode polish --dry-run` on five real fixtures after Issue 58:
  `fig1_overview_v2_pair_001_vault`, `fig1_overview_v2`,
  `golden_trap_depth_picture`, `n3_trial_01_trap_depth`, and
  `n3_trial_02_actuation_sequence`.
- All five fixtures had `render_state: FRESH` and `critique_state: STALE`.
- All five selected `action: run_critique` with
  `stop_boundary: host_llm_critique_required`.
- No fixture emitted `ready_for_svg_polish`, which is the correct conservative
  behavior while the host-vision critique is stale.
- No source, export, accepted, golden, publication provenance, or polished-SVG
  artifact was edited.

Positive real-fixture SVG polish promotion remains unproven. The next valid
attempt must first refresh a host-vision critique and adjudication state for a
candidate fixture.
