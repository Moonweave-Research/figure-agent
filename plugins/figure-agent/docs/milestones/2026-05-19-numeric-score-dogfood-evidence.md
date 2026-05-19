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

- Total attempted fixtures: 3
- Valid numeric score runs: 3
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

### Run 2: `golden_trap_depth_picture`

- **commands used:**
  1. `uv run python3 scripts/fig_driver.py golden_trap_depth_picture --mode review --goal "dogfood 9D numeric score evidence" --dry-run` (returned `safe_command: /fig_critique golden_trap_depth_picture`, `stop_boundary: host_llm_critique_required`; critique was STALE because the previous critique was authored under generator_version `4a7d64ba...` while the current generator is `b48de8a1...`)
  2. `uv run python3 scripts/critique_brief.py examples/golden_trap_depth_picture` (generated brief; current `critique_input_hash` = `sha256:a794641f2a9dd36468d704e2e7de8ca22e17bf6c3e1c9900bebe20aab9f04fba` — unchanged from prior run because the rendered artifact is byte-identical; only the generator version moved)
  3. host `/fig_critique golden_trap_depth_picture` (host Claude main loop read `build/golden_trap_depth_picture.png` and `reference/golden_target_001.png`, then wrote `examples/golden_trap_depth_picture/critique.md` at schema v1.2 with full `audit_enumeration`, `quality_axes`, and a fresh `journal_grade_assessment` numeric score block; prior critique had only the qualitative score block — `score_is_gateable: true` without `overall_score` / `sub_scores` / `score_rationale` — so this run is the first to attach the complete Issue 9B score block to this fixture)
  4. `uv run python3 scripts/critique_adjudication.py scaffold golden_trap_depth_picture --force` (succeeded on first attempt because `verdict: ready` with empty panel and top-level findings produced `decision_count: 0`; the Run 1 cross-panel `P001` footgun did not recur)
  5. `uv run python3 scripts/fig_loop.py golden_trap_depth_picture --goal "dogfood 9D numeric score evidence" --json` (ingested the `journal_grade_assessment` block; loop checkpoint at `.scratch/fig-loop-runs/20260519-135234-541083-golden_trap_depth_picture/iteration_001.json`)
  6. `uv run python3 scripts/fig_driver.py golden_trap_depth_picture --mode review --goal "dogfood 9D numeric score evidence" --dry-run` (final action `release_blocked`)
- **critique source:** newly generated
- **critique schema:** `figure-agent.critique.v1.2`
- **critique_input_hash:** `sha256:a794641f2a9dd36468d704e2e7de8ca22e17bf6c3e1c9900bebe20aab9f04fba`
- **assessed_artifact_hash:** `sha256:a794641f2a9dd36468d704e2e7de8ca22e17bf6c3e1c9900bebe20aab9f04fba`
- **benchmark_level:** `solid_manuscript`
- **overall_score:** `86`
- **sub_scores:** `{storyline: 90, composition: 84, component_fidelity: 90, scientific_plausibility: 94, label_semantics: 86, polish: 78, reference_fidelity: 92, export_scale_readability: 82}`
- **score_rationale:** "Numbers describe only the current artifact, not progress. Storyline (90) is high because three left-side rows converge to one right-side picture through the teal brace and the read path is unambiguous. Composition (84) reflects clean 4-column landscape with thin gray row separators; the right-side energy diagram still carries the densest visual region (CB/VB lines, scattered shallow/deep markers, vertical Energy axis, E_t label, lobe pair all packed against a single vertical axis). Component fidelity (90) reflects every briefing-named element being identifiable in the render. Scientific plausibility (94) is the highest sub-score because all five physics invariants hold cleanly. Label semantics (86) reflects PlotCallout-anchored leader lines with white backing, including 'Discharge (Debye reference)' placed outside the plot box per briefing semantic_assertion. Polish (78) is the lowest sub-score because the visual register is intentionally explanatory-schematic — rows feel utilitarian, teal accent is single-purpose, and Row 3 polymer chains carry lower visual mass than Row 1 plots or the right-side diagram. Reference fidelity (92) reflects close layout and callout-structure match to reference/golden_target_001.png with only briefing-mandated functional deviations (PGFPlots curves, skeletal polymer chains). Export-scale readability (82) reflects 5.2pt tiny labels for chemical/physical-origin sub-captions still being readable at PNG scale, though this loop did not verify thumbnail / print-scale legibility."
- **score_policy from /fig_loop:** `absent` (`scripts/fig_loop.py:467` only emits `score_policy: advisory_fresh_reaudit_not_gate` when the host opts in with `score_is_gateable: true`; this run keeps the score advisory per the Issue 9B safe default)
- **score_is_gateable:** `false`
- **evaluation_state:** `stale` (loop wrapper marks the score block stale because `score_is_gateable: false` keeps the score advisory-only, as designed by Issue 9B)
- **next_quality_bottleneck:** `polish`
- **regression_detected:** `false`
- **regressions:** `[]`
- **/fig_loop stop_reason:** `status_action_required`
- **/fig_loop escalation_level:** `manual_approval_required`
- **/fig_driver final action:** `release_blocked`
- **/fig_driver stop_boundary:** `force_golden_required`
- **reviewer verdict:** `useful`
- **rationale:** The score block is complete and validates through `critique_adjudication.py scaffold` (0 decisions because the figure had no findings, `verdict: ready`) and through `fig_loop.py` ingestion (assessed_artifact_hash matches critique_input_hash; loop surfaces `evaluation_state: stale` exactly because the host kept `score_is_gateable: false`, matching the safe Issue 9B default). `overall_score: 86` broadly agrees with `benchmark_level: solid_manuscript` — the score is comfortably above the Run 1 figure (78) and consistent with a golden-target-matched, physics-invariant-clean schematic that intentionally stays in explanatory-schematic register rather than promoting to `high_impact_candidate`. Sub-scores separate four meaningful dimensions: scientific_plausibility (94) is highest because every physics invariant from briefing.md holds, polish (78) is lowest because Row 3 polymer chains carry lower visual mass than Row 1 plots and the right-side diagram, and reference_fidelity (92) reads above polish because the build matches the golden target while only deviating in briefing-mandated ways. `next_quality_bottleneck: polish` is concrete (it points to the visual-weight balance lever and the polymer-chain rendering richness). Critically, this run satisfies the Issue 9D acceptance bullet that score must not bypass a non-score gate: the driver's final action is `release_blocked` and the stop_boundary is `force_golden_required` (driven by tracked-golden roll-forward needing manual approval), not by the numeric score. Acceptance, golden, final-artifact, and export gates all stayed at `NOT_ACCEPTED` / `TRACKED_GOLDEN` / `NONE` / `false`. Together with Run 1's `human_gate_required` stop boundary, the two runs demonstrate score-orthogonality against two distinct non-score gates.

