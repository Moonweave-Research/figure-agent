# Issue 100 - Comprehensive Figure-Agent Gap Inventory

Status: active roadmap; listed P0-P3 hardening slices implemented through Issue 100DU plus operator/install evidence and the reference-aware candidate-search vertical slice, with real-fixture SVG polish promotion still evidence-gated

Type: architecture review, operator workflow, audit coverage, roadmap

## Context

This document records the current figure-agent plugin gaps after the v0.9.x
audit hardening work, including Issues 90, 91, 97, and 99.

Current baseline:

- plugin root: `plugins/figure-agent`;
- branch baseline: `main` after Issue 100DU fig-run JSON flag compatibility,
  operator completion explanation dogfood, install-refresh blocked evidence, and
  the reference-aware candidate-search vertical slice;
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

6. **Reference-aware candidate search**
   `fig-agent intent`, `candidates`, `render-candidates`, `rank-candidates`,
   and `review-candidate` now form a CLI-first search loop. The loop creates
   fixture-local candidate evidence, renders sandbox copies, ranks with hard
   gates, exposes read-only MCP tools, and refuses MCP-side source mutation.

## Gap Inventory

This table is a historical findings log, not a live open-backlog table. It
preserves the gap/evidence wording from the review pass that found each issue,
so some rows intentionally describe pre-fix behavior. Implemented status is
recorded in the Recommended Execution Order and issue-specific docs below.

