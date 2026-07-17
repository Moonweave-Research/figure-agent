# Issue 100H/I - Schema Capability Matrix and Module Ownership Map

Status: completed on main in commit `d3ccf37`; merged by `200910c`

Type: maintainability, schema governance, module ownership

## Problem

The plugin has reached a size where the hard problem is no longer only adding
detectors or critique slots. The hard problem is knowing where a new contract
belongs.

Current inventory on 2026-06-01:

- `scripts/*.py`: 104
- `tests/test*.py`: 116
- `commands/*.md`: 15
- critique schema lineage: `figure-agent.critique.v1` through
  `figure-agent.critique.v1.17`

Without a map, agents can accidentally:

- add a schema field in `critique_brief.py` but forget
  `critique_schema_validator.py`;
- add an audit report but forget `audit_evidence_summary.py`;
- expose a driver state without updating `next_action_summary.py`;
- create another script for logic already owned by an existing module.

This issue is intentionally docs-only. It does not change runtime behavior.

## Schema Capability Matrix

### Critique Schema Lineage

| Schema | Main capability introduced | Primary producers | Primary validators | Primary consumers | Current policy |
|---|---|---|---|---|---|
| `figure-agent.critique.v1` | Legacy frontmatter + findings | historical `critique.md` | `critique_schema_validator.py` legacy path | `critique_adjudication.py`, status fallback | Parse only; do not author new critiques |
| `v1.1` | mandatory `audit_enumeration` | retired 2026-07-02 | `critique_schema_validator.py` retired-schema guard | none | Retired; re-run `/fig_critique` to emit `v1.10`, `v1.14`, or `v1.17` |
| `v1.2` | quality axes + `journal_grade_assessment` | retired 2026-07-02 | `critique_schema_validator.py` retired-schema guard | none | Retired; capability retained in live `v1.10+` contracts |
| `v1.3` | top-tier journal audit | retired 2026-07-02 | `critique_schema_validator.py` retired-schema guard | none | Retired; capability retained in live `v1.10+` contracts |
| `v1.4` | high-zoom/print micro-defect accounting expansion | retired 2026-07-02 | `critique_schema_validator.py` retired-schema guard | none | Retired; capability retained in live `v1.10+` contracts |
| `v1.5` | editorial art-direction audit | retired 2026-07-02 | `critique_schema_validator.py` retired-schema guard | none | Retired; capability retained in live `v1.10+` contracts |
| `v1.6` | SVG-polish route semantics begin | retired 2026-07-02 | `critique_schema_validator.py` retired-schema guard | none | Retired; SVG polish remains handoff-only route language |
| `v1.7` | visual-clash candidate accounting | retired 2026-07-02 | `critique_schema_validator.py` retired-schema guard | none | Retired; capability retained in live `v1.10+` contracts |
| `v1.8` | crop-read accountability via audit crop manifest | retired 2026-07-02 | `critique_schema_validator.py` retired-schema guard | none | Retired; capability retained in live `v1.10+` contracts |
| `v1.9` | print/zoom grounded micro-defect hardening | retired 2026-07-02 | `critique_schema_validator.py` retired-schema guard | none | Retired; capability retained in live `v1.10+` contracts |
| `v1.10` | mature default critique contract | `critique_brief.py` | `critique_schema_validator.py`, `critique_lint.py` | `quality_manifest.py`, `fig_loop.py` | Default for non-grounded current critiques |
| `v1.11` | aesthetic lever grammar audit | retired 2026-07-02 | `critique_schema_validator.py` retired-schema guard | none | Retired; optional audit retained in live `v1.14+` contracts |
| `v1.12` | journal art-direction playbook audit | retired 2026-07-02 | `critique_schema_validator.py` retired-schema guard | none | Retired; optional audit retained in live `v1.14+` contracts |
| `v1.13` | reference learning accountability | retired 2026-07-02 | `critique_schema_validator.py` retired-schema guard | none | Retired; crop anomaly/accountability retained in live `v1.14+` contracts |
| `v1.14` | route-detail contract and richer aesthetic intent | `critique_brief.py` | `critique_lint.py`, `quality_manifest.py` | `fig_driver.py`, `fig_loop.py` | Route-specific rationale required |
| `v1.15` | retired SVG polish gate/delta hardening | retired 2026-07-02 | retired 2026-07-02 | retired 2026-07-02 | Superseded by external handoff-only route labels |
| `v1.16` | retired SVG polish delta audit | retired 2026-07-02 | retired 2026-07-02 | retired 2026-07-02 | Superseded by external handoff-only route labels |
| `v1.17` | grounded observation and anomaly accountability | `critique_zoom_crops.py`, `check_undeclared_geometry.py`, `critique_brief.py` | `critique_schema_validator.py`, `critique_lint.py`, `audit_evidence_summary.py` | `fig_loop_assessments.py`, `fig_driver.py` | Current grounded schema; new grounded fields should extend this |

### Non-Critique Schemas

