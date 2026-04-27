# figure-agent v0.1 Design

**Date**: 2026-04-27
**Status**: scaffold complete, implementation pending

## Origin

Successor to `[tikz-paper-workflow]` plugin (archived). Architecture pivoted after Y0 fig1
pilot (3-way: V_brief / V_weak / V_curated) showed reference-image layer hurt more than
helped: V_curated (strong reference) produced 41 visual_clash WARN vs V_brief (no reference)
9, a +32 inflation that triggered INCONCLUSIVE verdict despite +1.75 rubric mean uplift.

Interpretation: reference images, regardless of selection quality, induce anchor misuse and
density inflation. Removing the reference layer entirely — and replacing it with
generative-draft-from-prompt — eliminates the failure mechanism.

## Two Responsibilities

### 1. Confident Prompt Generation

Goal: one text block that, copy-pasted into any modern image-gen tool, produces a usable
scientific schematic on first attempt.

Components:
- Domain vocabulary (specific terms from briefing.md)
- Style block (Nature schematic, minimal labels, balanced composition)
- Composition hint (panel layout, flow direction, arrow semantics)
- Negative prompt (no numerical values, no labels)
- Automatic redaction (numbers, units, geometry, experimental conditions)
- Redaction audit (visible to user for confirm before send)

### 2. Tight Vector Compile

Goal: selected preview → SVG/TikZ deterministic reconstruction with publication quality.

Components:
- Compile chain (lualatex via `scripts/compile.sh`)
- Style Lock (`styles/polymer-paper-preamble.sty` macros)
- Collision check (`scripts/check_collisions.py`)
- Visual clash check (`scripts/check_visual_clash.py`)
- Multi-panel alignment (TikZ subfigure pattern)
- Revision re-render from spec.yaml + selected preview

## Out of Scope

- Image-gen API integration (any backend)
- Reference image retrieval (Crossref / Semantic Scholar / PaperBanana paths deprecated)
- "Single source of truth" YAML spec (spec.yaml is lightweight; meaning in briefing.md + .tex)
- Reference-quality pilots (Y0/Y1 retired with the reference layer)

## Workflow Stages (5 slash commands)

```
/fig_new <name>             scaffold
/fig_prompt                 redacted prompt → HALT
   ↓ user works externally (any image-gen tool)
/fig_preview_select         user picks 1 of 3-5 candidates
/fig_compile                vector reconstruct + checks
/fig_export                 PDF/SVG/TIFF
```

Manual gate naturally embedded between `/fig_prompt` and `/fig_preview_select` — workflow
exits, user does external work, returns when ready.

## Per-figure Folder Convention

```
examples/<figure_name>/
├── spec.yaml         # lightweight (panels + style_profile + selected_preview)
├── briefing.md       # human's intent in prose
├── previews/         # external image-gen output (any filename)
├── selected/         # chosen preview (symlink or copy)
├── <name>.tex        # human-authored TikZ source
├── build/            # lualatex artifacts (gitignored)
└── exports/          # PDF/SVG/TIFF (gitignored except on release)
```

## Asset Inheritance from [tikz-paper-workflow]

**Copied (90% of compile-side value)**:
- `styles/polymer-paper-preamble.sty`
- `scripts/check_collisions.py`
- `scripts/check_visual_clash.py`
- `scripts/compile.sh`
- `scripts/export_svg.sh`
- `scripts/svg_to_png.sh`

**Discarded**:
- `retrieve_refs.py` (925 LOC — reference retrieval no longer needed)
- `init_figure_refs.sh`
- `promote_internal_success.sh`
- `registry_update.sh`
- `_check_manifest.py`
- `build_contactsheet.sh` (preview select handles this differently)
- `references/<fig>/{retrieved, claude_svg, imagegen}` per-figure structure
- 5-layer source / role / license registry
- Gate γ reference-quality decision logic

## v0.1 Scope (this scaffold)

- Repo structure ✓
- 5 slash command stubs (this doc)
- plugin.json + SKILL.md ✓
- Asset copy (sty + 5 scripts) ✓
- design-v0.1.md (this file)

## v0.1 Implementation Pending

- `scripts/redact.py` — regex + ontology-stub redaction
- `scripts/prompt_gen.py` — prompt template engine
- Wire each slash command to its script
- First dogfooding: port `sc4_ispd_iso` from [tikz-paper-workflow] as inaugural example
- Decision: keep `compile.sh` script invocation pattern as-is, or wrap in plugin script

## Known Risks (1-line pin)

The whole bet rides on whether selected preview → vector reconstruct actually reaches
Nature-tone quality. Cannot answer with design alone — first dogfooding figure is the
empirical test. If that fails, the question is not "fix the plugin" but "is generative draft
from prompt-only sufficient anchor for a paper-grade vector reconstruction."
