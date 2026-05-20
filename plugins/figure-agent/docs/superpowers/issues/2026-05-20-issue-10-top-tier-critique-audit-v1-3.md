# Issue 10: Top-Tier Critique Audit v1.3

**Date:** 2026-05-20 KST
**Status:** completed on main
**Type:** AFK schema/docs/tests, HITL dogfood after implementation

## Problem

The current v1.2 critique contract catches many local defects, but it can still
under-audit the qualities that distinguish a merely clean manuscript figure from
a top-tier journal figure: immediate message, novelty support, target-journal
fit, cross-panel visual grammar, reader misinterpretation risk, and print-scale
robustness.

## Goal

Implement the v1.3 top-tier audit contract from
`docs/superpowers/specs/2026-05-20-top-tier-critique-audit-v1-3-design.md`.

## Current Repo Truth

The main branch already contains the v1.3 brief/schema/rubric surfaces and
baseline v1.3 adjudication validation. The remaining Issue 10 risk is contract
hardening: top-tier audit slots must not pass as decorative prose when they
raise `fail`, `needs_human`, or high-impact-blocking `weak` verdicts.

## Acceptance Criteria

- [x] `/fig_critique` brief includes a mandatory
  `## Top-Tier Journal Figure Audit` section.
- [x] Output schema advances to `figure-agent.critique.v1.3`.
- [x] Rubric version advances to `figure-agent.critique-rubric.v1.3`.
- [x] v1.3 critiques must include all ten `top_tier_audit` keys.
- [x] Missing, empty, or invalid top-tier audit fields fail with controlled
  `CritiqueAdjudicationError`.
- [x] `fail`, `needs_human`, and high-impact-blocking `weak` top-tier slots
  must link to `top_tier_audit.<slot_key>` in a panel/top-level finding,
  `quality_axes.blocking_items`, or explicit `accept_simplification`.
- [x] Unrelated findings must not satisfy the top-tier link rule.
- [x] v1.2 critiques remain loadable/scaffoldable for compatibility.
- [x] `/fig_loop`, `/fig_drive`, `/fig_export`, accepted, golden, and final
  artifact behavior do not change in this slice.
- [x] Focused tests pass and full plugin validation passes.

## Out of Scope

- SVG polish automation.
- Score-driven release gates.
- Learned visual quality model.
- External API or web-search based journal policy validation.
- Automatic accepted/golden/export mutation.