| Schema | Owner | Producer | Validator/reader | Blocking authority |
|---|---|---|---|---|
| `figure-agent.audit-crop-manifest.v1` | audit evidence | `critique_zoom_crops.py` | `critique_lint.py`, `audit_evidence_summary.py` | Blocks critique evidence if required crops mismatch |
| `figure-agent.audit-evidence-summary.v1` | audit evidence | `audit_evidence_summary.py` | `status.py`, `fig_loop.py`, `fig_driver.py` | Advisory until state is `missing_input`, `needs_action`, or `stale_or_mismatched` |
| `figure-agent.audit-evidence-graph.v1` | audit evidence | `audit_evidence_graph.py` | operators, MCP resource metadata | Read-only provenance graph; never mutates fixture state |
| `figure-agent.initial-visual-review-request.v1` | outbound initial visual-review request | `closed_loop_initial_review.py` | `closed_loop_initial_review.py`, host workflow | Hash-bound authored source/render plus exact attempt-local full/panel/print crops; requests host review only and never invokes host, critique, adjudication, repair, or publication acceptance |
| `figure-agent.initial-visual-review-response.v1` | inbound initial visual-review response | `closed_loop_initial_review_response.py` | `closed_loop_initial_review_response.py` | Hash-binds the current outbound request, validated critique, host execution receipt, exact response pack, and ordered full-render plus six crop inspections; publishes only `critique_unadjudicated` and stops for human adjudication |
| `figure-agent.initial-human-adjudication.v1` | initial named-human decision | `closed_loop_initial_adjudication.py` | `closed_loop_initial_adjudication.py` | Exact current-state and response/critique/transcript binding; may reject terminally or create attribution-only handoff, never repair-bound |
| `figure-agent.initial-attribution-handoff.v1` | approved initial finding handoff | `closed_loop_initial_adjudication.py` | `closed_loop_initial_adjudication.py` | Deterministically carries selected validated findings, named human attributor, and explicit source-mutation prohibition |
| `figure-agent.initial-attribution-binding.v2` | attempt-local human selector binding | `closed_loop_initial_attribution_binding.py` | `closed_loop_initial_attribution_binding.py` | Requires current approved handoff, root source, exact selector/semantic references, and immutable snapshot; publishes `repair_bound` only; R4.13a compiles a separate same-attempt packet bundle |
| `figure-agent.attempt-local-repair-binding.v2` / `figure-agent.attempt-local-repair-packet.v1` | R4.13 attempt-local repair authority | `attempt_local_repair_binding.py`, `authoring_repair_packet.py` | packet compiler plus explicit candidate/authorization/materialization lifecycle | R4.13a revalidates initial request/response, adjudication handoff, v2 binding, root source/render, and exact six crops to create an immutable binding/packet/prompt/source sandbox. R4.13b accepts only explicit response/preview and named human authorization for the exact packet, preserves sandbox `repaired.tex`, writes only adjacent `materialized-repair.tex`, and stops strict success at human-or-host post-repair review; it invokes no model/host/review and claims no publication acceptance. |
| `figure-agent.visual-finding-artifacts.v1` | visual attribution review evidence | `visual_finding_artifacts.py` | operators, future review packets | Deterministic overlays/crops only; `review_evidence_only` and never publication acceptance |
| `figure-agent.three-way-blind-review.v3` | direct-SVG blinded review | `direct_svg_stage_review.py` | named human reviewers, `direct_svg_stage_review.py` replay/export | Public score inputs use seed-bound opaque commitments; exact file inventory rejects unbound files and diagnostics/machine gates cannot claim publication acceptance |
| `figure-agent.three-way-review-response.v2` | direct-SVG blinded response protocol | `direct_svg_stage_review.py` | `direct_svg_stage_review.py` response state machine | Scientific hard gate precedes visual scoring; borderline/disputed results require a distinct second named reviewer |
| `figure-agent.direct-svg-review-state.v4` | direct-SVG protected review state | `direct_svg_stage_review.py` | `direct_svg_stage_review.py` replay/advance/reveal/recovery | Stores fixed response hashes and transaction state; blocks unblinding until the finalized response validates |
| `figure-agent.private-three-way-review-key.v3` | direct-SVG protected blinding key | `direct_svg_stage_review.py` | locked replay, validated export, and post-finalization reveal only | External ignored 0700/0600 evidence; raw upstream hashes, seed, and assignments never enter the public distribution before reveal |
| `figure-agent.spine-evidence-summary.v1` | compile evidence spine | `status.py` | `fig_driver.py`, `fig_queue.py`, `fig_closeout.py`, operators | Read-only summary of compile-produced assertion, convention receipt, and grounding reports; report-only and does not create a new gate |
| `figure-agent.detector-feedback-ledger.v1` | detector tuning diagnostics | `detector_feedback_ledger.py` | operators | Read-only cross-fixture summary; no threshold or gate authority |
| `figure-agent.text-boundary-clash.v1` | deterministic detector | `check_text_boundary_clash.py` | `audit_evidence_summary.py`, `fig_closeout.py` | Can block closeout when stale/missing or malformed |
| `figure-agent.label-path-proximity.v1` | deterministic detector | `check_label_path_proximity.py` | `audit_evidence_summary.py`, `critique_brief.py` | Candidate evidence until critique/adjudication acts |
| `figure-agent.undeclared-geometry.v1` | deterministic detector | `check_undeclared_geometry.py` | `audit_evidence_summary.py`, `critique_brief.py` | Candidate evidence until critique/adjudication acts |
| `figure-agent.label-hyphenation.v1` | deterministic detector | `check_label_hyphenation.py` | `finding_source_attribution.py`, strict compile | WARN evidence with stable IDs; exact declared attribution may authorize a bounded repair, while strict mode remains a gate |
| `figure-agent.semantic-assertions.v1` | deterministic detector | `semantic_assertions.py` | none (report-only) | Report-only WARN; verifies spec-declared spatial relations (above/below/left/right) against rendered text geometry |
| `figure-agent.warning-budget.v1` | deterministic detector budget | `check_visual_clash_budget.py` | `fig_driver_guidance.py`, operators | Can route final mode to strict compile or human review when warnings exceed cap |
| `figure-agent.critique-adjudication.v1` | critique decision handoff | `critique_adjudication.py` (`scaffold`/`sync`) | `fig_loop_adjudication.py`, `fig_closeout.py` | Can create human gate, stale gate, or patch handoff |
| `figure-agent.adjudication-decision-diff.v1` | critique decision preservation | `critique_adjudication.py sync --preview` | operators | Read-only preview; does not write adjudication decisions |
| `figure-agent.journal-grade-assessment.v1` | critique sub-schema | `critique_brief_sections.py` | `critique_schema_validator.py`, `fig_loop_assessments.py` | Advisory score block; never overrides gates |
| `figure-agent.journal-art-direction-playbook-audit.v1` | critique sub-schema | `critique_brief.py` | `critique_schema_validator.py`, `critique_lint.py` | Requires anchored art-direction evidence |
| `figure-agent.top-tier-audit-summary.v1` | loop summary | `fig_loop_assessments.py` | `fig_driver.py`, `ready_improvement.py` | Can create human/art-direction stop before release |
| `figure-agent.fig-loop-run.v1` | loop record | `fig_loop.py` | `fig_driver.py`, `fig_closeout.py`, `fig_run_records.py` | Records latest loop state; freshness still comes from status |
| `figure-agent.patch-evidence.v1` / `figure-agent.post-patch-evidence.v1` | patch evidence | `fig_loop_patch_evidence.py` | `fig_loop.py`, `fig_driver.py` | Evidence only until closeout reruns live checks |
| `figure-agent.patch-apply.v1` | patch executor report | `fig_loop_patch_executor.py` | operators, tests | Must require explicit closeout before continuation |
| `figure-agent.driver.v1` | routing | `fig_driver.py` | `fig_run.py`, queue tools, operators | Advisory only; `may_execute` remains false |
| `figure-agent.run.v1` | bounded execution | `fig_run.py` | `fig_run_records.py`, `fig_run_journal.py` | Executes only allowlisted deterministic shell actions |
| `figure-agent.closeout.v1` | post-run closeout | `fig_closeout.py` | `fig_driver.py`, `next_action_summary.py` | Can block continuation until compile/critique/loop/export closeout is clean |
| `figure-agent.closeout-readiness.v1` | post-run closeout | `closeout_readiness.py` | operators, MCP closeout tools | Read-only readiness envelope; cannot accept golden/publication state |
| `figure-agent.fig-run-journal.v1` / `figure-agent.fig-run-journal-ref.v1` | run journal | `fig_run_records.py` | `fig_run_journal.py` | Non-authoritative; never replay |
| `figure-agent.fig-run-evidence-snapshot.v1` | run journal freshness | `fig_run_evidence.py`, `fig_run_records.py` | `fig_run_journal.py` | Non-authoritative content freshness check; never replay |
| `figure-agent.fig-run-journal-error.v1` | run journal error | `fig_run.py` | `fig_run_journal.py` | Diagnostic only; rerun live status/driver |
| `figure-agent.fig-run-journal-summary.v1` | run continuation UX | `fig_run_journal.py` | operators | Non-authoritative; points to live status/driver |
| `figure-agent.boundary-handoff.v1` | stop explanation | `fig_run.py`, `next_action_summary.py` | operators, outer agents | Explanation only, not a second router |
| `figure-agent.decision-boundary.v1` | advisory/blocking language | `next_action_summary.py`, `fig_driver_guidance.py` | command output, docs | Clarifies who may decide; does not execute |
| `figure-agent.next-action-summary.v1` | operator UX | `next_action_summary.py` | `fig_driver.py`, queue/run outputs | Explanation only; not a state owner |
| `figure-agent.next.v1` | agent state router | `agent_next.py` | `fig-agent next`, MCP next tool | Read-only envelope that wraps existing status and next-action policies; not a second router |
| `figure-agent.operator-guidance.v1` / `figure-agent.final-readiness.v1` | operator UX | `fig_driver_guidance.py` | command output | Guidance only; does not bypass status/export gates |
| `figure-agent.loop-basin.v1` | loop progress detection | `fig_loop_basin.py` | `fig_loop.py`, `fig_driver.py`, `fig_run.py` | Step-out advisory/handoff, not auto-patch |
| `figure-agent.improve.v1` | bounded improvement loop | `fig_improve.py` | operators | Runs bounded commands; stops at gates |
| `figure-agent.ready-improvement-summary.v1` / `figure-agent.marginal-return-summary.v1` | post-ready improvement discovery | `ready_improvement.py` | `fig_driver.py`, operators | Advisory; not acceptance |
| `figure-agent.fixture-driver-queue.v1` / `figure-agent.fixture-command-plan.v1` / `figure-agent.human-decision-packet.v1` / `figure-agent.queue-bottleneck-report.v1` / `figure-agent.queue-workspace-diagnostic.v1` | batch planning | `fig_queue.py` | operators, `fig_queue_run.py` | Must preserve per-fixture gates; bottleneck report is read-only live queue/status rollup; workspace diagnostic only explains missing examples discovery |
| `figure-agent.queue-run.v1` / `figure-agent.queue-operator-handoff.v1` | batch execution | `fig_queue_run.py`, `fig_queue.py` | operators | Must stop at human/closeout boundaries |
| `figure-agent.human-decision-packet.v1` / `figure-agent.release-decision-packet.v1` / `figure-agent.style-direction-packet.v1` / `figure-agent.design-direction-packet.v1` / `figure-agent.svg-polish-readiness-evidence.v1` / `figure-agent.human-decision-digest.v1` | human/release/style/design decision handoff | `fig_queue.py`, `design_direction_packet.py` | operators | Read-only recommendation and digest packets; source, SVG, accepted/golden/publication mutations remain explicit separate actions |
| `figure-agent.human-decision-record.v1` | human decision record | `human_decision_record.py`, `fig_queue.py` validation helper | operators, style comparison loader | Durable record only; style decisions stay distinct from release/golden mutation authority |
| `figure-agent.human-attestation.v1` | publication release gate | `human_attestation.py` | `publication_gate.py`, `status.py`, operators | Human-in-terminal HMAC attestation; required for accepted publication PASS and never stored with the repo-local signing key |
| `figure-agent.paper-figure-map.v1` | paper-plan consistency | `docs/paper_figure_map.yaml` | `check_plan_consistency.py`, operators | Machine-readable map for the canonical prose plan; does not replace the plan document |
| `figure-agent.plan-consistency.v1` | paper-plan consistency | `check_plan_consistency.py` | operators, `fig-agent plan-check` | Report-only fixture-plan drift signal; strict mode is opt-in |
| `figure-agent.editorial-redesign-packet.v1` | editorial redesign handoff | `editorial_redesign_packet.py` | operators, design-direction queue handoff | Read-only redesign brief; creates no source, accepted/golden, or publication mutation authority |
| `figure-agent.style-benchmark-candidate-pack.v1` / `figure-agent.style-benchmark-comparison-packet.v1` | style benchmark decisions | `style_benchmark_pack.py`, `style_benchmark_comparison.py` | `fig_queue.py`, operators | Read-only candidate/comparison evidence; editorial redesign and SVG polish remain handoff-only until separately approved |
| `figure-agent.e2e-smoke.v1` | deterministic smoke | `fig_e2e_smoke.py` | operators, CI | Deterministic gate only; not host-vision readiness |
| `figure-agent.svg-polish-readiness.v1` / `figure-agent.svg-polish-gate.v1` | SVG route/gate | `fig_driver_editorial.py` | `fig_driver.py`, `fig_loop.py` | Can route to SVG polish or semantic backport |
| `figure-agent.reference-aesthetic-metrics.v1` | numeric reference-class signal | `reference_aesthetic_metrics.py` | `critique_brief.py`, `critique_lint.py` | Advisory unless explicitly routed |
| `figure-agent.critique-reference-pack.v1.1` / `figure-agent.reference-learning.v1` | reference learning | `critique_reference_pack.py` | `quality_manifest.py`, `critique_brief.py`, `critique_lint.py` | Freshness input; not copy target |
| `figure-agent.aesthetic-intent.v1` / `figure-agent.aesthetic-intent.v2` | aesthetic direction | `aesthetic_intent.py` | `critique_brief.py`, `critique_lint.py`, `quality_manifest.py` | Grounding input; not acceptance |
| `figure-agent.paper-aesthetic-context.v1` | paper-wide consistency | `paper_aesthetic_context.py` | `critique_brief.py`, `critique_lint.py` | Requires explicit anchor citations |
| `figure-agent.journal-art-direction-playbook.v1` | target-journal style anchors | `journal_art_direction_playbook.py` | `critique_brief.py`, `critique_lint.py` | Requires exact anchor citations |
| `figure-agent.authoring-rules.v1` | source-anchored authoring rules | `authoring_rules.py` | `authoring_context_pack.py`, tests | N=1 hypotheses until transfer is validated |
| `figure-agent.semantic-contracts.v1` | opt-in semantic claims/invariants | `semantic_contracts.py` | `authoring_context_pack.py`, `critique_brief.py` | Narrow authoring/critique questions only; no automatic physics detection |
| `figure-agent.semantic-regions.v1` | opt-in visual-region/source declaration | `semantic_region_contract.py` | downstream visual finding attribution | Hash- and anchor-validated evidence only; ambiguous/unbound selectors cannot authorize source edits or publication claims |
| `figure-agent.narrative-context.v1` | read-only human-perspective context | `narrative_context.py` | `authoring_context_pack.py`, `critique_brief.py`, `candidate_review_packet.py`, `fig_loop.py` | Advisory reader-story context only; no model calls, prompt loops, rank scoring, source mutation, or autonomous patch selection |
| `figure-agent.authoring-context-pack.v1` | read-only authoring context | `authoring_context_pack.py` | `fig-agent context-pack`, MCP context-pack tool | Read-only durable context compilation; no model calls or generation executor |
| `figure-agent.convention-receipt.v1` | injected convention surfacing | `convention_receipt.py` | `compile.sh` (report-only `--write`), tests | Surfaces injected `use_as_constraint` rules with source quotes on every figure; report-only injection half, no render verification |
| `figure-agent.external-vision-review.v1` | optional second opinion | `external_vision_review.py` | `quality_manifest.py`, `critique_lint.py` | Evidence only unless routed through findings |
| `figure-agent.inspection-trace.v1` | host/subagent inspection trace | `inspection_trace.py` | `critique_lint.py`, operators | Optional auditability artifact; cannot prove image inspection by itself |
| `figure-agent.diagnostic-artifact-provenance.v1` | scratch/debug artifact safety | `diagnostic_artifact_provenance.py` | operators | Prevents stale diagnostics from becoming truth |
| `figure-agent.plugin-install-freshness.v1` | plugin install diagnostics | `plugin_install_freshness.py` | operators | Read-only source-vs-cache check; never mutates install state |
| `figure-agent.release-gate.v1` | package/release gate | `release_gate.py` | operators, CI | Builds and audits Cowork ZIP; skips missing host validators explicitly |
| `figure-agent.quality-defect-ledger.v1` | quality improvement loop | `quality_defect_ledger.py` | `quality_patch_plan.py`, MCP quality tools | Read-only defect ledger; no source mutation |
| `figure-agent.promotion-queue.v1` / `figure-agent.promotion-triage.v1` | G4 promotion wiring | `promotion_wiring.py`, `status.py` | `quality_defect_ledger.py`, `fig-agent promotion-queue`, `fig-agent triage`, `fig-agent status`, `fig-agent next` | `visual_clash` stays human-review queued; triage acceptance synthesizes bounded ledger fields with provenance, while status only exposes count/top-N |
| `figure-agent.tex-assertions.v1` | deterministic TeX assertion audit | `check_tex_assertions.py`, `promotion_wiring.py` | `quality_defect_ledger.py`, compile/export gates | Auto-promotable only because zero-match and multi-match fail loud; still deterministic declaration evidence, not visual or aesthetic judgment |
| `figure-agent.vector-clearance.v1` | deterministic declared vector geometry audit | `vector_clearance.py`, `promotion_wiring.py` | `quality_defect_ledger.py`, compile gate | Declaration-gated only; selector zero/multi-match fails loud; curve/circle/marker envelope violations remain non-auto-promotable |
| `figure-agent.quality-patch-policy.v1` | quality improvement loop | `quality_patch_policy.py` | `quality_defect_ledger.py`, `quality_patch_plan.py` | Classifies patchability; `may_edit` remains false |
| `figure-agent.quality-patch-plan.v1` | quality improvement loop | `quality_patch_plan.py` | `quality_patch_apply.py`, MCP quality tools | Proposal evidence only until explicit apply |
| `figure-agent.quality-patch-result.v1` | quality improvement loop | `quality_patch_apply.py` | operators, MCP quality tools | Records explicit apply/dry-run result and rollback path |
| `figure-agent.quality-memory-event.v1` | quality memory | `quality_memory_events.py` | `quality_memory_index.py`, operators | Fixture-local event derived from existing artifacts; cannot invent outcomes |
| `figure-agent.quality-memory-log.v1` | quality memory | `quality_memory_events.py` | `quality_memory_index.py`, operators | Read-only event list for one fixture |
| `figure-agent.quality-memory-index.v1` | quality memory | `quality_memory_index.py` | future memory-aware ranking, operators | Conservative priors only; cannot upgrade hard gates or apply authority |
| `figure-agent.benchmark-contract.v1` | quality benchmark | `benchmark_contracts.py` | `quality_benchmark.py`, release gate | Fixture-local benchmark contract; separates defect, family, edit-class, detector, and source-policy axes |
| `figure-agent.benchmark-detectors-preview.v1` | quality benchmark | `benchmark_detector_reports.py` | `fig-agent benchmark-detectors`, MCP benchmark tools, release gate | Read-only-by-default detector report generation envelope; write mode stays fixture-local |
| `figure-agent.benchmark-detector-report.v1` | quality benchmark | `benchmark_detector_reports.py` | `quality_benchmark.py`, release gate, candidate ranking | Explicit normalized detector report schema for seed and future render-derived metrics |
| `figure-agent.quality-benchmark-list.v1` | quality benchmark | `quality_benchmark.py` | operators, future MCP benchmark tools | Read-only suite manifest view |
| `figure-agent.quality-benchmark-run.v1` | quality benchmark | `quality_benchmark.py` | benchmark compare, operators | Local benchmark report; writes only repo/workspace-local scratch when explicit |
| `figure-agent.quality-benchmark-comparison.v1` | quality benchmark | `quality_benchmark.py` | operators, future release gate checks | Compares local benchmark reports and surfaces regressions |
| `figure-agent.quality-next-experiment.v1` | quality benchmark | `quality_next_experiment.py` | MCP benchmark tools, operators | Read-only preview recommendation; command is allowlisted and contains no write/apply/accept flags |
| `figure-agent.intent-model.v1` | candidate search | `figure_intent_model.py` | `candidate_generator.py`, MCP candidate tools | Read-only fixture intent model; missing optional inputs downgrade authority instead of inventing claims |
| `figure-agent.candidate-tex-index.v1` | candidate search | `candidate_tex_index.py` | `candidate_panel_model.py`, `candidate_families.py` | Read-only TeX selector index; panel hints and active command ranges only |
| `figure-agent.candidate-panel-model.v1` | candidate search | `candidate_panel_model.py` | `candidate_families.py`, MCP panel tools | Read-only panel model joining intent, bbox hints, selectors, and visual-review state |
| `figure-agent.candidate-set.v1` | candidate search | `candidate_generator.py` | `candidate_render.py`, `candidate_rank.py`, MCP candidate tools | Bounded improvement alternatives; pre-render apply authority ceiling only |
| `figure-agent.candidate-manifest.v1` | candidate search | `candidate_render.py` | `candidate_rank.py`, `candidate_review_packet.py` | Fixture-local sandbox evidence; never final exports or source truth |
| `figure-agent.candidate-render-manifest.v1` | candidate search | `candidate_render.py` | `candidate_rank.py`, `candidate_review_packet.py`, `quality_memory_events.py` | Per-candidate render evidence; human review still required |
| `figure-agent.candidate-render-result.v1` | candidate search | `candidate_render.py` | CLI/MCP candidate workflow | Records rendered candidate sandbox manifests and artifacts |
| `figure-agent.composition-candidate-set.v1` | LLM-amplifying composition search | `composition_contracts.py` | `composition_render.py`, CLI composition workflow | Host-authored proposal capture only; plugin does not call models or execute payloads |
| `figure-agent.freshness-vector.v1` | LLM-amplifying composition search | `composition_contracts.py` | ranking/apply readiness, composition workflow | Captured evidence freshness; stale source downgrades to rebase/refresh instead of ranking or applying |
| `figure-agent.composition-render-manifest.v1` | LLM-amplifying composition search | `composition_render.py` | CLI composition workflow, `composition_rank.py`, `composition_review.py` | Fixture-local sandbox prepare manifest; compile/export/crop/evaluate remain not-run in this slice |
| `figure-agent.composition-render-result.v1` | LLM-amplifying composition search | `composition_render.py` | CLI composition workflow | Records safe candidate source-copy preparation and drift/block diagnostics; no TeX execution |
| `figure-agent.semantic-scene-model.v1` | LLM-amplifying composition search | `composition_scene.py` | CLI composition workflow, composition render selector resolution, future lint/rank/review | Read-only semantic block inventory and invariant coverage report; never invents scientific invariants |
| `figure-agent.composition-lint.v1` | LLM-amplifying composition search | `composition_lint.py` | CLI composition workflow, `composition_rank.py`, `composition_review.py` | Scene-only composition lint packet; deterministic checks carry metric/evidence/threshold, human commentary cannot rank or block |
| `figure-agent.composition-rank-result.v1` | LLM-amplifying composition search | `composition_rank.py` | CLI composition workflow, `composition_review.py` | Ranks only by hard gates and metric-backed deterministic composition lint deltas; human commentary and aesthetic/taste claims cannot rank or block |
| `figure-agent.composition-review-packet.v1` | LLM-amplifying composition search | `composition_review.py` | operators, future MCP composition tools | Read-only before/after source packet for prepared candidate sandboxes; no TeX execution, source mutation, acceptance, or apply authority |
| `figure-agent.candidate-score.v1` | candidate search | `candidate_rank.py` | `candidate_review_packet.py`, operators | Hard gates and scores may preserve or downgrade authority, never upgrade it |
| `figure-agent.candidate-rank-result.v1` | candidate search | `candidate_rank.py` | CLI/MCP candidate workflow | Ordered candidate scores for human or later CLI review |
| `figure-agent.candidate-review-packet.v1` | candidate search | `candidate_review_packet.py` | operators, MCP candidate tools | Read-only packet for human review of one rendered candidate |
| `figure-agent.semantic-candidate-review.v1` | candidate search | `semantic_candidate_review.py` | `candidate_review_packet.py`, `candidate_acceptance.py`, `candidate_apply.py` | Local semantic review artifact; can block apply but cannot grant authority |
| `figure-agent.semantic-review-state.v1` | candidate search | `semantic_candidate_review.py` | `candidate_review_packet.py`, `candidate_acceptance.py`, `candidate_apply.py` | Derived gate state; invalid, stale, or risky reviews fail closed |
| `figure-agent.candidate-apply-readiness.v1` | candidate search | `candidate_acceptance.py` | operators | Human acceptance preflight; no source mutation |
| `figure-agent.candidate-acceptance.v1` | candidate search | `candidate_acceptance.py` | `candidate_apply.py`, operators | Explicit human decision artifact required before apply |
| `figure-agent.candidate-apply-result.v1` | candidate search | `candidate_apply.py` | operators | Explicit CLI apply boundary; current implementation refuses source mutation unless eligible and opted in |
| `figure-agent.bounded-tikz-candidate-packet.v1` | bounded TikZ candidate handoff | `bounded_tikz_candidate_packet.py` | `bounded_tikz_candidate_apply.py`, operators | Read-only candidate packet; no source mutation authority |
| `figure-agent.bounded-tikz-apply-result.v1` | bounded TikZ candidate handoff | `bounded_tikz_candidate_apply.py` | operators | Hash-gated apply boundary; refuses mutation on packet/source hash mismatch |
| `figure-agent.bounded-tikz-refinement-packet.v1` | bounded TikZ candidate handoff | `bounded_tikz_refinement_packet.py` | operators | Read-only refinement request packet; `no_source_mutation` boundary |
| `figure-agent.design-dogfood-packet.v1` | design dogfood handoff | `design_dogfood_packet.py` | operators | Read-only human-gated dogfood packet over live queue state; `no_source_mutation` boundary |
| `figure-agent.evidence-index.v1` | candidate/evidence sync | `evidence_index.py` | `evidence_sync.py`, `closeout_readiness.py`, `quality_memory_events.py` | Fixture-local evidence summary; stale source checks can block acceptance |
| `figure-agent.evidence-sync.v1` | candidate/evidence sync | `evidence_sync.py` | operators, closeout tools | Writes only fixture evidence index when explicitly requested |
| `figure-agent.golden-acceptance.v1` | closeout acceptance | `golden_acceptance.py` | `closeout_readiness.py`, `quality_memory_events.py` | Explicit human/golden acceptance artifact; never inferred by MCP |
| `figure-agent.figure-spec.v1` | figure convergence contract | `convergence_models.py` | (none) | Defined and validated internally by `validate_figure_spec`; no other module imports it yet |
| `figure-agent.journal-guide.v1` | journal hard-constraint guide | `convergence_models.py`, `journal_guide.py` | `quality_search.py` | Hard constraints drive `evaluate_journal_constraints` violations that feed `figure-attempt.journal_constraints.passed`, which gates auto-accept eligibility |
| `figure-agent.aesthetic-objective.v1` | deterministic aesthetic scoring | `convergence_models.py`, `aesthetic_objective.py` | `quality_search.py` | Non-blocking score envelope; feeds `figure-attempt.aesthetic_score` used for ranking/convergence, not a hard gate itself |
| `figure-agent.figure-attempt.v1` | per-attempt convergence record | `convergence_models.py` | `convergence_controller.py`, `experience_log.py`, `attempt_store.py`, `quality_search.py` | Validated attempt (journal/semantic/aesthetic state) is required input to `decide_attempt`; failed journal/semantic state forces `reject`/blocks `auto_accept_recommended` |
| `figure-agent.convergence-decision.v1` | accept/reject/rollback/stop policy | `convergence_models.py`, `convergence_controller.py` | `quality_search.py`, `experience_log.py` | `quality_search.py` requires `decision == accept` before granting `auto_accept_recommended`; non-accept keeps the recommendation `status: blocked` |
| `figure-agent.critique-scaffold.v1` | fillable critique template | `critique_scaffold.py` | operators | `verdict_policy: human_required`; forbidden from writing `critique.md`/`human_attestation.json`/acceptance state — scaffold-only, never gates itself |
| `figure-agent.detector-demotion-recommendations.v1` | detector false-positive audit | `detector_demotion.py` | operators | Docstring states the signal is deliberately advisory; no other module consumes it, so it has no wired blocking authority |
| `figure-agent.experience-record.v1` | durable candidate/attempt ledger | `experience_log.py` | `candidate_generator.py`, `candidate_apply.py`, `quality_memory_index.py`, `quality_loop_metrics.py`, `quality_search.py` | Ground-truth append-only log; records `apply_status` (e.g. `blocked` until explicit apply) and supplies attempt history that feeds convergence decisions |
| `figure-agent.fixture-compare.v1` | read-only multi-fixture comparison | `fixture_compare.py` | operators | `mutation_boundary: read_only_no_source_or_state_mutation`; recommendation buckets are advisory next-action hints, not enforced elsewhere |
| `figure-agent.fixture-fork.v1` | fixture duplication receipt | `fixture_fork.py` | operators | Receipt sets `acceptance_state: NOT_DECLARED`; copy explicitly excludes state files (`critique.md`, `golden_acceptance.json`); no downstream reader |
| `figure-agent.fixture-visual-quality-metrics.v1` | advisory visual-quality metrics | `visual_quality_metrics.py` | `fixture_compare.py` | Payload declares `policy: advisory_only` and `mutation_boundary: writes_build_metrics_only_no_gate_state`; read for display only, no gating |

