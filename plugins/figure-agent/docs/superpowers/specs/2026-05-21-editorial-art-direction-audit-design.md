# Editorial Art-Direction Audit Design

**Date:** 2026-05-21 KST
**Status:** implemented through Issue 16C
**Related issues:** Issue 16A, Issue 16B, Issue 16C
**Follows:** critique schema v1.4, top-tier audit v1.3, micro-defect audit v1.4, final-artifact SVG polish contract

## Purpose

`figure-agent` now catches many technical figure defects: stale artifacts,
missing references, label-target mismatch, structural gaps, physical
plausibility issues, high-zoom micro-defects, print-scale readability, and
top-tier audit blockers. That is enough to move many figures from draft toward
solid manuscript quality.

The remaining gap is editorial art direction. A figure can pass technical
checks and still fail to feel like a Nature, Science, Nature Materials, or
Nature Communications level illustration. The missing contract is a forced
audit surface that asks whether the current artifact has a clear hero focus,
visual narrative, illustration register, coherent abstraction level, and a
credible path to SVG polish when TikZ has reached its practical ceiling.

Issue 16A adds that audit surface to the critique contract. Issue 16B surfaces
the resulting polish trigger through `/fig_loop` and `/fig_drive --mode polish`.
Issue 16C keeps that routing policy in a focused helper module. None of these
issues add auto-editing, SVG editing, release approval, accepted/golden
mutation, or hidden polish automation.

## Current Repo Truth

The current critique contract already includes:

- `audit_enumeration` for structural, label-target, physical, and conceptual
  completeness.
- `quality_axes` for journal-grade technical assessment.
- `top_tier_audit` for high-impact figure risks.
- `journal_grade_assessment` for fresh re-audit benchmark level and optional
  advisory scores.
- `micro_defects` for high-zoom and print-scale observations.

The current final-artifact contract already supports polished SVG as an
opt-in release-relevant artifact through `spec.yaml.final_artifact` and
`polish/svg_polish_manifest.yaml`.

The current gap is not "no top-tier audit exists." The gap is that the existing
`top_tier_audit` mixes scientific claim, print readability, visual economy, and
art-direction taste in one broad block. Host LLMs can still answer it with
generic prose instead of making a concrete editorial decision about whether
the figure has the visual authority of a target-journal illustration.

## Design Decision

Add a new top-level critique block:

```yaml
editorial_art_direction:
  hero_focus:
  narrative_choreography:
  illustration_readiness:
  abstraction_consistency:
  reference_class_fit:
  visual_identity:
  claim_payload_fit:
  aesthetic_risk:
  tikz_vs_svg_polish_trigger:
  human_art_direction_gate:
```

This block is separate from `top_tier_audit` for three reasons:

1. `top_tier_audit` remains the broad high-impact journal check.
2. `editorial_art_direction` is specifically about illustration register,
   art direction, and the decision boundary between TikZ repair and SVG polish.
3. Later `/fig_loop` or `/fig_drive` routing can consume the polish trigger
   without overloading every top-tier slot.

## Schema Version

Issue 16A bumps the critique schema to:

```yaml
schema: figure-agent.critique.v1.5
rubric_version: figure-agent.critique-rubric.v1.5
```

v1.0-v1.4 critiques remain legacy-parseable under existing rules. Existing
tracked examples must not be force-migrated by this slice; they may become
freshness-stale after the v1.5 rubric/generator bump and should be refreshed
only through normal `/fig_critique` runs.

## Editorial Slot Shape

Each slot must use the same shape:

```yaml
<slot_key>:
  verdict: pass | weak | fail | needs_human
  evidence: "<specific current-artifact evidence>"
  rationale: "<why this matters for target-journal illustration quality>"
  concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
  blocks_high_impact: true | false
```

`tikz_vs_svg_polish_trigger` has one additional machine-readable field:

```yaml
tikz_vs_svg_polish_trigger:
  verdict: pass | weak | fail | needs_human
  evidence: "<specific current-artifact evidence>"
  rationale: "<why this matters for target-journal illustration quality>"
  concrete_fix: "<specific edit, polish handoff, or accept_simplification>"
  blocks_high_impact: true | false
  recommended_path: continue_tikz | ready_for_svg_polish | needs_human_art_direction | semantic_backport_required
```

Required semantics:

- `pass`: current artifact satisfies the slot for the stated target or generic
  high-impact schematic standard.
- `weak`: artifact is usable but holds the figure below high-impact visual
  register.
- `fail`: artifact has a concrete art-direction defect that should block
  high-impact promotion.
- `needs_human`: the decision depends on target journal, author preference,
  scientific emphasis, publication policy, or taste that automation should not
  decide.

Every slot must have non-empty `evidence`, `rationale`, and `concrete_fix`.
`blocks_high_impact` must be boolean.

## Slot Definitions

### hero_focus

Checks whether the figure has a clear visual anchor. The critique must name
the hero object, hero panel, or central visual claim. If every panel has equal
weight and the reader has no obvious first fixation, this slot is weak or fail.

### narrative_choreography

Checks the emotional and explanatory sequence of the figure, not only the
reading path. The critique must state whether the visual story flows through
problem, mechanism, evidence, and implication, or whether panels feel like
assembled fragments.

### illustration_readiness

Checks whether the current artifact reads as editorial illustration rather
than a plain schematic. It considers depth cues, soft shading, material
rendering, dimensionality, highlight/shadow discipline, and whether the visual
register matches the target journal.

### abstraction_consistency

Checks whether panels share a consistent abstraction level. Mixed icon,
cartoon, pseudo-3D, data-plot, and diagram registers are allowed only when the
role difference is intentional and visually controlled.

### reference_class_fit

Classifies the artifact against a reference class, such as:

