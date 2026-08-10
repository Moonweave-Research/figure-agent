---
name: figure-agent
description: Use for paper-figure quality, compile, export, and reproducibility gates around scientific schematics. A human or any LLM/tool may author the figure; figure-agent enforces Style Lock, compiles/exports, runs visual QA checks, and reports stale or unreplayable figure state. Deleted v0.1 prompt/image-gen commands are historical only. Symbolic schematic axes are inside scope; quantitative data plots and measured datasets belong in matplotlib / Graph_making_hub.
---

# figure-agent SKILL

## Plugin Identity

**Scope: schematic quality kernel.** Mechanism diagrams, band structures,
conceptual flows, potential wells, comparison schematics, isometric device
stacks — qualitative figures whose value comes from clarity of concept rather
than precision of numerical data. **Data plots are out of scope** (see
Boundaries below).

Durable responsibilities:

1. **Style Lock** — keep palette, fonts, macro usage, and figure-wide style
   consistent across a manuscript.
2. **Compile/export reliability** — produce PDF/SVG/TIFF/PNG artifacts from
   editable source without stale-output ambiguity.
3. **Visual QA** — run collision and render-based clash checks before manuscript
   use.
4. **Reproducibility** — keep per-figure folders, source, briefing, status, and
   exports auditable months later.

Prompt/image-gen orchestration from v0.1 is historical only in this plugin line.
Do not route users to deleted commands.
Read-only authoring context packs are durable paper-specific knowledge
compilation in scope when they compile explicit paper-local files, Style Lock
tokens, source-anchored rule catalogs, and opt-in semantic claims/invariants.
They are not prompt-loop revival, generation execution, or automatic physics
detection.
For mechanism figures, a prose physics section plus one arrow assertion is not
scientific validation. When a fixture sets `semantic_contract_required: true`,
its coordinate-free semantic contract must declare the objects, visible
relations, and forbidden readings before strict compile can pass. Keep
unresolved electrical topology explicit; never infer a charging instrument,
contact, ground path, or measurement stage from the word “charging”. This
contract constrains meaning, not the author's TikZ style or primitive choices.
Every rendered force-direction connector must declare whether its direction is
observed, derived, or conditional. A conditional force direction needs its
visible condition and must use a conditional force style; never let a
plausible-but-unverified arrow read as a measured vector. A panel declared as
an observed comparison must bind a source-traceable evidence asset. Until that
asset is selected, call the panel a schematic state comparison or remove it;
do not silently upgrade a redraw into evidence.
For a staged causal mechanism story, treat a boundary-changing intermediate
state as its own reader-facing step: preparation -> isolation -> perturbation
-> response. Do not compress isolation into an arrow caption and then spend a
panel on a duplicated result-state cartoon. Declare this opt-in causal sequence
in the semantic contract before authoring the detailed composition.
Keep superseded rules in catalog provenance, but exclude them from authoring
context so stale hypotheses cannot compete with later human-confirmed rules.
Before product-level work, read `docs/figure-agent.md`. It is the sole active
product specification and forward execution roadmap. Treat other specs, plans,
roadmaps, and milestones as scoped evidence unless that authority explicitly
delegates to them.

## Dogfood routing boundary

For **Figure Agent dogfood** or product-development work, this skill and the
repo-local Figure Agent commands take priority over generic TikZ refinement.
Do not automatically invoke `tikz`, `tikz-refine`, or another external drawing
skill merely because the editable representation is TeX/TikZ. A specialist is
an explicit user-selected tool, not an implicit dependency of Figure Agent.

Keep the authoring model free to redraw or replace constructions. Review the
rendered meaning, attribute a real defect, and constrain the repair boundary;
do not force a reusable primitive or specialist coordinate recipe. If whole,
panel, and print-reduction review finds **no defensible defect**, preserve the
source unchanged and record the review basin. Compile-generated and ignored
build artifacts are verification evidence, not product edits; do not delete,
stage, or count them as the source change required to make a review succeed.

## Runtime Entrypoint

Use `fig-agent ...` for shell commands. If `fig-agent` is not on `PATH`, use
`"${CLAUDE_PLUGIN_ROOT}/bin/fig-agent" ...`.