## Module Ownership Map

### Layer 0 - Inputs and Reference Grounding

Owns fixture source inputs and authoring/reference context. These modules should
not decide release readiness.

- `inputs.py`, `reference_contract.py`, `reference_extract.py`,
  `reference_pack.py`, `critique_reference_pack.py`
- `aesthetic_intent.py`, `paper_aesthetic_context.py`,
  `journal_art_direction_playbook.py`
- `authoring_rules.py`, `semantic_contracts.py`, `semantic_region_contract.py`,
  `narrative_context.py`, `authoring_context_pack.py`,
  `convention_receipt.py`
- `subregion_active_set.py`, `text_boundary_spec_helper.py`,
  `spec_bbox_helper.py`, `tex_coordinate_shift.py`

Add here when the feature declares author intent, reference intent, or fixture
metadata. Do not add detector reports here.

### Layer 1 - Build and Deterministic Detectors

Owns compile-time or render-derived facts. These modules may emit JSON reports
but should not decide host-vision verdicts.

- `compile.sh`, `lint_tex.py`, `palette.py`, `ocr.py`
- `check_collisions.py`, `check_visual_clash.py`,
  `check_visual_clash_budget.py`
- `check_text_boundary_clash.py`, `check_label_path_proximity.py`,
  `check_undeclared_geometry.py`, `vector_clearance.py`
