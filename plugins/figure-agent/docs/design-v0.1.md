# figure-agent v0.1 Design

**Date**: 2026-04-28
**Status**: v0.1 ship spec, implementation alignment pending

## One-line Identity

`figure-agent` v0.1 is an **intent-controlled schematic workflow**.

It turns research intent into image-gen-ready schematic prompts, lets the user
create and select external visual drafts, then supports human/LLM-authored TikZ
vector finishing with deterministic compile, clash checks, and export.

It is **not** an automatic image-to-vector reconstruction system in v0.1.

## Origin

`figure-agent` succeeds the archived `[tikz-paper-workflow]` plugin. The old
reference-layer path was retired after the Y0 fig1 pilot showed that strong
reference images could increase visual density and visual-clash warnings instead
of improving schematic quality. The new workflow uses external generative drafts
as disposable visual exploration, not as source-of-truth references.

The pivot is not "hide all information from external tools." The real goal is to
control what image-gen models attend to, so the draft stays schematic, clean, and
mechanism-focused.

## Product Bet

For publication schematics, the bottleneck is usually not API access or raw image
generation. The bottleneck is preserving the author's conceptual intent while
preventing image-gen from overfitting to distracting literals such as exact
counts, sample labels, dimensions, or experimental conditions.

v0.1 therefore optimizes for:

- Better first-pass external schematic drafts.
- Clear separation between draft exploration and final vector source.
- Deterministic compile/check/export once TikZ exists.
- Honest capability boundaries.

## Core Responsibilities

### 1. Prompt Intent Control

Goal: produce one prompt block that can be copied into any modern image-gen tool
and is likely to yield a useful scientific schematic draft.

The prompt engine reads `spec.yaml` and `briefing.md`, then applies
**normalization**, not security-first redaction.

Normalization means:

- Preserve the scientific mechanism and domain vocabulary.
- Surface explicit physics invariants early in the prompt when the briefing
  provides them.
- Preserve useful visual intent: layout, hierarchy, arrows, material contrast,
  and visual metaphors.
- Generalize literals that can pull image-gen toward clutter or data-plot
  behavior.
- Surface an audit so the user can judge whether the prompt still reflects the
  intended schematic.

Examples:

| Input from briefing | Prompt-facing form | Why |
| --- | --- | --- |
| `4 dots` | `a few electron dots` | Avoid brittle literal counting. |
| `S60-S85` | `different material compositions` | Avoid sample-code/data-plot drift. |
| `200 nm film` | `thin film` | Preserve visual role, drop exact dimension. |
| `three layers` | `stacked layers` | Keep structure without over-constraining count. |
| `70/30 copolymer` | `copolymer material` | Keep material class, avoid exact formulation. |

The audit vocabulary distinguishes:

- `NORMALIZED`: literal detail was generalized for image-gen quality.
- `KEPT`: domain term was intentionally preserved.
- `WARN`: the input looks like a data plot or experiment-specific request that
  may need user confirmation.

The existing `redact.py` name may remain during v0.1 implementation for
compatibility, but the design contract is prompt normalization / intent control.

### 2. Human/LLM-in-the-loop Vector Finishing

Goal: once a draft direction is selected, produce a stable vector figure through
TikZ compile, visual checks, and export.

v0.1 does not automatically vectorize preview images. The selected preview is an
inspiration/reference for the authoring step. The final `.tex` source may be
written by the human, by an LLM, or by both iteratively.

The plugin owns the deterministic finishing surface:

- Compile chain via `scripts/compile.sh`.
- Style Lock through `styles/polymer-paper-preamble.sty`.
- Text collision checks via `scripts/check_collisions.py`.
- Render-based visual clash checks via `scripts/check_visual_clash.py`.
- Export to PDF/SVG/TIFF or PNG through export scripts.

## Non-goals

v0.1 does not:

- Call image-generation APIs.
- Manage image-generation API keys.
- Automatically convert selected preview images into TikZ/SVG.
- Guarantee final publication quality without human/LLM vector refinement.
- Generate quantitative data plots.
- Treat `spec.yaml` as a full single source of truth.
- Retrieve external reference images or revive the old reference registry.
- Target PyPI packaging or `uv build` as a release artifact.

## Workflow

```text
/fig_new <name>
  -> create examples/<name>/ scaffold
  -> collect research intent into briefing.md
  -> catch obvious data-plot drift early

/fig_prompt
  -> read spec.yaml + briefing.md
  -> normalize prompt for external image-gen
  -> output one prompt block + audit
  -> HALT

user works externally
  -> choose any image-gen tool
  -> generate 3-5 schematic draft candidates
  -> save files into examples/<name>/previews/

/fig_preview_select
  -> list previews
  -> user selects one visual direction
  -> record selected_preview in spec.yaml
  -> optionally record selection_notes — preview-grounded authoring guide
     (visual motifs to preserve, preview errors to fix in TikZ, labels to
     lift, style overrides). Free-form; 4-heading template recommended.
     selection_notes is plumbed into the LLM authoring prompt with priority
     §6 invariants > §3 composition intent > selection notes.

human/LLM vector finishing
  -> author examples/<name>/<name>.tex using selected preview as inspiration
  -> keep final source independent and editable

/fig_compile
  -> compile the .tex source
  -> run collision and visual-clash checks
  -> report warnings without auto-fixing

/fig_review
  -> emit a self-contained reviewer brief for an external vision-capable critic
  -> ask the critic to check briefing §6 physics invariants and visual placement
  -> HALT so the user attaches build/<name>.png and works externally

/fig_export
  -> export final files into examples/<name>/exports/
```

