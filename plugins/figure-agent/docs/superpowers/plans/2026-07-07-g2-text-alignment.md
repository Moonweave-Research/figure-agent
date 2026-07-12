# G2 Text Alignment Plan

## Goal

Ship G2 only: extend `semantic_assertions` with declaration-driven text alignment checks and wire alignment violations into the existing deterministic auto-promotion path. Do not build G1/G3 vector parsing or vector alignment.

## Constraints

- No LLM or aesthetic pass/fail gate.
- No topology or intent inference; every check is authored in `spec.yaml`.
- Preserve fail-closed behavior and make selector resolution P5-compliant: zero-match and multi-match both fail loud.
- Keep G2 as a separate stacked PR over G4; do not batch G1/G3.
- P2 false-positive verdict remains a human checkpoint. Produce raw findings only.

## Implementation Steps

1. Add RED semantic assertion tests.
   - Parse alignment declarations with `kind`, `targets`, and optional `tolerance_cm`.
   - Reject malformed alignment declarations and too-few targets.
   - Detect `baseline_aligned`, `top_aligned`, `left_aligned`, `right_aligned`, `center_aligned_x`, and `center_aligned_y` violations with numeric deltas.
   - Enforce P5 for relation and alignment selectors: zero-match -> `anchor_missing`; multi-match -> `anchor_ambiguous`.

2. Implement text-only alignment in `scripts/semantic_assertions.py`.
   - Preserve existing relation assertions and `tolerance_pt`.
   - Add alignment assertion parsing with default `tolerance_cm = 0.05`.
   - Convert cm tolerance to points explicitly.
   - Measure N-way alignment as `max(metric) - min(metric)`.
   - Emit deterministic issues with `measured_delta_pt`, `measured_delta_cm`, `tolerance_pt`, `tolerance_cm`, `kind`, and `targets`.

3. Add source freshness to semantic reports.
   - Include current TeX source hashes in `semantic_assertions_payload` when available.
   - Keep missing spec = no declarations; corrupt spec/report remains loud.

4. Wire semantic assertions into G4 promotion.
   - Mark `semantic_assertions` auto-promote eligible only after P5 tests pass.
   - Validate `semantic_assertions.json` schema and freshness.
   - Auto-promote semantic violations with `promoted_by: auto`, `source_detector: semantic_assertions`, measured deltas, and edit family `label_offset` / `bounded_coordinate_offset` for alignment violations.
   - Leave non-promoting advisory detectors unchanged.

5. Seed declarations and acceptance fixtures.
   - Add fig1 v5f row-subtitle baseline assertion for `kinetic`, `ISPD`, and `mechanical`.
   - Add a synthetic non-v5f alignment-recall test with a deliberate baseline float.
   - Produce corpus raw-finding output for the human P2 false-positive review without deciding verdicts.

6. Verify.
   - Run targeted semantic and promotion tests.
   - Run ruff on changed Python.
   - Run the full test suite before PR.
   - Push `g2-text-alignment` and open a separate stacked PR.
