# Fresh Re-Audit Dogfood Evidence (Issue 9C)

**Date opened:** 2026-05-19 KST
**Parent issue:** `docs/superpowers/issues/2026-05-19-issue-9c-fresh-reaudit-dogfood-evidence.md`
**Status:** queue closed (5/5 fixtures attempted; 2 valid v1.2 runs + 3 critique-not-required blockers; Issue 9C N=5 quorum NOT met)

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

### Run 4 — `fig3_trapping_concept` (critique-not-required blocker)

- **fixture name:** `fig3_trapping_concept`
- **command sequence actually used:**
  ```bash
  uv run python3 scripts/fig_driver.py fig3_trapping_concept --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  # driver returned action: run_compile (render STALE), safe_command: bash scripts/compile.sh examples/fig3_trapping_concept/fig3_trapping_concept.tex
  bash scripts/compile.sh examples/fig3_trapping_concept/fig3_trapping_concept.tex
  uv run python3 scripts/fig_driver.py fig3_trapping_concept --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  # driver returned action: run_fig_loop, critique_state: NOT_REQUIRED (spec.yaml declares no reference_image; selected_preview is null)
  uv run python3 scripts/fig_loop.py fig3_trapping_concept --goal "dogfood 9A fresh re-audit" --json
  uv run python3 scripts/fig_driver.py fig3_trapping_concept --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  ```
  `critique_adjudication.py scaffold` was NOT run for this fixture (no critique to scaffold against).
- **critique schema:** none (no critique.md written and none present in the fixture directory)
- **why critique was not produced:** `examples/fig3_trapping_concept/spec.yaml` declares no `reference_image`, no `panels[].reference_image`, no `panels[].bbox_pdf_cm`, and `selected_preview: null`. The driver therefore reports `critique_state: NOT_REQUIRED`; `/fig_critique` has no reference grounding to bind to. Per Issue 9C the blocker is recorded honestly instead of forcing a synthetic critique.
- **`critique_input_hash`:** N/A
- **`journal_grade_assessment.assessed_artifact_hash`:** N/A
- **`score_is_gateable`:** N/A
- **`benchmark_level`:** N/A
- **`confidence`:** N/A
- **`next_quality_bottleneck`:** N/A
- **`regression_detected`:** N/A
- **`regressions`:** N/A
- **`/fig_loop` `stop_reason`:** `status_action_required`
- **`/fig_loop` surfaced `journal_grade_assessment.evaluation_state`:** N/A (`journal_grade_assessment` is `null` in iteration record — confirmed at `.scratch/fig-loop-runs/20260519-115303-371997-fig3_trapping_concept/iteration_001.json`)
- **`/fig_loop` `escalation_level`:** `agent_action_required` (same shape as Run 3 — stale-export agent-actionable, no golden contract human gate)
- **`/fig_driver` next action after loop ingestion:** `action: run_fig_loop`, `safe_command: uv run python3 scripts/fig_loop.py fig3_trapping_concept --goal 'dogfood 9A fresh re-audit' --json`, `stop_boundary: null`.
- **reviewer verdict:** `invalid` (for the journal-grade fresh re-audit purpose of Issue 9C — no `journal_grade_assessment` field could be exercised)
- **short rationale:**
  - Same structural blocker shape as Run 3: the fixture's spec.yaml never declared a `reference_image`, so `/fig_critique` is `NOT_REQUIRED` rather than `STALE`. The journal-grade fresh re-audit rubric cannot be evaluated against this fixture.
  - Marking `useful/too_coarse/confusing` would mis-claim that a journal_grade_assessment was produced. `invalid` is the honest reading and is not a defect signal against the rubric or the v1.2 pipeline — it is a fixture-contract gap.
  - The remaining iteration also exposes that the fig3 build has 14 visual clash candidates (logged by `scripts/check_visual_clash.py` during compile). These are real authoring polish items but do not factor into the fresh-re-audit assessment because that field has no critique to feed it.
