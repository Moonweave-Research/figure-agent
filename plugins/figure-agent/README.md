# figure-agent

Claude Code plugin for paper-grade scientific figures.

**Plugin responsibility (two only):**
1. **Prompt intent control** — turn research intent into image-gen-ready schematic prompts. Preserve scientific mechanism and visual intent; normalize literals that make image-gen overfit to counts, sample codes, dimensions, or experimental conditions.
2. **Human/LLM-in-the-loop vector finishing** — selected preview is visual inspiration only. The final TikZ source is authored by a human, an LLM, or both; the plugin provides deterministic compile, Style Lock, collision/visual-clash checks, and export.

**Plugin does not:**
- Call image generation APIs
- Manage API keys
- Pay per-figure inference cost

**User does:**
- Pick external image-gen tool (ChatGPT / Gemini / Nano Banana / Midjourney / local SD — free choice)
- Save generated PNG/JPG/JPEG previews into `examples/<name>/previews/`
- Final select among 3-5 candidates
- Author the final editable TikZ source at `examples/<name>/<name>.tex` with a human,
  an LLM, or both after preview selection

## Workflow (5 slash commands)

```
/fig_new <name>            → spec.yaml + briefing.md scaffold
/fig_prompt <name>         → normalized prompt (copy → external tool → save PNG/JPG/JPEG previews)
                             [HALT — slash exits]
                             (user generates images externally)
/fig_preview_select <name> → list examples/<name>/previews/ → user picks 1
                             [HALT — user/LLM authors examples/<name>/<name>.tex]
/fig_compile <name>        → compile human/LLM-authored TikZ + Style Lock + clash checks
/fig_export <name>         → PDF / SVG / TIFF / PNG (600 dpi raster)
```

Run commands from the plugin root. `<name>` resolves to `examples/<name>/`.
Starter TikZ source: `cp styles/tex_template.tex examples/<name>/<name>.tex`.

## Status

v0.1 scaffold (2026-04-27). Spec under `docs/design-v0.1.md`.

v0.1 is source-only as a Claude Code plugin. Use
`claude plugin validate .claude-plugin/plugin.json`, `claude plugin validate .`,
`uv run pytest`, and `uv run ruff check .`; `uv build` is not a release gate.

## History

Successor to `[tikz-paper-workflow]` (archived 2026-04-27). Reference-layer architecture
deprecated based on Y0 fig1 pilot finding (strong refs increased visual_clash WARN by +32 vs
no-ref baseline). New direction: generative draft from prompt only, no external reference images.

## Repo location rationale

Lives under `~/workspace/ResearchOS/` as sibling to `[Athena]/`, `[Graph_making_hub]/`. Plugin
install copies to `~/.claude/plugins/cache/...` regardless of repo location, so position is
chosen for development proximity to research data.
