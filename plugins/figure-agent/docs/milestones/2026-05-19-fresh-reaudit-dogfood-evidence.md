# Fresh Re-Audit Dogfood Evidence (Issue 9C)

**Date opened:** 2026-05-19 KST
**Parent issue:** `docs/superpowers/issues/2026-05-19-issue-9c-fresh-reaudit-dogfood-evidence.md`
**Status:** in progress (3/5 fixtures recorded; 1 critique-not-required blocker)

This milestone collects host-LLM `journal_grade_assessment` evidence on real
fixtures so the level-only fresh re-audit rubric can be evaluated against
actual failure modes before Issue 9B numeric scoring is opened.

Constraints (per Issue 9C):

- Do not patch source.
- Do not force golden exports.
- Do not edit accepted state.
- Do not invent numeric scores.
- Each evidence row must come from a real host-authored v1.2 `critique.md` or
  record why a v1.2 critique could not be produced.

## Evidence Rows

### Run 1 — `fig1_overview_v2_pair_001_vault`

- **fixture name:** `fig1_overview_v2_pair_001_vault`
- **command sequence actually used:**
  ```bash
  uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  /fig_critique fig1_overview_v2_pair_001_vault                # host vision; reads build PNG + figure-level reference + panel D/E/F build crops and their references; writes critique.md (v1.2 + journal_grade_assessment)
  uv run python3 scripts/critique_adjudication.py scaffold fig1_overview_v2_pair_001_vault --force  # prior adjudication was stale against new critique hash; --force required
  uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault --goal "dogfood 9A fresh re-audit" --json
  uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  ```
- **critique schema:** `figure-agent.critique.v1.2`
- **`critique_input_hash`:** `sha256:c338cef68e9d2ea4b5722f08d96bb021f6bc2096b9ab508fb6a710da044b2ed4`
- **`journal_grade_assessment.assessed_artifact_hash`:** `sha256:c338cef68e9d2ea4b5722f08d96bb021f6bc2096b9ab508fb6a710da044b2ed4` (matches `critique_input_hash`)
- **`score_is_gateable`:** `true`
- **`benchmark_level`:** `solid_manuscript`
- **`confidence`:** `medium`
- **`next_quality_bottleneck`:** `polish`
- **`regression_detected`:** `false`
- **`regressions`:** `[]`
- **`/fig_loop` `stop_reason`:** `status_action_required`
- **`/fig_loop` surfaced `journal_grade_assessment.evaluation_state`:** `passed` (per `.scratch/fig-loop-runs/20260519-112458-298063-fig1_overview_v2_pair_001_vault/iteration_001.json` → `journal_grade_assessment.evaluation_state`)
- **`/fig_driver` next action after loop ingestion:** `action: release_blocked`, `safe_command: null`, `stop_boundary: force_golden_required`, `loop_checkpoint.recommended_next_action: "tracked golden artifact is intentionally stale; to roll forward run /fig_export fig1_overview_v2_pair_001_vault --force-golden."`
- **reviewer verdict:** `useful`
- **rationale for verdict:**
  - Audit + quality-axis blocks were all filled; `journal_grade_assessment` is fresh (`assessed_artifact_hash == critique_input_hash`) and gateable.
  - `benchmark_level: solid_manuscript` is consistent with every applicable quality axis being `pass`. The host did NOT promote to `high_impact_candidate` because two real polish-ceiling items (Panel D label-on-line readability; Panel F faint `F_Maxwell` baseline) are intentional iconic choices but cap journal-grade impact — this matches the rubric warning against treating `pass` as "above ordinary manuscript quality".
  - `next_quality_bottleneck: polish` is a concrete next-loop target (it names a real on-figure region — Panel D labels and Panel F arrow contrast — not a generic axis).
  - Assessment did not imply monotonic progress from the prior critique (which itself was schema v1.2 but pre-Issue 9A and therefore had no `journal_grade_assessment`); fresh re-audit started from the current build artifact rather than inheriting prior pass states.
  - `/fig_loop` ingestion preserved every field; `/fig_driver` correctly held the workflow at `release_blocked` because of the orthogonal `force_golden_required` stop boundary, which is a separate gate from the fresh-re-audit assessment and was not auto-cleared by a passing assessment — this is the safer behavior.

### Run 2 — `golden_trap_depth_picture`

