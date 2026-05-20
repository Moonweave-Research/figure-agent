# Issue 9A: Fresh Re-Audit Benchmark Level

**Date:** 2026-05-19 KST
**Status:** completed
**Parent:** Issue 9
**Type:** AFK

## What to build

Add a level-only journal-grade assessment contract to fresh v1.2 critiques and
surface it in `/fig_loop`.

This slice deliberately avoids numeric scores. It introduces only the
non-monotonic fresh re-audit classification needed for loop gating:

```yaml
journal_grade_assessment:
  schema: figure-agent.journal-grade-assessment.v1
  scoring_mode: fresh_reaudit
  assessed_artifact_hash: sha256:<current critique input hash>
  benchmark_level: draft | solid_manuscript | high_impact_candidate | needs_human_art_direction | blocked
  confidence: low | medium | high
  blockers: []
  regression_detected: true | false
  regressions: []
  score_is_gateable: true | false
  next_quality_bottleneck: storyline | composition | component_fidelity | scientific_plausibility | label_semantics | polish | reference_fidelity | export_scale_readability | human_policy
  rationale: "<current artifact only>"
```

The assessment is current-artifact evidence, not progress history. Previous
levels become stale when critique inputs change.

## Acceptance criteria

- [x] `/fig_critique` brief includes the level-only assessment schema.
- [x] v1.2 critique validation accepts a valid assessment block.
- [x] v1.2 critique validation rejects invalid `scoring_mode`.
- [x] v1.2 critique validation rejects non-`sha256:` `assessed_artifact_hash`.
- [x] v1.2 critique validation rejects `high_impact_candidate` when any
  upstream quality axis is not `pass` or `not_applicable`.
- [x] v1.2 critique validation rejects `score_is_gateable: true` when
  `assessed_artifact_hash` does not match `critique_input_hash`.
- [x] v1 and v1.1 critiques remain legacy-compatible.
- [x] `/fig_loop` surfaces a valid fresh assessment in its JSON iteration.
- [x] `/fig_loop` does not mark a stale or malformed assessment as gateable.

## Blocked by

None. Can start immediately.

## Out of scope

- Numeric `overall_score` or `sub_scores`.
- Deterministic 1-column/2-column OCR/raster scoring.
- Learned quality model.
- Auto-polish, auto-patch, auto-accept, or golden mutation.