### Run 3: `fig1_overview_v2`

- **commands used:**
  1. `uv run python3 scripts/fig_driver.py fig1_overview_v2 --mode review --goal "dogfood 9D numeric score evidence" --dry-run` (returned `safe_command: /fig_critique fig1_overview_v2`, `stop_boundary: host_llm_critique_required`; critique was STALE because the previous critique was authored under generator_version `4a7d64ba...` while the current generator is `b48de8a1...`)
  2. `uv run python3 scripts/critique_brief.py examples/fig1_overview_v2` (generated brief; current `critique_input_hash` = `sha256:eef5193f0298b64c503391e6ea556425851f0ec9d4da5ac795d4220ba225bd77` — unchanged from prior run because the rendered artifact is byte-identical; only the generator version moved)
  3. host `/fig_critique fig1_overview_v2` (host Claude main loop read `build/fig1_overview_v2.png` and `reference/codex_gen_overview_v1.png`, then refreshed `examples/fig1_overview_v2/critique.md` to current generator version while preserving the three prior fresh-re-audit findings F001/F002/F003 and attaching the complete Issue 9B numeric score block; prior critique had only the qualitative score block — `score_is_gateable: true` without `overall_score` / `sub_scores` / `score_rationale`)
  4. `uv run python3 scripts/critique_adjudication.py scaffold fig1_overview_v2 --force` (succeeded on first attempt; the prior cross-panel `P001` footgun did not recur because this fixture uses figure-level finding ids F001/F002/F003 rather than per-panel ids; `decision_count: 3` with every decision defaulted to `needs_human`)
  5. `uv run python3 scripts/fig_loop.py fig1_overview_v2 --goal "dogfood 9D numeric score evidence" --json` (ingested the `journal_grade_assessment` block; after correcting the markdown-body `score_is_gateable` prose to match the frontmatter, the verified loop checkpoint is `.scratch/fig-loop-runs/20260519-231944-022469-fig1_overview_v2/iteration_001.json`)
  6. `uv run python3 scripts/fig_driver.py fig1_overview_v2 --mode review --goal "dogfood 9D numeric score evidence" --dry-run` (final action `human_gate_stop`)