## Per-figure Folder Contract

```text
examples/<figure_name>/
├── spec.yaml          # lightweight metadata: name, panels, style_profile, selected_preview, selection_notes
├── briefing.md        # research intent and schematic direction
├── previews/          # user-generated external image-gen drafts
├── selected/          # optional copy/symlink of chosen draft
├── <name>.tex         # human/LLM-authored TikZ source
├── build/             # canonical compile artifacts
└── exports/           # final PDF/SVG/TIFF/PNG outputs
```

The canonical compile output should be `build/`. Root-level generated
`<name>.pdf` or `<name>.png` files should not be the long-term contract because
they make stale-artifact checks and git noise more likely.

## Execution Contract

v0.1 commands and scripts should be documented from the plugin root unless a
specific wrapper supports figure-directory execution.

Canonical examples:

```bash
uv run python3 scripts/prompt_gen.py examples/<name>
bash scripts/compile.sh examples/<name>/<name>.tex
uv run python3 scripts/check_collisions.py examples/<name>/build/<name>.pdf
uv run python3 scripts/check_visual_clash.py examples/<name>/build/<name>.pdf
uv run python3 scripts/review_brief.py examples/<name>
bash scripts/export_svg.sh examples/<name>/build/<name>.pdf examples/<name>/exports/<name>.svg
```

Module-style Python execution with `python -m scripts.prompt_gen` is not a v0.1
contract unless the scripts are later packaged as importable modules.

## Data Plot Boundary

`figure-agent` is for schematic figures. Data plots belong in matplotlib,
Graph_making_hub, or a dedicated plotting workflow.

When the briefing contains data-plot signals, the plugin should not silently
continue as if it were a schematic request. It should ask whether the user wants
to reframe the idea as a qualitative schematic or redirect to a plotting tool.

Data-plot signals include:

- Quantitative axes or tick values.
- `vs composition`, `vs time`, sweep/range language.
- Raw/fitted curves, error bars, spectra, peak positions.
- Sample-code series such as `S60-S85` when used as data categories.
- Real measurement values that matter to the figure's scientific claim.

Not every number is forbidden. Numbers are only a problem when they distract the
image-gen draft or indicate that the requested artifact is really a data plot.

## v0.1 Ship Criteria

v0.1 is shippable when these are true:

- Docs describe v0.1 as intent-controlled prompt generation plus
  human/LLM-in-the-loop vector finishing.
- Docs do not claim automatic preview-to-vector reconstruction.
- Prompt normalization covers at least:
  - numeric count phrases such as `4 dots`;
  - English count words such as `three layers`;
  - sample labels/ranges such as `S60-S85`;
  - unitless geometry phrases such as `width 200 by 50 pixels`.
- Prompt audit explains what was generalized and why.
- Physics invariants from `briefing.md` are placed before general composition
  bullets and preserved verbatim so external image-gen sees them as hard
  conceptual constraints. Literal details in this block are reported as kept
  invariant constraints in the audit rather than silently normalized.
- Compile/check/export all consume the same canonical artifact path.
- `/fig_review` emits an API-free external-critic brief between compile and export.
- Slash command docs use one cwd convention.
- `uv run pytest -q` and `uv run ruff check .` pass.
- At least one compile/check/export smoke path is verified against the dogfood
  example or a smaller fixture.

## v0.2 Direction

v0.2 may add preview-assisted TikZ scaffolding, but only after v0.1's prompt
control and deterministic finishing contracts are stable.

Possible v0.2 work:

- Generate a first-pass TikZ scaffold from `briefing.md`, `spec.yaml`, and the
  selected preview metadata.
- Add stronger prompt-quality scoring before external image-gen.
- Extend `/fig_review` with prompt-mode critique before external image-gen and
  optional apply helpers for critic output. Keep the shipped v0.1.3 command
  API-free and user-gated.
- Add visual contact-sheet/ranking helpers for previews.
- Package Python helpers as importable modules if script-only execution becomes
  limiting.

## Design Risk

The main risk is not that a few numbers leave the local machine. The main risk is
that image-gen models over-attend to literal numeric details, sample codes, or
experimental conditions and produce dense, data-plot-like drafts instead of clean
scientific schematics.

The v0.1 design succeeds if it consistently keeps external drafts visually
schematic and makes the final TikZ finishing loop predictable.
