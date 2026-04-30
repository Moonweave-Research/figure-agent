---
description: "[frozen legacy] Generate normalized external image-gen prompt from spec.yaml + briefing.md. HALTS workflow."
---

> **Status: frozen legacy.** Preserved from v0.1 orchestration; not the active development direction. The quality-kernel workflow (`/fig_compile` / `/fig_export` / `/fig_status`) does not require this command. See `docs/quality-kernel-goal.md`.

Generate prompt for external image-gen tool.

**Usage**: `/fig_prompt <name>`

Run from the plugin root:

`uv run python3 scripts/prompt_gen.py examples/<name>`

`<name>` maps to `examples/<name>/`.

Steps:
1. Read `examples/<name>/spec.yaml` + `examples/<name>/briefing.md`.
2. Apply prompt normalization: preserve mechanism and visual intent while generalizing
   literals that make image-gen overfit to counts, sample codes, dimensions, or experimental
   conditions.
3. Compose ONE prompt block:
   - Opening: "Create a clean white-background Nature-style scientific schematic."
   - Topic line (from briefing.md)
   - A near-top scientific-constraints block from briefing.md §6, if present;
     preserve those bullets verbatim and do not echo the briefing section title verbatim
   - Include: bullet list of what must appear (from briefing.md, normalized)
   - Style: minimal, elegant, no unnecessary text, consistent colors, balanced composition
   - Normalization policy: avoid distracting literals while preserving schematic intent
4. Print:
   ```
   === NORMALIZED PROMPT (copy below for external tool) ===
   <prompt body>
   === END PROMPT ===

   Normalization audit:
   - <list of items generalized, kept, or warned>

   Next steps:
   1. Copy prompt above into your image-gen tool of choice.
   2. Generate 3-5 candidates.
   3. Save PNG/JPG/JPEG candidates into examples/<name>/previews/ (any filename).
   4. Run /fig_preview_select <name> to continue.
   ```
5. HALT. Do not call any API. Do not generate images.

This is a manual gate. The slash exits and user works externally.

Next: copy prompt to image-gen, save PNG/JPG/JPEG into examples/<name>/previews/, then /fig_preview_select <name>
