# Fresh Re-Audit Dogfood Evidence (Issue 9C)

**Date opened:** 2026-05-19 KST
**Parent issue:** `docs/superpowers/issues/2026-05-19-issue-9c-fresh-reaudit-dogfood-evidence.md`
**Status:** N=5 quorum MET (5 valid v1.2 critique-grounded runs after substitute pass; 3 published-queue blockers retained as honest evidence; Issue 9B unblocked)

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

## Substitute Pass (fixtures with declared reference grounding, 2026-05-19 PM)

Three real fixtures in `examples/` already declared `reference_image` and had not yet been run in the dogfood pass. Picking these substitutes preserves Issue 9C's measurement intent (real failure modes, not synthetic cases) and does not require fixture-authoring work.

### Run S1 — `fig1_overview_v2` (valid v1.2 substitute)

- **fixture name:** `fig1_overview_v2`
- **eligibility:** `examples/fig1_overview_v2/spec.yaml` declares `reference_image: reference/codex_gen_overview_v1.png`; reference file present and fresh.
- **command sequence actually used:**
  ```bash
  uv run python3 scripts/fig_driver.py fig1_overview_v2 --mode review --goal "dogfood 9A fresh re-audit substitute" --dry-run
  # action: run_compile (render STALE, critique STALE)
  bash scripts/compile.sh examples/fig1_overview_v2/fig1_overview_v2.tex
  uv run python3 scripts/fig_driver.py fig1_overview_v2 --mode review --goal "dogfood 9A fresh re-audit substitute" --dry-run
  # action: run_critique, safe_command: /fig_critique fig1_overview_v2
  /fig_critique fig1_overview_v2                                                       # host vision writes v1.2 critique.md
  uv run python3 scripts/critique_adjudication.py scaffold fig1_overview_v2 --force
  uv run python3 scripts/fig_loop.py fig1_overview_v2 --goal "dogfood 9A fresh re-audit substitute" --json
  uv run python3 scripts/fig_driver.py fig1_overview_v2 --mode review --goal "dogfood 9A fresh re-audit substitute" --dry-run
  ```
- **critique schema:** `figure-agent.critique.v1.2`
- **`critique_input_hash`:** `sha256:eef5193f0298b64c503391e6ea556425851f0ec9d4da5ac795d4220ba225bd77`
- **`journal_grade_assessment.assessed_artifact_hash`:** `sha256:eef5193f0298b64c503391e6ea556425851f0ec9d4da5ac795d4220ba225bd77` (matches)
- **`score_is_gateable`:** `true`
- **`benchmark_level`:** `draft`
- **`confidence`:** `medium`
- **`next_quality_bottleneck`:** `scientific_plausibility`
- **`regression_detected`:** `false`
- **`regressions`:** `[]`
- **`/fig_loop` `stop_reason`:** `human_gate_required`
- **`/fig_loop` `escalation_level`:** `human_review_required`
- **`/fig_loop` surfaced `journal_grade_assessment.evaluation_state`:** `passed` (per `.scratch/fig-loop-runs/20260519-121347-875399-fig1_overview_v2/iteration_001.json`)
- **`/fig_driver` next action after loop ingestion:** `action: human_gate_stop`, `safe_command: null`, `stop_boundary: human_gate_required`, `recommended_next_action: "human review required for F001"`.
- **reviewer verdict:** `useful`
- **rationale for verdict:**
  - All audit blocks + 10 quality_axes filled; `journal_grade_assessment` is fresh and gateable.
  - **First non-`solid_manuscript` level produced.** This is the critical rubric-falsification evidence Issue 9C needs: the level set is not collapsed to a single value. Three real findings (F001 MAJOR cross-panel palette inconsistency between briefing §2 and §3, F002 MINOR Row 1→Row 2 bridge weak, F003 MAJOR 45 visual-clash candidates) drove the assessment to `draft`.
  - `next_quality_bottleneck: scientific_plausibility` is correct: the color-convention bug lives in `briefing.md` rather than the .tex, so polishing labels (F003) before resolving F001 would lock in the wrong convention. The level-only rubric correctly identifies the upstream lever.
  - New gate shape observed: `human_review_required` / `human_gate_required` / `human_gate_stop`. This is a third escalation shape (alongside `manual_approval_required` for Runs 1–2 and `agent_action_required` for Runs 3–5 / S3). The fresh-re-audit assessment did not auto-clear this gate; the driver correctly held at `human_gate_stop` until the F001 adjudication is reviewed.
