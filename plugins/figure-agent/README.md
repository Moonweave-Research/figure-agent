# figure-agent

A Claude Code plugin that helps you build **reproducible, paper-grade scientific figures** in TikZ — so the same `.tex` source rebuilds the same figure every time, even after revisions.

You (or any LLM) draw the figure. The plugin handles the boring-but-critical parts: keeping styles consistent, catching layout problems, running the build, and exporting clean PDF/SVG.

---

## What you get

- **One folder per figure** with a fixed structure — never lose track of which source matches which output.
- **Style Lock** — palette, fonts, line weights stay consistent across every figure in a manuscript.
- **Build + visual QA** in one command — compile errors, label collisions, and clash warnings all in one report.
- **Reference analysis** — `reference PNG -> OCR + palette clusters + optional vtracer structural hints`, then `coordinate_hints.yaml -> semantic TikZ authoring`. SVG-to-TikZ path conversion is not the active workflow.
- **Vision critique without API costs** — the host Claude Code reads your compiled figure and writes feedback. Subscription tokens only; no external API keys, no per-figure inference bill.
- **Export to PDF / SVG / TIFF / PNG** with text staying as text (SVG preserves editable labels).

## What this is NOT

- ❌ **Image generation.** No DALL·E / Imagen / SDXL calls. You author the TikZ.
- ❌ **Data plots.** Numerical plots from real datasets go in `[Graph_making_hub]/`. This plugin is for **symbolic schematics** — energy diagrams, mechanism cartoons, device overviews.
- ❌ **Auto-magic SVG → TikZ converter.** Reference images are used as visual guides for *you*, not as inputs to a code generator.
- ❌ **Paid API service.** All vision work is done by the host Claude Code session you're already running.

---

## The six commands

```
/fig_new      Start a new figure — chat interview fills briefing.md + spec.yaml
/fig_extract  (optional) reference PNG -> OCR + palette clusters + optional vtracer structural hints
/fig_compile  Build the TikZ → PDF + PNG, run Style Lock + collision checks
/fig_critique Have host Claude read the build PNG and write critique.md
/fig_export   Export final PDF / SVG / TIFF / PNG
/fig_status   "Where am I?" — read-only stage check
```

## A typical figure (start to finish)

```bash
# 1. Scaffold the folder. Claude asks you 7 questions and fills briefing.md.
/fig_new fig3_trap_concept

# 2. (Optional) If you have a reference image (paper figure, sketch, mockup),
#    drop it in examples/fig3_trap_concept/reference/ and extract hints.
/fig_extract fig3_trap_concept

# 3. You (or an LLM) write examples/fig3_trap_concept/fig3_trap_concept.tex
#    using briefing.md intent + reference + coordinate_hints.yaml.
#    Contract: coordinate_hints.yaml -> semantic TikZ authoring.
#    SVG-to-TikZ path conversion is not the active workflow.

# 4. Compile. This runs Style Lock + builds PDF + PNG + collision/clash checks.
/fig_compile fig3_trap_concept

# 5. Get vision feedback. Host Claude reads the build PNG.
/fig_critique fig3_trap_concept   # writes critique.md

# 6. Iterate: edit .tex (often one line at a time), re-compile, re-critique.
#    When the critique looks clean, export.
/fig_export fig3_trap_concept
```

**Iteration philosophy.** Don't redraw the figure each time the critique fires. Make small, targeted edits — one polymer chain, one label, one arrow at a time. 5–10 iterations × 1-line patch is the path to paper-grade quality. (See `docs/architecture-v0.5-per-panel-reference-workflow.md` for the per-panel critique workflow.)

---

## Current state (v0.5.2)

| Area | What's working |
|---|---|
| **Build pipeline** | `/fig_compile` runs Style Lock + lualatex + collision + clash checks. Report-only by default; manuscript runs use `FIGURE_AGENT_STRICT=1` for hard fail. |
| **Vision critique** | `/fig_critique` reads build PNG + per-panel reference crops, writes structured `critique.md`. Host Claude only — no external API. |
| **Per-panel reference** | `spec.yaml.panels[i].reference_image` + `bbox_pdf_cm`. Each panel compared against its own reference. |
| **Perception pack** | `/fig_compile` emits descriptive data (`extract.yaml`, `overlay.png`) under `build/perception/` for downstream inspection. |
| **Reproducibility** | `/fig_status` separates render freshness (`.tex`, briefing, spec, Style Lock) from critique freshness (reference images, hints, authoring context), and reports a `final_ready` state vector. |
| **Golden fixtures** | Accepted figures declare `accepted: true` + `golden_contract`; `check_golden_artifacts.py --require-accepted` is the hard gate. |

