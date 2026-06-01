# Issue 100 - Comprehensive Figure-Agent Gap Inventory

Status: active roadmap; P0/P1 implemented, P2/P3 hardening continuing

Type: architecture review, operator workflow, audit coverage, roadmap

## Context

This document records the current figure-agent plugin gaps after the v0.9.x
audit hardening work, including Issues 90, 91, 97, and 99.

Current baseline:

- plugin root: `plugins/figure-agent`;
- branch baseline: `main` after Issue 99 label-frame boundary detection;
- user figure-source edits may be dirty and must not be treated as plugin work;
- shipped command surface includes `/fig_status`, `/fig_drive`, `/fig_run`,
  `/fig_improve`, `/fig_compile`, `/fig_critique`, `/fig_loop`,
  `/fig_export`, queue commands, and SVG polish handoff commands;
- current architecture intentionally separates deterministic gates, host-vision
  critique, verify-only loop state, bounded automation, and human release
  approval.

The plugin is no longer just a compiler wrapper. It is a quality kernel with
deterministic geometry checks, crop/candidate accounting, structured critique,
adjudication, loop state, guided runner, queue runner, SVG polish manifests,
publication gates, and golden/accepted boundaries.

It is still not a hidden auto-designer, journal acceptance oracle, or fully
automatic Nature/Science art director. The remaining work should make that
boundary clearer while reducing places where the operator must manually stitch
the workflow together.

## Current Strengths

1. **Deterministic compile QA**
   `/fig_compile` runs Style Lock checks, text collision checks, visual clash
   candidate generation, text-boundary checks, label-path proximity checks,
   undeclared geometry checks, and perception-pack generation.

2. **Freshness and release boundaries**
   `/fig_status` separates render, critique, export, acceptance, final-artifact,
   and publication state. `/fig_drive` dry-runs the next action and stops at
   host/human/release/polish boundaries instead of mutating hidden state.

3. **Structured host-vision critique**
   `/fig_critique` now carries high-zoom crops, print crops, candidate
   accounting, crop-read accountability, reference packs, aesthetic intent,
   top-tier audit slots, micro-defect categories, anti-pattern audit, and
   optional SVG polish delta evidence.

4. **Bounded SVG polish layer**
   SVG polish is manifest/recipe/delta based. Allowed edit classes are narrow,
   source hashes are checked, semantic backport requirements are explicit, and
   the plugin does not silently treat SVG polish as source truth.

5. **Operator-safe automation**
   `/fig_run`, `/fig_improve`, and queue commands execute only safe mechanical
   steps, then stop at host critique, patch handoff, human adjudication, SVG
   polish handoff, accepted/golden, force-golden, and publication boundaries.

## Gap Inventory

