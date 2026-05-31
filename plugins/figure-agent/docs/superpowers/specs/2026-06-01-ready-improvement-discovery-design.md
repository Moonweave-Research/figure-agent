# Ready Improvement Discovery Design

Date: 2026-06-01

Parent issue:
`docs/superpowers/issues/2026-06-01-issue-94-ready-improvement-discovery-mode.md`

## Current State

`figure-agent` has become strong at blocking unsafe states:

- stale or missing render, critique, adjudication, export, accepted, golden,
  publication, crop-accounting, visual-clash, and SVG-polish evidence;
- human boundaries such as host-vision critique, force-golden, human
  art-direction, and accepted/final-ready decisions;
- semantic backport before SVG polish when the figure still needs TikZ/source
  repair.

The remaining operator gap is different. Once a fixture is safe enough to ship,
the driver can legitimately say `complete` even when the fresh critique contains
optional improvement evidence:

- open NIT or MINOR findings that were adjudicated as acceptable but still
  visible;
- `editorial_art_direction.tikz_vs_svg_polish_trigger.remaining_tikz_lever`;
- weak/non-blocking `top_tier_audit` slots;
- weak aesthetic lever audit entries that do not require human review;
- journal playbook weak items whose route is a bounded TikZ/SVG refinement.

This makes the plugin feel passive: it proves "no blocker remains" but does not
answer "what can still improve this figure without weakening release safety?"

## Design Goal

Add a read-only **ready improvement discovery** layer that surfaces optional,
bounded improvement candidates for already-safe fixtures.

The layer must preserve the meaning of existing gates:

- `complete` and `release_ready` still mean no blocking plugin action remains.
- Optional candidates never block export, release, accepted, golden, or
  publication gates.
- The driver must not auto-edit source, SVG, export, accepted, or golden state.
- The layer derives only from structured critique/loop evidence, not host prose.

The practical user-facing answer should become:

> This figure is safe to ship, and here are the non-blocking improvement levers
> still visible. They are optional; choose one only if you want more polish.

## Contract

The summary is additive and may appear in `/fig_driver` JSON:

```yaml
ready_improvement_summary:
  schema: figure-agent.ready-improvement-summary.v1
  source: critique.md | latest_loop_checkpoint | status
  state: not_ready | ready_no_actionable_improvement | ready_but_improvable
  safe_to_ship: true | false
  blocks_release: false
  auto_patch_allowed: false
  candidate_count: 0
  candidates:
    - id: I001
      source: editorial_art_direction_summary | top_tier_audit_summary | aesthetic_lever_summary | journal_art_direction_playbook_summary
      source_id: "<slot/finding/lever id>"
      type: tikz_micro_polish | svg_polish | human_art_direction | accept_simplification_review
      target: "<short visible target>"
      suggested_action: "<one bounded action>"
      expected_gain: low | medium
      risk: low | medium | needs_human
      required_actor: workflow_agent | svg_editor | human_art_direction
      allowed_scope:
        - examples/<name>/<name>.tex
        - examples/<name>/polish/
      reason: "<one-line evidence>"
```

### State Meaning

- `not_ready`: existing workflow blockers are present. Operators should follow
  existing status/driver/loop actions instead of optional improvement discovery.
- `ready_no_actionable_improvement`: the figure is safe and no structured
  optional improvement evidence was found.
- `ready_but_improvable`: the figure is safe and at least one optional,
  non-blocking candidate was found.

`safe_to_ship` is true only when the current driver outcome is a non-blocking
ready/complete shape or the status says release-ready/final-ready. It must not
be inferred from high scores alone.

## Candidate Sources

Candidate extraction is intentionally conservative:

1. `editorial_art_direction_summary`
   - `polish_recommended_path: continue_tikz` plus non-empty
     `polish_route_detail` becomes a `tikz_micro_polish` candidate.
   - `polish_recommended_path: ready_for_svg_polish` becomes an `svg_polish`
     candidate only when existing SVG-polish readiness is not blocked.
   - `needs_human_art_direction` remains a human gate through existing routing,
     not an optional candidate.

2. `top_tier_audit_summary`
   - weak slots without high-impact blockers become optional
     `human_art_direction` or `tikz_micro_polish` candidates depending on the
     available slot name.
   - fail/needs_human/high-impact blockers keep using the existing human gate.

3. `aesthetic_lever_summary`
   - `evaluation_state: needs_patch` or weak non-human levers become optional
     candidates.
   - `needs_human` and `blocked` remain existing blockers.

4. `journal_art_direction_playbook_summary`
   - weak routes that are non-human and non-blocking become optional
     candidates.
   - fail/needs_human routes stay blocking through existing loop checks.

Findings/adjudication-based optional resurfacing is explicitly deferred from
the first slice. It needs a separate decision-state extractor so stale
adjudication or dismissed human rationale cannot be accidentally converted into
fresh improvement advice.

## Non-Goals

- Do not add automatic source or SVG editing.
- Do not create a second route selector.
- Do not add a new slash command in the first slice.
- Do not change driver action vocabulary.
- Do not mark optional candidates as blockers.
- Do not make journal-grade numeric scores gateable.
- Do not require SVG polish for safe/accepted fixtures.
- Do not mutate existing critique schemas in place.

## Integration

The first implementation slice should add a pure helper module, then attach its
result to `/fig_driver` summaries. Existing actions, stop boundaries, and
`next_action_summary` remain authoritative.

The helper should accept:

- compact status;
- selected action and stop boundary;
- latest loop checkpoint, if available;

The helper should return a deterministic summary or `None` when insufficient
evidence exists.

## Edge Cases

1. Blocking loop checkpoint exists.
   - Expected: `state: not_ready`, `candidate_count: 0`.

2. Human gate exists.
   - Expected: existing `human_gate_stop`; optional candidates must not obscure
     the human boundary.

3. Release is blocked only by force-golden or accepted/final-ready manual gate.
   - Expected: summary may be `ready_but_improvable` with `safe_to_ship: true`
     if all quality evidence is clean.

4. No loop checkpoint exists.
   - Expected: do not invent candidates. The summary may be omitted or
     `not_ready` depending on the driver action.

5. `continue_tikz` route detail exists but all gates are otherwise clean.
   - Expected: one optional TikZ candidate, not `run_fig_loop` as a blocker.

6. `ready_for_svg_polish` exists but SVG polish gate is blocked by missing
   recipe/delta.
   - Expected: optional SVG candidate can be surfaced, but existing polish-mode
     gate still owns the actual handoff.

7. Weak aesthetic lever uses `route: human_art_direction`.
   - Expected: risk `needs_human`; never auto-patch.

8. Legacy critique has no v1.11+ aesthetic fields.
   - Expected: no candidate, no failure.

9. Host prose mentions a stale issue but structured fields are pass.
   - Expected: do not extract prose-only candidates.

10. Candidate ids must be stable across repeated driver runs on the same
    evidence.
    - Expected: deterministic sort by source and source id.

## Review Checklist

- Does this create any new release blocker? It must not.
- Can it hide a real blocker behind optional language? It must not.
- Does it require trusting natural-language critique prose? It must not.
- Can it recommend editing accepted/golden/export state? It must not.
- Does it preserve current driver action and stop-boundary contracts? It must.
- Is it useful when the user asks why the plugin says "complete"? It should
  surface the remaining optional levers or explicitly say none are structured.
