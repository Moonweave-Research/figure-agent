---
name: figure-agent
description: Use when generating publication-grade scientific **schematics** for papers — mechanism diagrams, band structures, conceptual flows, comparison schematics. **NOT for data plots** (quantitative axes, measurement curves, error bars) — those belong in matplotlib / Graph_making_hub. Workflow halts after prompt generation so user produces draft images in any external tool (ChatGPT / Gemini / Nano Banana / Midjourney / local SD), then resumes for human/LLM-authored TikZ compile, checks, and export. Plugin handles prompt intent control + deterministic vector finishing only — no image-gen API calls. Trigger on "figure 만들어 / paper figure / nature figure / schematic 그려줘 / fig new".
---

# figure-agent SKILL

## Plugin Identity

**Scope: schematic only.** Mechanism diagrams, band structures, conceptual flows, potential
wells, comparison schematics, isometric device stacks — qualitative figures whose value comes
from clarity of concept rather than precision of numerical data. **Data plots are out of
scope** (see Boundaries below).

Two responsibilities, no more:

1. **Prompt intent control** — produce one prompt block that preserves the author's
   scientific mechanism and visual hierarchy while normalizing distracting literals such as
   exact counts, sample labels, dimensions, and experimental conditions.
2. **Human/LLM-in-the-loop vector finishing** — selected preview is inspiration only. v0.1
   does not automatically vectorize preview images; it compiles/checks/exports TikZ authored
   by a human, an LLM, or both.

Image generation itself is **not** a plugin responsibility. User picks any external tool and
saves PNG/JPG/JPEG output to `examples/<name>/previews/`.

## Workflow (6 stages, slash-separated)

```
/fig_new <name>            step 1 — creates per-figure folder scaffold; HALTS for briefing
/fig_prompt <name>         step 2 — outputs normalized prompt block + audit; HALTS for user image-gen
(user works externally — no plugin involvement)
/fig_preview_select <name> step 3 — user selects preview; records in spec.yaml; HALTS for .tex authoring
/fig_compile <name>        step 4 — compiles .tex, applies Style Lock, runs clash checks; warns
/fig_review <name>         step 5 — emits Reviewer brief for external vision critique; HALTS
/fig_export <name>         step 6 — produces PDF + SVG + TIFF + PNG (600 dpi) into exports/
```

Run slash commands from the plugin root. `<name>` maps to `examples/<name>/`. After `/fig_preview_select`, authoring `examples/<name>/<name>.tex` is required; v0.1 does not create it automatically.

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

- **No data plots.** Quantitative axes (n vs composition, I(t) curves, DOS spectra, etc.),
  measurement curves derived from real data, error bars → out of scope. Redirect user to
  matplotlib or Graph_making_hub. *Schematic mockups* of these (qualitative shape only, no
  numbers, no axis ticks, illustrative-only) are inside scope — but if the user names
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

- Quantitative variable symbols: `n`, `τ`, `V`, `I`, `T`, `t`, `E_t`, `g(E_t)`, etc.
- Sweep / vs phrasing: "vs composition", "vs time", "ratio", "sweep S60..S85"
- Measurement keywords: "raw + fit", "error bar", "peak position", "RLM MM", "ISPD curves"
- Real-data axes: any axis whose tick values would matter to a reader

## Asset references

- Style Lock source: `styles/polymer-paper-preamble.sty` (\IsoCharge, \GradSlab, \IsoBlock, \IsoConeTip)
- Compile chain: `scripts/compile.sh` (lualatex)
- Checks: `scripts/check_collisions.py`, `scripts/check_visual_clash.py`
- Export: `scripts/export_svg.sh`, `scripts/svg_to_png.sh`
