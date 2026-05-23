# Issue 36 — Aesthetic Intent Lint Accountability

**Status:** completed in commit `170265a`

## Problem

Issue 35 added optional `examples/<name>/aesthetic_intent.yaml` and made
`/fig_critique` include it in the brief and critique freshness hash. That is
necessary but not sufficient: a host critique can still write generic
`aesthetic_coherence`, `visual_identity`, `aesthetic_risk`, and
`tikz_vs_svg_polish_trigger` prose without proving it actually consumed the
fixture-specific aesthetic target.

This is the same class of failure the plugin already fixed for crop reads,
visual-clash candidates, and text-boundary candidates: evidence can be present
but silently unused unless lint requires explicit accounting.

## Goal

When `aesthetic_intent.yaml` exists, `critique_lint.py` must require the
current critique to cite at least one exact aesthetic-intent anchor in each of
the four slots named by the brief:

- `top_tier_audit.aesthetic_coherence`
- `editorial_art_direction.visual_identity`
- `editorial_art_direction.aesthetic_risk`
- `editorial_art_direction.tikz_vs_svg_polish_trigger`

Valid anchors are deterministic strings from the intent pack:

- `target_journal`
- `visual_maturity`
- `density`
- `reference_style`
- any `design_principles[].id`
- any `must_avoid[].id`
- any `polish_triggers[].id`

## Scope

In scope:

- Add lint-only accountability for current critiques when an aesthetic intent
  pack exists.
- Update the brief to tell host LLMs that these four slots must cite exact
  aesthetic intent anchors.
- Keep legacy critiques and fixtures without `aesthetic_intent.yaml` unchanged.
- Treat malformed `aesthetic_intent.yaml` as a controlled lint blocker.

Out of scope:

- New critique schema version.
- New score gates.
- Automatic art-direction edits.
- SVG polish generation.
- Export, accepted, golden, or release behavior changes.

## Acceptance Criteria

- `critique_lint.py` rejects a critique for a fixture with
  `aesthetic_intent.yaml` when any required slot is generic and cites no
  aesthetic-intent anchor.
- `critique_lint.py` accepts the same critique when all four required slots cite
  exact anchors from the pack.
- Missing `aesthetic_intent.yaml` preserves existing lint behavior.
- Malformed `aesthetic_intent.yaml` produces a controlled
  `aesthetic_intent_accounting` blocker.
- `critique_brief.py` explicitly states the required anchor-citation rule.
- Tests cover reject, accept, missing-pack legacy behavior, malformed-pack
  behavior, and brief text.

## Implementation Notes

- `critique_lint.py` now loads optional `aesthetic_intent.yaml` and checks the
  four required critique slots for exact anchors from the intent pack.
- Malformed aesthetic-intent packs are reported as controlled
  `aesthetic_intent_accounting` blockers.
- Fixtures without `aesthetic_intent.yaml` keep their previous lint behavior.
- `critique_brief.py` now tells the host LLM that the four slots must cite exact
  aesthetic intent anchors; generic style prose is invalid.
