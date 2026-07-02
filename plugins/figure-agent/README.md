# figure-agent

A Claude Code plugin that helps you build **reproducible, paper-grade scientific figures** in TikZ — so the same `.tex` source rebuilds the same figure every time, even after revisions.

You (or any LLM) draw the figure. The plugin handles the boring-but-critical parts: keeping styles consistent, catching layout problems, running the build, and exporting clean PDF/SVG.

---

## What you get

- **One folder per figure** with a fixed structure — never lose track of which source matches which output.
- **Style Lock** — palette, fonts, line weights stay consistent across every figure in a manuscript.
- **Build + visual QA** in one command — compile errors, label collisions, and clash warnings all in one report.
- **Reference analysis** — `reference PNG -> OCR + palette clusters + optional vtracer structural hints`, then `coordinate_hints.yaml -> semantic TikZ authoring`. SVG-to-TikZ path conversion is not the active workflow.
- **Vision critique without API costs** — the host Claude Code reads your compiled figure and writes feedback. Subscription tokens only; no external API keys, no per-figure inference bill.
- **Export to PDF / SVG / TIFF / PNG** with text staying as text (SVG preserves editable labels).

## What this is NOT

- ❌ **Image generation.** No DALL·E / Imagen / SDXL calls. You author the TikZ.
- ❌ **Data plots.** Numerical plots from real datasets go in `[Graph_making_hub]/`. This plugin is for **symbolic schematics** — energy diagrams, mechanism cartoons, device overviews.
- ❌ **Auto-magic SVG → TikZ converter.** Reference images are used as visual guides for *you*, not as inputs to a code generator.
- ❌ **Paid API service.** All vision work is done by the host Claude Code session you're already running.
- ❌ **A hidden auto-designer.** The plugin exposes evidence, gates, and bounded handoffs; it does not silently invent art direction or source edits.
- ❌ **Journal acceptance oracle.** It can raise a figure toward paper-grade quality, but it cannot certify Nature/Science acceptance.

---

## Core commands

```
/fig_new      Start a new figure — chat interview fills briefing.md + spec.yaml
/fig_extract  (optional) reference PNG -> OCR + palette clusters + optional vtracer structural hints
/fig_compile  Build the TikZ → PDF + PNG, run Style Lock + collision checks
/fig_critique Have host Claude read the build PNG and write critique.md
/fig_ground   Ground physics intent — author tex/semantic assertions from briefing §6/§7
/fig_adjudicate Scaffold critique_adjudication.yaml after critique lint passes
/fig_loop     Record a verify-only loop checkpoint
/fig_export   Export final PDF / SVG / TIFF / PNG
/fig_status   "Where am I?" — read-only stage check
/fig_drive    Dry-run advisory driver — recommends one next action
/fig_run      Bounded runner — executes safe mechanical steps, stops at gates
/fig_improve  Loop-centered single-fixture improvement entry point
/fig_queue    Multi-fixture driver queue — groups next actions by actor/gate
/fig_queue_run Plan or execute the queue's workflow-agent subset
/fig_closeout Read-only post-patch closeout checklist
/fig_context_pack Read-only authoring context pack (JSON; accepts --json / --format json)
/fig_e2e_smoke Deterministic compile/export/status/loop smoke harness (JSON; accepts --json / --format json)
```

## Runtime Entrypoint

Preferred shell form is `fig-agent ...`. If the host does not put plugin
`bin/` on `PATH`, use `"${CLAUDE_PLUGIN_ROOT}/bin/fig-agent" ...`.

Runtime roots are explicit:

- `FIGURE_AGENT_PLUGIN_ROOT` or `CLAUDE_PLUGIN_ROOT`: installed plugin bundle
  root containing `.claude-plugin/`, `bin/`, `scripts/`, and `styles/`.
- `FIGURE_AGENT_WORKSPACE` or `CLAUDE_PROJECT_DIR`: user project root
  containing `examples/`.

## A typical figure (start to finish)

