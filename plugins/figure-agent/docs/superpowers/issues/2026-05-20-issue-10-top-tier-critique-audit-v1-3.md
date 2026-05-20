# Issue 10: Top-Tier Critique Audit v1.3

**Date:** 2026-05-20 KST
**Status:** planned
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

## Acceptance Criteria

- [ ] `/fig_critique` brief includes a mandatory
  `## Top-Tier Journal Figure Audit` section.
- [ ] Output schema advances to `figure-agent.critique.v1.3`.
- [ ] Rubric version advances to `figure-agent.critique-rubric.v1.3`.
- [ ] v1.3 critiques must include all ten `top_tier_audit` keys.
- [ ] Missing, empty, or invalid top-tier audit fields fail with controlled
  `CritiqueAdjudicationError`.
- [ ] v1.2 critiques remain loadable/scaffoldable for compatibility.
- [ ] `/fig_loop`, `/fig_drive`, `/fig_export`, accepted, golden, and final
  artifact behavior do not change in this slice.
- [ ] Focused tests pass and full plugin validation passes.

## Out of Scope

- SVG polish automation.
- Score-driven release gates.
- Learned visual quality model.
- External API or web-search based journal policy validation.
- Automatic accepted/golden/export mutation.