- **counts toward valid quorum:** yes.

### Run S2 — `n3_trial_01_trap_depth` (valid v1.2 substitute)

- **fixture name:** `n3_trial_01_trap_depth`
- **eligibility:** `examples/n3_trial_01_trap_depth/spec.yaml` declares `reference_image: reference/codex_gen_v1.png`; reference file present.
- **command sequence actually used:**
  ```bash
  uv run python3 scripts/fig_driver.py n3_trial_01_trap_depth --mode review --goal "dogfood 9A fresh re-audit substitute" --dry-run
  # action: run_compile
  bash scripts/compile.sh examples/n3_trial_01_trap_depth/n3_trial_01_trap_depth.tex
  uv run python3 scripts/fig_driver.py n3_trial_01_trap_depth --mode review --goal "dogfood 9A fresh re-audit substitute" --dry-run
  # action: run_critique, safe_command: /fig_critique n3_trial_01_trap_depth
  /fig_critique n3_trial_01_trap_depth                                                 # host vision writes v1.2 critique.md (replacing prior v1 critique)
  uv run python3 scripts/critique_adjudication.py scaffold n3_trial_01_trap_depth --force
  uv run python3 scripts/fig_loop.py n3_trial_01_trap_depth --goal "dogfood 9A fresh re-audit substitute" --json
  uv run python3 scripts/fig_driver.py n3_trial_01_trap_depth --mode review --goal "dogfood 9A fresh re-audit substitute" --dry-run
  ```
- **critique schema:** `figure-agent.critique.v1.2`
- **`critique_input_hash`:** `sha256:fdf8612825c2b1aae34fed682a1db8f20299e854c9d40b9b769f3a3cb4a2df01`
- **`journal_grade_assessment.assessed_artifact_hash`:** `sha256:fdf8612825c2b1aae34fed682a1db8f20299e854c9d40b9b769f3a3cb4a2df01` (matches)
- **`score_is_gateable`:** `true`
- **`benchmark_level`:** `draft`
- **`confidence`:** `high`
- **`next_quality_bottleneck`:** `component_fidelity`
- **`regression_detected`:** `false`
- **`regressions`:** `[]`
- **`/fig_loop` `stop_reason`:** `human_gate_required`
- **`/fig_loop` `escalation_level`:** `human_review_required`
- **`/fig_loop` surfaced `journal_grade_assessment.evaluation_state`:** `passed` (per `.scratch/fig-loop-runs/20260519-121708-842425-n3_trial_01_trap_depth/iteration_001.json`)
- **`/fig_driver` next action after loop ingestion:** `action: human_gate_stop`, `stop_boundary: human_gate_required`, `recommended_next_action: "human review required for F001"`.
- **reviewer verdict:** `useful`
- **rationale for verdict:**
  - Second `draft`-level assessment, on a different fixture, with a *different* `next_quality_bottleneck` (`component_fidelity` rather than `scientific_plausibility`). The rubric distinguishes between two real failure modes — color-convention upstream defect (S1) vs polymer-chain rendering defect (S2) — using only the level + bottleneck pair.
  - **BLOCKER finding F001 (Row 3 polymer chain is a featureless wavy line) is the same anti-pattern that sibling fixture `golden_trap_depth_picture` recorded as G001 BLOCKER in its v0.2 baseline.** The host-LLM critique caught the same defect that the prior adjudication framework caught — independent verification of the rubric's blocker-detection signal.
  - `score_is_gateable: true` despite a BLOCKER finding because severity gating is finding-level, not assessment-level. The level rubric correctly treats BLOCKER as "fix this before promotion" rather than "field is invalid".
- **counts toward valid quorum:** yes.

### Run S3 — `n3_trial_02_actuation_sequence` (valid v1.2 substitute)

