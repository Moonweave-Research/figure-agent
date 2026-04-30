# AGENTS.md — figure-agent

Codex entry point. Authoritative workflow: `skills/figure-agent/SKILL.md`. Active product direction: `docs/quality-kernel-goal.md`.

## Identity

`figure-agent` is a **paper-figure quality kernel**. A human, Codex, GPT, Claude, image-generation tool, Illustrator, or any other workflow may author the TikZ source; the plugin's durable job is to enforce style and reproducibility invariants regardless of author.

Quality kernel responsibilities:

1. **Style Lock** — palette / font / stroke / macro-usage consistency across a manuscript's figures.
2. **Compile & Export reliability** — deterministic PDF / SVG / TIFF / PNG output with stale-artifact detection.
3. **Visual QA** — collision and visual-clash checks; spec-driven golden-fixture artifact gates.
4. **Reproducibility** — per-figure folder contract, transparent state inference (`/fig_status`), explicit export tracking policy for golden fixtures.

Plugin does **not**:
- Call image-gen or vision APIs.
- Decide which frontier LLM/agent to use.
- Convert PNG → SVG/TikZ automatically (see `docs/quality-kernel-goal.md`).

## Workflow

**Active (quality kernel):**
```
/fig_new <name>       scaffold (briefing + spec)
/fig_extract <name>   optional Layer 2.5 — OCR + palette shape clusters from reference PNG
                      → coordinate_hints.yaml (recommended when spec.yaml.reference_image exists)
                      [user/LLM authors examples/<name>/<name>.tex]
/fig_compile <name>   lint + lualatex + collision/clash checks
                      (FIGURE_AGENT_STRICT=1 promotes findings to hard fail)
/fig_export <name>    PDF / SVG / TIFF / PNG export (dvisvgm preserves text)
/fig_status [<name>]  read-only stage + accepted-state inference
```

**Frozen legacy (v0.1 orchestration; preserved for backwards compatibility, not the development direction):**
```
/fig_prompt <name>           normalized image-gen prompt block
/fig_preview_select <name>   record selected preview in spec.yaml
/fig_review <name>           reviewer brief for external critique
```

See `docs/quality-kernel-goal.md` for why these are frozen.

## Repo Notes

- ResearchOS workspace sibling to `[Athena]/`, `[Graph_making_hub]/`.
- Successor to `[tikz-paper-workflow]/` (archived 2026-04-27).
- Reference-layer architecture deprecated (Y0 pilot evidence).
- v0.1 spec: `docs/historical/design-v0.1.md` (frozen historical).
- v0.2 direction: `docs/quality-kernel-goal.md` (active).