- **fixture name:** `golden_trap_depth_picture`
- **command sequence actually used:**
  ```bash
  uv run python3 scripts/fig_driver.py golden_trap_depth_picture --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  /fig_critique golden_trap_depth_picture                      # host vision; reads build PNG + figure-level reference (golden_target_001.png); writes v1.2 critique.md (replacing prior v1-schema critique) with journal_grade_assessment
  uv run python3 scripts/critique_adjudication.py scaffold golden_trap_depth_picture --force  # prior adjudication.yaml was a historical baseline+grounded-experiment record with non-v1 schema; --force required to refresh to the v1 scaffold against the new critique hash
  uv run python3 scripts/fig_loop.py golden_trap_depth_picture --goal "dogfood 9A fresh re-audit" --json
  uv run python3 scripts/fig_driver.py golden_trap_depth_picture --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  ```
- **critique schema:** `figure-agent.critique.v1.2`
- **`critique_input_hash`:** `sha256:a794641f2a9dd36468d704e2e7de8ca22e17bf6c3e1c9900bebe20aab9f04fba`
- **`journal_grade_assessment.assessed_artifact_hash`:** `sha256:a794641f2a9dd36468d704e2e7de8ca22e17bf6c3e1c9900bebe20aab9f04fba` (matches `critique_input_hash`)
- **`score_is_gateable`:** `true`
- **`benchmark_level`:** `solid_manuscript`
- **`confidence`:** `medium`
- **`next_quality_bottleneck`:** `polish`
- **`regression_detected`:** `false`
- **`regressions`:** `[]`
- **`/fig_loop` `stop_reason`:** `status_action_required`
- **`/fig_loop` surfaced `journal_grade_assessment.evaluation_state`:** `passed` (per `.scratch/fig-loop-runs/20260519-113420-191592-golden_trap_depth_picture/iteration_001.json`)
- **`/fig_driver` next action after loop ingestion:** `action: release_blocked`, `safe_command: null`, `stop_boundary: force_golden_required`, `loop_checkpoint.recommended_next_action: "tracked golden artifact is intentionally stale; to roll forward run /fig_export golden_trap_depth_picture --force-golden."`
- **reviewer verdict:** `useful`
- **rationale for verdict:**
  - Audit + quality-axis blocks fully filled; `journal_grade_assessment` is fresh (`assessed_artifact_hash == critique_input_hash`) and gateable.
  - All applicable axes pass yet the host did NOT promote to `high_impact_candidate`. The rationale names a concrete visible reason: the figure is a clean explanatory schematic but its visual register (gray row separators, single-purpose teal accent, Row 3 polymer chains lighter in visual mass than Row 1 plots and the right-side band diagram) does not read above ordinary manuscript quality. That is the level-only rubric working correctly — `pass` axes alone do not promote.
  - `next_quality_bottleneck: polish` points at a concrete next loop target (visual-weight balance between rows and polymer-chain rendering richness), not a generic axis.
  - The fresh re-audit verdict was generated against the current build hash rather than inheriting prior critique pass states. The prior critique.md on disk was schema v1, which means there is no prior v1.2 `journal_grade_assessment` to be inherited — the assessment had to be produced from scratch. This is exactly the failure mode Issue 9C wants to catch (a host LLM that re-uses an old verdict). The host correctly produced a fresh-eye level rather than carrying forward "iter 10 ready" framing.
  - `/fig_loop` ingestion preserved every field. `/fig_driver` correctly held the workflow at `release_blocked` — same pattern as Run 1, indicating the `force_golden_required` stop boundary is orthogonal to the fresh re-audit assessment regardless of fixture.
  - Cross-run signal worth noting: two fixtures, both `solid_manuscript` + `polish` bottleneck. If runs 3–5 also land on `solid_manuscript`, the level rubric is at risk of collapsing to a single value in practice and the `too_coarse` failure mode becomes a real concern.

### Run 3 — `smoke_trap_demo` (critique-not-required blocker)

- **fixture name:** `smoke_trap_demo`
- **command sequence actually used:**
  ```bash
  uv run python3 scripts/fig_driver.py smoke_trap_demo --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  # driver returned action: run_compile (render STALE), safe_command: bash scripts/compile.sh examples/smoke_trap_demo/smoke_trap_demo.tex
  bash scripts/compile.sh examples/smoke_trap_demo/smoke_trap_demo.tex
  uv run python3 scripts/fig_driver.py smoke_trap_demo --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  # driver returned action: run_fig_loop (critique NOT_REQUIRED — spec.yaml declares no reference_image), safe_command: uv run python3 scripts/fig_loop.py smoke_trap_demo --goal 'dogfood 9A fresh re-audit' --json
  uv run python3 scripts/fig_loop.py smoke_trap_demo --goal "dogfood 9A fresh re-audit" --json
  uv run python3 scripts/fig_driver.py smoke_trap_demo --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  ```
  `critique_adjudication.py scaffold` was NOT run for this fixture because no critique was produced; scaffolding without a critique would be a fabricated artifact.