| ID | Priority | Area | Gap | Evidence | Impact | Candidate issue |
| --- | --- | --- | --- | --- | --- | --- |
| G100-01 | P0 | Evidence parity | `undeclared_geometry` is produced by compile and accepted by critique schema, but it was not first-class in `audit_evidence_summary.py`/status/driver UX. | Issue 99 explicitly scoped out mandatory audit-evidence integration; Issue 100A adds this path to the shared summary. | A real label-frame boundary risk should now surface through the same operator summary path as visual/text/label/crop evidence. | Issue 100A - undeclared-geometry audit evidence surfacing |
| G100-02 | P0 | Operator routing | The command surface is powerful but still confusing: users and agents can bounce among `/fig_status`, `/fig_drive`, `/fig_run`, `/fig_improve`, `/fig_loop`, `/fig_critique`, and `/fig_export` without knowing the canonical mode. | README says status/drive first and `fig_run` has no resume; repeated dogfood questions show "why does it say done?" and "which command should I run?" remains unresolved. | Correct tools exist, but operator friction makes the plugin feel less autonomous than it is. | Issue 100B - single guided entrypoint and explanation UX |
| G100-03 | P0 | Final pass discipline | Strict/final audit mode is opt-in and spread across compile, critique, loop, driver, and export. | `FIGURE_AGENT_STRICT=1` exists, but final release confidence still depends on humans knowing which checks to run. | Top-tier closeout can miss an available strict/final pass unless the operator requests it explicitly. | Issue 100C - final-readiness preset |
| G100-04 | P1 | SVG polish production path | SVG polish is safe and bounded, but positive-route real-figure evidence is still thin; the route mostly prevents unsafe polish rather than routinely improving finish. | Issue 100D added the fixture-aware recipe starter, and Issue 100V adds a deterministic positive harness that proves the SVG polish plumbing closes. README still keeps real-fixture promotion conservative. | The "last 5 percent" visual polish is mechanically supported but remains art-direction gated on real figures. | Issue 100D - SVG polish positive-route template; Issue 100V - SVG polish positive harness |
| G100-05 | P1 | Reference learning | Reference packs and aesthetic metrics exist, but authoring high-quality reference lessons is still operator-dependent. | `critique_reference_pack.yaml` and reference-learning metrics are opt-in; the plugin can warn against copying but cannot infer the best lessons without user framing. | Poor reference packs can cause under-learning, over-learning, or generic prose. | Issue 100E - reference-learning authoring template and anti-copy checklist |
| G100-06 | P1 | Aesthetic guidance | Aesthetic scores/signals are advisory by design, but the UX does not always distinguish "measurable defect", "style recommendation", and "human taste decision" clearly enough. | Issue 97 added anti-pattern and marginal-return audits, but release still cannot be blocked on taste alone. | Users may expect the plugin to autonomously make Nature/Science art-direction calls it should only surface. | Issue 100F - advisory-vs-blocking aesthetic language |
| G100-07 | P1 | Loop basin detection | The system has basin summaries, but they are not yet paired with resumable long-run UX and durable defect-class history across interrupted sessions. | `/fig_run` records journals but has no resume command; current basin surfacing is useful but not a full continuation model. | Long polish sessions can still require human reconstruction after interruptions or repeated subjective loops. | Issue 100G - run-history basin and repeated-defect detector |
| G100-08 | P2 | Schema/version sprawl | Critique schemas now span v1 through v1.17. Backward compatibility is valuable, but the mental model is heavy. | `critique_schema_vocab.py` lists many active schema versions and validators carry optional legacy paths. Issue 100Z adds a release-contract guard so script schema constants cannot drift out of the module map. | Future changes now have a test-backed ownership map instead of relying on manual updates alone. | Issue 100H - schema capability matrix and deprecation policy; Issue 100Z - schema map drift guard |
| G100-09 | P2 | Code surface size | The plugin has many scripts and commands; boundaries are mostly documented but not summarized as an ownership map. | Current inventory is 111 scripts, 124 tests, and 15 command docs. | New contributors or agents can pick the wrong module and duplicate logic. | Issue 100I - module ownership map |
| G100-10 | P2 | Queue and resume UX | Multi-fixture queue support exists, but single-fixture long-loop resume remains manual. | README states there is no resume command; continuation requires inspecting journal JSON. | Real dogfood sessions lose time reconstructing state after interruption. | Issue 100J - resumable guided run checkpoint |
| G100-11 | P2 | External second opinion | External review evidence is supported, but second-opinion routing is not a simple first-class queue mode. | External vision support exists as evidence, not as a default loop actor. | Hard subjective defects may still require ad hoc advisor/subagent orchestration. | Issue 100K - optional second-opinion route |
| G100-12 | P2 | Paper-wide style propagation | Paper-wide aesthetic context existed, but starting a new pack required manual copying from catalog examples. | README marked paper-wide context as opt-in but did not provide a starter command. | A single figure can pass while the paper series remains visually inconsistent, and operators may skip the pack because it is too manual to start. | Issue 100L - paper-wide context template |
| G100-13 | P2 | Subregion iteration | Subregion iteration tooling had parser/loop integration but no starter/append helper for the operator-facing log. | README listed `docs/subregion-iteration-tool.md` as experimental/proposed even though active-set plumbing existed. | The most effective human workflow could still drift into inconsistent hand-authored logs. | Issue 100M - subregion iteration assistant |
| G100-14 | P3 | Plugin freshness/install UX | Plugin cache and marketplace validation exist, but "am I using the newest plugin?" is still something users ask. | Issue 100W adds a read-only source-vs-installed cache freshness command; Issue 100Y fixes same-version stale guidance where `claude plugin update` does not recopy an already-latest version. | Users can now distinguish stale installed plugin state from actual workflow behavior and get the correct update vs reinstall action. | Issue 100W - plugin install freshness check; Issue 100Y - same-version install refresh guidance |
| G100-15 | P3 | Detector tuning feedback | Deterministic detectors catch more issues now, but threshold tuning is empirical and false-positive/false-negative memory is scattered across milestones. | Visual clash and geometry checkers have known report-only/noisy modes. Issue 100X aggregates existing per-fixture detector feedback into a cross-fixture read-only ledger. | Detector quality improves through a stable review surface instead of ad hoc issue creation alone. | Issue 100O - detector feedback fields; Issue 100X - detector feedback ledger |
| G100-16 | P3 | Documentation hygiene | Some older issue documents carried stale status text such as "pending commit" or branch-only implementation status after later merges. | Issue 100P swept the current stale headers for 100F/100G and normalized 100E/100R/100J/100H-I/100N-O to main commit references. | Agents no longer see already-merged Issue 100 work as pending branch work. | Issue 100P - stale issue status sweep |
| G100-17 | P1 | Critique semantic drift | A critique can be hash-fresh while prose or audit slots still mention a phantom/deleted visual entity. | Issue 100Q adds a conservative source-text lint for matched symbolic label-target entities that are absent from active TeX or survive only in comments. | Fresh critiques that claim a removed symbolic label is visible are blocked before they confuse human operators. | Issue 100Q - critique entity consistency lint |
| G100-18 | P1 | Scratch artifact provenance | Ad hoc diagnostic crops can be stale relative to the current build and still influence human or agent judgment. | Generated build crops are manifest-bound, but arbitrary scratch crops are not part of the freshness graph. | Users can chase a defect that exists only in an old diagnostic artifact. | Issue 100R - diagnostic artifact provenance rule |
| G100-19 | P1 | Strict-mode false-positive budget | A final-readiness preset cannot be just raw `FIGURE_AGENT_STRICT=1`; noisy report-only candidates need fixture caps or adjudicated budgets. | Issue 100S makes `visual_clash_cap` a first-class final-mode warning budget and routes missing reports to strict compile, over-budget reports to human review. | Final mode no longer claims completion while visual-clash warnings exceed the reviewed fixture cap. | Issue 100S - final strict profile and warning budgets |
| G100-20 | P2 | Host/subagent evidence trace | Crop accounting says what the critique claims to have inspected, but there is no durable transcript-level read log for subagent-host inspection. | Milestones often record manual Read counts, but the plugin contract stores crop audit results rather than the viewer transcript. | Independent review of "did the host actually inspect this?" still relies on session prose. | Issue 100T - optional inspection transcript artifact |
| G100-21 | P2 | Human-decision preservation | `scaffold --force` and re-adjudication flows can be correct but still risky if operators do not see which human decisions were preserved, dropped, or rebound. | Sync paths exist, but force-scaffold remains a sharp tool in real workflows. | Human rationale can be accidentally flattened during freshness repair. | Issue 100U - adjudication decision diff preview |
| G100-22 | P2 | Command surface drift | Command docs can be added without the README Core commands list naming the command. | `/fig_closeout` and `/fig_e2e_smoke` had command docs, but the README Core commands list omitted them. | Operators can miss important workflow and smoke-test commands even after reading the main README. | Issue 100AA - command surface drift guard |
| G100-23 | P3 | Stale issue status headers | Completed issue docs can still claim implementation is only in a branch or working tree after merge. | Issues 16A, 44, 49, and 50 had stale branch/working-tree status headers. | Future operators can misroute already-mainline work as unfinished branch work. | Issue 100AB - stale issue status guard |
| G100-24 | P1 | Package cleanup safety | The installed-cache package cleanup helper could delete tracked files when accidentally run in a development checkout. | Running `plugin_package_audit.py --clean` in a feature worktree classified tracked `.gitkeep` and golden export paths under `build/`/`exports/` as junk. | A release hygiene command can damage source-controlled fixture artifacts unless tracked paths are protected. | Issue 100AC - package audit tracked-path safety |
| G100-25 | P2 | SVG polish queue triage | `/fig_drive --mode polish` computes `svg_polish_gate` and readiness, but `/fig_queue --mode polish` did not copy those fields into rows or the human-readable table. | A polish-mode queue could show only `run_fig_loop` or `mode_forbidden_action`, hiding whether the blocker was missing checkpoint evidence, `continue_tikz`, crop uncertainty, human gate, or a true ready path. | Operators still had to inspect each fixture's driver JSON individually to understand SVG polish readiness across a corpus. | Issue 100AD - polish queue SVG gate surfacing |
| G100-26 | P3 | SVG polish queue summary | After Issue 100AD, SVG polish gate details were present per row but not aggregated in `summary`. | Corpus-level polish triage still required scanning every row to know how many fixtures were ready, blocked, `continue_tikz`, or blocked by a specific source. | Operators could miss the dominant SVG-polish blocker class across a fixture set. | Issue 100AE - polish queue SVG summary counts |
| G100-27 | P3 | Queue mode docs drift | `/fig_queue` accepts every `fig_driver.MODES` value, but its command doc listed only `authoring`, `review`, `release`, and `polish`. | `fig_driver.MODES` includes `final`, while `commands/fig_queue.md` omitted it from the mode contract and examples. | Operators could miss the final-readiness queue path even though it is supported by code. | Issue 100AF - fig_queue driver-mode documentation guard |
| G100-28 | P3 | Skill command list drift | The README core command list included `/fig_e2e_smoke`, but the agent-facing SKILL quick command list did not. | README and command docs exposed the deterministic smoke harness while the host-agent skill inventory omitted it. | Agents could miss the smoke harness during final plugin/fixture verification even after reading the plugin skill. | Issue 100AG - skill command list drift guard |
| G100-29 | P3 | Run journal continuation docs | `fig_run_journal.py` existed, but README/SKILL continuation guidance still said only to inspect the prior journal as context. | Issue 100J shipped the safe summary helper; `commands/fig_run.md` documented it, but the two highest-traffic docs did not. | Interrupted sessions could still drift into raw journal spelunking or stale command replay instead of live-state continuation. | Issue 100AH - run journal summary doc guard |
| G100-30 | P3 | Gap inventory freshness | The Issue 100 inventory body listed Issues 100AG/AH, but the status header still claimed the roadmap was current only through Issue 100AF; code-surface counts were also stale. | The inventory is the active whole-plugin review ledger, so its own freshness metadata needs a guard. | Future review loops can mis-prioritize if the roadmap appears older than its body or reports stale surface size. | Issue 100AI - gap inventory freshness guard |
| G100-31 | P1 | External finding handoff | `external_vision_review.yaml` could report a fresh external finding without a `conflicts[]` entry, and the loop treated that review as `passed`. | Issue 100K intentionally left external review as optional local evidence, but only explicit host-vs-external conflicts triggered human review. | A second-opinion reviewer could find a new issue that is neither copied into host critique nor surfaced as a human gate. | Issue 100AJ - external finding handoff gate |
| G100-32 | P3 | Gap inventory baseline freshness | The Issue 100 inventory status header was current, but the context section still said the branch baseline was `main` after Issue 99. | Issue 100AI guarded only the header and code-surface counts, leaving another stale roadmap metadata field unguarded. | Future agents could anchor review decisions to an obsolete baseline even though the body lists newer completed work. | Issue 100AK - inventory baseline freshness guard |
| G100-33 | P1 | External review crop-set freshness | `external_vision_review.yaml` hashed reviewed crops, but did not become stale when the current audit-crop manifest later added or removed crop paths. | Issue 100K template binds the initial crop set, but freshness only rechecked files already listed by `reviewed_crops[]`. | A second-opinion review could remain fresh even though a new high-zoom crop was never inspected by the external reviewer. | Issue 100AL - external review crop-set freshness |
| G100-34 | P3 | External finding docs | README and `/fig_critique` docs still described external second-opinion routing in terms of stale or conflicting reviews after unresolved external findings became first-class human-gate evidence. | Issue 100AJ changed loop behavior, but the high-traffic operator docs did not yet name the new unresolved-finding boundary. | Operators could under-use the second-opinion path by thinking only conflicts matter, not standalone new findings. | Issue 100AM - external finding documentation guard |
| G100-35 | P2 | Run journal optional evidence staleness | `fig_run_journal.py` marked journals stale against core fixture and build files, but not newer optional evidence such as `external_vision_review.yaml`. | External reviews, reference packs, aesthetic intent, and detector reports can change the next review route after a run journal was written. | A continuation summary could appear available even though important review evidence changed after the interrupted run. | Issue 100AN - run journal optional evidence staleness |
| G100-36 | P2 | Run journal inspection/SVG polish evidence staleness | Issue 100AN still omitted `inspection_trace.yaml` and SVG polish sidecars from journal staleness checks. | Inspection traces and SVG polish delta/final-artifact sidecars can change after a run journal stops. | A continuation summary could appear available even though host-read accountability or SVG polish evidence changed after the interrupted run. | Issue 100AO - run journal inspection/SVG polish evidence staleness |
| G100-37 | P2 | Run journal declared context staleness | `fig_run_journal.py` still did not consider spec-declared paper-wide aesthetic context or journal art-direction playbook packs stored outside the fixture directory. | `quality_manifest.py` includes declared context/playbook paths in critique input hashing, but the journal helper used only fixed fixture-local paths. | A continuation summary could appear available even though paper-wide or journal-specific art-direction context changed after the interrupted run. | Issue 100AP - run journal declared context pack staleness |
| G100-38 | P2 | Run journal critique input parity | `fig_run_journal.py` still maintained its own stale evidence list instead of reusing the critique input manifest source set. | Reference images, panel reference images, `reference/reference_pack.md`, and shared style lock changes participate in critique freshness but were not guaranteed to stale a prior journal. | An interrupted run could appear resumable even though the next `/fig_critique` would be based on changed reference/style evidence. | Issue 100AQ - run journal critique input parity |
| G100-39 | P2 | Run journal content freshness | `fig_run_journal.py` still used mtime-only stale checks for continuation evidence. | A fixture evidence file can be rewritten while preserving or restoring an older mtime than the run journal. | An interrupted run could appear available even though briefing/spec/evidence content changed since the journal was recorded. | Issue 100AR - run journal evidence hash snapshot |
| G100-40 | P2 | Run journal malformed input safety | Issue 100AR's snapshot writer reused critique input path expansion directly, and malformed `spec.yaml.panels[]` entries could raise while recording a non-authoritative journal. | A scalar panel entry reproduces `AttributeError: 'str' object has no attribute 'get'` through `participating_panel_reference_paths()`. | `/fig_run --record` could fail to write a continuation journal exactly when malformed inputs make recovery context more important. | Issue 100AS - run journal malformed-spec safe snapshot |
| G100-41 | P2 | Run journal new evidence freshness | Issue 100AR compared only files present in the stored snapshot, while the legacy mtime fallback missed newly added evidence files with older mtimes. | A new `spec.yaml` or optional evidence file can be copied in after the journal while preserving an old timestamp. | A continuation summary could appear available even though the current evidence source set contains files that were never present in the recorded run journal. | Issue 100AT - run journal new evidence snapshot gap |
| G100-42 | P2 | Queue fixture path boundary | `/fig_queue` treated explicit fixture arguments as path fragments under `examples/` without rejecting `../` or multi-component names first. | `examples/../outside` can resolve to an existing directory outside `examples/`, allowing the queue to call the driver with an unsafe fixture identity. | Batch queue triage could inspect or route a non-fixture path instead of surfacing an operator error row. | Issue 100AU - queue fixture name boundary |
| G100-43 | P2 | Driver fixture path boundary | `/fig_drive` and `/fig_run` still relied on `examples/<name>` path joining after Issue 100AU fixed only the queue surface. | `fig_driver.build_driver_summary("../outside", ...)` could reach status inference if `examples/../outside` existed, and `fig_run` inherits driver behavior. | Direct single-fixture entrypoints could inspect or plan commands for a non-fixture path instead of failing before workflow routing. | Issue 100AV - driver fixture name boundary |
| G100-44 | P1 | Export fixture path boundary | `/fig_export` still accepted raw fixture names after queue/driver boundary hardening and resolved them as `examples/<name>` before export checks. | `run_export.py ../outside --skip-critique` could reach internal build/export path checks for an escaped path instead of failing at fixture identity validation. | A mutation-capable export command should not rely on downstream path failures to avoid writing outside a declared fixture. | Issue 100AW - export fixture name boundary |
| G100-45 | P1 | Direct fixture command path boundary | `/fig_loop`, `/fig_closeout`, `/fig_e2e_smoke`, and `fig_loop_patch_executor.py` still resolved `examples/<name>` directly instead of sharing the fixture identity boundary. | Unsafe fixture names could reach scratch run writing, status inference, smoke command planning, or patch loop lookup before failing for incidental reasons. | Direct workflow and mutation-capable commands need the same boundary as queue/driver/export so traversal syntax cannot become a fixture identity. | Issue 100AX - direct fixture command boundary |
| G100-46 | P2 | Perception pack path boundary | `perception_pack.py` supports cwd-based figure-directory operation, but still used `name` as a raw filename segment under `build/`. | `build_perception_pack("../outside")` could resolve `build/../outside.pdf` in cwd mode and reset `build/perception/` before any fixture identity error. | A compile-side evidence generator should preserve cwd mode for safe names while rejecting traversal syntax before output reset. | Issue 100AY - perception pack figure name boundary |
| G100-47 | P2 | Spec bbox helper path boundary | `spec_bbox_helper.py` accepted `name` under a custom `--examples-root` without validating that it was a single fixture identity. | `spec_bbox_helper.run(["../outside", "--examples-root", ".../examples"])` could read an escaped TeX file if the normalized path existed. | A geometry-authoring helper should not let traversal syntax become the source of panel reference coordinates. | Issue 100AZ - spec bbox helper fixture name boundary |
| G100-48 | P2 | Detector feedback ledger path boundary | `detector_feedback_ledger.py` accepted selected fixture names without validating that each one was a single fixture identity. | `build_detector_feedback_ledger(examples_root, ["../outside"])` could include an escaped critique directory if the normalized path existed. | Detector tuning and whole-plugin review evidence should not be polluted by traversal-selected non-fixtures. | Issue 100BA - detector feedback ledger fixture name boundary |
| G100-49 | P2 | Run journal continuation path boundary | `fig_run_journal.py` accepted raw fixture names before producing `next_live_commands`. | `fig_run_journal.py ../outside` produced normal JSON with `/fig_status ../outside` and `/fig_drive ../outside ...` commands. | A continuation helper should not generate follow-up commands for traversal syntax. | Issue 100BB - fig run journal fixture name boundary |
| G100-50 | P2 | Run journal writer path boundary | `fig_run_records.write_run_journal()` accepted raw `payload["fixture"]`, sanitized the run directory name, and wrote non-authoritative journal evidence for traversal syntax if called directly. | Tests could bypass the driver boundary by monkeypatching the runner and still record a journal for `../bad/name with spaces`. | A write-capable continuation helper should reject unsafe fixture identity before run directory allocation, evidence snapshotting, or JSON writes. | Issue 100BC - fig run journal writer fixture name boundary |
| G100-51 | P2 | Run journal evidence helper path boundary | `fig_run_evidence.py` exposed shared evidence path/snapshot helpers that resolved raw fixture names under `examples/<name>` without validating the fixture identity itself. | Direct `evidence_snapshot(repo_root, "../outside")` could read existing files outside `examples/` even though normal journal reader/writer paths had been hardened. | Shared continuation-evidence helpers should enforce the same fixture boundary as their callers, so future module reuse cannot reintroduce traversal reads. | Issue 100BD - fig run evidence helper fixture name boundary |
| G100-52 | P2 | Text-boundary helper write path boundary | `text_boundary_spec_helper.py --write` accepted parent-relative relative paths such as `examples/../outside` and could rewrite a normalized `outside/spec.yaml` if it existed. | The helper is usually invoked as `examples/<name> --write`, but its parser also accepted arbitrary path-like input before rejecting traversal syntax. | A write-capable authoring helper should preserve explicit path support while rejecting accidental traversal paths before spec resolution or mutation. | Issue 100BE - text-boundary helper parent-relative path boundary |
| G100-53 | P2 | Diagnostic provenance fixture path boundary | `diagnostic_artifact_provenance.py` accepted traversal-like fixture paths and still emitted normal provenance JSON. | `diagnostic_artifact_provenance.py examples/../outside ... --repo-root <repo>` returned schema-valid output instead of surfacing invalid fixture identity. | A tool that decides whether diagnostic images are authoritative should reject invalid fixture/path inputs instead of making wrong-fixture evidence look like a normal report. | Issue 100BF - diagnostic provenance fixture path boundary |
| G100-54 | P1 | Critique adjudication write path boundary | `critique_adjudication.py scaffold/sync` accepted `examples/../outside` and could reach or write `critique_adjudication.yaml` outside `examples/` before failing for incidental downstream reasons. | TDD reproduced `scaffold examples/../outside --force` exiting 0 and writing an adjudication file when a normalized outside critique existed. | A write-capable human-decision helper must reject unsafe fixture/path syntax before scaffold/sync can mutate or refresh adjudication state. | Issue 100BG - critique adjudication CLI fixture path boundary |
| G100-55 | P2 | Critique lint CLI fixture path boundary | `critique_lint.py` accepted `examples/../outside` and could report `OK: critique lint passed` for a normalized directory outside `examples/`. | TDD reproduced a valid outside `critique.md` returning exit code 0 through the traversal-like CLI path. | A read-only validity gate should not make escaped or malformed fixture identity look like normal plugin truth. | Issue 100BH - critique lint CLI fixture path boundary |
| G100-56 | P1 | Critique brief CLI fixture path boundary | `critique_brief.py` accepted `examples/../outside` and emitted a full host-vision critique brief for the normalized outside directory. | TDD reproduced the CLI printing a complete `# Critique brief` and audit crop list for `examples/../review_demo`. | The host-vision entrypoint must not make an escaped path look like the intended `/fig_critique <name>` target. | Issue 100BI - critique brief CLI fixture path boundary |
| G100-57 | P1 | Status CLI fixture path boundary | `status.py` accepted `examples/../outside` and printed a normal stage/state summary for the normalized outside directory. | TDD reproduced `/fig_status` equivalent output `outside — stage 1/4` for `examples/../outside`. | The canonical first workflow check must not make an escaped path look like normal fixture state. | Issue 100BJ - status CLI fixture path boundary |
| G100-58 | P1 | SVG polish handoff write path boundary | `svg_polish_handoff.py --write` accepted `examples/../outside`, and also accepted an existing single-component relative directory outside `examples/`, then wrote `polish/svg_polish_audit.md` plus `polish/svg_polish_manifest.yaml` there. | TDD reproduced exit code 0 and both handoff files written for traversal-like and existing outside-relative CLI paths. | A final-artifact handoff writer must reject unsafe fixture syntax before writing audit/manifest state outside declared examples. | Issue 100BK - SVG polish handoff CLI fixture path boundary |
| G100-59 | P1 | SVG polish executor write path boundary | `svg_polish_executor.py --write` accepted `examples/../outside`, and also accepted an existing single-component relative directory outside `examples/`, then wrote `polish/<name>.polished.svg` there. | TDD reproduced exit code 0 and an outside polished SVG write for traversal-like and existing outside-relative CLI paths. | The recipe executor is the direct SVG mutation step, so it must reject unsafe fixture syntax before applying recipe operations or writing polished SVG output. | Issue 100BL - SVG polish executor CLI fixture path boundary |
| G100-60 | P2 | SVG polish recipe template write path boundary | `svg_polish_recipe.py --template ... --write-template` accepted `examples/../outside`, and also accepted an existing single-component relative directory outside `examples/`, then wrote `polish/svg_polish_recipe.yaml` there. | TDD reproduced exit code 0 and an outside recipe template write for traversal-like and existing outside-relative CLI paths. | The recipe starter should not create polish workflow state outside declared examples before executor/handoff boundaries run. | Issue 100BM - SVG polish recipe CLI fixture path boundary |
| G100-61 | P2 | External vision review template write path boundary | `external_vision_review.py --template ... --write-template` accepted `examples/../outside`, and also accepted an existing single-component relative directory outside `examples/`, then wrote `external_vision_review.yaml` there. | TDD reproduced exit code 0 and an outside external review template write for traversal-like and existing outside-relative CLI paths. | External second-opinion evidence can influence loop/human gates, so its template writer must not create review state outside declared examples. | Issue 100BN - external vision review CLI fixture path boundary |
| G100-62 | P2 | Subregion iteration log write path boundary | `subregion_iteration_log.py --template --write-template` and `--append` accepted traversal-like or existing outside-relative fixture paths, then wrote or appended `subregion_iteration_log.md` outside `examples/`. | TDD reproduced exit code 0 for `examples/../outside --write-template` and an outside append through `--append outside`. | Subregion logs drive active target context in critique/loop handoff, so helper writes must stay bound to declared examples. | Issue 100BO - subregion iteration log CLI fixture path boundary |
| G100-63 | P2 | Paper-wide context fixture identity boundary | `paper_aesthetic_context.py --template --fixture` and the v1 pack validator accepted unsafe fixture role strings such as `../outside`. | TDD reproduced the CLI writing `figure_roles[].fixture: ../outside` into a reloadable paper-wide context pack, and the loader accepted a hand-authored unsafe role fixture. | Paper-wide style context should not make traversal syntax or non-fixture identities look like valid cross-figure design contract targets. | Issue 100BP - paper aesthetic context fixture identity boundary |
| G100-64 | P2 | Publication scaffold fixture identity boundary | `publication_gate.py` scaffold helpers accepted unsafe fixture strings and embedded them into `QUALITY_AUDIT.md` as `fixture: ../outside`. | TDD reproduced `publication_audit_scaffold_text("../outside")` returning text and `write_publication_audit_scaffold(..., fixture="../outside")` writing a scaffold file. | Publication provenance scaffolds should not normalize traversal syntax or non-fixture identities into accepted/release-adjacent human audit files. | Issue 100BQ - publication scaffold fixture identity boundary |
| G100-65 | P2 | TeX coordinate shift file-type boundary | `tex_coordinate_shift.py --write` accepted any existing file path, not only `.tex`, and could mutate non-TeX files containing coordinate-like text. | TDD reproduced `spec.yaml` being rewritten from `(1.00, 2.00)` to shifted coordinates through the TeX-only helper. | A source authoring helper should fail before mutation when the target is not a TeX source file. | Issue 100BR - TeX coordinate shift suffix boundary |
| G100-66 | P2 | Reference extract path boundary | `reference_extract.py` accepted `spec.yaml.reference_image: ../outside.png` and read a reference image outside the fixture before writing `coordinate_hints.yaml`. | TDD reproduced an outside PNG being consumed and a fixture-local coordinate hints file being written. | Reference-derived authoring evidence must remain bound to the declared fixture; escaped references can make unrelated images look like trusted layout evidence. | Issue 100BS - reference extract path boundary |
| G100-67 | P2 | Reference learning path boundary | `critique_reference_pack.py` validated `reference_learning.references[].path` as a non-empty string but did not reject absolute or parent-relative paths at the pack contract layer. | TDD reproduced `../outside.png` and `/tmp/outside.png` being accepted as valid reference-learning anchors; downstream metrics only skipped them later. | Unsafe reference-learning paths could make a malformed pack look like a missing/skipped metrics issue instead of an invalid contract, weakening reference-aesthetic routing. | Issue 100BT - reference-learning path boundary |
| G100-68 | P1 | SVG semantic diff CLI path boundary | `svg_semantic_diff.py` accepted raw relative fixture paths and could write `polish/svg_semantic_diff.json` outside `examples/` for traversal-like or existing outside-relative paths. | TDD reproduced `examples/../outside` and `outside` returning exit 0 and writing a semantic diff report outside declared fixtures. | A final-artifact semantic safety report should not be creatable for escaped paths before SVG polish status/gates consume it. | Issue 100BU - SVG semantic diff CLI fixture path boundary |
| G100-69 | P1 | Golden artifact gate path boundary | `check_golden_artifacts.py` accepted raw relative fixture paths and could print `OK: golden artifact gates passed` for an existing directory outside `examples/`. | TDD reproduced `examples/../outside` and `outside --no-require-accepted` returning exit 0 for a minimal outside artifact set. | A release-adjacent accepted/golden gate must not certify escaped paths as normal fixture artifacts. | Issue 100BV - golden artifact gate CLI fixture path boundary |
| G100-70 | P1 | Warning-budget gate path boundary | `check_visual_clash_budget.py` accepted raw relative target paths and could print `OK outside: visual_clash total ... <= cap ...` for traversal-like or existing outside-relative directories. | TDD reproduced `examples/../outside` returning exit 0 for an outside fixture-shaped directory. The existing CLI also accepted a single-component `outside` target when that directory existed. | A CI/final-mode warning budget guardrail must only certify the repo `examples/` tree or declared fixtures under it, not arbitrary sibling directories. | Issue 100BW - visual-clash warning budget CLI target boundary |
| G100-71 | P1 | Reference-aesthetic metrics path boundary | `reference_aesthetic_metrics.py` accepted raw relative fixture paths and could write `build/reference_aesthetic_metrics.json` outside `examples/`. | TDD reproduced `examples/../outside` returning exit 0 and writing metrics for an outside fixture-shaped directory. | A reference/aesthetic critique input generator must not produce fresh-looking metrics for escaped paths before critique freshness and routing consume them. | Issue 100BX - reference-aesthetic metrics CLI fixture path boundary |
| G100-72 | P1 | Reference extract CLI path boundary | `reference_extract.py` accepted raw relative fixture paths and could write `coordinate_hints.yaml` outside `examples/`. | TDD reproduced `examples/../outside --ocr-passes 1.0` returning exit 0 and writing outside coordinate hints. | Reference-derived authoring evidence must not be generated for escaped fixture paths before status, critique, and layout-drift consumers treat it as trusted context. | Issue 100BY - reference extract CLI fixture path boundary |
| G100-73 | P2 | Inspection trace CLI path boundary | `inspection_trace.py validate` accepted raw relative fixture paths and could print `valid examples/../outside/inspection_trace.yaml` for a trace outside `examples/`. | TDD reproduced `examples/../outside` returning exit 0 for a valid outside trace. | Crop-read accountability evidence should not be certified for escaped fixture paths before critique/loop consumers trust it as audit proof. | Issue 100BZ - inspection trace CLI fixture path boundary |
| G100-74 | P2 | Layout-drift CLI path boundary | `check_layout_drift.py` accepted raw relative fixture paths and could print a normal-looking `SKIP` for a normalized outside directory. | TDD reproduced `check_layout_drift.py examples/../outside` returning exit 0 for an outside fixture-shaped directory. | A compile-stage layout gate should not make escaped paths look like normal fixture state before status/export consumers rely on coordinate hints. | Issue 100CA - layout drift CLI fixture path boundary |
| G100-75 | P3 | Layout-drift usage docs | After Issue 100CA hardened the CLI, the script docstring and argparse help still described `<example_dir>`, implying arbitrary directories were accepted. | `check_layout_drift.py --help` used the old positional name even though the hardened CLI accepted only fixture name, `examples/<name>`, absolute examples child, or compile-local `.`. | Operators could follow stale usage text and think parent-relative or sibling directories were part of the public contract. | Issue 100CB - layout drift CLI usage doc sync |
| G100-76 | P3 | Inventory file freshness guard | The release-contract guard checked the latest Issue 100 suffix mentioned inside the inventory, but did not compare against the actual issue files on disk. | TDD reproduced the inventory passing while issue files existed through Issue 100CB and the inventory still claimed Issue 100BZ. | The whole-plugin review ledger could silently lag behind completed hardening slices. | Issue 100CC - inventory issue-file freshness guard |
| G100-77 | P3 | Plugin install package hygiene visibility | `plugin_install_freshness.py` could report `state: fresh` while the installed cache still contained generated package junk that `plugin_package_audit.py` would reject. | Live same-version reinstall copied generated build/cache paths, freshness became `fresh`, then package audit failed until the installed cache was cleaned separately. | Operators could believe the installed plugin is fully ready while package hygiene still needs cleanup. | Issue 100CD - plugin install package hygiene summary |
| G100-78 | P3 | Plugin install hygiene exit code | After Issue 100CD surfaced `installed_package_hygiene`, the CLI still exited `0` for `state: fresh` even when hygiene was `dirty`. | TDD reproduced a matching install with `.venv` package junk returning exit code 0 while JSON said `installed_package_hygiene.state: dirty`. | CI or shell operators that only check exit status could still treat a dirty installed plugin cache as ready. | Issue 100CE - plugin install hygiene exit-code guard |
| G100-79 | P3 | Source package hygiene visibility | After Issue 100CE, the installed cache could be fresh+clean while the development plugin tree still contained generated package junk that the next reinstall would copy. | Live `plugin_package_audit.py . --max-mib 300` failed on the source tree while `plugin_install_freshness.py` exited 0 because it checked only installed hygiene. | Operators could clean the installed cache, see readiness pass, then reintroduce the same package junk on the next same-version reinstall. | Issue 100CF - source package hygiene guard |
| G100-80 | P3 | Plugin hygiene next-action quoting | Issue 100CF emitted a source cleanup `next_action` containing the repo path `/Users/.../[figure-agent]/...` without shell quoting. | Live zsh execution failed with `no matches found: /Users/.../[figure-agent]/plugins/figure-agent`; TDD reproduced shell-special paths in source and installed hygiene commands. | Operators could follow the emitted cleanup command and fail before reaching the actual package hygiene fix. | Issue 100CG - plugin hygiene next-action quoting |
| G100-81 | P3 | Inventory completion summary freshness | The Issue 100 header/table tracked through Issue 100CG, but the Recommended Execution Order completion summaries stopped at Issue 100BS. | TDD reproduced the release-contract guard passing header/baseline freshness while the completion-summary section lacked the latest Issue 100 suffix. | Operators could use the inventory as a status briefing and miss already-completed hardening slices after 100BS. | Issue 100CH - inventory completion-summary guard |
| G100-82 | P3 | Stale issue-status recurrence | Issue 100P/100AB swept stale branch-status wording, but the guard only caught `implemented on branch` and `implemented in working tree`; later Issues 100BV-100CH used `implemented in branch` and stayed stale after merge. | TDD reproduced `test_completed_issue_headers_do_not_claim_branch_or_worktree_only` passing while 13 Issue 100 headers still claimed branch implementation. | Operators could read merged work as branch-only work even though the roadmap and git history said it was already on main. | Issue 100CI - stale issue-status recurrence guard |
| G100-83 | P3 | Source git hygiene visibility | `plugin_install_freshness.py` could report `state: fresh`, source package hygiene `clean`, and installed package hygiene `clean` while the development plugin tree still had uncommitted tracked changes that had been copied into the installed cache. | Live reproduction: user-edited `examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex` was byte-identical in the installed cache, yet freshness exited 0 because payload hashing excludes `examples/` and package hygiene only detects generated junk. | Dirty user figure-source work can be installed as "fresh" plugin state, confusing Claude cache truth and release/operator checks. | Issue 100CJ - source git hygiene guard |
| G100-84 | P3 | Install freshness next-action precedence | After Issue 100CJ, `plugin_install_freshness.py` could exit nonzero for dirty source git or dirty installed package hygiene while the top-level `next_action` still said the install matched or recommended reinstall. | TDD reproduced fresh payloads with dirty source git and dirty installed package hygiene where exit code was 1 but top-level `next_action` did not point at the blocking hygiene action. | Operators could copy the wrong top-level action and reinstall or stop early instead of fixing the actual readiness blocker. | Issue 100CK - install next-action precedence guard |
| G100-85 | P3 | Installed example-source drift | Payload freshness intentionally excludes `examples/`, but installed cache examples can still be stale or dirty while payload/package/source hygiene all look clean. | TDD reproduced source and installed `examples/demo/demo.tex` differing while `state: fresh` and `changed_files: []`; the old CLI exited 0. | Claude can read or copy stale installed example sources while the install diagnostic claims readiness. | Issue 100CL - installed example-source hygiene guard |
| G100-86 | P3 | Marketplace source-path mismatch | `plugin_install_freshness.py` could be run from a clean feature worktree while raw `claude plugin install figure-agent@figure-agent-local` still installed from the registered `figure-agent-local` marketplace source, which may point at a different checkout. | Live Claude config inspection showed `figure-agent-local` is resolved from `~/.claude/plugins/known_marketplaces.json`, not from the current shell directory. | Operators could review a clean worktree, run the printed install command, and copy a dirty or stale registered source into the installed plugin cache. | Issue 100CM - marketplace source hygiene guard |
| G100-87 | P3 | Inventory next-analysis freshness | The Issue 100 header/table tracked through Issue 100CM, but the `Additional Update Analysis` section still told operators that the next urgent slices were Issue 100A and Issue 100B/C. | TDD reproduced the release-contract guard passing while that analysis section did not mention the latest Issue 100 suffix and still carried stale 100A-C recommendation text. | Operators could use the inventory as a live roadmap and restart already-implemented work instead of moving to the current post-100CM gap. | Issue 100CN - inventory next-analysis freshness guard |
| G100-88 | P1 | Mode-scoped completion ambiguity | `/fig_drive --mode authoring` and review-mode clean checkpoints could return `action: complete` with generic guidance that no required plugin action remained for the selected mode. | TDD reproduced authoring/review complete states that did not explicitly point to review/release/final follow-up, even though users repeatedly asked why the agent said a figure was complete. | Operators could read a mode-local completion as whole-figure, release, or art-direction completion and stop before the next broader gate. | Issue 100CO - mode-scoped completion guidance |
| G100-89 | P2 | Polish prerequisite gate mismatch | In clean checkouts with ignored build artifacts absent, `/fig_drive --mode polish` correctly returned `action: run_compile`, but additive `svg_polish_gate.next_action` still said `rerun_fig_loop` through the generic no-current-checkpoint path. | Live queue reproduction showed all real fixtures at `run_compile` while SVG-specific queue columns said `svg_polish_next_action: rerun_fig_loop`. TDD reproduced render-missing and export-missing polish modes. | Operators could follow the SVG-specific column and skip the actual first prerequisite before any loop checkpoint can prove SVG readiness. | Issue 100CP - polish prerequisite gate alignment |
| G100-90 | P2 | SVG polish readiness filtering | `/fig_queue --mode polish` surfaced SVG gate/readiness fields, but operators still had to hand-filter JSON to find ready fixtures or a specific blocker source. | After Issue 100CP, the next real-fixture SVG promotion evidence query was still manual: `can_start_svg_polish` existed as a row field but not as a supported filter. | Positive-route evidence remains harder to reproduce, and operators can miss a ready candidate or blocker cluster in a large fixture set. | Issue 100CQ - SVG polish queue readiness filters |
| G100-91 | P2 | SVG polish gate blocker-source projection | Issue 100CQ's `--svg-polish-blocking-source` filter matched readiness blocker sources, but not gate-only blocker sources such as `driver_blocker` on no-current-checkpoint rows. | The Issue 100CR evidence pass produced three `svg_polish_gate_state: no_current_checkpoint` rows, then `--svg-polish-blocking-source driver_blocker` returned zero rows until the projection was fixed. | Operators could still miss why no real fixture was ready for SVG polish when the blocker lived in `svg_polish_gate.blocking_items` instead of `svg_polish_readiness`. | Issue 100CR - SVG polish gate blocker-source filters |
| G100-92 | P3 | Queue-run SVG filter parity | `/fig_queue` supported SVG polish readiness filters, but `/fig_queue_run` still accepted only actor/action/status filters despite claiming to share the same filter surface. | TDD reproduced `fig_queue_run.py --mode polish --can-start-svg-polish true --svg-polish-blocking-source driver_prerequisite` failing at argparse before it could plan queue execution. | Operators could inspect SVG readiness with `/fig_queue` but then lose the same filter when moving to plan-only bounded queue execution. | Issue 100CS - queue-run SVG filter parity |
| G100-93 | P3 | Inventory version consistency | The Issue 100 Documentation Consistency Check still claimed README/plugin manifest identified the plugin as v0.9.1 after the live release metadata had moved to v0.9.2. | TDD reproduced the release-contract suite not checking the inventory's version sentence even though it already checked README, pyproject, and plugin manifest versions. | The main roadmap could give stale release-readiness evidence even while the actual release metadata was correct. | Issue 100CT - inventory version consistency guard |
| G100-94 | P3 | Queue-run filter drift recurrence | Issue 100CS copied the current queue filters into `/fig_queue_run`, but there was no parity guard proving future `/fig_queue` filter additions are mirrored in the runner. | TDD reproduced that `fig_queue_run` had no declared filter-surface constant to compare against `fig_queue._FILTER_KEYS`. | The same filter drift could recur whenever `/fig_queue` grows a new filter, sending operators back to manual JSON filtering. | Issue 100CU - queue-run filter surface guard |
| G100-95 | P3 | JSON/dry-run CLI compatibility | `fig_driver.py` and `fig_queue_run.py` emit JSON by default, but rejected reasonable explicit `--json` flags; `fig_queue_run.py` also rejected `--dry-run` even though it is plan-only unless `--execute` is supplied. | Live post-100CU SVG polish evidence pass hit argparse errors on `fig_driver.py ... --dry-run --json` and `fig_queue_run.py ... --dry-run --json`; TDD reproduced both. | Operators and agents can fail before reaching the actual evidence path simply by adding explicit output/dry-run flags that work conceptually for these commands. | Issue 100CV - JSON/dry-run CLI compatibility aliases |
| G100-96 | P3 | Package audit evidence preservation | `plugin_package_audit.py --clean` correctly removed package junk, but the same broad cleanup erased freshly compiled fixture `build/` and `exports/` evidence during development review loops. | Live SVG-polish promotion work compiled fixtures, then default package cleanup removed the generated evidence before the next queue/driver inspection. | Operators need a way to clean `.venv` and tool caches without destroying the local render/export evidence they are actively reviewing. | Issue 100CW - package audit evidence-preserving clean |
| G100-97 | P3 | Queue output flag compatibility | `/fig_queue` supported `--json`, but rejected the common `--format json` spelling when an operator tried to inspect polish readiness as JSON. | Live command `fig_queue.py --mode polish --format json` failed with `unrecognized arguments: --format`; TDD reproduced the argparse failure. | Operators can fail before queue evidence appears just by choosing a common output flag spelling. | Issue 100CX - fig_queue format-json compatibility |
| G100-98 | P3 | Queue-run output flag compatibility | `/fig_queue_run` emits JSON and accepts `--json`, but rejected `--format json` during plan-only polish queue continuation. | Live command `fig_queue_run.py --mode polish --goal "inspect" --format json --dry-run` failed with `unrecognized arguments: --format`; TDD reproduced the argparse failure. | Operators can fail before queue-run plan evidence appears just by using the same output flag spelling that `/fig_queue` now accepts. | Issue 100CY - fig_queue-run format-json compatibility |
| G100-99 | P3 | Driver/run output flag compatibility | After queue commands accepted `--format json`, adjacent single-fixture commands `fig_driver.py` and `fig_run.py` still rejected the same JSON-output spelling. | Live commands `fig_driver.py ... --format json` and `fig_run.py ... --format json` failed at argparse; TDD reproduced both. | Operators can move from queue to single-fixture driver/run and hit another needless output-flag trap before seeing the real boundary state. | Issue 100CZ - driver/run format-json compatibility |
| G100-100 | P3 | Loop/closeout output flag compatibility | `/fig_loop` and `/fig_closeout` had automation JSON paths via `--json`, but rejected the same `--format json` spelling now accepted by queue, queue-run, driver, and run. | Live commands `fig_loop.py ... --format json` and `fig_closeout.py ... --format json` failed at argparse; TDD reproduced both. | Operators can still hit an output-flag trap at the verify-only checkpoint or post-patch closeout stage. | Issue 100DA - loop/closeout format-json compatibility |
| G100-101 | P3 | Helper output flag compatibility | Documented helper parsers `subregion_active_set.py` and `reference_pack.py` had stdout JSON paths via `--json`, but rejected the same `--format json` spelling as the primary workflow commands. | TDD reproduced both helper CLIs failing with `unrecognized arguments: --format json`. | Operators can still hit the same output-flag trap when inspecting subregion active sets or role-typed reference packs. | Issue 100DB - helper format-json compatibility |
| G100-102 | P2 | Status JSON argument contract | `/fig_status` is the canonical first check, but `status.py <fixture> --json` silently ignored `--json` and printed prose because `main()` only inspected `sys.argv[1]`. | Live command `status.py fig1_overview_v2_pair_001_vault --json` printed text; TDD reproduced JSON parsing failure. | Automation can believe it requested machine-readable state while receiving prose, corrupting the traffic-controller entry point. | Issue 100DC - status JSON CLI contract |
| G100-103 | P3 | Improve output flag compatibility | `/fig_improve` emits JSON by default but rejected explicit `--json` and `--format json` spellings. | TDD reproduced `fig_improve.py ... --format json` failing with `unrecognized arguments`. | Operators using the loop-centered entrypoint can still hit a parser trap before seeing the real improvement boundary. | Issue 100DD - fig_improve JSON flag compatibility |
| G100-104 | P2 | Critique brief CLI argument contract | `critique_brief.py` read only `sys.argv[1]`, so unknown extra arguments were silently ignored while still emitting a full host-vision brief. | TDD reproduced `critique_brief.py examples/<fixture> --bogus` producing a brief instead of failing. | Operators can believe a host-critique option was applied when the generated audit prompt ignored it. | Issue 100DE - critique brief CLI argument contract |
| G100-105 | P3 | Match snippet CLI help contract | `match_snippet.py --help` was treated as a missing briefing file because the helper used manual argv counting. | Live command printed `missing: --help`; TDD reproduced missing argparse help and unknown-argument handling. | Operators cannot discover helper usage normally, and parser behavior remains inconsistent with the hardened workflow surface. | Issue 100DF - match_snippet CLI help contract |
| G100-106 | P3 | Plugin install freshness output flag compatibility | `plugin_install_freshness.py` emits JSON by default but rejected explicit `--json` and `--format json` spellings. | Live commands failed at argparse; TDD reproduced both no-op output flags failing. | Operators checking "am I using the newest plugin?" can hit a parser trap before seeing the real source/install hygiene state. | Issue 100DG - plugin install freshness JSON flag compatibility |
| G100-107 | P3 | JSON evidence-helper output flag compatibility | `fig_run_journal.py`, `detector_feedback_ledger.py`, and `diagnostic_artifact_provenance.py` emit JSON by default but rejected explicit `--json` and `--format json` spellings. | TDD reproduced all three helper CLIs failing at argparse on explicit JSON-output flags. | Operators can hit a parser trap while checking interrupted-run continuation, detector tuning evidence, or scratch-artifact provenance. | Issue 100DH - JSON evidence-helper flag compatibility |
| G100-108 | P3 | JSON smoke/patch/harness output flag compatibility | `fig_e2e_smoke.py`, `fig_loop_patch_executor.py`, and `svg_polish_positive_harness.py` emit JSON by default but rejected explicit `--json` and `--format json` spellings. | TDD reproduced all three CLIs failing at argparse on explicit JSON-output flags. | Operators can hit the same parser trap while running deterministic smoke, explicit patch closeout, or SVG-polish plumbing evidence. | Issue 100DI - JSON smoke/patch/harness flag compatibility |
| G100-109 | P2 | Queue completion guidance projection | `/fig_drive` complete states carried mode-scoped `operator_guidance`, but `/fig_queue` dropped that guidance from compact rows, table output, and command-plan handoff. | TDD reproduced authoring complete rows with no `operator_guidance`, no `--mode review` next-step text in the queue table, and generic command-plan handoff. | Operators could read multi-fixture queue `complete` rows as whole-figure completion and stop before broader review/release/final gates. | Issue 100DJ - queue operator-guidance projection |
| G100-110 | P2 | Polish release-boundary gate mismatch | Polish mode could stop at `accepted_or_final_ready_required` while additive SVG columns still said `no_current_checkpoint` / `rerun_fig_loop`. | Live `fig5_floating_clip_mechanism` polish queue row showed `required_actor: release_operator` but `svg_polish_next_action: rerun_fig_loop`; TDD reproduced the not-accepted missing-export edge case. | Operators could follow SVG-specific columns and rerun the loop even though release/accepted/final/publication boundary was authoritative. | Issue 100DK - polish release-boundary gate alignment |
| G100-111 | P3 | Polish next-action summary visibility | `/fig_queue --mode polish` rows exposed `svg_polish_next_action`, but the summary did not aggregate those values. | Live polish queue had `run_fig_critique`, `run_fig_compile`, `rerun_fig_loop`, and `resolve_release_boundary` row values while summary omitted `by_svg_polish_next_action`; TDD reproduced the missing summary key. | Operators still had to scan rows manually to know the corpus-level SVG next-action distribution. | Issue 100DL - polish next-action summary counts |
| G100-112 | P3 | Polish blocking-source doc drift | `/fig_queue` row docs said SVG blocking sources merge gate and readiness blockers, but the summary docs still described readiness-only blocker sources. | TDD reproduced the `/fig_queue` summary contract lacking `gate/readiness` wording even though implementation counts both sources. | Future operators or agents could misunderstand `by_svg_polish_blocking_source` and miss gate-only blockers. | Issue 100DM - polish blocking-source doc guard |
| G100-113 | P3 | Queue table summary visibility | `/fig_queue` JSON summary exposed grouped counts, but the default human-readable table printed only `summary total=... errors=...`. | Live polish queue showed 4 host critiques, 1 compile prerequisite, 2 loop reruns, and 1 release-boundary row in JSON, while table output hid those corpus-level counts. | Operators using the default table still had to scan rows manually or switch to JSON to know the dominant next action. | Issue 100DN - queue table summary counts |
| G100-114 | P2 | Queue-run execute/dry-run ambiguity | `/fig_queue_run` accepted both `--execute` and `--dry-run`, then silently executed because only `args.execute` controlled mutation. | TDD reproduced `--execute --dry-run` returning exit 0 and calling the workflow runner. | A user or agent intending a dry run could accidentally trigger bounded workflow execution. | Issue 100DO - queue-run execute/dry-run conflict |
| G100-115 | P3 | Complete row blocker-source noise | Mode-scoped `complete` rows preserved broader next-step guidance, but still contributed `blocking_source: driver.action` to queue summaries. | Live authoring queue showed seven complete rows and one compile row, but `by_blocking_source` reported `driver.action:8`. | Completion clusters could look like blocker clusters, making operator triage noisier. | Issue 100DP - complete row blocking-source cleanup |
| G100-116 | P2 | Command-plan complete rows counted as blocked | After Issue 100DP, table/summary attribution was fixed, but `command_plan.blocked` still contained mode-scoped complete rows. | Live authoring command-plan JSON reported `blocked_count: 7` for seven local complete rows, each with `reason: required_actor:none`. | Batch planning JSON could still make local completion look like blocked automation. | Issue 100DQ - command-plan complete bucket |
| G100-117 | P3 | Queue-run complete rows hidden from summary | After Issue 100DQ, `/fig_queue_run` embedded `queue.command_plan.complete` but its top-level `summary` still omitted a complete-row count. | TDD reproduced a command plan with `complete_count: 1` where queue-run summary exposed planned executable and blocked counts but no `planned_complete`. | Plan-only batch output could make mode-scoped completion disappear unless the operator inspected nested command-plan JSON. | Issue 100DR - queue-run complete summary |
| G100-118 | P3 | First-blocker summary context ambiguity | Complete rows no longer counted as blocked, but live authoring dogfood still showed `by_first_blocker=critique_stale:4...` because `first_blocker` is global status context. | Live table/JSON after Issue 100DR had `complete:7`, `blocked_count:0`, and `planned_complete:7`, while `by_first_blocker` still included broader workflow blockers. | Operators could read status-context first blockers as selected-mode blocked-row counts unless docs name the distinction. | Issue 100DS - first-blocker status context |
| G100-119 | P2 | Polish mode-forbidden guidance contradiction | `/fig_driver --mode polish` could return `stop_boundary: mode_forbidden_action` while `operator_guidance.next_step` still said to run the selected `fig_loop` command. | Live `fig3_trapping_concept` and `smoke_trap_demo` polish driver output showed no-current-checkpoint rows with mode-forbidden stop boundaries and "Run the selected command" guidance. | Single-fixture driver JSON contradicted itself and could send operators to run a command the current mode declares non-executable. | Issue 100DT - polish mode-forbidden guidance |
| G100-120 | P3 | Fig-run explicit JSON flag compatibility | `/fig_run` emitted JSON by default and accepted `--format json`, but rejected the adjacent `--json` spelling used by other JSON-first workflow commands. | TDD reproduced `fig_run.py ... --json` failing with `unrecognized arguments: --json`. | Operators can hit a parser trap when switching from `/fig_drive`, `/fig_queue_run`, or `/fig_improve` to the bounded runner and carrying the explicit JSON flag habit. | Issue 100DU - fig_run json flag compatibility |
| G100-121 | P1 | Better-drawing search layer | The plugin could block stale/unsafe figures and propose narrow quality patches, but it lacked a first-class way to explore multiple bounded alternatives before source mutation. | The reference-aware candidate-search slice adds intent/candidate/render/rank/review/apply-boundary modules, CLI commands, MCP read-only tools, release-gate coverage, and synthetic dogfood. | Figure-agent can now make "better drawing" measurable as candidate evidence and ranking, while accepted/golden and semantic changes remain human-gated. | Reference-aware candidate-search vertical slice |

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