- `perception_pack.py`, `reference_aesthetic_metrics.py`

Add here when the output is a deterministic detector artifact under
`examples/<name>/build/`.

### Layer 2 - Audit Evidence Packaging

Owns official evidence packs that host vision or status consumers inspect.

- `critique_zoom_crops.py` owns `build/audit_crops/manifest.json`
- `audit_evidence_summary.py` owns compact accounting state
- `audit_evidence_graph.py` owns deterministic read-only provenance graph output
- `visual_finding_artifacts.py` owns deterministic finding overlays, crops, and hashes
- `detector_feedback_ledger.py` owns cross-fixture detector feedback rollups
- `diagnostic_artifact_provenance.py` owns ad hoc/scratch artifact classification
- `critique_evidence_lint.py` owns narrow evidence-specific lint helpers

Add here when the feature answers "is every required evidence item present and
accounted?"

### Layer 2.5 - Operator Environment Diagnostics

Owns read-only diagnostics about the local plugin/operator environment. These
modules should not inspect or mutate figure release state.

- `plugin_install_freshness.py` owns source-vs-installed plugin cache freshness

Add here when the feature answers "is this local operator/plugin environment
using the intended tool version or package?"

### Layer 3 - Critique Authoring Contract

Owns prompt/schema/lint contract for host-vision critique. This layer may
require fields, but should not execute patches or exports.

