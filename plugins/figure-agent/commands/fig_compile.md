---
description: Compile human/LLM-authored TikZ. Style Lock + clash checks.
---

Compile the final TikZ source.

**Usage**: `/fig_compile <name>`

Run from the plugin root:

`bash scripts/compile.sh examples/<name>/<name>.tex`

`<name>` maps to `examples/<name>/`.

Check target: `examples/<name>/build/<name>.pdf`

Steps:
1. Read `examples/<name>/spec.yaml`. If `selected_preview` is null, note that direct
   human/LLM-authored TikZ compile is allowed; suggest `/fig_preview_select <name>` only
   when the user wants preview-guided authoring.
2. Verify `examples/<name>/<name>.tex` exists. If missing, instruct the user to author it
   with a human, an LLM, or both from the selected preview before compiling.
3. Compile target: `examples/<name>/<name>.tex` (TikZ authored by a human, an LLM, or both).
   - For v0.1, the selected preview is visual inspiration only.
   - The final `.tex` must remain editable and independent.
4. Run `bash scripts/compile.sh examples/<name>/<name>.tex` (lualatex via shared chain).
5. Run `uv run python3 scripts/check_collisions.py` on `examples/<name>/build/<name>.pdf`.
6. Run `uv run python3 scripts/check_visual_clash.py` on `examples/<name>/build/<name>.pdf`.
7. Report:
   - Compile success/fail
   - Collision report (count, severity)
   - Visual clash report (WARN list, NOT blocking)
   After review of compile + clash reports, run `/fig_review <name>` for structured
   physics + aesthetic critique before exporting.
8. Style Lock: confirm `\usepackage{polymer-paper-preamble}` is loaded in .tex.
   If missing, warn user but do not auto-inject.

Human-gated. Reports inform; do not block on WARN.

Next: /fig_review <name> or /fig_export <name> (if WARN > 0, revise <name>.tex and re-run /fig_compile <name>)