15. **Issue 100Z - schema map drift guard**
    Implemented as a release-contract guard over `scripts/*.py` schema
    constants. `tests/test_release_contract.py` now fails when a
    `figure-agent.*` `SCHEMA` / `*_SCHEMA` constant is missing from the
    schema/module map, with critique lineage shorthand preserved.

16. **Issue 100N/O - freshness and detector feedback**
    Completed on main in commit `d50da39`; merged by `5a51be3`. Added
    read-only `critique_freshness` diagnostics to status output and
    `detector_feedback` counts to audit evidence so stale critique causes and
    detector tuning signals are visible without changing gates or mutating
    fixture state.

17. **Issue 100X - detector feedback ledger**
    Implemented as a read-only cross-fixture diagnostic. Added
    `scripts/detector_feedback_ledger.py` to aggregate existing
    `audit_evidence_summary.py` detector feedback across selected fixtures or
    all critiques under `examples/`. The ledger reports detector totals and
    fixture-qualified unlinked micro-defect ids without changing thresholds,
    critique schema, or release gates.

18. **Issue 100W - plugin install freshness check**
    Implemented as a read-only operator diagnostic. Added
    `scripts/plugin_install_freshness.py` to compare the development plugin
    tree with the latest local Claude plugin cache, ignore generated package
    junk, and report fresh/stale/missing/invalid JSON with changed, missing, and
    extra file lists.