- `critique_brief.py`, `critique_brief_sections.py`
- `critique_schema_vocab.py`, `critique_schema_validator.py`
- `critique_lint.py`, `critique_contract.py`
- `quality_manifest.py`

Any new critique schema field must update, at minimum:

1. `critique_schema_vocab.py`
2. `critique_brief.py` or `critique_brief_sections.py`
3. `critique_schema_validator.py`
4. `critique_lint.py` if the field has cross-field/accounting semantics
5. `quality_manifest.py` if the input set or rubric version changes
6. `fig_loop_assessments.py` if loop/driver output consumes it
7. command docs when host authoring instructions change

### Layer 4 - Adjudication and Loop Analysis

Owns converting critique findings into decisions, axis records, loop stops, and
patch handoff context. It should not mutate source except through explicit patch
executor paths.

- `critique_adjudication.py` (`scaffold` and `sync`)
- `fig_loop.py`, `fig_loop_decision.py`, `fig_loop_escalation.py`
- `fig_loop_assessments.py`, `fig_loop_axes.py`, `fig_loop_axis_records.py`
- `fig_loop_adjudication.py`, `fig_loop_quality_axes.py`,
  `fig_loop_subregion.py`, `fig_loop_markdown.py`
- `fig_loop_basin.py`, `fig_loop_handoff.py`, `fig_loop_records.py`
- `fig_loop_patch_evidence.py`, `fig_loop_patch_executor.py`,
  `fig_loop_auto_patch.py`
