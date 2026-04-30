# TikZ Authoring Prompt — {{example_name}}

## 1. Role

You are an expert TikZ author for materials-science schematics. Your task is to
produce a single compilable `.tex` file body that implements the figure described
below. Follow every constraint exactly; do not explain or comment on your choices.

## 2. Hard Constraints

- Preserve §6 Physics Invariants verbatim as logical constraints. Do not
  contradict, weaken, or reorder them.
- Use only palette colors: {{palette_names}}. No `\definecolor`, no font
  overrides, no raw hex (`#RRGGBB`), no non-palette color names (red, blue,
  green, etc.).
- Required scaffolding contract — see §3 for the exact open/close sequences.
  The output must be a complete standalone `.tex` (compile.sh runs `lualatex`
  on the file directly; nothing is wrapped around it).

## 3. Required Scaffolding

Every output must start with:

```latex
\documentclass{standalone}
\usepackage{polymer-paper-preamble}
\begin{document}
\begin{tikzpicture}
```

and end with:

```latex
\end{tikzpicture}
\end{document}
```

## 4. Flagship Macro Guidance

Prefer these macros over raw TikZ primitives for blocks, charges, gradients, and
cone tips. Use them wherever the schematic calls for corresponding elements.

{{flagship_macros_signature}}

## 5. Reference Examples — Read First

Before authoring, read the accepted `.tex` from other figures in this paper. These examples teach you the house style:
- **smooth curves**: How chains and plots use `plot[smooth]` with carefully placed coordinate points
- **flagship macros**: Actual usage of `\TrapLevel`, `\SmallLobe`, `\GradSlab`, and custom drawing patterns
- **tick labels**: How axes annotate quantitative values (e.g., `$10^{-3}$`, `$10^0$`, `$10^3$`)
- **text labels**: Placement anchors, font sizes, and multi-line formatting
- **dashed regions**: How to denote physical zones (trap-localized areas, integration regions)
- **element spacing**: Panel layout, horizontal separators, and visual hierarchy

Examples to inspect:
{{reference_fixture_paths}}

Copy patterns you find there when they apply to your schematic. You are authoring in the same style, on the same palette, under the same Style Lock.

## 5b. Structural Regions from Reference Image (Layer 2.5)

When a reference image is provided, the coordinates below are extracted via OCR
and vtracer vectorization. Use them as **precise placement guidelines** — draw
every labelled element so it falls inside the stated bounding box.
All coordinates are in centimeters in TikZ space (y=0 at bottom).

{{structural_regions}}

## 6. Briefing Context

### §1 — What does this figure show?

{{briefing_section_1}}

### §3 — Composition intent

{{briefing_section_3}}

### §5 — Style notes

{{briefing_section_5}}

### §6 — Physics invariants (hard constraints)

{{briefing_section_6}}

## 6. Spec Context

### Panels

{{spec_panels}}

### Selected preview

{{selected_preview}}

### Selection notes (preview-grounded authoring guide)

The notes below refine §3 composition intent with preview-specific element
placement, palette use, and corrections. Priority order: §6 invariants >
§3 composition intent > selection notes. When selection notes conflict
with §6, honor §6 and ignore the conflicting note. Selection notes may
add visual detail consistent with §6 but cannot introduce new invariants.

{{selection_notes}}

## 7. Output Contract

- Output a single `.tex` file body. No prose, no markdown fences, no commentary.
- The file must compile with `lualatex` against `polymer-paper-preamble.sty`
  without errors.
- Every color reference must be from the palette list in §2.
- Every element that corresponds to a flagship macro must use that macro.