19. **Issue 100Y - same-version install refresh guidance**
    Implemented as an additive `plugin_install_freshness.py` UX fix. The
    diagnostic now reports source/install versions plus `refresh_strategy`, and
    recommends uninstall + install when source and installed cache have the same
    version but different payloads. Different-version stale caches still
    recommend `claude plugin update`.

20. **Issue 100AA - command surface drift guard**
    Implemented as a release-contract documentation guard. README Core commands
    now names every `commands/fig_*.md` slash command, including `/fig_closeout`
    and `/fig_e2e_smoke`, and `tests/test_release_contract.py` fails when a new
    command doc is added without README command-surface review.

21. **Issue 100AB - stale issue status guard**
    Implemented as a broader release-contract documentation guard. Completed
    issue headers may no longer claim `implemented on branch` or
    `implemented in working tree`; Issues 16A, 44, 49, and 50 were normalized to
    mainline truth.

22. **Issue 100AC - package audit tracked-path safety**
    Implemented as an operations-safety fix. `plugin_package_audit.py --clean`
    still removes generated junk from installed plugin caches, but when run
    inside a development git worktree it protects tracked files and directories
    containing tracked files.

23. **Issue 100P - stale issue status sweep**
    Completed as a docs-only sweep. Swept current Issue 100 headers for
    `pending commit`, `pending merge`, and branch-only stale status markers.
    Updated 100F/100G from pending-commit to completed main commits and
    normalized already-merged 100E/100R/100J/100H-I/100N-O headers to main
    commit references.

