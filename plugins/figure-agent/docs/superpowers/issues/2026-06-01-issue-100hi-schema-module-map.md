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
| `v1.1` | mandatory `audit_enumeration` | `critique_brief.py` | `critique_schema_validator.py` | `critique_adjudication.py` | Legacy-compatible |
| `v1.2` | quality axes + `journal_grade_assessment` | `critique_brief.py` | `critique_schema_validator.py`, `critique_lint.py` | `fig_loop_assessments.py`, `fig_loop_axes.py` | Advisory scores only unless explicitly gateable |
| `v1.3` | top-tier journal audit | `critique_brief.py` | `critique_schema_validator.py`, `critique_lint.py` | `fig_loop_assessments.py` | Top-tier failure must surface as visible finding/blocker |
| `v1.4` | high-zoom/print micro-defect accounting expansion | `critique_brief.py` | `critique_lint.py`, `audit_evidence_summary.py` | `/fig_loop`, `/fig_drive` via audit evidence | Required when audit candidate JSON exists |
| `v1.5` | editorial art-direction audit | `critique_brief.py` | `critique_schema_validator.py`, `critique_lint.py` | `fig_driver_editorial.py`, `fig_loop_assessments.py` | Human art-direction gates stay explicit |
| `v1.6` | SVG-polish route semantics begin | `critique_brief.py` | `critique_lint.py` | `fig_driver_editorial.py` | SVG polish remains handoff, not hidden edit |
| `v1.7` | visual-clash candidate accounting | `check_visual_clash.py`, `critique_brief.py` | `critique_lint.py`, `audit_evidence_summary.py` | `fig_status`, `fig_loop`, `fig_drive` | Every `VC###` must be accounted |
| `v1.8` | crop-read accountability via audit crop manifest | `critique_zoom_crops.py`, `critique_brief.py` | `critique_lint.py`, `audit_evidence_summary.py` | `fig_loop_assessments.py` | Required crop ids must appear exactly once |
| `v1.9` | print/zoom grounded micro-defect hardening | `critique_brief.py` | `critique_lint.py` | `audit_evidence_summary.py` | Ambiguous crops route to action, not silent pass |
| `v1.10` | mature default critique contract | `critique_brief.py` | `critique_schema_validator.py`, `critique_lint.py` | `quality_manifest.py`, `fig_loop.py` | Default for non-grounded current critiques |
| `v1.11` | aesthetic lever grammar audit | `aesthetic_intent.py`, `critique_brief.py` | `critique_lint.py` | `fig_loop_assessments.py` | Lever route must match declared route |
| `v1.12` | journal art-direction playbook audit | `journal_art_direction_playbook.py`, `critique_brief.py` | `critique_lint.py`, `critique_schema_validator.py` | `fig_loop_assessments.py` | Generic journal prose invalid once opted in |
| `v1.13` | reference learning accountability | `critique_reference_pack.py`, `reference_aesthetic_metrics.py` | `critique_lint.py` | `fig_loop_assessments.py` | Reference is learning anchor, not copy target |
| `v1.14` | route-detail contract and richer aesthetic intent | `critique_brief.py` | `critique_lint.py`, `quality_manifest.py` | `fig_driver.py`, `fig_loop.py` | Route-specific rationale required |
| `v1.15` | SVG polish gate/delta hardening | `svg_polish_manifest.py`, `svg_polish_delta.py` | `critique_lint.py`, `fig_driver_editorial.py` | `fig_driver.py`, `check_golden_artifacts.py` | SVG polish cannot bypass semantic backport |
| `v1.16` | SVG polish delta audit | `svg_polish_delta.py`, `critique_brief.py` | `critique_lint.py` | `fig_driver_editorial.py` | Before/after/diff evidence required |
| `v1.17` | grounded observation and anomaly accountability | `critique_zoom_crops.py`, `check_undeclared_geometry.py`, `critique_brief.py` | `critique_schema_validator.py`, `critique_lint.py`, `audit_evidence_summary.py` | `fig_loop_assessments.py`, `fig_driver.py` | Current grounded schema; new grounded fields should extend this |