| ID | Priority | Area | Gap | Evidence | Impact | Candidate issue |
| --- | --- | --- | --- | --- | --- | --- |
| G100-01 | P0 | Evidence parity | `undeclared_geometry` is produced by compile and accepted by critique schema, but it was not first-class in `audit_evidence_summary.py`/status/driver UX. | Issue 99 explicitly scoped out mandatory audit-evidence integration; Issue 100A adds this path to the shared summary. | A real label-frame boundary risk should now surface through the same operator summary path as visual/text/label/crop evidence. | Issue 100A - undeclared-geometry audit evidence surfacing |
| G100-02 | P0 | Operator routing | The command surface is powerful but still confusing: users and agents can bounce among `/fig_status`, `/fig_drive`, `/fig_run`, `/fig_improve`, `/fig_loop`, `/fig_critique`, and `/fig_export` without knowing the canonical mode. | README says status/drive first and `fig_run` has no resume; repeated dogfood questions show "why does it say done?" and "which command should I run?" remains unresolved. | Correct tools exist, but operator friction makes the plugin feel less autonomous than it is. | Issue 100B - single guided entrypoint and explanation UX |
| G100-03 | P0 | Final pass discipline | Strict/final audit mode is opt-in and spread across compile, critique, loop, driver, and export. | `FIGURE_AGENT_STRICT=1` exists, but final release confidence still depends on humans knowing which checks to run. | Top-tier closeout can miss an available strict/final pass unless the operator requests it explicitly. | Issue 100C - final-readiness preset |
| G100-04 | P1 | SVG polish production path | SVG polish is safe and bounded, but positive-route real-figure evidence is still thin; the route mostly prevents unsafe polish rather than routinely improving finish. | Issue 100D added the fixture-aware recipe starter, and Issue 100V adds a deterministic positive harness that proves the SVG polish plumbing closes. README still keeps real-fixture promotion conservative. | The "last 5 percent" visual polish is mechanically supported but remains art-direction gated on real figures. | Issue 100D - SVG polish positive-route template; Issue 100V - SVG polish positive harness |
| G100-05 | P1 | Reference learning | Reference packs and aesthetic metrics exist, but authoring high-quality reference lessons is still operator-dependent. | `critique_reference_pack.yaml` and reference-learning metrics are opt-in; the plugin can warn against copying but cannot infer the best lessons without user framing. | Poor reference packs can cause under-learning, over-learning, or generic prose. | Issue 100E - reference-learning authoring template and anti-copy checklist |
| G100-06 | P1 | Aesthetic guidance | Aesthetic scores/signals are advisory by design, but the UX does not always distinguish "measurable defect", "style recommendation", and "human taste decision" clearly enough. | Issue 97 added anti-pattern and marginal-return audits, but release still cannot be blocked on taste alone. | Users may expect the plugin to autonomously make Nature/Science art-direction calls it should only surface. | Issue 100F - advisory-vs-blocking aesthetic language |
| G100-07 | P1 | Loop basin detection | The system has basin summaries, but they are not yet paired with resumable long-run UX and durable defect-class history across interrupted sessions. | `/fig_run` records journals but has no resume command; current basin surfacing is useful but not a full continuation model. | Long polish sessions can still require human reconstruction after interruptions or repeated subjective loops. | Issue 100G - run-history basin and repeated-defect detector |
| G100-08 | P2 | Schema/version sprawl | Critique schemas now span v1 through v1.17. Backward compatibility is valuable, but the mental model is heavy. | `critique_schema_vocab.py` lists many active schema versions and validators carry optional legacy paths. | Future changes risk silent contract drift or overfitting tests to old formats. | Issue 100H - schema capability matrix and deprecation policy |
| G100-09 | P2 | Code surface size | The plugin has many scripts and commands; boundaries are mostly documented but not summarized as an ownership map. | Current inventory is 89 scripts, 100 tests, and 15 command docs. | New contributors or agents can pick the wrong module and duplicate logic. | Issue 100I - module ownership map |
| G100-10 | P2 | Queue and resume UX | Multi-fixture queue support exists, but single-fixture long-loop resume remains manual. | README states there is no resume command; continuation requires inspecting journal JSON. | Real dogfood sessions lose time reconstructing state after interruption. | Issue 100J - resumable guided run checkpoint |
| G100-11 | P2 | External second opinion | External review evidence is supported, but second-opinion routing is not a simple first-class queue mode. | External vision support exists as evidence, not as a default loop actor. | Hard subjective defects may still require ad hoc advisor/subagent orchestration. | Issue 100K - optional second-opinion route |
| G100-12 | P2 | Paper-wide style propagation | Paper-wide aesthetic context existed, but starting a new pack required manual copying from catalog examples. | README marked paper-wide context as opt-in but did not provide a starter command. | A single figure can pass while the paper series remains visually inconsistent, and operators may skip the pack because it is too manual to start. | Issue 100L - paper-wide context template |
| G100-13 | P2 | Subregion iteration | Subregion iteration tooling had parser/loop integration but no starter/append helper for the operator-facing log. | README listed `docs/subregion-iteration-tool.md` as experimental/proposed even though active-set plumbing existed. | The most effective human workflow could still drift into inconsistent hand-authored logs. | Issue 100M - subregion iteration assistant |
| G100-14 | P3 | Plugin freshness/install UX | Plugin cache and marketplace validation exist, but "am I using the newest plugin?" is still something users ask. | README discusses plugin install validation and cache audit, but no single user-facing freshness command is prominent. | Users may run old cached command docs while main has newer behavior. | Issue 100N - plugin install/version freshness check |
| G100-15 | P3 | Detector tuning feedback | Deterministic detectors catch more issues now, but threshold tuning is empirical and false-positive/false-negative memory is scattered across milestones. | Visual clash and geometry checkers have known report-only/noisy modes. | Detector quality improves only through ad hoc issue creation instead of a systematic feedback log. | Issue 100O - detector feedback ledger |
| G100-16 | P3 | Documentation hygiene | Some older issue documents carried stale status text such as "pending commit" or branch-only implementation status after later merges. | Issue 100P swept the current stale headers for 100F/100G and normalized 100E/100R/100J/100H-I/100N-O to main commit references. | Agents no longer see already-merged Issue 100 work as pending branch work. | Issue 100P - stale issue status sweep |
| G100-17 | P1 | Critique semantic drift | A critique can be hash-fresh while prose or audit slots still mention a phantom/deleted visual entity. | Issue 100Q adds a conservative source-text lint for matched symbolic label-target entities that are absent from active TeX or survive only in comments. | Fresh critiques that claim a removed symbolic label is visible are blocked before they confuse human operators. | Issue 100Q - critique entity consistency lint |
| G100-18 | P1 | Scratch artifact provenance | Ad hoc diagnostic crops can be stale relative to the current build and still influence human or agent judgment. | Generated build crops are manifest-bound, but arbitrary scratch crops are not part of the freshness graph. | Users can chase a defect that exists only in an old diagnostic artifact. | Issue 100R - diagnostic artifact provenance rule |
| G100-19 | P1 | Strict-mode false-positive budget | A final-readiness preset cannot be just raw `FIGURE_AGENT_STRICT=1`; noisy report-only candidates need fixture caps or adjudicated budgets. | Issue 100S makes `visual_clash_cap` a first-class final-mode warning budget and routes missing reports to strict compile, over-budget reports to human review. | Final mode no longer claims completion while visual-clash warnings exceed the reviewed fixture cap. | Issue 100S - final strict profile and warning budgets |
| G100-20 | P2 | Host/subagent evidence trace | Crop accounting says what the critique claims to have inspected, but there is no durable transcript-level read log for subagent-host inspection. | Milestones often record manual Read counts, but the plugin contract stores crop audit results rather than the viewer transcript. | Independent review of "did the host actually inspect this?" still relies on session prose. | Issue 100T - optional inspection transcript artifact |
| G100-21 | P2 | Human-decision preservation | `scaffold --force` and re-adjudication flows can be correct but still risky if operators do not see which human decisions were preserved, dropped, or rebound. | Sync paths exist, but force-scaffold remains a sharp tool in real workflows. | Human rationale can be accidentally flattened during freshness repair. | Issue 100U - adjudication decision diff preview |

