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
Active direction: `docs/quality-kernel-goal.md`.

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

If the user asks to proceed autonomously on one fixture, use
`/fig_run <name> --mode <mode> --goal "<goal>" --execute` rather than manually
copy-pasting each safe driver command. `/fig_run` is bounded: it executes
compile, missing adjudication scaffold, verify-only loop checkpoint commands,
and non-golden draft export, then stops at host critique, existing adjudication
repair, patch, polish, human, accepted, tracked-golden, force-golden, and
release boundaries. It records non-authoritative `.scratch/fig-run-runs/`
evidence in execute mode. There is no resume command; after any interruption,
inspect the prior journal only as context, then rerun live `/fig_status` or
`/fig_drive` before using `/fig_run --execute` again.

If the user asks to proceed autonomously across multiple fixtures, start with
the queue:

1. `uv run python3 scripts/fig_queue.py --mode review --goal "<goal>"`
2. `uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor host_llm`
3. `uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor workflow_agent --command-plan --json`
4. `uv run python3 scripts/fig_queue_run.py --mode review --goal "<goal>" --actor workflow_agent`
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
                          run scripts/spec_bbox_helper.py to compute bboxes]
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
/fig_critique <name>     required before export when usable reference grounding exists
/fig_adjudicate <name>   scaffold critique_adjudication.yaml from critique.md
                         after `uv run python3 scripts/critique_lint.py <name>`;
                         unresolved findings default to needs_human
/fig_loop <name> --goal "<goal>"
                         verify-only loop evidence record under .scratch/fig-loop-runs/
/fig_closeout <name>    read-only post-patch checklist for compile, critique,
                         adjudication, export, and loop rerun freshness
/fig_export <name>       PDF / SVG (dvisvgm preserves text) / TIFF / PNG
/fig_status [<name>]     stage + render/critique/export/acceptance/final_ready state inference
/fig_drive <name> --mode <mode> --goal "<goal>" --dry-run
                         read-only next-action selector
/fig_run <name> --mode <mode> --goal "<goal>" --execute
                         bounded executor for safe mechanical steps; stops at gates
                         and writes non-authoritative .scratch/fig-run-runs/
                         evidence; no resume/replay command exists
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
`uv run python3 scripts/tex_coordinate_shift.py examples/<name>/<name>.tex --line START:END --dx <cm> --dy <cm>`.
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

### L4.5 Vision Critique (host-orchestrated)

```
/fig_critique <name>         host Claude reads build/<name>.png + briefing,
                             plus any panel crop/reference pairs declared by
                             panels[].reference_image + panels[].bbox_pdf_cm,
                             writes structured critique.md (YAML + Markdown).
                             Report-only; subscription tokens, zero external API.
```

When a usable figure-level reference image or panel reference+bbox pair exists,
`/fig_status` and `/fig_export` promote missing/stale `critique.md` to a
pre-export checkpoint. Use `scripts/run_export.py <name> --skip-critique` only
for intentional draft exports.

`/fig_loop <name> --goal "<goal>"` records a single verify-only loop checkpoint
under `.scratch/fig-loop-runs/`. It shares `/fig_status` state inference and
records `critique_adjudication.yaml` as missing, fresh, stale, or invalid when
present. It does not patch source, compile, export, accept artifacts, or mutate
git state.

Use `uv run python3 scripts/critique_lint.py <name>` after `/fig_critique
<name>` and before `/fig_adjudicate <name>` when `critique_adjudication.yaml`
is missing or stale. The lint preflight catches duplicate finding ids,
malformed critique frontmatter, and missing top-tier finding links before they
become loop state. `/fig_adjudicate` then scaffolds every panel-level and
top-level critique finding, stamps the current critique hash, and defaults
unresolved findings to `needs_human` so the loop cannot silently drop reviewer
findings.

