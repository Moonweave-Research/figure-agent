# Numeric Score Dogfood Evidence (Issue 9D)

**Date opened:** 2026-05-19 KST
**Status:** open

This milestone records real host-LLM `/fig_critique` runs after Issue 9B added
optional advisory numeric score fields to `journal_grade_assessment`.

The purpose is to test whether `overall_score`, `sub_scores`, and
`score_rationale` are useful advisory evidence without becoming release gates,
progress meters, or substitutes for `quality_axes`, `benchmark_level`, human
review, export state, final-artifact state, accepted state, or golden state.

## Fixture Queue

1. `fig1_overview_v2_pair_001_vault`
2. `golden_trap_depth_picture`
3. `fig1_overview_v2`
4. `n3_trial_01_trap_depth`
5. `n3_trial_02_actuation_sequence`

## Result Summary

- Total attempted fixtures: 0
- Valid numeric score runs: 0
- Runs without complete score block: 0
- Validation or ingestion defects: 0
- Safety defects: 0

## Evidence Rows

Rows should use this structure:

### Run N: `<fixture>`

- **commands used:** `<exact sequence>`
- **critique source:** newly generated | reused fresh | not produced
- **critique schema:** `<schema or N/A>`
- **critique_input_hash:** `<sha256:... or N/A>`
- **assessed_artifact_hash:** `<sha256:... or N/A>`
- **benchmark_level:** `<value or N/A>`
- **overall_score:** `<number or N/A>`
- **sub_scores:** `<mapping or N/A>`
- **score_rationale:** `<text or N/A>`
- **score_policy from /fig_loop:** `<value or absent>`
- **score_is_gateable:** `<true/false/N/A>`
- **evaluation_state:** `<passed/stale/blocked/N/A>`
- **next_quality_bottleneck:** `<value or N/A>`
- **regression_detected:** `<true/false/N/A>`
- **regressions:** `<list or []/N/A>`
- **/fig_loop stop_reason:** `<value>`
- **/fig_loop escalation_level:** `<value>`
- **/fig_driver final action:** `<value>`
- **/fig_driver stop_boundary:** `<value or null>`
- **reviewer verdict:** useful | too_flat | contradictory | unsafe | invalid
- **rationale:** `<short evidence-grounded rationale>`

## Final Judgment

Pending 5 real fixture runs.