## Recommended Execution Order

### Track A - Make Existing Evidence Impossible To Miss

1. **Issue 100A - undeclared-geometry audit evidence surfacing**
   Implemented in `scripts/audit_evidence_summary.py` with tests covering
   missing report, malformed report, unaccounted candidate, unknown reference,
   accounted candidate, and no-candidate states. `/fig_status`, `/fig_loop`, and
   `/fig_drive` inherit this through the existing shared `audit_evidence` path.

2. **Issue 100B - guided entrypoint and explanation UX**
   Implemented in `/fig_drive` through additive `operator_guidance`, which
   names the plain next step and the required actor (`workflow_agent`,
   `host_llm`, `human`, `release_operator`, `svg_editor`, or `none`) without
   changing the existing action vocabulary or mutation boundaries.

3. **Issue 100C - final-readiness preset**
   Implemented as `/fig_drive --mode final --goal "final readiness" --dry-run`.
   The mode reuses release gates and emits `final_readiness_profile` with a
   strict compile row, critique, loop, export, publication, and release-gate
   states. It remains dry-run and does not mutate accepted/golden/publication
   state.

### Track B - Improve Top-Tier Polish Without Pretending It Is Objective

4. **Issue 100D - SVG polish positive-route dogfood**
   Completed as a positive-route usability hardening slice. Added a
   fixture-aware `svg_polish_recipe.py --template examples/<name>` starter that
   emits a valid bounded recipe with current `recipe_input_hash` and conservative
   visual-only operation classes. This improves startability without changing
   executor safety or claiming SVG polish should run automatically.

5. **Issue 100V - SVG polish positive harness**
   Implemented as a deterministic fixture-shaped plumbing proof. Added
   `scripts/svg_polish_positive_harness.py`, a synthetic fixture seed, and tests
   that exercise recipe execution, delta generation, semantic diff, handoff
   manifest/audit writing, status final-artifact freshness, and polish-driver
   completion without mutating real examples or claiming real-figure readiness.

6. **Issue 100E - reference-learning authoring template**
   Completed on main in commit `99a440e`. The reference pack tool now emits a
   v1.1 starter template and validates that v1.1 opt-in
   `reference_learning` covers concrete allowed-transfer axes (palette family,
   density, typography hierarchy, abstraction level, line language, composition
   rhythm) plus anti-copy guards (topology, exact geometry, label text, claim
   payload, panel semantics). Legacy v1 packs remain parseable.

7. **Issue 100F - advisory-vs-blocking aesthetic language**
   Completed on main in commit `52855e1`. Shared `next_action_summary` now
   includes additive `decision_boundary` metadata, and
   `/fig_drive.operator_guidance` copies it so deterministic gates,
   host-vision gates, human decisions, release decisions, SVG-polish handoffs,
   advisory-only improvements, and clean completion are explicit.

