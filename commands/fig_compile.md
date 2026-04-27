---
description: Reconstruct selected preview as SVG/TikZ. Style Lock + clash checks.
---

Compile selected preview into vector form.

**Usage**: `/fig_compile` (inside examples/<name>/ or --name)

Steps:
1. Verify `spec.yaml.selected_preview` is set. If null, instruct to run `/fig_preview_select` first.
2. Compile target: `examples/<name>/<name>.tex` (the human-authored TikZ source).
   - For v0.1, the .tex file is hand-written by user using selected preview as visual reference.
   - Future: auto-scaffold .tex from selected preview (out of scope for v0.1).
3. Run `uv run python3 scripts/compile.sh examples/<name>/<name>.tex` (lualatex via shared chain).
4. Run `uv run python3 scripts/check_collisions.py` on the compile output.
5. Run `uv run python3 scripts/check_visual_clash.py` on rendered PNG.
6. Report:
   - Compile success/fail
   - Collision report (count, severity)
   - Visual clash report (WARN list, NOT blocking)
7. Style Lock: confirm `\usepackage{polymer-paper-preamble}` is loaded in .tex.
   If missing, warn user but do not auto-inject.

Human-gated. Reports inform; do not block on WARN.