- **strengthens the quorum gap from Run 3:** **yes.** Two of the three originally-queued non-golden fixtures (`smoke_trap_demo`, `fig3_trapping_concept`) cannot exercise the v1.2 critique surface. Quorum gap is now structural rather than incidental.

### Run 5 — `fig5_floating_clip_mechanism` (critique-not-required blocker)

- **fixture name:** `fig5_floating_clip_mechanism`
- **command sequence actually used:**
  ```bash
  uv run python3 scripts/fig_driver.py fig5_floating_clip_mechanism --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  # action: run_compile (render STALE, export MISSING), safe_command: bash scripts/compile.sh examples/fig5_floating_clip_mechanism/fig5_floating_clip_mechanism.tex
  bash scripts/compile.sh examples/fig5_floating_clip_mechanism/fig5_floating_clip_mechanism.tex
  uv run python3 scripts/fig_driver.py fig5_floating_clip_mechanism --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  # action: run_fig_loop, critique_state: NOT_REQUIRED (spec.yaml declares panel bboxes only; no figure-level or per-panel reference_image)
  uv run python3 scripts/fig_loop.py fig5_floating_clip_mechanism --goal "dogfood 9A fresh re-audit" --json
  uv run python3 scripts/fig_driver.py fig5_floating_clip_mechanism --mode review --goal "dogfood 9A fresh re-audit" --dry-run
  ```
  `critique_adjudication.py scaffold` was NOT run for this fixture (no critique).
- **critique schema:** none (no critique.md written and none present in the fixture directory)
- **why critique was not produced:** `examples/fig5_floating_clip_mechanism/spec.yaml` declares panel `bbox_pdf_cm` for A and B but no `reference_image` at figure level and no `panels[].reference_image`. The driver therefore reports `critique_state: NOT_REQUIRED` and `/fig_critique` has no reference grounding to bind to. Same structural shape as Runs 3 and 4.
- **`critique_input_hash`:** N/A
- **`journal_grade_assessment.assessed_artifact_hash`:** N/A
- **`score_is_gateable`:** N/A
- **`benchmark_level`:** N/A
- **`confidence`:** N/A
- **`next_quality_bottleneck`:** N/A
- **`regression_detected`:** N/A
- **`regressions`:** N/A
- **`/fig_loop` `stop_reason`:** `status_action_required`
- **`/fig_loop` surfaced `journal_grade_assessment.evaluation_state`:** N/A (`journal_grade_assessment` is `null` in iteration record at `.scratch/fig-loop-runs/20260519-120014-049340-fig5_floating_clip_mechanism/iteration_001.json`)
- **`/fig_loop` `escalation_level`:** `agent_action_required` (same shape as Runs 3–4; no golden contract gate)
- **`/fig_loop` `recommended_next_action`:** `run /fig_critique fig5_floating_clip_mechanism for vision review (optional), then /fig_export fig5_floating_clip_mechanism.` (loop suggests critique as *optional* because no reference grounding makes critique non-actionable for v1.2; treated as informational, not a blocker)
- **`/fig_driver` next action after loop ingestion:** `action: run_fig_loop`, `safe_command: uv run python3 scripts/fig_loop.py fig5_floating_clip_mechanism --goal 'dogfood 9A fresh re-audit' --json`, `stop_boundary: null`.
- **reviewer verdict:** `invalid` (for Issue 9C purpose — no `journal_grade_assessment` could be exercised)
- **short rationale:**
  - Third consecutive critique-not-required outcome. The fixture has panel bbox declarations (A: 7-phase voltage waveform timeline; B: geometry + force diagram) but never declared reference imagery, so the v1.2 critique surface does not engage.
  - Compile produced 41 visual-clash candidates (report-only); these are real authoring polish items, but they do not feed the journal-grade fresh re-audit field because no critique is produced.
  - `invalid` is again the honest reading — not a rubric defect or a host-LLM failure mode.
