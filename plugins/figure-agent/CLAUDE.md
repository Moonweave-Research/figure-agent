# CLAUDE.md — figure-agent

This repo is a Claude Code plugin. Authoritative workflow: `skills/figure-agent/SKILL.md`. Active product direction: `docs/quality-kernel-goal.md`.

## Identity

`figure-agent` is a **paper-figure quality kernel**. A human, Claude, GPT, Gemini, image-generation tool, Illustrator, or any other workflow may author the TikZ source; the plugin's durable job is to enforce style and reproducibility invariants regardless of author.

Quality kernel responsibilities:

1. **Style Lock** — palette / font / stroke / macro-usage consistency across a manuscript's figures.
2. **Compile & Export reliability** — deterministic PDF / SVG / TIFF / PNG output with stale-artifact detection.
3. **Visual QA** — collision, visual-clash, and (when Layer 2.5 hints exist) reference-vs-build layout drift checks; spec-driven golden-fixture artifact gates.
4. **Reproducibility** — per-figure folder contract, transparent state inference (`/fig_status`), explicit export tracking policy for golden fixtures.

Plugin does **not**:
- Call image-gen or external vision APIs directly.
- Decide which frontier LLM to use.
- Convert PNG → SVG/TikZ automatically (see `docs/quality-kernel-goal.md`).

Plugin **does** delegate vision tasks to the host Claude Code main loop
(L4.5 vision critique). The host reads the build PNG and writes
`critique.md` using subscription tokens — no external API call originates
from plugin code.

## Workflow

**Active (quality kernel + L4.5 vision critique):**
```
/fig_new <name>       scaffold (briefing + spec)
/fig_extract <name>   optional Layer 2.5 — OCR + palette shape clusters from reference PNG
                      → coordinate_hints.yaml (recommended when spec.yaml.reference_image exists)
                      [user/LLM authors examples/<name>/<name>.tex]
/fig_compile <name>   lint + lualatex + collision/clash/(optional drift) checks
                      + perception data pack in build/perception/
/fig_critique <name>  L4.5 — host Claude reads build/<name>.png + briefing,
                      writes structured critique.md (report-only)
/fig_export <name>    PDF / SVG / TIFF / PNG export
/fig_status [<name>]  read-only stage + accepted-state inference
```

`/fig_prompt`, `/fig_preview_select`, the prompt-template / redaction /
selection-notes pipeline, the `selected_preview` stage gate, and the
auxiliary scripts behind them were removed in the v0.2 frozen-legacy
cleanup (PR #8a + #8b). The legacy `/fig_review` HALT-then-paste workflow
was renamed and extended into `/fig_critique` (PR #9). See
`docs/architecture-v0.2-proposal.md`.

## Repo Notes

- ResearchOS workspace sibling to `[Athena]/`, `[Graph_making_hub]/`.
- Successor to `[tikz-paper-workflow]/` (archived 2026-04-27).
- Reference-layer architecture deprecated (Y0 pilot evidence).
- v0.1 spec: `docs/historical/design-v0.1.md` (frozen historical).
- v0.5 direction: `docs/quality-kernel-goal.md` plus
  `docs/architecture-v0.5-per-panel-reference-workflow.md` (active).