The installed plugin bundle and user figure workspace are separate. Bundled
tools/styles come from `FIGURE_AGENT_PLUGIN_ROOT` or `CLAUDE_PLUGIN_ROOT`;
figure fixtures come from `FIGURE_AGENT_WORKSPACE` or `CLAUDE_PROJECT_DIR`.
Successful compiles bind the PDF to the content hashes of the authored source,
briefing, spec, and Style Lock in `build/<name>_render_inputs.json`. When that
manifest exists, judge render freshness from its hashes rather than file mtimes
or installation paths: copying identical Style Lock bytes into a newer plugin
cache must remain fresh, while byte drift must become stale even if timestamps
are older. Missing manifests retain legacy mtime compatibility; invalid or
incomplete manifests fail closed.

## Workflow shape

`/fig_new` is the shared entry point that scaffolds per-figure folders via
a conversational interview. After scaffolding, author semantic TikZ from the
briefing, optional reference image, and optional coordinate hints.

For reference-conditioned authoring pilots, read
`examples/<name>/authoring_contract.md` and
`examples/<name>/reference/reference_pack.md` before editing TikZ. Write or
refresh `examples/<name>/authoring_plan.md` first, naming the panel/sub-region
patch order, theory-critical decisions, and human checkpoints. The first TikZ
patch must trace back to the plan rather than to chat-only intent.

### Driver rule for agents

Unless the user explicitly asks for a specific low-level command, start every
figure workflow by running `/fig_status <name>` and follow its `Next:` hint.
Do not choose between compile, critique, export, loop, polish, or release from
memory. `/fig_status` is the traffic controller.

Canonical next-action order:

1. If `render_state` is `MISSING` or `STALE`, run `/fig_compile <name>` first.
   Do not request host vision critique against a stale render.
2. If render is `FRESH` and `critique_state` is `MISSING`, `STALE`, or
   `REFERENCE_MISSING`, close that critique/reference gate next.
3. If critique is `FRESH` and `critique_adjudication.yaml` is missing, stale,
   or invalid, run `/fig_adjudicate <name>` or repair the adjudication file.
4. Run `/fig_loop <name> --goal "<goal>"` only after status prerequisites are
   closed enough to record a meaningful verify-only checkpoint.
5. Run `/fig_export`, release, or SVG polish only when `/fig_status` or
   `/fig_drive --dry-run` explicitly routes there.
6. For final submission or "am I done?" checks, use
   `/fig_drive <name> --mode final --goal "final readiness" --dry-run`. This is
   the non-mutating final-readiness preset: it explains the required actor,
   surfaces the strict compile final check, requires a current verify-only
   `/fig_loop` checkpoint before `complete`, and preserves human
   accepted/golden/publication boundaries.

If the user asks to proceed autonomously on one fixture, use
`/fig_run <name> --mode <mode> --goal "<goal>" --execute` rather than manually
copy-pasting each safe driver command. `/fig_run` is bounded: it executes
compile, missing adjudication scaffold, verify-only loop checkpoint commands,
and non-golden draft export, then stops at host critique, existing adjudication
repair, patch, polish, human, accepted, tracked-golden, force-golden, and
release boundaries. It records non-authoritative `.scratch/fig-run-runs/`
evidence in execute mode. There is no resume command; after any interruption,
run `fig-agent helper fig_run_journal.py <name>` to summarize the prior
stop, then rerun live `/fig_status` or `/fig_drive` before using
`/fig_run --execute` again. Do not replay commands from a journal.

For the first canonical lifecycle state after a fresh real render, require one
explicit `--closed-loop-attempt-manifest <manifest.json>` on `/fig_run`; never
discover it adjacently. The manifest must bind fixture, named authoring-agent
identity/role, source/render paths and hashes, task/model/budget provenance, and
`publication_acceptance: not_claimed`. Plan-only validates and reports the
proposed `authored_rendered` path without writing. Execute revalidates under the
shared transition lock, publishes only that root state, and stops. This is
lifecycle admission, not prospective defect proof, visual acceptance, or
publication acceptance; do not synthesize any critique, review, repair,
authorization, verdict, accepted, or golden evidence in this step.