24. **Issue 100T/U - evidence trace and human-decision diff**
    Completed as an auditability hardening slice. Added optional
    `inspection_trace.yaml` parser/validator + CLI, wired present traces into
    `critique_lint.py`, and added `critique_adjudication.py sync --preview`
    for a read-only preserved/dropped/added/shape-changed decision diff before
    operators choose normal sync or force-scaffold.

25. **Issue 100Q - critique entity consistency lint**
    Completed as a conservative critique-lint hardening slice.
    `critique_lint.py` now blocks matched symbolic label-target audit entries
    whose entity token is absent from active TeX or appears only in comments.
    This closes the narrow phantom-entity gap without attempting broad visual
    OCR or natural-language object detection.

26. **Issue 100S - final strict profile and warning budgets**
    Completed as a final-mode warning-budget hardening slice. Reused
    `spec.yaml.visual_clash_cap` and `build/visual_clash.json` as
    `figure-agent.warning-budget.v1`; `/fig_drive --mode final` now requests
    strict compile when the report is missing and stops at a human gate when
    visual-clash warnings exceed the reviewed fixture cap.

27. **Issue 100AD - polish queue SVG gate surfacing**
    Completed as an operator-triage hardening slice. `/fig_queue --mode polish`
    now copies `svg_polish_gate` and `svg_polish_readiness` fields from
    `/fig_drive` into queue rows, and the table view adds SVG-specific columns
    when those fields are present. This keeps SVG polish conservative while
    making corpus-level blockers visible without per-fixture driver JSON.

28. **Issue 100AE - polish queue SVG summary counts**
    Completed as a corpus-triage hardening slice. `/fig_queue --mode polish`
    now aggregates SVG gate state, recommended path, and readiness blocker
    sources under summary counts when those row fields are present, so the queue
    can identify dominant polish blockers without weakening readiness policy.

29. **Issue 100AF - fig_queue driver-mode documentation guard**
    Completed as a release-contract docs guard. `/fig_queue` docs now list the
    full `fig_driver.MODES` set, including `final`, and the release contract
    test fails if future driver modes are added without queue documentation.

30. **Issue 100AG - skill command list drift guard**
    Completed as a command-surface docs guard. The SKILL quick command list now
    names `/fig_e2e_smoke`, and the release contract test fails if README core
    commands are missing from the agent-facing skill inventory.

31. **Issue 100AH - run journal summary doc guard**
    Completed as a continuation-UX docs guard. README and SKILL now point
    interrupted `/fig_run` sessions to `fig_run_journal.py`, and the release
    contract test fails if either doc stops naming the safe summary helper or
    the no-replay boundary.

32. **Issue 100AI - gap inventory freshness guard**
    Completed as a roadmap-hygiene docs guard. The Issue 100 status header and
    code-surface counts now track the current document/body and repository tree
    through a release-contract test.

33. **Issue 100AJ - external finding handoff gate**
    Completed as an external-review routing guard. Fresh external findings now
    become unresolved `needs_human` evidence unless explicitly marked
    `accept_simplification`, and `/fig_loop` names the active external finding
    in its human-gate recommendation.

34. **Issue 100AK - inventory baseline freshness guard**
    Completed as a roadmap-hygiene guard. The Issue 100 branch-baseline line
    now tracks the latest Issue 100 suffix through the same release-contract
    test that protects the status header and code-surface counts.

35. **Issue 100AL - external review crop-set freshness**
    Completed as a crop-manifest freshness guard. External second-opinion
    reviews now become stale when the current audit-crop manifest adds or
    removes crop paths that were not represented in `reviewed_crops[]`.

36. **Issue 100AM - external finding documentation guard**
    Completed as a high-traffic docs guard. README and `/fig_critique` now say
    external unresolved findings become human-gate evidence, and the release
    contract fails if either doc drops that boundary.

37. **Issue 100AN - run journal optional evidence staleness**
    Completed as a continuation-safety guard. `fig_run_journal.py` now marks a
    prior journal stale when newer optional critique/evidence inputs such as
    `external_vision_review.yaml`, reference packs, aesthetic intent, or build
    detector reports appear after the journal.

