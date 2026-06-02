# Issue 100 - Comprehensive Figure-Agent Gap Inventory

Status: active roadmap; listed P0-P3 hardening slices implemented through Issue 100BY, with real-fixture SVG polish promotion still evidence-gated

Type: architecture review, operator workflow, audit coverage, roadmap

## Context

This document records the current figure-agent plugin gaps after the v0.9.x
audit hardening work, including Issues 90, 91, 97, and 99.

Current baseline:

- plugin root: `plugins/figure-agent`;
- branch baseline: `main` after Issue 100BY reference-extract CLI path boundary;
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
| G100-08 | P2 | Schema/version sprawl | Critique schemas now span v1 through v1.17. Backward compatibility is valuable, but the mental model is heavy. | `critique_schema_vocab.py` lists many active schema versions and validators carry optional legacy paths. Issue 100Z adds a release-contract guard so script schema constants cannot drift out of the module map. | Future changes now have a test-backed ownership map instead of relying on manual updates alone. | Issue 100H - schema capability matrix and deprecation policy; Issue 100Z - schema map drift guard |
| G100-09 | P2 | Code surface size | The plugin has many scripts and commands; boundaries are mostly documented but not summarized as an ownership map. | Current inventory is 96 scripts, 103 tests, and 15 command docs. | New contributors or agents can pick the wrong module and duplicate logic. | Issue 100I - module ownership map |
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