### Non-Critique Schemas

| Schema | Owner | Producer | Validator/reader | Blocking authority |
|---|---|---|---|---|
| `figure-agent.audit-crop-manifest.v1` | audit evidence | `critique_zoom_crops.py` | `critique_lint.py`, `audit_evidence_summary.py` | Blocks critique evidence if required crops mismatch |
| `figure-agent.audit-evidence-summary.v1` | audit evidence | `audit_evidence_summary.py` | `status.py`, `fig_loop.py`, `fig_driver.py` | Advisory until state is `missing_input`, `needs_action`, or `stale_or_mismatched` |
| `figure-agent.audit-evidence-graph.v1` | audit evidence | `audit_evidence_graph.py` | operators, MCP resource metadata | Read-only provenance graph; never mutates fixture state |
| `figure-agent.detector-feedback-ledger.v1` | detector tuning diagnostics | `detector_feedback_ledger.py` | operators | Read-only cross-fixture summary; no threshold or gate authority |
| `figure-agent.text-boundary-clash.v1` | deterministic detector | `check_text_boundary_clash.py` | `audit_evidence_summary.py`, `fig_closeout.py` | Can block closeout when stale/missing or malformed |
| `figure-agent.label-path-proximity.v1` | deterministic detector | `check_label_path_proximity.py` | `audit_evidence_summary.py`, `critique_brief.py` | Candidate evidence until critique/adjudication acts |
| `figure-agent.undeclared-geometry.v1` | deterministic detector | `check_undeclared_geometry.py` | `audit_evidence_summary.py`, `critique_brief.py` | Candidate evidence until critique/adjudication acts |
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
| `figure-agent.fig-run-journal.v1` / `figure-agent.fig-run-journal-ref.v1` | run journal | `fig_run_records.py` | `fig_run_journal.py` | Non-authoritative; never replay |
| `figure-agent.fig-run-evidence-snapshot.v1` | run journal freshness | `fig_run_evidence.py`, `fig_run_records.py` | `fig_run_journal.py` | Non-authoritative content freshness check; never replay |
| `figure-agent.fig-run-journal-error.v1` | run journal error | `fig_run.py` | `fig_run_journal.py` | Diagnostic only; rerun live status/driver |
| `figure-agent.fig-run-journal-summary.v1` | run continuation UX | `fig_run_journal.py` | operators | Non-authoritative; points to live status/driver |
| `figure-agent.boundary-handoff.v1` | stop explanation | `fig_run.py`, `next_action_summary.py` | operators, outer agents | Explanation only, not a second router |
| `figure-agent.decision-boundary.v1` | advisory/blocking language | `next_action_summary.py`, `fig_driver_guidance.py` | command output, docs | Clarifies who may decide; does not execute |
| `figure-agent.next-action-summary.v1` | operator UX | `next_action_summary.py` | `fig_driver.py`, queue/run outputs | Explanation only; not a state owner |
| `figure-agent.operator-guidance.v1` / `figure-agent.final-readiness.v1` | operator UX | `fig_driver_guidance.py` | command output | Guidance only; does not bypass status/export gates |
| `figure-agent.loop-basin.v1` | loop progress detection | `fig_loop_basin.py` | `fig_loop.py`, `fig_driver.py`, `fig_run.py` | Step-out advisory/handoff, not auto-patch |
| `figure-agent.improve.v1` | bounded improvement loop | `fig_improve.py` | operators | Runs bounded commands; stops at gates |
| `figure-agent.ready-improvement-summary.v1` / `figure-agent.marginal-return-summary.v1` | post-ready improvement discovery | `ready_improvement.py` | `fig_driver.py`, operators | Advisory; not acceptance |
| `figure-agent.fixture-driver-queue.v1` / `figure-agent.fixture-command-plan.v1` | batch planning | `fig_queue.py` | operators, `fig_queue_run.py` | Must preserve per-fixture gates |
| `figure-agent.queue-run.v1` / `figure-agent.queue-operator-handoff.v1` | batch execution | `fig_queue_run.py`, `fig_queue.py` | operators | Must stop at human/closeout boundaries |
| `figure-agent.e2e-smoke.v1` | deterministic smoke | `fig_e2e_smoke.py` | operators, CI | Deterministic gate only; not host-vision readiness |
| `figure-agent.svg-polish-manifest.v1` | final artifact integrity | `svg_polish_manifest.py` | `status.py`, `check_golden_artifacts.py` | Can block final readiness |
| `figure-agent.svg-polish-recipe.v1` | SVG edit intent | `svg_polish_recipe.py` | `svg_polish_executor.py`, `svg_polish_delta.py` | Executor input only |
| `figure-agent.svg-polish-plan.v1` | SVG executor plan | `svg_polish_executor.py` | operators, tests | Plan evidence only until delta/manifest validate |
| `figure-agent.svg-polish-positive-harness.v1` | SVG polish plumbing harness | `svg_polish_positive_harness.py` | tests, operators | Synthetic proof only; not real-figure readiness |
| `figure-agent.svg-polish-readiness.v1` / `figure-agent.svg-polish-gate.v1` | SVG route/gate | `fig_driver_editorial.py` | `fig_driver.py`, `fig_loop.py` | Can route to SVG polish or semantic backport |
| `figure-agent.svg-polish-delta.v1` | SVG before/after audit pack | `svg_polish_delta.py` | `critique_brief.py`, `critique_lint.py`, `fig_driver.py` | Can require semantic backport or human art direction |
| `figure-agent.svg-semantic-diff.v1` | SVG semantic safety | `svg_semantic_diff.py` | `svg_polish_manifest.py` | Can block final artifact freshness |
| `figure-agent.reference-aesthetic-metrics.v1` | numeric reference-class signal | `reference_aesthetic_metrics.py` | `critique_brief.py`, `critique_lint.py` | Advisory unless explicitly routed |
| `figure-agent.critique-reference-pack.v1.1` / `figure-agent.reference-learning.v1` | reference learning | `critique_reference_pack.py` | `quality_manifest.py`, `critique_brief.py`, `critique_lint.py` | Freshness input; not copy target |
| `figure-agent.aesthetic-intent.v1` / `figure-agent.aesthetic-intent.v2` | aesthetic direction | `aesthetic_intent.py` | `critique_brief.py`, `critique_lint.py`, `quality_manifest.py` | Grounding input; not acceptance |
| `figure-agent.paper-aesthetic-context.v1` | paper-wide consistency | `paper_aesthetic_context.py` | `critique_brief.py`, `critique_lint.py` | Requires explicit anchor citations |
| `figure-agent.journal-art-direction-playbook.v1` | target-journal style anchors | `journal_art_direction_playbook.py` | `critique_brief.py`, `critique_lint.py` | Requires exact anchor citations |
| `figure-agent.external-vision-review.v1` | optional second opinion | `external_vision_review.py` | `quality_manifest.py`, `critique_lint.py` | Evidence only unless routed through findings |
| `figure-agent.inspection-trace.v1` | host/subagent inspection trace | `inspection_trace.py` | `critique_lint.py`, operators | Optional auditability artifact; cannot prove image inspection by itself |
| `figure-agent.diagnostic-artifact-provenance.v1` | scratch/debug artifact safety | `diagnostic_artifact_provenance.py` | operators | Prevents stale diagnostics from becoming truth |
| `figure-agent.plugin-install-freshness.v1` | plugin install diagnostics | `plugin_install_freshness.py` | operators | Read-only source-vs-cache check; never mutates install state |
| `figure-agent.release-gate.v1` | package/release gate | `release_gate.py` | operators, CI | Builds and audits Cowork ZIP; skips missing host validators explicitly |
| `figure-agent.quality-defect-ledger.v1` | quality improvement loop | `quality_defect_ledger.py` | `quality_patch_plan.py`, MCP quality tools | Read-only defect ledger; no source mutation |
| `figure-agent.quality-patch-policy.v1` | quality improvement loop | `quality_patch_policy.py` | `quality_defect_ledger.py`, `quality_patch_plan.py` | Classifies patchability; `may_edit` remains false |
| `figure-agent.quality-patch-plan.v1` | quality improvement loop | `quality_patch_plan.py` | `quality_patch_apply.py`, MCP quality tools | Proposal evidence only until explicit apply |
| `figure-agent.quality-patch-result.v1` | quality improvement loop | `quality_patch_apply.py` | operators, MCP quality tools | Records explicit apply/dry-run result and rollback path |
| `figure-agent.intent-model.v1` | candidate search | `figure_intent_model.py` | `candidate_generator.py`, MCP candidate tools | Read-only fixture intent model; missing optional inputs downgrade authority instead of inventing claims |
| `figure-agent.candidate-set.v1` | candidate search | `candidate_generator.py` | `candidate_render.py`, `candidate_rank.py`, MCP candidate tools | Bounded improvement alternatives; pre-render apply authority ceiling only |
| `figure-agent.candidate-manifest.v1` | candidate search | `candidate_render.py` | `candidate_rank.py`, `candidate_review_packet.py` | Fixture-local sandbox evidence; never final exports or source truth |
| `figure-agent.candidate-render-result.v1` | candidate search | `candidate_render.py` | CLI/MCP candidate workflow | Records rendered candidate sandbox manifests and artifacts |
| `figure-agent.candidate-score.v1` | candidate search | `candidate_rank.py` | `candidate_review_packet.py`, operators | Hard gates and scores may preserve or downgrade authority, never upgrade it |
| `figure-agent.candidate-rank-result.v1` | candidate search | `candidate_rank.py` | CLI/MCP candidate workflow | Ordered candidate scores for human or later CLI review |
| `figure-agent.candidate-review-packet.v1` | candidate search | `candidate_review_packet.py` | operators, MCP candidate tools | Read-only packet for human review of one rendered candidate |
| `figure-agent.candidate-apply-result.v1` | candidate search | `candidate_apply.py` | operators | Explicit CLI apply boundary; current implementation refuses source mutation unless eligible and opted in |

