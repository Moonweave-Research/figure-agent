# AGENTS.md — figure-agent

This repo is a Codex plugin. Authoritative workflow: `skills/figure-agent/SKILL.md`.

## Identity

Plugin responsibilities (only two):
1. Confident prompt generation (with redaction)
2. Tight vector compile (Style Lock + clash checks)

Plugin does **not** call image-gen APIs. User generates draft images externally and saves
them into `examples/<name>/previews/`.

## Workflow

```
/fig_new <name>  →  /fig_prompt  →  [HALT, user works externally]
                 →  /fig_preview_select  →  /fig_compile  →  /fig_export
```

## Repo Notes

- ResearchOS workspace sibling to `[Athena]/`, `[Graph_making_hub]/`
- Successor to `[tikz-paper-workflow]/` (archived 2026-04-27)
- Reference-layer architecture deprecated (Y0 pilot evidence)
- Design doc: `docs/design-v0.1.md`
