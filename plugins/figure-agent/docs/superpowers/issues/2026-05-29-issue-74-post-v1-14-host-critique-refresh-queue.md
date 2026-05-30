# Issue 74 - Post-v1.14 Host Critique Refresh Queue

Status: completed

Closeout: `docs/milestones/2026-05-29-post-v1-14-host-critique-refresh-queue.md`

All three queued critiques were refreshed to the v1.14 generator stamp
(`sha256:46e53b4c…`) with byte-identical inputs (`critique_input_hash` unchanged):
`golden_trap_depth_picture` and `fig1_overview_v2` stayed on the v1.10 base
(generator re-stamp only); `fig1_overview_v2_pair_001_vault` migrated to schema
v1.14 (added editorial route-detail + crop-anomaly accounting), carrying its
observations and all human adjudication decisions forward via `sync`. Each fixture
now reports `critique_state: FRESH` and no longer stops first on `critique_stale`.

Next true gates: `golden_trap_depth_picture` and `fig1_overview_v2_pair_001_vault`
stop on the tracked-golden export / `--force-golden` (and accepted-or-final-ready
for pair_001) human gate; `fig1_overview_v2` stops on human acceptance
(`not_accepted`). No protected file was mutated. Full pytest (1434 passed), ruff,
diff check, and all three plugin validations pass.

Depends on:

- Issue 73 SVG polish trigger semantics
- Issue 71E release/golden/publication gate rehearsal

Type: HITL host-vision closeout

## Problem

Issue 73 intentionally changed `critique_brief.py` and the advanced critique
contract to v1.14. Hash-based freshness therefore marks existing critiques
stale even when the rendered figure image did not change. Issue 71E confirmed
that several release candidates now stop at `host_llm_critique_required`
before release, tracked-golden, publication, or acceptance gates can be
rehearsed again.

This is correct safety behavior. The plugin must not bypass stale host-vision
critique just to reach release gates.

## Current Queue

As of 2026-05-29, these fixtures are the active post-Issue-73 queue:

| Fixture | First blocker | Driver action | Boundary | Notes |
|---|---|---|---|---|
| `fig1_overview_v2_pair_001_vault` | `critique_stale` | `/fig_critique fig1_overview_v2_pair_001_vault` | `host_llm_critique_required` | accepted/tracked-golden candidate; publication gate currently PASS |
| `golden_trap_depth_picture` | `critique_stale` | `/fig_critique golden_trap_depth_picture` | `host_llm_critique_required` | tracked-golden, not accepted; publication provenance still human-gated |
| `fig1_overview_v2` | `critique_stale` | `/fig_critique fig1_overview_v2` | `host_llm_critique_required` | export present, not accepted; missing publication audit |

Out-of-queue controls:

- `fig5_floating_clip_mechanism` is release-blocked by missing export plus
  `acceptance_state: NOT_ACCEPTED`, not host critique.
- `fig3_trapping_concept` and `smoke_trap_demo` exercise release-operator
  boundary behavior but do not need host critique.

## Goal

Refresh the stale host-vision critiques introduced by the v1.14 contract change
without source edits, export edits, accepted/golden mutation, or publication
provenance fabrication. Then re-run lint, adjudication sync/scaffold, loop, and
driver checks to prove each fixture has moved past `critique_stale` to its
next true gate.

## Scope

In scope:

- Run `/fig_critique <fixture>` in a host vision loop for the three fixtures.
- Ensure the host reads full render, required audit crops, visual-clash crops,
  text-boundary/label-path candidates, print-scale images, reference images,
  and any v1.14 route-detail prompt sections printed by `critique_brief.py`.
- Run `critique_lint.py` after each critique.
- Use conservative adjudication handling:
  - preserve existing human-authored decisions when possible with sync or
    hash-only rebind;
  - use scaffold/force only if the prior adjudication contains no human value
    to preserve.
- Run `/fig_loop --json` and `/fig_driver --mode review/release --dry-run` to
  record the next gate.
- Document the outcome in a milestone.

Out of scope:

- Editing `.tex`, `briefing.md`, `spec.yaml`, exports, polished SVGs, accepted
  flags, golden artifacts, or `QUALITY_AUDIT.md`.
- Running `--force-golden`.
- Changing publication provenance.
- Auto-applying critique findings.
- Treating numeric score or `ready_for_svg_polish` as release authority.

## Acceptance

- All three queued fixtures have `critique_state: FRESH` after refresh.
- Every new `critique.md` passes `uv run python3 scripts/critique_lint.py
  examples/<fixture>`.
- Every `critique_adjudication.yaml` is present, schema-valid, and fresh
  against its source critique.
- `/fig_loop <fixture> --json` runs successfully where the status gate allows
  it, or the milestone records the earlier gate that prevents loop.
- `/fig_driver --mode release --dry-run` no longer stops first on
  `critique_stale`; it stops on the true human/release/publication/golden gate.
- No source/export/accepted/golden/publication/SVG file is mutated.
- Full pytest, ruff, diff check, and plugin validation pass after the queue is
  closed.

## Review Questions

1. Did the host vision step actually inspect the required crops and references,
   or merely rewrite hashes?
2. Did the v1.14 route-detail contract improve SVG-polish trigger clarity?
3. Were human adjudication decisions preserved rather than overwritten?
4. Did release mode expose the next true gate after critique freshness closed?
5. Did any plugin defect appear, or are remaining blockers fixture/human
   decisions?
