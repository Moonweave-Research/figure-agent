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

## Workflow shape

`/fig_new` is the **shared entry point** that scaffolds `examples/<name>/spec.yaml`
+ `briefing.md` via a conversational interview. After scaffolding, the workflow
branches into two paths; either is supported, but only the active path is
maintained going forward.

### Active (quality kernel)

```
/fig_new <name>          scaffold (briefing + spec)
/fig_extract <name>      OPTIONAL: OCR + palette shape clusters from reference PNG → coordinate_hints.yaml
                         (Layer 2.5; recommended for fixtures with reference_image)
                         [user/LLM authors examples/<name>/<name>.tex from briefing intent
                          + optional reference_image + (if available) coordinate_hints.yaml]
/fig_compile <name>      Style Lock (incl. preamble import) + PDF/PNG build + collision/clash
                         (FIGURE_AGENT_STRICT=1 promotes findings to hard fail)
/fig_export <name>       PDF / SVG (dvisvgm preserves text) / TIFF / PNG
/fig_status [<name>]     stage + accepted-state inference; legacy hints carry a [legacy] marker
```

Golden fixtures additionally declare `accepted` and `golden_contract` keys in
`spec.yaml`; `check_golden_artifacts.py` then auto-escalates into accepted-mode
contract checks (rendered-label match, source-inventory floor, audit freshness,
checker-warning budgets). Override with `--no-require-accepted` for ad-hoc
basic-mode inspection.

### Frozen (v0.1 image-gen orchestration; preserved for in-flight users)

```
/fig_new <name>              shared with the active path; same scaffold
/fig_prompt <name>           normalize spec + briefing into an external image-gen prompt
                             [HALT — user runs the prompt in their image-gen tool of choice]
/fig_preview_select <name>   record the chosen PNG in spec.yaml.selected_preview
                             [HALT — user/LLM authors <name>.tex influenced by the preview]
/fig_compile <name>          shared with the active path
/fig_review <name>           emit a reviewer brief for an external vision LLM
                             [HALT — user critiques externally, revises .tex]
/fig_export <name>           shared with the active path
```

Frozen does not mean unsupported; it means no new features land here unless
real dogfooding proves a durable non-transient need. See
`docs/quality-kernel-goal.md` for the rationale and
`docs/architecture-overview.md` for the layer model behind both paths.

## Status

v0.1 line is active; latest shipped plugin version is recorded in
`.claude-plugin/plugin.json`. Active direction is recorded in
`docs/quality-kernel-goal.md`; the original v0.1 ship spec is preserved
under `docs/historical/design-v0.1.md` as a frozen reference.

## Documentation map

Active:
- `docs/architecture-overview.md` — layer-by-layer reference; start here.
- `docs/quality-kernel-goal.md` — current product direction (durable kernel,
  frozen-legacy boundary, export tracking policy).
- `docs/golden-target-trap-depth-picture.md` — Golden Target 001 acceptance
  criteria (the canonical fixture spec).
- `docs/golden-target-001-retrospective.md` — N=1 evidence retrospective and
  the gap list driving v0.2 cleanup.

Historical (not maintained, pinned for context):
- `docs/historical/design-v0.1.md` — v0.1 ship spec.
- `docs/historical/roadmap-v0.1.7-selection-notes.md` — v0.1.7 selection_notes
  rollout decisions; superseded by the quality-kernel goal.
- `docs/historical/superpowers-plan-2026-04-29-golden-target-001.md` —
  executed implementation plan for Golden Target 001.

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