- `quality_defect_ledger.py`, `quality_patch_policy.py`,
  `quality_patch_plan.py`, `quality_patch_apply.py`
- `figure_intent_model.py`, `candidate_contracts.py`,
  `candidate_tex_index.py`, `candidate_panel_model.py`,
  `candidate_families.py`, `candidate_generator.py`, `candidate_render.py`,
  `candidate_rank.py`, `candidate_review_packet.py`, `candidate_apply.py`

Add here when the feature changes what `/fig_loop` sees or how it stops.
Candidate-search modules also belong here when they propose or rank bounded
improvement alternatives; they remain evidence/proposal owners until an
explicit CLI apply path mutates source.

### Layer 5 - Status, Driver, Runner, Queue

Owns operator routing and bounded execution. Driver outputs are advisory unless
the runner separately allows a deterministic shell command.

- `status.py`, `status_next_policy.py`, `status_explanation.py`,
  `status_readiness_policy.py`
- `fig_driver.py`, `fig_driver_commands.py`, `fig_driver_guidance.py`,
  `fig_driver_editorial.py`, `fig_driver_checkpoint.py`,
  `fig_driver_closeout.py`, `driver_actor.py`, `next_action_summary.py`
- `fig_run.py`, `fig_run_records.py`, `fig_run_journal.py`,
  `fig_improve.py`
