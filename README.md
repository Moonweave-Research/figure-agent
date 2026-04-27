# figure-agent

Claude Code plugin for paper-grade scientific figures.

**Plugin responsibility (two only):**
1. **Confident prompt generation** — domain vocabulary + style block + composition hint + automatic redaction (numbers/units/conditions stripped) so external image-gen tools produce a usable draft on first try.
2. **Tight vector compile** — selected preview → SVG/TikZ reconstruction with collision/visual-clash checks, Style Lock, multi-panel alignment, deterministic re-render.

**Plugin does not:**
- Call image generation APIs
- Manage API keys
- Pay per-figure inference cost

**User does:**
- Pick external image-gen tool (ChatGPT / Gemini / Nano Banana / Midjourney / local SD — free choice)
- Save generated previews into `previews/`
- Final select among 3-5 candidates

## Workflow (5 slash commands)

```
/fig_new <name>            → spec.yaml + briefing.md scaffold
/fig_prompt                → redacted prompt (copy → external tool → save to previews/)
                             [HALT — slash exits]
                             (user generates images externally)
/fig_preview_select        → listdir previews/ → user picks 1
/fig_compile               → vector reconstruct (SVG/TikZ) + Style Lock + clash check
/fig_export                → PDF / SVG / TIFF (600 dpi)
```

## Status

v0.1 scaffold (2026-04-27). Spec under `docs/design-v0.1.md`.

## History

Successor to `[tikz-paper-workflow]` (archived 2026-04-27). Reference-layer architecture
deprecated based on Y0 fig1 pilot finding (strong refs increased visual_clash WARN by +32 vs
no-ref baseline). New direction: generative draft from prompt only, no external reference images.

## Repo location rationale

Lives under `~/workspace/ResearchOS/` as sibling to `[Athena]/`, `[Graph_making_hub]/`. Plugin
install copies to `~/.claude/plugins/cache/...` regardless of repo location, so position is
chosen for development proximity to research data.
