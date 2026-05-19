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

- Total attempted fixtures: 1
- Valid numeric score runs: 1
- Runs without complete score block: 0
- Open validation or ingestion defects: 0
- Validation footguns caught and fixed during run: 1
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

### Run 1: `fig1_overview_v2_pair_001_vault`

- **commands used:**
  1. `uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal "dogfood 9D numeric score evidence" --dry-run` (returned `safe_command: /fig_critique fig1_overview_v2_pair_001_vault`, `stop_boundary: host_llm_critique_required`)
  2. `uv run python3 scripts/critique_brief.py examples/fig1_overview_v2_pair_001_vault` (generated brief; current `critique_input_hash` = `sha256:5fa0e33a844ce285e3b43a816ac264254b9099e660b7f56906ca065bee68596b`)
  3. host `/fig_critique fig1_overview_v2_pair_001_vault` (host Claude main loop read `build/fig1_overview_v2_pair_001_vault.png`, `reference/codex_gen_overview_v1.png`, and the three panel D/E/F build-crop + reference pairs, then wrote `examples/fig1_overview_v2_pair_001_vault/critique.md` at schema v1.2 with full `audit_enumeration`, `quality_axes`, and `journal_grade_assessment` numeric score block)
  4. `uv run python3 scripts/critique_adjudication.py scaffold fig1_overview_v2_pair_001_vault --force` (first attempt failed with `adjudication.decisions[1].duplicate finding_id: P001` because both panels D and E reused id `P001`; after retitling panel E's finding to `P002` the scaffold succeeded and wrote `critique_adjudication.yaml` with both findings stamped `needs_human`)
  5. `uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault --goal "dogfood 9D numeric score evidence" --json` (ingested the `journal_grade_assessment` block; loop checkpoint at `.scratch/fig-loop-runs/20260519-133131-775392-fig1_overview_v2_pair_001_vault/iteration_001.json`)
  6. `uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal "dogfood 9D numeric score evidence" --dry-run` (final action `human_gate_stop`)
- **critique source:** newly generated
- **critique schema:** `figure-agent.critique.v1.2`
- **critique_input_hash:** `sha256:5fa0e33a844ce285e3b43a816ac264254b9099e660b7f56906ca065bee68596b`
- **assessed_artifact_hash:** `sha256:5fa0e33a844ce285e3b43a816ac264254b9099e660b7f56906ca065bee68596b`
- **benchmark_level:** `solid_manuscript`
- **overall_score:** `78`
- **sub_scores:** `{storyline: 88, composition: 76, component_fidelity: 86, scientific_plausibility: 92, label_semantics: 78, polish: 70, reference_fidelity: 75, export_scale_readability: 80}`
- **score_rationale:** "Numbers describe only the current artifact, not progress. Storyline (88) is high because the 30-second message is legible at a glance and the three-spoke bridge is unambiguous. Composition (76) reflects the D label-density notch and the busy E sub-zone gap. Component fidelity (86) reflects clear apparatus identity in all three result panels and the consistent C setup; it is not 95 because the row-2 background wavy chains add visual texture that competes mildly with apparatus outlines. Scientific plausibility (92) reflects clean BLOCKER-invariant compliance. Label semantics (78) reflects correct label-target binding with the D deep-rich/shallow-rich labels constrained to white-fill mid-line slots. Polish (70) is the lowest sub-score because the D label-on-line and the E τ_d/derive cluster are the residual visible items. Reference fidelity (75) reflects style-only transfer with no hallucinated content; it cannot rise higher because per-panel references are not content authorities. Export-scale readability (80) reflects Nature 7pt typography compliance and PNG-scale visibility but has not been verified at thumbnail / print scale in this loop."
- **score_policy from /fig_loop:** `absent` (omitted because `score_is_gateable: false`; `scripts/fig_loop.py:467` only emits `score_policy: advisory_fresh_reaudit_not_gate` when the host opts the score in as gateable)
- **score_is_gateable:** `false` (host claim; loop also confirmed `false` after re-deriving from hashes)
- **evaluation_state:** `stale` (loop wrapper marks the score block stale because `score_is_gateable: false` keeps the score advisory-only, as designed by Issue 9B)
- **next_quality_bottleneck:** `polish`
- **regression_detected:** `false`
- **regressions:** `[]`
- **/fig_loop stop_reason:** `human_gate_required`
- **/fig_loop escalation_level:** `human_review_required`
- **/fig_driver final action:** `human_gate_stop`
- **/fig_driver stop_boundary:** `human_gate_required`
- **reviewer verdict:** `useful`
- **rationale:** The score block is complete (all eight sub-scores present), validates through `critique_adjudication.py scaffold` and `fig_loop.py` ingestion, and `overall_score: 78` broadly agrees with `benchmark_level: solid_manuscript`. Sub-scores distinguish at least four meaningful quality dimensions: polish (70) sits 22 points below scientific_plausibility (92), and storyline (88) sits 18 points above polish; the spread points concretely to the D label-on-line density and the E τ_d/derive sub-zone clustering. `next_quality_bottleneck: polish` is concrete (cites two specific findings P001/P002) and matches the prose rationale. Most importantly, the score did not bypass any non-score gate: `score_is_gateable: false` cleanly kept the loop on `human_gate_required` for the two NIT findings, and the driver's final action `human_gate_stop` and stop boundary `human_gate_required` came from the `needs_human` adjudication of P001/P002 rather than from the numeric score. Acceptance, golden, and export gates all stayed at `NOT_ACCEPTED` / `TRACKED_GOLDEN` / `NONE` throughout. The one validation defect (duplicate panel finding id `P001` across panels D and E) was caught by `critique_adjudication.py scaffold` and fixed in-loop by retitling panel E's finding to `P002` before any downstream step relied on the duplicate; it is recorded here as a recurring authoring footgun for cross-panel finding-id uniqueness rather than a score-block defect.

## Final Judgment

Pending 5 real fixture runs.