38. **Issue 100AO - run journal inspection/SVG polish evidence staleness**
    Completed as a continuation-safety guard. `fig_run_journal.py` now also
    marks a prior journal stale when newer host-read accountability evidence or
    SVG polish sidecars appear after the journal.

39. **Issue 100AP - run journal declared context pack staleness**
    Completed as a continuation-safety guard. `fig_run_journal.py` now reads
    `spec.yaml` best-effort and marks a prior journal stale when declared
    paper-wide aesthetic context or journal art-direction playbook packs change
    after the journal.

40. **Issue 100AQ - run journal critique input parity**
    Completed as a continuation-safety guard. `fig_run_journal.py` now reuses
    `quality_manifest.critique_manifest_paths()` so reference, panel reference,
    authoring reference-pack, style-lock, and future shared critique input paths
    stale prior journals through the same source set used by critique freshness.

41. **Issue 100AR - run journal evidence hash snapshot**
    Completed as a continuation-safety guard. `fig_run_records.py` now stores a
    non-authoritative `evidence_snapshot` of repo-relative sha256 entries, and
    `fig_run_journal.py` marks a journal stale when a snapshotted file changes
    content even if its mtime is older than the journal.

42. **Issue 100AS - run journal malformed-spec safe snapshot**
    Completed as a malformed-input hardening slice. Snapshot generation now
    treats critique input expansion as best-effort: malformed spec shape errors
    skip only optional manifest expansion while preserving core fixture evidence
    snapshot recording.

43. **Issue 100AT - run journal new evidence snapshot gap**
    Completed as continuation freshness hardening. For journals with
    `evidence_snapshot`, `fig_run_journal.py` now compares the current evidence
    source set with recorded snapshot paths and marks newly present evidence
    files stale even when their mtime is older than the journal.

44. **Issue 100AU - queue fixture name boundary**
    Completed as queue safety hardening. Explicit `/fig_queue` fixture
    arguments are now validated as non-empty single relative path components
    before driver invocation; unsafe names surface as blocked
    `unsafe_fixture_name` rows.

45. **Issue 100AV - driver fixture name boundary**
    Completed as direct-entrypoint safety hardening. `/fig_drive` now validates
    fixture names before status inference or command planning, and `/fig_run`
    inherits the same controlled error path instead of letting traversal syntax
    become a fixture identity. `/fig_queue` reuses the same driver-side policy
    so the queue and direct-entrypoint boundaries stay aligned.

46. **Issue 100AW - export fixture name boundary**
    Completed as export safety hardening. Added shared fixture identity helpers
    and made `/fig_export` reject unsafe fixture names before critique, export,
    build-PDF, or regeneration checks. `/fig_drive` and `/fig_queue` use the
    same policy to prevent path-boundary drift.

47. **Issue 100AX - direct fixture command boundary**
    Completed as direct command safety hardening. `/fig_loop`, `/fig_closeout`,
    `/fig_e2e_smoke`, and `fig_loop_patch_executor.py` now reject unsafe fixture
    names before scratch writes, status inference, smoke command planning, or
    patch loop lookup. `perception_pack.py` remains a separate design question
    because it supports cwd-based figure-directory operation.

48. **Issue 100AY - perception pack figure name boundary**
    Completed as compile-side evidence safety hardening. `perception_pack.py`
    now preserves cwd-based operation for safe single-component figure names,
    but rejects absolute, parent-relative, or multi-component names before
    resolving build PDFs/PNGs or resetting `build/perception/`. The CLI reports
    unsafe figure names as controlled errors without masking other runtime
    failures.

49. **Issue 100AZ - spec bbox helper fixture name boundary**
    Completed as helper safety hardening. `spec_bbox_helper.py` now preserves
    custom `--examples-root` operation for safe single-component fixture names,
    but rejects absolute, parent-relative, or multi-component names before
    resolving the source TeX file used to derive panel `bbox_pdf_cm` values.

50. **Issue 100BA - detector feedback ledger fixture name boundary**
    Completed as diagnostic safety hardening. Explicit selected fixture names
    in `detector_feedback_ledger.py` now share the common fixture identity
    validator before any directory lookup. Default all-fixture scanning still
    reads direct child directories under `examples_root`, but skips symlinked
    entries whose resolved path escapes the examples root.

51. **Issue 100BB - fig run journal fixture name boundary**
    Completed as continuation safety hardening. `fig_run_journal.py` now
    validates fixture names before journal lookup or `next_live_commands`
    generation, and the CLI reports unsafe names through a controlled non-zero
    error instead of emitting follow-up commands for traversal syntax.

52. **Issue 100BC - fig run journal writer fixture name boundary**
    Completed as continuation safety hardening. `fig_run_records.py` now
    validates `payload["fixture"]` before allocating a run directory, computing
    an evidence snapshot, or writing non-authoritative journal JSON. `/fig_run`
    keeps its existing live-payload behavior by reporting writer validation
    failures as `journal_error` when a caller bypasses the normal driver-side
    fixture boundary.

53. **Issue 100BD - fig run evidence helper fixture name boundary**
    Completed as shared-helper safety hardening. `fig_run_evidence.py` now
    validates fixture identity inside the evidence path and stale-snapshot
    helpers themselves, so direct helper reuse cannot read traversal-selected
    files outside `examples/` even if a future caller forgets the normal driver
    or journal validation precondition.

54. **Issue 100BE - text-boundary helper parent-relative path boundary**
    Completed as authoring-helper safety hardening. `text_boundary_spec_helper.py`
    still supports `examples/<name>`, `examples/<name>/spec.yaml`, and absolute
    explicit paths, but rejects relative paths containing `..` before resolving
    or rewriting `spec.yaml`.

55. **Issue 100BF - diagnostic provenance fixture path boundary**
    Completed as evidence-provenance safety hardening.
    `diagnostic_artifact_provenance.py` now resolves fixture input through a
    CLI-only boundary that accepts fixture names, `examples/<name>`, or direct
    absolute children of `<repo-root>/examples`, and rejects traversal-like or
    nested fixture paths before emitting authoritative/diagnostic classifications.

56. **Issue 100BG - critique adjudication CLI fixture path boundary**
    Completed as mutation-surface safety hardening. `critique_adjudication.py`
    scaffold/sync now resolve CLI fixture input through the same narrow boundary
    used by diagnostic provenance: fixture name, `examples/<name>`, or a direct
    absolute child of `<repo-root>/examples`. Traversal-like or nested fixture
    paths are rejected before any adjudication scaffold/sync write.

57. **Issue 100BH - critique lint CLI fixture path boundary**
    Completed as read-only gate safety hardening. `critique_lint.py` now rejects
    traversal-like, nested, and invalid fixture inputs before running lint, while
    preserving fixture-name, `examples/<name>`, and explicit absolute-path
    invocation. Invalid input is reported as a normal BLOCKER
    `critique_contract` CLI result instead of an OK lint result or traceback.

58. **Issue 100BI - critique brief CLI fixture path boundary**
    Completed as host-critique input safety hardening. `critique_brief.py` now
    validates CLI fixture-like input before generating the host LLM brief:
    fixture names and `examples/<name>` remain valid, explicit absolute paths
    remain valid for tests/ad hoc review, and traversal-like or nested relative
    paths fail with a controlled `invalid fixture path` error before a brief is
    emitted.

59. **Issue 100BJ - status CLI fixture path boundary**
    Completed as canonical-status safety hardening. `status.py` now validates
    single-figure CLI fixture input before computing the state vector: fixture
    names, `examples/<name>`, and explicit absolute paths remain valid, while
    traversal-like or nested relative paths fail with a controlled
    `invalid fixture path` error before a stage/status summary is printed.

60. **Issue 100BK - SVG polish handoff CLI fixture path boundary**
    Completed as final-artifact handoff safety hardening. `svg_polish_handoff.py`
    now validates CLI fixture input before dry-run validation or `--write`:
    fixture names resolve under `examples/<name>`, `examples/<name>` remains
    valid, and explicit absolute paths remain valid. Traversal-like, nested, or
    existing outside-relative paths fail with a controlled `invalid fixture path`
    error before `polish/svg_polish_audit.md` or
    `polish/svg_polish_manifest.yaml` can be written.

61. **Issue 100BL - SVG polish executor CLI fixture path boundary**
    Completed as direct SVG-mutation safety hardening. `svg_polish_executor.py`
    now validates CLI fixture input before dry-run planning or `--write`:
    fixture names resolve under `examples/<name>`, `examples/<name>` remains
    valid, and explicit absolute paths remain valid. Traversal-like, nested, or
    existing outside-relative paths fail with a controlled `invalid fixture path`
    error before the recipe can be loaded or `polish/<name>.polished.svg` can be
    written.

62. **Issue 100BM - SVG polish recipe CLI fixture path boundary**
    Completed as SVG polish starter safety hardening. `svg_polish_recipe.py`
    `--template` now validates CLI fixture input before printing or writing a
    starter recipe: fixture names resolve under `examples/<name>`,
    `examples/<name>` remains valid, and explicit absolute paths remain valid.
    Traversal-like, nested, or existing outside-relative paths fail with a
    controlled `invalid fixture path` error before
    `polish/svg_polish_recipe.yaml` can be written.

63. **Issue 100BN - external vision review CLI fixture path boundary**
    Completed as second-opinion evidence safety hardening.
    `external_vision_review.py --template` now validates CLI fixture input
    before printing or writing a starter review: fixture names resolve under
    `examples/<name>`, `examples/<name>` remains valid, and explicit absolute
    paths remain valid. Traversal-like, nested, or existing outside-relative
    paths fail with a controlled `invalid fixture path` error before
    `external_vision_review.yaml` can be written.

64. **Issue 100BO - subregion iteration log CLI fixture path boundary**
    Completed as subregion workflow safety hardening.
    `subregion_iteration_log.py --template` and `--append` now validate CLI
    fixture input before writing or appending the iteration log: fixture names
    resolve under `examples/<name>`, `examples/<name>` remains valid, and
    explicit absolute paths remain valid. Traversal-like, nested, or existing
    outside-relative paths fail with a controlled `invalid fixture path` error
    before `subregion_iteration_log.md` can be written.

65. **Issue 100BP - paper aesthetic context fixture identity boundary**
    Completed as paper-wide contract identity hardening.
    `paper_aesthetic_context.py --template --fixture` and the v1 loader now
    validate `figure_roles[].fixture` through the shared fixture identity
    contract. Unsafe fixture strings such as `../outside` fail before a template
    can be written or a pack can be accepted as a normal paper-wide design
    contract.

66. **Issue 100BQ - publication scaffold fixture identity boundary**
    Completed as publication provenance scaffold hardening.
    `publication_audit_scaffold_text()` now validates the fixture name before
    rendering `QUALITY_AUDIT.md` scaffold content. The writer inherits the same
    guard, so unsafe fixture strings fail before a publication audit file can be
    written.

67. **Issue 100BR - TeX coordinate shift suffix boundary**
    Completed as source authoring helper hardening.
    `tex_coordinate_shift.py` now rejects non-`.tex` target paths before reading
    and before `--write` can mutate a file. The helper remains path-explicit for
    normal TeX source files and still requires `--line` or intentional `--all`.

68. **Issue 100BS - reference extract path boundary**
    Completed as reference-authoring evidence hardening.
    `reference_extract.py` now requires `spec.yaml.reference_image` to resolve
    under the fixture directory before OCR, palette clustering, structural
    extraction, or `coordinate_hints.yaml` writes can occur. Absolute and
    parent-relative escaped references fail with a controlled message.

69. **Issue 100BT - reference-learning path boundary**
    Completed as reference-learning contract hardening.
    `critique_reference_pack.py` now rejects absolute and parent-relative
    reference paths at the pack validation layer instead of letting downstream
    metrics treat escaped anchors as missing/skipped evidence.

70. **Issue 100BU - SVG semantic diff CLI fixture path boundary**
    Completed as final-artifact semantic-safety hardening.
    `svg_semantic_diff.py` now rejects traversal-like and outside-relative
    fixture paths before writing `polish/svg_semantic_diff.json`, keeping
    semantic-diff reports bound to declared examples.

71. **Issue 100BV - golden artifact gate CLI fixture path boundary**
    Completed as release-adjacent gate hardening.
    `check_golden_artifacts.py` now rejects escaped fixture paths before
    certifying accepted/golden artifact state, so outside directories cannot be
    reported as normal golden-ready fixtures.

72. **Issue 100BW - visual-clash warning budget CLI target boundary**
    Completed as final-mode warning-budget hardening.
    `check_visual_clash_budget.py` now validates explicit targets so CI/final
    warning-budget checks certify only the repo examples tree or declared
    fixtures under it.