### Track C - Reduce Long-Session Friction

8. **Issue 100G - repeated-defect basin detector**
   Completed on main in commit `417805b`. Existing `fig_loop_basin.py`
   history detection now stays visible through
   `/fig_drive.loop_checkpoint` and `/fig_run.boundary_handoff`: basin stops
   name the repeated signal, preserve `basin_summary`, and begin closeout with
   step-out actions instead of flattening into a generic human gate.

9. **Issue 100R - diagnostic artifact provenance rule**
   Completed on main in commit `49cb61d`; merged by `14c5b64`. Added
   `scripts/diagnostic_artifact_provenance.py` so extra screenshots, `/tmp`
   crops, and `.scratch/` diagnostics can be classified before use:
   current build renders and manifest-bound audit crops are authoritative;
   stale, mismatched, missing, or unmanifested diagnostics are context only.

10. **Issue 100K - optional second-opinion route**
   Completed. The external review validator now emits a
   hash-bound starter `external_vision_review.yaml` from the current build PNG
   and audit-crop manifest. This makes the second-opinion path first-class
   without adding provider APIs or changing external review authority.

11. **Issue 100J - resumable guided run checkpoint**
   Completed on main in commit `12c66c2`; merged by `8b0ff98`. Added
   `scripts/fig_run_journal.py` to summarize the latest
   `.scratch/fig-run-runs` journal for a fixture without replaying stored
   commands. The summary names the previous stop, required actor, closeout
   checks, and stale fixture evidence, then points operators back to live
   `/fig_status` and `/fig_drive`.

12. **Issue 100L - paper-wide context template**
    Completed as paper-series workflow hardening. Added
    `scripts/paper_aesthetic_context.py --template <paper_id> --fixture <name>
    --write-template` so operators can start a valid v1 paper-wide context pack
    without manually copying catalog examples. Fixture opt-in remains explicit
    through `spec.yaml.paper_aesthetic_context`.

13. **Issue 100M - subregion iteration assistant**
    Completed as text-form workflow hardening. Added
    `scripts/subregion_iteration_log.py` so operators can create the canonical
    `subregion_iteration_log.md` and append one patch row at a time while
    preserving compatibility with the existing active-set parser, critique
    brief, and loop handoff.

### Track D - Maintainability

14. **Issue 100H/I - schema and module maps**
   Completed on main in commit `d3ccf37`; merged by `200910c`. Added
   `docs/superpowers/issues/2026-06-01-issue-100hi-schema-module-map.md`,
   covering active schema owners, critique schema capability lineage, module
   layer ownership, and governance rules for future schema/script changes.

15. **Issue 100N/O - freshness and detector feedback**
    Completed on main in commit `d50da39`; merged by `5a51be3`. Added
    read-only `critique_freshness` diagnostics to status output and
    `detector_feedback` counts to audit evidence so stale critique causes and
    detector tuning signals are visible without changing gates or mutating
    fixture state.

16. **Issue 100P - stale issue status sweep**
    Completed as a docs-only sweep. Swept current Issue 100 headers for
    `pending commit`, `pending merge`, and branch-only stale status markers.
    Updated 100F/100G from pending-commit to completed main commits and
    normalized already-merged 100E/100R/100J/100H-I/100N-O headers to main
    commit references.

17. **Issue 100T/U - evidence trace and human-decision diff**
    Completed as an auditability hardening slice. Added optional
    `inspection_trace.yaml` parser/validator + CLI, wired present traces into
    `critique_lint.py`, and added `critique_adjudication.py sync --preview`
    for a read-only preserved/dropped/added/shape-changed decision diff before
    operators choose normal sync or force-scaffold.

18. **Issue 100Q - critique entity consistency lint**
    Completed as a conservative critique-lint hardening slice.
    `critique_lint.py` now blocks matched symbolic label-target audit entries
    whose entity token is absent from active TeX or appears only in comments.
    This closes the narrow phantom-entity gap without attempting broad visual
    OCR or natural-language object detection.

19. **Issue 100S - final strict profile and warning budgets**
    Completed as a final-mode warning-budget hardening slice. Reused
    `spec.yaml.visual_clash_cap` and `build/visual_clash.json` as
    `figure-agent.warning-budget.v1`; `/fig_drive --mode final` now requests
    strict compile when the report is missing and stops at a human gate when
    visual-clash warnings exceed the reviewed fixture cap.

## Non-Goals

- Do not create hidden auto-editing or hidden auto-design behavior.
- Do not mutate source, accepted, golden, export, SVG polish, or publication
  state from a status/review command.
