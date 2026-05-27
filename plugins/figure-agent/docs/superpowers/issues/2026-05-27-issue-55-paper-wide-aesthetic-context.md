# Issue 55 - Paper-Wide Aesthetic Context

Status: design drafted

Design spec:
`../specs/2026-05-27-paper-wide-aesthetic-context-design.md`

## Problem

The plugin can now audit and route a single figure through fixture-local
aesthetic intent, high-zoom evidence, reference-calibrated critique, SVG polish
readiness, and deterministic geometry checks. It still lacks a paper-wide
aesthetic context: the shared visual language that keeps multiple figures in
one manuscript coherent.

Without that layer, each figure can become locally polished but drift from the
series in palette restraint, typography, line-weight rhythm, density, panel
grammar, iconography, or visual maturity.

## Goal

Add an optional, explicit, paper-wide aesthetic context that `/fig_critique`
can use as evidence when judging whether an opted-in fixture still belongs to
the same manuscript visual system.

The feature must remain a critique-grounding contract. It must not draw
figures, auto-polish SVGs, mutate exports, or claim journal readiness.

## Proposed Scope

Implement in narrow slices:

1. **Issue 55A - Parser and Freshness**
   - `scripts/paper_aesthetic_context.py`
   - explicit `spec.yaml.paper_aesthetic_context` opt-in
   - pack resolution from `examples/_paper_aesthetic_contexts/<paper_id>.yaml`
   - critique input hash participation

2. **Issue 55B - Critique Brief Section**
   - `## Paper-Wide Aesthetic Context`
   - matching fixture role only
   - exact paper-wide anchor list
   - command/skill docs

3. **Issue 55C - Lint Accountability**
   - reject generic critiques that ignore paper-wide anchors
   - preserve fixtures without paper context
   - controlled blockers for malformed opted-in packs

4. **Issue 55D - Dogfood and Closeout**
   - one real fixture opt-in
   - no figure source edit
   - freshness and lint-accounting evidence

## Key Design Constraints

- No ambient global `examples/paper_aesthetic_context.yaml`.
- A fixture must opt in through `spec.yaml.paper_aesthetic_context`.
- The pack must explicitly list the fixture in `figure_roles[]`.
- `paper_aesthetic_context` ids must be safe ids, not arbitrary paths.
- Paper-wide context complements, not replaces, fixture-local
  `aesthetic_intent.yaml`.
- Do not extend existing `aesthetic_lever_audit.dimension` enums in v1.
- Anchor-accountability follows the same pattern as existing aesthetic intent,
  visual-clash, text-boundary, label-path, and crop-read contracts.

## Acceptance

- Design spec is reviewed and approved before implementation.
- Each implementation slice uses TDD.
- Existing fixtures without `spec.yaml.paper_aesthetic_context` keep current
  behavior.
- Paper context changes make existing critiques stale for opted-in fixtures.
- Host critiques cannot silently ignore paper-wide context once opted in.