- **strengthens the quorum gap:** **yes — final.** Three of the five published queue fixtures (`smoke_trap_demo`, `fig3_trapping_concept`, `fig5_floating_clip_mechanism`) are structurally critique-not-required. Only the two fixtures with declared reference imagery (`fig1_overview_v2_pair_001_vault`, `golden_trap_depth_picture`) produced valid v1.2 evidence.

## Issue 9C Final Quorum Judgment (5 attempted fixtures, 2026-05-19)

- **Valid v1.2 critique-grounded runs:** 2 (`fig1_overview_v2_pair_001_vault`, `golden_trap_depth_picture`).
- **Critique-not-required blockers:** 3 (`smoke_trap_demo`, `fig3_trapping_concept`, `fig5_floating_clip_mechanism`).
- **Issue 9C N=5 quorum:** NOT met. The published queue cannot reach N=5 because three of its five fixtures lack the spec-level `reference_image` that v1.2 critique requires.
- **Issue 9B status:** remains **blocked**. Issue 9C Acceptance Criteria require "At least five real fixture runs are recorded" with valid v1.2 evidence before Issue 9B numeric scoring is opened. That bar is not yet cleared.
- **Recommended follow-up:**
  1. **Substitute fixtures (preferred).** Identify two more real fixtures in `examples/` that already declare a `reference_image` and re-run the dogfood loop on them. This preserves the Issue 9C measurement intent (real failure modes, not synthetic cases) and meets N=5 without changing what is being measured.
  2. **Add reference grounding to existing fixtures (not preferred).** Authoring reference imagery for `smoke_trap_demo` / `fig3_trapping_concept` / `fig5_floating_clip_mechanism` would change those fixtures to satisfy the critique contract, but that is fixture-authoring work rather than rubric measurement; if used, it should be a separate follow-up issue.
  3. **Issue 9C exception for sub-N=5 acceptance (last resort).** Accept the two-run evidence on the strength of the recorded blocker artifact (this document), with a written note that the rubric was not exercised against the originally planned fixture diversity. Only viable if substitute fixtures cannot be found.
- **Rubric-evidence summary (level-only fresh re-audit):**
  - Both valid runs landed at `solid_manuscript` + `next_quality_bottleneck: polish`. The rubric did not silently promote either fixture despite all upstream axes being `pass` — i.e., the "above ordinary manuscript quality" guard against `high_impact_candidate` worked.
  - Neither run flagged `regression_detected: true`; both gateable hashes matched their `critique_input_hash`.
  - **`too_coarse` risk surfaced but not yet confirmed.** Two `solid_manuscript` runs on two structurally different fixtures is too small a sample to call the level set narrow. The same outcome on a wider fixture set (e.g., a substitute that should plausibly be `draft` or one that should plausibly be `needs_human_art_direction`) would test the rubric better than re-running on the same two figures.
- **Pattern-level findings worth carrying into Issue 9B/9D:**
  - `force_golden_required` is orthogonal to the fresh re-audit assessment. A fresh `solid_manuscript` does not unlock golden roll-forward (Runs 1–2).
  - Gate set is fixture-shape dependent: golden-contract fixtures end at `manual_approval_required`; non-golden fixtures end at `agent_action_required`. Surface this in Issue 9B numeric scoring so the score-gate logic does not assume a single escalation shape.
  - Critique-not-required fixtures still produce `/fig_loop` iteration records with `journal_grade_assessment: null`. Downstream consumers must handle the null cleanly; do not assume every fixture has an assessment.

## Open Items

- **PRIMARY:** decide between the three follow-up options above before opening Issue 9B. Recommendation: option (1) substitute fixtures.
- Watchlist: level-set width remains untested. Even with two more reference-grounded runs, the rubric will only be falsifiable if at least one run lands outside `solid_manuscript`.
- Cross-run pattern (still useful): gate set is fixture-shape dependent. Two distinct end states observed (`force_golden_required` for Runs 1–2; `agent_action_required` for Runs 3–5).