- Do not make aesthetic score alone a release gate.
- Do not require external web/API calls for the core plugin loop.
- Do not treat reference images as templates to copy.
- Do not touch unrelated dirty figure-source work while improving the plugin.

## Design Review Notes

### Review 1 - Safety

The roadmap preserves the core boundary: deterministic checks can block,
structured critique can route, and human approval still owns subjective art
direction, accepted/golden roll-forward, and publication claims.

### Review 2 - Architecture Fit

The highest-priority gap is not another broad aesthetic field. It is evidence
parity: once a detector exists, its evidence must surface through the same
summary/loop/driver channels as older detectors. This keeps the plugin coherent
instead of adding more isolated scripts.

### Review 3 - Operator Reality

The plugin can be technically correct and still feel incomplete if the user
must remember which command to run. The next ergonomic improvement should be a
clear guided entrypoint and final-readiness preset, not another parallel command
with overlapping responsibilities.

## Additional Update Analysis

After writing the inventory, the most urgent update candidate was
**Issue 100A**. It is a narrow contract-completion fix, not a new feature:
`check_undeclared_geometry.py` already emits evidence and the critique validator
already accepts `undeclared_geometry` references. Issue 100A closes the missing
operator-summary path.

The second update candidate is **Issue 100B/100C together**. They should be
designed as one UX slice before implementation so the plugin gets one coherent
operator story:

- "What should I run first?"
- "Why did the agent say this is complete?"
- "What is the final non-mutating check before human force-golden/release?"

The third update candidate is a maintainability guard: before the next critique
schema bump, write the schema capability matrix from Issue 100H. The validator
is still workable, but adding more fields without a matrix will make future
host-critique changes harder to review.

No new broad aesthetic detector should be added before 100A-C. The plugin's
current risk is not lack of another taste rubric; it is that existing evidence
and command guidance are not always surfaced in the path the user actually
runs.

## Edge-Case Review

1. **Fresh hash, stale semantic claim**
   Hash freshness prevents old inputs from masquerading as new critique, but it
   does not prove that every named object in `critique.md` still exists in the
   rendered figure. This is a host-vision contract gap, not a file freshness gap.

2. **Current PDF, stale scratch crop**
   Only manifest-bound build artifacts should be treated as plugin truth. Any
   ad hoc crop outside the manifest needs a timestamp/source hash or should be
   treated as diagnostic-only.

3. **Strict mode as final mode**
   Strict mode is not automatically a good final gate. A final preset needs
   warning budgets, fixture caps, or explicit adjudicated exceptions so known
   false positives do not drown real failures.

4. **Subagent critique without durable read trace**
   The schema can require crop accounting, but session-level proof that an agent
   opened each image is still outside the plugin artifact contract. This is
   acceptable for now, but it should be named as an audit limitation.

5. **Adjudication freshness repair**
   A hash rebind can preserve human decisions, but force-scaffolding can also
   erase useful rationale. Before automating more of this path, the plugin needs
   a decision diff preview.

6. **Aesthetic overreach**
   The plugin should improve how it asks aesthetic questions, but it should not
   pretend a numeric or prose taste signal is equivalent to journal acceptance.
   The right direction is better routing and better evidence, not hidden design
   authority.

## Documentation Consistency Check

- `README.md` and `.claude-plugin/plugin.json` both identify the current plugin
  as v0.9.1.
- `README.md` and `skills/figure-agent/SKILL.md` agree that `/fig_run` and
  `/fig_improve` are bounded and have no resume command.
- `README.md`, `commands/fig_drive.md`, and `svg_polish_*` scripts agree that
  SVG polish is a bounded handoff path, not an automatic broad beautifier.
- Issue 99 explicitly deferred `undeclared_geometry` audit-evidence surfacing;
  this is now tracked and implemented as G100-01/Issue 100A.
- Two older issue files carried drift-prone status text:
  `2026-05-27-issue-53-post-compile-real-fixture-state-sweep.md` and
  `2026-05-30-issue-89-v0-9-operator-grade-release-candidate.md`. Issue 100
  cleanup now updates both headers to completed/current-state wording.

## Completion Criteria For This Roadmap

This inventory is complete when:

- every listed P0/P1 gap has a follow-up issue or explicit decision to defer;
- Issue 100A is implemented before adding another detector family;
- command docs explain status, drive, run, improve, loop, critique, export, and
  SVG polish routing in operator language;
- final-readiness checks can be invoked as one non-mutating command path;
- schema/module maps exist before the next schema bump beyond v1.17.
