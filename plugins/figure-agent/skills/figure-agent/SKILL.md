---
name: figure-agent
description: Use when generating publication-grade scientific **schematics** for papers — mechanism diagrams, band structures, conceptual flows, comparison schematics. **NOT for data plots** (quantitative axes, measurement curves, error bars) — those belong in matplotlib / Graph_making_hub. Workflow halts after prompt generation so user produces draft images in any external tool (ChatGPT / Gemini / Nano Banana / Midjourney / local SD), then resumes for vector reconstruction. Plugin handles prompt confidence + vector compile only — no image-gen API calls. Trigger on "figure 만들어 / paper figure / nature figure / schematic 그려줘 / fig new".
---

# figure-agent SKILL

## Plugin Identity

**Scope: schematic only.** Mechanism diagrams, band structures, conceptual flows, potential
wells, comparison schematics, isometric device stacks — qualitative figures whose value comes
from clarity of concept rather than precision of numerical data. **Data plots are out of
scope** (see Boundaries below).

Two responsibilities, no more:

1. **Confident schematic prompt generation** — produce one text block that, copy-pasted into
   any modern image-gen tool, yields a usable scientific schematic on first try. Domain
   vocabulary, style block, composition hint, automatic redaction of numerical/condition/
   geometry leakage.
2. **Tight vector compile** — selected preview → SVG/TikZ deterministic reconstruction.
   Collision check, visual clash check, Style Lock, multi-panel alignment, revision-safe
   re-render from spec.

Image generation itself is **not** a plugin responsibility. User picks any external tool and
saves output to `previews/`.

## Workflow (5 stages, slash-separated)

```
/fig_new <name>          step 1
   → creates examples/<name>/{spec.yaml, briefing.md, previews/, build/, exports/}

/fig_prompt              step 2
   → reads spec.yaml + briefing.md
   → applies redaction (numbers, units, experimental conditions, geometry)
   → outputs ONE prompt block + redaction audit
   → tells user: "Copy this prompt to your image-gen tool of choice.
                  Generate 3-5 candidates. Save into examples/<name>/previews/
                  with any filename. Then run /fig_preview_select."
   → HALTS — slash exits

(user works externally — no plugin involvement)

/fig_preview_select      step 3
   → lists examples/<name>/previews/*.png|jpg
   → presents to user (numbered, alphabetical sort)
   → user picks 1
   → records selection in spec.yaml

/fig_compile             step 4
   → reconstructs selected preview as SVG/TikZ
   → applies Style Lock (font/color/thickness from styles/polymer-paper-preamble.sty)
   → runs check_collisions.py + check_visual_clash.py
   → reports WARN (does not block — human-gated)

/fig_export              step 5
   → produces PDF + SVG + TIFF (600 dpi) into examples/<name>/exports/
```

## Per-figure folder convention

```
examples/<figure_name>/
├── spec.yaml          # scope/panels/style profile (lightweight, NOT single source of truth)
├── briefing.md        # human's intent in prose (used to seed prompt)
├── previews/          # user-generated draft images (any filename, any format)
├── selected/          # symlink or copy of chosen preview
├── build/             # compile artifacts (gitignored)
└── exports/           # final PDF/SVG/TIFF (gitignored — checked in only on release)
```

## What the prompt must contain

- Domain vocabulary (specific terms — e.g., "charge trapping in polymer dielectric", not "charges in plastic")
- Style block (Nature schematic, white background, minimal labels, balanced composition)
- Composition hint (panel layout, flow direction, arrow semantics)
- Negative prompt (no numerical values, no labels — labels added in vector stage)
- Redaction summary (what was stripped, for user review before sending)

## What the compile must guarantee

- Selected preview is **inspiration only**, not copied verbatim. Vector path independent.
- Labels precise (clash-checked).
- Style Lock honored (no ad-hoc font/color).
- Re-runnable from spec.yaml + selected preview without manual intervention.

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

Lesson source: 2026-04-28 fig3_trapping_concept first attempt drifted to a 4-panel data
figure before scope was caught. Plugin is responsible for catching this at the briefing
stage, not after a full image-gen + vector-compile cycle.

## Asset references

- Style Lock source: `styles/polymer-paper-preamble.sty` (\IsoCharge, \GradSlab, \IsoBlock, \IsoConeTip)
- Compile chain: `scripts/compile.sh` (lualatex)
- Checks: `scripts/check_collisions.py`, `scripts/check_visual_clash.py`
- Export: `scripts/export_svg.sh`, `scripts/svg_to_png.sh`

## Rationale (one paragraph)

The reference-image layer was removed after Y0 fig1 pilot showed strong references inflated
visual_clash WARN by +32 vs no-reference baseline (V_curated 41 > V_brief 9, INCONCLUSIVE).
Generative draft from prompt-only avoids the anchor-misuse mechanism entirely. Image generation
stays external because (a) the user already pays for one image-gen tool, (b) plugin avoids API
key management, (c) the natural "halt → user generates → resume" structure is a built-in
manual gate that prevents automated pipeline from skipping human judgment on draft quality.