```bash
# 1. Scaffold the folder. Claude asks you 7 questions and fills briefing.md.
/fig_new fig3_trap_concept

# 1b. After scaffolding, use status as the canonical first check.
/fig_status fig3_trap_concept

# 2. (Optional) If you have a reference image (paper figure, sketch, mockup),
#    drop it in examples/fig3_trap_concept/reference/ and extract hints.
/fig_extract fig3_trap_concept

# 3. You (or an LLM) write examples/fig3_trap_concept/fig3_trap_concept.tex
#    using briefing.md intent + reference + coordinate_hints.yaml.
#    Contract: coordinate_hints.yaml -> semantic TikZ authoring.
#    SVG-to-TikZ path conversion is not the active workflow.

# 4. Compile. This runs Style Lock + builds PDF + PNG + collision/clash checks.
/fig_compile fig3_trap_concept

# 5. Get vision feedback. Host Claude reads the build PNG.
/fig_critique fig3_trap_concept   # writes critique.md

# 6. For loop work, lint critique.md, scaffold adjudication, then record state.
fig-agent helper critique_lint.py fig3_trap_concept
/fig_adjudicate fig3_trap_concept
/fig_loop fig3_trap_concept --goal "resolve the next safe critique target"

# 7. Iterate: edit .tex (often one line at a time), re-compile, re-critique.
#    When the critique and loop state look clean, export.
/fig_export fig3_trap_concept
```

**Iterating an existing figure.** For an already-scaffolded figure, the single
canonical entry point is `/fig_improve <name> --goal "<goal>"`. It wraps the
compile / critique / loop steps and stops at human or taste boundaries;
`/fig_status <name>` remains the read-only "where am I?" check to run first,
especially when resuming after a break.

For agent-driven work, use `/fig_status <name>` or
`/fig_drive <name> --mode review --goal "<goal>" --dry-run` as the canonical
first check and follow the printed `Next:` / driver action. Export, release, or
polish only when status or the driver explicitly routes there.

When the user asks the plugin to proceed autonomously through safe mechanical
steps, use `/fig_run <name> --mode review --goal "<goal>" --execute`. It runs
only deterministic allowlisted shell work (compile, missing adjudication
scaffold, verify-only loop checkpoints, and non-golden draft export) and stops
before host critique, existing adjudication repair, patch, polish, accepted,
tracked-golden, force-golden, or release boundaries.

`/fig_run --execute` records non-authoritative evidence under
`.scratch/fig-run-runs/`. There is no resume command. To continue later, run
`fig-agent helper fig_run_journal.py <name>` to summarize the previous
stop, then rerun live `/fig_status` or `/fig_drive` and let the fresh driver
choose the next action. Do not replay commands from a journal. The journal
summary emits JSON; `--json` and `--format json` are accepted as explicit
no-op output flags.

When the user asks to keep improving one fixture through repeated critical
loops, use `/fig_improve <name> --goal "<goal>" --execute --max-loops N`.
It wraps `/fig_run`, summarizes the final actor boundary, and exposes optional
improvement candidates when the fixture is already safe. It still stops before
host critique, source patching, SVG polish, human decisions, accepted/golden
roll-forward, and release mutation; after that actor acts, rerun
`/fig_improve`.

For multi-fixture work, start with the queue rather than running fixture commands
one by one:

```bash
fig-agent queue --mode review --goal "<goal>"
fig-agent queue --mode review --goal "<goal>" --actor host_llm
fig-agent queue --mode review --goal "<goal>" --actor workflow_agent --command-plan --json
fig-agent queue-run --mode review --goal "<goal>" --actor workflow_agent
```

Add `--execute` to `/fig_queue_run` only after inspecting the plan-only output.
Queue execution delegates each fixture to `/fig_run`, so live driver
revalidation remains the safety gate. Host, human, release/golden, SVG-polish,
and closeout rows stay visible as blocked operator handoffs.

**Iteration philosophy.** Don't redraw the figure each time the critique fires. Make small, targeted edits — one polymer chain, one label, one arrow at a time. 5–10 iterations × 1-line patch is the path to paper-grade quality. (See `docs/architecture-v0.5-per-panel-reference-workflow.md` for the per-panel critique workflow.)

---

## Current state (v0.9.3)