When canonical status is `repair_bound`, pass all of
`--closed-loop-repair-packet <v4.json>` and
`--closed-loop-candidate-response <response.json>` and
`--closed-loop-materialization-preview <preview.json>` to `/fig_run`. The run
recomputes the preview from this explicit triplet, validates it against the
state binding, and only publishes
`repair_candidate_ready`; it does not discover candidate files, invoke a model,
materialize source, or cross the named-human authorization boundary.
Retired pre-R4.8 candidate leaves cannot restart in place. Use
`fig-agent helper closed_loop_legacy_candidate_quarantine.py --fixture <name> --state <leaf.json> --authorization <record.json> --execute`
only as an explicit preservation step; it moves no evidence until `--execute`,
requires a named-human record bound to the exact leaf path/state/file hashes,
preserves both outside discovery, and re-exposes only its verified `repair_bound`
parent.

If the user asks to "use figure-agent to improve this", "loop 10 times", or
"keep reviewing and polishing until no major issues remain" for one fixture,
use `/fig_status` and then rerun the canonical bounded `/fig_run` after each
host, human, or repair boundary. `/fig_improve` remains a compatibility wrapper
over `/fig_run`; it is not a separate default workflow and does not reactivate
autonomous quality search.

When an LLM or human directly changes the `.tex` source outside the candidate
pipeline, do not retrofit a candidate outcome or infer a win from compile
success. After a fresh strict compile, use `fig-agent record-manual-edit <name>
--edit-family <free-description> --target-panel <panel> --target-subregion
<free-description> --rationale <why>`; add `--decision accept|reject --reviewer
<name>` only for a real human verdict. This preserves free redraw while keeping
learning evidence auditable and reward truth conservative.

If the user asks to proceed autonomously across multiple fixtures, start with
the queue:

1. `fig-agent queue --mode review --goal "<goal>"`
2. `fig-agent queue --mode review --goal "<goal>" --actor host_llm`
3. `fig-agent queue --mode review --goal "<goal>" --actor workflow_agent --command-plan --json`
4. `fig-agent queue-run --mode review --goal "<goal>" --actor workflow_agent`
5. Add `--execute` only after reading the plan-only queue-run output.

`/fig_queue_run` never executes queue commands directly. It delegates each
planned fixture to `/fig_run`, so live driver revalidation remains the execution
gate. Human, release/golden, host-vision, and SVG-polish rows stay explicit
boundaries. For blocked command-plan rows, read `operator_handoff` for the
required actor, next step, allowed scope, forbidden scope, and closeout checks.

Use modes mentally:

- `authoring`: source edits and `/fig_compile`; rerun `/fig_status <name>`
  between compiles to confirm `render_state: FRESH` before promoting work.
  Forbidden: export, critique, adjudication, accepted/golden mutation, SVG
  polish.
- `review`: close compile, critique, adjudication, and `/fig_loop` evidence,
  one patch target at a time. Forbidden: hidden source editing, automatic host
  critique authoring, final SVG polish, accepted/golden mutation.
- `release`: check accepted/golden/final artifact readiness. Forbidden:
  changing `accepted`, forcing golden overwrite, creating polished SVG, hiding
  unresolved findings.
- `polish`: start only after generated export is current and the remaining
  work is visual-only SVG finalization. Forbidden: editing generated
  `exports/`, treating polish as source repair, setting `accepted: true`,
  bypassing semantic backport.
- `final`: non-mutating final-readiness check. It reuses release gates, shows
  strict compile as the final render check, and emits one plain operator
  instruction. Forbidden: forcing golden, setting accepted state, editing
  source/SVG, or mutating publication evidence.

`/fig_loop` is a verify-only checkpoint. It records state and patch handoff
evidence; it does not compile, export, critique, patch, polish, accept, or
commit. Stop for host LLM critique, missing reference inputs, ambiguous patch
selection, human gates, accepted/golden promotion, `--force-golden`, semantic
polish backport, or actions the current mode forbids.

### Active (quality kernel)

