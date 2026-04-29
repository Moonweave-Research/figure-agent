# figure-agent Quality Kernel Goal

**Date**: 2026-04-29
**Status**: active direction after v0.1.7.2 review

## Decision

`figure-agent` is not primarily a figure-generation orchestrator. It is a
paper-figure quality, compile, and reproducibility infrastructure layer.

The plugin should assume that a human, Claude, GPT, Gemini, image-generation
tool, Illustrator, or another workflow may create the figure source. The plugin's
durable job is to decide whether the resulting source and exports are consistent,
reproducible, and good enough to continue toward a manuscript.

## Product Identity

One sentence:

> Deterministic quality gates for paper figures, regardless of who or what
> authored the figure.

The plugin owns:

- Style consistency across a paper's figures.
- Compile and export reliability.
- Visual QA gates before manuscript use.
- Reproducible per-figure folders and provenance.
- Honest status reporting when examples or exports are stale.

The plugin does not own:

- Choosing the best frontier LLM.
- Calling image-generation or vision APIs.
- Teaching an LLM how to create every figure.
- Automatic PNG-to-SVG or PNG-to-TikZ reconstruction.
- More orchestration steps whose value depends on today's model weaknesses.

## Why The Pivot

The earlier v0.1 identity mixed two concerns:

1. **Transient orchestration**: prompt normalization, selection notes, LLM
   authoring prompts, preview selection, HALT/paste/resume loops.
2. **Durable infrastructure**: Style Lock, compile/export, visual checks,
   reproducibility, status and stale-artifact detection.

The transient layer may become less valuable as frontier models improve. The
durable layer remains necessary because manuscripts need consistent style,
repeatable artifacts, and quality gates that do not depend on memory or model
behavior.

## Frozen Legacy Helpers

These v0.1 helpers may remain because they already work, but they are not the
main development direction:

- `/fig_prompt`
- `scripts/redact.py` prompt normalization
- `spec.yaml.selection_notes` and the 4-heading recommendation
- `prompts/llm_author_tikz.md`
- preview-selection orchestration
- `/fig_review` as an external critic brief generator

Do not add new orchestration features unless dogfooding proves a repeated,
non-transient bottleneck.

## Durable Kernel

Future work should improve this kernel:

1. **Style Lock**
   - Stronger `lint_tex.py` BLOCKER rules.
   - Journal-scale typography and stroke constraints.
   - Palette and font drift prevention.
   - Macro usage contracts for paper-wide consistency.

2. **Macro Library**
   - Better `polymer-paper-preamble.sty` flagship macros.
   - Higher-level reusable schematic primitives.
   - Tested examples that produce visually credible figures.

3. **Compile and Export**
   - Reliable PDF/SVG/TIFF/PNG output.
   - Stale artifact prevention.
   - Export backend quality checks.
   - Font/text policy for SVG and raster outputs.
   - Golden fixtures track accepted exports as reproducibility baselines; ordinary
     generated build/export contents remain ignored.

4. **Visual QA**
   - Collision and visual-clash checks that catch real manuscript problems.
   - Golden render fixtures for representative figures.
   - Snapshot or metric checks that prevent regression in output quality.
   - Minimum artifact gates for rendered labels, SVG non-emptiness, PNG size, and
     opaque-white PNG backgrounds via `scripts/check_golden_artifacts.py`.
   - Separate first-pass sanity gates from accepted-mode gates. Accepted golden
     fixtures require `accepted: true`, fresh audit, and checker-warning budgets.

5. **Reproducibility**
   - Per-figure folder contract.
   - `spec.yaml`, `briefing.md`, `.tex`, build/export status.
   - Clear `fig_status` diagnostics for stale or unreplayable examples.

## Immediate Quality Target

The first representative figure is fixed:

- `docs/golden-target-trap-depth-picture.md`

Before expanding features, recreate that target as vector source and audit the
actual PDF/SVG/PNG output.

Golden Target 001 uses `reference_image` for the fixed target PNG. It must not
overload `selected_preview`, which remains the legacy field for an image-gen
candidate chosen from `previews/`.

The audit must classify every defect into one of four layers:

- **Source**: the `.tex` layout or drawing commands are weak.
- **Macro**: `polymer-paper-preamble.sty` lacks the right reusable primitive.
- **Export**: the rendered SVG/PNG/PDF path degrades the figure.
- **QA**: the checker failed to catch a visible manuscript-quality problem.

This audit is the next milestone. Passing tests and producing files are not
enough; the output must be visually credible for a manuscript and must match the
golden target's labels, layout, visual hierarchy, and export fidelity.

## v0.2 Direction

v0.2 is no longer a selection-notes or LLM-orchestration branch decision.

v0.2 should be a quality-kernel release:

- one golden figure fixture;
- stronger Style Lock rules;
- improved flagship macros;
- compile/export reliability checks;
- visual QA improvements tied to real defects observed in the golden fixture.

The old v0.2 ideas around `/fig_decompose`, prompt scoring, and contact-sheet
ranking remain deferred indefinitely unless real figure dogfooding proves they
are still necessary after the kernel is credible.