- `fig_queue.py`, `fig_queue_run.py`, `fig_e2e_smoke.py`

Add here when the feature changes command routing, stop boundaries, queue/run
behavior, or operator UX.

### Layer 6 - Export, Acceptance, Publication, Final Artifact

Owns release blockers and final artifact integrity. It should not silently
approve human decisions.

- `run_export.py`, `export_freshness.py`, `export_svg.sh`, `svg_to_png.sh`,
  `diff_pdf_content.py`, `git_tracked.py`
- `check_golden_artifacts.py`, `publication_gate.py`, `fig_closeout.py`

Add here when the feature changes export freshness, accepted/golden gates,
publication compliance, SVG polish, or final-artifact readiness.

### Layer 7 - Package/Meta Utilities

Owns package integrity and helper tools that do not affect fixture state.

- `plugin_package_audit.py`, `release_gate.py`, `match_snippet.py`, `vtrace.py`

## Governance Rules

1. **One schema owner.** Every `figure-agent.*.vN` schema must have one primary
   owner module listed above.
2. **No silent critique schema bump.** If host prompt semantics change, update
   the schema/rubric version or explicitly document why the existing schema is
   unchanged.
3. **No detached detector report.** A new build JSON report must either be
   consumed by `critique_brief.py`, `audit_evidence_summary.py`, or both.
