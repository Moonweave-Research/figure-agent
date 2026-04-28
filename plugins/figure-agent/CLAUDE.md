# CLAUDE.md — figure-agent

This repo is a Claude Code plugin. Authoritative workflow: `skills/figure-agent/SKILL.md`.

## Identity

Plugin responsibilities (only two):
1. Prompt intent control (normalization, not security-first redaction)
2. Human/LLM-authored TikZ compile/export (Style Lock + clash checks)

Plugin does **not** call image-gen APIs. User generates draft images externally and saves
them into `examples/<name>/previews/`.

## Workflow

```
/fig_new <name>  →  /fig_prompt <name>  →  [HALT, user works externally]
                 →  /fig_preview_select <name>
                 →  [HALT, user/LLM authors examples/<name>/<name>.tex]
                 →  /fig_compile <name>  →  /fig_export <name>
```

## Repo Notes

- ResearchOS workspace sibling to `[Athena]/`, `[Graph_making_hub]/`
- Successor to `[tikz-paper-workflow]/` (archived 2026-04-27)
- Reference-layer architecture deprecated (Y0 pilot evidence)
- Design doc: `docs/design-v0.1.md`