- **critique source:** newly generated
- **critique schema:** `figure-agent.critique.v1.2`
- **critique_input_hash:** `sha256:eef5193f0298b64c503391e6ea556425851f0ec9d4da5ac795d4220ba225bd77`
- **assessed_artifact_hash:** `sha256:eef5193f0298b64c503391e6ea556425851f0ec9d4da5ac795d4220ba225bd77`
- **benchmark_level:** `draft`
- **overall_score:** `64`
- **sub_scores:** `{storyline: 72, composition: 64, component_fidelity: 76, scientific_plausibility: 56, label_semantics: 58, polish: 60, reference_fidelity: 70, export_scale_readability: 66}`
- **score_rationale:** "Numbers describe only the current artifact, not progress. Storyline (72) reflects that the two-row narrative is recoverable but the Row 1 → Row 2 bridge is visibly thin (F002). Composition (64) reflects the 7-panel grid feel — no HERO panel and no cover-style row-2 background wash. Component fidelity (76) is the strongest reading because every briefing-named element (S8 inset, DIB ring, polysulfide chains, S60–S85 chains, distributed-release wells, V_s(t) decay, g(E_t) lobes, cantilever, electrode, q_tr, air gap, Coulomb, Maxwell) is identifiable in the render. Scientific plausibility (56) is the lowest sub-score because of the unresolved cross-panel color-convention contradiction (F001: Panel C uses blue=deep / red=shallow per briefing §3 but g(E_t) uses blue=Shallow / red=Deep per briefing §2). Label semantics (58) reflects 45 visual-clash candidates from check_visual_clash.py with several real label-on-geometry collisions on 'Coulomb', 'Maxwell', 'attraction', 'log', 't', 'I(t)', and minus signs (F003). Polish (60) reflects the draft-level execution: label clash on the Row 2 power-law plot, weak Row 1 → Row 2 bridge, and no cover-binding wash. Reference fidelity (70) reflects panel ordering, color-block placement, and macroscopic-probe geometry following codex_gen_overview_v1.png with only schematic simplifications; it cannot rise higher because the missing cover-binding pattern is a real reference-deviation. Export-scale readability (66) reflects the small label sizes around the distributed-release wells and the ISPD column with no thumbnail / print-scale verification this loop."
- **score_policy from /fig_loop:** `absent` (`scripts/fig_loop.py:467` only emits `score_policy: advisory_fresh_reaudit_not_gate` when the host opts in with `score_is_gateable: true`; this run keeps the score advisory per the Issue 9B safe default)
- **score_is_gateable:** `false` (downgraded from the prior critique's `true`; this run honors the Issue 9D safe default that hosts should not opt scores into the gate path without separate review)
- **evaluation_state:** `stale` (loop wrapper marks the score block stale because `score_is_gateable: false` keeps the score advisory-only, as designed by Issue 9B)
- **next_quality_bottleneck:** `scientific_plausibility`
- **regression_detected:** `false`
- **regressions:** `[]`
- **/fig_loop stop_reason:** `human_gate_required`
- **/fig_loop escalation_level:** `human_review_required`
- **/fig_driver final action:** `human_gate_stop`
- **/fig_driver stop_boundary:** `human_gate_required`
- **reviewer verdict:** `useful`
- **rationale:** The score block is complete and validates through `critique_adjudication.py scaffold` (3 decisions for F001/F002/F003 all defaulted to `needs_human`) and through `fig_loop.py` ingestion. `overall_score: 64` broadly agrees with `benchmark_level: draft` and sits 14 points below Run 1's solid_manuscript (78) and 22 points below Run 2's golden (86), which is the kind of fixture-vs-fixture separation Issue 9D is testing for. Sub-scores distinguish at least four meaningful quality dimensions: scientific_plausibility (56) is the lowest because of F001's cross-panel color-convention contradiction, label_semantics (58) is next because of F003's 45 clash candidates, and component_fidelity (76) reads highest because every briefing-named element is identifiable in the render. `next_quality_bottleneck: scientific_plausibility` is concrete (it points specifically to the F001 briefing-level color reconciliation as the upstream fix that must precede polish — matching the prior critique's diagnosis). Critically, the score did not bypass any non-score gate: the driver's `action: human_gate_stop` and `stop_boundary: human_gate_required` came from the `needs_human` adjudication of F001 (a MAJOR palette finding flagged via `quality_axes.scientific_plausibility.blocking_items` and `publication_readiness.blocking_items`), not from `overall_score: 64`. Acceptance, golden, and final-artifact gates all stayed at `NOT_ACCEPTED` / `false` / `NONE`. Together with Run 1 (`human_gate_required` driven by panel-level NIT adjudication) and Run 2 (`force_golden_required` driven by tracked-golden roll-forward), Run 3 reaffirms that `human_gate_required` is preserved even at a much lower overall_score (64 vs 78) and with a much more severe upstream verdict (`publication_readiness: needs_patch` vs `pass`). No regression vs the prior re-audit; the three findings F001/F002/F003 are byte-identical to the prior critique because the rendered artifact is byte-identical.

## Final Judgment

Pending 5 real fixture runs.
