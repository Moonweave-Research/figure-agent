# Issue 43 — Aesthetic Lever Grammar

**Status:** implemented through Issue 43F; final dogfood evidence captured

Design spec:
`../specs/2026-05-24-issue43-aesthetic-lever-grammar-design.md`

Implementation commits:

- `b3868db` — design aesthetic lever grammar.
- `a49bda8` — Issue 43A, `aesthetic_intent.yaml` v2 parser/validator.
- `4604dfa` — Issue 43B, `/fig_critique` v1.11 brief/rubric integration.
- `aa1d6fd` — Issue 43C, critique schema v1.11 validation.
- `c65a4bd` — Issue 43D, fixture-aware `critique_lint.py` lever accountability.
- `a1a19ae` — Issue 43E, `/fig_loop` aesthetic lever summary surfacing.
- `2107e39` — Issue 43E follow-up, JSON summary contract test alignment.
- `1a02791` — Issue 43B/43E follow-up, v2 aesthetic-intent freshness expects rubric v1.11.
- `5511fba` — Review fixup, schema-aware freshness and strict aesthetic route gates.
- `d817022` — Review fixup, polish driver honors loop-level aesthetic/top-tier blockers.
- `91de4e9` — Review coverage, release driver preserves aesthetic lever checkpoint summary.
- `8a865a6` — Issue 43F, fixture-level aesthetic lever grammar dogfood.

Issue 43F dogfood evidence:
`../../milestones-archive/2026-05-24-aesthetic-lever-grammar-dogfood.md`.

The dogfood upgraded one intentionally selected real fixture to
`aesthetic_intent.yaml` v2, refreshed its critique to schema v1.11, and verified
lint/status/loop/driver consumption. No TikZ source, accepted/golden state,
export artifact, or publication provenance file was edited.

## Problem

Issue 35 added optional `examples/<name>/aesthetic_intent.yaml`, and Issue 36
made `critique_lint.py` require exact aesthetic-intent anchor citations in key
top-tier and editorial critique slots. That closes the "present but unused"
failure mode, but the contract is still too coarse for repeated visual polish.

The current intent file can say a figure targets `editorial`, `balanced`, or
`multipanel_story`, and it can list broad design principles and anti-patterns.
It does not force the host LLM to enumerate the concrete aesthetic levers that
make those abstractions actionable: maturity, hero hierarchy, whitespace,
typography, color economy, line-weight rhythm, component fidelity, hand-crafted
detail, cross-panel grammar, and TikZ-vs-SVG routing.

Without that lever grammar, a critique can technically cite the aesthetic intent
while still producing generic prose such as "improve polish" or "more
Nature-like" without a bounded next action.

## Goal

Define an `aesthetic_intent.yaml` v2 contract and matching critique-output
contract that turns subjective aesthetic targets into explicitly auditable
lever-by-lever decisions.

The design must keep `figure-agent` as a verification and handoff kernel. It
must not make the plugin an autonomous illustrator or allow aesthetic preference
to override science, critique, freshness, export, accepted, golden, or
publication gates.

## Scope

In scope for implementation:

- Add `figure-agent.aesthetic-intent.v2` as a backward-compatible extension of
  the current v1 intent file.
- Add a controlled `aesthetic_levers[]` list with stable ids, dimensions,
  positive signals, anti-patterns, allowed adjustments, forbidden adjustments,
  and routing.
- Add a schema/rubric bump for critique output that includes
  `aesthetic_lever_audit`.
- Make `/fig_critique` force the host LLM to evaluate every declared lever.
- Make `critique_lint.py` reject missing lever accounting, unknown lever ids,
  duplicated lever ids, and blocking lever verdicts that are not linked to a
  finding, quality-axis blocker, SVG-polish route, semantic backport route, or
  human art-direction route.
- Surface the worst aesthetic bottleneck in `/fig_loop` without changing
  release behavior.

Out of scope:

- Automatic SVG geometry edits.
- Automatic TikZ patching.
- New scoring gates.
- Journal acceptance probability estimates.
- Web/reference scraping.
- Editing existing figure sources or generated artifacts.
- Promoting any aesthetic score above science, freshness, export, accepted,
  golden, or publication gates.

## Acceptance Criteria

- The design clearly defines the v2 intent schema and its compatibility with
  v1.
- The design clearly defines the critique output field and how it links to
  existing `top_tier_audit`, `editorial_art_direction`,
  `journal_grade_assessment`, `micro_defects`, and SVG polish routing.
- The design names the default recommended lever dimensions and explains which
  failures must route to TikZ patching, SVG polish, semantic backport, or
  human art direction.
- The design includes controlled failure modes for malformed intent files,
  stale critiques, missing lever accounting, and generic unsupported aesthetic
  prose.
- The design includes a TDD implementation plan outline with target files and
  test coverage, but does not implement code in this issue.
- Three critical review passes find no in-scope design blocker.

## Initial Priority

This issue is the highest-value next design slice after Issue 42 because the
deterministic audit kernel is now strong enough that the remaining quality gap
is mostly "how to translate abstract visual taste into repeatable critique and
handoff language."