- **fixture name:** `n3_trial_02_actuation_sequence`
- **eligibility:** `examples/n3_trial_02_actuation_sequence/spec.yaml` declares `reference_image: reference/codex_gen_v1.png`; reference file present; no prior critique on disk.
- **command sequence actually used:**
  ```bash
  uv run python3 scripts/fig_driver.py n3_trial_02_actuation_sequence --mode review --goal "dogfood 9A fresh re-audit substitute" --dry-run
  # action: run_compile (render STALE, critique MISSING)
  bash scripts/compile.sh examples/n3_trial_02_actuation_sequence/n3_trial_02_actuation_sequence.tex
  uv run python3 scripts/fig_driver.py n3_trial_02_actuation_sequence --mode review --goal "dogfood 9A fresh re-audit substitute" --dry-run
  # action: run_critique, safe_command: /fig_critique n3_trial_02_actuation_sequence
  /fig_critique n3_trial_02_actuation_sequence                                         # host vision writes v1.2 critique.md from scratch (no prior file)
  uv run python3 scripts/critique_adjudication.py scaffold n3_trial_02_actuation_sequence --force
  uv run python3 scripts/fig_loop.py n3_trial_02_actuation_sequence --goal "dogfood 9A fresh re-audit substitute" --json
  uv run python3 scripts/fig_driver.py n3_trial_02_actuation_sequence --mode review --goal "dogfood 9A fresh re-audit substitute" --dry-run
  ```
- **critique schema:** `figure-agent.critique.v1.2`
- **`critique_input_hash`:** `sha256:89c9593862f8997911462db8107621623e25f504e55aecd88e68ea9d882fe7ae`
- **`journal_grade_assessment.assessed_artifact_hash`:** `sha256:89c9593862f8997911462db8107621623e25f504e55aecd88e68ea9d882fe7ae` (matches)
- **`score_is_gateable`:** `true`
- **`benchmark_level`:** `solid_manuscript`
- **`confidence`:** `medium`
- **`next_quality_bottleneck`:** `polish`
- **`regression_detected`:** `false`
- **`regressions`:** `[]`
- **`/fig_loop` `stop_reason`:** `status_action_required`
- **`/fig_loop` `escalation_level`:** `agent_action_required`
- **`/fig_loop` surfaced `journal_grade_assessment.evaluation_state`:** `passed` (per `.scratch/fig-loop-runs/20260519-121948-905577-n3_trial_02_actuation_sequence/iteration_001.json`)
- **`/fig_driver` next action after loop ingestion:** `action: run_fig_loop`, `safe_command: uv run python3 scripts/fig_loop.py n3_trial_02_actuation_sequence --goal 'dogfood 9A fresh re-audit substitute' --json`, `stop_boundary: null`.
- **reviewer verdict:** `useful`
- **rationale for verdict:**
  - Clean three-phase actuation sequence (Charge Injection / Coulomb Repulsion / Relaxation) with all physics invariants honored and reference fidelity high; the v1.2 critique surfaces zero findings.
  - All upstream axes `pass`, yet host did NOT auto-promote to `high_impact_candidate`. Rationale names two concrete polish levers (e^- charge-rendering style and explicit phase index), so the level rubric correctly identifies that "all pass" does not equal "above ordinary manuscript quality".
  - This is the **third `solid_manuscript`** outcome but with the highest visual fidelity of the three solid_manuscript runs — confirms the level can absorb non-trivial quality variation without auto-promoting and without falsely escalating to higher levels.
- **counts toward valid quorum:** yes.

## Issue 9C Final Quorum Judgment (after substitute pass, 2026-05-19 PM)