For schema v1.8+ critiques, treat intra-instrument label failures as named
micro-defects rather than generic polish comments: use
`label_backdrop_overflows_outline` when a label fill/backdrop protrudes outside
its enclosing box, and `label_glyph_overlaps_internal_drawing` when a label or
backdrop crosses an internal display, axis, needle, or separator in the same
box. Use `label_crosses_column_rule`, `label_crosses_panel_boundary`, and
`label_overflows_row_box` for declared text-boundary candidates from
`build/text_boundary_clash.json`. Author or refresh verbose
`spec.yaml.text_boundary_checks` from `spec.yaml.text_boundary_layout` with
`uv run python3 scripts/text_boundary_spec_helper.py examples/<name> --write`
after adding row boxes, column rules, horizontal rules, or forbidden internal
rectangles. `BLOCKER` and `MAJOR` instances must link to a normal finding or
be explicitly marked `accept_simplification`. When the brief lists Visual Clash
Candidates, every `VC###` id must appear in exactly one
`micro_defects[].visual_clash_ref` entry; accepted candidates still need an
explicit `accept_simplification` rationale. When the brief lists Text Boundary
Clash Candidates, every `TB###` id must appear in exactly one
`micro_defects[].text_boundary_ref` entry. For schema v1.10+ critiques, every
accepted visual-clash candidate must also set `accept_simplification_reason` to
one of `false_positive`, `intentional_schematic`, `outside_target_region`,
`convention_acceptable`, or `decorative_background`, plus a non-empty
`accept_simplification_rationale`.
The critique must also fill `crop_audit_log` with exactly one entry for every
`build/audit_crops/manifest.json.required_crop_ids` item; uncertain crop
verdicts must remain explicit rather than being treated as pass.
When `critique_reference_pack.yaml` exists, `/fig_critique` uses it as the
project-specific top-tier calibration source and includes its target journal,
reference class, must-match traits, must-avoid traits, and calibration
questions in the brief.
When `spec.yaml.paper_aesthetic_context` is declared, `/fig_critique` resolves
`examples/_paper_aesthetic_contexts/<paper_id>.yaml` and emits a
`Paper-Wide Aesthetic Context` section. The critique must cite exact paper-wide
anchors in `top_tier_audit.cross_panel_semantic_grammar`,
`top_tier_audit.aesthetic_coherence`, and
`editorial_art_direction.visual_identity`; generic art-direction prose is
invalid once the fixture opts in.
When `spec.yaml.journal_art_direction_playbook` is declared, `/fig_critique`
resolves `examples/_journal_art_direction_playbooks/<playbook_id>.yaml` and
emits a `Journal Art-Direction Playbook` section. The critique must fill
`journal_art_direction_playbook_audit`, cite exact playbook anchors in the
required top-tier/editorial/journal assessment rationale slots, and tie those
anchors to current-artifact evidence; generic "looks polished" prose is
invalid once the fixture opts in.
When `aesthetic_intent.yaml` uses schema v2, `/fig_critique` emits an
`Aesthetic Lever Grammar` section and the critique must fill
`aesthetic_lever_audit` exactly once for every declared lever. The host critique
must cite exact aesthetic-intent anchors with current-artifact evidence in the
required top-tier/editorial slots and route each non-passing lever through a
visible TikZ patch, SVG polish, semantic backport, or human art-direction path;
generic "improve polish" prose is invalid. Non-passing levers must name concrete
anti-pattern evidence; active routes must match the declared `default_route`;
`svg_polish` requires `ready_for_svg_polish`, `semantic_backport` requires
`semantic_backport_required`, and `human_art_direction` must cite the explicit
human art-direction gate.

Use `/fig_closeout <name>` after a human or outer agent patches one loop-selected
target. It reports which closeout steps are still stale, missing, blocked, or
passed without running those steps itself. It withholds the final loop-rerun
action until prerequisites are closed and keeps golden roll-forward as manual
approval.

Replaces the v0.1 HALT-then-paste review surface via rename + extend
(`scripts/review_brief.py` → `scripts/critique_brief.py`,
`commands/fig_review.md` → `commands/fig_critique.md`). The old prompt-template,
redaction, preview-selection pipeline, and selected-preview stage gate were
deleted in PR #8a + #8b. See `docs/architecture-v0.2-proposal.md`.

**Status check** (canonical first step — see Driver rule for agents above): /fig_status <name> — infers stage plus render/critique/export/acceptance/final_ready state from filesystem + spec.yaml; with no arg, summarizes all figures. It is read-only (no persistent state written), but it is the workflow entry point, not a passive query.

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

- Style Lock source: `styles/polymer-paper-preamble.sty` (\IsoCharge, \GradSlab, \IsoBlock, \IsoConeTip)
- Compile chain: `scripts/compile.sh` (lualatex; optional `FIGURE_AGENT_STRICT=1`
  hard gate)
- Checks: `scripts/check_collisions.py`, `scripts/check_visual_clash.py`,
  `scripts/check_layout_drift.py` (auto-fires when `coordinate_hints.yaml` exists)
- Perception pack: `scripts/perception_pack.py` writes
  `build/perception/extract.yaml` and `build/perception/overlay.png`
- Export: `scripts/export_svg.sh`, `scripts/svg_to_png.sh`
