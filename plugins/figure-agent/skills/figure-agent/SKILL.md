---
name: figure-agent
description: Use for paper-figure quality, compile, export, and reproducibility gates around scientific schematics. A human or any LLM/tool may author the figure; figure-agent enforces Style Lock, compiles/exports, runs visual QA checks, and reports stale or unreplayable figure state. Prompt/image-gen helpers exist but are frozen legacy helpers, not the main development direction. **NOT for data plots** (quantitative axes, measurement curves, error bars) — those belong in matplotlib / Graph_making_hub.
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

## Quality-kernel workflow

Use this plugin first as a deterministic gate around editable figure source:

```
reference/source        → examples/<name>/briefing.md + optional reference_image
editable vector source  → examples/<name>/<name>.tex
/fig_compile <name>     → Style Lock + PDF/PNG build + collision/clash checks
/fig_export <name>      → PDF / SVG / TIFF / PNG accepted exports
/fig_status <name>      → stale/missing/replayability diagnosis
golden artifact checks  → rendered labels + SVG element floor + white PNG background
```

For golden fixtures, `reference_image` points to the fixed visual target. Do not
store that target in `selected_preview`; `selected_preview` means a user-chosen
candidate from `previews/`.

## Frozen legacy workflow (6 stages, slash-separated)

```
/fig_new <name>            step 1 — creates per-figure folder scaffold; HALTS for briefing
/fig_prompt <name>         step 2 — outputs normalized prompt block + audit; HALTS for user image-gen
(user works externally — no plugin involvement)
/fig_preview_select <name> step 3 — user selects preview; records in spec.yaml; HALTS for .tex authoring
/fig_compile <name>        step 4 — compiles .tex, applies Style Lock, runs clash checks; warns
/fig_review <name>         step 5 — emits Reviewer brief for external vision critique; HALTS
/fig_export <name>         step 6 — produces PDF + SVG + TIFF + PNG (600 dpi) into exports/
```

Run slash commands from the plugin root. `<name>` maps to `examples/<name>/`. After `/fig_preview_select`, authoring `examples/<name>/<name>.tex` is required; v0.1 does not create it automatically. These helpers remain available for old workflows, but do not expand them unless dogfooding proves a durable non-transient need.

**Status query** (not a workflow step): /fig_status <name> — infers stage from filesystem + spec.yaml; with no arg, summarizes all figures.

## Per-figure folder convention

```
examples/<name>/
├── spec.yaml          # scope/panels/style profile (lightweight, NOT single source of truth)
├── briefing.md        # human's intent in prose (used to seed prompt)
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
- Compile chain: `scripts/compile.sh` (lualatex)
- Checks: `scripts/check_collisions.py`, `scripts/check_visual_clash.py`
- Export: `scripts/export_svg.sh`, `scripts/svg_to_png.sh`
