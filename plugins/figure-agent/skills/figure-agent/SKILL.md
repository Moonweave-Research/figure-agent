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
```

Agent rule: when `coordinate_hints.yaml` exists, read it before authoring or
reviewing `<name>.tex`. Use OCR labels, palette clusters, and optional vtracer
structural hints as evidence for layout and color placement. Do not convert SVG
paths into the final TikZ source; produce semantic TikZ macros and named
drawing constructs that remain editable during manuscript revision. The handoff
is `coordinate_hints.yaml -> semantic TikZ authoring`.

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

For schema v1.8 critiques, treat intra-instrument label failures as named
micro-defects rather than generic polish comments: use
`label_backdrop_overflows_outline` when a label fill/backdrop protrudes outside
its enclosing box, and `label_glyph_overlaps_internal_drawing` when a label or
backdrop crosses an internal display, axis, needle, or separator in the same
box. `BLOCKER` and `MAJOR` instances must link to a normal finding or be
explicitly marked `accept_simplification`. When the brief lists Visual Clash
Candidates, every `VC###` id must appear in exactly one
`micro_defects[].visual_clash_ref` entry; accepted candidates still need an
explicit `accept_simplification` rationale.
The critique must also fill `crop_audit_log` with exactly one entry for every
`build/audit_crops/manifest.json.required_crop_ids` item; uncertain crop
verdicts must remain explicit rather than being treated as pass.
When `critique_reference_pack.yaml` exists, `/fig_critique` uses it as the
project-specific top-tier calibration source and includes its target journal,
reference class, must-match traits, must-avoid traits, and calibration
questions in the brief.

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
