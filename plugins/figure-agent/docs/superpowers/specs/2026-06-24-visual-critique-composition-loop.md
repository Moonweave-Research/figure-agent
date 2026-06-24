# Visual Critique Composition Loop

Date: 2026-06-24

Source of truth: `2026-06-24-visual-critique-composition-loop.workflow.plan.json`

## Research And Prior Art

The existing composition-search plan already established the safe rail:
host-authored candidates enter as structured JSON, render in fixture-local
sandboxes, rank/review without hidden mutation, then require hash-bound human
acceptance and apply gates before source changes.

The current fig3 dogfood slice proved the first visible milestone: structural
families can generate candidates, render them, form composites, and produce a
comparison board. The remaining gap is not more candidate plumbing. The gap is
that visible evidence must become a first-class review artifact, so a human can
judge the figure without reverse-engineering TeX operations.

## Product Position And Non-Goals

This workflow positions figure-agent as a visual editing amplifier for scientific
figures. It should expose rendered alternatives, preserve scientific/source
boundaries, and make the best next edit inspectable.

Non-goals:

- plugin-side model or API calls;
- automatic aesthetic judgment;
- hidden fixture source mutation;
- automatic TeX/export/golden refresh after apply;
- MCP or external surface expansion;
- replacing human acceptance.

## Workflow Architecture

Pattern mix:

- Pipeline for candidate generation, render, rank, review, acceptance, and apply.
- Bounded fan-out/fan-in for independent reviewers and composite candidates.
- Adversarial verification for claims about visual improvement, source mutation,
  and scientific invariants.
- Human gate before any source mutation.
- Resume/cache by candidate-set, source, render-manifest, board, and review hashes.
- Judge panel where multiple visually plausible candidates compete.

Phases:

1. `P0 Freeze Current Visual Baseline`: inventory current fig3 candidates, boards,
   hashes, and verification state.
2. `P1 Review Packet Carries Visible Evidence`: review packets must include
   render artifacts, board paths, and hash linkage.
3. `P2 Render-Derived Visual Signals`: add deterministic checks such as nonblank
   images, dimensions, and expected artifacts. No aesthetic scoring.
4. `P3 Composite Search Loop`: create bounded composite candidates from
   compatible single-family operations.
5. `P4 Judge Panel And Refutation`: independently refute claims against source,
   rendered artifacts, tests, and gates.
6. `P5 Human Acceptance And Apply Boundary`: use only existing hash-bound
   readiness, acceptance, and apply commands.
7. `P6 Post-Apply Proof`: if apply happens, produce before/after visual proof and
   rollback evidence.
8. `P7 Generalize Beyond Fig3`: move the visible-evidence contract to a second
   fixture or record a precise prerequisite gap.

## Execution Model

First wave:

- `W1S1-baseline-receipt`: write `baseline_state.json` for the current fig3
  candidate artifact set.
- `W1S2-review-packet-gap-test`: add a RED test requiring visual evidence fields
  in review packets.

Follow-on waves:

- `W2`: implement visual evidence in review packets and deterministic
  render-derived signals.
- `W3`: build bounded composite search and run judge/refutation fan-in.
- `W4`: either accept/apply with explicit human approval or generalize the
  workflow to another fixture.

The safe default at every gate is to preserve artifacts and stop rather than
mutate source, refresh golden/export outputs, add dependencies, or call models.

## Safety And Verification Gates

Verification must falsify these outputs:

- Review packets are visible decision packets, not JSON-only summaries.
- Visual metrics are deterministic artifact checks, not aesthetic scoring.
- Composite search preserves sandbox and source-mutation boundaries.
- No plugin-side model/API calls were introduced.
- The workflow produces a nonblank, inspectable comparison PNG.

Risk gates requiring explicit user approval:

- dependency installation;
- TeX/render beyond the selected fixture;
- source mutation;
- accepted/golden/export writes;
- push/publish;
- model/API/MCP expansion.

## Evaluation Fixtures

Primary fixture:

- `plugins/figure-agent/examples/fig3_resistance_mechanism/`

Current visible artifacts to preserve and improve:

- `build/candidates/fig3_structural_family_comparison.png`
- `build/candidates/fig3_composite_comparison.png`
- `build/candidates/fig3_refined_composite_comparison.png`
- `build/candidates/CFAM_COMBO_002/composition_review_packet.json`

Secondary fixture selection is deliberately deferred until fig3 visible-evidence
contracts pass. The next fixture must have enough semantic markers to avoid
creating fixture-specific hacks.

## Release Or Implementation Plan

Start with `W1`. Do not implement the full workflow in one pass.

Minimal first commands after `W1` edits:

```bash
uv run --project plugins/figure-agent pytest \
  plugins/figure-agent/tests/test_composition_review.py \
  plugins/figure-agent/tests/test_composition_render.py \
  plugins/figure-agent/tests/test_composition_structural_families.py
```

Then run:

```bash
uv run --project plugins/figure-agent ruff check \
  plugins/figure-agent/scripts/composition_review.py \
  plugins/figure-agent/scripts/composition_render.py \
  plugins/figure-agent/tests/test_composition_review.py \
  plugins/figure-agent/tests/test_composition_render.py \
  plugins/figure-agent/tests/test_composition_structural_families.py
```

For completion, the wave receipt must name exact files changed, exact commands
run, skipped checks, and the current best visible board path.
