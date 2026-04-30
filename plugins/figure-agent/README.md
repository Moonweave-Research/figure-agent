# figure-agent

Claude Code plugin for paper-grade scientific figures.

**Current product direction: quality kernel.**

`figure-agent` is now treated as paper-figure quality, compile, and
reproducibility infrastructure. A human or any LLM/tool may author the figure;
the plugin's durable job is to enforce Style Lock, compile/export reliably,
surface visual QA problems, and keep the figure reproducible.

The earlier prompt/image-gen orchestration helpers remain available, but they
are frozen legacy helpers rather than the main development direction. See
`docs/quality-kernel-goal.md`.

**Plugin does not:**
- Call image generation APIs
- Manage API keys
- Pay per-figure inference cost

**User or external tool does:**
- Provide a reference, sketch, draft image, or direct editable source.
- Author the final editable TikZ/SVG source with a human, an LLM, or both.

## Quality-kernel workflow

Primary development is now centered on deterministic gates:

```
reference/source        → examples/<name>/briefing.md + optional reference_image
editable vector source  → examples/<name>/<name>.tex
/fig_compile <name>     → Style Lock + PDF/PNG build + collision/clash checks
/fig_export <name>      → PDF / SVG / TIFF / PNG accepted exports
/fig_status <name>      → stale/missing/replayability diagnosis
golden artifact checks  → rendered labels + SVG element floor + white PNG background
accepted artifact checks → explicit accepted flag + fresh audit + warning budgets
```

`/fig_compile` is report-only by default for collision/clash findings. For a
hard manuscript or CI gate, run the same wrapper with
`FIGURE_AGENT_STRICT=1`; this propagates `--strict` to the collision and visual
clash checkers so any finding exits non-zero.

For golden fixtures, `reference_image` records the target image. `selected_preview`
remains reserved for legacy preview selection from `previews/`.

## Frozen v0.1 orchestration helpers

```
/fig_new <name>            → spec.yaml + briefing.md scaffold
/fig_prompt <name>         → normalized prompt (copy → external tool → save PNG/JPG/JPEG previews)
                             [HALT — slash exits]
                             (user generates images externally)
/fig_preview_select <name> → list examples/<name>/previews/ → user picks 1
                             [HALT — user/LLM authors examples/<name>/<name>.tex]
/fig_compile <name>        → compile human/LLM-authored TikZ + Style Lock + clash checks
/fig_review <name>         → reviewer brief for external physics + aesthetic critique
                             [HALT — user critiques externally, revises .tex if needed]
/fig_export <name>         → PDF / SVG / TIFF / PNG (600 dpi raster)
```

These helpers remain available for old workflows, but they are not the main
post-v0.1.7.2 development direction. Run commands from the plugin root.
`<name>` resolves to `examples/<name>/`. Starter TikZ source:
`cp styles/tex_template.tex examples/<name>/<name>.tex`.

## Status

v0.1 line is active; latest shipped plugin version is recorded in
`.claude-plugin/plugin.json`. Spec under `docs/design-v0.1.md`.
Active direction is recorded in `docs/quality-kernel-goal.md`.

v0.1 is source-only as a Claude Code plugin. Use
`claude plugin validate .claude-plugin/plugin.json`, `claude plugin validate .`,
`claude plugin validate ../../.claude-plugin/marketplace.json`, `uv run pytest`,
and `uv run ruff check .`; `uv build` is not a release gate.

## History

Successor to `[tikz-paper-workflow]` (archived 2026-04-27). The v0.1 prompt
workflow remains available, but post-v0.1.7.2 development pivots toward a
durable quality kernel: Style Lock, macro quality, compile/export reliability,
visual QA, and reproducibility.

## Repo location rationale

Lives under `~/workspace/ResearchOS/` as sibling to `[Athena]/`, `[Graph_making_hub]/`. Plugin
install copies to `~/.claude/plugins/cache/...` regardless of repo location, so position is
chosen for development proximity to research data.