```
/fig_new <name>          scaffold (briefing + spec)
                         [user saves reference PNG and records it as
                          spec.yaml.reference_image when target matching matters]
                         [for multi-panel target matching, user may save panel
                          reference PNGs under reference/ and record
                          panels[].reference_image plus panels[].bbox_pdf_cm;
                          run `fig-agent helper spec_bbox_helper.py` to compute bboxes]
/fig_extract <name>      reference PNG -> OCR + palette clusters + optional vtracer structural hints
                         -> coordinate_hints.yaml
                         [human/LLM authors semantic TikZ from briefing intent,
                          reference PNG, and coordinate_hints.yaml;
                          SVG-to-TikZ path conversion is not the active workflow]
                         [reference-conditioned pilots: contract/reference pack
                          -> authoring_plan.md -> scoped TikZ patch]
/fig_compile <name>      Style Lock + PDF/PNG build + collision/clash + drift check
                         + perception data pack (extract.yaml + overlay.png)
                         (FIGURE_AGENT_STRICT=1 promotes findings to hard fail)
/fig_record_manual_edit <name>
                         append direct-source-edit provenance only after strict,
                         semantic-hash, and 100%/50%/33% render evidence agree;
                         compile success is never a reward. Pass a human verdict
                         only after a human reviewed these exact source bytes.
/fig_critique <name>     required before export when usable reference grounding exists
/fig_ground <name>       author tex/semantic assertions from briefing §6/§7 so a
                         reversed force/bend direction is fail-loud (Layer 2)
/fig_adjudicate <name>   scaffold critique_adjudication.yaml from critique.md
                         after `fig-agent helper critique_lint.py <name>`;
                         unresolved findings default to needs_human
/fig_loop <name> --goal "<goal>"
                         verify-only loop evidence record under .scratch/fig-loop-runs/
/fig_closeout <name>    read-only post-patch checklist for compile, critique,
                         adjudication, export, and loop rerun freshness
/fig_context_pack <name>
                         read-only authoring context pack for explicit
                         briefing/spec/design/style/rule/semantic contracts
/fig_export <name>       candidate-aware PDF / outlined SVG / TIFF / PNG;
                         export never promotes or accepts a candidate
/fig_e2e_smoke <name>    deterministic compile/export/status/loop smoke harness
/fig_status [<name>]     stage + render/critique/export/acceptance/final_ready state inference
/fig_drive <name> --mode <mode> --goal "<goal>" --dry-run
                         read-only next-action selector
/fig_run <name> --mode <mode> --goal "<goal>" --execute
                         bounded executor for safe mechanical steps; stops at gates
                         and writes non-authoritative .scratch/fig-run-runs/
                         evidence; no resume/replay command exists
/fig_improve <name> --goal "<goal>" --execute --max-loops N
                         compatibility wrapper over /fig_run; not the default route
/fig_queue --mode <mode> --goal "<goal>"
                         read-only multi-fixture driver queue with actor/action
                         filters and optional command plan
/fig_queue_run --mode <mode> --goal "<goal>"
                         plan or execute the queue's workflow-agent subset by
                         delegating each fixture to /fig_run
```

Agent rule: when `coordinate_hints.yaml` exists, read it before authoring or
reviewing `<name>.tex`. Use OCR labels, palette clusters, and optional vtracer
structural hints as evidence for layout and color placement. Do not convert SVG
paths into the final TikZ source; produce semantic TikZ macros and named
drawing constructs that remain editable during manuscript revision. The handoff
is `coordinate_hints.yaml -> semantic TikZ authoring`.

When moving a panel/subregion by a fixed offset, prefer the scoped dry-run
helper over ad-hoc regex scripts:
`fig-agent helper tex_coordinate_shift.py examples/<name>/<name>.tex --line START:END --dx <cm> --dy <cm>`.
Inspect the diff first; add `--write` only after confirming the selected line
range is exactly the intended patch scope. The helper intentionally does not
infer visual scope or parse arbitrary TikZ expressions.

Golden fixtures declare `accepted` + `golden_contract` in `spec.yaml`;
`check_golden_artifacts.py` auto-escalates into accepted mode when the key is
present. Override with `--no-require-accepted` for ad-hoc inspection. Keep
`/fig_compile` report-only during authoring so the PNG/PDF are produced for
human visual review; the perception data pack is always emitted under
`build/perception/` after successful render. Use `FIGURE_AGENT_STRICT=1` for
manuscript/CI checks and `check_golden_artifacts.py --require-accepted` for the
golden hard gate.

For golden fixtures, `reference_image` points to the fixed visual target. Run
`/fig_extract` to create `coordinate_hints.yaml` from that target before
authoring or drift review.

### Vision critique routing