| Area | What's working |
|---|---|
| **Build pipeline** | `/fig_compile` runs Style Lock + lualatex + collision + clash checks. Report-only by default; manuscript runs use `FIGURE_AGENT_STRICT=1` for hard fail. |
| **Vision critique** | `/fig_critique` reads build PNG, high-zoom crops, print-scale crops, visual/text clash candidates, optional reference packs, and optional aesthetic intent, then writes structured `critique.md`. Host Claude only — no external API. |
| **Single next-action summary** | `/fig_status`, `/fig_drive`, `/fig_loop`, and `/fig_closeout` expose the same compact read-only `next_action_summary`, including `decision_boundary` so agents can tell deterministic gates, human decisions, release decisions, SVG-polish handoffs, and advisory-only aesthetic improvements apart. |
| **Bounded safe runner** | `/fig_run` wraps `/fig_drive` and executes only allowlisted deterministic shell actions, then re-queries state. It can execute compile, missing adjudication scaffold, verify-only loop checkpoints, and non-golden draft export; host/human/existing-adjudication/accepted/golden/release/polish boundaries remain explicit stops. |
| **Loop-centered improvement orchestrator** | `/fig_improve` wraps `/fig_run` for repeated one-fixture improvement requests. It gives agents one default entry point for "loop until clean enough" while preserving host/human/patch/SVG/release boundaries and optional-improvement handoffs. |
| **Operator queue** | `/fig_queue` scans real fixtures through `/fig_drive`, groups next work by actor/action/blocker, emits blocked-row `operator_handoff` packets, and `/fig_queue_run` delegates the workflow-agent subset to `/fig_run` after plan-only review. |
| **Runner journal** | `/fig_run --execute` records `.scratch/fig-run-runs/<timestamp>-<name>/` evidence by default. Journals are not replayable and do not replace fresh `/fig_status` or `/fig_drive` checks. |
| **Per-panel reference** | `spec.yaml.panels[i].reference_image` + `bbox_pdf_cm`. Each panel compared against its own reference. |
| **Perception pack** | `/fig_compile` emits descriptive data (`extract.yaml`, `overlay.png`) under `build/perception/` for downstream inspection. |
| **Reproducibility** | `/fig_status` separates render freshness (`.tex`, briefing, spec, Style Lock) from critique freshness (reference images, hints, authoring context, audit evidence, and aesthetic intent), and reports workflow/golden/release readiness separately. Routine generated export SVGs do not make critiques stale. |
| **Golden fixtures** | Accepted figures declare `accepted: true` + `golden_contract`; `check_golden_artifacts.py --require-accepted` is the hard gate and rejects low-resolution TIFF exports. |
| **SVG polish handoff label** | `/fig_drive --mode polish` and `svg_polish_readiness` preserve the `ready_for_svg_polish` external handoff vocabulary. The built-in recipe/executor/delta/manifest/semantic-diff pipeline was retired on 2026-07-02 because it was quarantined, structurally vacuous on real figures, and never provided a live production guarantee. |
| **Style packs** | `docs/style-pack-catalog.md` and the opt-in journal style-pack catalog provide reusable Nature Communications, Nature Materials, Science, and graphical-abstract restraint/playbook anchors without applying them globally. |
| **External vision review** | Optional `external_vision_review.yaml` evidence can be imported when `spec.yaml.external_vision_review: true`; stale reviews, unresolved findings, or conflicting second opinions surface as a human gate, not automatic truth. Start a hash-bound review file with `fig-agent helper external_vision_review.py --template examples/<name> --write-template`. |
| **Reference learning** | Optional `critique_reference_pack.yaml.reference_learning` lets references teach editorial principles without becoming copy targets. Start a v1.1 pack with `fig-agent helper critique_reference_pack.py --template <fixture>`; validation requires concrete allowed-transfer axes and anti-copy guards before `/fig_critique` can use the pack. Legacy v1 packs remain parseable. `reference_aesthetic_metrics.py` adds non-model aesthetic-class divergence signals for palette, density, silhouette, and line density; severe divergence routes to review, not release bypass. |
| **Paper-wide context** | Optional `spec.yaml.paper_aesthetic_context` grounds a figure against explicit paper-series style anchors. Start a pack with `fig-agent helper paper_aesthetic_context.py --template <paper_id> --fixture <name> --write-template`, then opt fixtures in deliberately through `spec.yaml`. |
| **Authoring context pack** | `fig-agent context-pack <name> [--json | --format json]` compiles design philosophy, Style Lock tokens, the project rule catalog, any source-anchored paper/series rule catalog explicitly selected by `spec.yaml`, paper-local briefing/spec context, and opt-in `authoring_context_pack.enabled`, `panels[].semantic_claims`, and `panels[].locked_invariants`. This is durable paper-specific knowledge compilation, not LLM prompt plumbing: it is read-only and does not call a model, execute generation, or act as automatic physics detection. |
| **Narrative context / humanizer layer** | `narrative_context` is a read-only human-perspective compiler surfaced through context packs, critique briefs, candidate review packets, and verify-only loop checkpoints. It records reader path, panel-story inputs, and human review questions while explicitly forbidding model calls, prompt loops, source mutation, rank scoring, and autonomous patch selection. See `docs/humanizer-layer-v1.md`. |
| **Sub-region iteration log** | Optional `subregion_iteration_log.md` evidence narrows critique and loop handoff to the current one-line patch unit. Start a canonical log with `fig-agent helper subregion_iteration_log.py --template examples/<name> --write-template`, then append one row per patch with `--append examples/<name> ...`. The helper records evidence only; it does not infer regions or edit source. |

