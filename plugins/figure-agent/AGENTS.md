# AGENTS.md — figure-agent

Codex entry point. Authoritative workflow: `skills/figure-agent/SKILL.md`.
Before product work, read the sole product and execution authority
`docs/figure-agent.md`. Other specifications, plans, roadmaps, and milestones
are evidence, not product authority.

## Routing priority

For **Figure Agent dogfood** and Figure Agent product-development work, use this
repository's Figure Agent workflow and rendered-evidence contracts before any
generic TikZ refinement workflow. A `.tex` extension is a representation detail,
not permission to invoke `tikz`, `tikz-refine`, or another external drawing
skill. Use such a specialist only when the user explicitly requests it.

Preserve free LLM authoring: diagnose the rendered defect and constrain meaning,
evidence, and regression risk rather than requiring a reusable primitive or a
specialist's coordinate recipe. If full, panel, and reduction-scale review finds
**no defensible defect**, a source no-op is a valid review outcome; report the
basin instead of manufacturing a diff. Compile-generated and ignored build
artifacts are evidence, not source mutations, and must not be cleaned merely to
make the worktree look changed or unchanged.

## Identity

`figure-agent` is a **paper-figure quality kernel**. A human, Codex, GPT, Claude, image-generation tool, Illustrator, or any other workflow may author the TikZ source; the plugin's durable job is to enforce style and reproducibility invariants regardless of author.

Quality kernel responsibilities:

1. **Style Lock** — palette / font / stroke / macro-usage consistency across a manuscript's figures.
2. **Compile & Export reliability** — deterministic PDF / SVG / TIFF / PNG output with stale-artifact detection.
3. **Visual QA** — collision and visual-clash checks; spec-driven golden-fixture artifact gates.
4. **Reproducibility** — per-figure folder contract, transparent state inference (`/fig_status`), explicit export tracking policy for golden fixtures.

Plugin does **not**:
- Call image-gen or external vision APIs directly.
- Decide which frontier LLM/agent to use.
- Convert PNG → SVG/TikZ automatically (see `docs/figure-agent.md`).

Plugin **does** delegate vision tasks to the host main loop (L4.5 vision
critique). The host reads the build PNG and writes `critique.md` using
subscription tokens — no external API call originates from plugin code.

## Workflow

**Active (quality kernel + L4.5 vision critique):**
```
/fig_new <name>       scaffold (briefing + spec)
/fig_extract <name>   optional Layer 2.5 — OCR + palette shape clusters from reference PNG
                      → coordinate_hints.yaml (recommended when spec.yaml.reference_image exists)
                      [user/LLM authors examples/<name>/<name>.tex]
/fig_compile <name>   lint + lualatex + collision/clash checks
                      + perception data pack in build/perception/
                      (FIGURE_AGENT_STRICT=1 promotes findings to hard fail)
/fig_critique <name>  L4.5 — host reads build/<name>.png + briefing,
                      writes structured critique.md (report-only)
/fig_export <name>    PDF / SVG / TIFF / PNG export (dvisvgm preserves text)
/fig_status [<name>]  read-only stage + accepted-state inference
```

The v0.1 frozen helpers (`/fig_prompt`, `/fig_preview_select`,
prompt-template / redaction / selection-notes pipeline,
`spec.yaml.selected_preview` stage gate) were removed in the v0.2
cleanup (PR #8a + #8b). The v0.1 `/fig_review` HALT-then-paste workflow
was renamed and extended into `/fig_critique` (PR #9). See
`docs/architecture-v0.2-proposal.md`.

## Repo Notes

- ResearchOS workspace sibling to `[Athena]/`, `[Graph_making_hub]/`.
- Successor to `[tikz-paper-workflow]/` (archived 2026-04-27).
- Reference-layer architecture deprecated (Y0 pilot evidence).
- v0.1 spec: `docs/historical/design-v0.1.md` (frozen historical).
- Product and forward execution authority: `docs/figure-agent.md`.
- Operational reference:
  `docs/architecture-v0.5-per-panel-reference-workflow.md`.
