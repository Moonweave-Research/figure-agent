# Issue 73 - SVG Polish Trigger Semantics

Status: proposed

Depends on:

- Issue 71D positive SVG polish promotion evidence

Type: design + small contract hardening

## Problem

Issue 71D tried to find a real fixture that could enter SVG polish mode and
found none. The strongest candidate,
`fig1_overview_v2_pair_001_vault`, had strong evidence:

- `benchmark_level: high_impact_candidate`
- `overall_score: 88`
- audit evidence passed
- crop audit passed
- editorial art-direction slots all `pass`

But it still produced:

```yaml
editorial_art_direction_summary:
  polish_trigger_verdict: pass
  polish_recommended_path: continue_tikz

svg_polish_readiness:
  can_start_svg_polish: false
  blocking_items:
    - id: tikz_vs_svg_polish_trigger
```

That may be conservative and correct, but the contract is ambiguous: a `pass`
verdict can still mean "do not start SVG polish." The plugin therefore has no
clear positive real-fixture path for bounded SVG optical polish.

## Goal

Clarify and harden the semantics of
`editorial_art_direction.tikz_vs_svg_polish_trigger` so operators and drivers
can distinguish:

- keep iterating in TikZ/source,
- start bounded SVG optical polish,
- perform semantic backport first,
- stop for human art direction.

## Non-Goals

- Do not weaken human gates.
- Do not let SVG polish repair semantic, scientific, label-target, or
  publication blockers.
- Do not auto-edit SVG.
- Do not mutate accepted/golden/export state.
- Do not make high numeric score sufficient for SVG polish.

## Design Questions

1. Should `verdict: pass` mean "the routing decision itself is valid" while
   `recommended_path` carries the real route?
2. Should the brief require an explicit rationale when
   `verdict: pass` and `recommended_path: continue_tikz` coexist on a
   high-quality, audit-clean fixture?
3. Should `ready_for_svg_polish` require a specific positive statement that all
   semantic/source-level levers are exhausted?
4. Should `/fig_loop` surface a separate "near SVG polish but blocked by
   trigger semantics" summary so operators know what to do next?

## Proposed Direction

Keep the safe rule: only `recommended_path: ready_for_svg_polish` can start SVG
polish. Improve the contract around why the trigger chooses
`continue_tikz` instead:

- Add a required `remaining_tikz_lever` field when
  `recommended_path: continue_tikz`.
- Add a required `svg_polish_candidate_reason` field when
  `recommended_path: ready_for_svg_polish`.
- Lint v1.14+ critiques so the trigger cannot be a bare pass/fail without a
  route-specific rationale.
- Make `/fig_loop` summarize the blocker as "source-level polish still
  available" versus "trigger semantics ambiguous."

## Acceptance

- A real or synthetic fixture can demonstrate each route:
  `continue_tikz`, `ready_for_svg_polish`, `semantic_backport_required`,
  `needs_human_art_direction`.
- `fig_loop` and `fig_driver --mode polish` preserve the existing hard rule:
  SVG polish starts only on `ready_for_svg_polish`.
- Lint rejects missing route-specific rationale in the new schema/rubric
  version while preserving legacy compatibility.
- A follow-up 71D-style dogfood run can identify whether the strongest real
  fixture is truly source-polish-only or ready for bounded SVG optical polish.
