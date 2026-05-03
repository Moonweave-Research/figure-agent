---
name: figure-agent
description: Use for paper-figure quality, compile, export, and reproducibility gates around scientific schematics. A human or any LLM/tool may author the figure; figure-agent enforces Style Lock, compiles/exports, runs visual QA checks, and reports stale or unreplayable figure state. Prompt/image-gen helpers exist but are frozen legacy helpers, not the main development direction. Symbolic schematic axes are inside scope; quantitative data plots and measured datasets belong in matplotlib / Graph_making_hub.
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

Prompt/image-gen orchestration from v0.1 remains available but frozen. Do not
expand it unless real dogfooding proves a repeated non-transient bottleneck.
Active direction: `docs/quality-kernel-goal.md`.

## Workflow shape

`/fig_new` is the shared entry point that scaffolds per-figure folders via
a conversational interview. After scaffolding, the workflow branches; both
paths land at the same `/fig_compile` and `/fig_export`, but only the
quality-kernel path is the active development direction.

### Active (quality kernel)

```
/fig_new <name>          scaffold (briefing + spec)
                         [user saves reference PNG and records it as
                          spec.yaml.reference_image when target matching matters]
/fig_extract <name>      reference PNG -> OCR + palette clusters + optional vtracer structural hints
                         -> coordinate_hints.yaml
                         [human/LLM authors semantic TikZ from briefing intent,
                          reference PNG, and coordinate_hints.yaml;
                          SVG-to-TikZ path conversion is not the active workflow]
/fig_compile <name>      Style Lock + PDF/PNG build + collision/clash + drift check
                         (FIGURE_AGENT_STRICT=1 promotes findings to hard fail)
/fig_export <name>       PDF / SVG (dvisvgm preserves text) / TIFF / PNG
/fig_status [<name>]     stage + accepted-state inference; legacy hints carry a [legacy] marker
```

Agent rule: when `coordinate_hints.yaml` exists, read it before authoring or
reviewing `<name>.tex`. Use OCR labels, palette clusters, and optional vtracer
structural hints as evidence for layout and color placement. Do not convert SVG
paths into the final TikZ source; produce semantic TikZ macros and named
drawing constructs that remain editable during manuscript revision. The handoff
is `coordinate_hints.yaml -> semantic TikZ authoring`.

Golden fixtures declare `accepted` + `golden_contract` in `spec.yaml`;
`check_golden_artifacts.py` auto-escalates into accepted mode when the key is
present. Override with `--no-require-accepted` for ad-hoc inspection.

For golden fixtures, `reference_image` points to the fixed visual target. Run
`/fig_extract` to create `coordinate_hints.yaml` from that target before
authoring or drift review. Do not store that target in `selected_preview`;
`selected_preview` means a user-chosen candidate from `previews/` and belongs
to the legacy path only.

### Frozen legacy (reduced to one helper after v0.2 cleanup)

```
/fig_review <name>           emit reviewer brief for external vision LLM
                             [HALT — user critiques, revises .tex]
                             (becomes /fig_critique with host-LLM orchestration in v0.2)
```

`/fig_prompt`, `/fig_preview_select`, the prompt-template / redaction /
selection-notes pipeline, and their auxiliary scripts were removed in the
v0.2 frozen-legacy cleanup. See `docs/architecture-v0.2-proposal.md`.

**Status query** (not a workflow step): /fig_status <name> — infers stage from filesystem + spec.yaml; with no arg, summarizes all figures.

## Per-figure folder convention

```
examples/<name>/
├── spec.yaml          # scope/panels/style profile (lightweight, NOT single source of truth)
├── briefing.md        # human's intent in prose (used to seed prompt)
├── reference/         # optional saved reference PNGs for target matching
├── coordinate_hints.yaml # /fig_extract authoring hints from reference_image
├── previews/          # user-generated draft images saved under examples/<name>/previews/
├── selected/          # optional symlink or copy of chosen preview
├── <name>.tex         # human/LLM-authored TikZ source
├── build/             # compile artifacts (gitignored)
└── exports/           # final PDF/SVG/TIFF/PNG (gitignored — checked in only on release)
```

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
- Export: `scripts/export_svg.sh`, `scripts/svg_to_png.sh`