- **critique schema:** none (no critique.md written; no critique.md present in the fixture directory at any point)
- **why critique was not produced:** `examples/smoke_trap_demo/spec.yaml` declares no `reference_image` and no `panels[].reference_image`. The driver therefore reports `critique_state: NOT_REQUIRED` rather than `STALE`, and `/fig_critique` has no reference-grounding to bind to. Per Issue 9C "If a fixture cannot produce a v1.2 critique because it lacks required visual or reference inputs, record the blocker instead of substituting a synthetic case," this run is recorded as a blocker rather than an invented critique.
- **`critique_input_hash`:** N/A (no critique)
- **`journal_grade_assessment.assessed_artifact_hash`:** N/A (no assessment)
- **`score_is_gateable`:** N/A
- **`benchmark_level`:** N/A
- **`confidence`:** N/A
- **`next_quality_bottleneck`:** N/A
- **`regression_detected`:** N/A
- **`regressions`:** N/A
- **`/fig_loop` `stop_reason`:** `status_action_required`
- **`/fig_loop` surfaced `journal_grade_assessment.evaluation_state`:** N/A (`journal_grade_assessment` is `null` in the iteration record because the critique source is `NOT_REQUIRED` — confirmed at `.scratch/fig-loop-runs/20260519-114125-424872-smoke_trap_demo/iteration_001.json`)
- **`/fig_loop` `escalation_level`:** `agent_action_required` (distinct from runs 1–2 which were `manual_approval_required`; this fixture has no golden contract gate, so the export stale-state is an agent-actionable signal rather than a human gate)
- **`/fig_driver` next action after loop ingestion:** `action: run_fig_loop`, `safe_command: uv run python3 scripts/fig_loop.py smoke_trap_demo --goal 'dogfood 9A fresh re-audit' --json`, `stop_boundary: null`. The driver does NOT escalate to `release_blocked` for this fixture because `acceptance_state: NOT_DECLARED` (no `golden_contract`), so the only structural blocker is the stale export that `/fig_export` would close in a separate workflow surface.
- **reviewer verdict:** `invalid` (for the journal-grade fresh re-audit purpose of Issue 9C — no `journal_grade_assessment` field could be exercised against this fixture)
- **short rationale:**
  - The fixture is a smoke-test placeholder (`selected_preview: dummy_v1.png` in spec.yaml; `selection_notes` describe it as a band-diagram cartoon stub). It deliberately does not carry the reference grounding that `/fig_critique` v1.2 needs, so the journal-grade fresh re-audit rubric cannot be evaluated here.
  - Marking the run `useful` or `too_coarse` would mis-claim that a journal_grade_assessment was produced; marking it `confusing` would suggest a host-LLM failure mode that does not apply. `invalid` is the honest reading: the assessment field was not produced, so the rubric cannot be tested against this run, and the fixture is not a counter-example against the rubric either.
  - The blocker is structural (fixture contract gap), not a defect in the v1.2 critique pipeline or the journal_grade_assessment design. If Issue 9C requires N≥5 v1.2 critique-grounded fixtures, this run does not count toward that quorum; a substitute fixture from the remaining queue is needed.

## Open Items

- Runs 4–5 not yet executed against the published queue (`fig3_trapping_concept`, `fig5_floating_clip_mechanism`).
- Quorum gap: 2 valid v1.2 critique-grounded runs vs. the Issue 9C minimum of 5. If the remaining queue also lacks reference grounding, Issue 9C will need either fixture-grounding work or an Issue 9C exception note for sub-N=5 evidence acceptance — recorded here so the gap is visible.
- Watchlist (carryover from Run 2): does any fixture land at `draft`, `high_impact_candidate`, `needs_human_art_direction`, or `blocked`? Two `solid_manuscript` + `polish` outcomes so far; level coverage remains narrow.
- Note for the cross-run pattern: a fresh `journal_grade_assessment` does NOT clear the orthogonal `force_golden_required` stop boundary (Runs 1–2). For fixtures without a `golden_contract` (Run 3), the driver lands on `agent_action_required` for stale exports rather than `manual_approval_required` — the gate set is fixture-shape dependent.