73. **Issue 100BX - reference-aesthetic metrics CLI fixture path boundary**
    Completed as reference/aesthetic evidence hardening.
    `reference_aesthetic_metrics.py` now rejects escaped fixture paths before
    writing `build/reference_aesthetic_metrics.json`, preventing fresh-looking
    metrics from being generated outside declared examples.

74. **Issue 100BY - reference extract CLI fixture path boundary**
    Completed as reference-authoring CLI hardening.
    `reference_extract.py` now validates the fixture argument itself before OCR,
    palette extraction, structural hints, or `coordinate_hints.yaml` writes can
    occur.

75. **Issue 100BZ - inspection trace CLI path boundary**
    Completed as crop-read accountability hardening.
    `inspection_trace.py validate` now rejects traversal-like fixture paths
    before certifying `inspection_trace.yaml` as valid audit evidence.

76. **Issue 100CA - layout drift CLI fixture path boundary**
    Completed as compile-stage layout-evidence hardening.
    `check_layout_drift.py` now accepts fixture names, `examples/<name>`,
    absolute direct examples children, or compile-local `.`, while rejecting
    traversal-like fixture paths before emitting normal `SKIP`/OK output.

77. **Issue 100CB - layout drift usage doc sync**
    Completed as usage-contract cleanup.
    `check_layout_drift.py` help/docstrings now describe the hardened fixture
    argument contract instead of implying arbitrary `<example_dir>` paths are
    accepted.

78. **Issue 100CC - inventory issue-file freshness guard**
    Completed as roadmap-hygiene hardening.
    `tests/test_release_contract.py` now compares the Issue 100 inventory
    header/baseline against actual Issue 100 files on disk, preventing the
    roadmap from claiming an older suffix after new issue docs land.

79. **Issue 100CD - plugin install package hygiene summary**
    Completed as install-readiness visibility hardening.
    `plugin_install_freshness.py` now emits `installed_package_hygiene` so a
    payload-fresh install can still show dirty package cache state and the
    package-audit cleanup action.

80. **Issue 100CE - plugin install hygiene exit-code guard**
    Completed as install-readiness gate hardening.
    `plugin_install_freshness.py` now exits `0` only when payload freshness is
    `fresh` and installed package hygiene is `clean`, so shell/CI consumers do
    not silently pass dirty installed caches.

81. **Issue 100CF - source package hygiene guard**
    Completed as source-install loop hardening.
    `plugin_install_freshness.py` now emits `source_package_hygiene` and exits
    nonzero when the development plugin tree contains generated package junk
    that the next reinstall would copy.

82. **Issue 100CG - plugin hygiene next-action quoting**
    Completed as shell-safety hardening.
    `plugin_install_freshness.py` now shell-quotes package-audit cleanup paths
    in source and installed hygiene `next_action` values, so repo paths such as
    `[figure-agent]` can be copied into zsh without glob failure.

83. **Issue 100CH - inventory completion-summary guard**
    Completed as roadmap-status hardening.
    `tests/test_release_contract.py` now requires the Issue 100 Recommended
    Execution Order completion summary to mention the latest Issue 100 file
    suffix, so the inventory cannot have a fresh header/table with a stale
    completion briefing.

84. **Issue 100CI - stale issue-status recurrence guard**
    Implemented as documentation-status regression hardening. The stale-status
    release-contract guard now rejects `implemented in branch`, `pending
    commit`, and `pending merge` header wording in addition to earlier
    branch/worktree variants, and recent Issue 100 headers were normalized to
    their main merge commits.

85. **Issue 100CJ - source git hygiene guard**
    Implemented as plugin-install readiness hardening.
    `plugin_install_freshness.py` now emits `source_git_hygiene` and exits
    nonzero when the development plugin tree has uncommitted git changes, so
    dirty user figure-source edits cannot be copied into the installed plugin
    cache and reported as fresh plugin state.

86. **Issue 100CK - install next-action precedence guard**
    Implemented as plugin-install UX hardening. The top-level
    `plugin_install_freshness.py` `next_action` now prioritizes dirty source
    package hygiene, dirty source git hygiene, and dirty installed package
    hygiene before payload update/reinstall actions, so the printed action
    matches the readiness blocker that made the CLI exit nonzero.

87. **Issue 100CL - installed example-source hygiene guard**
    Implemented as plugin-install cache-readiness hardening.
    `plugin_install_freshness.py` now emits
    `installed_example_source_hygiene`, comparing non-generated files under
    `examples/` separately from payload freshness. Payload `changed_files`
    still ignores example work products, but installed example-source drift now
    exits nonzero and points the operator at clean-source reinstall.

88. **Issue 100CM - marketplace source hygiene guard**
    Implemented as plugin-install source-resolution hardening.
    `plugin_install_freshness.py` now emits `marketplace_source_hygiene`,
    comparing the current repo marketplace root with the registered
    `figure-agent-local` source in `known_marketplaces.json`, so raw Claude
    install/update commands cannot silently install from a different checkout
    than the one being reviewed.

89. **Issue 100CN - inventory next-analysis freshness guard**
    Implemented as roadmap-status hardening. The release-contract suite now
    requires the `Additional Update Analysis` section of the Issue 100 inventory
    to mention the latest Issue 100 suffix and reject stale "next candidate"
    prose that points operators back to already-implemented Issue 100A-C work.

90. **Issue 100CO - mode-scoped completion guidance**
    Implemented as operator-guidance hardening. `/fig_drive` complete states
    now explain the selected mode scope: authoring complete points to review,
    review complete points to release/final, polish complete says it is only
    a polish-mode closure, and final complete keeps the terminal no-action
    wording.

91. **Issue 100CP - polish prerequisite gate alignment**
    Implemented as polish-mode operator UX hardening. When polish mode is
    blocked before loop evidence is meaningful, the additive `svg_polish_gate`
    now mirrors the authoritative prerequisite action (`run_fig_compile`,
    `run_fig_export`, etc.) instead of telling operators to skip ahead to a loop
    rerun.

92. **Issue 100CQ - SVG polish queue readiness filters**
    Implemented as polish-queue evidence UX. `/fig_queue --mode polish` now
    supports direct filters for SVG gate state, `can_start_svg_polish`, route,
    next action, and blocking source so real-fixture promotion evidence can be
    gathered without manual JSON post-processing.

93. **Issue 100CR - SVG polish gate blocker-source filters**
    Implemented as a queue projection fix found during real-fixture evidence.
    `svg_polish_blocking_sources` now merges both gate and readiness blocker
    sources, so `--svg-polish-blocking-source driver_blocker` finds
    no-current-checkpoint rows instead of silently returning zero.

94. **Issue 100CS - queue-run SVG filter parity**
    Implemented as queue-run UX parity. `/fig_queue_run --mode polish` now
    accepts the same SVG polish readiness filters as `/fig_queue`, so plan-only
    and bounded queue execution can use `--can-start-svg-polish`,
    `--svg-polish-gate-state`, route, next-action, and blocker-source filters
    without manual JSON post-processing.

95. **Issue 100CT - inventory version consistency guard**
    Implemented as roadmap metadata hardening. The release-contract suite now
    checks that the Issue 100 Documentation Consistency Check names the live
    plugin manifest version, so the inventory cannot keep stale v0.9.x claims
    after README, pyproject, and plugin metadata advance.

96. **Issue 100CU - queue-run filter surface guard**
    Implemented as queue-run drift prevention. `fig_queue_run.py` now declares
    `QUEUE_FILTER_KEYS`, ties it to `fig_queue._FILTER_KEYS`, builds CLI filter
    payloads through one helper, and tests that the two command surfaces stay
    in sync when future queue filters are added.

97. **Issue 100CV - JSON/dry-run CLI compatibility aliases**
    Implemented as operator CLI compatibility hardening. `fig_driver.py` now
    accepts `--json` as a no-op because it always emits JSON, and
    `fig_queue_run.py` accepts `--json` plus `--dry-run` as no-ops because it
    always emits JSON and remains plan-only unless `--execute` is supplied.

98. **Issue 100CW - package audit evidence-preserving clean**
    Implemented as a development-cleanup safety mode. The default
    `plugin_package_audit.py --clean` still removes fixture `build/` and
    `exports/` artifacts for package/install hygiene, while the explicit
    `--preserve-fixture-artifacts` flag keeps current
    `examples/<name>/build` and `examples/<name>/exports` evidence during
    local review loops and still removes cache/virtualenv junk.

99. **Issue 100CX - fig_queue format-json compatibility**
    Implemented as queue-output CLI compatibility. `/fig_queue` still prints a
    table by default and still accepts `--json`; it now also accepts
    `--format json` for the same JSON contract and `--format table` as the
    explicit table form.

100. **Issue 100CY - fig_queue-run format-json compatibility**
     Implemented as queue-run output CLI compatibility. `/fig_queue_run`
     remains JSON-only and still accepts `--json` plus `--dry-run` as no-ops;
     it now also accepts `--format json` so the plan-only wrapper matches the
     JSON output spelling operators use on `/fig_queue`.

101. **Issue 100CZ - driver/run format-json compatibility**
     Implemented as single-fixture output CLI compatibility. `/fig_drive` and
     `/fig_run` both already emit JSON by default; they now accept
     `--format json` as an explicit output spelling without changing dry-run,
     plan-only, execution, or journaling policy.

102. **Issue 100DA - loop/closeout format-json compatibility**
     Implemented as loop/closeout output CLI compatibility. `/fig_loop` and
     `/fig_closeout` keep their existing `--json` behavior and now accept
     `--format json` as the same automation output spelling; `--format text`
     names the existing prose/default output.

103. **Issue 100DB - helper format-json compatibility**
     Implemented as helper output CLI compatibility. `subregion_active_set.py`
     and `reference_pack.py` keep their existing `--json` and text behavior
     while accepting `--format json` for stdout JSON and `--format text` for
     the default text output.

104. **Issue 100DC - status JSON CLI contract**
     Implemented as canonical status CLI hardening. `status.py` now uses
     argparse, emits machine-readable status with `--json` or `--format json`,
     preserves default text output, and rejects unknown extra arguments instead
     of silently ignoring them.

105. **Issue 100DD - fig_improve JSON flag compatibility**
     Implemented as loop-centered CLI compatibility. `fig_improve.py` keeps its
     JSON-only output contract while accepting explicit `--json` and
     `--format json` no-op flags.

106. **Issue 100DE - critique brief CLI argument contract**
     Implemented as host-brief CLI hardening. `critique_brief.py` now rejects
     unknown extra arguments with argparse while preserving the existing
     fixture positional contract and no-argument usage error.

107. **Issue 100DF - match_snippet CLI help contract**
     Implemented as helper CLI parser hardening. `match_snippet.py` now uses
     argparse for help and unknown-argument handling while preserving snippet
     scoring and the single `briefing.md` positional contract.

108. **Issue 100DG - plugin install freshness JSON flag compatibility**
     Implemented as install-readiness CLI compatibility. `plugin_install_freshness.py`
     keeps its JSON-only output and exit-code policy while accepting explicit
     `--json` and `--format json` no-op flags.

109. **Issue 100DH - JSON evidence-helper flag compatibility**
     Implemented as helper CLI compatibility. `fig_run_journal.py`,
     `detector_feedback_ledger.py`, and `diagnostic_artifact_provenance.py`
     keep their JSON-only output contracts while accepting explicit `--json`
     and `--format json` no-op flags.

110. **Issue 100DI - JSON smoke/patch/harness flag compatibility**
     Implemented as CLI compatibility for remaining JSON-only operator tools.
     `fig_e2e_smoke.py`, `fig_loop_patch_executor.py`, and
     `svg_polish_positive_harness.py` now accept explicit `--json` and
     `--format json` no-op flags while preserving their existing output and
     mutation policies.

111. **Issue 100DJ - queue operator-guidance projection**
     Implemented as queue UX hardening. `/fig_queue` now preserves
     `/fig_drive.operator_guidance` in compact rows and uses complete-row
     `operator_guidance.next_step` in the table and command-plan handoff, while
     blocked host/human/release/SVG rows continue to use the queue
     operator-handoff policy.

112. **Issue 100DK - polish release-boundary gate alignment**
     Implemented as polish-mode gate UX hardening. When polish mode is blocked
     by `accepted_or_final_ready_required`, additive `svg_polish_gate` now
     reports `state: blocked` and `next_action: resolve_release_boundary`
     instead of falling through to no-current-checkpoint loop advice.

113. **Issue 100DL - polish next-action summary counts**
     Implemented as polish-queue corpus-triage UX. `/fig_queue --mode polish`
     now adds `summary.by_svg_polish_next_action` when rows expose SVG
     next-action guidance, so operators can see the action distribution without
     row-by-row JSON post-processing.