4. **No replay from scratch.** `.scratch` artifacts are evidence only unless a
   live status/driver check revalidates the state.
5. **Human gates stay human.** Driver, score, aesthetic, and reference metrics
   can recommend; accepted/golden/publication decisions require explicit human
   action.
6. **Prefer extending an existing layer.** Create a new script only when no
   existing owner has the same responsibility.

## Review Notes

### Review 1 - Schema Completeness

The matrix covers the high-churn contracts: critique lineage, audit evidence,
driver/run/queue contracts, SVG polish/final artifact contracts, aesthetic and
reference packs, and scratch provenance. Historical docs may mention older
perception schemas, but those are architecture notes rather than active command
contracts.

### Review 2 - Boundary Safety

The ownership map keeps source inputs, deterministic detectors, host-vision
critique, loop/adjudication, driver/runner, and release/final-artifact logic in
separate layers. The main safety rule is preserved: advisory quality signals do
not mutate accepted/golden/publication state.

### Review 3 - Future Work Routing

For future development:

- add visual detector outputs under Layer 1 and surface them through Layer 2;
- add critique slots under Layer 3 and consume them through Layer 4 only when
  routing needs them;
- add operator UX under Layer 5 without changing release semantics;
- add SVG/final artifact behavior under Layer 6 with explicit freshness and
  human-gate preservation.
