# Issue 35 — Aesthetic Intent Contract

Status: completed in commit `2cc0c03`

Design spec:
`../specs/2026-05-23-issue35-aesthetic-intent-contract-design.md`

Implementation plan:
`../plans/2026-05-23-issue35-aesthetic-intent-contract-implementation.md`

## Problem

The plugin now audits top-tier, editorial, zoom, print-scale, reference, visual
clash, and text-boundary defects. That makes the verification kernel strong,
but it still leaves a design-coaching gap: the host critique can evaluate
`aesthetic_coherence`, `visual_identity`, and `aesthetic_risk` without a stable
fixture-specific aesthetic target.

When the target aesthetic is not explicit, critique may drift toward generic
best-practice prose or overfit the current artifact. The result can pass
technical gates while still feeling visually immature, generic, too dense, too
cartoonish, or insufficiently hand-crafted for the intended journal context.

## Goal

Add an optional, validated `examples/<name>/aesthetic_intent.yaml` contract that
grounds `/fig_critique` in fixture-specific design intent without turning
`figure-agent` into an autonomous illustrator.

## Scope

In scope:

- Parse and validate optional `aesthetic_intent.yaml`.
- Include its content in the critique brief as a mandatory calibration input
  when present.
- Include it in `critique_input_hash` freshness.
- Keep existing behavior unchanged when the file is absent.
- Add focused tests for valid, missing, malformed, and freshness behavior.

Out of scope:

- New generated drawing behavior.
- Automatic SVG editing or polish generation.
- New score gates.
- Changes to `critique.md` schema v1.10.
- Changes to accepted/golden/export behavior.

## Candidate Contract

```yaml
schema: figure-agent.aesthetic-intent.v1
fixture: fig1_overview_v2_pair_001_vault
target_journal: Nature Materials
visual_maturity: restrained | polished | editorial | cover_like
density: sparse | balanced | dense
reference_style: mechanism_schematic | apparatus_schematic | multipanel_story | data_plus_schematic | graphical_abstract
design_principles:
  - id: mature_restraint
    instruction: avoid cartoon-like oversized labels and decorative gradients
  - id: hand_crafted_detail
    instruction: preserve subtle component-level texture where it clarifies physics
must_avoid:
  - id: toy_diagram
    pattern: rounded generic blocks, oversized arrows, and unmodulated flat color
    severity: MAJOR
polish_triggers:
  - id: svg_micro_polish
    condition: TikZ output is semantically correct but lacks print-scale optical refinement
    recommended_path: ready_for_svg_polish
```

## Acceptance Criteria

- A valid `aesthetic_intent.yaml` appears in `/fig_critique` output under
  `## Aesthetic Intent Calibration`.
- Missing `aesthetic_intent.yaml` preserves current brief behavior.
- Malformed YAML or invalid enum values fail with a controlled
  `CritiqueBriefError`.
- `aesthetic_intent.yaml` participates in `critique_input_hash` when present.
- The section instructs the host LLM to apply this intent to
  `top_tier_audit.aesthetic_coherence`, `editorial_art_direction.visual_identity`,
  `editorial_art_direction.aesthetic_risk`, and
  `editorial_art_direction.tikz_vs_svg_polish_trigger`.
- No source figure, export, accepted, or golden artifact is mutated.