114. **Issue 100DM - polish blocking-source doc guard**
     Implemented as documentation-contract hardening. `/fig_queue` summary docs
     now describe `by_svg_polish_blocking_source` as gate/readiness blocker
     aggregation, and the release-contract suite guards that wording.

115. **Issue 100DN - queue table summary counts**
     Implemented as default-table operator UX hardening. `/fig_queue` now prints
     deterministic grouped summary count lines after `summary total=...`, so
     operators can see dominant action, actor, blocker, and SVG-polish
     next-action distributions without switching to JSON or scanning every row.

116. **Issue 100DO - queue-run execute/dry-run conflict**
     Implemented as execution-safety hardening. `/fig_queue_run --execute
     --dry-run` now exits 2 before building/running the queue, preserving
     plan-only `--dry-run` compatibility while requiring unambiguous
     `--execute` for mutation.

117. **Issue 100DP - complete row blocking-source cleanup**
     Implemented as queue attribution cleanup. Mode-scoped `complete` rows now
     use `blocking_source: null`, so `by_blocking_source` summarizes actual
     blockers/actions instead of counting local completion as `driver.action`.

118. **Issue 100DQ - command-plan complete bucket**
     Implemented as command-plan UX hardening. Mode-scoped `complete` rows now
     live under additive `command_plan.complete` with `complete_count`, while
     `blocked_count` is reserved for host/human/release/closeout/unsafe
     workflow blockers.

119. **Issue 100DR - queue-run complete summary**
     Implemented as queue-run summary UX hardening. `/fig_queue_run` now
     exposes `summary.planned_complete`, so plan-only batch output carries the
     same blocked-vs-complete distinction as `/fig_queue --command-plan`.

120. **Issue 100DS - first-blocker status context**
     Implemented as queue documentation hardening. `/fig_queue` now explicitly
     says `by_first_blocker` is global status context, can include
     mode-scoped complete rows, and should not be used as the selected-mode
     blocker count.

121. **Issue 100DT - polish mode-forbidden guidance**
     Implemented as driver operator-guidance hardening. Polish-mode rows with
     `stop_boundary: mode_forbidden_action` no longer tell operators to run the
     selected command; they route back to review mode to close TikZ/loop
     prerequisites before re-entering polish mode.

122. **Issue 100DU - fig_run json flag compatibility**
     Implemented as bounded-runner CLI compatibility. `/fig_run` keeps its
     JSON-only output and existing `--format json` spelling while accepting
     explicit `--json` as the same no-op output flag.

123. **Reference-aware candidate-search vertical slice**
     Completed as the first search-layer upgrade beyond single safe-mechanical
     patch proposals. Added fixture intent modeling, deterministic candidate-set
     generation, sandbox rendering, ranking authority, human review packets,
     explicit apply refusal/guarding, CLI commands, read-only MCP facade tools,
     release-gate coverage, and synthetic dogfood evidence. This does not make
     the plugin a taste oracle; it makes alternatives inspectable and rankable
     before any source mutation is considered.

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

Issue 100CN makes this section itself part of the release-contract freshness
surface. Issue 100CO then closes the highest-priority operator explanation
gap by making complete states explicitly mode-scoped. Issue 100CP closes the
next polish-mode operator mismatch: when compile/export prerequisites block
polish mode, the SVG-specific gate now points at the same prerequisite instead
of the later loop checkpoint. Issue 100CQ then adds direct queue filters for
SVG polish readiness and blocker sources, so promotion evidence queries are
repeatable without manual JSON post-processing. Issue 100CR closes the first
defect found by using those filters on real fixtures: gate-only blocker sources
now project into `svg_polish_blocking_sources` alongside readiness blocker
sources. Issue 100CS then closes the queue-run parity gap, so the same SVG
readiness filters work in the plan-only/bounded execution wrapper instead of
only in the read-only dashboard. Issue 100CT closes the next roadmap-metadata
hole by tying the inventory's own version consistency statement to the live
plugin manifest version. Issue 100CU then prevents the same queue/queue-run
filter drift from recurring by making the runner filter surface test-backed.
Issue 100CV removes the explicit `--json`/`--dry-run` CLI trap discovered while
starting real-fixture evidence work. Issue 100CW then separates development
cleanup from package cleanup: operators can clean local `uv`/pytest junk without
erasing the fixture build/export evidence they are about to inspect, while final
package validation still treats those artifacts as generated junk. Issue 100CX
then removes the next live queue-inspection trap: `/fig_queue --format json`
now reaches the same JSON contract as `--json` instead of failing at argparse.
Issue 100CY applies the same compatibility to `/fig_queue_run --format json`,
without adding table output or changing plan/execution safety. Issue 100CZ
extends that compatibility to the adjacent single-fixture driver/run commands,
where both commands already emit JSON by default. Issue 100DA closes the
remaining primary workflow JSON surfaces, `/fig_loop` and `/fig_closeout`,
without changing their artifact writes, read-only behavior, or exit-code
semantics. Issue 100DB closes the same compatibility gap in the documented
stdout-JSON helper parsers while leaving detector `--json-output` file-writing
contracts alone. Issue 100DC fixes the higher-impact status entrypoint, where
`--json` was previously accepted only by accident and produced prose. Issue
100DD closes the same explicit-output-flag trap on the loop-centered
`/fig_improve` entrypoint. Issue 100DE applies the same no-silent-argument-loss
standard to the host-vision brief generator. Issue 100DF brings the snippet
candidate helper under the same parser hygiene without changing matching logic.
Issue 100DG applies the same explicit JSON-output flag compatibility to the
plugin install freshness checker, preserving its JSON-only output and exit-code
contract. Issue 100DH applies the same standard to the JSON-only evidence
helpers used for interrupted-run continuation, detector tuning, and diagnostic
artifact provenance. Issue 100DI closes the remaining JSON-only operator tools
on smoke, explicit patch execution, and SVG-polish plumbing evidence. Issue
100DJ then closes the next operator interpretation gap found in real queue
inspection: complete rows now preserve the same mode-scoped follow-up guidance
as `/fig_drive` in both table and command-plan JSON, so
authoring/review/polish/final local completion is not flattened into ambiguous
whole-figure completion. Issue 100DK closes the next SVG polish queue
contradiction found in the same evidence pass: release-boundary rows now point
SVG-specific `next_action` at release-boundary resolution instead of loop
reruns. Issue 100DL then makes those row-level SVG next actions visible at
summary level for corpus triage. Issue 100DM fixes the adjacent docs drift so
summary-level SVG blocking-source aggregation is described as gate/readiness
based, matching the implementation. Issue 100DN then closes the default-output
gap: the same grouped summary counts now appear in the human-readable table
instead of requiring JSON output. Issue 100DO closes the adjacent execution
safety ambiguity: `/fig_queue_run --execute --dry-run` now fails before any
workflow attempt instead of silently treating the call as execution. Issue
100DP then removes the adjacent attribution noise where mode-scoped complete
rows were still summarized as `driver.action` blocking sources. Issue 100DQ
then applies the same distinction to command-plan JSON by separating
mode-scoped complete rows from true blocked rows. Issue 100DR closes the
follow-on queue-run summary gap by surfacing `planned_complete` at the same
level as planned executable and blocked counts. Issue 100DS closes the
remaining wording gap by naming `by_first_blocker` as status context rather
than selected-mode blocker evidence. Issue 100DT closes the adjacent
single-fixture driver contradiction where polish-mode mode-forbidden rows still
told operators to run the selected command. Issue 100DU closes the last
bounded-runner spelling gap found in this pass by allowing `/fig_run --json`
as the same no-op output flag as `/fig_run --format json`.

After Issue 100DU, JSON-output helper tools on the active operator path are now
correctly able to say, without forcing operators to remember which commands are
JSON-only:

- the registered `figure-agent-local` marketplace source matches or mismatches
  the reviewed checkout;
- dirty source figure work must be committed, stashed, or moved aside before a
  raw Claude reinstall is trusted;
- installed example-source drift is separate from payload freshness.
- interrupted-run summaries, detector feedback ledgers, and diagnostic artifact
  provenance reports can be requested with the same explicit JSON-output
  spelling as the primary driver and queue commands.
- deterministic smoke, explicit patch-executor, and SVG-polish harness evidence
  can also use that explicit JSON-output spelling without changing their
  existing safety or mutation policies.
- multi-fixture queue complete rows carry driver mode-scoped next-step guidance
  in both table and command-plan JSON instead of forcing operators to inspect
  each single-fixture driver JSON.
- polish-mode release-boundary rows carry SVG-specific next-action guidance
  that matches the release/operator boundary.
- polish-mode queue summaries count SVG next actions directly.
- polish-mode queue docs correctly state that blocking-source summaries merge
  gate and readiness blocker sources.
- the default queue table mirrors grouped JSON summary counts, including
  SVG-polish next-action and blocker-source distributions.
- queue-run execution requires an unambiguous `--execute`; explicit
  `--dry-run` cannot be combined with it.
- mode-scoped complete rows no longer pollute blocker-source summaries.
- command-plan JSON separates complete rows from blocked rows.
- queue-run summaries count planned complete rows instead of hiding them inside
  nested command-plan JSON.
- queue first-blocker summaries are documented as status context rather than
  current-mode blocker counts.
- live authoring queue dogfood confirms complete rows preserve broader-mode
  review guidance while `blocked_count`/`planned_blocked` remain zero.
- polish-mode mode-forbidden driver guidance routes back to review mode instead
  of telling operators to execute the forbidden selected command.
- install freshness diagnostics now confirm the current install refresh is
  correctly blocked by user-owned dirty figure source, not package junk.

The current post-100DT next candidates are therefore not old Issue 100A-C
contract gaps. They are:

1. **Real-fixture SVG polish promotion evidence.** The route is mechanically
   supported, deterministic harness coverage exists, and prerequisite gate UX
   plus queue and queue-run filters now make the evidence query direct.
   Post-100DT evidence still finds zero real fixtures with
   `can_start_svg_polish: true`. Before package cleanup, blockers were four
   host-vision critique refreshes, one compile/render prerequisite on
   user-owned dirty source, two no-current-checkpoint gates, and one release
   boundary. After package cleanup removed generated build artifacts, the
   current blockers are five compile/render refreshes, one host-vision critique
   refresh, and two no-current-checkpoint gates. The next valid positive pass
   should regenerate required builds, refresh the remaining host-vision
   critique, keep the dirty fig1 source separate from plugin hardening, then
   rerun `--can-start-svg-polish true`.
2. **Installed-cache refresh after dirty figure work is resolved.** The
   diagnostic path has been verified: source/package and installed package
   hygiene are clean after cleanup, marketplace source hygiene is clean, and
   `plugin_install_freshness.py` exits nonzero with top-level `next_action`
   pointing at the dirty user-owned `.tex`. Reinstall should wait until that
   source git blocker is intentionally handled.

No new broad aesthetic detector should be added before these current routing and
evidence gaps are addressed. The plugin's risk is not lack of another taste
rubric; it is that existing evidence and command guidance are not always
surfaced in the path the user actually runs.

Issues 100DD-100DI close the explicit JSON-output and parser hygiene traps on
the remaining operator path. Issue 100DJ closes the adjacent projection trap:
queue rows, table output, and command-plan handoff now preserve the driver
guidance that explains what a mode-local `complete` state does and does not
mean. Issue 100DK closes the SVG polish gate mismatch where release-boundary
rows still looked like loop-checkpoint blockers in SVG-specific columns. Issue
100DL closes the follow-on summary gap so the exact SVG next-action
distribution is visible without manual row inspection. Issue 100DM closes the
matching documentation-contract drift for merged gate/readiness blocking-source
summaries. Issue 100DN closes the remaining default-table summary visibility
gap by printing the same grouped counts that JSON already exposed. Issue 100DO
closes the adjacent flag-conflict safety gap in the bounded queue runner. Issue
100DP closes the adjacent queue-attribution gap by removing complete rows from
blocking-source counts. Issue 100DQ closes the matching command-plan gap by
placing complete rows in `command_plan.complete` instead of
`command_plan.blocked`. Issue 100DR closes the queue-run projection gap by
copying that complete count into `summary.planned_complete`. Issue 100DS
closes the last adjacent wording trap by clarifying that `by_first_blocker`
is broader status context, not selected-mode blocker accounting. Issue 100DT
closes the polish driver guidance contradiction found during real SVG-promotion
evidence refresh.

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
  as v0.9.3.
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

- every listed gap has a follow-up issue, implementation summary, or explicit
  decision to defer;
- release-contract tests keep the inventory header, branch baseline, latest
  issue-file suffix, completion summaries, and issue-status headers aligned
  with mainline truth;
- command docs explain status, drive, run, improve, loop, critique, export, and
  SVG polish routing in operator language;
- final-readiness checks remain invokable as one non-mutating command path;
- schema/module maps stay current before any future schema bump.