### Release boundary

- **Automatic:** deterministic compile, lint, freshness, export, golden, publication, visual/text clash, crop/accounting, package validation gates, and the shared single next-action summary.
- **Semi-automatic:** `/fig_improve` for loop-centered one-fixture operation,
  `/fig_run` for allowlisted mechanical shell work,
  host-vision critique, and `/fig_loop` review checkpoints. Claude reads
  prepared images/evidence and writes structured critique; lint and loop
  contracts verify the result.
- **Opt-in:** authoring context packs, semantic claims/locked invariants,
  paper-wide context, aesthetic intent, journal style-pack catalog,
  reference-calibrated packs, reference-learning aesthetic metrics,
  SVG-polish delta packs, and external vision review evidence.
- **Manual:** source drawing, semantic patch choices, human art direction,
  accepted/golden roll-forward, final SVG/vector editing, and any decision to
  promote an N=1 authoring rule beyond a narrow question or constraint.

The plugin is a quality/audit kernel, not a hidden auto-designer. It can make
bad or under-audited figure states much harder to ship, but it cannot certify
Nature/Science acceptance or replace author judgment about taste, novelty, or
venue fit.

## What remains experimental / proposed

Filed as promotion-policy gaps; no production workflow depends on them yet. Each
has a decision gate that blocks broad automation until empirical data exists.
This is a deliberate response to v0.3/v0.4 specs being rejected for lack of data.

- **Real-fixture SVG polish promotion policy** — Issue 47 proved the safe negative route (`continue_tikz` blocks recipe authoring), and Issue 48 made that readiness state explicit. Issue 100D adds a fixture-aware recipe starter, and Issue 100V proves the positive plumbing closes in a deterministic fixture-shaped harness. More positive-route real fixture evidence is still needed before treating `ready_for_svg_polish` as a routine production art-direction handoff.

Falsified directions kept on record in `docs/historical/` and the relevant `architecture-v0.X-*.md` files: Python+SVG-from-scratch, LLM-as-quality-judge, perception auto-detection.

---

## Documentation map

**Read these first:**
- `docs/architecture-overview.md` — the layer-by-layer reference. Start here.
- `docs/v0.9-operator-playbook.md` — release-candidate command sequence for
  single-fixture, queue, host critique, closeout, and release/golden operation.
- `docs/quality-kernel-goal.md` — current product direction.
- `docs/architecture-v0.5-per-panel-reference-workflow.md` — how `/fig_critique` works now.
- `docs/milestones-archive/2026-05-17-quality-state-hardening.md` — current issue record for reference contracts, readiness states, manifest hashes, and TIFF quality gates.

**Topic deep-dives:**
- `docs/architecture-v0.4.2-perception-data-only.md` — the perception data pack.
- `docs/golden-target-trap-depth-picture.md` — Golden Target 001 spec.
- `docs/golden-target-001-retrospective.md` — N=1 evidence + gap list.
- `docs/macros/` — macro API docs (band-diagram, bell-curve, plot-callout).
- `docs/trials/` — dated dogfood reports.

**Frozen historical (do not maintain, kept for context):**
- `docs/historical/design-v0.1.md` — the v0.1 prompt/preview/selection-notes workflow that was removed in v0.2.
- `docs/historical/roadmap-v0.1.7-selection-notes.md` — rollout decisions superseded by the quality-kernel goal.

---

## Power-user notes

