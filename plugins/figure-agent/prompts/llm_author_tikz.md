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

## 5. Briefing Context

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

{{selection_notes}}

These notes refine §3 composition intent with preview-specific element
placement, palette use, and corrections. Priority order: §6 invariants >
§3 composition intent > selection notes. When selection notes conflict
with §6, honor §6 and ignore the conflicting note.

## 7. Output Contract

- Output a single `.tex` file body. No prose, no markdown fences, no commentary.
- The file must compile with `lualatex` against `polymer-paper-preamble.sty`
  without errors.
- Every color reference must be from the palette list in §2.
- Every element that corresponds to a flagship macro must use that macro.
