---
description: Generate Reviewer brief (physics + aesthetic critique) from briefing + .tex + render. HALTS workflow.
---

Generate a structured reviewer brief for an external critic.

**Usage**: `/fig_review <name>`

Run from the plugin root:

`uv run python3 scripts/review_brief.py examples/<name>`

`<name>` maps to `examples/<name>/`.

Steps:
1. Read `examples/<name>/spec.yaml` + `examples/<name>/briefing.md`.
2. Verify `examples/<name>/<name>.tex` exists.
3. Verify `examples/<name>/build/<name>.png` exists. If missing, run `/fig_compile <name>` first.
4. Print one self-contained Reviewer brief:
   - Absolute path to the rendered PNG to attach
   - Author intent from briefing.md §1 and §3
   - Physics invariants from briefing.md §6
   - Full TikZ source under review
   - Rubric for physics correctness and aesthetic placement
   - Requested Markdown-table output format
5. HALT. Do not call any API. Do not critique or edit the `.tex` automatically.

Copy the brief into Claude Code's main loop, claude.ai, or another vision-capable critic,
attach the PNG, then decide whether to revise the `.tex`, re-run `/fig_compile <name>`,
or proceed to `/fig_export <name>`.