- **Strict mode.** `FIGURE_AGENT_STRICT=1` promotes collision/clash findings to hard fail. Useful in CI; off by default so build PNG stays available during iteration.
- **Golden fixture gate.** `check_golden_artifacts.py` auto-escalates when `spec.yaml` declares the `accepted` key (`true` or `false`). Override with `--no-require-accepted` for ad-hoc inspection.
- **Skip critique on export.** `fig-agent export <name> --skip-critique` for intentional drafts. Otherwise, when a declared reference image is usable, missing/stale `critique.md` blocks export. Declared-but-missing references are configuration errors and are not bypassed by `--skip-critique`.
- **Status vector.** `/fig_status` prints `render_state`, `critique_state`, `export_state`, `acceptance_state`, `final_artifact_state/kind/path`, `workflow_ready`, `golden_ready`, `release_ready`, and `final_ready`. Treat `final_ready` as a compatibility alias for `release_ready`; use `workflow_ready` when checking ordinary draft closure. Final-artifact fields are compatibility output for the generated export, not a second polished-SVG release gate.
- **Plugin install.** Validate with `claude plugin validate .claude-plugin/plugin.json`, `claude plugin validate .`, and `claude plugin validate ../../.claude-plugin/marketplace.json`. Test with `uv run pytest` and `uv run ruff check .`. `uv build` is *not* a release gate.
- **Plugin install freshness.** Local installs copy the registered marketplace working directory into `~/.claude/plugins/cache/`. Run `fig-agent helper plugin_install_freshness.py` to compare the development plugin tree with the latest local cache and emit `figure-agent.plugin-install-freshness.v1` JSON (`fresh`, `stale`, `missing`, or `invalid`) plus `source_package_hygiene`, `source_git_hygiene`, `marketplace_source_hygiene`, `installed_package_hygiene`, and `installed_example_source_hygiene`; `--json` and `--format json` are accepted as explicit no-op output flags. The command exits `0` only when source/install freshness is `fresh`, source package hygiene is `clean`, source git hygiene is `clean` or unavailable outside git, marketplace source hygiene is `clean` or unavailable, installed package hygiene is `clean`, and installed example source hygiene is `clean`. Follow the emitted `next_action`: different-version stale installs use `claude plugin update figure-agent@figure-agent-local`; same-version stale installs need uninstall + install because Claude does not recopy an already-latest version. If a package hygiene block is `dirty`, run its shell-quoted emitted `next_action`, which calls `fig-agent helper plugin_package_audit.py ... --clean --max-mib 300`, to remove generated build/cache paths and confirm future installs will not copy package junk. During an evidence pass, use `fig-agent helper plugin_package_audit.py ... --clean --preserve-fixture-artifacts --max-mib 300` only when you want to remove cache/virtualenv junk while keeping current `examples/<name>/build` and `exports` evidence for queue or driver inspection; do not use that narrower mode as final package validation. If `source_git_hygiene` is `dirty`, commit, stash, or move aside plugin-root changes before reinstalling so user figure-source edits are not copied into the installed plugin cache as "fresh" plugin state. If `marketplace_source_hygiene` is `dirty`, update the `figure-agent-local` marketplace registration before trusting a raw `claude plugin install`, because Claude installs from the registered marketplace source rather than the current shell directory. If `installed_example_source_hygiene` is `dirty`, reinstall from a clean source tree before trusting installed examples; payload freshness intentionally ignores `examples/`, so this separate hygiene block catches installed example-source drift without treating generated example build products as payload drift. The package audit is conservative in a development git worktree: tracked files and tracked-containing directories are protected from `--clean`.
- **Detector tuning ledger.** Run `fig-agent helper detector_feedback_ledger.py [fixture ...]` to aggregate existing audit-evidence detector feedback across selected fixtures, or across all `examples/*/critique.md` files when no fixture is selected. The output is read-only `figure-agent.detector-feedback-ledger.v1` JSON that separates detector candidates, accepted false positives, detector-linked defects, and unlinked micro-defects for tuning review; `--json` and `--format json` are accepted as explicit no-op output flags.
- **Repo location.** Lives under `~/workspace/ResearchOS/` as a sibling to `[Athena]/` and `[Graph_making_hub]/` for development proximity. Plugin install copies to `~/.claude/plugins/cache/…` regardless.

---

## History

Successor to `[tikz-paper-workflow]/` (archived 2026-04-27). The v0.1 prompt-template / preview-selection workflow is preserved only in `docs/historical/`. Active development is the quality kernel: Style Lock, macro quality, compile/export reliability, visual QA, and reproducibility.