For `/fig_critique`, figure authoring or review, rendered-defect adjudication,
or final rendered inspection, open `references/vision-critique-rubric.md` and
read it completely before judging or editing the figure. That reference carries
the detailed L4.5 rendered-meaning, morphology,
composition, print, and critique-schema rules; this entry skill carries routing
and workflow authority.
The vision-capable host may be Codex or Claude; the plugin remains report-only
and makes no external vision API call.

Do not load the reference for status, compile, export, packaging, or other
mechanical-only work unless the task also requires visual interpretation. Project-
and paper-specific authoring rules are selected and injected by the authoring
context pack; do not duplicate those catalogs into this entry skill.

## Per-figure folder convention

```
examples/<name>/
├── spec.yaml          # scope/panels/style profile (lightweight, NOT single source of truth)
├── briefing.md        # human's intent in prose (used to seed prompt)
├── reference/         # optional saved reference PNGs for target matching
├── coordinate_hints.yaml # /fig_extract authoring hints from reference_image
├── previews/          # user-generated draft images saved under examples/<name>/previews/
├── <name>.tex         # human/LLM-authored TikZ source
├── build/             # compile artifacts (gitignored)
└── exports/           # final PDF/SVG/TIFF/PNG (gitignored — checked in only on release)
```

`selected/` and selected-preview metadata are v0.1 legacy surfaces, not part of
the active workflow.

## Boundaries

- **No data plots.** Quantitative axes (n vs composition, measured I(t) curves, DOS spectra, etc.),
  measurement curves derived from real data, error bars → out of scope. Redirect user to
  matplotlib or Graph_making_hub. *Schematic mockups* of symbolic axes are inside scope
  when the axis labels are conceptual, tick values are illustrative or absent, and no
  measured numeric values are encoded. If the user names
  numerical sweep ranges (S60-S85), peak positions (S70-S75), or specific measurement values,
  that is the data-plot signal and belongs elsewhere.
- **No image-gen API call** in any step. If user asks for one, decline and remind them this
  plugin is gen-tool-agnostic.
- **No reference image retrieval** (Crossref/Semantic Scholar/PaperBanana paths deprecated).
- **No "single source of truth" YAML spec.** spec.yaml is lightweight (panels + style
  profile). Meaning lives in briefing.md and the .tex source.

### Scope-drift signals during interview

When `/fig_new` is collecting the briefing, watch for these red flags in user answers and
**ask the user to confirm intent before continuing** ("data figure → reframe to schematic, or
redirect to matplotlib?"):

- Quantitative variable symbols tied to measured values or fitted datasets: `n`, `τ`, `V`, `I`, `T`, `t`, `E_t`, `g(E_t)`, etc.
- Sweep / vs phrasing: "vs composition", "vs time", "ratio", "sweep S60..S85"
- Measurement keywords: "raw + fit", "error bar", "peak position", "RLM MM", "ISPD curves"
- Real-data axes: any axis whose tick values would matter to a reader

## Asset references

- Cowork path rule: run the automated pipeline from the source plugin root
  (`plugins/figure-agent`) or another workspace where `scripts/`, `styles/`,
  and `examples/` are siblings. If those directories are missing from the
  current working directory, treat it as a mount/working-directory issue, not as
  a missing installed-plugin bundle.
- Style Lock source: `styles/polymer-paper-preamble.sty` (\IsoCharge, \GradSlab, \IsoBlock, \IsoConeTip)
- Compile chain: `scripts/compile.sh` (lualatex; optional `FIGURE_AGENT_STRICT=1`
  hard gate)
- Physical print contract: every strict fixture must declare
  `spec.yaml.final_size_contract` with `natural_size_mm`, `target_width_mm`,
  `max_height_mm`, and `min_print_font_pt`. The compile gate checks the PDF
  page geometry and the smallest explicit `\\fontsize` declaration at the
  height-limited placement scale. A fresh PNG alone is not print-size evidence.
  A prospective review source may instead declare a sibling
  `<source-stem>.authority.yaml` print contract when its deliberate composition
  changes natural page geometry. That sidecar applies only to that source's
  physical measurement and cannot change canonical acceptance, semantic
  contracts, or promotion state.
- Checks: `fig-agent helper check_collisions.py`, `fig-agent helper check_visual_clash.py`
- Perception pack: `scripts/perception_pack.py` writes
  `build/perception/extract.yaml` and `build/perception/overlay.png`
- Export: `scripts/export_svg.sh`, `scripts/svg_to_png.sh`