- **Total attempted fixtures:** 8 (5 published queue + 3 substitutes).
- **Valid v1.2 critique-grounded runs:** **5** (`fig1_overview_v2_pair_001_vault`, `golden_trap_depth_picture`, `fig1_overview_v2`, `n3_trial_01_trap_depth`, `n3_trial_02_actuation_sequence`). **N=5 quorum MET.**
- **Invalid / blocker runs (critique-not-required):** 3 (`smoke_trap_demo`, `fig3_trapping_concept`, `fig5_floating_clip_mechanism`) — retained as honest evidence of fixture-contract gaps rather than substituted-away.
- **Issue 9B status:** **UNBLOCKED.** The Issue 9C Acceptance Criteria minimum of "at least five real fixture runs are recorded" with valid v1.2 evidence is now satisfied (5/5), and every valid run records both a fresh-gateable journal_grade_assessment outcome and a captured `/fig_loop` ingestion + `/fig_driver` next-action.
- **Numeric scoring (Issue 9B) can proceed** with the following calibration evidence pulled from these 5 runs:
  - Level coverage observed: `draft` (2) + `solid_manuscript` (3). Levels not yet exercised on real fixtures: `high_impact_candidate`, `needs_human_art_direction`, `blocked`.
  - Bottleneck coverage observed: `polish` (3), `scientific_plausibility` (1), `component_fidelity` (1). Bottlenecks not yet exercised: `storyline`, `composition`, `label_semantics`, `reference_fidelity`, `export_scale_readability`, `human_policy`.
  - Score-is-gateable rate: 5/5 = 100%. Every valid critique had `assessed_artifact_hash == critique_input_hash`.
  - Regression-detection rate: 0/5. No fixture had a prior gateable assessment to regress against; this should be re-checked after Issue 9B numeric scoring adds a comparable score history.
- **Rubric falsifiability evidence:**
  - Two `draft` outcomes on distinct fixtures with distinct bottlenecks (S1 → `scientific_plausibility`, S2 → `component_fidelity`) confirm the level set is not collapsed and the bottleneck enum distinguishes structurally different failure modes.
  - Three `solid_manuscript` outcomes on distinct fixtures all rationalized their non-promotion to `high_impact_candidate` against concrete polish ceilings — the "above ordinary manuscript quality" guard is functioning.
  - BLOCKER finding in S2 was the same anti-pattern as sibling fixture `golden_trap_depth_picture`'s recorded G001 — independent verification of the rubric's blocker detection.
- **Pattern-level findings for Issue 9B/9D:**
  - **Three distinct end-state shapes** observed: `force_golden_required` (Runs 1–2, golden-contract fixtures with stale export), `agent_action_required` (Runs 3–5, S3 — non-golden fixtures with stale/missing export), and `human_gate_required` (S1, S2 — fixtures whose adjudication still has `needs_human` decisions on real findings). Issue 9B numeric scoring must not assume a single escalation shape.
  - The fresh `journal_grade_assessment` field is orthogonal to every one of those gates. A passing assessment does not unblock golden roll-forward, export refresh, or adjudication-pending human review.
  - Critique-not-required fixtures still produce loop iteration records with `journal_grade_assessment: null`. Downstream Issue 9B consumers must handle the null cleanly.
- **Recommended Issue 9C Acceptance Criteria status:**
  - [x] At least five real fixture runs are recorded.
  - [x] Each recorded run uses a host-authored v1.2 `critique.md` (5 valid) or records why v1.2 critique could not be produced (3 blockers, honestly documented above).
  - [x] Every valid run records a fresh/gateable `journal_grade_assessment` outcome.
  - [x] `/fig_loop` ingestion behavior captured for every valid run.
  - [x] `/fig_driver` next action after loop ingestion captured for every valid run.
  - [x] Every run has a reviewer verdict.
  - [/] Validation/ingestion defects: none surfaced during these 8 runs. No follow-up issue needed yet.
  - [x] Issue 9B remains deferred per Issue 9C control — and is now positioned to be opened with the calibration evidence above.

## Open Items

- **For Issue 9B:** plan numeric scoring with awareness that `high_impact_candidate`, `needs_human_art_direction`, and `blocked` have not yet been exercised on real fixtures; calibration should not anchor on the 5 currently-recorded levels alone.
- **For Issue 9D (or follow-up):** decide whether to add reference grounding to the 3 published-queue blockers (`smoke_trap_demo`, `fig3_trapping_concept`, `fig5_floating_clip_mechanism`) so the journal_grade_assessment surface can exercise them, or accept them as critique-not-required by-design. Recorded blockers above are sufficient evidence for either decision.
- Cross-run pattern (carryover, now confirmed 3-way): gate set is fixture-shape dependent. Three distinct end states observed.
