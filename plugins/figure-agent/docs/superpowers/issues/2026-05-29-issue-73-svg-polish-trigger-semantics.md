# Issue 73 - SVG Polish Trigger Semantics

Status: completed

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

## Implementation Notes

- Added schema/rubric `figure-agent.critique.v1.14` /
  `figure-agent.critique-rubric.v1.14` for advanced aesthetic/reference
  contracts only:
  - `figure-agent.aesthetic-intent.v2`
  - `spec.yaml.journal_art_direction_playbook`
  - `critique_reference_pack.yaml.reference_learning`
- Default and legacy fixtures remain on v1.10 unless one of those advanced
  opt-ins is present. Legacy v1.13 critiques remain parseable without route
  detail.
- v1.14 requires exactly one route-specific rationale field on
  `editorial_art_direction.tikz_vs_svg_polish_trigger`:
  - `remaining_tikz_lever` for `continue_tikz`
  - `svg_polish_candidate_reason` for `ready_for_svg_polish`
  - `semantic_backport_reason` for `semantic_backport_required`
  - `human_art_direction_reason` for `needs_human_art_direction`
- `/fig_loop` surfaces the selected rationale as `polish_route_detail`.
- `/fig_driver --mode polish` preserves the hard gate and includes route detail
  in `svg_polish_readiness` without authorizing mutation.

## Verification

- Targeted pytest:
  `uv run pytest -q tests/test_critique_brief.py tests/test_quality_manifest.py tests/test_critique_schema_validator.py tests/test_critique_lint.py tests/test_fig_driver_editorial.py tests/test_fig_loop.py tests/test_status.py tests/test_sync_critique_adjudication.py`
  -> 496 passed.
- Targeted ruff + `git diff --check` passed before final full-suite
  verification.
