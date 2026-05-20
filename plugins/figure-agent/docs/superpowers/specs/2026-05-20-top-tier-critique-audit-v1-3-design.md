# Top-Tier Critique Audit v1.3 Design

**Date:** 2026-05-20 KST
**Status:** design ready for implementation
**Parent:** Issue 10

## Problem

The current v1.2 `/fig_critique` brief already forces structural completeness,
label-target matching, physical plausibility, conceptual completeness,
journal-grade quality axes, and advisory scoring. Dogfood shows that this is
useful, but the critique can still behave like a defect-finder rather than a
top-tier figure reviewer.

The missing layer is not SVG polish. It is the audit prompt that tells the host
LLM what a high-impact journal figure must prove before any polish is worth
doing.

## Goal

Add a v1.3 critique contract that forces a top-tier journal audit before the
host writes findings, quality axes, or scores.

The new audit must make the host enumerate:

1. first-glance message quality;
2. target-journal fit;
3. novelty and claim support;
4. figure-caption coupling;
5. visual economy;
6. cross-panel semantic grammar;
7. reader misinterpretation risk;
8. reduction/print/readability;
9. accessibility and color robustness;
10. aesthetic coherence.

## Non-Goals

- Do not add SVG polish automation.
- Do not change `/fig_loop`, `/fig_drive`, `/fig_export`, accepted, or golden
  behavior in this slice.
- Do not claim objective Nature, Science, Nature Materials, or Nature
  Communications acceptance.
- Do not require external API calls, web search, or learned visual models.
- Do not make numeric scores gate release.

## Contract

`critique.md` schema advances from:

```yaml
schema: figure-agent.critique.v1.2
rubric_version: figure-agent.critique-rubric.v1.2
```

to:

```yaml
schema: figure-agent.critique.v1.3
rubric_version: figure-agent.critique-rubric.v1.3
```

The v1.3 frontmatter adds:

```yaml
top_tier_audit:
  first_glance_message:
    verdict: pass | weak | fail | needs_human
    finding: "<what a reader understands in 3/10/30 seconds>"
    concrete_fix: "<specific figure edit or accept_simplification>"
    blocks_high_impact: true | false
  target_journal_fit:
    verdict: pass | weak | fail | needs_human
    finding: "<fit to target journal or generic high-impact schematic standard>"
    concrete_fix: "<specific edit or human art-direction question>"
    blocks_high_impact: true | false
  novelty_claim_support:
    verdict: pass | weak | fail | needs_human
    finding: "<whether the visual supports the manuscript's central claim>"
    concrete_fix: "<specific edit or claim-figure alignment question>"
    blocks_high_impact: true | false
  figure_caption_coupling:
    verdict: pass | weak | fail | needs_human
    finding: "<whether caption and figure share the right explanatory burden>"
    concrete_fix: "<specific figure or caption-side recommendation>"
    blocks_high_impact: true | false
  visual_economy:
    verdict: pass | weak | fail | needs_human
    finding: "<unnecessary ink, redundant marks, or missing explanatory marks>"
    concrete_fix: "<delete, simplify, or emphasize one concrete element>"
    blocks_high_impact: true | false
  cross_panel_semantic_grammar:
    verdict: pass | weak | fail | needs_human
    finding: "<color, arrow, shape, texture, and label grammar across panels>"
    concrete_fix: "<one grammar normalization edit>"
    blocks_high_impact: true | false
  reader_misinterpretation_risk:
    verdict: pass | weak | fail | needs_human
    finding: "<most likely wrong interpretation by a qualified reader>"
    concrete_fix: "<specific guardrail label, spacing, or visual cue>"
    blocks_high_impact: true | false
  reduction_print_readability:
    verdict: pass | weak | fail | needs_human
    finding: "<1-column, 2-column, thumbnail, grayscale, or print weakness>"
    concrete_fix: "<specific scale/contrast/typography edit>"
    blocks_high_impact: true | false
  accessibility_color_robustness:
    verdict: pass | weak | fail | needs_human
    finding: "<colorblind/grayscale/contrast/texture redundancy assessment>"
    concrete_fix: "<specific redundant encoding or contrast edit>"
    blocks_high_impact: true | false
  aesthetic_coherence:
    verdict: pass | weak | fail | needs_human
    finding: "<style authority across line weights, detail level, depth cues>"
    concrete_fix: "<specific style-normalization edit>"
    blocks_high_impact: true | false
```

Every v1.3 critique must include all ten keys. Empty strings are invalid.

## Finding Link Rule

Any `fail` item, any `weak` item with `blocks_high_impact: true`, or any
`needs_human` item must either:

- appear as a normal panel/top-level finding, or
- be explicitly represented in `quality_axes` as `needs_human`,
  `revise_briefing`, or `block_release`, or
- be justified in `concrete_fix` as `accept_simplification`.

This keeps the new audit from becoming prose-only decoration.

## Integration

- `scripts/critique_brief.py` emits the new section between
  `Journal-Grade Quality Axes` and `Journal-Grade Fresh Re-Audit Assessment`.
- `scripts/critique_adjudication.py` validates v1.3 critiques while preserving
  v1, v1.1, and v1.2 compatibility.
- `scripts/quality_manifest.py` bumps `CRITIQUE_RUBRIC_VERSION` to
  `figure-agent.critique-rubric.v1.3`.
- `scripts/status.py` critique freshness naturally marks older v1.2 critiques
  stale by rubric mismatch when hash metadata is present.
- `/fig_loop`, `/fig_drive`, `/fig_export`, accepted, golden, and final artifact
  behavior remain unchanged.

## Tests

Add focused tests for:

- brief contains `## Top-Tier Journal Figure Audit`;
- brief output format uses schema v1.3 and rubric v1.3;
- valid v1.3 critique with complete `top_tier_audit` scaffolds adjudication;
- missing top-tier audit block fails controlled validation;
- empty top-tier audit item fails controlled validation;
- invalid top-tier verdict fails controlled validation;
- v1.2 critique remains accepted as legacy/current-compatible input.

## Review Risks

- If the block is too large, host critiques may become verbose. This is
  acceptable for v1.3 because the purpose is audit quality, not brevity.
- If target journal is unknown, the host must use a generic high-impact
  schematic standard and mark target-specific decisions as `needs_human`.
- If no caption exists, `figure_caption_coupling` should evaluate whether the
  figure is over- or under-dependent on a future caption, not fail by default.

