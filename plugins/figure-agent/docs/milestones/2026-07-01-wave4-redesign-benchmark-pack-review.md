# Wave 4 Redesign Benchmark Pack Review

Date: 2026-07-01

## Scope

Review and evidence-hardening slice for the Wave 4 bounded candidate/redesign
benchmark pack. This slice documents the existing style benchmark pack and
comparison contract and adds regression coverage for the per-family evidence
fields already required by the loaders.

Hard boundaries preserved:

- No fixture source mutation under `examples/`.
- No generated export, `.scratch`, accepted, golden, final-artifact,
  publication, or release-state mutation.
- No polished SVG output.
- No candidate apply path was invoked; comparisons remain review metadata only.

## Contract reviewed

The style benchmark pack/comparison surfaces keep the required family set aligned:

- `current_style`
- `restrained_tikz_refinement`
- `editorial_redesign`
- `svg_polish_handoff`

For each family, the surfaces encode:

- `what_can_improve` — the bounded visual/design improvement claim.
- `forbidden_semantic_changes` — the semantic boundaries a prettier candidate
  cannot cross.
- `proof_criteria` — evidence required before the family can beat the current
  benchmark.
- `human_only_question` — the remaining decision that must stay human-gated.

The comparison contract also preserves per-family `authorizes_mutation=false`,
`semantic_change_allowed=false`, and the mutation-boundary match against the
source style benchmark pack. `current_style` remains the only allowed winner
until a real candidate exists and separately approved mutation gates are opened.

## Files reviewed / hardened

- `docs/style-benchmark-packs/2026-06-30-wave-c/*.json`
- `docs/style-benchmark-comparisons/2026-07-01-wave-f/*.json`
- `scripts/style_benchmark_pack.py`
- `scripts/style_benchmark_comparison.py`
- `tests/test_style_benchmark_pack_loader.py`
- `tests/test_style_benchmark_comparison.py`

## Added regression coverage

- Style benchmark packs now have focused test coverage that removing a
  per-family proof criterion is rejected.
- Style benchmark comparisons now have focused test coverage that removing a
  per-family proof criterion is rejected.

These tests guard the Wave 4 requirement that every required family states what
can improve, what semantic changes are forbidden, what evidence would prove it
is better, and what human-only question remains.

## Stop condition

This slice stops at review/documentation/test hardening. It does not apply a
candidate, accept a candidate, export, force golden, polish SVG, or change
release/accepted/publication/final-artifact state.
