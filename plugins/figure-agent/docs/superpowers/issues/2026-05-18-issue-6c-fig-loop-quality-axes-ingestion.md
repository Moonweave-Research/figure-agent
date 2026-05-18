# Issue 6C: Fig Loop Quality Axes Ingestion

**Status:** Completed in commits `35819ce` and `d0aa750`.

## Problem

Issue 6B makes `/fig_critique` emit schema v1.2 with required
`quality_axes`, and `/fig_adjudicate` validates those axes before scaffolding
decisions. `/fig_loop` still treats several higher-level audit slots as
placeholders even when a fresh v1.2 critique already contains usable quality
axis verdicts.

This leaves a contract gap: the host LLM may have judged storyline,
reference fidelity, and publication readiness, but the loop checkpoint does
not surface that judgment in `axis_verdicts`.

## Scope

Implement read-only ingestion of v1.2 `critique.md` quality axes into existing
`/fig_loop.axis_verdicts` slots.

## In Scope

- Parse `critique.md` YAML frontmatter safely.
- Use `quality_axes` only when `schema` is `figure-agent.critique.v1.2`.
- Map selected quality axes into existing axis keys:
  - `story_hierarchy`
  - `reference_fidelity`
  - `publication_safety`
- Preserve existing `axis_verdicts` keys, stop reasons, patch handoff,
  escalation fields, and verify-only behavior.
- Fall back to the previous placeholder behavior when critique metadata is
  missing, legacy, malformed, or not v1.2.

## Out of Scope

- Adding ten new top-level loop axis keys.
- Revalidating the full v1.2 critique schema inside `/fig_loop`.
- Changing `/fig_compile`, `/fig_status`, `/fig_export`, acceptance, or golden
  behavior.
- Hidden auto-patching or critique mutation.

## Acceptance Criteria

- [x] A v1.2 critique with `quality_axes.message_storyline`,
  `panel_role_coherence`, and `composition_layout` updates
  `axis_verdicts.story_hierarchy`.
- [x] A v1.2 critique with `quality_axes.reference_fidelity` updates
  `axis_verdicts.reference_fidelity`, unless reference input is missing.
- [x] A v1.2 critique with `quality_axes.publication_readiness` updates
  `axis_verdicts.publication_safety`, while existing human-gate and accepted
  state behavior remains intact.
- [x] Malformed or legacy critique frontmatter does not crash `/fig_loop`.
- [x] `/fig_loop` remains verify-only and does not edit source, critique, export,
  accepted, or golden files.
- [x] Stale or missing critique evidence takes precedence over adjudicated human
  gates and manual golden roll-forward recommendations.