## What's experimental / proposed (not built)

Filed as pre-spec issues; **no design committed**. Each has a decision gate that blocks design until empirical data exists. This is a deliberate response to v0.3/v0.4 specs being rejected for lack of data.

- **`docs/subregion-iteration-tool.md`** — lift critique granularity from panel → sub-region (e.g., the 8 distinct elements inside one panel). Prerequisite: v0.5 dogfood log on `fig1_overview_v2`.
- **`docs/svg-polish-pipeline.md`** — TikZ skeleton + SVG polish layer (Inkscape-replayable operations) for the final 5–10% of paper-grade quality. Prerequisite: sub-region tool data + verified SVG element-ID stability.

Falsified directions kept on record in `docs/historical/` and the relevant `architecture-v0.X-*.md` files: Python+SVG-from-scratch, LLM-as-quality-judge, perception auto-detection.

---

## Documentation map

**Read these first:**
- `docs/architecture-overview.md` — the layer-by-layer reference. Start here.
- `docs/quality-kernel-goal.md` — current product direction.
- `docs/architecture-v0.5-per-panel-reference-workflow.md` — how `/fig_critique` works now.

**Topic deep-dives:**
- `docs/architecture-v0.4.2-perception-data-only.md` — the perception data pack.
- `docs/golden-target-trap-depth-picture.md` — Golden Target 001 spec.
- `docs/golden-target-001-retrospective.md` — N=1 evidence + gap list.
- `docs/macros/` — macro API docs (band-diagram, bell-curve, plot-callout).
- `docs/trials/` — dated dogfood reports.

**Frozen historical (do not maintain, kept for context):**
- `docs/historical/design-v0.1.md` — the v0.1 prompt/preview/selection-notes workflow that was removed in v0.2.
- `docs/historical/roadmap-v0.1.7-selection-notes.md` — rollout decisions superseded by the quality-kernel goal.

---

## Power-user notes

- **Strict mode.** `FIGURE_AGENT_STRICT=1` promotes collision/clash findings to hard fail. Useful in CI; off by default so build PNG stays available during iteration.
- **Golden fixture gate.** `check_golden_artifacts.py` auto-escalates when `spec.yaml` declares the `accepted` key (`true` or `false`). Override with `--no-require-accepted` for ad-hoc inspection.
- **Skip critique on export.** `scripts/run_export.py <name> --skip-critique` for intentional drafts. Otherwise, when a declared reference image is usable, missing/stale `critique.md` blocks export. Declared-but-missing references are configuration errors and are not bypassed by `--skip-critique`.
- **Status vector.** `/fig_status` prints `render_state`, `critique_state`, `export_state`, `acceptance_state`, and `final_ready`; use `final_ready: true` as the quick release triage signal, not stage 4 alone.
- **Plugin install.** Validate with `claude plugin validate .claude-plugin/plugin.json`, `claude plugin validate .`, and `claude plugin validate ../../.claude-plugin/marketplace.json`. Test with `uv run pytest` and `uv run ruff check .`. `uv build` is *not* a release gate.
- **Plugin cache audit.** Local installs copy the working directory into `~/.claude/plugins/cache/`. If a local install was made from a dirty checkout, run `python3 scripts/plugin_package_audit.py ~/.claude/plugins/cache/figure-agent-local/figure-agent/<version> --clean --max-mib 300` after `claude plugin update figure-agent@figure-agent-local` to remove generated build/cache paths and confirm the installed package is not bloated.
- **Repo location.** Lives under `~/workspace/ResearchOS/` as a sibling to `[Athena]/` and `[Graph_making_hub]/` for development proximity. Plugin install copies to `~/.claude/plugins/cache/…` regardless.

---

## History

Successor to `[tikz-paper-workflow]/` (archived 2026-04-27). The v0.1 prompt-template / preview-selection workflow is preserved only in `docs/historical/`. Active development is the quality kernel: Style Lock, macro quality, compile/export reliability, visual QA, and reproducibility.