## Module Ownership Map

### Layer 0 - Inputs and Reference Grounding

Owns fixture source inputs and authoring/reference context. These modules should
not decide release readiness.

- `inputs.py`, `reference_contract.py`, `reference_extract.py`,
  `reference_pack.py`, `critique_reference_pack.py`
- `aesthetic_intent.py`, `paper_aesthetic_context.py`,
  `journal_art_direction_playbook.py`
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
  `check_undeclared_geometry.py`, `check_layout_drift.py`
- `perception_pack.py`, `reference_aesthetic_metrics.py`

Add here when the output is a deterministic detector artifact under
`examples/<name>/build/`.

### Layer 2 - Audit Evidence Packaging

Owns official evidence packs that host vision or status consumers inspect.

- `critique_zoom_crops.py` owns `build/audit_crops/manifest.json`
- `audit_evidence_summary.py` owns compact accounting state
- `audit_evidence_graph.py` owns deterministic read-only provenance graph output
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
  `candidate_generator.py`, `candidate_render.py`, `candidate_rank.py`,
  `candidate_review_packet.py`, `candidate_apply.py`

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
- `svg_polish_manifest.py`, `svg_polish_recipe.py`,
  `svg_polish_executor.py`, `svg_polish_delta.py`,
  `svg_polish_handoff.py`, `svg_semantic_diff.py`

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