- `nature_communications_mechanism_schematic`
- `nature_materials_main_schematic`
- `science_conceptual_mechanism`
- `graphical_abstract`
- `cover_candidate`
- `ordinary_manuscript_schematic`

The critique must say which class the current artifact most resembles and
which class it is trying to reach.

### visual_identity

Checks whether the figure has a coherent motif: repeated color grammar,
material texture, charge glyph, energy landscape, trap motif, arrow grammar,
or other visual language that makes the figure memorable.

### claim_payload_fit

Checks whether the central manuscript claim receives the most visual weight.
If the figure draws correct components but the novelty claim is visually
secondary, this slot is weak or fail.

### aesthetic_risk

Names concrete signs of amateurism or non-editorial rendering: clip-art
feeling, inconsistent stroke weights, awkward gradients, overdecorated
backgrounds, mismatched icons, crowded text, weak whitespace, or color choices
that feel accidental rather than designed.

### tikz_vs_svg_polish_trigger

Decides whether the remaining gap should stay in TikZ or move to controlled
SVG polish. This slot must include `recommended_path` so Issue 16B can consume
the result without prose parsing. Allowed values:

- `continue_tikz`: source-level semantic repair is still needed.
- `ready_for_svg_polish`: source/export are semantically adequate and the
  remaining gap is visual-only.
- `needs_human_art_direction`: target-journal taste must be decided before
  further polish.
- `semantic_backport_required`: SVG polish would change scientific meaning
  unless TikZ/briefing/critique are updated first.

Issue 16A records this judgment. Issue 16B routes it through `/fig_loop` and
`/fig_drive --mode polish` without adding mutation.

### human_art_direction_gate

States whether a human should make an art-direction decision before the next
loop. This is distinct from scientific correctness. It covers target-journal
choice, hero-panel priority, cover-style ambition, SVG polish scope, and
whether an illustration should remain schematic or become more dimensional.

## Link Rule

Any `fail`, any `needs_human`, or any `weak` slot with
`blocks_high_impact: true` must be represented downstream.

For `needs_human`, at least one of the following must be true:

1. a normal panel/top-level finding explicitly mentions
   `editorial_art_direction.<slot_key>`;
2. a `quality_axes.*.blocking_items` entry explicitly mentions
   `editorial_art_direction.<slot_key>` with a human/revise/block action;

For `fail` or `weak` plus `blocks_high_impact: true`, the two downstream-link
paths above are valid, or the slot's `concrete_fix` may contain
`accept_simplification` only when it explains why the weakness is intentional.

This mirrors the existing `top_tier_audit` link rule and prevents decorative
audit prose from bypassing adjudication and loop state.

## Brief Placement

`/fig_critique` brief should place the new section after
`Top-Tier Journal Figure Audit` and before `Journal-Grade Fresh Re-Audit
Assessment`.

Rationale: the editorial decision depends on top-tier slots, and the final
`journal_grade_assessment.benchmark_level` should know whether art direction
blocks high-impact promotion.

## Validator Behavior

`critique_adjudication.py scaffold` and `critique_lint.py` should reject v1.5
critiques when:

- `editorial_art_direction` is missing or not a mapping;
- any required slot is missing;
- any slot is not a mapping;
- `verdict` is outside `pass | weak | fail | needs_human`;
- `evidence`, `rationale`, or `concrete_fix` is missing or empty;
- `blocks_high_impact` is not boolean;
- `tikz_vs_svg_polish_trigger.recommended_path` is missing or outside the
  allowed enum;
- any blocking slot violates the link rule.

Legacy v1.0-v1.4 critiques should remain parseable under current compatibility
rules. This does not mean existing v1.4 critique files stay fresh after the
rubric/generator version changes. Freshness remains metadata-based: after
Issue 16A lands, existing tracked critiques may become `STALE` and should be
refreshed by the next `/fig_critique` run, not force-migrated in bulk by this
slice.

## Journal Assessment Interaction

`journal_grade_assessment.benchmark_level: high_impact_candidate` must require
all editorial art-direction slots to be `pass`. A `weak`, `fail`, or
`needs_human` editorial slot should prevent high-impact promotion even if
technical quality axes pass.

`benchmark_level: needs_human_art_direction` is the right outcome when the
technical artifact is credible but editorial ambition, target journal fit, or
SVG polish scope requires human judgment.

Numeric scores remain advisory and must not override editorial blockers.

## Non-Goals

- No SVG editing.
- No hidden `/fig_loop` or `/fig_drive` mutation.
- No auto-patch behavior.
- No accepted/golden/final-artifact mutation.
- No migration of existing example critiques.
- No claim that the plugin can guarantee Nature or Science acceptance.

## Success Criteria

Issue 16A is complete when:

1. `/fig_critique` brief forces the `editorial_art_direction` audit.
2. The output schema documents `figure-agent.critique.v1.5`.
3. The validator rejects missing, malformed, or unlinked editorial audit slots.
4. `high_impact_candidate` cannot pass with non-passing editorial slots.
5. Legacy critiques remain parseable without bulk migration.
6. `tikz_vs_svg_polish_trigger` has a validated `recommended_path`.
7. `needs_human` editorial slots cannot be hidden behind
   `accept_simplification`.
8. Tests cover valid v1.5, missing block, invalid verdict, missing evidence,
   invalid `recommended_path`, link-rule failure, high-impact promotion
   blocking, and legacy v1.4 parsing.

## Follow-Up: Issue 16B

Issue 16B consumes `editorial_art_direction.tikz_vs_svg_polish_trigger` inside
`/fig_loop` and `/fig_drive --mode polish`. Issue 16C extracts the driver-side
policy into `scripts/fig_driver_editorial.py` so future editorial routing
changes have a focused module and tests.
